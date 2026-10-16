
import time
import numpy as np

FULL = (1 << 64) - 1
A_FILE = 0x0101010101010101
H_FILE = 0x8080808080808080
NOT_A = FULL ^ A_FILE
NOT_H = FULL ^ H_FILE

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
FILES = "abcdefgh"

INF = 10**18
WIN_UNIT = 1_000_000

# Positional table, row-major: a1..h1, ..., a8..h8.
_BASE_WEIGHTS = (
     80, -18,  20,   8,   8,  20, -18,  80,
    -18, -45,  -4,  -4,  -4,  -4, -45, -18,
     20,  -4,   6,   2,   2,   6,  -4,  20,
      8,  -4,   2,   1,   1,   2,  -4,   8,
      8,  -4,   2,   1,   1,   2,  -4,   8,
     20,  -4,   6,   2,   2,   6,  -4,  20,
    -18, -45,  -4,  -4,  -4,  -4, -45, -18,
     80, -18,  20,   8,   8,  20, -18,  80,
)

# Byte lookup table for fast positional sums.
_BYTE_PSQ = tuple(
    tuple(
        sum(_BASE_WEIGHTS[row * 8 + i] for i in range(8) if value & (1 << i))
        for value in range(256)
    )
    for row in range(8)
)

# For each corner: (corner_bit, x_square_bit, c_squares_bits)
_CORNER_INFO = (
    (1 << 0,  1 << 9,  (1 << 1)  | (1 << 8)),
    (1 << 7,  1 << 14, (1 << 6)  | (1 << 15)),
    (1 << 56, 1 << 49, (1 << 48) | (1 << 57)),
    (1 << 63, 1 << 54, (1 << 55) | (1 << 62)),
)

_STABLE_RAYS = (
    (0,  (1, 2, 3, 4, 5, 6, 7),        (8, 16, 24, 32, 40, 48, 56)),
    (7,  (6, 5, 4, 3, 2, 1, 0),        (15, 23, 31, 39, 47, 55, 63)),
    (56, (57, 58, 59, 60, 61, 62, 63), (48, 40, 32, 24, 16, 8, 0)),
    (63, (62, 61, 60, 59, 58, 57, 56), (55, 47, 39, 31, 23, 15, 7)),
)


class _SearchTimeout(Exception):
    pass


_TT = {}
_HISTORY = [0] * 64
_DEADLINE = 0.0
_NODES = 0


def _arrays_to_bits(you, opponent):
    yf = np.asarray(you).reshape(64)
    of = np.asarray(opponent).reshape(64)
    p = 0
    o = 0
    for i in range(64):
        if yf[i]:
            p |= 1 << i
        elif of[i]:
            o |= 1 << i
    return p, o


def _move_to_str(m):
    i = m.bit_length() - 1
    return FILES[i & 7] + str((i >> 3) + 1)


def _legal_moves(p, o):
    empty = (~(p | o)) & FULL
    moves = 0

    # East
    mask = o & NOT_H
    x = mask & ((p & NOT_H) << 1)
    x |= mask & (x << 1)
    x |= mask & (x << 1)
    x |= mask & (x << 1)
    x |= mask & (x << 1)
    x |= mask & (x << 1)
    moves |= empty & (x << 1)

    # West
    mask = o & NOT_A
    x = mask & ((p & NOT_A) >> 1)
    x |= mask & (x >> 1)
    x |= mask & (x >> 1)
    x |= mask & (x >> 1)
    x |= mask & (x >> 1)
    x |= mask & (x >> 1)
    moves |= empty & (x >> 1)

    # South
    mask = o
    x = mask & (p << 8)
    x |= mask & (x << 8)
    x |= mask & (x << 8)
    x |= mask & (x << 8)
    x |= mask & (x << 8)
    x |= mask & (x << 8)
    moves |= empty & (x << 8)

    # North
    x = mask & (p >> 8)
    x |= mask & (x >> 8)
    x |= mask & (x >> 8)
    x |= mask & (x >> 8)
    x |= mask & (x >> 8)
    x |= mask & (x >> 8)
    moves |= empty & (x >> 8)

    # South-East
    mask = o & NOT_H
    x = mask & ((p & NOT_H) << 9)
    x |= mask & (x << 9)
    x |= mask & (x << 9)
    x |= mask & (x << 9)
    x |= mask & (x << 9)
    x |= mask & (x << 9)
    moves |= empty & (x << 9)

    # South-West
    mask = o & NOT_A
    x = mask & ((p & NOT_A) << 7)
    x |= mask & (x << 7)
    x |= mask & (x << 7)
    x |= mask & (x << 7)
    x |= mask & (x << 7)
    x |= mask & (x << 7)
    moves |= empty & (x << 7)

    # North-East
    mask = o & NOT_H
    x = mask & ((p & NOT_H) >> 7)
    x |= mask & (x >> 7)
    x |= mask & (x >> 7)
    x |= mask & (x >> 7)
    x |= mask & (x >> 7)
    x |= mask & (x >> 7)
    moves |= empty & (x >> 7)

    # North-West
    mask = o & NOT_A
    x = mask & ((p & NOT_A) >> 9)
    x |= mask & (x >> 9)
    x |= mask & (x >> 9)
    x |= mask & (x >> 9)
    x |= mask & (x >> 9)
    x |= mask & (x >> 9)
    moves |= empty & (x >> 9)

    return moves & FULL


def _flips(m, p, o):
    flips = 0

    cap = 0
    x = ((m & NOT_H) << 1) & o
    while x:
        cap |= x
        x = (x & NOT_H) << 1
        if x & p:
            flips |= cap
            break
        x &= o

    cap = 0
    x = ((m & NOT_A) >> 1) & o
    while x:
        cap |= x
        x = (x & NOT_A) >> 1
        if x & p:
            flips |= cap
            break
        x &= o

    cap = 0
    x = (m << 8) & o
    while x:
        cap |= x
        x <<= 8
        if x & p:
            flips |= cap
            break
        x &= o

    cap = 0
    x = (m >> 8) & o
    while x:
        cap |= x
        x >>= 8
        if x & p:
            flips |= cap
            break
        x &= o

    cap = 0
    x = ((m & NOT_H) << 9) & o
    while x:
        cap |= x
        x = (x & NOT_H) << 9
        if x & p:
            flips |= cap
            break
        x &= o

    cap = 0
    x = ((m & NOT_A) << 7) & o
    while x:
        cap |= x
        x = (x & NOT_A) << 7
        if x & p:
            flips |= cap
            break
        x &= o

    cap = 0
    x = ((m & NOT_H) >> 7) & o
    while x:
        cap |= x
        x = (x & NOT_H) >> 7
        if x & p:
            flips |= cap
            break
        x &= o

    cap = 0
    x = ((m & NOT_A) >> 9) & o
    while x:
        cap |= x
        x = (x & NOT_A) >> 9
        if x & p:
            flips |= cap
            break
        x &= o

    return flips


def _make_move(p, o, m):
    f = _flips(m, p, o)
    return p | m | f, o & ~f


def _psq_sum(bb):
    return (
        _BYTE_PSQ[0][bb & 255] +
        _BYTE_PSQ[1][(bb >> 8) & 255] +
        _BYTE_PSQ[2][(bb >> 16) & 255] +
        _BYTE_PSQ[3][(bb >> 24) & 255] +
        _BYTE_PSQ[4][(bb >> 32) & 255] +
        _BYTE_PSQ[5][(bb >> 40) & 255] +
        _BYTE_PSQ[6][(bb >> 48) & 255] +
        _BYTE_PSQ[7][(bb >> 56) & 255]
    )


def _adjacent(x):
    return (
        ((x & NOT_H) << 1) |
        ((x & NOT_A) >> 1) |
        (x << 8) |
        (x >> 8) |
        ((x & NOT_H) << 9) |
        ((x & NOT_A) << 7) |
        ((x & NOT_H) >> 7) |
        ((x & NOT_A) >> 9)
    ) & FULL


def _corner_danger(p, o, occ):
    score = 0
    for corner, x_sq, c_sqs in _CORNER_INFO:
        if not (occ & corner):
            score += 450 * ((o & x_sq).bit_count() - (p & x_sq).bit_count())
            score += 220 * ((o & c_sqs).bit_count() - (p & c_sqs).bit_count())
    return score


def _edge_stable_score(p, o):
    if not ((p | o) & CORNERS):
        return 0

    stable_p = 0
    stable_o = 0

    for corner_idx, ray1, ray2 in _STABLE_RAYS:
        cb = 1 << corner_idx
        if p & cb:
            mask = cb
            for sq in ray1:
                b = 1 << sq
                if p & b:
                    mask |= b
                else:
                    break
            for sq in ray2:
                b = 1 << sq
                if p & b:
                    mask |= b
                else:
                    break
            stable_p |= mask
        elif o & cb:
            mask = cb
            for sq in ray1:
                b = 1 << sq
                if o & b:
                    mask |= b
                else:
                    break
            for sq in ray2:
                b = 1 << sq
                if o & b:
                    mask |= b
                else:
                    break
            stable_o |= mask

    return stable_p.bit_count() - stable_o.bit_count()


def _evaluate(p, o, moves=None, opp_moves=None):
    occ = p | o
    empty = (~occ) & FULL
    empties = 64 - occ.bit_count()

    if moves is None:
        moves = _legal_moves(p, o)
    if opp_moves is None:
        opp_moves = _legal_moves(o, p)

    pc = p.bit_count()
    oc = o.bit_count()

    mobility = moves.bit_count() - opp_moves.bit_count()
    legal_corner = (moves & CORNERS).bit_count() - (opp_moves & CORNERS).bit_count()
    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()

    adj_p = _adjacent(p)
    adj_o = _adjacent(o)
    potential = (adj_o & empty).bit_count() - (adj_p & empty).bit_count()

    adj_empty = _adjacent(empty)
    frontier = (o & adj_empty).bit_count() - (p & adj_empty).bit_count()

    pos = _psq_sum(p) - _psq_sum(o)
    danger = _corner_danger(p, o, occ)
    stable = _edge_stable_score(p, o)

    if empties > 44:
        disc_w = -2
        mob_w = 85
        pot_w = 24
        front_w = 22
        pos_w = 4
        corner_w = 1300
        legal_corner_w = 900
        edge_w = 90
    elif empties > 24:
        disc_w = 1
        mob_w = 95
        pot_w = 18
        front_w = 20
        pos_w = 3
        corner_w = 1500
        legal_corner_w = 1000
        edge_w = 110
    elif empties > 12:
        disc_w = 10
        mob_w = 75
        pot_w = 10
        front_w = 10
        pos_w = 2
        corner_w = 1800
        legal_corner_w = 900
        edge_w = 130
    else:
        disc_w = 75
        mob_w = 30
        pot_w = 0
        front_w = 0
        pos_w = 1
        corner_w = 2000
        legal_corner_w = 500
        edge_w = 100

    return (
        disc_w * (pc - oc) +
        mob_w * mobility +
        pot_w * potential +
        front_w * frontier +
        pos_w * pos +
        corner_w * corner_diff +
        legal_corner_w * legal_corner +
        edge_w * stable +
        danger
    )


def _ordered_moves(p, o, moves, tt_move=0):
    occ = p | o
    arr = []
    mm = moves

    while mm:
        m = mm & -mm
        mm ^= m
        idx = m.bit_length() - 1

        score = _BASE_WEIGHTS[idx] * 20 + _HISTORY[idx]

        if m == tt_move:
            score += 100_000_000
        if m & CORNERS:
            score += 50_000_000

        for corner, x_sq, c_sqs in _CORNER_INFO:
            if not (occ & corner):
                if m & x_sq:
                    score -= 2_000_000
                if m & c_sqs:
                    score -= 800_000

        arr.append((score, m))

    arr.sort(reverse=True)
    return [m for _, m in arr]


def _fallback_move(p, o, moves):
    best = moves & -moves
    best_score = -INF
    occ = p | o
    mm = moves

    while mm:
        m = mm & -mm
        mm ^= m

        np_, no_ = _make_move(p, o, m)
        oppm = _legal_moves(no_, np_)
        ourm = _legal_moves(np_, no_)

        if oppm == 0 and ourm == 0:
            score = (np_.bit_count() - no_.bit_count()) * 1000
        elif oppm == 0:
            score = _evaluate(np_, no_, ourm, oppm) + 2500
        else:
            score = -_evaluate(no_, np_, oppm, ourm)

        idx = m.bit_length() - 1
        score += _BASE_WEIGHTS[idx] * 8
        score -= 40 * oppm.bit_count()

        if m & CORNERS:
            score += 12000
        if oppm & CORNERS:
            score -= 15000 * (oppm & CORNERS).bit_count()

        for corner, x_sq, c_sqs in _CORNER_INFO:
            if not (occ & corner):
                if m & x_sq:
                    score -= 7000
                if m & c_sqs:
                    score -= 3000

        if score > best_score:
            best_score = score
            best = m

    return best


def _negamax(p, o, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()

    moves = _legal_moves(p, o)

    if moves == 0:
        opp_moves = _legal_moves(o, p)
        if opp_moves == 0:
            return (p.bit_count() - o.bit_count()) * WIN_UNIT
        # Passing does not consume search depth.
        return -_negamax(o, p, depth, -beta, -alpha)

    if depth <= 0:
        return _evaluate(p, o, moves, None)

    key = (p, o)
    entry = _TT.get(key)
    tt_move = 0

    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:      # exact
                return e_val
            elif e_flag == 1:    # lower bound
                if e_val > alpha:
                    alpha = e_val
            else:                # upper bound
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    alpha0 = alpha
    beta0 = beta
    best_val = -INF
    best_move = 0
    cutoff = False

    for m in _ordered_moves(p, o, moves, tt_move):
        np_, no_ = _make_move(p, o, m)
        val = -_negamax(no_, np_, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val
            if alpha >= beta:
                _HISTORY[m.bit_length() - 1] += depth * depth
                cutoff = True
                break

    if cutoff or best_val >= beta0:
        flag = 1      # lower bound
    elif best_val <= alpha0:
        flag = 2      # upper bound
    else:
        flag = 0      # exact

    old = _TT.get(key)
    if old is None or depth >= old[0]:
        _TT[key] = (depth, best_val, flag, best_move)

    return best_val


def _root_search(p, o, depth, previous_best):
    moves = _legal_moves(p, o)
    ordered = _ordered_moves(p, o, moves, previous_best)

    best_move = ordered[0]
    best_val = -INF
    alpha = -INF
    beta = INF

    for m in ordered:
        np_, no_ = _make_move(p, o, m)
        val = -_negamax(no_, np_, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m

        if val > alpha:
            alpha = val

    return best_val, best_move


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _TT, _HISTORY, _DEADLINE, _NODES

    p = 0
    o = 0
    moves = 0
    best = 0

    _DEADLINE = time.perf_counter() + 0.88

    try:
        p, o = _arrays_to_bits(you, opponent)
        moves = _legal_moves(p, o)

        if moves == 0:
            return "pass"

        if (moves & (moves - 1)) == 0:
            return _move_to_str(moves)

        # Legal, fast fallback before any expensive search.
        best = _fallback_move(p, o, moves)

        _TT = {}
        _HISTORY = [0] * 64
        _NODES = 0

        empties = 64 - (p | o).bit_count()

        # Iterative deepening; if empties is small this can become exact solving.
        for depth in range(1, empties + 1):
            if time.perf_counter() > _DEADLINE:
                break

            _, bm = _root_search(p, o, depth, best)
            if bm & moves:
                best = bm

            if depth >= empties:
                break

        if not (best & moves):
            best = moves & -moves

        return _move_to_str(best)

    except _SearchTimeout:
        if moves:
            if not (best & moves):
                best = moves & -moves
            return _move_to_str(best)
        return "pass"

    except Exception:
        # Last-resort legality safeguard.
        try:
            if not moves:
                p, o = _arrays_to_bits(you, opponent)
                moves = _legal_moves(p, o)
            if moves:
                corner_moves = moves & CORNERS
                if corner_moves:
                    return _move_to_str(corner_moves & -corner_moves)
                return _move_to_str(moves & -moves)
            return "pass"
        except Exception:
            return "pass"
