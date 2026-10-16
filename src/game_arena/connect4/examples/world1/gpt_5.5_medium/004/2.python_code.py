
import time

ROWS = 6
COLS = 7
HEIGHT = 7  # 6 playable cells + 1 sentinel bit per column

ORDER = (3, 4, 2, 5, 1, 6, 0)

BOTTOM_MASKS = tuple(1 << (c * HEIGHT) for c in range(COLS))
TOP_MASKS = tuple(1 << (c * HEIGHT + ROWS - 1) for c in range(COLS))
COL_MASKS = tuple(((1 << ROWS) - 1) << (c * HEIGHT) for c in range(COLS))
CENTER_MASK = COL_MASKS[3]

INF = 10**9
WIN_SCORE = 1_000_000

TT = {}
START_TIME = 0.0
TIME_LIMIT = 0.86
NODES = 0


class _Timeout(Exception):
    pass


def _bit(c, r):
    return 1 << (c * HEIGHT + r)


def _make_windows():
    masks = []
    dirs = ((1, 0), (0, 1), (1, 1), (1, -1))
    for c in range(COLS):
        for r in range(ROWS):
            for dc, dr in dirs:
                c2 = c + 3 * dc
                r2 = r + 3 * dr
                if 0 <= c2 < COLS and 0 <= r2 < ROWS:
                    m = 0
                    for k in range(4):
                        m |= _bit(c + k * dc, r + k * dr)
                    masks.append(m)
    return tuple(masks)


WINDOWS = _make_windows()


def _has_won(pos):
    # vertical
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True

    # horizontal
    m = pos & (pos >> HEIGHT)
    if m & (m >> (2 * HEIGHT)):
        return True

    # diagonal /
    m = pos & (pos >> (HEIGHT - 1))
    if m & (m >> (2 * (HEIGHT - 1))):
        return True

    # diagonal \
    m = pos & (pos >> (HEIGHT + 1))
    if m & (m >> (2 * (HEIGHT + 1))):
        return True

    return False


def _convert(board):
    cur = 0
    opp = 0
    mask = 0

    for rt in range(ROWS):
        br = ROWS - 1 - rt
        row = board[rt]
        for c in range(COLS):
            v = row[c]
            if v:
                b = _bit(c, br)
                mask |= b
                if v == 1:
                    cur |= b
                else:
                    opp |= b

    return cur, opp, mask


def _legal_cols(mask):
    return [c for c in ORDER if (mask & TOP_MASKS[c]) == 0]


def _move_bit(mask, col):
    return (mask + BOTTOM_MASKS[col]) & COL_MASKS[col]


def _winning_cols(pos, mask):
    wins = []
    for c in ORDER:
        if mask & TOP_MASKS[c]:
            continue
        mv = _move_bit(mask, c)
        if _has_won(pos | mv):
            wins.append(c)
    return wins


def _playable_bits(mask):
    bits = 0
    for c in ORDER:
        if (mask & TOP_MASKS[c]) == 0:
            bits |= _move_bit(mask, c)
    return bits


def _evaluate(cur, opp, mask):
    if _has_won(cur):
        return WIN_SCORE
    if _has_won(opp):
        return -WIN_SCORE

    score = 0

    # Center control is very important in Connect 4.
    score += 8 * ((cur & CENTER_MASK).bit_count())
    score -= 8 * ((opp & CENTER_MASK).bit_count())

    playable = _playable_bits(mask)

    for w in WINDOWS:
        cp = (cur & w).bit_count()
        op = (opp & w).bit_count()

        if cp and op:
            continue

        if op == 0:
            if cp == 1:
                score += 3
            elif cp == 2:
                score += 18
            elif cp == 3:
                empty = w & ~mask
                score += 170 if (empty & playable) else 65
            elif cp == 4:
                score += WIN_SCORE

        elif cp == 0:
            if op == 1:
                score -= 3
            elif op == 2:
                score -= 20
            elif op == 3:
                empty = w & ~mask
                score -= 210 if (empty & playable) else 80
            elif op == 4:
                score -= WIN_SCORE

    my_wins = len(_winning_cols(cur, mask))
    op_wins = len(_winning_cols(opp, mask))

    score += 450 * my_wins
    score -= 600 * op_wins

    if my_wins >= 2:
        score += 3500
    if op_wins >= 2:
        score -= 4500

    return score


def _ordered_moves(legal, tt_move=None):
    if tt_move in legal:
        return sorted(legal, key=lambda c: 0 if c == tt_move else 10 + abs(c - 3))
    return sorted(legal, key=lambda c: abs(c - 3))


def _negamax(cur, opp, mask, depth, alpha, beta, ply):
    global NODES

    NODES += 1
    if (NODES & 1023) == 0:
        if time.perf_counter() - START_TIME > TIME_LIMIT:
            raise _Timeout()

    if _has_won(opp):
        return -WIN_SCORE + ply

    legal = _legal_cols(mask)
    if not legal:
        return 0

    # If the side to move can win immediately, do so.
    for c in legal:
        mv = _move_bit(mask, c)
        if _has_won(cur | mv):
            return WIN_SCORE - ply

    # If opponent has immediate winning threats, they must be blocked.
    opp_wins = []
    for c in legal:
        mv = _move_bit(mask, c)
        if _has_won(opp | mv):
            opp_wins.append(c)

    if len(opp_wins) > 1:
        return -WIN_SCORE + ply
    if len(opp_wins) == 1:
        legal = [opp_wins[0]]

    if depth <= 0:
        return _evaluate(cur, opp, mask)

    key = (cur, opp)
    alpha0 = alpha
    beta0 = beta
    tt_move = None

    entry = TT.get(key)
    if entry is not None and entry[0] >= depth:
        _, val, flag, stored_move = entry
        tt_move = stored_move
        if flag == 0:
            return val
        elif flag == 1:
            alpha = max(alpha, val)
        else:
            beta = min(beta, val)

        if alpha >= beta:
            return val
    elif entry is not None:
        tt_move = entry[3]

    best = -INF
    best_col = legal[0]

    for c in _ordered_moves(legal, tt_move):
        mv = _move_bit(mask, c)
        val = -_negamax(opp, cur | mv, mask | mv, depth - 1, -beta, -alpha, ply + 1)

        if val > best:
            best = val
            best_col = c

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best <= alpha0:
        flag = 2  # upper bound
    elif best >= beta0:
        flag = 1  # lower bound
    else:
        flag = 0  # exact

    TT[key] = (depth, best, flag, best_col)
    return best


def _fallback_move(cur, opp, mask, legal):
    # Prefer moves that do not allow an immediate opponent win.
    candidates = []
    for c in legal:
        mv = _move_bit(mask, c)
        new_mask = mask | mv
        if not _winning_cols(opp, new_mask):
            candidates.append(c)

    if not candidates:
        candidates = legal

    best_col = candidates[0]
    best_score = -INF

    for c in candidates:
        mv = _move_bit(mask, c)
        val = _evaluate(cur | mv, opp, mask | mv)
        val += 6 * (3 - abs(c - 3))

        if val > best_score:
            best_score = val
            best_col = c

    return best_col


def _ensure_legal(board, col):
    try:
        if 0 <= col < COLS and board[0][col] == 0:
            return int(col)
        for c in ORDER:
            if board[0][c] == 0:
                return int(c)
    except Exception:
        pass
    return 0


def policy(board: list[list[int]]) -> int:
    global TT, START_TIME, NODES

    selected = 3

    try:
        cur, opp, mask = _convert(board)
        legal = _legal_cols(mask)

        if not legal:
            return _ensure_legal(board, selected)

        selected = _fallback_move(cur, opp, mask, legal)

        # Take an immediate win.
        for c in legal:
            mv = _move_bit(mask, c)
            if _has_won(cur | mv):
                return _ensure_legal(board, c)

        # Block a single immediate opponent win.
        opp_wins = _winning_cols(opp, mask)
        if len(opp_wins) == 1:
            return _ensure_legal(board, opp_wins[0])

        TT = {}
        NODES = 0
        START_TIME = time.perf_counter()

        filled = mask.bit_count()
        empties = ROWS * COLS - filled

        if empties <= 10:
            max_depth = empties
        elif empties <= 18:
            max_depth = 12
        else:
            max_depth = 10

        last_best = selected

        for depth in range(1, max_depth + 1):
            if time.perf_counter() - START_TIME > TIME_LIMIT:
                break

            local_best = last_best
            local_val = -INF
            alpha = -INF
            beta = INF

            root_order = _ordered_moves(legal, last_best)

            for c in root_order:
                if time.perf_counter() - START_TIME > TIME_LIMIT:
                    raise _Timeout()

                mv = _move_bit(mask, c)
                val = -_negamax(opp, cur | mv, mask | mv, depth - 1, -beta, -alpha, 1)

                if val > local_val:
                    local_val = val
                    local_best = c

                if val > alpha:
                    alpha = val

            selected = local_best
            last_best = local_best

            # Found a forced win; no need to search deeper.
            if local_val > WIN_SCORE // 2:
                break

    except _Timeout:
        pass
    except Exception:
        pass

    return _ensure_legal(board, selected)
