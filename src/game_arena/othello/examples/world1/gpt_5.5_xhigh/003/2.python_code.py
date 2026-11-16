
import time
import numpy as np

FULL = (1 << 64) - 1
A_FILE = 0x0101010101010101
H_FILE = 0x8080808080808080
NOT_A_FILE = FULL ^ A_FILE
NOT_H_FILE = FULL ^ H_FILE

BITS = tuple(1 << i for i in range(64))
FILES = "abcdefgh"

CORNERS = BITS[0] | BITS[7] | BITS[56] | BITS[63]
BORDER = 0xFF | (0xFF << 56) | A_FILE | H_FILE
EDGES = BORDER & ~CORNERS
X_SQUARES = BITS[9] | BITS[14] | BITS[49] | BITS[54]

_CORNER_ADJ = (
    (BITS[0],  BITS[1] | BITS[8] | BITS[9],   BITS[9]),
    (BITS[7],  BITS[6] | BITS[14] | BITS[15], BITS[14]),
    (BITS[56], BITS[48] | BITS[49] | BITS[57], BITS[49]),
    (BITS[63], BITS[54] | BITS[55] | BITS[62], BITS[54]),
)

_POS = (
    120, -30,  20,   5,   5,  20, -30, 120,
    -30, -70,  -5,  -5,  -5,  -5, -70, -30,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -30, -70,  -5,  -5,  -5,  -5, -70, -30,
    120, -30,  20,   5,   5,  20, -30, 120,
)

def _build_pos_tables():
    tabs = []
    for chunk in range(4):
        offset = chunk * 16
        table = [0] * 65536
        for mask in range(1, 65536):
            lsb = mask & -mask
            table[mask] = table[mask ^ lsb] + _POS[offset + lsb.bit_length() - 1]
        tabs.append(table)
    return tuple(tabs)

_POS_TABLES = _build_pos_tables()

_ORDER = []
for i, w in enumerate(_POS):
    b = BITS[i]
    s = w
    if b & CORNERS:
        s += 100000
    elif b & EDGES:
        s += 1000
    if b & X_SQUARES:
        s -= 2000
    _ORDER.append(s)
_ORDER = tuple(_ORDER)

INF = 1_000_000_000
WIN = 10_000_000
EXACT, LOWER, UPPER = 0, 1, 2

_TT = {}
_TT_LIMIT = 350000
_DEADLINE = 0.0
_NODES = 0
_CLOCK = time.perf_counter

class _Timeout(Exception):
    pass

def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and _CLOCK() >= _DEADLINE:
        raise _Timeout()

def _arrays_to_bits(you, opponent):
    yf = np.asarray(you).ravel()
    of = np.asarray(opponent).ravel()
    p = 0
    o = 0
    bits = BITS
    for i in range(64):
        if yf[i]:
            p |= bits[i]
        elif of[i]:
            o |= bits[i]
    return p, o

def _legal_moves(P, O):
    empty = ~(P | O) & FULL
    moves = 0
    notA = NOT_A_FILE
    notH = NOT_H_FILE

    t = O & ((P & notH) << 1)
    t |= O & ((t & notH) << 1)
    t |= O & ((t & notH) << 1)
    t |= O & ((t & notH) << 1)
    t |= O & ((t & notH) << 1)
    t |= O & ((t & notH) << 1)
    moves |= empty & ((t & notH) << 1)

    t = O & ((P & notA) >> 1)
    t |= O & ((t & notA) >> 1)
    t |= O & ((t & notA) >> 1)
    t |= O & ((t & notA) >> 1)
    t |= O & ((t & notA) >> 1)
    t |= O & ((t & notA) >> 1)
    moves |= empty & ((t & notA) >> 1)

    t = O & (P >> 8)
    t |= O & (t >> 8)
    t |= O & (t >> 8)
    t |= O & (t >> 8)
    t |= O & (t >> 8)
    t |= O & (t >> 8)
    moves |= empty & (t >> 8)

    t = O & (P << 8)
    t |= O & (t << 8)
    t |= O & (t << 8)
    t |= O & (t << 8)
    t |= O & (t << 8)
    t |= O & (t << 8)
    moves |= empty & (t << 8)

    t = O & ((P & notH) >> 7)
    t |= O & ((t & notH) >> 7)
    t |= O & ((t & notH) >> 7)
    t |= O & ((t & notH) >> 7)
    t |= O & ((t & notH) >> 7)
    t |= O & ((t & notH) >> 7)
    moves |= empty & ((t & notH) >> 7)

    t = O & ((P & notA) >> 9)
    t |= O & ((t & notA) >> 9)
    t |= O & ((t & notA) >> 9)
    t |= O & ((t & notA) >> 9)
    t |= O & ((t & notA) >> 9)
    t |= O & ((t & notA) >> 9)
    moves |= empty & ((t & notA) >> 9)

    t = O & ((P & notH) << 9)
    t |= O & ((t & notH) << 9)
    t |= O & ((t & notH) << 9)
    t |= O & ((t & notH) << 9)
    t |= O & ((t & notH) << 9)
    t |= O & ((t & notH) << 9)
    moves |= empty & ((t & notH) << 9)

    t = O & ((P & notA) << 7)
    t |= O & ((t & notA) << 7)
    t |= O & ((t & notA) << 7)
    t |= O & ((t & notA) << 7)
    t |= O & ((t & notA) << 7)
    t |= O & ((t & notA) << 7)
    moves |= empty & ((t & notA) << 7)

    return moves

def _neighbors(x):
    return (
        ((x & NOT_H_FILE) << 1) |
        ((x & NOT_A_FILE) >> 1) |
        (x << 8) |
        (x >> 8) |
        ((x & NOT_H_FILE) << 9) |
        ((x & NOT_A_FILE) << 7) |
        ((x & NOT_H_FILE) >> 7) |
        ((x & NOT_A_FILE) >> 9)
    ) & FULL

def _make_move(P, O, m):
    flips = 0
    notA = NOT_A_FILE
    notH = NOT_H_FILE

    cap = 0
    x = (m & notH) << 1
    while x & O:
        cap |= x
        x = (x & notH) << 1
    if x & P:
        flips |= cap

    cap = 0
    x = (m & notA) >> 1
    while x & O:
        cap |= x
        x = (x & notA) >> 1
    if x & P:
        flips |= cap

    cap = 0
    x = m >> 8
    while x & O:
        cap |= x
        x >>= 8
    if x & P:
        flips |= cap

    cap = 0
    x = m << 8
    while x & O:
        cap |= x
        x <<= 8
    if x & P:
        flips |= cap

    cap = 0
    x = (m & notH) >> 7
    while x & O:
        cap |= x
        x = (x & notH) >> 7
    if x & P:
        flips |= cap

    cap = 0
    x = (m & notA) >> 9
    while x & O:
        cap |= x
        x = (x & notA) >> 9
    if x & P:
        flips |= cap

    cap = 0
    x = (m & notH) << 9
    while x & O:
        cap |= x
        x = (x & notH) << 9
    if x & P:
        flips |= cap

    cap = 0
    x = (m & notA) << 7
    while x & O:
        cap |= x
        x = (x & notA) << 7
    if x & P:
        flips |= cap

    return P | m | flips, O ^ flips

def _pos_sum(B):
    tabs = _POS_TABLES
    return (
        tabs[0][B & 0xFFFF] +
        tabs[1][(B >> 16) & 0xFFFF] +
        tabs[2][(B >> 32) & 0xFFFF] +
        tabs[3][(B >> 48) & 0xFFFF]
    )

def _edge_stability(B):
    bits = BITS
    stable = 0

    if B & bits[0]:
        i = 0
        while i < 8 and (B & bits[i]):
            stable |= bits[i]
            i += 1
        i = 0
        while i < 64 and (B & bits[i]):
            stable |= bits[i]
            i += 8

    if B & bits[7]:
        i = 7
        while i >= 0 and (B & bits[i]):
            stable |= bits[i]
            i -= 1
        i = 7
        while i < 64 and (B & bits[i]):
            stable |= bits[i]
            i += 8

    if B & bits[56]:
        i = 56
        while i < 64 and (B & bits[i]):
            stable |= bits[i]
            i += 1
        i = 56
        while i >= 0 and (B & bits[i]):
            stable |= bits[i]
            i -= 8

    if B & bits[63]:
        i = 63
        while i >= 56 and (B & bits[i]):
            stable |= bits[i]
            i -= 1
        i = 63
        while i >= 0 and (B & bits[i]):
            stable |= bits[i]
            i -= 8

    return stable.bit_count()

def _final_value(P, O):
    diff = P.bit_count() - O.bit_count()
    if diff > 0:
        return WIN + diff
    if diff < 0:
        return -WIN + diff
    return 0

def _evaluate(P, O, my_moves_bb=None, opp_moves_bb=None):
    if my_moves_bb is None:
        my_moves_bb = _legal_moves(P, O)
    if opp_moves_bb is None:
        opp_moves_bb = _legal_moves(O, P)

    my_moves = my_moves_bb.bit_count()
    opp_moves = opp_moves_bb.bit_count()

    my_discs = P.bit_count()
    opp_discs = O.bit_count()
    empties = 64 - my_discs - opp_discs
    occ = P | O
    empty = (~occ) & FULL

    if empties > 44:
        mob_w, pot_w, front_w, disc_w, pos_w, edge_w, close_w, corner_w = 95, 18, 14, -4, 5, 8, 360, 3000
    elif empties > 18:
        mob_w, pot_w, front_w, disc_w, pos_w, edge_w, close_w, corner_w = 85, 12, 12, 2, 4, 12, 300, 3500
    else:
        mob_w, pot_w, front_w, disc_w, pos_w, edge_w, close_w, corner_w = 45, 4, 6, 24, 2, 20, 160, 4000

    score = 0

    score += corner_w * ((P & CORNERS).bit_count() - (O & CORNERS).bit_count())
    score += (corner_w // 2) * ((my_moves_bb & CORNERS).bit_count() - (opp_moves_bb & CORNERS).bit_count())

    score += mob_w * (my_moves - opp_moves)
    if opp_moves == 0 and my_moves:
        score += 700
    if my_moves == 0 and opp_moves:
        score -= 700

    score += pos_w * (_pos_sum(P) - _pos_sum(O))
    score += edge_w * ((P & EDGES).bit_count() - (O & EDGES).bit_count())

    nO = _neighbors(O)
    nP = _neighbors(P)
    score += pot_w * ((empty & nO).bit_count() - (empty & nP).bit_count())

    near_empty = _neighbors(empty)
    score += front_w * ((O & near_empty).bit_count() - (P & near_empty).bit_count())

    danger = 0
    safe_adj = 0
    for corner, adj, x in _CORNER_ADJ:
        if not (occ & corner):
            danger += (P & adj).bit_count() - (O & adj).bit_count()
            danger += (P & x).bit_count() - (O & x).bit_count()
        elif P & corner:
            safe_adj += (P & adj).bit_count()
        else:
            safe_adj -= (O & adj).bit_count()

    score -= close_w * danger
    score += 70 * safe_adj

    if occ & CORNERS:
        score += 75 * (_edge_stability(P) - _edge_stability(O))

    score += disc_w * (my_discs - opp_discs)

    if empties <= 16:
        score += 30 if (empties & 1) else -30

    return score

def _static_value(P, O, moves_bb=None):
    if moves_bb is None:
        moves_bb = _legal_moves(P, O)
    if moves_bb:
        return _evaluate(P, O, moves_bb, None)

    om = _legal_moves(O, P)
    if not om:
        return _final_value(P, O)
    return -_evaluate(O, P, om, None)

def _ordered_moves(moves, P, O, tt_move, depth):
    if (moves & (moves - 1)) == 0:
        return [moves]

    occ = P | O
    arr = []
    mm = moves

    while mm:
        m = mm & -mm
        mm ^= m

        if m == tt_move:
            score = 100000000
        else:
            idx = m.bit_length() - 1
            score = _ORDER[idx]

            for corner, adj, x in _CORNER_ADJ:
                if not (occ & corner):
                    if m & adj:
                        score -= 30000
                    if m & x:
                        score -= 30000
                elif P & corner:
                    if m & adj:
                        score += 2000

            if depth >= 5:
                P2, O2 = _make_move(P, O, m)
                om = _legal_moves(O2, P2)
                om_count = om.bit_count()
                score -= 25 * om_count
                score -= 3000 * ((om & CORNERS).bit_count())
                if om == 0:
                    score += 5000

        arr.append((score, m))

    arr.sort(reverse=True)
    return [m for _, m in arr]

def _alphabeta(P, O, depth, alpha, beta):
    _check_time()

    key = (P, O)
    alpha0 = alpha
    beta0 = beta

    entry = _TT.get(key)
    tt_move = 0
    if entry is not None:
        tt_move = entry[3]
        if entry[0] >= depth:
            val, flag = entry[1], entry[2]
            if flag == EXACT:
                return val
            if flag == LOWER:
                if val > alpha:
                    alpha = val
            elif flag == UPPER:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    moves = _legal_moves(P, O)

    if moves == 0:
        opp_moves = _legal_moves(O, P)
        if opp_moves == 0:
            val = _final_value(P, O)
            flag = EXACT
        else:
            val = -_alphabeta(O, P, depth, -beta, -alpha)
            if val <= alpha0:
                flag = UPPER
            elif val >= beta0:
                flag = LOWER
            else:
                flag = EXACT
        if depth > 0:
            _TT[key] = (depth, val, flag, 0)
        return val

    if depth <= 0:
        return _evaluate(P, O, moves, None)

    best = -INF
    best_move = tt_move if (tt_move & moves) else 0
    ordered = _ordered_moves(moves, P, O, best_move, depth)

    for m in ordered:
        P2, O2 = _make_move(P, O, m)
        val = -_alphabeta(O2, P2, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    if best <= alpha0:
        flag = UPPER
    elif best >= beta0:
        flag = LOWER
    else:
        flag = EXACT

    _TT[key] = (depth, best, flag, best_move)
    return best

def _root_order(P, O, moves):
    arr = []
    mm = moves
    while mm:
        m = mm & -mm
        mm ^= m
        P2, O2 = _make_move(P, O, m)
        val = -_static_value(O2, P2, _legal_moves(O2, P2))
        val += _ORDER[m.bit_length() - 1] // 8
        arr.append((val, m))
    arr.sort(reverse=True)
    return [m for _, m in arr]

def _root_search(P, O, depth, root_order, hint):
    alpha = -INF
    beta = INF
    best = -INF
    best_move = hint if hint else root_order[0]

    if hint and hint in root_order:
        ordered = [hint] + [m for m in root_order if m != hint]
    else:
        ordered = root_order

    for m in ordered:
        if _CLOCK() >= _DEADLINE:
            raise _Timeout()

        P2, O2 = _make_move(P, O, m)
        val = -_alphabeta(O2, P2, depth - 1, -beta, -alpha)

        if val > best:
            best = val
            best_move = m
        if val > alpha:
            alpha = val

    _TT[(P, O)] = (depth, best, EXACT, best_move)
    return best, best_move

def _move_to_str(m):
    if not m:
        return "pass"
    i = m.bit_length() - 1
    return FILES[i & 7] + str((i >> 3) + 1)

def _policy_impl(you, opponent):
    global _DEADLINE, _NODES

    _DEADLINE = _CLOCK() + 0.90
    _NODES = 0

    if len(_TT) > _TT_LIMIT:
        _TT.clear()

    P, O = _arrays_to_bits(you, opponent)
    moves = _legal_moves(P, O)

    if moves == 0:
        return "pass"

    first = moves & -moves
    if (moves & (moves - 1)) == 0:
        return _move_to_str(first)

    root_order = _root_order(P, O, moves)
    fallback = root_order[0]
    hint = fallback

    entry = _TT.get((P, O))
    if entry is not None and (entry[3] & moves):
        hint = entry[3]

    best_move = fallback
    empties = 64 - (P | O).bit_count()
    move_count = moves.bit_count()

    if empties <= 20:
        max_depth = empties
    elif empties <= 28:
        max_depth = 16
    elif empties <= 44:
        max_depth = 11
    else:
        max_depth = 9

    if move_count <= 3:
        max_depth = min(empties, max_depth + 4)
    elif move_count <= 5:
        max_depth = min(empties, max_depth + 2)

    for depth in range(1, max_depth + 1):
        if _CLOCK() >= _DEADLINE - 0.018:
            break
        try:
            _, m = _root_search(P, O, depth, root_order, hint)
            if m & moves:
                best_move = m
                hint = m
            if depth >= empties:
                break
        except _Timeout:
            break

    if not (best_move & moves):
        best_move = first

    return _move_to_str(best_move)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    try:
        return _policy_impl(you, opponent)
    except Exception:
        try:
            P, O = _arrays_to_bits(you, opponent)
            moves = _legal_moves(P, O)
            if moves:
                return _move_to_str(moves & -moves)
        except Exception:
            pass
        return "pass"
