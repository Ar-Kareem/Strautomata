
import numpy as np
import time

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

W = [
    120,-20, 20,  5,  5, 20,-20,120,
    -20,-40, -5, -5, -5, -5,-40,-20,
     20, -5, 15,  3,  3, 15, -5, 20,
      5, -5,  3,  3,  3,  3, -5,  5,
      5, -5,  3,  3,  3,  3, -5,  5,
     20, -5, 15,  3,  3, 15, -5, 20,
    -20,-40, -5, -5, -5, -5,-40,-20,
    120,-20, 20,  5,  5, 20,-20,120,
]

CORNER_INFO = [
    ((1 << 0),  (1 << 1) | (1 << 8),  (1 << 9)),
    ((1 << 7),  (1 << 6) | (1 << 15), (1 << 14)),
    ((1 << 56), (1 << 57) | (1 << 48), (1 << 49)),
    ((1 << 63), (1 << 62) | (1 << 55), (1 << 54)),
]

try:
    (1).bit_count()
    def popcnt(x):
        return x.bit_count()
except AttributeError:
    def popcnt(x):
        return bin(x).count("1")

def get_moves(P, O):
    empty = (~(P | O)) & FULL
    if empty == 0:
        return 0
    moves = 0
    # E
    x = (((P & NOT_H) << 1)) & O
    x |= (((x & NOT_H) << 1)) & O
    x |= (((x & NOT_H) << 1)) & O
    x |= (((x & NOT_H) << 1)) & O
    x |= (((x & NOT_H) << 1)) & O
    x |= (((x & NOT_H) << 1)) & O
    moves |= (((x & NOT_H) << 1)) & empty
    # W
    x = ((P & NOT_A) >> 1) & O
    x |= (((x & NOT_A) >> 1)) & O
    x |= (((x & NOT_A) >> 1)) & O
    x |= (((x & NOT_A) >> 1)) & O
    x |= (((x & NOT_A) >> 1)) & O
    x |= (((x & NOT_A) >> 1)) & O
    moves |= (((x & NOT_A) >> 1)) & empty
    # N
    x = (P >> 8) & O
    x |= ((x >> 8)) & O
    x |= ((x >> 8)) & O
    x |= ((x >> 8)) & O
    x |= ((x >> 8)) & O
    x |= ((x >> 8)) & O
    moves |= ((x >> 8)) & empty
    # S
    x = ((P << 8)) & O
    x |= (((x << 8))) & O
    x |= (((x << 8))) & O
    x |= (((x << 8))) & O
    x |= (((x << 8))) & O
    x |= (((x << 8))) & O
    moves |= (((x << 8))) & empty
    # NE
    x = ((P & NOT_H) >> 7) & O
    x |= (((x & NOT_H) >> 7)) & O
    x |= (((x & NOT_H) >> 7)) & O
    x |= (((x & NOT_H) >> 7)) & O
    x |= (((x & NOT_H) >> 7)) & O
    x |= (((x & NOT_H) >> 7)) & O
    moves |= (((x & NOT_H) >> 7)) & empty
    # NW
    x = ((P & NOT_A) >> 9) & O
    x |= (((x & NOT_A) >> 9)) & O
    x |= (((x & NOT_A) >> 9)) & O
    x |= (((x & NOT_A) >> 9)) & O
    x |= (((x & NOT_A) >> 9)) & O
    x |= (((x & NOT_A) >> 9)) & O
    moves |= (((x & NOT_A) >> 9)) & empty
    # SE
    x = (((P & NOT_H) << 9)) & O
    x |= ((((x & NOT_H) << 9))) & O
    x |= ((((x & NOT_H) << 9))) & O
    x |= ((((x & NOT_H) << 9))) & O
    x |= ((((x & NOT_H) << 9))) & O
    x |= ((((x & NOT_H) << 9))) & O
    moves |= ((((x & NOT_H) << 9))) & empty
    # SW
    x = (((P & NOT_A) << 7)) & O
    x |= ((((x & NOT_A) << 7))) & O
    x |= ((((x & NOT_A) << 7))) & O
    x |= ((((x & NOT_A) << 7))) & O
    x |= ((((x & NOT_A) << 7))) & O
    x |= ((((x & NOT_A) << 7))) & O
    moves |= ((((x & NOT_A) << 7))) & empty
    return moves & FULL

def get_flips(P, O, m):
    flips = 0
    # E
    cur = ((m & NOT_H) << 1)
    cap = 0
    while cur & O:
        cap |= cur
        cur = ((cur & NOT_H) << 1)
    if cur & P:
        flips |= cap
    # W
    cur = ((m & NOT_A) >> 1)
    cap = 0
    while cur & O:
        cap |= cur
        cur = ((cur & NOT_A) >> 1)
    if cur & P:
        flips |= cap
    # N
    cur = (m >> 8)
    cap = 0
    while cur & O:
        cap |= cur
        cur = (cur >> 8)
    if cur & P:
        flips |= cap
    # S
    cur = (m << 8)
    cap = 0
    while cur & O:
        cap |= cur
        cur = (cur << 8)
        if cur > (1 << 70):
            break
    if cur & P:
        flips |= cap
    # NE
    cur = ((m & NOT_H) >> 7)
    cap = 0
    while cur & O:
        cap |= cur
        cur = ((cur & NOT_H) >> 7)
    if cur & P:
        flips |= cap
    # NW
    cur = ((m & NOT_A) >> 9)
    cap = 0
    while cur & O:
        cap |= cur
        cur = ((cur & NOT_A) >> 9)
    if cur & P:
        flips |= cap
    # SE
    cur = (((m & NOT_H) << 9))
    cap = 0
    while cur & O:
        cap |= cur
        cur = (((cur & NOT_H) << 9))
        if cur > (1 << 70):
            break
    if cur & P:
        flips |= cap
    # SW
    cur = (((m & NOT_A) << 7))
    cap = 0
    while cur & O:
        cap |= cur
        cur = (((cur & NOT_A) << 7))
        if cur > (1 << 70):
            break
    if cur & P:
        flips |= cap
    return flips

def evaluate(P, O):
    cp = popcnt(P & CORNERS)
    co = popcnt(O & CORNERS)
    score = (cp - co) * 1000
    occ = P | O
    for cb, cmask, xbit in CORNER_INFO:
        if not (occ & cb):
            my_c = popcnt(P & cmask)
            op_c = popcnt(O & cmask)
            my_x = 1 if (P & xbit) else 0
            op_x = 1 if (O & xbit) else 0
            score += (op_c - my_c) * 150 + (op_x - my_x) * 400
    my_moves = get_moves(P, O)
    op_moves = get_moves(O, P)
    my_mob = popcnt(my_moves)
    op_mob = popcnt(op_moves)
    if my_mob == 0 and op_mob == 0:
        d = popcnt(P) - popcnt(O)
        if d > 0:
            return 100000 + d
        elif d < 0:
            return -100000 + d
        return 0
    score += (my_mob - op_mob) * 25
    empty = (~occ) & FULL
    e = (((empty & NOT_H) << 1) | ((empty & NOT_A) >> 1) | (empty >> 8) | (empty << 8) | ((empty & NOT_H) >> 7) | ((empty & NOT_A) >> 9) | (((empty & NOT_H) << 9)) | (((empty & NOT_A) << 7)))
    my_front = popcnt(P & e)
    op_front = popcnt(O & e)
    score += (op_front - my_front) * 12
    empt = popcnt(empty)
    disc = popcnt(P) - popcnt(O)
    if empt < 14:
        score += disc * 50
    elif empt < 20:
        score += disc * 10
    else:
        score += disc
    return score

class _Timeout(Exception):
    pass

INF = 10 ** 9

def _bit_to_str(bit):
    idx = (bit.bit_length() - 1)
    r = idx >> 3
    c = idx & 7
    return chr(ord('a') + c) + str(r + 1)

def _brute_fallback(you, opponent):
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for r in range(8):
        for c in range(8):
            if you[r, c] == 0 and opponent[r, c] == 0:
                for dr, dc in dirs:
                    rr, cc = r + dr, c + dc
                    found = False
                    while 0 <= rr < 8 and 0 <= cc < 8:
                        if opponent[rr, cc] == 1:
                            found = True
                            rr += dr
                            cc += dc
                        elif you[rr, cc] == 1:
                            if found:
                                return chr(ord('a') + c) + str(r + 1)
                            break
                        else:
                            break
    return "pass"

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    try:
        start = time.perf_counter()
        deadline = start + 0.90
        P = 0
        O = 0
        for r in range(8):
            yr = you[r]
            opr = opponent[r]
            base = r * 8
            for c in range(8):
                if yr[c]:
                    P |= 1 << (base + c)
                elif opr[c]:
                    O |= 1 << (base + c)
        moves_bb = get_moves(P, O)
        if moves_bb == 0:
            return "pass"
        cm = moves_bb & CORNERS
        if cm != 0:
            lsb = cm & (-cm)
            return _bit_to_str(lsb)
        # collect moves
        bits = []
        bb = moves_bb
        while bb:
            lsb = bb & (-bb)
            bits.append(lsb)
            bb ^= lsb
        if len(bits) == 1:
            return _bit_to_str(bits[0])
        def wkey(b):
            return W[(b.bit_length() - 1)]
        bits.sort(key=wkey, reverse=True)
        best_overall = bits[0]
        empty_cnt = popcnt((~(P | O)) & FULL)
        # iterative deepening
        nodes = 0
        TTmove = {}
        # closure negamax
        def negamax(Pc, Oc, depth, alpha, beta):
            nonlocal nodes
            nodes += 1
            if (nodes & 255) == 0 and time.perf_counter() > deadline:
                raise _Timeout()
            if depth <= 0:
                return evaluate(Pc, Oc)
            mb = get_moves(Pc, Oc)
            if mb == 0:
                ob = get_moves(Oc, Pc)
                if ob == 0:
                    d = popcnt(Pc) - popcnt(Oc)
                    if d > 0:
                        return 100000 + d
                    elif d < 0:
                        return -100000 + d
                    return 0
                return -negamax(Oc, Pc, depth - 1, -beta, -alpha)
            # order moves
            mlist = []
            t = mb
            while t:
                l = t & (-t)
                mlist.append(l)
                t ^= l
            bm = TTmove.get((Pc, Oc))
            if bm is not None and (mb & bm):
                try:
                    mlist.remove(bm)
                    mlist = [bm] + sorted(mlist, key=lambda b: W[(b.bit_length() - 1)], reverse=True)
                except ValueError:
                    mlist.sort(key=lambda b: W[(b.bit_length() - 1)], reverse=True)
            else:
                mlist.sort(key=lambda b: W[(b.bit_length() - 1)], reverse=True)
            best = -INF
            bestm = mlist[0]
            for m in mlist:
                f = get_flips(Pc, Oc, m)
                Pc2 = Pc | m | f
                Oc2 = Oc ^ f
                s = -negamax(Oc2, Pc2, depth - 1, -beta, -alpha)
                if s > best:
                    best = s
                    bestm = m
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            TTmove[(Pc, Oc)] = bestm
            return best
        # root iterative deepening
        root_scores = {m: W[(m.bit_length() - 1)] for m in bits}
        max_depth = empty_cnt if empty_cnt < 14 else 12
        if max_depth < 4:
            max_depth = 4
        if max_depth > 20:
            max_depth = 20
        ordered = list(bits)
        for depth in range(3, max_depth + 1):
            if time.perf_counter() > deadline - 0.05:
                break
            try:
                ordered = sorted(ordered, key=lambda b: root_scores.get(b, 0), reverse=True)
                alpha = -INF
                best_this = ordered[0]
                best_score = -INF
                for m in ordered:
                    f = get_flips(P, O, m)
                    P2 = P | m | f
                    O2 = O ^ f
                    s = -negamax(O2, P2, depth - 1, -beta if (beta := INF) else INF, -alpha)
                    root_scores[m] = s
                    if s > best_score:
                        best_score = s
                        best_this = m
                    if s > alpha:
                        alpha = s
                best_overall = best_this
                if best_score > 90000:
                    break
            except _Timeout:
                break
            except Exception:
                break
        return _bit_to_str(best_overall)
    except Exception:
        try:
            return _brute_fallback(you, opponent)
        except Exception:
            return "pass"
