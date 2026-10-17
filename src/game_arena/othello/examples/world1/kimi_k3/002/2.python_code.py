
import time
import numpy as np

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

# Positive d means left-shift; negative d means right-shift. Mask clears file-wrap destinations.
DIRS = (
    (1, NOT_A), (-1, NOT_H),
    (8, FULL), (-8, FULL),
    (9, NOT_A), (7, NOT_H),
    (-7, NOT_A), (-9, NOT_H),
)

W = (
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
)

BYTEW = tuple(
    tuple(sum(W[pos * 8 + k] for k in range(8) if (byte >> k) & 1) for byte in range(256))
    for pos in range(8)
)

ORDER_VAL = list(W)
for _i in (0, 7, 56, 63):
    ORDER_VAL[_i] += 10000
SQUARE_ORDER = tuple(
    sorted((1 << i for i in range(64)), key=lambda b: ORDER_VAL[b.bit_length() - 1], reverse=True)
)

_pc = getattr(int, "bit_count", None)
if _pc is None:
    def POPCOUNT(x): return bin(x).count("1")
else:
    POPCOUNT = _pc

INF = 10 ** 9
TERM = 10000
TIME_LIMIT = 0.90
EXACT_EMPTY = 14
TT = {}
EXACT_TT = {}
NODES = 0
DEADLINE = 0.0

class _Timeout(Exception):
    pass

def _sq(r, c):
    return 1 << (r * 8 + c)

CORNER_ADJ = (
    (_sq(0, 0), ((_sq(0, 1), 34), (_sq(1, 0), 34), (_sq(1, 1), 88))),
    (_sq(0, 7), ((_sq(0, 6), 34), (_sq(1, 7), 34), (_sq(1, 6), 88))),
    (_sq(7, 0), ((_sq(6, 0), 34), (_sq(7, 1), 34), (_sq(6, 1), 88))),
    (_sq(7, 7), ((_sq(7, 6), 34), (_sq(6, 7), 34), (_sq(6, 6), 88))),
)

EDGE_RAYS = (
    tuple(_sq(0, c) for c in range(8)),
    tuple(_sq(r, 0) for r in range(8)),
    tuple(_sq(0, c) for c in range(7, -1, -1)),
    tuple(_sq(r, 7) for r in range(8)),
    tuple(_sq(7, c) for c in range(8)),
    tuple(_sq(r, 0) for r in range(7, -1, -1)),
    tuple(_sq(7, c) for c in range(7, -1, -1)),
    tuple(_sq(r, 7) for r in range(7, -1, -1)),
)

def _bits_from_array(a):
    b = 0
    for i, v in enumerate(a.reshape(64)):
        if v:
            b |= 1 << i
    return b

def _bits(b):
    while b:
        lsb = b & -b
        yield lsb
        b ^= lsb

def _move_str(bit):
    i = bit.bit_length() - 1
    return chr(97 + (i & 7)) + str((i >> 3) + 1)

def legal_moves(me, opp):
    empty = FULL ^ (me | opp)
    moves = 0
    for d, mask in DIRS:
        if d > 0:
            x = (((me << d) & FULL) & mask) & opp
            for _ in range(5):
                x |= (((x << d) & FULL) & mask) & opp
            moves |= (((x << d) & FULL) & mask) & empty
        else:
            s = -d
            x = ((me >> s) & mask) & opp
            for _ in range(5):
                x |= ((x >> s) & mask) & opp
            moves |= ((x >> s) & mask) & empty
    return moves

def _do_move(me, opp, bit):
    flips = 0
    for d, mask in DIRS:
        if d > 0:
            x = (((bit << d) & FULL) & mask) & opp
            for _ in range(5):
                x |= (((x << d) & FULL) & mask) & opp
            if (((x << d) & FULL) & mask) & me:
                flips |= x
        else:
            s = -d
            x = ((bit >> s) & mask) & opp
            for _ in range(5):
                x |= ((x >> s) & mask) & opp
            if ((x >> s) & mask) & me:
                flips |= x
    new_me = me | bit | flips
    new_opp = opp & ~flips
    return new_opp, new_me, flips

def _neighbors(b):
    return (
        (((b << 1) & FULL) & NOT_A) |
        ((b >> 1) & NOT_H) |
        ((b << 8) & FULL) |
        (b >> 8) |
        (((b << 9) & FULL) & NOT_A) |
        (((b << 7) & FULL) & NOT_H) |
        ((b >> 7) & NOT_A) |
        ((b >> 9) & NOT_H)
    )

def _wsum(b):
    return (
        BYTEW[0][b & 255] + BYTEW[1][(b >> 8) & 255] +
        BYTEW[2][(b >> 16) & 255] + BYTEW[3][(b >> 24) & 255] +
        BYTEW[4][(b >> 32) & 255] + BYTEW[5][(b >> 40) & 255] +
        BYTEW[6][(b >> 48) & 255] + BYTEW[7][(b >> 56) & 255]
    )

def _edge_stable_count(color):
    sm = 0
    for ray in EDGE_RAYS:
        if color & ray[0]:
            for bit in ray:
                if color & bit:
                    sm |= bit
                else:
                    break
    return POPCOUNT(sm)

def _evaluate(me, opp):
    occ = me | opp
    empty = FULL ^ occ
    empties = 64 - POPCOUNT(occ)
    if empties == 0:
        return (POPCOUNT(me) - POPCOUNT(opp)) * TERM

    my_moves = legal_moves(me, opp)
    op_moves = legal_moves(opp, me)
    mob = POPCOUNT(my_moves) - POPCOUNT(op_moves)

    pos = _wsum(me) - _wsum(opp)
    disc = POPCOUNT(me) - POPCOUNT(opp)

    adj_empty = _neighbors(empty)
    frontier = POPCOUNT(me & adj_empty) - POPCOUNT(opp & adj_empty)
    potential = POPCOUNT(_neighbors(opp) & empty) - POPCOUNT(_neighbors(me) & empty)

    corners = POPCOUNT(me & CORNERS) - POPCOUNT(opp & CORNERS)
    corner_pen = 0
    for cbit, adj in CORNER_ADJ:
        if not (occ & cbit):
            for abit, pen in adj:
                if me & abit:
                    corner_pen += pen
                elif opp & abit:
                    corner_pen -= pen

    if empties <= 28:
        stable = _edge_stable_count(me) - _edge_stable_count(opp)
    else:
        stable = 0

    if empties > 40:
        return (pos * 4 + mob * 46 + potential * 8 - frontier * 14 +
                corners * 145 - corner_pen + disc + stable * 0)
    if empties > 22:
        return (pos * 5 + mob * 33 + potential * 6 - frontier * 10 +
                corners * 190 - corner_pen + disc * 4 + stable * 16)
    if empties > 10:
        return (pos * 3 + mob * 21 + potential * 4 - frontier * 6 +
                corners * 230 - corner_pen + disc * 26 + stable * 34)
    return (pos + mob * 10 + potential * 2 - frontier * 3 +
            corners * 150 - corner_pen + disc * 105 + stable * 60)

def _order_bits(moves, first=0, second=0):
    out = []
    used = 0
    if first and (moves & first):
        out.append(first); used |= first
    if second and (moves & second) and not (used & second):
        out.append(second); used |= second
    for b in SQUARE_ORDER:
        if (moves & b) and not (used & b):
            out.append(b); used |= b
    return out

def _negamax(me, opp, depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise _Timeout()

    key = (me, opp)
    ent = TT.get(key)
    tt_move = 0
    if ent is not None:
        ed, ev, ef, eb = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1:
                if ev > alpha:
                    alpha = ev
            else:
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev
        tt_move = eb

    moves = legal_moves(me, opp)
    if moves == 0:
        if legal_moves(opp, me) == 0:
            return (POPCOUNT(me) - POPCOUNT(opp)) * TERM
        if depth <= 0:
            return -_evaluate(opp, me)
        return -_negamax(opp, me, depth - 1, -beta, -alpha, ply + 1)

    if depth <= 0:
        return _evaluate(me, opp)

    orig_alpha = alpha
    orig_beta = beta
    value = -INF
    best = 0

    for bit in _order_bits(moves, tt_move):
        nm, no, _fl = _do_move(me, opp, bit)
        v = -_negamax(nm, no, depth - 1, -beta, -alpha, ply + 1)
        if v > value:
            value = v
            best = bit
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break

    if best:
        if value <= orig_alpha:
            flag = 2
        elif value >= orig_beta:
            flag = 1
        else:
            flag = 0
        TT[key] = (depth, value, flag, best)
    return value

def _search_root(me, opp, depth, prev_best):
    moves = legal_moves(me, opp)
    ent = TT.get((me, opp))
    tt_move = ent[3] if ent is not None else 0
    bits = _order_bits(moves, prev_best, tt_move)

    alpha = -INF
    beta = INF
    best_val = -INF
    best_bit = bits[0]
    for bit in bits:
        nm, no, _fl = _do_move(me, opp, bit)
        v = -_negamax(nm, no, depth - 1, -beta, -alpha, 1)
        if v > best_val:
            best_val = v
            best_bit = bit
            if v > alpha:
                alpha = v
    return best_bit, best_val

def _solve_exact(me, opp, alpha, beta):
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() > DEADLINE:
        raise _Timeout()

    key = (me, opp)
    ent = EXACT_TT.get(key)
    if ent is not None:
        ev, ef = ent
        if ef == 0:
            return ev
        if ef == 1:
            if ev > alpha:
                alpha = ev
        else:
            if ev < beta:
                beta = ev
        if alpha >= beta:
            return ev

    moves = legal_moves(me, opp)
    if moves == 0:
        if legal_moves(opp, me) == 0:
            return POPCOUNT(me) - POPCOUNT(opp)
        return -_solve_exact(opp, me, -beta, -alpha)

    items = []
    for bit in _bits(moves):
        nm, no, fl = _do_move(me, opp, bit)
        i = bit.bit_length() - 1
        items.append((ORDER_VAL[i] * 8 + POPCOUNT(fl) * 32, bit, nm, no))
    items.sort(key=lambda x: x[0], reverse=True)

    orig_alpha = alpha
    orig_beta = beta
    best = -65
    for _sc, _bit, nm, no in items:
        v = -_solve_exact(nm, no, -beta, -alpha)
        if v > best:
            best = v
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break

    if len(EXACT_TT) < 1_500_000:
        if best <= orig_alpha:
            flag = 2
        elif best >= orig_beta:
            flag = 1
        else:
            flag = 0
        EXACT_TT[key] = (best, flag)
    return best

def _root_order(me, opp, moves):
    empties = 64 - POPCOUNT(me | opp)
    items = []
    for bit in _bits(moves):
        nm, no, fl = _do_move(me, opp, bit)
        i = bit.bit_length() - 1
        opp_mob = POPCOUNT(legal_moves(nm, no))
        flipn = POPCOUNT(fl)
        if empties > 24:
            sc = ORDER_VAL[i] * 8 - opp_mob * 46 + flipn * 3
        else:
            sc = ORDER_VAL[i] * 5 - opp_mob * 22 + flipn * 30
        if bit & CORNERS:
            sc += 100000
        items.append((sc, bit))
    items.sort(key=lambda x: x[0], reverse=True)
    return [b for _s, b in items]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global DEADLINE, NODES
    me = _bits_from_array(you)
    opp = _bits_from_array(opponent)

    legal = legal_moves(me, opp)
    if legal == 0:
        return "pass"

    DEADLINE = time.perf_counter() + TIME_LIMIT
    NODES = 0
    if len(TT) > 900_000:
        TT.clear()
    if len(EXACT_TT) > 1_800_000:
        EXACT_TT.clear()

    try:
        ordered = _root_order(me, opp, legal)
        best = ordered[0]
        if len(ordered) == 1:
            return _move_str(best)

        empties = 64 - POPCOUNT(me | opp)

        if empties <= EXACT_EMPTY:
            alpha = -65
            for bit in ordered:
                if time.perf_counter() > DEADLINE:
                    raise _Timeout()
                nm, no, _fl = _do_move(me, opp, bit)
                v = -_solve_exact(nm, no, -65, -alpha)
                if v > alpha:
                    alpha = v
                    best = bit
            return _move_str(best)

        max_depth = empties + 4 if empties <= 26 else 64
        prev = best
        depth = 1
        while depth <= max_depth and time.perf_counter() < DEADLINE - 0.025:
            bit, val = _search_root(me, opp, depth, prev)
            best = bit
            prev = bit
            if val > 60 * TERM or val < -60 * TERM:
                break
            depth += 1
        return _move_str(best)
    except _Timeout:
        try:
            return _move_str(best)
        except Exception:
            return _move_str(next(iter(_bits(legal))))
    except Exception:
        # Absolute safety fallback: always return a legal move.
        return _move_str(next(iter(_bits(legal))))
