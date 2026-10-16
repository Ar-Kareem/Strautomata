
import time
import numpy as np

FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
CORNERS_MASK = 0x8100000000000081
INF = 10 ** 9
WIN = 1000000

# (shift, landing-mask); +d = left shift, -d = right shift
DIRS = ((1, NOT_A), (-1, NOT_H), (8, FULL), (-8, FULL),
        (9, NOT_A), (-9, NOT_H), (7, NOT_H), (-7, NOT_A))

if hasattr(int, "bit_count"):
    def popcount(x):
        return x.bit_count()
else:
    def popcount(x):
        return bin(x).count("1")

SQ = (
    100, -25,  10,   5,   5,  10, -25, 100,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
     10,  -5,   3,   1,   1,   3,  -5,  10,
      5,  -5,   1,   1,   1,   1,  -5,   5,
      5,  -5,   1,   1,   1,   1,  -5,   5,
     10,  -5,   3,   1,   1,   3,  -5,  10,
    -25, -45,  -5,  -5,  -5,  -5, -45, -25,
    100, -25,  10,   5,   5,  10, -25, 100,
)

BYTE_POS = tuple(
    tuple(sum(SQ[b * 8 + i] for i in range(8) if (v >> i) & 1) for v in range(256))
    for b in range(8)
)

def pos_score(P, O):
    BP = BYTE_POS
    return (BP[0][P & 255] - BP[0][O & 255]
            + BP[1][(P >> 8) & 255] - BP[1][(O >> 8) & 255]
            + BP[2][(P >> 16) & 255] - BP[2][(O >> 16) & 255]
            + BP[3][(P >> 24) & 255] - BP[3][(O >> 24) & 255]
            + BP[4][(P >> 32) & 255] - BP[4][(O >> 32) & 255]
            + BP[5][(P >> 40) & 255] - BP[5][(O >> 40) & 255]
            + BP[6][(P >> 48) & 255] - BP[6][(O >> 48) & 255]
            + BP[7][(P >> 56) & 255] - BP[7][(O >> 56) & 255])

def _adj_mask(r, c):
    m = 0
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            rr, cc = r + dr, c + dc
            if 0 <= rr < 8 and 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
    return m

CORNER_ZONES = tuple((1 << i, _adj_mask(i >> 3, i & 7)) for i in (0, 7, 56, 63))

def gen_moves(P, O):
    empty = ~(P | O) & FULL
    moves = 0
    for d, m in DIRS:
        if d > 0:
            x = ((P << d) & m) & O
            x |= ((x << d) & m) & O
            x |= ((x << d) & m) & O
            x |= ((x << d) & m) & O
            x |= ((x << d) & m) & O
            x |= ((x << d) & m) & O
            moves |= ((x << d) & m) & empty
        else:
            s = -d
            x = ((P >> s) & m) & O
            x |= ((x >> s) & m) & O
            x |= ((x >> s) & m) & O
            x |= ((x >> s) & m) & O
            x |= ((x >> s) & m) & O
            x |= ((x >> s) & m) & O
            moves |= ((x >> s) & m) & empty
    return moves

def flips_for(P, O, mv):
    f = 0
    for d, m in DIRS:
        if d > 0:
            x = ((mv << d) & m) & O
            if x:
                x |= ((x << d) & m) & O
                x |= ((x << d) & m) & O
                x |= ((x << d) & m) & O
                x |= ((x << d) & m) & O
                x |= ((x << d) & m) & O
                if ((x << d) & m) & P:
                    f |= x
        else:
            s = -d
            x = ((mv >> s) & m) & O
            if x:
                x |= ((x >> s) & m) & O
                x |= ((x >> s) & m) & O
                x |= ((x >> s) & m) & O
                x |= ((x >> s) & m) & O
                x |= ((x >> s) & m) & O
                if ((x >> s) & m) & P:
                    f |= x
    return f

def evaluate(P, O, my_moves_bits):
    pc = popcount(P)
    oc = popcount(O)
    occ = pc + oc
    empties = 64 - occ
    om_bits = gen_moves(O, P)
    mm = popcount(my_moves_bits)
    om = popcount(om_bits)
    parity_n = (100 * (pc - oc)) // occ if occ else 0
    mob_n = (100 * (mm - om)) // (mm + om) if (mm + om) else 0
    corner_n = 25 * (popcount(P & CORNERS_MASK) - popcount(O & CORNERS_MASK))
    myclose = 0
    opclose = 0
    for corner, adj in CORNER_ZONES:
        if not ((P | O) & corner):
            myclose += popcount(P & adj)
            opclose += popcount(O & adj)
    cclose_n = -12 * (myclose - opclose)
    empty = ~(P | O) & FULL
    dil = 0
    for d, m in DIRS:
        if d > 0:
            dil |= (empty << d) & m
        else:
            dil |= (empty >> -d) & m
    fme = popcount(P & dil)
    fop = popcount(O & dil)
    front_n = (-100 * (fme - fop)) // (fme + fop) if (fme + fop) else 0
    pos_n = pos_score(P, O) >> 3
    if empties > 44:
        return (4 * parity_n + 75 * mob_n + 350 * corner_n
                + 12 * cclose_n + 8 * front_n + 18 * pos_n)
    if empties > 20:
        return (15 * parity_n + 65 * mob_n + 350 * corner_n
                + 10 * cclose_n + 10 * front_n + 18 * pos_n)
    return (60 * parity_n + 30 * mob_n + 350 * corner_n
            + 5 * cclose_n + 5 * front_n + 8 * pos_n)

class _Timeout(Exception):
    pass

TT = {}

def negamax(P, O, depth, alpha, beta, passed, emp, deadline, counter):
    counter[0] += 1
    if (counter[0] & 1023) == 0:
        if time.time() > deadline or counter[0] > 9000000:
            raise _Timeout
    gm = gen_moves
    moves = gm(P, O)
    if moves == 0:
        if passed:
            d = popcount(P) - popcount(O)
            if d > 0:
                return WIN + d
            if d < 0:
                return -WIN + d
            return 0
        return -negamax(O, P, depth, -beta, -alpha, True, emp, deadline, counter)
    if depth <= 0:
        return evaluate(P, O, moves)
    alpha_entry = alpha
    beta_entry = beta
    key = (P << 64) | O
    ent = TT.get(key)
    tt_move = 0
    if ent is not None:
        ed, ev, ef, em = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1:
                if ev >= beta:
                    return ev
                if ev > alpha:
                    alpha = ev
            else:
                if ev <= alpha:
                    return ev
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev
        tt_move = em
    children = []
    b = moves
    if emp <= 16:
        while b:
            lsb = b & -b
            b ^= lsb
            f = flips_for(P, O, lsb)
            nO = O ^ f
            nP = P ^ f ^ lsb
            om = popcount(gm(nO, nP))
            k = (om << 9) - SQ[lsb.bit_length() - 1]
            if lsb == tt_move:
                k = -INF
            children.append((k, nO, nP, lsb))
    else:
        while b:
            lsb = b & -b
            b ^= lsb
            f = flips_for(P, O, lsb)
            nO = O ^ f
            nP = P ^ f ^ lsb
            k = -SQ[lsb.bit_length() - 1]
            if lsb == tt_move:
                k = -INF
            children.append((k, nO, nP, lsb))
    children.sort(key=lambda t: t[0])
    best_val = -INF
    best_move = children[0][3]
    a = alpha
    for _, nO, nP, lsb in children:
        v = -negamax(nO, nP, depth - 1, -beta, -a, False, emp - 1, deadline, counter)
        if v > best_val:
            best_val = v
            best_move = lsb
        if v > a:
            a = v
            if a >= beta:
                break
    if best_val <= alpha_entry:
        flag = 2
    elif best_val >= beta_entry:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best_val, flag, best_move)
    return best_val

def search_root(P, O, moves, deadline):
    ml = []
    b = moves
    while b:
        lsb = b & -b
        b ^= lsb
        ml.append(lsb)
    best_overall = ml[0]
    root_scores = {}
    counter = [0]
    empties = 64 - popcount(P | O)
    depth = 3
    try:
        while depth <= 64:
            ml.sort(key=lambda mv: -root_scores.get(mv, SQ[mv.bit_length() - 1]))
            a = -INF
            best_val = -INF
            best_mv = ml[0]
            for mv in ml:
                f = flips_for(P, O, mv)
                v = -negamax(O ^ f, P ^ f ^ mv, depth - 1, -INF, -a,
                             False, empties - 1, deadline, counter)
                root_scores[mv] = v
                if v > best_val:
                    best_val = v
                    best_mv = mv
                if v > a:
                    a = v
            best_overall = best_mv
            if best_val >= WIN - 100 or best_val <= -(WIN - 100):
                break
            if depth >= empties:
                break
            if time.time() > deadline - 0.03:
                break
            depth += 1
    except _Timeout:
        pass
    return best_overall

def _board_to_int(arr):
    b = np.packbits(np.asarray(arr, dtype=np.uint8).ravel(), bitorder="little")
    return int.from_bytes(b.tobytes(), "little")

def policy(you, opponent):
    try:
        P = _board_to_int(you)
        O = _board_to_int(opponent)
        moves = gen_moves(P, O)
        if moves == 0:
            return "pass"
        lsb = moves & -moves
        if moves == lsb:
            mv = lsb
        else:
            if len(TT) > 2500000:
                TT.clear()
            deadline = time.time() + 0.90
            mv = search_root(P, O, moves, deadline)
        idx = mv.bit_length() - 1
        return chr(97 + (idx & 7)) + str((idx >> 3) + 1)
    except Exception:
        try:
            P = 0
            O = 0
            for r in range(8):
                for c in range(8):
                    if int(you[r][c]):
                        P |= 1 << (r * 8 + c)
                    elif int(opponent[r][c]):
                        O |= 1 << (r * 8 + c)
            m = gen_moves(P, O)
            if m:
                lsb = m & -m
                idx = lsb.bit_length() - 1
                return chr(97 + (idx & 7)) + str((idx >> 3) + 1)
            return "pass"
        except Exception:
            return "pass"
