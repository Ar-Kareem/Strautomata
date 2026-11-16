
import time
import sys
import numpy as np

sys.setrecursionlimit(10000)

FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F

INF = 10**12
DISC_VALUE = 1_000_000
FILES = "abcdefgh"

EXACT, LOWER, UPPER = 0, 1, 2

_TT = {}
_DEADLINE = 0.0
_NODES = 0


def _bit(r, c):
    return 1 << (r * 8 + c)


A1, H1, A8, H8 = _bit(0, 0), _bit(0, 7), _bit(7, 0), _bit(7, 7)
CORNERS = A1 | H1 | A8 | H8

_CORNER_DATA = (
    (A1, _bit(1, 1), _bit(0, 1) | _bit(1, 0), _bit(0, 1) | _bit(1, 0) | _bit(1, 1)),
    (H1, _bit(1, 6), _bit(0, 6) | _bit(1, 7), _bit(0, 6) | _bit(1, 7) | _bit(1, 6)),
    (A8, _bit(6, 1), _bit(7, 1) | _bit(6, 0), _bit(7, 1) | _bit(6, 0) | _bit(6, 1)),
    (H8, _bit(6, 6), _bit(7, 6) | _bit(6, 7), _bit(7, 6) | _bit(6, 7) | _bit(6, 6)),
)

_STABLE_RAYS = (
    (A1, (0, 1, 2, 3, 4, 5, 6, 7), (0, 8, 16, 24, 32, 40, 48, 56)),
    (H1, (7, 6, 5, 4, 3, 2, 1, 0), (7, 15, 23, 31, 39, 47, 55, 63)),
    (A8, (56, 57, 58, 59, 60, 61, 62, 63), (56, 48, 40, 32, 24, 16, 8, 0)),
    (H8, (63, 62, 61, 60, 59, 58, 57, 56), (63, 55, 47, 39, 31, 23, 15, 7)),
)

_POS_MATRIX = (
    (120, -30, 22, 8, 8, 22, -30, 120),
    (-30, -85, -10, -6, -6, -10, -85, -30),
    (22, -10, 16, 3, 3, 16, -10, 22),
    (8, -6, 3, 2, 2, 3, -6, 8),
    (8, -6, 3, 2, 2, 3, -6, 8),
    (22, -10, 16, 3, 3, 16, -10, 22),
    (-30, -85, -10, -6, -6, -10, -85, -30),
    (120, -30, 22, 8, 8, 22, -30, 120),
)

_ORDER_MATRIX = (
    (50000, -8000, 1800, 900, 900, 1800, -8000, 50000),
    (-8000, -16000, -1600, -900, -900, -1600, -16000, -8000),
    (1800, -1600, 1200, 350, 350, 1200, -1600, 1800),
    (900, -900, 350, 120, 120, 350, -900, 900),
    (900, -900, 350, 120, 120, 350, -900, 900),
    (1800, -1600, 1200, 350, 350, 1200, -1600, 1800),
    (-8000, -16000, -1600, -900, -900, -1600, -16000, -8000),
    (50000, -8000, 1800, 900, 900, 1800, -8000, 50000),
)

_ROW_SCORE = tuple(
    tuple(
        sum(_POS_MATRIX[r][c] for c in range(8) if byte & (1 << c))
        for byte in range(256)
    )
    for r in range(8)
)

_MOVE_VALUE = tuple(_ORDER_MATRIX[r][c] for r in range(8) for c in range(8))


class _Timeout(Exception):
    pass


def _bits_from_array(a):
    bb = 0
    rows, cols = np.nonzero(a)
    for r, c in zip(rows, cols):
        bb |= 1 << (int(r) * 8 + int(c))
    return bb


def _move_to_str(mv):
    idx = mv.bit_length() - 1
    return FILES[idx & 7] + str((idx >> 3) + 1)


def _legal_moves(p, o):
    empty = (~(p | o)) & FULL
    moves = 0

    t = ((p & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    moves |= ((t & NOT_H) << 1) & empty

    t = ((p & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    moves |= ((t & NOT_A) >> 1) & empty

    t = (p << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    moves |= (t << 8) & empty

    t = (p >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    moves |= (t >> 8) & empty

    t = ((p & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    moves |= ((t & NOT_H) << 9) & empty

    t = ((p & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    moves |= ((t & NOT_A) << 7) & empty

    t = ((p & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    moves |= ((t & NOT_H) >> 7) & empty

    t = ((p & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    moves |= ((t & NOT_A) >> 9) & empty

    return moves


def _flips(m, p, o):
    flips = 0

    x = (m & NOT_H) << 1
    cap = 0
    while x & o:
        cap |= x
        x = (x & NOT_H) << 1
    if x & p:
        flips |= cap

    x = (m & NOT_A) >> 1
    cap = 0
    while x & o:
        cap |= x
        x = (x & NOT_A) >> 1
    if x & p:
        flips |= cap

    x = m << 8
    cap = 0
    while x & o:
        cap |= x
        x <<= 8
    if x & p:
        flips |= cap

    x = m >> 8
    cap = 0
    while x & o:
        cap |= x
        x >>= 8
    if x & p:
        flips |= cap

    x = (m & NOT_H) << 9
    cap = 0
    while x & o:
        cap |= x
        x = (x & NOT_H) << 9
    if x & p:
        flips |= cap

    x = (m & NOT_A) << 7
    cap = 0
    while x & o:
        cap |= x
        x = (x & NOT_A) << 7
    if x & p:
        flips |= cap

    x = (m & NOT_H) >> 7
    cap = 0
    while x & o:
        cap |= x
        x = (x & NOT_H) >> 7
    if x & p:
        flips |= cap

    x = (m & NOT_A) >> 9
    cap = 0
    while x & o:
        cap |= x
        x = (x & NOT_A) >> 9
    if x & p:
        flips |= cap

    return flips


def _make_move(m, p, o):
    f = _flips(m, p, o)
    return p | m | f, o & ~f


def _adjacent(x):
    return (
        ((x << 8) & FULL)
        | (x >> 8)
        | ((x & NOT_H) << 1)
        | ((x & NOT_A) >> 1)
        | (((x & NOT_H) << 9) & FULL)
        | (((x & NOT_A) << 7) & FULL)
        | ((x & NOT_H) >> 7)
        | ((x & NOT_A) >> 9)
    ) & FULL


def _piece_square_score(p, o):
    s = 0
    for r in range(8):
        sh = 8 * r
        s += _ROW_SCORE[r][(p >> sh) & 255]
        s -= _ROW_SCORE[r][(o >> sh) & 255]
    return s


def _edge_stable_count(p):
    stable = 0
    for corner, ray1, ray2 in _STABLE_RAYS:
        if p & corner:
            for idx in ray1:
                b = 1 << idx
                if p & b:
                    stable |= b
                else:
                    break
            for idx in ray2:
                b = 1 << idx
                if p & b:
                    stable |= b
                else:
                    break
    return stable.bit_count()


def _evaluate(p, o, pm=None):
    occupied = p | o
    empty = (~occupied) & FULL
    empties = empty.bit_count()

    if pm is None:
        pm = _legal_moves(p, o)
    om = _legal_moves(o, p)

    if pm == 0 and om == 0:
        return (p.bit_count() - o.bit_count()) * DISC_VALUE

    pcount = p.bit_count()
    ocount = o.bit_count()
    diff = pcount - ocount

    score = 0

    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()
    score += 30000 * corner_diff

    for corner, xmask, cmask, adjmask in _CORNER_DATA:
        if not (occupied & corner):
            score -= 8000 * (p & xmask).bit_count()
            score += 8000 * (o & xmask).bit_count()
            score -= 3500 * (p & cmask).bit_count()
            score += 3500 * (o & cmask).bit_count()
        elif p & corner:
            score += 450 * (p & adjmask).bit_count()
            score -= 220 * (o & adjmask).bit_count()
        else:
            score -= 450 * (o & adjmask).bit_count()
            score += 220 * (p & adjmask).bit_count()

    pmc = pm.bit_count()
    omc = om.bit_count()
    if pmc + omc:
        mobility = 100 * (pmc - omc) // (pmc + omc)
        if empties >= 24:
            score += 90 * mobility
        elif empties >= 12:
            score += 55 * mobility
        else:
            score += 25 * mobility

    pot_p = (_adjacent(o) & empty).bit_count()
    pot_o = (_adjacent(p) & empty).bit_count()
    if pot_p + pot_o:
        potential = 100 * (pot_p - pot_o) // (pot_p + pot_o)
        score += (40 if empties > 24 else 16) * potential

    adj_empty = _adjacent(empty)
    frontier_diff = (p & adj_empty).bit_count() - (o & adj_empty).bit_count()
    score -= (40 if empties > 24 else 18) * frontier_diff

    if empties > 24:
        score += 5 * _piece_square_score(p, o)
    elif empties > 12:
        score += 3 * _piece_square_score(p, o)
    else:
        score += _piece_square_score(p, o)

    if occupied & CORNERS:
        score += 650 * (_edge_stable_count(p) - _edge_stable_count(o))

    if empties > 44:
        score -= 6 * diff
    elif empties > 20:
        score += 4 * diff
    else:
        score += (24 - empties) * 45 * diff
        score += 150 if (empties & 1) else -150

    return score


def _order_moves(p, o, moves, tt_move=0, depth=0):
    occ = p | o
    empties = ((~occ) & FULL).bit_count()
    arr = []
    m = moves

    while m:
        mv = m & -m
        m ^= mv
        idx = mv.bit_length() - 1

        score = _MOVE_VALUE[idx]

        if mv == tt_move:
            score += 10_000_000

        if mv & CORNERS:
            score += 250_000

        for corner, xmask, cmask, _adjmask in _CORNER_DATA:
            if not (occ & corner):
                if mv & xmask:
                    score -= 130_000
                elif mv & cmask:
                    score -= 55_000

        if depth >= 4:
            pp, oo = _make_move(mv, p, o)
            opp_moves = _legal_moves(oo, pp)
            opp_count = opp_moves.bit_count()

            if opp_moves == 0:
                score += 25_000

            score -= 800 * opp_count

            opp_corners = opp_moves & CORNERS
            if opp_corners:
                score -= 180_000 * opp_corners.bit_count()

            gain = pp.bit_count() - p.bit_count()
            if empties <= 16:
                score += 350 * gain
            elif empties >= 40:
                score -= 45 * gain

        arr.append((score, mv))

    arr.sort(reverse=True)
    return [mv for score, mv in arr]


def _search(p, o, depth, alpha, beta, ply):
    global _NODES

    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()

    key = (p, o)
    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        e_depth, e_flag, e_val, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_val
            if e_flag == LOWER and e_val >= beta:
                return e_val
            if e_flag == UPPER and e_val <= alpha:
                return e_val

    alpha_orig = alpha
    beta_orig = beta

    moves = _legal_moves(p, o)

    if moves == 0:
        opp_moves = _legal_moves(o, p)
        if opp_moves == 0:
            val = (p.bit_count() - o.bit_count()) * DISC_VALUE
            _TT[key] = (100, EXACT, val, 0)
            return val

        val = -_search(o, p, depth, -beta, -alpha, ply + 1)

        if val <= alpha_orig:
            flag = UPPER
        elif val >= beta_orig:
            flag = LOWER
        else:
            flag = EXACT
        _TT[key] = (depth, flag, val, 0)
        return val

    if depth <= 0:
        return _evaluate(p, o, moves)

    ordered = _order_moves(p, o, moves, tt_move, depth)

    best_val = -INF
    best_move = 0
    first = True

    for mv in ordered:
        pp, oo = _make_move(mv, p, o)

        if first:
            val = -_search(oo, pp, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            val = -_search(oo, pp, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < val < beta:
                val = -_search(oo, pp, depth - 1, -beta, -alpha, ply + 1)

        if val > best_val:
            best_val = val
            best_move = mv

        if val > alpha:
            alpha = val

        if alpha >= beta:
            break

    if best_val <= alpha_orig:
        flag = UPPER
    elif best_val >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT

    _TT[key] = (depth, flag, best_val, best_move)
    return best_val


def _choose_max_depth(empties, legal_count):
    if empties <= 14:
        d = empties
    elif empties <= 18:
        d = 12
    elif empties <= 26:
        d = 10
    elif empties <= 38:
        d = 8
    elif empties <= 52:
        d = 7
    else:
        d = 6

    if legal_count <= 3 and empties > 14:
        d += 3
    elif legal_count <= 5 and empties > 14:
        d += 2
    elif legal_count <= 8 and empties > 20:
        d += 1

    return max(1, min(d, empties))


def _fallback_move(p, o, legal):
    ordered = _order_moves(p, o, legal, 0, 6)
    if ordered:
        return ordered[0]
    return legal & -legal


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _TT, _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0
    _TT = {}

    p = _bits_from_array(you)
    o = _bits_from_array(opponent)

    legal = _legal_moves(p, o)

    if legal == 0:
        return "pass"

    if (legal & (legal - 1)) == 0:
        return _move_to_str(legal)

    fallback = _fallback_move(p, o, legal)
    if not (fallback & legal):
        fallback = legal & -legal

    best_move = fallback

    empties = ((~(p | o)) & FULL).bit_count()
    legal_count = legal.bit_count()
    max_depth = _choose_max_depth(empties, legal_count)

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break

            ordered = _order_moves(p, o, legal, best_move, depth + 2)
            if not ordered:
                break

            current_best = ordered[0]
            current_val = -INF
            alpha = -INF
            beta = INF

            for mv in ordered:
                pp, oo = _make_move(mv, p, o)
                val = -_search(oo, pp, depth - 1, -beta, -alpha, 1)

                if val > current_val:
                    current_val = val
                    current_best = mv

                if val > alpha:
                    alpha = val

            best_move = current_best
            _TT[(p, o)] = (depth, EXACT, current_val, current_best)

            if depth >= empties:
                break

    except _Timeout:
        pass
    except Exception:
        best_move = fallback

    if not (best_move & legal):
        best_move = fallback
    if not (best_move & legal):
        best_move = legal & -legal

    return _move_to_str(best_move)
