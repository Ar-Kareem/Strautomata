
import time

WIDTH = 7
HEIGHT = 6
STRIDE = HEIGHT + 1
SHIFT = WIDTH * STRIDE

BOTTOM_MASKS = tuple(1 << (c * STRIDE) for c in range(WIDTH))
COLUMN_MASKS = tuple(((1 << HEIGHT) - 1) << (c * STRIDE) for c in range(WIDTH))
TOP_MASKS = tuple(1 << (c * STRIDE + HEIGHT - 1) for c in range(WIDTH))

BOTTOM_MASK = sum(BOTTOM_MASKS)
BOARD_MASK = sum(COLUMN_MASKS)

ORDER = (3, 2, 4, 1, 5, 0, 6)

_rank = [0] * WIDTH
for _i, _c in enumerate(ORDER):
    _rank[_c] = _i
RANK = tuple(_rank)

COL_WEIGHTS = (3, 4, 5, 7, 5, 4, 3)
LINE_WEIGHTS = (0, 3, 14, 80, 100000)

WIN_SCORE = 1_000_000
INF = 1_000_000_000


def _make_win_masks():
    masks = []
    directions = ((1, 0), (0, 1), (1, 1), (1, -1))
    for c in range(WIDTH):
        for r in range(HEIGHT):
            for dc, dr in directions:
                ec = c + 3 * dc
                er = r + 3 * dr
                if 0 <= ec < WIDTH and 0 <= er < HEIGHT:
                    m = 0
                    for k in range(4):
                        m |= 1 << ((c + k * dc) * STRIDE + (r + k * dr))
                    masks.append(m)
    return tuple(masks)


WIN_MASKS = _make_win_masks()


def _possible(mask: int) -> int:
    return (mask + BOTTOM_MASK) & BOARD_MASK


def _winning_position(position: int, mask: int) -> int:
    r = (position << 1) & (position << 2) & (position << 3)

    p = (position << STRIDE) & (position << (2 * STRIDE))
    r |= p & (position << (3 * STRIDE))
    r |= p & (position >> STRIDE)
    p = (position >> STRIDE) & (position >> (2 * STRIDE))
    r |= p & (position << STRIDE)
    r |= p & (position >> (3 * STRIDE))

    p = (position << HEIGHT) & (position << (2 * HEIGHT))
    r |= p & (position << (3 * HEIGHT))
    r |= p & (position >> HEIGHT)
    p = (position >> HEIGHT) & (position >> (2 * HEIGHT))
    r |= p & (position << HEIGHT)
    r |= p & (position >> (3 * HEIGHT))

    diag = HEIGHT + 2
    p = (position << diag) & (position << (2 * diag))
    r |= p & (position << (3 * diag))
    r |= p & (position >> diag)
    p = (position >> diag) & (position >> (2 * diag))
    r |= p & (position << diag)
    r |= p & (position >> (3 * diag))

    return r & (BOARD_MASK & ~mask)


def _evaluate(cur: int, opp: int, mask: int, poss=None, cur_win=None, opp_win=None) -> int:
    score = 0

    for c in range(WIDTH):
        cm = COLUMN_MASKS[c]
        score += ((cur & cm).bit_count() - (opp & cm).bit_count()) * COL_WEIGHTS[c]

    weights = LINE_WEIGHTS
    for m in WIN_MASKS:
        a = (cur & m).bit_count()
        b = (opp & m).bit_count()
        if b == 0:
            score += weights[a]
        elif a == 0:
            score -= weights[b]

    if poss is None:
        poss = _possible(mask)
    if cur_win is None:
        cur_win = _winning_position(cur, mask)
    if opp_win is None:
        opp_win = _winning_position(opp, mask)

    score += ((cur_win & poss).bit_count() - (opp_win & poss).bit_count()) * 160
    score += (cur_win.bit_count() - opp_win.bit_count()) * 18

    return score


def _choose_col(bits: int) -> int:
    for c in ORDER:
        if bits & COLUMN_MASKS[c]:
            return c
    return 0


def policy(board: list[list[int]]) -> int:
    fallback = 0
    try:
        for c in ORDER:
            if board[0][c] == 0:
                fallback = c
                break
    except Exception:
        return 3

    try:
        me = 0
        opp = 0

        for row in range(HEIGHT):
            bit_row = HEIGHT - 1 - row
            b_row = board[row]
            for c in range(WIDTH):
                v = b_row[c]
                if v:
                    bit = 1 << (c * STRIDE + bit_row)
                    if v > 0:
                        me |= bit
                    else:
                        opp |= bit

        mask = me | opp
        poss = _possible(mask)

        if poss == 0:
            return fallback

        if mask.bit_count() <= 1 and (poss & COLUMN_MASKS[3]):
            return 3

        if poss & (poss - 1) == 0:
            return _choose_col(poss)

        immediate = poss & _winning_position(me, mask)
        if immediate:
            return _choose_col(immediate)

        opp_win = _winning_position(opp, mask)
        forced = poss & opp_win

        if forced:
            if forced & (forced - 1):
                root_safe = 0
            else:
                root_safe = forced & ~(opp_win >> 1)
        else:
            root_safe = poss & ~(opp_win >> 1)

        root_moves = root_safe if root_safe else (forced if forced else poss)

        if root_moves and not (root_moves & (root_moves - 1)):
            move = _choose_col(root_moves)
            if board[0][move] == 0:
                return move

        fallback = _choose_col(root_moves)

        deadline = time.perf_counter() + 0.92
        tt = {}
        nodes = 0

        possible = _possible
        winpos = _winning_position
        evaluate = _evaluate
        col_masks = COLUMN_MASKS
        order = ORDER
        rank = RANK

        def negamax(cur: int, other: int, msk: int, depth: int, alpha: int, beta: int) -> int:
            nonlocal nodes

            nodes += 1
            if (nodes & 1023) == 0 and time.perf_counter() >= deadline:
                raise TimeoutError

            ps = possible(msk)
            if ps == 0:
                return 0

            cur_win = winpos(cur, msk)
            if ps & cur_win:
                return WIN_SCORE + depth

            if depth <= 0:
                other_win = winpos(other, msk)
                forced_here = ps & other_win

                if forced_here:
                    if forced_here & (forced_here - 1):
                        return -WIN_SCORE + depth
                    only_block = forced_here & ~(other_win >> 1)
                    if only_block == 0:
                        return -WIN_SCORE + depth
                    if depth == 0:
                        return -negamax(other, cur | only_block, msk | only_block,
                                        -1, -beta, -alpha)
                else:
                    if (ps & ~(other_win >> 1)) == 0:
                        return -WIN_SCORE + depth

                return evaluate(cur, other, msk, ps, cur_win, other_win)

            key = cur | (other << SHIFT)
            entry = tt.get(key)
            tt_best = -1

            if entry is not None:
                e_depth, e_val, e_flag, e_best = entry
                tt_best = e_best
                if e_depth >= depth:
                    if e_flag == 0:
                        return e_val
                    if e_flag == 1:
                        if e_val > alpha:
                            alpha = e_val
                    else:
                        if e_val < beta:
                            beta = e_val
                    if alpha >= beta:
                        return e_val

            orig_alpha = alpha
            orig_beta = beta

            other_win = winpos(other, msk)
            forced_here = ps & other_win

            if forced_here:
                if forced_here & (forced_here - 1):
                    return -WIN_SCORE - depth + 1
                moves = forced_here
            else:
                moves = ps

            moves &= ~(other_win >> 1)

            if moves == 0:
                return -WIN_SCORE - depth + 1

            best_val = -INF
            best_col = -1
            searched = False

            if 0 <= tt_best < WIDTH:
                bit = moves & col_masks[tt_best]
                if bit:
                    val = -negamax(other, cur | bit, msk | bit,
                                   depth - 1, -beta, -alpha)
                    best_val = val
                    best_col = tt_best
                    if val > alpha:
                        alpha = val
                    searched = True

            for c in order:
                if c == tt_best:
                    continue

                bit = moves & col_masks[c]
                if not bit:
                    continue

                if searched:
                    val = -negamax(other, cur | bit, msk | bit,
                                   depth - 1, -alpha - 1, -alpha)
                    if alpha < val < beta:
                        val = -negamax(other, cur | bit, msk | bit,
                                       depth - 1, -beta, -alpha)
                else:
                    val = -negamax(other, cur | bit, msk | bit,
                                   depth - 1, -beta, -alpha)
                    searched = True

                if val > best_val or (val == best_val and (best_col < 0 or rank[c] < rank[best_col])):
                    best_val = val
                    best_col = c

                if val > alpha:
                    alpha = val

                if alpha >= beta:
                    break

            if best_col < 0:
                return evaluate(cur, other, msk, ps, cur_win, other_win)

            if best_val <= orig_alpha:
                flag = 2
            elif best_val >= orig_beta:
                flag = 1
            else:
                flag = 0

            tt[key] = (depth, best_val, flag, best_col)
            return best_val

        def root_search(depth: int, first_col: int):
            alpha = -INF
            beta = INF
            best_val = -INF
            best_col = fallback

            if 0 <= first_col < WIDTH:
                bit = root_moves & col_masks[first_col]
                if bit:
                    val = -negamax(opp, me | bit, mask | bit,
                                   depth - 1, -beta, -alpha)
                    best_val = val
                    best_col = first_col
                    if val > alpha:
                        alpha = val

            for c in order:
                if c == first_col:
                    continue

                bit = root_moves & col_masks[c]
                if not bit:
                    continue

                val = -negamax(opp, me | bit, mask | bit,
                               depth - 1, -beta, -alpha)

                if val > best_val or (val == best_val and rank[c] < rank[best_col]):
                    best_val = val
                    best_col = c

                if val > alpha:
                    alpha = val

            return best_val, best_col

        best_col = fallback
        best_val = -INF
        max_depth = 42 - mask.bit_count()

        for depth in range(1, max_depth + 1):
            if time.perf_counter() >= deadline:
                break
            try:
                val, col = root_search(depth, best_col)
                if 0 <= col < WIDTH and board[0][col] == 0:
                    best_col = col
                    best_val = val
                if abs(best_val) > WIN_SCORE // 2:
                    break
            except TimeoutError:
                break

        if 0 <= best_col < WIDTH and board[0][best_col] == 0:
            return int(best_col)

        if 0 <= fallback < WIDTH and board[0][fallback] == 0:
            return int(fallback)

        for c in ORDER:
            if board[0][c] == 0:
                return int(c)

        return 0

    except Exception:
        if 0 <= fallback < WIDTH:
            return int(fallback)
        return 0
