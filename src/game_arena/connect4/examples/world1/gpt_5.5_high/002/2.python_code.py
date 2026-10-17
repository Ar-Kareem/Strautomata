
import time

ROWS = 6
COLS = 7
STRIDE = 7

CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]
COL_PREF = [0, 1, 2, 3, 2, 1, 0]

BOTTOM_MASKS = [1 << (c * STRIDE) for c in range(COLS)]
TOP_MASKS = [1 << (c * STRIDE + ROWS - 1) for c in range(COLS)]
COLUMN_MASKS = [((1 << ROWS) - 1) << (c * STRIDE) for c in range(COLS)]

BOARD_MASK = 0
for _cm in COLUMN_MASKS:
    BOARD_MASK |= _cm

INF = 10**9
WIN_SCORE = 1_000_000

EXACT = 0
LOWER = 1
UPPER = 2

_deadline = 0.0
_nodes = 0
_TT = {}


class _Timeout(Exception):
    pass


def _build_win_masks():
    masks = []

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + r)
            masks.append(m)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << (c * STRIDE + r + i)
            masks.append(m)

    # Diagonal up-right
    for c in range(COLS - 3):
        for r in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + r + i)
            masks.append(m)

    # Diagonal down-right
    for c in range(COLS - 3):
        for r in range(3, ROWS):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + r - i)
            masks.append(m)

    return masks


WIN_MASKS = _build_win_masks()

LINES_BY_INDEX = [[] for _ in range(COLS * STRIDE)]
for _m in WIN_MASKS:
    _x = _m
    while _x:
        _b = _x & -_x
        LINES_BY_INDEX[_b.bit_length() - 1].append(_m)
        _x ^= _b

CELL_WEIGHTS = []
for _c in range(COLS):
    for _r in range(ROWS):
        _idx = _c * STRIDE + _r
        _bit = 1 << _idx
        # Number of possible fours through the square plus center preference.
        _w = 3 * len(LINES_BY_INDEX[_idx]) + 2 * COL_PREF[_c]
        CELL_WEIGHTS.append((_bit, _w))

LINE_SCORE = [0, 2, 12, 80, 0]
OPP_LINE_SCORE = [0, 2, 14, 95, 0]

ORDER_MAKE_SCORE = [0, 1, 8, 55, 500]
ORDER_BLOCK_SCORE = [0, 0, 7, 50, 300]


def _has_won(bb: int) -> bool:
    m = bb & (bb >> 1)
    if m & (m >> 2):
        return True

    m = bb & (bb >> STRIDE)
    if m & (m >> (2 * STRIDE)):
        return True

    m = bb & (bb >> (STRIDE - 1))
    if m & (m >> (2 * (STRIDE - 1))):
        return True

    m = bb & (bb >> (STRIDE + 1))
    if m & (m >> (2 * (STRIDE + 1))):
        return True

    return False


def _play_bit(mask: int, col: int) -> int:
    return (mask + BOTTOM_MASKS[col]) & COLUMN_MASKS[col]


def _legal_cols(mask: int):
    return [c for c in CENTER_ORDER if (mask & TOP_MASKS[c]) == 0]


def _board_to_bits(board):
    cur = 0
    opp = 0

    for br in range(ROWS):
        rb = ROWS - 1 - br
        row = board[br]
        for c in range(COLS):
            v = row[c]
            if v:
                bit = 1 << (c * STRIDE + rb)
                if v > 0:
                    cur |= bit
                else:
                    opp |= bit

    return cur, opp, cur | opp


def _winning_cols(pos: int, mask: int):
    wins = []
    for c in CENTER_ORDER:
        if mask & TOP_MASKS[c]:
            continue
        bit = _play_bit(mask, c)
        if bit and _has_won(pos | bit):
            wins.append(c)
    return wins


def _immediate_win_exists(pos: int, mask: int) -> bool:
    for c in CENTER_ORDER:
        if mask & TOP_MASKS[c]:
            continue
        bit = _play_bit(mask, c)
        if bit and _has_won(pos | bit):
            return True
    return False


def _evaluate(cur: int, opp: int, mask: int) -> int:
    score = 0

    for bit, weight in CELL_WEIGHTS:
        if cur & bit:
            score += weight
        elif opp & bit:
            score -= weight

    for m in WIN_MASKS:
        cm = cur & m
        om = opp & m

        if om == 0:
            score += LINE_SCORE[cm.bit_count()]
        elif cm == 0:
            score -= OPP_LINE_SCORE[om.bit_count()]

    return score


def _move_static_score(cur: int, opp: int, bit: int) -> int:
    idx = bit.bit_length() - 1
    new_cur = cur | bit
    score = 0

    for m in LINES_BY_INDEX[idx]:
        if (m & opp) == 0:
            score += ORDER_MAKE_SCORE[(new_cur & m).bit_count()]
        elif (m & cur) == 0:
            score += ORDER_BLOCK_SCORE[(opp & m).bit_count()]

    return score


def _ordered_cols(cur: int, opp: int, mask: int, tt_col: int = -1):
    good = []
    bad = []

    for c in _legal_cols(mask):
        bit = _play_bit(mask, c)
        if not bit:
            continue

        new_mask = mask | bit
        allows_opp_win = _immediate_win_exists(opp, new_mask)

        s = 10 * COL_PREF[c] + _move_static_score(cur, opp, bit)
        if c == tt_col:
            s += 1_000_000
        if allows_opp_win:
            s -= 100_000

        if allows_opp_win:
            bad.append((s, c))
        else:
            good.append((s, c))

    # If at least one move does not allow an immediate opponent win,
    # exact play never needs the losing moves.
    arr = good if good else bad
    arr.sort(reverse=True)
    return [c for _, c in arr]


def _fallback_move(cur: int, opp: int, mask: int) -> int:
    legal = _legal_cols(mask)
    if not legal:
        return 0

    wins = _winning_cols(cur, mask)
    if wins:
        return wins[0]

    opp_wins = _winning_cols(opp, mask)
    if len(opp_wins) == 1:
        return opp_wins[0]

    safe = []
    for c in legal:
        bit = _play_bit(mask, c)
        if bit and not _immediate_win_exists(opp, mask | bit):
            safe.append(c)

    return safe[0] if safe else legal[0]


def _check_time():
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()


def _negamax(cur: int, opp: int, mask: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    if _has_won(opp):
        return -WIN_SCORE - depth

    if (mask & BOARD_MASK) == BOARD_MASK:
        return 0

    win_cols = _winning_cols(cur, mask)
    if win_cols:
        return WIN_SCORE + depth

    opp_win_cols = _winning_cols(opp, mask)
    if len(opp_win_cols) > 1:
        return -WIN_SCORE - depth

    if depth <= 0:
        val = _evaluate(cur, opp, mask)
        if len(opp_win_cols) == 1:
            val -= 120
        return val

    alpha_orig = alpha
    beta_orig = beta

    key = (cur, opp)
    entry = _TT.get(key)
    tt_col = -1

    if entry is not None:
        e_depth, e_val, e_flag, e_col = entry
        tt_col = e_col
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_val
            if e_flag == LOWER:
                alpha = max(alpha, e_val)
            elif e_flag == UPPER:
                beta = min(beta, e_val)
            if alpha >= beta:
                return e_val

    if len(opp_win_cols) == 1:
        cols = opp_win_cols
    else:
        cols = _ordered_cols(cur, opp, mask, tt_col)

    if not cols:
        return 0

    best_score = -INF
    best_col = cols[0]
    first = True

    for c in cols:
        bit = _play_bit(mask, c)
        if not bit:
            continue

        new_mask = mask | bit
        new_opp = cur | bit

        if _has_won(new_opp):
            score = WIN_SCORE + depth
        else:
            if first:
                score = -_negamax(opp, new_opp, new_mask, depth - 1, -beta, -alpha)
            else:
                # Principal variation search / null-window search.
                score = -_negamax(opp, new_opp, new_mask, depth - 1, -alpha - 1, -alpha)
                if alpha < score < beta:
                    score = -_negamax(opp, new_opp, new_mask, depth - 1, -beta, -alpha)

        first = False

        if score > best_score:
            best_score = score
            best_col = c

        if score > alpha:
            alpha = score

        if alpha >= beta:
            break

    flag = EXACT
    if best_score <= alpha_orig:
        flag = UPPER
    elif best_score >= beta_orig:
        flag = LOWER

    if len(_TT) < 200_000:
        _TT[key] = (depth, best_score, flag, best_col)

    return best_score


def _root_search(cur: int, opp: int, mask: int, depth: int, preferred: int):
    cols = _ordered_cols(cur, opp, mask, preferred)
    if not cols:
        cols = _legal_cols(mask)

    best_col = cols[0]
    best_score = -INF
    alpha = -INF

    for c in cols:
        if time.perf_counter() > _deadline:
            raise _Timeout()

        bit = _play_bit(mask, c)
        if not bit:
            continue

        new_mask = mask | bit
        new_opp = cur | bit

        if _has_won(new_opp):
            score = WIN_SCORE + depth
        else:
            score = -_negamax(opp, new_opp, new_mask, depth - 1, -INF, -alpha)

        if score > best_score:
            best_score = score
            best_col = c

        if score > alpha:
            alpha = score

    return best_score, best_col


def _emergency_move(board) -> int:
    for c in CENTER_ORDER:
        try:
            if board[0][c] == 0:
                return int(c)
        except Exception:
            pass
    return 0


def policy(board: list[list[int]]) -> int:
    global _deadline, _nodes, _TT

    try:
        cur, opp, mask = _board_to_bits(board)
        legal = _legal_cols(mask)

        if not legal:
            return _emergency_move(board)

        if len(legal) == 1:
            return int(legal[0])

        # Perfect opening on an empty board.
        if mask == 0 and 3 in legal:
            return 3

        # Immediate tactical necessities.
        my_wins = _winning_cols(cur, mask)
        if my_wins:
            return int(my_wins[0])

        opp_wins = _winning_cols(opp, mask)
        if len(opp_wins) == 1:
            return int(opp_wins[0])

        best = _fallback_move(cur, opp, mask)
        preferred = best

        _deadline = time.perf_counter() + 0.90
        _nodes = 0
        _TT = {}

        empties = 42 - mask.bit_count()
        if empties > 30:
            max_depth = 10
        elif empties > 18:
            max_depth = 12
        else:
            max_depth = min(18, empties)

        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _deadline:
                break

            try:
                score, col = _root_search(cur, opp, mask, depth, preferred)
            except _Timeout:
                break

            if col in legal:
                best = col
                preferred = col

            # A proven tactical win has been found.
            if score >= WIN_SCORE // 2:
                break

        if best not in legal:
            best = legal[0]

        return int(best)

    except Exception:
        return _emergency_move(board)
