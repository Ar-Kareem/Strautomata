
import time
import numpy as np

FULL = (1 << 64) - 1
FILE_A = sum(1 << (8 * r) for r in range(8))
FILE_H = sum(1 << (8 * r + 7) for r in range(8))
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

# Positional values, row-major, with row 0 = rank 1.
_POS_TABLE = (
    120, -25,  25,   8,   8,  25, -25, 120,
    -25, -60,  -8,  -6,  -6,  -8, -60, -25,
     25,  -8,  18,   4,   4,  18,  -8,  25,
      8,  -6,   4,   2,   2,   4,  -6,   8,
      8,  -6,   4,   2,   2,   4,  -6,   8,
     25,  -8,  18,   4,   4,  18,  -8,  25,
    -25, -60,  -8,  -6,  -6,  -8, -60, -25,
    120, -25,  25,   8,   8,  25, -25, 120,
)
_MOVE_ORDER = tuple(v * 100 for v in _POS_TABLE)

_CORNER_ADJ = (
    (1 << 0,  (1 << 1)  | (1 << 8)  | (1 << 9)),
    (1 << 7,  (1 << 6)  | (1 << 15) | (1 << 14)),
    (1 << 56, (1 << 48) | (1 << 57) | (1 << 49)),
    (1 << 63, (1 << 55) | (1 << 62) | (1 << 54)),
)

_DIRS = (1, -1, 8, -8, 9, -9, 7, -7)
_INF = 10 ** 9
_WIN = 10 ** 6
_TT_LIMIT = 250000

_TT = {}
_DEADLINE = 0.0
_NODES = 0


class _SearchTimeout(Exception):
    pass


def _make_psq_byte():
    out = []
    for row in range(8):
        arr = []
        base = row * 8
        for b in range(256):
            s = 0
            for c in range(8):
                if b & (1 << c):
                    s += _POS_TABLE[base + c]
            arr.append(s)
        out.append(arr)
    return out


_PSQ_BYTE = _make_psq_byte()


def _make_stable_byte_counts():
    arr = []
    for b in range(256):
        mask = 0
        if b & 1:
            for i in range(8):
                if b & (1 << i):
                    mask |= 1 << i
                else:
                    break
        if b & 128:
            for i in range(7, -1, -1):
                if b & (1 << i):
                    mask |= 1 << i
                else:
                    break
        arr.append(mask.bit_count())
    return arr


_STABLE_BYTE_COUNT = _make_stable_byte_counts()


def _array_to_bitboard(a):
    flat = np.asarray(a).ravel()
    bb = 0
    for i in range(64):
        if flat[i]:
            bb |= 1 << i
    return bb


def _move_to_str(move):
    i = move.bit_length() - 1
    return chr(97 + (i & 7)) + str((i >> 3) + 1)


def _shift(x, d):
    if d == 1:
        return ((x & NOT_H) << 1) & FULL
    if d == -1:
        return (x & NOT_A) >> 1
    if d == 8:
        return (x << 8) & FULL
    if d == -8:
        return x >> 8
    if d == 9:
        return ((x & NOT_H) << 9) & FULL
    if d == -9:
        return (x & NOT_A) >> 9
    if d == 7:
        return ((x & NOT_A) << 7) & FULL
    if d == -7:
        return (x & NOT_H) >> 7
    return 0


def _neighbors(x):
    return (
        _shift(x, 1) | _shift(x, -1) | _shift(x, 8) | _shift(x, -8) |
        _shift(x, 9) | _shift(x, -9) | _shift(x, 7) | _shift(x, -7)
    )


def _legal_moves(p, o):
    empty = (~(p | o)) & FULL
    moves = 0

    # East
    t = ((p & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    t |= ((t & NOT_H) << 1) & o
    moves |= ((t & NOT_H) << 1) & empty

    # West
    t = ((p & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    t |= ((t & NOT_A) >> 1) & o
    moves |= ((t & NOT_A) >> 1) & empty

    # South
    t = (p << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    t |= (t << 8) & o
    moves |= (t << 8) & empty

    # North
    t = (p >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    t |= (t >> 8) & o
    moves |= (t >> 8) & empty

    # South-east
    t = ((p & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    t |= ((t & NOT_H) << 9) & o
    moves |= ((t & NOT_H) << 9) & empty

    # North-west
    t = ((p & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    t |= ((t & NOT_A) >> 9) & o
    moves |= ((t & NOT_A) >> 9) & empty

    # South-west
    t = ((p & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    t |= ((t & NOT_A) << 7) & o
    moves |= ((t & NOT_A) << 7) & empty

    # North-east
    t = ((p & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    t |= ((t & NOT_H) >> 7) & o
    moves |= ((t & NOT_H) >> 7) & empty

    return moves & FULL


def _flips_for_move(move, p, o):
    flips = 0
    for d in _DIRS:
        captured = 0
        x = _shift(move, d) & o
        while x:
            captured |= x
            y = _shift(x, d)
            if y & p:
                flips |= captured
                break
            x = y & o
    return flips


def _weighted_sum(bb):
    return (
        _PSQ_BYTE[0][bb & 255] +
        _PSQ_BYTE[1][(bb >> 8) & 255] +
        _PSQ_BYTE[2][(bb >> 16) & 255] +
        _PSQ_BYTE[3][(bb >> 24) & 255] +
        _PSQ_BYTE[4][(bb >> 32) & 255] +
        _PSQ_BYTE[5][(bb >> 40) & 255] +
        _PSQ_BYTE[6][(bb >> 48) & 255] +
        _PSQ_BYTE[7][(bb >> 56) & 255]
    )


def _col_byte(bb, c):
    return (
        ((bb >> c) & 1) |
        (((bb >> (c + 8)) & 1) << 1) |
        (((bb >> (c + 16)) & 1) << 2) |
        (((bb >> (c + 24)) & 1) << 3) |
        (((bb >> (c + 32)) & 1) << 4) |
        (((bb >> (c + 40)) & 1) << 5) |
        (((bb >> (c + 48)) & 1) << 6) |
        (((bb >> (c + 56)) & 1) << 7)
    )


def _stable_edge_count(p):
    if not (p & CORNERS):
        return 0
    top = _STABLE_BYTE_COUNT[p & 255]
    bottom = _STABLE_BYTE_COUNT[(p >> 56) & 255]
    left = _STABLE_BYTE_COUNT[_col_byte(p, 0)]
    right = _STABLE_BYTE_COUNT[_col_byte(p, 7)]
    return top + bottom + left + right - (p & CORNERS).bit_count()


def _norm(a, b):
    s = a + b
    if s == 0:
        return 0
    d = a - b
    if d >= 0:
        return (100 * d) // s
    return -((100 * (-d)) // s)


def _final_value(diff):
    if diff > 0:
        return _WIN + diff
    if diff < 0:
        return -_WIN + diff
    return 0


def _evaluate(p, o, legal_p=None):
    occ = p | o
    empties = 64 - occ.bit_count()

    if legal_p is None:
        legal_p = _legal_moves(p, o)
    legal_o = _legal_moves(o, p)

    if legal_p == 0 and legal_o == 0:
        return _final_value(p.bit_count() - o.bit_count())

    disc_diff = p.bit_count() - o.bit_count()
    corner_diff = (p & CORNERS).bit_count() - (o & CORNERS).bit_count()

    mp = legal_p.bit_count()
    mo = legal_o.bit_count()
    mobility = _norm(mp, mo)

    empty = (~occ) & FULL
    pot_p = (empty & _neighbors(o)).bit_count()
    pot_o = (empty & _neighbors(p)).bit_count()
    potential = _norm(pot_p, pot_o)

    adj_empty = _neighbors(empty)
    front_p = (p & adj_empty).bit_count()
    front_o = (o & adj_empty).bit_count()
    frontier = _norm(front_p, front_o)

    psq = _weighted_sum(p) - _weighted_sum(o)
    stable = _stable_edge_count(p) - _stable_edge_count(o)

    corner_adj = 0
    for corner, adj in _CORNER_ADJ:
        pc = (p & adj).bit_count()
        oc = (o & adj).bit_count()
        if not (occ & corner):
            # Occupying squares next to an empty corner is usually dangerous.
            corner_adj -= 250 * (pc - oc)
        elif p & corner:
            corner_adj += 55 * pc + 25 * oc
        else:
            corner_adj -= 55 * oc + 25 * pc

    if empties > 44:
        score = (
            1000 * corner_diff + corner_adj +
            8 * mobility + 3 * potential - 4 * frontier +
            2 * psq + 45 * stable - 4 * disc_diff
        )
    elif empties > 16:
        score = (
            1100 * corner_diff + corner_adj +
            7 * mobility + 2 * potential - 3 * frontier +
            2 * psq + 55 * stable + disc_diff
        )
    else:
        score = (
            1250 * corner_diff + corner_adj +
            4 * mobility - 2 * frontier +
            psq + 70 * stable + 10 * disc_diff
        )
        if empties <= 12:
            score += 20 if (empties & 1) else -20

    return int(score)


def _ordered_moves(moves, p, o, tt_best=0):
    occ = p | o
    scored = []
    while moves:
        m = moves & -moves
        moves ^= m
        idx = m.bit_length() - 1
        s = _MOVE_ORDER[idx]

        if m == tt_best:
            s += 10_000_000
        if m & CORNERS:
            s += 1_000_000

        for corner, adj in _CORNER_ADJ:
            if m & adj:
                if not (occ & corner):
                    s -= 220_000
                elif p & corner:
                    s += 30_000
                else:
                    s -= 20_000

        scored.append((s, m))

    scored.sort(reverse=True)
    return [m for _, m in scored]


def _negamax(p, o, depth, alpha, beta):
    global _NODES

    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()

    key = p | (o << 64)
    entry = _TT.get(key)
    tt_best = 0

    if entry is not None:
        e_depth, e_val, e_flag, e_best = entry
        tt_best = e_best
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            if e_flag > 0:
                if e_val > alpha:
                    alpha = e_val
            else:
                if e_val < beta:
                    beta = e_val
            if alpha >= beta:
                return e_val

    alpha_start = alpha
    beta_start = beta

    legal = _legal_moves(p, o)

    if legal == 0:
        opp_legal = _legal_moves(o, p)
        if opp_legal == 0:
            val = _final_value(p.bit_count() - o.bit_count())
        else:
            val = -_negamax(o, p, depth, -beta, -alpha)

        old = _TT.get(key)
        if (len(_TT) < _TT_LIMIT or old is not None) and (old is None or old[0] <= depth):
            _TT[key] = (depth, val, 0, 0)
        return val

    if depth <= 0:
        return _evaluate(p, o, legal)

    best_val = -_INF
    best_move = 0

    for m in _ordered_moves(legal, p, o, tt_best):
        flips = _flips_for_move(m, p, o)
        p2 = p | m | flips
        o2 = o & ~flips

        val = -_negamax(o2, p2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    flag = 0
    if best_val <= alpha_start:
        flag = -1
    elif best_val >= beta_start:
        flag = 1

    old = _TT.get(key)
    if (len(_TT) < _TT_LIMIT or old is not None) and (old is None or old[0] <= depth):
        _TT[key] = (depth, best_val, flag, best_move)

    return best_val


def _search_root(p, o, legal, depth, first_move):
    if time.perf_counter() > _DEADLINE:
        raise _SearchTimeout()

    alpha = -_INF
    beta = _INF
    best_val = -_INF
    best_move = 0

    for m in _ordered_moves(legal, p, o, first_move):
        if time.perf_counter() > _DEADLINE:
            raise _SearchTimeout()

        flips = _flips_for_move(m, p, o)
        p2 = p | m | flips
        o2 = o & ~flips

        val = -_negamax(o2, p2, depth - 1, -beta, -alpha)

        if val > best_val:
            best_val = val
            best_move = m
        if val > alpha:
            alpha = val

    return best_val, best_move


def _fallback_move(legal, p, o):
    best_move = legal & -legal
    best_val = -_INF

    for m in _ordered_moves(legal, p, o, 0):
        flips = _flips_for_move(m, p, o)
        if flips == 0:
            continue

        p2 = p | m | flips
        o2 = o & ~flips
        opp_legal = _legal_moves(o2, p2)

        if opp_legal:
            val = -_evaluate(o2, p2, opp_legal)
            if opp_legal & CORNERS:
                val -= 800
        else:
            my_legal = _legal_moves(p2, o2)
            if my_legal:
                val = _evaluate(p2, o2, my_legal) + 150
            else:
                val = _final_value(p2.bit_count() - o2.bit_count())

        if m & CORNERS:
            val += 600

        if val > best_val:
            best_val = val
            best_move = m

    return best_move


def _policy_impl(you, opponent):
    global _TT, _DEADLINE, _NODES

    p = _array_to_bitboard(you)
    o = _array_to_bitboard(opponent)

    legal = _legal_moves(p, o)
    if legal == 0:
        return "pass"

    if legal & (legal - 1) == 0:
        return _move_to_str(legal)

    _TT = {}
    _NODES = 0
    _DEADLINE = time.perf_counter() + 0.88

    best = _fallback_move(legal, p, o)
    hint = best

    empties = 64 - (p | o).bit_count()
    legal_count = legal.bit_count()

    if empties <= 14:
        max_depth = empties
    elif empties <= 20:
        max_depth = 11
    elif empties <= 28:
        max_depth = 9
    elif empties <= 44:
        max_depth = 7
    else:
        max_depth = 6

    if empties > 14:
        if legal_count <= 4:
            max_depth += 2
        elif legal_count <= 8:
            max_depth += 1

    for depth in range(1, max_depth + 1):
        try:
            _, move = _search_root(p, o, legal, depth, hint)
            if move:
                best = move
                hint = move
            if depth >= empties:
                break
            if time.perf_counter() > _DEADLINE - 0.01:
                break
        except _SearchTimeout:
            break

    return _move_to_str(best)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    try:
        return _policy_impl(you, opponent)
    except Exception:
        # Last-resort safety: still return a legal move if anything unexpected occurs.
        try:
            p = _array_to_bitboard(you)
            o = _array_to_bitboard(opponent)
            legal = _legal_moves(p, o)
            if legal:
                return _move_to_str(legal & -legal)
            return "pass"
        except Exception:
            return "pass"
