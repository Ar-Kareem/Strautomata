
import time
import numpy as np

FULL = 0xFFFFFFFFFFFFFFFF
A_FILE = 0x0101010101010101
H_FILE = 0x8080808080808080
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

INF = 10 ** 9
TIME_LIMIT = 0.86

EXACT, LOWER, UPPER = 0, 1, 2

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
X_SQUARES = (1 << 9) | (1 << 14) | (1 << 49) | (1 << 54)
C_SQUARES = (
    (1 << 1) | (1 << 8) |
    (1 << 6) | (1 << 15) |
    (1 << 48) | (1 << 57) |
    (1 << 55) | (1 << 62)
)

CORNER_ADJ = (
    (1 << 0,  (1 << 1) | (1 << 8) | (1 << 9)),
    (1 << 7,  (1 << 6) | (1 << 14) | (1 << 15)),
    (1 << 56, (1 << 48) | (1 << 49) | (1 << 57)),
    (1 << 63, (1 << 54) | (1 << 55) | (1 << 62)),
)

ADJ_CORNER_FOR_SQUARE = [0] * 64
for _corner, _adj in CORNER_ADJ:
    _x = _adj
    while _x:
        _b = _x & -_x
        ADJ_CORNER_FOR_SQUARE[_b.bit_length() - 1] = _corner
        _x -= _b

MOVE_STR = tuple(
    chr(ord("a") + c) + str(r + 1)
    for r in range(8)
    for c in range(8)
)

POSITION_WEIGHTS = (
    120, -25,  20,   5,   5,  20, -25, 120,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
    120, -25,  20,   5,   5,  20, -25, 120,
)

_order = [w * 10 for w in POSITION_WEIGHTS]
for _i in range(64):
    _m = 1 << _i
    if _m & CORNERS:
        _order[_i] = 10000
    elif _m & X_SQUARES:
        _order[_i] = -5000
    elif _m & C_SQUARES:
        _order[_i] = -1500
ORDER_WEIGHTS = tuple(_order)

_BYTE_WEIGHT_TABLE = []
for _block in range(8):
    _base = _block * 8
    _arr = [0] * 256
    for _mask in range(1, 256):
        _lsb = _mask & -_mask
        _arr[_mask] = _arr[_mask ^ _lsb] + POSITION_WEIGHTS[_base + _lsb.bit_length() - 1]
    _BYTE_WEIGHT_TABLE.append(tuple(_arr))
_BYTE_WEIGHT_TABLE = tuple(_BYTE_WEIGHT_TABLE)

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _array_to_bits(a):
    bb = 0
    for i in np.flatnonzero(a):
        bb |= 1 << int(i)
    return bb


def _shift_n(x):
    return x >> 8


def _shift_s(x):
    return (x << 8) & FULL


def _shift_e(x):
    return ((x & NOT_H) << 1) & FULL


def _shift_w(x):
    return (x & NOT_A) >> 1


def _shift_ne(x):
    return (x & NOT_H) >> 7


def _shift_nw(x):
    return (x & NOT_A) >> 9


def _shift_se(x):
    return ((x & NOT_H) << 9) & FULL


def _shift_sw(x):
    return ((x & NOT_A) << 7) & FULL


_SHIFTS = (_shift_n, _shift_s, _shift_e, _shift_w, _shift_ne, _shift_nw, _shift_se, _shift_sw)


def _legal_moves(me, opp):
    empty = (~(me | opp)) & FULL
    moves = 0

    t = ((me & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    t |= ((t & NOT_H) << 1) & opp
    moves |= ((t & NOT_H) << 1) & empty

    t = ((me & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    t |= ((t & NOT_A) >> 1) & opp
    moves |= ((t & NOT_A) >> 1) & empty

    t = (me >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    moves |= (t >> 8) & empty

    t = ((me << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    t |= ((t << 8) & FULL) & opp
    moves |= ((t << 8) & FULL) & empty

    t = ((me & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    t |= ((t & NOT_H) >> 7) & opp
    moves |= ((t & NOT_H) >> 7) & empty

    t = ((me & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    t |= ((t & NOT_A) >> 9) & opp
    moves |= ((t & NOT_A) >> 9) & empty

    t = ((me & NOT_H) << 9) & FULL & opp
    t |= ((t & NOT_H) << 9) & FULL & opp
    t |= ((t & NOT_H) << 9) & FULL & opp
    t |= ((t & NOT_H) << 9) & FULL & opp
    t |= ((t & NOT_H) << 9) & FULL & opp
    t |= ((t & NOT_H) << 9) & FULL & opp
    moves |= ((t & NOT_H) << 9) & FULL & empty

    t = ((me & NOT_A) << 7) & FULL & opp
    t |= ((t & NOT_A) << 7) & FULL & opp
    t |= ((t & NOT_A) << 7) & FULL & opp
    t |= ((t & NOT_A) << 7) & FULL & opp
    t |= ((t & NOT_A) << 7) & FULL & opp
    t |= ((t & NOT_A) << 7) & FULL & opp
    moves |= ((t & NOT_A) << 7) & FULL & empty

    return moves


def _make_move(me, opp, move):
    flips = 0
    for sh in _SHIFTS:
        captured = 0
        x = sh(move)
        while x & opp:
            captured |= x
            x = sh(x)
        if x & me:
            flips |= captured
    return me | move | flips, opp & ~flips


def _neighbors(x):
    return (
        (x >> 8) |
        ((x << 8) & FULL) |
        ((x & NOT_H) << 1) |
        ((x & NOT_A) >> 1) |
        ((x & NOT_H) >> 7) |
        ((x & NOT_A) >> 9) |
        (((x & NOT_H) << 9) & FULL) |
        (((x & NOT_A) << 7) & FULL)
    ) & FULL


def _weighted_score(bb):
    t = _BYTE_WEIGHT_TABLE
    return (
        t[0][bb & 255] +
        t[1][(bb >> 8) & 255] +
        t[2][(bb >> 16) & 255] +
        t[3][(bb >> 24) & 255] +
        t[4][(bb >> 32) & 255] +
        t[5][(bb >> 40) & 255] +
        t[6][(bb >> 48) & 255] +
        t[7][(bb >> 56) & 255]
    )


def _edge_stable_mask(bb):
    stable = 0

    if bb & (1 << 0):
        for c in range(8):
            b = 1 << c
            if bb & b:
                stable |= b
            else:
                break
        for r in range(8):
            b = 1 << (8 * r)
            if bb & b:
                stable |= b
            else:
                break

    if bb & (1 << 7):
        for c in range(7, -1, -1):
            b = 1 << c
            if bb & b:
                stable |= b
            else:
                break
        for r in range(8):
            b = 1 << (8 * r + 7)
            if bb & b:
                stable |= b
            else:
                break

    if bb & (1 << 56):
        for c in range(8):
            b = 1 << (56 + c)
            if bb & b:
                stable |= b
            else:
                break
        for r in range(7, -1, -1):
            b = 1 << (8 * r)
            if bb & b:
                stable |= b
            else:
                break

    if bb & (1 << 63):
        for c in range(7, -1, -1):
            b = 1 << (56 + c)
            if bb & b:
                stable |= b
            else:
                break
        for r in range(7, -1, -1):
            b = 1 << (8 * r + 7)
            if bb & b:
                stable |= b
            else:
                break

    return stable


def _final_score(me, opp):
    return (me.bit_count() - opp.bit_count()) * 100000


def _evaluate(me, opp, my_moves=None):
    occupied = me | opp
    empties = 64 - occupied.bit_count()
    empty = (~occupied) & FULL

    if my_moves is None:
        my_moves = _legal_moves(me, opp)
    op_moves = _legal_moves(opp, me)

    my_mob = my_moves.bit_count()
    op_mob = op_moves.bit_count()

    disc_diff = me.bit_count() - opp.bit_count()
    corner_diff = (me & CORNERS).bit_count() - (opp & CORNERS).bit_count()

    close_score = 0
    for corner, adj in CORNER_ADJ:
        if not (occupied & corner):
            close_score += (opp & adj).bit_count() - (me & adj).bit_count()

    neigh_empty = _neighbors(empty)
    my_frontier = (me & neigh_empty).bit_count()
    op_frontier = (opp & neigh_empty).bit_count()

    my_potential = (_neighbors(opp) & empty).bit_count()
    op_potential = (_neighbors(me) & empty).bit_count()

    stable_diff = (_edge_stable_mask(me).bit_count() -
                   _edge_stable_mask(opp).bit_count())

    pst = _weighted_score(me) - _weighted_score(opp)

    if empties > 44:
        disc_w = -2
        mob_w = 90
        pot_w = 18
        front_w = 35
        pst_w = 5
    elif empties > 20:
        disc_w = 1
        mob_w = 100
        pot_w = 14
        front_w = 45
        pst_w = 3
    else:
        disc_w = 15 + (20 - empties) * 6
        mob_w = 60
        pot_w = 8
        front_w = 25
        pst_w = 1

    return (
        disc_w * disc_diff +
        mob_w * (my_mob - op_mob) +
        pot_w * (my_potential - op_potential) +
        front_w * (op_frontier - my_frontier) +
        2500 * corner_diff +
        400 * close_score +
        350 * stable_diff +
        pst_w * pst
    )


def _move_order_score(me, opp, move, tt_move):
    idx = move.bit_length() - 1
    score = ORDER_WEIGHTS[idx]

    if move == tt_move:
        score += 2000000

    if move & CORNERS:
        score += 1000000

    corner = ADJ_CORNER_FOR_SQUARE[idx]
    if corner:
        occupied = me | opp
        if not (occupied & corner):
            if move & X_SQUARES:
                score -= 200000
            else:
                score -= 80000
        elif me & corner:
            score += 1500
        else:
            score -= 300

    return score


def _ordered_moves(me, opp, moves, tt_move=0):
    arr = []
    x = moves
    while x:
        m = x & -x
        x -= m
        arr.append((_move_order_score(me, opp, m, tt_move), m))
    arr.sort(reverse=True)
    return [m for _, m in arr]


def _store_tt(key, depth, value, flag, best_move):
    old = _TT.get(key)
    if old is None or depth >= old[0]:
        if len(_TT) < 250000 or old is not None:
            _TT[key] = (depth, value, flag, best_move)


def _negamax(me, opp, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()

    moves = _legal_moves(me, opp)

    if moves == 0:
        opp_moves = _legal_moves(opp, me)
        if opp_moves == 0:
            return _final_score(me, opp)
        return -_negamax(opp, me, depth, -beta, -alpha)

    if depth <= 0:
        return _evaluate(me, opp, moves)

    key = (me, opp)
    entry = _TT.get(key)
    tt_move = 0
    if entry is not None:
        edepth, eval_value, flag, stored_move = entry
        tt_move = stored_move
        if edepth >= depth:
            if flag == EXACT:
                return eval_value
            if flag == LOWER and eval_value >= beta:
                return eval_value
            if flag == UPPER and eval_value <= alpha:
                return eval_value

    alpha_orig = alpha
    beta_orig = beta
    best_score = -INF
    best_move = 0

    for move in _ordered_moves(me, opp, moves, tt_move):
        new_me, new_opp = _make_move(me, opp, move)
        score = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best_score <= alpha_orig:
        flag = UPPER
    elif best_score >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _store_tt(key, depth, best_score, flag, best_move)
    return best_score


def _root_search(me, opp, moves, depth, previous_best):
    if time.perf_counter() > _DEADLINE:
        raise _Timeout()

    entry = _TT.get((me, opp))
    tt_move = previous_best
    if entry is not None and entry[3]:
        tt_move = entry[3]

    best_move = 0
    best_score = -INF
    alpha = -INF
    beta = INF

    for move in _ordered_moves(me, opp, moves, tt_move):
        if time.perf_counter() > _DEADLINE:
            raise _Timeout()

        new_me, new_opp = _make_move(me, opp, move)
        score = -_negamax(new_opp, new_me, depth - 1, -beta, -alpha)

        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score

    _store_tt((me, opp), depth, best_score, EXACT, best_move)
    return best_move, best_score


def _first_move(moves):
    return moves & -moves


def _choose_static_move(me, opp, moves):
    best_move = _first_move(moves)
    best_score = -INF

    for move in _ordered_moves(me, opp, moves, 0):
        new_me, new_opp = _make_move(me, opp, move)
        opp_moves = _legal_moves(new_opp, new_me)

        if opp_moves == 0 and _legal_moves(new_me, new_opp) == 0:
            score = _final_score(new_me, new_opp)
        else:
            score = -_evaluate(new_opp, new_me, opp_moves)

        if move & CORNERS:
            score += 5000

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def _move_to_str(move):
    return MOVE_STR[move.bit_length() - 1]


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _TT, _DEADLINE, _NODES

    me = _array_to_bits(you)
    opp = _array_to_bits(opponent)

    moves = _legal_moves(me, opp)
    if moves == 0:
        return "pass"

    if moves & (moves - 1) == 0:
        return _move_to_str(moves)

    start = time.perf_counter()
    _DEADLINE = start + TIME_LIMIT
    _TT = {}
    _NODES = 0

    fallback = _choose_static_move(me, opp, moves)
    best_move = fallback
    previous_best = fallback

    empties = 64 - (me | opp).bit_count()
    max_depth = max(1, empties)

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > _DEADLINE:
            break
        try:
            move, score = _root_search(me, opp, moves, depth, previous_best)
            if move & moves:
                best_move = move
                previous_best = move
            if depth >= empties:
                break
        except _Timeout:
            break
        except Exception:
            break

    if not (best_move & moves):
        best_move = fallback
    if not (best_move & moves):
        best_move = _first_move(moves)

    return _move_to_str(best_move)
