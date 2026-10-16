
import time

ROWS = 6
COLS = 7
STRIDE = 7

ORDER = [3, 2, 4, 1, 5, 0, 6]

BOTTOM_MASK = [1 << (c * STRIDE) for c in range(COLS)]
TOP_MASK = [1 << (c * STRIDE + ROWS - 1) for c in range(COLS)]
COLUMN_MASK = [((1 << ROWS) - 1) << (c * STRIDE) for c in range(COLS)]

FULL_MASK = 0
for c in range(COLS):
    FULL_MASK |= COLUMN_MASK[c]

CENTER_MASK = COLUMN_MASK[3]

WIN_MASKS = []
for c in range(COLS):
    for r in range(ROWS):
        for dc, dr in ((1, 0), (0, 1), (1, 1), (1, -1)):
            c2 = c + 3 * dc
            r2 = r + 3 * dr
            if 0 <= c2 < COLS and 0 <= r2 < ROWS:
                m = 0
                for k in range(4):
                    m |= 1 << ((c + k * dc) * STRIDE + (r + k * dr))
                WIN_MASKS.append(m)

INF = 10 ** 9
WIN_SCORE = 1_000_000

_TT = {}
_DEADLINE = 0.0
_NODES = 0


def _has_won(bb: int) -> bool:
    m = bb & (bb >> 1)
    if m & (m >> 2):
        return True

    m = bb & (bb >> 7)
    if m & (m >> 14):
        return True

    m = bb & (bb >> 6)
    if m & (m >> 12):
        return True

    m = bb & (bb >> 8)
    if m & (m >> 16):
        return True

    return False


def _board_to_bits(board):
    p1 = 0
    p2 = 0

    for r in range(ROWS):
        for c in range(COLS):
            v = board[r][c]
            bit = 1 << (c * STRIDE + (ROWS - 1 - r))
            if v == 1:
                p1 |= bit
            elif v == -1:
                p2 |= bit

    return p1, p2, p1 | p2


def _is_legal(mask: int, col: int) -> bool:
    return (mask & TOP_MASK[col]) == 0


def _move_bit(mask: int, col: int) -> int:
    return (mask + BOTTOM_MASK[col]) & COLUMN_MASK[col]


def _legal_moves(mask: int, preferred: int = -1):
    moves = []

    if 0 <= preferred < COLS and _is_legal(mask, preferred):
        moves.append(preferred)

    for c in ORDER:
        if c != preferred and _is_legal(mask, c):
            moves.append(c)

    return moves


def _evaluate(p1: int, p2: int) -> int:
    score = 0

    score += 5 * ((p1 & CENTER_MASK).bit_count() - (p2 & CENTER_MASK).bit_count())

    my_score = (0, 2, 14, 90, 0)
    opp_score = (0, 2, 16, 110, 0)

    for m in WIN_MASKS:
        a = (p1 & m).bit_count()
        b = (p2 & m).bit_count()

        if a and b:
            continue

        if a:
            score += my_score[a]
        elif b:
            score -= opp_score[b]

    return score


def _alphabeta(p1: int, p2: int, mask: int, depth: int, alpha: int, beta: int, side: int) -> int:
    global _NODES

    _NODES += 1
    if (_NODES & 2047) == 0 and time.perf_counter() > _DEADLINE:
        raise TimeoutError

    if _has_won(p1):
        return WIN_SCORE + depth
    if _has_won(p2):
        return -WIN_SCORE - depth
    if mask == FULL_MASK:
        return 0
    if depth <= 0:
        return _evaluate(p1, p2)

    key = (p1, p2, side)
    entry = _TT.get(key)

    if entry is not None and entry[0] >= depth:
        stored_depth, stored_value, stored_flag = entry
        if stored_flag == 0:
            return stored_value
        if stored_flag == 1:
            alpha = max(alpha, stored_value)
        elif stored_flag == 2:
            beta = min(beta, stored_value)
        if alpha >= beta:
            return stored_value

    original_alpha = alpha
    original_beta = beta

    if side == 1:
        value = -INF

        for col in _legal_moves(mask):
            bit = _move_bit(mask, col)
            new_p1 = p1 | bit
            new_mask = mask | bit

            if _has_won(new_p1):
                child_value = WIN_SCORE + depth
            else:
                child_value = _alphabeta(new_p1, p2, new_mask, depth - 1, alpha, beta, -1)

            if child_value > value:
                value = child_value
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

    else:
        value = INF

        for col in _legal_moves(mask):
            bit = _move_bit(mask, col)
            new_p2 = p2 | bit
            new_mask = mask | bit

            if _has_won(new_p2):
                child_value = -WIN_SCORE - depth
            else:
                child_value = _alphabeta(p1, new_p2, new_mask, depth - 1, alpha, beta, 1)

            if child_value < value:
                value = child_value
            if value < beta:
                beta = value
            if alpha >= beta:
                break

    if value <= original_alpha:
        flag = 2
    elif value >= original_beta:
        flag = 1
    else:
        flag = 0

    _TT[key] = (depth, value, flag)
    return value


def _fallback(board):
    for c in ORDER:
        if 0 <= c < COLS and board[0][c] == 0:
            return c

    for c in range(COLS):
        if board[0][c] == 0:
            return c

    return 0


def policy(board: list[list[int]]) -> int:
    global _TT, _DEADLINE, _NODES

    fallback = _fallback(board)

    try:
        p1, p2, mask = _board_to_bits(board)

        legal = _legal_moves(mask)
        if not legal:
            return fallback

        fallback = legal[0]

        # Immediate winning move.
        for col in legal:
            bit = _move_bit(mask, col)
            if _has_won(p1 | bit):
                return col

        # Forced block of opponent's immediate win.
        opponent_wins = []
        for col in legal:
            bit = _move_bit(mask, col)
            if _has_won(p2 | bit):
                opponent_wins.append(col)

        if len(opponent_wins) == 1:
            return opponent_wins[0]

        _TT = {}
        _NODES = 0
        _DEADLINE = time.perf_counter() + 0.88

        best_col = fallback
        max_depth = 11

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break

            current_best = best_col
            best_value = -INF
            alpha = -INF
            beta = INF

            try:
                for col in _legal_moves(mask, best_col):
                    if time.perf_counter() > _DEADLINE:
                        raise TimeoutError

                    bit = _move_bit(mask, col)
                    new_p1 = p1 | bit
                    new_mask = mask | bit

                    if _has_won(new_p1):
                        value = WIN_SCORE + depth
                    else:
                        value = _alphabeta(new_p1, p2, new_mask, depth - 1, alpha, beta, -1)

                    if value > best_value:
                        best_value = value
                        current_best = col

                    if value > alpha:
                        alpha = value

                best_col = current_best

                if best_value >= WIN_SCORE:
                    break

            except TimeoutError:
                break

        if 0 <= best_col < COLS and board[0][best_col] == 0:
            return best_col

        return fallback

    except Exception:
        return fallback
