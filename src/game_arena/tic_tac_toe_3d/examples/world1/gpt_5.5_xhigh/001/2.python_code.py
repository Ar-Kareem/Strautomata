
from __future__ import annotations

from functools import lru_cache
from time import perf_counter


# ---------- Board geometry ----------

_COORDS = tuple((i, j, k) for i in range(3) for j in range(3) for k in range(3))
_ALL_MASK = (1 << 27) - 1
_CENTER_INDEX = 13
_CENTER_BIT = 1 << _CENTER_INDEX

_WIN_SCORE = 100000
_INF = 10**9
_TIME_BUDGET = 0.80

_MINE_LINE_SCORE = (0, 9, 170, _WIN_SCORE)
_OPP_LINE_SCORE = (0, 10, 190, _WIN_SCORE)
_EVAL_LIMIT = _WIN_SCORE - 1000


def _index(i: int, j: int, k: int) -> int:
    return i * 9 + j * 3 + k


def _inside(i: int, j: int, k: int) -> bool:
    return 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3


# Unique line directions in a 3x3x3 cube.
_DIRECTIONS = []
for _dx in (-1, 0, 1):
    for _dy in (-1, 0, 1):
        for _dz in (-1, 0, 1):
            if _dx == 0 and _dy == 0 and _dz == 0:
                continue
            _first = _dx if _dx != 0 else (_dy if _dy != 0 else _dz)
            if _first > 0:
                _DIRECTIONS.append((_dx, _dy, _dz))

# All 49 winning lines.
_line_masks = set()
for _i, _j, _k in _COORDS:
    for _dx, _dy, _dz in _DIRECTIONS:
        if _inside(_i - _dx, _j - _dy, _k - _dz):
            continue
        _i2, _j2, _k2 = _i + 2 * _dx, _j + 2 * _dy, _k + 2 * _dz
        if _inside(_i2, _j2, _k2):
            _mask = 0
            for _t in range(3):
                _mask |= 1 << _index(_i + _t * _dx, _j + _t * _dy, _k + _t * _dz)
            _line_masks.add(_mask)

_WIN_MASKS = tuple(_line_masks)

_cell_lines_list = [[] for _ in range(27)]
for _line in _WIN_MASKS:
    _m = _line
    while _m:
        _b = _m & -_m
        _cell_lines_list[_b.bit_length() - 1].append(_line)
        _m ^= _b

_CELL_LINES = tuple(tuple(x) for x in _cell_lines_list)

_cell_values = []
for _idx, (_i, _j, _k) in enumerate(_COORDS):
    _extremes = int(_i != 1) + int(_j != 1) + int(_k != 1)
    _value = len(_CELL_LINES[_idx]) * 18 + _extremes * 3
    if _idx == _CENTER_INDEX:
        _value += 80
    _cell_values.append(_value)
_CELL_VALUE = tuple(_cell_values)


# ---------- Tactical helpers ----------

@lru_cache(maxsize=262144)
def _is_win(bits: int) -> bool:
    if bits.bit_count() < 3:
        return False
    for line in _WIN_MASKS:
        if (bits & line) == line:
            return True
    return False


@lru_cache(maxsize=262144)
def _winning_moves(bits: int, empty: int) -> int:
    """Cells that immediately complete a line for this bitboard."""
    if empty == 0 or bits.bit_count() < 2:
        return 0

    result = 0
    for line in _WIN_MASKS:
        e = line & empty
        if e and (e & (e - 1)) == 0 and ((line & bits).bit_count() == 2):
            result |= e
    return result


@lru_cache(maxsize=262144)
def _fork_moves(bits: int, empty: int) -> int:
    """Moves that create at least two distinct immediate winning cells."""
    if empty == 0 or bits.bit_count() < 2:
        return 0

    result = 0
    m = empty
    while m:
        b = m & -m
        m ^= b
        new_bits = bits | b
        if _is_win(new_bits):
            continue
        threats = _winning_moves(new_bits, empty ^ b)
        if threats.bit_count() >= 2:
            result |= b
    return result


@lru_cache(maxsize=131072)
def _threat_to_fork_moves(bits: int, enemy: int, empty: int) -> int:
    """
    Conservative forcing trap:
    play a move that creates exactly one immediate threat; opponent is forced
    to block it; after that block, we have a fork and the opponent has no
    immediate win.
    """
    if empty == 0 or bits.bit_count() < 1:
        return 0

    result = 0
    m = empty
    while m:
        b = m & -m
        m ^= b

        new_bits = bits | b
        if _is_win(new_bits):
            continue

        empty_after_move = empty ^ b
        threats = _winning_moves(new_bits, empty_after_move)

        if threats and (threats & (threats - 1)) == 0:
            forced_block = threats
            empty_after_block = empty_after_move ^ forced_block
            enemy_after_block = enemy | forced_block

            if _is_win(enemy_after_block):
                continue
            if _winning_moves(enemy_after_block, empty_after_block):
                continue
            if _fork_moves(new_bits, empty_after_block):
                result |= b

    return result


# ---------- Evaluation and move ordering ----------

@lru_cache(maxsize=131072)
def _evaluate(me: int, opp: int) -> int:
    empty = _ALL_MASK & ~(me | opp)

    if _is_win(me):
        return _WIN_SCORE + empty.bit_count()
    if _is_win(opp):
        return -_WIN_SCORE - empty.bit_count()

    score = 0

    for line in _WIN_MASKS:
        mc = (me & line).bit_count()
        oc = (opp & line).bit_count()

        if oc == 0:
            score += _MINE_LINE_SCORE[mc]
        elif mc == 0:
            score -= _OPP_LINE_SCORE[oc]

    m = me
    while m:
        b = m & -m
        m ^= b
        score += _CELL_VALUE[b.bit_length() - 1]

    m = opp
    while m:
        b = m & -m
        m ^= b
        score -= _CELL_VALUE[b.bit_length() - 1]

    ecount = empty.bit_count()

    if ecount <= 22:
        if me.bit_count() >= 2:
            score += 300 * _fork_moves(me, empty).bit_count()
        if opp.bit_count() >= 2:
            score -= 340 * _fork_moves(opp, empty).bit_count()

    if ecount <= 18:
        if me.bit_count() >= 1:
            score += 180 * _threat_to_fork_moves(me, opp, empty).bit_count()
        if opp.bit_count() >= 1:
            score -= 220 * _threat_to_fork_moves(opp, me, empty).bit_count()

    if score > _EVAL_LIMIT:
        return _EVAL_LIMIT
    if score < -_EVAL_LIMIT:
        return -_EVAL_LIMIT
    return score


def _ordered_moves(mask: int, me: int, opp: int, empty: int) -> list[int]:
    mask &= empty
    if mask == 0:
        return []

    ecount = empty.bit_count()

    opp_forks = 0
    my_traps = 0
    if ecount <= 18:
        if opp.bit_count() >= 2:
            opp_forks = _fork_moves(opp, empty)
        if me.bit_count() >= 1:
            my_traps = _threat_to_fork_moves(me, opp, empty)

    items = []
    m = mask
    while m:
        b = m & -m
        m ^= b
        idx = b.bit_length() - 1

        score = _CELL_VALUE[idx]

        if b & opp_forks:
            score += 20000
        if b & my_traps:
            score += 40000

        new_me = me | b
        empty_after = empty ^ b
        threats = _winning_moves(new_me, empty_after)
        threat_count = threats.bit_count()

        if threat_count >= 2:
            score += 60000
        elif threat_count == 1:
            score += 1800

        for line in _CELL_LINES[idx]:
            if (line & opp) == 0:
                c = (line & me).bit_count()
                if c == 2:
                    score += 9000
                elif c == 1:
                    score += 160
                else:
                    score += 6

            if (line & me) == 0:
                c = (line & opp).bit_count()
                if c == 2:
                    score += 8500
                elif c == 1:
                    score += 130

        items.append((score, b))

    items.sort(reverse=True)
    return [b for _, b in items]


def _choose_best_bit(mask: int, me: int, opp: int, empty: int) -> int:
    mask &= empty
    if mask == 0:
        return empty & -empty
    moves = _ordered_moves(mask, me, opp, empty)
    return moves[0] if moves else (mask & -mask)


def _fallback_bit(me: int, opp: int, empty: int) -> int:
    """Fast always-legal strategic fallback."""
    if empty == 0:
        return 0

    my_win = _winning_moves(me, empty)
    if my_win:
        return _choose_best_bit(my_win, me, opp, empty)

    opp_win = _winning_moves(opp, empty)
    if opp_win:
        return _choose_best_bit(opp_win, me, opp, empty)

    # First move or first reply: center is the strongest cell if available.
    if me == 0 and (_CENTER_BIT & empty):
        return _CENTER_BIT

    me_count = me.bit_count()
    opp_count = opp.bit_count()

    if me_count >= 2:
        forks = _fork_moves(me, empty)
        if forks:
            return _choose_best_bit(forks, me, opp, empty)

    if me_count >= 1:
        traps = _threat_to_fork_moves(me, opp, empty)
        if traps:
            return _choose_best_bit(traps, me, opp, empty)

    # Avoid letting the opponent fork/trap when possible.
    danger = 0
    if opp_count >= 2:
        danger |= _fork_moves(opp, empty)
    if opp_count >= 1:
        danger |= _threat_to_fork_moves(opp, me, empty)

    if danger:
        safe = 0
        m = empty
        while m:
            b = m & -m
            m ^= b
            e2 = empty ^ b

            remaining_danger = 0
            if opp_count >= 2:
                remaining_danger |= _fork_moves(opp, e2)
            if opp_count >= 1:
                remaining_danger |= _threat_to_fork_moves(opp, me | b, e2)

            if remaining_danger == 0:
                safe |= b

        if safe:
            return _choose_best_bit(safe, me, opp, empty)

        danger &= empty
        if danger:
            return _choose_best_bit(danger, me, opp, empty)

    if _CENTER_BIT & empty:
        return _CENTER_BIT

    # Prefer making a forcing single threat.
    threat_moves = 0
    m = empty
    while m:
        b = m & -m
        m ^= b
        if _winning_moves(me | b, empty ^ b):
            threat_moves |= b

    if threat_moves:
        return _choose_best_bit(threat_moves, me, opp, empty)

    return _choose_best_bit(empty, me, opp, empty)


# ---------- Alpha-beta search ----------

_DEADLINE = 0.0
_NODES = 0
_TT = {}
_TT_LIMIT = 300000


class _SearchTimeout(Exception):
    pass


def _check_time() -> None:
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and perf_counter() > _DEADLINE:
        raise _SearchTimeout()


def _negamax(me: int, opp: int, depth: int, alpha: int, beta: int) -> int:
    _check_time()

    empty = _ALL_MASK & ~(me | opp)
    ecount = empty.bit_count()

    if _is_win(opp):
        return -_WIN_SCORE - ecount
    if _is_win(me):  # Safeguard for unusual already-terminal inputs.
        return _WIN_SCORE + ecount
    if empty == 0:
        return 0

    my_win = _winning_moves(me, empty)
    if my_win:
        return _WIN_SCORE + ecount

    opp_win = _winning_moves(opp, empty)
    opp_win_count = opp_win.bit_count()

    if opp_win_count >= 2:
        return -_WIN_SCORE - max(0, ecount - 1)

    if opp_win_count == 0:
        if me.bit_count() >= 2:
            forks = _fork_moves(me, empty)
            if forks:
                return _WIN_SCORE + max(0, ecount - 2)

        if depth >= 2 and me.bit_count() >= 1:
            traps = _threat_to_fork_moves(me, opp, empty)
            if traps:
                return _WIN_SCORE + max(0, ecount - 4)

    # Quiescence: if opponent has one immediate win, search the forced block
    # even at nominal depth zero.
    if depth <= 0:
        if opp_win_count == 1:
            depth = 1
        else:
            return _evaluate(me, opp)

    key = (me, opp, depth)
    cached = _TT.get(key)
    if cached is not None:
        return cached

    moves_mask = opp_win if opp_win_count == 1 else empty
    moves = _ordered_moves(moves_mask, me, opp, empty)

    best = -_INF
    cutoff = False

    for b in moves:
        value = -_negamax(opp, me | b, depth - 1, -beta, -alpha)

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            cutoff = True
            break

    if best == -_INF:
        best = 0

    # Store only exact nodes, not beta-cutoff bounds.
    if not cutoff:
        _TT[key] = best

    return best


def _root_search(me: int, opp: int, empty: int, depth: int) -> tuple[int, int]:
    if perf_counter() > _DEADLINE:
        raise _SearchTimeout()

    best_move = 0
    best_value = -_INF
    alpha = -_INF
    beta = _INF

    for b in _ordered_moves(empty, me, opp, empty):
        value = -_negamax(opp, me | b, depth - 1, -beta, -alpha)

        if value > best_value:
            best_value = value
            best_move = b
        if value > alpha:
            alpha = value

    return best_move, best_value


def _search_best(me: int, opp: int, empty: int, initial: int) -> int:
    global _DEADLINE, _NODES

    if len(_TT) > _TT_LIMIT:
        _TT.clear()

    _DEADLINE = perf_counter() + _TIME_BUDGET
    _NODES = 0

    best = initial
    ecount = empty.bit_count()

    if ecount <= 12:
        max_depth = ecount
    elif ecount <= 16:
        max_depth = 11
    elif ecount <= 20:
        max_depth = 8
    elif ecount <= 24:
        max_depth = 6
    else:
        max_depth = 4

    for depth in range(1, max_depth + 1):
        try:
            move, value = _root_search(me, opp, empty, depth)
            if move & empty:
                best = move

            if value >= _WIN_SCORE:
                break
            if depth >= ecount:
                break
            if perf_counter() > _DEADLINE:
                break

        except _SearchTimeout:
            break

    return best


# ---------- Public API ----------

def _board_to_bits(board) -> tuple[int, int]:
    me = 0
    opp = 0
    idx = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                if v == 1:
                    me |= 1 << idx
                elif v == -1:
                    opp |= 1 << idx
                idx += 1

    return me, opp


def _first_empty_from_board(board) -> tuple[int, int, int]:
    for i in range(3):
        for j in range(3):
            for k in range(3):
                try:
                    if board[i][j][k] == 0:
                        return (i, j, k)
                except Exception:
                    pass
    return (0, 0, 0)


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    try:
        me, opp = _board_to_bits(board)
        empty = _ALL_MASK & ~(me | opp)

        if empty == 0:
            return _first_empty_from_board(board)

        # If somehow called after a terminal state, still return a legal move.
        if _is_win(me) or _is_win(opp):
            move = _choose_best_bit(empty, me, opp, empty)
            if move & empty:
                return _COORDS[move.bit_length() - 1]
            return _first_empty_from_board(board)

        # Forced tactical priorities.
        my_win = _winning_moves(me, empty)
        if my_win:
            move = _choose_best_bit(my_win, me, opp, empty)
            return _COORDS[move.bit_length() - 1]

        opp_win = _winning_moves(opp, empty)
        if opp_win:
            move = _choose_best_bit(opp_win, me, opp, empty)
            return _COORDS[move.bit_length() - 1]

        # Strong opening rule.
        if me == 0 and (_CENTER_BIT & empty):
            return _COORDS[_CENTER_INDEX]

        if me.bit_count() >= 2:
            forks = _fork_moves(me, empty)
            if forks:
                move = _choose_best_bit(forks, me, opp, empty)
                return _COORDS[move.bit_length() - 1]

        if me.bit_count() >= 1:
            traps = _threat_to_fork_moves(me, opp, empty)
            if traps:
                move = _choose_best_bit(traps, me, opp, empty)
                return _COORDS[move.bit_length() - 1]

        # Heuristic fallback first, then improve with bounded search.
        initial = _fallback_bit(me, opp, empty)
        move = _search_best(me, opp, empty, initial)

        if not (move & empty):
            move = initial if (initial & empty) else (empty & -empty)

        if move & empty:
            return _COORDS[move.bit_length() - 1]

        return _first_empty_from_board(board)

    except Exception:
        return _first_empty_from_board(board)
