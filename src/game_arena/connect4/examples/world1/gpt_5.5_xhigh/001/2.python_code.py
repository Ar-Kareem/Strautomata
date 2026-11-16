
from __future__ import annotations
import time

ROWS = 6
COLS = 7
STRIDE = ROWS + 1

INF = 1_000_000_000
WIN = 10_000_000
TIME_LIMIT = 0.92

BOTTOM_MASK = [1 << (c * STRIDE) for c in range(COLS)]
TOP_MASK = [1 << (c * STRIDE + ROWS - 1) for c in range(COLS)]
COL_MASK = [((1 << ROWS) - 1) << (c * STRIDE) for c in range(COLS)]
BOTTOM_ALL = sum(BOTTOM_MASK)
BOARD_MASK = sum(COL_MASK)

ORDER = (3, 2, 4, 1, 5, 0, 6)
ORDER_INDEX = [0] * COLS
for _i, _c in enumerate(ORDER):
    ORDER_INDEX[_c] = _i

COL_WEIGHTS = (3, 4, 5, 7, 5, 4, 3)
BASE_ORDER_SCORE = (3, 4, 5, 7, 5, 4, 3)

LINE_SCORE = (0, 2, 14, 90, 100000)
OPP_LINE_SCORE = (0, 2, 18, 120, 100000)

EXACT = 0
LOWER = 1
UPPER = 2


def _build_windows():
    windows = []

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + r)
            windows.append(m)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << (c * STRIDE + r + i)
            windows.append(m)

    # Diagonal up-right
    for c in range(COLS - 3):
        for r in range(ROWS - 3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + r + i)
            windows.append(m)

    # Diagonal down-right
    for c in range(COLS - 3):
        for r in range(3, ROWS):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * STRIDE + r - i)
            windows.append(m)

    return tuple(windows)


WINDOWS = _build_windows()

_deadline = 0.0
_nodes = 0
_tt = {}
_history = [0] * COLS
_killers = [[-1, -1] for _ in range(64)]


class _Timeout(Exception):
    pass


def _possible(mask: int) -> int:
    return (mask + BOTTOM_ALL) & BOARD_MASK


def _move_bit(mask: int, col: int) -> int:
    return (mask + BOTTOM_MASK[col]) & COL_MASK[col]


def _is_win(pos: int) -> bool:
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True
    m = pos & (pos >> STRIDE)
    if m & (m >> (2 * STRIDE)):
        return True
    m = pos & (pos >> (STRIDE - 1))
    if m & (m >> (2 * (STRIDE - 1))):
        return True
    m = pos & (pos >> (STRIDE + 1))
    return bool(m & (m >> (2 * (STRIDE + 1))))


def _winning_position(position: int, mask: int) -> int:
    # Empty cells that would complete four for position.
    r = (position << 1) & (position << 2) & (position << 3)

    d = STRIDE
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    d = STRIDE - 1
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    d = STRIDE + 1
    p = (position << d) & (position << (2 * d))
    r |= p & (position << (3 * d))
    r |= p & (position >> d)
    p = (position >> d) & (position >> (2 * d))
    r |= p & (position << d)
    r |= p & (position >> (3 * d))

    return r & (BOARD_MASK ^ mask)


def _non_losing_moves(player: int, opp: int, mask: int) -> int:
    possible = _possible(mask)
    opp_win = _winning_position(opp, mask)
    forced = possible & opp_win

    if forced:
        if forced & (forced - 1):
            return 0
        possible = forced

    # Avoid playing directly below an opponent winning square.
    return possible & ~(opp_win >> 1)


def _best_col_from_moves(move_mask: int) -> int:
    for c in ORDER:
        if move_mask & COL_MASK[c]:
            return c
    return 0


def _board_to_bits(board):
    player = 0
    opponent = 0
    for r in range(ROWS):
        row = board[r]
        br = ROWS - 1 - r
        for c in range(COLS):
            v = row[c]
            if v:
                bit = 1 << (c * STRIDE + br)
                if v > 0:
                    player |= bit
                else:
                    opponent |= bit
    return player, opponent


def _simple_legal(board) -> int:
    for c in ORDER:
        try:
            for r in range(ROWS):
                if board[r][c] == 0:
                    return c
        except Exception:
            pass
    return 0


def _evaluate(player: int, opp: int, mask: int, ply: int) -> int:
    possible = _possible(mask)

    wp = _winning_position(player, mask)
    wo = _winning_position(opp, mask)

    playable_p = wp & possible
    if playable_p:
        return WIN - (ply + 1)

    playable_o = wo & possible
    o_count = playable_o.bit_count()
    if o_count >= 2:
        return -WIN + (ply + 2)

    score = 0

    for c in range(COLS):
        score += COL_WEIGHTS[c] * (
            (player & COL_MASK[c]).bit_count() -
            (opp & COL_MASK[c]).bit_count()
        )

    score += 55 * wp.bit_count()
    score -= 65 * wo.bit_count()

    if o_count == 1:
        score -= 1400

    for w in WINDOWS:
        pc = (player & w).bit_count()
        oc = (opp & w).bit_count()

        if pc and oc:
            continue
        if pc:
            score += LINE_SCORE[pc]
        elif oc:
            score -= OPP_LINE_SCORE[oc]

    return score


def _ordered_cols(possible: int, player: int, opp: int, mask: int,
                  tt_col: int, ply: int, depth: int):
    items = []
    for c in ORDER:
        if possible & COL_MASK[c]:
            sc = BASE_ORDER_SCORE[c] * 100 - ORDER_INDEX[c]
            sc += _history[c]

            if c == tt_col:
                sc += 1_000_000

            if ply < len(_killers):
                if c == _killers[ply][0]:
                    sc += 50_000
                elif c == _killers[ply][1]:
                    sc += 25_000

            if depth > 1:
                move = _move_bit(mask, c)
                new_mask = mask | move
                sc += 12 * _winning_position(player | move, new_mask).bit_count()

            items.append((sc, c))

    items.sort(reverse=True)
    return [c for _, c in items]


def _negamax(player: int, opp: int, depth: int, alpha: int, beta: int, ply: int) -> int:
    global _nodes

    _nodes += 1
    if (_nodes & 2047) == 0 and time.perf_counter() >= _deadline:
        raise _Timeout()

    mask = player | opp

    if _is_win(opp):
        return -WIN + ply

    possible = _possible(mask)
    if not possible:
        return 0

    if possible & _winning_position(player, mask):
        return WIN - (ply + 1)

    if depth <= 0:
        return _evaluate(player, opp, mask, ply)

    key = player | (opp << 49)
    alpha_orig = alpha
    beta_orig = beta
    tt_col = -1

    entry = _tt.get(key)
    if entry is not None:
        edepth, eval_score, flag, best_col = entry
        tt_col = best_col
        if edepth >= depth:
            if flag == EXACT:
                return eval_score
            if flag == LOWER:
                if eval_score > alpha:
                    alpha = eval_score
            elif flag == UPPER:
                if eval_score < beta:
                    beta = eval_score
            if alpha >= beta:
                return eval_score

    moves = _non_losing_moves(player, opp, mask)
    if not moves:
        return -WIN + (ply + 2)

    best = -INF
    best_col = -1

    for col in _ordered_cols(moves, player, opp, mask, tt_col, ply, depth):
        move = _move_bit(mask, col)
        score = -_negamax(opp, player | move, depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
            best_col = col

        if score > alpha:
            alpha = score

        if alpha >= beta:
            _history[col] += depth * depth
            if ply < len(_killers) and _killers[ply][0] != col:
                _killers[ply][1] = _killers[ply][0]
                _killers[ply][0] = col
            break

    if best_col < 0:
        return _evaluate(player, opp, mask, ply)

    if best <= alpha_orig:
        flag = UPPER
    elif best >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _tt[key] = (depth, best, flag, best_col)
    return best


def _search_root(player: int, opp: int, depth: int, preferred: int):
    mask = player | opp
    moves = _non_losing_moves(player, opp, mask)
    if not moves:
        moves = _possible(mask)

    cols = _ordered_cols(moves, player, opp, mask, preferred, 0, depth)
    if not cols:
        return preferred, 0

    best_col = cols[0]
    best = -INF
    alpha = -INF
    beta = INF

    for col in cols:
        if time.perf_counter() >= _deadline:
            raise _Timeout()

        move = _move_bit(mask, col)
        score = -_negamax(opp, player | move, depth - 1, -beta, -alpha, 1)

        if score > best:
            best = score
            best_col = col

        if score > alpha:
            alpha = score

        if best > WIN // 2:
            break

    return best_col, best


def _fallback_col(player: int, opp: int, mask: int) -> int:
    possible = _possible(mask)
    if not possible:
        return 0

    win_now = possible & _winning_position(player, mask)
    if win_now:
        return _best_col_from_moves(win_now)

    opp_now = possible & _winning_position(opp, mask)
    if opp_now and not (opp_now & (opp_now - 1)):
        return _best_col_from_moves(opp_now)

    safe = _non_losing_moves(player, opp, mask)
    if safe:
        return _best_col_from_moves(safe)

    return _best_col_from_moves(possible)


def policy(board: list[list[int]]) -> int:
    global _deadline, _nodes, _tt, _history, _killers

    simple_fallback = _simple_legal(board)

    try:
        player, opp = _board_to_bits(board)
        mask = player | opp
        possible = _possible(mask)

        if not possible:
            return simple_fallback

        if possible and not (possible & (possible - 1)):
            return _best_col_from_moves(possible)

        stones = mask.bit_count()

        if stones <= 1 and (possible & COL_MASK[3]):
            return 3

        win_now = possible & _winning_position(player, mask)
        if win_now:
            return _best_col_from_moves(win_now)

        opp_now = possible & _winning_position(opp, mask)
        if opp_now and not (opp_now & (opp_now - 1)):
            return _best_col_from_moves(opp_now)

        fallback = _fallback_col(player, opp, mask)

        _deadline = time.perf_counter() + TIME_LIMIT
        _nodes = 0
        _tt = {}
        _history = [0] * COLS
        _killers = [[-1, -1] for _ in range(64)]

        best_col = fallback
        best_score = -INF
        remaining = 42 - stones

        for depth in range(1, remaining + 1):
            if time.perf_counter() >= _deadline:
                break

            try:
                col, score = _search_root(player, opp, depth, best_col)
            except _Timeout:
                break

            if possible & COL_MASK[col]:
                best_col = col
                best_score = score

            if best_score > WIN // 2:
                break

        if possible & COL_MASK[best_col]:
            return int(best_col)

        return int(_best_col_from_moves(possible))

    except Exception:
        return int(simple_fallback)
