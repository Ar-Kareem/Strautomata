
import time

WIDTH = 7
HEIGHT = 6
H1 = HEIGHT + 1

ORDER = (3, 4, 2, 5, 1, 6, 0)
INF = 10**9
WIN = 10**6
TIME_LIMIT = 0.82

BOTTOM_MASK = [1 << (c * H1) for c in range(WIDTH)]
TOP_MASK = [1 << (c * H1 + HEIGHT - 1) for c in range(WIDTH)]
COLUMN_MASK = [((1 << HEIGHT) - 1) << (c * H1) for c in range(WIDTH)]
FULL_MASK = sum(COLUMN_MASK)
CENTER_MASK = COLUMN_MASK[3]


def _bit(c, r):
    return 1 << (c * H1 + r)


WINDOWS = []

for r in range(HEIGHT):
    for c in range(WIDTH - 3):
        m = 0
        for i in range(4):
            m |= _bit(c + i, r)
        WINDOWS.append(m)

for c in range(WIDTH):
    for r in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= _bit(c, r + i)
        WINDOWS.append(m)

for c in range(WIDTH - 3):
    for r in range(HEIGHT - 3):
        m = 0
        for i in range(4):
            m |= _bit(c + i, r + i)
        WINDOWS.append(m)

for c in range(WIDTH - 3):
    for r in range(3, HEIGHT):
        m = 0
        for i in range(4):
            m |= _bit(c + i, r - i)
        WINDOWS.append(m)


def _is_win(bb):
    m = bb & (bb >> 1)
    if m & (m >> 2):
        return True

    m = bb & (bb >> H1)
    if m & (m >> (2 * H1)):
        return True

    m = bb & (bb >> (H1 - 1))
    if m & (m >> (2 * (H1 - 1))):
        return True

    m = bb & (bb >> (H1 + 1))
    if m & (m >> (2 * (H1 + 1))):
        return True

    return False


def _can_play(mask, col):
    return (mask & TOP_MASK[col]) == 0


def _play_bit(mask, col):
    return (mask + BOTTOM_MASK[col]) & COLUMN_MASK[col]


def _winning_cols(pos, mask):
    wins = []
    for c in ORDER:
        if _can_play(mask, c):
            move = _play_bit(mask, c)
            if move and _is_win(pos | move):
                wins.append(c)
    return wins


def _evaluate(pos, mask):
    opp = mask ^ pos

    score = 5 * ((pos & CENTER_MASK).bit_count() - (opp & CENTER_MASK).bit_count())

    for w in WINDOWS:
        p = (pos & w).bit_count()
        o = (opp & w).bit_count()

        if p and o:
            continue

        if p:
            if p == 1:
                score += 2
            elif p == 2:
                score += 10
            elif p == 3:
                score += 85
            elif p == 4:
                score += 100000
        elif o:
            if o == 1:
                score -= 2
            elif o == 2:
                score -= 12
            elif o == 3:
                score -= 110
            elif o == 4:
                score -= 100000

    opp_wins = 0
    for c in ORDER:
        if _can_play(mask, c):
            move = _play_bit(mask, c)
            if move and _is_win(opp | move):
                opp_wins += 1

    if opp_wins == 1:
        score -= 750
    elif opp_wins >= 2:
        score -= 50000

    return score


def _negamax(pos, mask, depth, alpha, beta, deadline, tt, nodes):
    nodes[0] += 1
    if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
        raise TimeoutError

    win_cols = _winning_cols(pos, mask)
    if win_cols:
        return WIN + depth

    if mask == FULL_MASK:
        return 0

    if depth <= 0:
        return _evaluate(pos, mask)

    key = (pos, mask)
    entry = tt.get(key)
    if entry is not None and entry[0] >= depth:
        val, flag = entry[1], entry[2]
        if flag == 0:
            return val
        if flag > 0:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    alpha0 = alpha
    beta0 = beta

    opp = mask ^ pos
    opp_wins = _winning_cols(opp, mask)

    if len(opp_wins) >= 2:
        return -WIN - depth

    if len(opp_wins) == 1:
        move_order = opp_wins
    else:
        move_order = ORDER

    best = -INF

    for c in move_order:
        if not _can_play(mask, c):
            continue

        move = _play_bit(mask, c)
        if not move:
            continue

        if _is_win(pos | move):
            val = WIN + depth
        else:
            val = -_negamax(pos ^ mask, mask | move, depth - 1,
                            -beta, -alpha, deadline, tt, nodes)

        if val > best:
            best = val

        if best > alpha:
            alpha = best

        if alpha >= beta:
            break

    if best == -INF:
        best = 0

    if best <= alpha0:
        flag = -1
    elif best >= beta0:
        flag = 1
    else:
        flag = 0

    if len(tt) < 250000:
        tt[key] = (depth, best, flag)

    return best


def _fallback(board):
    for c in ORDER:
        if 0 <= c < WIDTH and board[0][c] == 0:
            return c
    return 0


def _convert_board(board):
    pos = 0
    mask = 0

    for r_top in range(HEIGHT):
        r = HEIGHT - 1 - r_top
        for c in range(WIDTH):
            v = board[r_top][c]
            if v:
                b = 1 << (c * H1 + r)
                mask |= b
                if v == 1:
                    pos |= b

    return pos, mask


def policy(board: list[list[int]]) -> int:
    try:
        fallback = _fallback(board)
        pos, mask = _convert_board(board)

        legal = [c for c in ORDER if _can_play(mask, c)]
        if not legal:
            return fallback
        if len(legal) == 1:
            return legal[0]

        for c in ORDER:
            if _can_play(mask, c):
                move = _play_bit(mask, c)
                if move and _is_win(pos | move):
                    return c

        opp = mask ^ pos
        opp_wins = _winning_cols(opp, mask)
        if len(opp_wins) == 1:
            return opp_wins[0]
        if len(opp_wins) >= 2:
            return opp_wins[0]

        deadline = time.perf_counter() + TIME_LIMIT
        tt = {}
        nodes = [0]

        best_col = fallback
        best_score = -INF

        remaining = WIDTH * HEIGHT - mask.bit_count()
        max_depth = min(12, remaining)

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            root_order = [best_col] + [c for c in ORDER if c != best_col]
            local_best_col = best_col
            local_best_score = -INF
            alpha = -INF
            beta = INF

            try:
                for c in root_order:
                    if not _can_play(mask, c):
                        continue

                    if time.perf_counter() > deadline:
                        raise TimeoutError

                    move = _play_bit(mask, c)
                    if not move:
                        continue

                    if _is_win(pos | move):
                        return c

                    val = -_negamax(pos ^ mask, mask | move, depth - 1,
                                    -beta, -alpha, deadline, tt, nodes)

                    if (
                        val > local_best_score
                        or (
                            val == local_best_score
                            and abs(c - 3) < abs(local_best_col - 3)
                        )
                    ):
                        local_best_score = val
                        local_best_col = c

                    if val > alpha:
                        alpha = val

                best_col = local_best_col
                best_score = local_best_score

                if best_score >= WIN - 100:
                    break

            except TimeoutError:
                break

        if _can_play(mask, best_col):
            return int(best_col)

        return int(fallback)

    except Exception:
        return int(_fallback(board))
