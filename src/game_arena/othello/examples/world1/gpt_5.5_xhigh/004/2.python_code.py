
import time
import numpy as np

_FULL = 0xFFFFFFFFFFFFFFFF
_NOT_A = 0xFEFEFEFEFEFEFEFE
_NOT_H = 0x7F7F7F7F7F7F7F7F

_BITS = [1 << i for i in range(64)]
_MOVE_NAMES = [chr(ord("a") + (i & 7)) + str((i >> 3) + 1) for i in range(64)]

_CORNERS = _BITS[0] | _BITS[7] | _BITS[56] | _BITS[63]
_X_SQUARES = _BITS[9] | _BITS[14] | _BITS[49] | _BITS[54]

_CORNER_INFO = (
    (_BITS[0],  _BITS[1] | _BITS[8] | _BITS[9],   _BITS[9]),
    (_BITS[7],  _BITS[6] | _BITS[14] | _BITS[15], _BITS[14]),
    (_BITS[56], _BITS[48] | _BITS[49] | _BITS[57], _BITS[49]),
    (_BITS[63], _BITS[54] | _BITS[55] | _BITS[62], _BITS[54]),
)

_STABLE_RAYS = (
    (_BITS[0],  (0, 1, 2, 3, 4, 5, 6, 7),          (0, 8, 16, 24, 32, 40, 48, 56)),
    (_BITS[7],  (7, 6, 5, 4, 3, 2, 1, 0),          (7, 15, 23, 31, 39, 47, 55, 63)),
    (_BITS[56], (56, 57, 58, 59, 60, 61, 62, 63),  (56, 48, 40, 32, 24, 16, 8, 0)),
    (_BITS[63], (63, 62, 61, 60, 59, 58, 57, 56),  (63, 55, 47, 39, 31, 23, 15, 7)),
)

_POS_WEIGHTS = [
    120, -40,  20,   5,   5,  20, -40, 120,
    -40, -80, -10, -10, -10, -10, -80, -40,
     20, -10,  15,   3,   3,  15, -10,  20,
      5, -10,   3,   3,   3,   3, -10,   5,
      5, -10,   3,   3,   3,   3, -10,   5,
     20, -10,  15,   3,   3,  15, -10,  20,
    -40, -80, -10, -10, -10, -10, -80, -40,
    120, -40,  20,   5,   5,  20, -40, 120,
]

_ORDER_WEIGHTS = [
    10000, -3000,   800,  300,  300,   800, -3000, 10000,
    -3000, -8000,  -600, -500, -500,  -600, -8000, -3000,
      800,  -600,   400,   50,   50,   400,  -600,   800,
      300,  -500,    50,   20,   20,    50,  -500,   300,
      300,  -500,    50,   20,   20,    50,  -500,   300,
      800,  -600,   400,   50,   50,   400,  -600,   800,
    -3000, -8000,  -600, -500, -500,  -600, -8000, -3000,
    10000, -3000,   800,  300,  300,   800, -3000, 10000,
]

_INF = 1_000_000_000
_WIN_SCALE = 1_000_000

_EXACT = 0
_LOWER = 1
_UPPER = 2

_TT = {}
_HISTORY = [0] * 64
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _n(x):
    return x >> 8


def _s(x):
    return (x << 8) & _FULL


def _e(x):
    return ((x & _NOT_H) << 1) & _FULL


def _w(x):
    return (x & _NOT_A) >> 1


def _ne(x):
    return (x & _NOT_H) >> 7


def _nw(x):
    return (x & _NOT_A) >> 9


def _se(x):
    return ((x & _NOT_H) << 9) & _FULL


def _sw(x):
    return ((x & _NOT_A) << 7) & _FULL


_DIRS = (_n, _s, _e, _w, _ne, _nw, _se, _sw)


def _bits_from_array(a):
    bits = 0
    for i in np.flatnonzero(a):
        bits |= 1 << int(i)
    return bits


def _move_to_str(m):
    return _MOVE_NAMES[m.bit_length() - 1]


def _legal_moves(p, o):
    empty = (~(p | o)) & _FULL
    if empty == 0:
        return 0

    moves = 0
    for sh in _DIRS:
        x = sh(p) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        x |= sh(x) & o
        moves |= sh(x) & empty
    return moves


def _make_move(p, o, m):
    flips = 0
    for sh in _DIRS:
        x = sh(m)
        line = 0
        while x & o:
            line |= x
            x = sh(x)
        if x & p:
            flips |= line
    return p | m | flips, o & ~flips


def _adjacent(x):
    return _n(x) | _s(x) | _e(x) | _w(x) | _ne(x) | _nw(x) | _se(x) | _sw(x)


def _terminal_score(p, o):
    return (p.bit_count() - o.bit_count()) * _WIN_SCALE


def _piece_square_score(p, o):
    score = 0

    x = p
    while x:
        m = x & -x
        score += _POS_WEIGHTS[m.bit_length() - 1]
        x ^= m

    x = o
    while x:
        m = x & -x
        score -= _POS_WEIGHTS[m.bit_length() - 1]
        x ^= m

    return score


def _corner_structure(p, o):
    occ = p | o
    score = 0

    for corner, adj, x_sq in _CORNER_INFO:
        if not (occ & corner):
            # Adjacent discs to an empty corner are dangerous, especially X-squares.
            p_bad = (p & adj).bit_count() + 2 * (p & x_sq).bit_count()
            o_bad = (o & adj).bit_count() + 2 * (o & x_sq).bit_count()
            score += o_bad - p_bad
        elif p & corner:
            score += (p & adj).bit_count()
        else:
            score -= (o & adj).bit_count()

    return score


def _stable_edges_one(bb):
    stable = 0
    for corner, ray_a, ray_b in _STABLE_RAYS:
        if bb & corner:
            for i in ray_a:
                b = _BITS[i]
                if bb & b:
                    stable |= b
                else:
                    break
            for i in ray_b:
                b = _BITS[i]
                if bb & b:
                    stable |= b
                else:
                    break
    return stable.bit_count()


def _evaluate(p, o):
    pc = p.bit_count()
    oc = o.bit_count()
    empties = 64 - pc - oc
    disc_diff = pc - oc

    p_moves_bits = _legal_moves(p, o)
    o_moves_bits = _legal_moves(o, p)

    if p_moves_bits == 0 and o_moves_bits == 0:
        return _terminal_score(p, o)

    mobility = p_moves_bits.bit_count() - o_moves_bits.bit_count()
    corner_access = (p_moves_bits & _CORNERS).bit_count() - (o_moves_bits & _CORNERS).bit_count()

    occupied = p | o
    empty = (~occupied) & _FULL

    adj_empty = _adjacent(empty)
    adj_p = _adjacent(p)
    adj_o = _adjacent(o)

    potential = (adj_o & empty).bit_count() - (adj_p & empty).bit_count()
    frontier = (o & adj_empty).bit_count() - (p & adj_empty).bit_count()

    corners = (p & _CORNERS).bit_count() - (o & _CORNERS).bit_count()
    corner_struct = _corner_structure(p, o)

    if occupied & _CORNERS:
        stable = _stable_edges_one(p) - _stable_edges_one(o)
    else:
        stable = 0

    pos = _piece_square_score(p, o)

    if empties > 44:
        return (
            3 * pos
            + 3500 * corners
            + 1800 * corner_access
            + 900 * corner_struct
            + 110 * mobility
            + 18 * potential
            + 12 * frontier
            + 240 * stable
            - 4 * disc_diff
        )
    elif empties > 18:
        return (
            2 * pos
            + 4200 * corners
            + 2000 * corner_access
            + 800 * corner_struct
            + 95 * mobility
            + 12 * potential
            + 9 * frontier
            + 300 * stable
            + 4 * disc_diff
        )
    else:
        return (
            pos
            + 5200 * corners
            + 1200 * corner_access
            + 500 * corner_struct
            + 65 * mobility
            + 5 * potential
            + 5 * frontier
            + 400 * stable
            + 75 * disc_diff
        )


def _corner_move_adjust(m, p, o):
    occ = p | o
    score = 0

    for corner, adj, x_sq in _CORNER_INFO:
        if m & adj:
            if not (occ & corner):
                score -= 12000 if (m & x_sq) else 5000
            elif p & corner:
                score += 6000 if (m & x_sq) else 2000
            else:
                score -= 1000

    return score


def _static_best_move(p, o, moves):
    best = moves & -moves
    best_score = -_INF

    x = moves
    while x:
        m = x & -x
        x ^= m

        p2, o2 = _make_move(p, o, m)
        opp_moves = _legal_moves(o2, p2)

        if opp_moves == 0:
            if _legal_moves(p2, o2) == 0:
                score = _terminal_score(p2, o2)
            else:
                score = _evaluate(p2, o2) + 2500
        else:
            score = -_evaluate(o2, p2)

        idx = m.bit_length() - 1
        score += _ORDER_WEIGHTS[idx] // 10
        score += _corner_move_adjust(m, p, o)

        opp_corners = opp_moves & _CORNERS
        if opp_corners:
            score -= 8000 * opp_corners.bit_count()

        if score > best_score:
            best_score = score
            best = m

    return best


def _check_time():
    if time.perf_counter() >= _DEADLINE:
        raise _Timeout()


def _ordered_children(p, o, moves, tt_move, depth):
    children = []
    empties = 64 - (p | o).bit_count()
    use_mobility_order = depth >= 3

    x = moves
    while x:
        m = x & -x
        x ^= m

        p2, o2 = _make_move(p, o, m)
        idx = m.bit_length() - 1

        score = _ORDER_WEIGHTS[idx] + (_HISTORY[idx] >> 2)

        if m == tt_move:
            score += 1_000_000
        if m & _CORNERS:
            score += 200_000

        score += _corner_move_adjust(m, p, o)

        flips = p2.bit_count() - p.bit_count() - 1
        if empties <= 14:
            score += 20 * flips
        else:
            score -= 3 * flips

        if use_mobility_order:
            opp_moves = _legal_moves(o2, p2)
            if opp_moves == 0:
                if _legal_moves(p2, o2) == 0:
                    score += _terminal_score(p2, o2) // 1000
                else:
                    score += 15000
            else:
                score -= 70 * opp_moves.bit_count()
                opp_corners = opp_moves & _CORNERS
                if opp_corners:
                    score -= 50000 * opp_corners.bit_count()

        children.append((score, m, p2, o2))

    children.sort(key=lambda t: t[0], reverse=True)
    return children


def _store_tt(p, o, depth, value, alpha0, beta0, best_move):
    if value <= alpha0:
        flag = _UPPER
    elif value >= beta0:
        flag = _LOWER
    else:
        flag = _EXACT

    old = _TT.get((p, o))
    if old is None or depth >= old[0]:
        _TT[(p, o)] = (depth, value, flag, best_move)


def _negamax(p, o, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 255) == 0:
        _check_time()

    tt_move = 0
    entry = _TT.get((p, o))
    if entry is not None:
        e_depth, e_value, e_flag, e_move = entry
        tt_move = e_move

        if e_depth >= depth:
            if e_flag == _EXACT:
                return e_value
            elif e_flag == _LOWER:
                if e_value > alpha:
                    alpha = e_value
            elif e_flag == _UPPER:
                if e_value < beta:
                    beta = e_value

            if alpha >= beta:
                return e_value

    alpha0 = alpha
    beta0 = beta

    moves = _legal_moves(p, o)

    if moves == 0:
        if _legal_moves(o, p) == 0:
            value = _terminal_score(p, o)
        else:
            value = -_negamax(o, p, depth, -beta, -alpha)
        _store_tt(p, o, depth, value, alpha0, beta0, 0)
        return value

    if depth <= 0:
        value = _evaluate(p, o)
        old = _TT.get((p, o))
        if old is None or old[0] <= 0:
            _TT[(p, o)] = (0, value, _EXACT, 0)
        return value

    best_value = -_INF
    best_move = 0
    first = True

    for _, m, p2, o2 in _ordered_children(p, o, moves, tt_move, depth):
        if first:
            value = -_negamax(o2, p2, depth - 1, -beta, -alpha)
        else:
            value = -_negamax(o2, p2, depth - 1, -alpha - 1, -alpha)
            if alpha < value < beta:
                value = -_negamax(o2, p2, depth - 1, -beta, -alpha)

        if value > best_value:
            best_value = value
            best_move = m

        if value > alpha:
            alpha = value

        if alpha >= beta:
            if best_move:
                idx = best_move.bit_length() - 1
                _HISTORY[idx] += depth * depth
            break

        first = False

    _store_tt(p, o, depth, best_value, alpha0, beta0, best_move)
    return best_value


def _root_search(p, o, moves, depth, prior_move):
    _check_time()

    entry = _TT.get((p, o))
    tt_move = prior_move
    if entry is not None and (entry[3] & moves):
        tt_move = entry[3]

    alpha = -_INF
    beta = _INF
    best_value = -_INF
    best_move = moves & -moves
    first = True

    for _, m, p2, o2 in _ordered_children(p, o, moves, tt_move, depth):
        _check_time()

        if first:
            value = -_negamax(o2, p2, depth - 1, -beta, -alpha)
        else:
            value = -_negamax(o2, p2, depth - 1, -alpha - 1, -alpha)
            if alpha < value < beta:
                value = -_negamax(o2, p2, depth - 1, -beta, -alpha)

        if value > best_value:
            best_value = value
            best_move = m

        if value > alpha:
            alpha = value

        first = False

    old = _TT.get((p, o))
    if old is None or depth >= old[0]:
        _TT[(p, o)] = (depth, best_value, _EXACT, best_move)

    return best_value, best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _DEADLINE, _NODES

    p = _bits_from_array(you)
    o = _bits_from_array(opponent)

    moves = _legal_moves(p, o)
    if moves == 0:
        return "pass"

    if moves & (moves - 1) == 0:
        return _move_to_str(moves)

    if len(_TT) > 300000:
        _TT.clear()

    if max(_HISTORY) > 200000:
        for i in range(64):
            _HISTORY[i] //= 2

    best = moves & -moves

    try:
        best = _static_best_move(p, o, moves)

        _DEADLINE = time.perf_counter() + 0.86
        _NODES = 0

        empties = 64 - (p | o).bit_count()
        depth = 1

        while depth <= empties:
            _, move = _root_search(p, o, moves, depth, best)
            if move & moves:
                best = move

            if depth >= empties:
                break

            if time.perf_counter() >= _DEADLINE:
                break

            depth += 1

    except Exception:
        pass

    if not (best & moves):
        best = moves & -moves

    return _move_to_str(best)
