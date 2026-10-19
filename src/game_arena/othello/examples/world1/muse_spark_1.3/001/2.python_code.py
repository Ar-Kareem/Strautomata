
import numpy as np
import time

FULL = (1 << 64) - 1
FE = 0xfefefefefefefefe
FW = 0x7f7f7f7f7f7f7f7f
CORNERS = 0x8100000000000081
INF = 10 ** 9

IDX_TO_STR = [chr(ord('a') + (i % 8)) + str(i // 8 + 1) for i in range(64)]

# positional weights, corners / X / C are 0 (handled dynamically)
POS = [
    0, 0, 12, 8, 8, 12, 0, 0,
    0, 0, 4, 4, 4, 4, 0, 0,
    12, 4, 6, 3, 3, 6, 4, 12,
    8, 4, 3, 2, 2, 3, 4, 8,
    8, 4, 3, 2, 2, 3, 4, 8,
    12, 4, 6, 3, 3, 6, 4, 12,
    0, 0, 4, 4, 4, 4, 0, 0,
    0, 0, 12, 8, 8, 12, 0, 0,
]

try:
    _bc = int.bit_count
    def popcnt(x: int) -> int:
        return x.bit_count()
except Exception:
    def popcnt(x: int) -> int:
        return bin(x).count("1")

class _Timeout(Exception):
    pass

def get_moves(P: int, O: int) -> int:
    empty = (~(P | O)) & FULL
    m = 0
    # N
    x = (P >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    x |= (x >> 8) & O
    m |= (x >> 8) & empty
    # S
    x = ((P << 8) & FULL) & O
    x |= ((x << 8) & FULL) & O
    x |= ((x << 8) & FULL) & O
    x |= ((x << 8) & FULL) & O
    x |= ((x << 8) & FULL) & O
    x |= ((x << 8) & FULL) & O
    m |= ((x << 8) & FULL) & empty
    # E
    x = ((P << 1) & FE) & O
    x |= ((x << 1) & FE) & O
    x |= ((x << 1) & FE) & O
    x |= ((x << 1) & FE) & O
    x |= ((x << 1) & FE) & O
    x |= ((x << 1) & FE) & O
    m |= ((x << 1) & FE) & empty
    # W
    x = ((P >> 1) & FW) & O
    x |= ((x >> 1) & FW) & O
    x |= ((x >> 1) & FW) & O
    x |= ((x >> 1) & FW) & O
    x |= ((x >> 1) & FW) & O
    x |= ((x >> 1) & FW) & O
    m |= ((x >> 1) & FW) & empty
    # NE
    x = ((P >> 7) & FE) & O
    x |= ((x >> 7) & FE) & O
    x |= ((x >> 7) & FE) & O
    x |= ((x >> 7) & FE) & O
    x |= ((x >> 7) & FE) & O
    x |= ((x >> 7) & FE) & O
    m |= ((x >> 7) & FE) & empty
    # NW
    x = ((P >> 9) & FW) & O
    x |= ((x >> 9) & FW) & O
    x |= ((x >> 9) & FW) & O
    x |= ((x >> 9) & FW) & O
    x |= ((x >> 9) & FW) & O
    x |= ((x >> 9) & FW) & O
    m |= ((x >> 9) & FW) & empty
    # SE
    x = ((P << 9) & FE) & O
    x |= ((x << 9) & FE) & O
    x |= ((x << 9) & FE) & O
    x |= ((x << 9) & FE) & O
    x |= ((x << 9) & FE) & O
    x |= ((x << 9) & FE) & O
    m |= ((x << 9) & FE) & empty
    # SW
    x = ((P << 7) & FW) & O
    x |= ((x << 7) & FW) & O
    x |= ((x << 7) & FW) & O
    x |= ((x << 7) & FW) & O
    x |= ((x << 7) & FW) & O
    x |= ((x << 7) & FW) & O
    m |= ((x << 7) & FW) & empty
    return m

def get_flips(P: int, O: int, mv: int) -> int:
    flips = 0
    # N
    c = mv >> 8
    mk = 0
    while c & O:
        mk |= c
        c >>= 8
    if c & P:
        flips |= mk
    # S
    c = (mv << 8) & FULL
    mk = 0
    while c & O:
        mk |= c
        c = (c << 8) & FULL
    if c & P:
        flips |= mk
    # E
    c = (mv << 1) & FE
    mk = 0
    while c & O:
        mk |= c
        c = (c << 1) & FE
    if c & P:
        flips |= mk
    # W
    c = (mv >> 1) & FW
    mk = 0
    while c & O:
        mk |= c
        c = (c >> 1) & FW
    if c & P:
        flips |= mk
    # NE
    c = (mv >> 7) & FE
    mk = 0
    while c & O:
        mk |= c
        c = (c >> 7) & FE
    if c & P:
        flips |= mk
    # NW
    c = (mv >> 9) & FW
    mk = 0
    while c & O:
        mk |= c
        c = (c >> 9) & FW
    if c & P:
        flips |= mk
    # SE
    c = (mv << 9) & FE
    mk = 0
    while c & O:
        mk |= c
        c = (c << 9) & FE
    if c & P:
        flips |= mk
    # SW
    c = (mv << 7) & FW
    mk = 0
    while c & O:
        mk |= c
        c = (c << 7) & FW
    if c & P:
        flips |= mk
    return flips

def evaluate(P: int, O: int) -> int:
    score = 0
    pc = popcnt(P & CORNERS)
    oc = popcnt(O & CORNERS)
    score += 1200 * (pc - oc)
    occ = P | O
    # corner 0 : a1, adj X=9 C=1,8
    if (occ & 1) == 0:
        if P & (1 << 9):
            score -= 450
        if O & (1 << 9):
            score += 450
        if P & (1 << 1):
            score -= 180
        if P & (1 << 8):
            score -= 180
        if O & (1 << 1):
            score += 180
        if O & (1 << 8):
            score += 180
    elif P & 1:
        if P & (1 << 9):
            score += 40
        if P & (1 << 1):
            score += 30
        if P & (1 << 8):
            score += 30
    else:
        if O & (1 << 9):
            score -= 40
        if O & (1 << 1):
            score -= 30
        if O & (1 << 8):
            score -= 30
    # corner 7 : h1, X=14 C=6,15
    c7 = 1 << 7
    if (occ & c7) == 0:
        if P & (1 << 14):
            score -= 450
        if O & (1 << 14):
            score += 450
        if P & (1 << 6):
            score -= 180
        if P & (1 << 15):
            score -= 180
        if O & (1 << 6):
            score += 180
        if O & (1 << 15):
            score += 180
    elif P & c7:
        if P & (1 << 14):
            score += 40
        if P & (1 << 6):
            score += 30
        if P & (1 << 15):
            score += 30
    else:
        if O & (1 << 14):
            score -= 40
        if O & (1 << 6):
            score -= 30
        if O & (1 << 15):
            score -= 30
    # corner 56 : a8, X=49 C=48,57
    c56 = 1 << 56
    if (occ & c56) == 0:
        if P & (1 << 49):
            score -= 450
        if O & (1 << 49):
            score += 450
        if P & (1 << 48):
            score -= 180
        if P & (1 << 57):
            score -= 180
        if O & (1 << 48):
            score += 180
        if O & (1 << 57):
            score += 180
    elif P & c56:
        if P & (1 << 49):
            score += 40
        if P & (1 << 48):
            score += 30
        if P & (1 << 57):
            score += 30
    else:
        if O & (1 << 49):
            score -= 40
        if O & (1 << 48):
            score -= 30
        if O & (1 << 57):
            score -= 30
    # corner 63 : h8, X=54 C=55,62
    c63 = 1 << 63
    if (occ & c63) == 0:
        if P & (1 << 54):
            score -= 450
        if O & (1 << 54):
            score += 450
        if P & (1 << 55):
            score -= 180
        if P & (1 << 62):
            score -= 180
        if O & (1 << 55):
            score += 180
        if O & (1 << 62):
            score += 180
    elif P & c63:
        if P & (1 << 54):
            score += 40
        if P & (1 << 55):
            score += 30
        if P & (1 << 62):
            score += 30
    else:
        if O & (1 << 54):
            score -= 40
        if O & (1 << 55):
            score -= 30
        if O & (1 << 62):
            score -= 30

    mP_bb = get_moves(P, O)
    mO_bb = get_moves(O, P)
    mP = popcnt(mP_bb)
    mO = popcnt(mO_bb)
    score += 22 * (mP - mO)
    if mP == 0 and mO != 0:
        score -= 150
    if mO == 0 and mP != 0:
        score += 150

    empty = (~occ) & FULL
    neigh = ((empty << 8) & FULL) | (empty >> 8) | ((empty << 1) & FE) | ((empty >> 1) & FW) | ((empty >> 7) & FE) | ((empty >> 9) & FW) | ((empty << 9) & FE) | ((empty << 7) & FW)
    neigh &= FULL
    fP = popcnt(P & neigh)
    fO = popcnt(O & neigh)
    score += -11 * (fP - fO)

    dP = popcnt(P)
    dO = popcnt(O)
    empt = 64 - dP - dO
    if empt < 14:
        score += 20 * (dP - dO)
    elif empt < 20:
        score += 5 * (dP - dO)
    elif empt < 30:
        score += 0
    else:
        score += -8 * (dP - dO)

    # positional
    ps = 0
    t = P
    while t:
        lsb = t & -t
        idx = (lsb.bit_length() - 1)
        ps += POS[idx]
        t ^= lsb
    t = O
    while t:
        lsb = t & -t
        idx = (lsb.bit_length() - 1)
        ps -= POS[idx]
        t ^= lsb
    score += ps
    return score

def _order_score(mv: int, idx: int, occ: int, P: int, O: int) -> int:
    if mv & CORNERS:
        return 10000
    # X squares
    if idx == 9:
        if (occ & 1) == 0:
            return -600
        return POS[idx]
    if idx == 14:
        if (occ & (1 << 7)) == 0:
            return -600
        return POS[idx]
    if idx == 49:
        if (occ & (1 << 56)) == 0:
            return -600
        return POS[idx]
    if idx == 54:
        if (occ & (1 << 63)) == 0:
            return -600
        return POS[idx]
    # C squares
    if idx == 1 or idx == 8:
        if (occ & 1) == 0:
            return -400
        return 20
    if idx == 6 or idx == 15:
        if (occ & (1 << 7)) == 0:
            return -400
        return 20
    if idx == 48 or idx == 57:
        if (occ & (1 << 56)) == 0:
            return -400
        return 20
    if idx == 55 or idx == 62:
        if (occ & (1 << 63)) == 0:
            return -400
        return 20
    return POS[idx]

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    P = 0
    O = 0
    try:
        # fast conversion
        for r in range(8):
            yr = you[r]
            opr = opponent[r]
            base = r * 8
            # unroll columns
            if yr[0]:
                P |= 1 << base
            if yr[1]:
                P |= 1 << (base + 1)
            if yr[2]:
                P |= 1 << (base + 2)
            if yr[3]:
                P |= 1 << (base + 3)
            if yr[4]:
                P |= 1 << (base + 4)
            if yr[5]:
                P |= 1 << (base + 5)
            if yr[6]:
                P |= 1 << (base + 6)
            if yr[7]:
                P |= 1 << (base + 7)
            if opr[0]:
                O |= 1 << base
            if opr[1]:
                O |= 1 << (base + 1)
            if opr[2]:
                O |= 1 << (base + 2)
            if opr[3]:
                O |= 1 << (base + 3)
            if opr[4]:
                O |= 1 << (base + 4)
            if opr[5]:
                O |= 1 << (base + 5)
            if opr[6]:
                O |= 1 << (base + 6)
            if opr[7]:
                O |= 1 << (base + 7)
    except Exception:
        # fallback generic
        try:
            yf = np.asarray(you).reshape(64)
            of = np.asarray(opponent).reshape(64)
            for i in range(64):
                if yf[i]:
                    P |= 1 << i
                if of[i]:
                    O |= 1 << i
        except Exception:
            return "pass"

    moves_bb = get_moves(P, O)
    if moves_bb == 0:
        return "pass"
    # single move
    if moves_bb & (moves_bb - 1) == 0:
        idx = (moves_bb.bit_length() - 1)
        return IDX_TO_STR[idx]

    dP = popcnt(P)
    dO = popcnt(O)
    empties = 64 - dP - dO

    # collect moves
    occ = P | O
    move_list = []
    bb = moves_bb
    while bb:
        lsb = bb & -bb
        idx = (lsb.bit_length() - 1)
        s = _order_score(lsb, idx, occ, P, O)
        move_list.append((s, lsb, idx))
        bb ^= lsb
    move_list.sort(key=lambda x: x[0], reverse=True)
    best_move_bit = move_list[0][1]
    best_idx = move_list[0][2]

    # quick corner take
    for _, mv, idx in move_list:
        if mv & CORNERS:
            # verify it is legal (it is) -> take immediately if safe search not needed?
            # still do search but prioritize
            break

    start = time.time()
    deadline = start + 0.88
    nodes = [0]

    # depth selection
    if empties <= 14:
        max_depth = empties
    elif empties <= 20:
        max_depth = 7
    elif empties <= 30:
        max_depth = 6
    else:
        max_depth = 5

    # negamax closure
    def negamax(cP: int, cO: int, depth: int, alpha: int, beta: int) -> int:
        nodes[0] += 1
        if (nodes[0] & 1023) == 0 and time.time() > deadline:
            raise _Timeout()
        mv_bb = get_moves(cP, cO)
        if mv_bb == 0:
            opp_bb = get_moves(cO, cP)
            if opp_bb == 0:
                d = popcnt(cP) - popcnt(cO)
                if d > 0:
                    return 100000 + d
                elif d < 0:
                    return -100000 + d
                else:
                    return 0
            if depth == 0:
                return -evaluate(cO, cP)
            return -negamax(cO, cP, depth - 1, -beta, -alpha)
        if depth == 0:
            return evaluate(cP, cO)
        # generate ordered children with flips precomputed
        occ2 = cP | cO
        childs = []
        b = mv_bb
        while b:
            lsb = b & -b
            idx2 = (lsb.bit_length() - 1)
            fl = get_flips(cP, cO, lsb)
            nP = cP | lsb | fl
            nO = cO & (~fl & FULL)
            sc = _order_score(lsb, idx2, occ2, cP, cO)
            # bonus for many flips in endgame, penalty early? small tiebreaker
            # add flip count tiebreaker
            sc = sc * 10 + popcnt(fl)
            childs.append((sc, nP, nO))
            b ^= lsb
        childs.sort(key=lambda x: x[0], reverse=True)
        best = -INF
        for _, nP, nO in childs:
            v = -negamax(nO, nP, depth - 1, -beta, -alpha)
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    try:
        # iterative deepening
        # order persistent: best first
        cur_order = [mv for _, mv, _ in move_list]
        cur_idx_order = [idx for _, _, idx in move_list]
        for depth in range(1, max_depth + 1):
            alpha = -INF
            beta = INF
            local_best_val = -INF
            local_best_mv = cur_order[0]
            # search each root move
            # compute flips once per root move (recompute each depth, cheap)
            scored_root = []
            for mv, idx in zip(cur_order, cur_idx_order):
                fl = get_flips(P, O, mv)
                nP = P | mv | fl
                nO = O & (~fl & FULL)
                # static order for this depth (keep previous best first by boosting)
                s = _order_score(mv, idx, occ, P, O)
                if mv == best_move_bit:
                    s += 10000
                scored_root.append((s, mv, nP, nO))
            scored_root.sort(key=lambda x: x[0], reverse=True)
            for _, mv, nP, nO in scored_root:
                v = -negamax(nO, nP, depth - 1, -beta, -alpha)
                if v > local_best_val:
                    local_best_val = v
                    local_best_mv = mv
                if v > alpha:
                    alpha = v
            # completed depth successfully
            best_move_bit = local_best_mv
            best_idx = (best_move_bit.bit_length() - 1)
            # move best to front for next depth
            # rebuild order with best first
            new_order = [best_move_bit] + [m for m in cur_order if m != best_move_bit]
            # rebuild idx order accordingly
            mp = {}
            for m, ii in zip(cur_order, cur_idx_order):
                mp[m] = ii
            cur_order = new_order
            cur_idx_order = [mp[m] for m in new_order]
            if time.time() > deadline:
                break
            # early exit if winning line found and deep enough?
            if local_best_val > 90000 and empties <= 14:
                # already won, but continue to find larger win if time allows
                pass
    except _Timeout:
        pass
    except Exception:
        pass

    try:
        # safety: ensure best is legal
        if (moves_bb & best_move_bit) == 0:
            # fallback to first legal
            lsb = moves_bb & -moves_bb
            best_idx = (lsb.bit_length() - 1)
            return IDX_TO_STR[best_idx]
        return IDX_TO_STR[best_idx]
    except Exception:
        # ultimate fallback
        bb = moves_bb
        lsb = bb & -bb
        idx = (lsb.bit_length() - 1)
        return IDX_TO_STR[idx]
