
from time import perf_counter

WIDTH = 7
HEIGHT = 6
H1 = HEIGHT + 1
KEY_SHIFT = WIDTH * H1

ORDER = (3, 4, 2, 5, 1, 6, 0)
COL_PREF = (3, 4, 5, 8, 5, 4, 3)

BOTTOM_MASK = tuple(1 << (c * H1) for c in range(WIDTH))
TOP_MASK = tuple(1 << (c * H1 + HEIGHT - 1) for c in range(WIDTH))
COL_MASK = tuple(((1 << HEIGHT) - 1) << (c * H1) for c in range(WIDTH))
FULL_TOP_MASK = sum(TOP_MASK)
CENTER_MASK = COL_MASK[3]
NEAR_CENTER_MASK = COL_MASK[2] | COL_MASK[4]

WIN_BASE = 1_000_000
INF = 10_000_000
TIME_LIMIT = 0.85


def _make_windows():
    windows = []
    cell_windows = [[] for _ in range(WIDTH * H1)]

    def add_window(cells):
        m = 0
        for c, r in cells:
            m |= 1 << (c * H1 + r)
        windows.append(m)
        for c, r in cells:
            cell_windows[c * H1 + r].append(m)

    # Horizontal
    for r in range(HEIGHT):
        for c in range(WIDTH - 3):
            add_window([(c + i, r) for i in range(4)])

    # Vertical
    for c in range(WIDTH):
        for r in range(HEIGHT - 3):
            add_window([(c, r + i) for i in range(4)])

    # Diagonal up-right
    for c in range(WIDTH - 3):
        for r in range(HEIGHT - 3):
            add_window([(c + i, r + i) for i in range(4)])

    # Diagonal down-right
    for c in range(WIDTH - 3):
        for r in range(3, HEIGHT):
            add_window([(c + i, r - i) for i in range(4)])

    return tuple(windows), tuple(tuple(x) for x in cell_windows)


WINDOWS, CELL_WINDOWS = _make_windows()


def _board_to_bitboards(board):
    position = 0
    mask = 0

    for row_index in range(HEIGHT):
        bit_row = HEIGHT - 1 - row_index
        row = board[row_index]
        for c in range(WIDTH):
            v = row[c]
            if v:
                bit = 1 << (c * H1 + bit_row)
                mask |= bit
                if v > 0:
                    position |= bit

    return position, mask


def _is_win(pos):
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True

    m = pos & (pos >> H1)
    if m & (m >> (2 * H1)):
        return True

    m = pos & (pos >> (H1 - 1))
    if m & (m >> (2 * (H1 - 1))):
        return True

    m = pos & (pos >> (H1 + 1))
    if m & (m >> (2 * (H1 + 1))):
        return True

    return False


def _is_winning_move(position, mask, col):
    move = (mask + BOTTOM_MASK[col]) & COL_MASK[col]
    return bool(move and _is_win(position | move))


def _has_winning_move(position, mask):
    for c in ORDER:
        if not (mask & TOP_MASK[c]) and _is_winning_move(position, mask, c):
            return True
    return False


def _winning_columns(position, mask):
    return [
        c for c in ORDER
        if not (mask & TOP_MASK[c]) and _is_winning_move(position, mask, c)
    ]


def _evaluate(position, mask):
    opponent = mask ^ position

    score = 0
    score += 7 * ((position & CENTER_MASK).bit_count() - (opponent & CENTER_MASK).bit_count())
    score += 2 * ((position & NEAR_CENTER_MASK).bit_count() - (opponent & NEAR_CENTER_MASK).bit_count())

    playable = 0
    for c in range(WIDTH):
        if not (mask & TOP_MASK[c]):
            playable |= (mask + BOTTOM_MASK[c]) & COL_MASK[c]

    for w in WINDOWS:
        p = (position & w).bit_count()
        o = (opponent & w).bit_count()

        if p and o:
            continue

        empty_playable = (w & ~mask) & playable

        if p:
            if p == 3:
                score += 120
                if empty_playable:
                    score += 600
            elif p == 2:
                score += 25
                if empty_playable:
                    score += 10
            elif p == 1:
                score += 3

        elif o:
            if o == 3:
                score -= 140
                if empty_playable:
                    score -= 750
            elif o == 2:
                score -= 32
                if empty_playable:
                    score -= 12
            elif o == 1:
                score -= 3

    return score


def _ordered_moves(position, mask):
    opponent = mask ^ position
    child_position_base = opponent
    scored = []

    for c in ORDER:
        if mask & TOP_MASK[c]:
            continue

        move = (mask + BOTTOM_MASK[c]) & COL_MASK[c]
        if not move:
            continue

        idx = move.bit_length() - 1
        s = COL_PREF[c]

        # Prefer moves that extend our clean lines or block opponent clean lines.
        for w in CELL_WINDOWS[idx]:
            if not (w & opponent):
                cnt = (position & w).bit_count()
                s += 4 * (cnt + 1) * (cnt + 1)

            if not (w & position):
                ocnt = (opponent & w).bit_count()
                s += 5 * ocnt * ocnt

        # Strongly delay moves that immediately give the opponent a win.
        if _has_winning_move(child_position_base, mask | move):
            s -= 10000

        scored.append((s, c))

    scored.sort(reverse=True)
    return [c for _, c in scored]


def _fallback_move(position, mask, legal):
    child_position_base = position ^ mask
    safe = []

    for c in legal:
        move = (mask + BOTTOM_MASK[c]) & COL_MASK[c]
        if move and not _has_winning_move(child_position_base, mask | move):
            safe.append(c)

    preferred = safe if safe else legal

    for c in _ordered_moves(position, mask):
        if c in preferred:
            return c

    return preferred[0]


def policy(board: list[list[int]]) -> int:
    try:
        position, mask = _board_to_bitboards(board)
        legal = [c for c in ORDER if not (mask & TOP_MASK[c])]

        if not legal:
            return 0

        # Very small opening book: center is the strongest opening area.
        if mask.bit_count() <= 1 and not (mask & TOP_MASK[3]):
            return 3

        # Win immediately if possible.
        wins = _winning_columns(position, mask)
        if wins:
            return int(wins[0])

        # If opponent has exactly one immediate win, blocking is mandatory.
        opponent = mask ^ position
        opp_wins = _winning_columns(opponent, mask)
        if len(opp_wins) == 1:
            return int(opp_wins[0])

        best_col = _fallback_move(position, mask, legal)
        deadline = perf_counter() + TIME_LIMIT
        table = {}
        nodes = 0

        def negamax(pos, msk, depth, alpha, beta):
            nonlocal nodes

            nodes += 1
            if (nodes & 511) == 0 and perf_counter() > deadline:
                raise TimeoutError

            # If the side to move can win now, this node is decisive.
            if _has_winning_move(pos, msk):
                return WIN_BASE + depth

            if (msk & FULL_TOP_MASK) == FULL_TOP_MASK:
                return 0

            if depth <= 0:
                return _evaluate(pos, msk)

            key = pos | (msk << KEY_SHIFT)
            entry = table.get(key)
            tt_move = -1

            if entry is not None:
                entry_depth, flag, value, stored_move = entry
                tt_move = stored_move

                if entry_depth >= depth:
                    if flag == 0:       # Exact
                        return value
                    elif flag == 1:     # Lower bound
                        if value > alpha:
                            alpha = value
                    else:               # Upper bound
                        if value < beta:
                            beta = value

                    if alpha >= beta:
                        return value

            alpha_start = alpha
            beta_start = beta

            opp = msk ^ pos
            immediate_opp_wins = _winning_columns(opp, msk)

            # If opponent has two immediate winning columns and we cannot win now,
            # the position is lost.
            if len(immediate_opp_wins) >= 2:
                value = -WIN_BASE - depth
                table[key] = (depth, 0, value, immediate_opp_wins[0])
                return value

            if len(immediate_opp_wins) == 1:
                moves = immediate_opp_wins
            else:
                moves = _ordered_moves(pos, msk)
                if tt_move in moves:
                    moves.remove(tt_move)
                    moves.insert(0, tt_move)

            if not moves:
                return 0

            best_value = -INF
            best_move = moves[0]
            next_pos_base = opp

            for c in moves:
                move = (msk + BOTTOM_MASK[c]) & COL_MASK[c]
                if not move:
                    continue

                value = -negamax(next_pos_base, msk | move, depth - 1, -beta, -alpha)

                if value > best_value:
                    best_value = value
                    best_move = c

                if value > alpha:
                    alpha = value

                if alpha >= beta:
                    break

            if best_value == -INF:
                best_value = 0

            if best_value <= alpha_start:
                flag = 2      # Upper bound
            elif best_value >= beta_start:
                flag = 1      # Lower bound
            else:
                flag = 0      # Exact

            table[key] = (depth, flag, best_value, best_move)
            return best_value

        remaining = 42 - mask.bit_count()
        best_score = -INF

        for depth in range(1, remaining + 1):
            if perf_counter() > deadline:
                break

            try:
                moves = _ordered_moves(position, mask)
                if best_col in moves:
                    moves.remove(best_col)
                    moves.insert(0, best_col)

                current_best_col = best_col
                current_best_score = -INF
                alpha = -INF
                beta = INF
                next_position_base = position ^ mask

                for c in moves:
                    if (nodes & 511) == 0 and perf_counter() > deadline:
                        raise TimeoutError

                    move = (mask + BOTTOM_MASK[c]) & COL_MASK[c]
                    if not move:
                        continue

                    if _is_win(position | move):
                        score = WIN_BASE + depth
                    else:
                        score = -negamax(next_position_base, mask | move, depth - 1, -beta, -alpha)

                    if score > current_best_score:
                        current_best_score = score
                        current_best_col = c

                    if score > alpha:
                        alpha = score

                if current_best_col in legal:
                    best_col = current_best_col
                    best_score = current_best_score

                # A proven forced win within the searched horizon is enough.
                if best_score >= WIN_BASE:
                    break

            except TimeoutError:
                break

        if best_col not in legal:
            best_col = legal[0]

        return int(best_col)

    except Exception:
        # Last-resort safety net: always return a non-full column if one exists.
        for c in ORDER:
            try:
                if board[0][c] == 0:
                    return int(c)
            except Exception:
                pass
        return 0
