
import time
import numpy as np

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

INF = 10 ** 9

_TT = {}
_MAX_TT = 250000
_DEADLINE = 0.0
_NODES = 0

_EXACT = 0
_LOWER = 1
_UPPER = 2


class _SearchTimeout(Exception):
    pass


def _b(r, c):
    return 1 << (r * 8 + c)


CORNERS = _b(0, 0) | _b(0, 7) | _b(7, 0) | _b(7, 7)

_CORNER_INFO = (
    (_b(0, 0), _b(1, 1), _b(0, 1) | _b(1, 0), _b(0, 1) | _b(1, 0) | _b(1, 1)),
    (_b(0, 7), _b(1, 6), _b(0, 6) | _b(1, 7), _b(0, 6) | _b(1, 7) | _b(1, 6)),
    (_b(7, 0), _b(6, 1), _b(7, 1) | _b(6, 0), _b(7, 1) | _b(6, 0) | _b(6, 1)),
    (_b(7, 7), _b(6, 6), _b(7, 6) | _b(6, 7), _b(7, 6) | _b(6, 7) | _b(6, 6)),
)


_POSITION = (
    120, -30, 25, 8, 8, 25, -30, 120,
    -30, -70, -10, -10, -10, -10, -70, -30,
    25, -10, 20, 5, 5, 20, -10, 25,
    8, -10, 5, 2, 2, 5, -10, 8,
    8, -10, 5, 2, 2, 5, -10, 8,
    25, -10, 20, 5, 5, 20, -10, 25,
    -30, -70, -10, -10, -10, -10, -70, -30,
    120, -30, 25, 8, 8, 25, -30, 120,
)

_POS16 = []
for _block in range(4):
    _tbl = [0] * 65536
    _offset = _block * 16
    for _pat in range(65536):
        _x = _pat
        _s = 0
        while _x:
            _lsb = _x & -_x
            _s += _POSITION[_offset + _lsb.bit_length() - 1]
            _x ^= _lsb
        _tbl[_pat] = _s
    _POS16.append(tuple(_tbl))
_POS16 = tuple(_POS16)


_EDGE_LINES = (
    tuple(_b(0, c) for c in range(8)),
    tuple(_b(r, 0) for r in range(8)),
    tuple(_b(0, c) for c in range(7, -1, -1)),
    tuple(_b(r, 7) for r in range(8)),
    tuple(_b(7, c) for c in range(8)),
    tuple(_b(r, 0) for r in range(7, -1, -1)),
    tuple(_b(7, c) for c in range(7, -1, -1)),
    tuple(_b(r, 7) for r in range(7, -1, -1)),
)


def _n(x):
    return x >> 8


def _s(x):
    return (x << 8) & FULL


def _e(x):
    return ((x & NOT_H) << 1) & FULL


def _w(x):
    return (x & NOT_A) >> 1


def _ne(x):
    return (x & NOT_H) >> 7


def _nw(x):
    return (x & NOT_A) >> 9


def _se(x):
    return ((x & NOT_H) << 9) & FULL


def _sw(x):
    return ((x & NOT_A) << 7) & FULL


_SHIFTS = (_n, _s, _e, _w, _ne, _nw, _se, _sw)


def _array_to_bits(arr):
    bits = 0
    flat = np.asarray(arr).reshape(-1)
    for i in np.flatnonzero(flat):
        bits |= 1 << int(i)
    return bits


def _move_to_str(move):
    idx = move.bit_length() - 1
    return chr(97 + (idx & 7)) + str((idx >> 3) + 1)


def _legal_moves(p, o):
    empty = (~(p | o)) & FULL
    moves = 0
    for sh in _SHIFTS:
        x = sh(p) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        moves |= sh(x) & empty
    return moves & FULL


def _make_move(p, o, move):
    flips = 0
    for sh in _SHIFTS:
        cur = sh(move) & o
        captured = 0
        while cur:
            captured |= cur
            nxt = sh(cur)
            if nxt & p:
                flips |= captured
                break
            if not (nxt & o):
                break
            cur = nxt & o
    return p | move | flips, o & ~flips


def _adjacent(x):
    return (
        _n(x) | _s(x) | _e(x) | _w(x) |
        _ne(x) | _nw(x) | _se(x) | _sw(x)
    ) & FULL


def _positional_score(p, o):
    return (
        _POS16[0][p & 0xffff]
        + _POS16[1][(p >> 16) & 0xffff]
        + _POS16[2][(p >> 32) & 0xffff]
        + _POS16[3][(p >> 48) & 0xffff]
        - _POS16[0][o & 0xffff]
        - _POS16[1][(o >> 16) & 0xffff]
        - _POS16[2][(o >> 32) & 0xffff]
        - _POS16[3][(o >> 48) & 0xffff]
    )


def _edge_stable_count(bits):
    stable = 0
    for line in _EDGE_LINES:
        for b in line:
            if bits & b:
                stable |= b
            else:
                break
    return stable.bit_count()


def _bad_corner_mask(p, o):
    occ = p | o
    mask = 0
    for corner, x_sq, c_sqs, adj in _CORNER_INFO:
        if not (occ & corner):
            mask |= adj
    return mask


def _corner_danger_score(p, o):
    occ = p | o
    score = 0
    for corner, x_sq, c_sqs, adj in _CORNER_INFO:
        if not (occ & corner):
            score -= 280 * ((p & x_sq).bit_count() - (o & x_sq).bit_count())
            score -= 125 * ((p & c_sqs).bit_count() - (o & c_sqs).bit_count())
        elif p & corner:
            score += 35 * ((p & adj).bit_count() - (o & adj).bit_count())
        else:
            score -= 35 * ((p & adj).bit_count() - (o & adj).bit_count())
    return score


def _terminal_score(p, o):
    return (p.bit_count() - o.bit_count()) * 100000


def _evaluate(p, o):
    occupied = p | o
    empties = 64 - occupied.bit_count()

    pmoves = _legal_moves(p, o)
    omoves = _legal_moves(o, p)

    if not pmoves and not omoves:
        return _terminal_score(p, o)

    pc = p.bit_count()
    oc = o.bit_count()
    disc_diff = pc - oc

    if empties > 44:
        mobility_w = 90
        potential_w = 25
        frontier_w = 35
        disc_w = -8
        pos_w = 5
        stable_w = 80
    elif empties > 20:
        mobility_w = 75
        potential_w = 20
        frontier_w = 25
        disc_w = 3
        pos_w = 4
        stable_w = 105
    else:
        mobility_w = 35
        potential_w = 8
        frontier_w = 10
        disc_w = 12 + (20 - empties) * 4
        pos_w = 2
        stable_w = 145
        if empties <= 10:
            disc_w = 80

    pm = pmoves.bit_count()
    om = omoves.bit_count()

    score = 0

    score += disc_w * disc_diff

    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()
    score += 1250 * corner_diff

    score += stable_w * (_edge_stable_count(p) - _edge_stable_count(o))

    score += mobility_w * (pm - om)
    if pm == 0:
        score -= 350
    if om == 0:
        score += 350

    empty = (~occupied) & FULL
    p_potential = (empty & _adjacent(o)).bit_count()
    o_potential = (empty & _adjacent(p)).bit_count()
    score += potential_w * (p_potential - o_potential)

    near_empty = _adjacent(empty)
    p_frontier = (p & near_empty).bit_count()
    o_frontier = (o & near_empty).bit_count()
    score -= frontier_w * (p_frontier - o_frontier)

    score += pos_w * _positional_score(p, o)
    score += _corner_danger_score(p, o)

    if empties <= 16:
        score += 40 if (empties & 1) else -40

    return score


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 255) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()


def _store_tt(key, depth, value, flag, best_move):
    if len(_TT) < _MAX_TT or key in _TT:
        _TT[key] = (depth, value, flag, best_move)


def _ordered_children(p, o, moves, tt_move, empties):
    bad = _bad_corner_mask(p, o)
    children = []

    mset = moves
    while mset:
        move = mset & -mset
        mset ^= move

        p2, o2 = _make_move(p, o, move)
        opp_moves = _legal_moves(o2, p2)

        score = 0

        if move == tt_move:
            score += 100000000

        if move & CORNERS:
            score += 10000000

        if move & bad:
            score -= 2500000

        if opp_moves & CORNERS:
            score -= 1500000 * (opp_moves & CORNERS).bit_count()

        if not opp_moves:
            score += 600000

        score -= 900 * opp_moves.bit_count()

        flips = (p2 & o).bit_count()
        if empties > 22:
            score -= 12 * flips
        else:
            score += 25 * flips

        score += 12000 * ((p2 & CORNERS).bit_count() - (o2 & CORNERS).bit_count())

        if empties <= 16:
            score += 80 * (p2.bit_count() - o2.bit_count())

        children.append((score, move, p2, o2))

    children.sort(key=lambda x: x[0], reverse=True)
    return children


def _negamax(p, o, depth, alpha, beta):
    _check_time()

    alpha_orig = alpha
    key = (p, o)
    tt_move = 0

    entry = _TT.get(key)
    if entry is not None:
        e_depth, e_value, e_flag, e_best = entry
        tt_move = e_best
        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_value
            if e_flag == _LOWER:
                if e_value >= beta:
                    return e_value
                if e_value > alpha:
                    alpha = e_value
            elif e_flag == _UPPER:
                if e_value <= alpha:
                    return e_value
                if e_value < beta:
                    beta = e_value
            if alpha >= beta:
                return e_value

    if depth <= 0:
        return _evaluate(p, o)

    moves = _legal_moves(p, o)
    if not moves:
        if not _legal_moves(o, p):
            return _terminal_score(p, o)
        return -_negamax(o, p, depth, -beta, -alpha)

    empties = 64 - (p | o).bit_count()

    best_value = -INF
    best_move = 0

    for _, move, p2, o2 in _ordered_children(p, o, moves, tt_move, empties):
        value = -_negamax(o2, p2, depth - 1, -beta, -alpha)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            break

    if best_value <= alpha_orig:
        flag = _UPPER
    elif best_value >= beta:
        flag = _LOWER
    else:
        flag = _EXACT

    _store_tt(key, depth, best_value, flag, best_move)
    return best_value


def _fallback_best(p, o, moves):
    empties = 64 - (p | o).bit_count()
    bad = _bad_corner_mask(p, o)

    best_move = moves & -moves
    best_score = -INF

    mset = moves
    while mset:
        move = mset & -mset
        mset ^= move

        p2, o2 = _make_move(p, o, move)
        opp_moves = _legal_moves(o2, p2)

        score = -_evaluate(o2, p2)

        if move & CORNERS:
            score += 100000

        if move & bad:
            score -= 50000

        if opp_moves & CORNERS:
            score -= 80000 * (opp_moves & CORNERS).bit_count()

        if not opp_moves:
            score += 30000

        if empties <= 12:
            score += 500 * (p2.bit_count() - o2.bit_count())

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _DEADLINE, _NODES

    p = _array_to_bits(you)
    o = _array_to_bits(opponent)

    moves = _legal_moves(p, o)

    if not moves:
        return "pass"

    if moves & (moves - 1) == 0:
        return _move_to_str(moves)

    if len(_TT) > _MAX_TT:
        _TT.clear()

    occupied_count = (p | o).bit_count()
    empties = 64 - occupied_count

    if empties <= 12:
        budget = 0.88
    elif empties <= 22:
        budget = 0.82
    else:
        budget = 0.78

    _DEADLINE = time.perf_counter() + budget
    _NODES = 0

    best = _fallback_best(p, o, moves)

    if empties <= 14:
        max_depth = empties
    elif empties <= 22:
        max_depth = 12
    elif empties <= 44:
        max_depth = 9
    else:
        max_depth = 8

    last_value = None

    try:
        depth = 1
        while depth <= max_depth:
            alpha = -INF
            beta = INF
            local_best = best
            local_value = -INF

            children = _ordered_children(p, o, moves, best, empties)

            for _, move, p2, o2 in children:
                value = -_negamax(o2, p2, depth - 1, -beta, -alpha)

                if value > local_value:
                    local_value = value
                    local_best = move

                if value > alpha:
                    alpha = value

            best = local_best
            last_value = local_value
            _store_tt((p, o), depth, local_value, _EXACT, best)

            if depth >= empties:
                break

            if time.perf_counter() > _DEADLINE:
                break

            depth += 1

    except _SearchTimeout:
        pass

    if best & moves:
        return _move_to_str(best)

    safe = moves & -moves
    return _move_to_str(safe)
