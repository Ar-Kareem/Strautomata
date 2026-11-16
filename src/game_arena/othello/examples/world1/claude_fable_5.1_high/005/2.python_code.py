
import numpy as np
import time

# ---------------- constants ----------------
FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
NOT_AB = 0xFCFCFCFCFCFCFCFC
NOT_GH = 0x3F3F3F3F3F3F3F3F
NOT_ABCD = 0xF0F0F0F0F0F0F0F0
NOT_EFGH = 0x0F0F0F0F0F0F0F0F
COL_A = 0x0101010101010101
COL_H = 0x8080808080808080
ROW_1 = 0xFF
ROW_8 = 0xFF << 56
EDGE_LR = COL_A | COL_H
EDGE_TB = ROW_1 | ROW_8
EDGES = EDGE_LR | EDGE_TB
CORNERS = 1 | (1 << 7) | (1 << 56) | (1 << 63)

INF = 10 ** 9
WIN = 20000
TIME_BUDGET = 0.6

try:
    popcount = int.bit_count
    popcount(5)
except Exception:
    def popcount(x):
        return bin(x).count('1')

# positional weights
W = [
    [60, -15, 10, 5, 5, 10, -15, 60],
    [-15, -40, -3, -2, -2, -3, -40, -15],
    [10, -3, 2, 1, 1, 2, -3, 10],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [5, -2, 1, 0, 0, 1, -2, 5],
    [10, -3, 2, 1, 1, 2, -3, 10],
    [-15, -40, -3, -2, -2, -3, -40, -15],
    [60, -15, 10, 5, 5, 10, -15, 60],
]
ROWW = [[sum(W[r][c] for c in range(8) if (b >> c) & 1) for b in range(256)] for r in range(8)]
ORD = [W[i >> 3][i & 7] for i in range(64)]
CORNER_ADJ = [
    (0, ((9, 40), (1, 15), (8, 15))),
    (7, ((14, 40), (6, 15), (15, 15))),
    (56, ((49, 40), (48, 15), (57, 15))),
    (63, ((54, 40), (55, 15), (62, 15))),
]

TT = {}
nodes = 0
deadline = 0.0


class Timeout(Exception):
    pass


# ---------------- bitboard ops ----------------
def gen_moves(me, opp):
    empty = ~(me | opp) & FULL
    # N
    t = (me >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    t |= (t >> 8) & opp
    mv = t >> 8
    # S
    t = (me << 8) & opp
    t |= (t << 8) & opp
    t |= (t << 8) & opp
    t |= (t << 8) & opp
    t |= (t << 8) & opp
    t |= (t << 8) & opp
    mv |= t << 8
    # E
    t = (me << 1) & NOT_A & opp
    t |= (t << 1) & NOT_A & opp
    t |= (t << 1) & NOT_A & opp
    t |= (t << 1) & NOT_A & opp
    t |= (t << 1) & NOT_A & opp
    t |= (t << 1) & NOT_A & opp
    mv |= (t << 1) & NOT_A
    # W
    t = (me >> 1) & NOT_H & opp
    t |= (t >> 1) & NOT_H & opp
    t |= (t >> 1) & NOT_H & opp
    t |= (t >> 1) & NOT_H & opp
    t |= (t >> 1) & NOT_H & opp
    t |= (t >> 1) & NOT_H & opp
    mv |= (t >> 1) & NOT_H
    # NE
    t = (me >> 7) & NOT_A & opp
    t |= (t >> 7) & NOT_A & opp
    t |= (t >> 7) & NOT_A & opp
    t |= (t >> 7) & NOT_A & opp
    t |= (t >> 7) & NOT_A & opp
    t |= (t >> 7) & NOT_A & opp
    mv |= (t >> 7) & NOT_A
    # NW
    t = (me >> 9) & NOT_H & opp
    t |= (t >> 9) & NOT_H & opp
    t |= (t >> 9) & NOT_H & opp
    t |= (t >> 9) & NOT_H & opp
    t |= (t >> 9) & NOT_H & opp
    t |= (t >> 9) & NOT_H & opp
    mv |= (t >> 9) & NOT_H
    # SE
    t = (me << 9) & NOT_A & opp
    t |= (t << 9) & NOT_A & opp
    t |= (t << 9) & NOT_A & opp
    t |= (t << 9) & NOT_A & opp
    t |= (t << 9) & NOT_A & opp
    t |= (t << 9) & NOT_A & opp
    mv |= (t << 9) & NOT_A
    # SW
    t = (me << 7) & NOT_H & opp
    t |= (t << 7) & NOT_H & opp
    t |= (t << 7) & NOT_H & opp
    t |= (t << 7) & NOT_H & opp
    t |= (t << 7) & NOT_H & opp
    t |= (t << 7) & NOT_H & opp
    mv |= (t << 7) & NOT_H
    return mv & empty


def get_flips(me, opp, sq):
    m = 1 << sq
    f = 0
    # N
    t = (m >> 8) & opp
    if t:
        t |= (t >> 8) & opp
        t |= (t >> 8) & opp
        t |= (t >> 8) & opp
        t |= (t >> 8) & opp
        t |= (t >> 8) & opp
        if (t >> 8) & me:
            f |= t
    # S
    t = (m << 8) & opp
    if t:
        t |= (t << 8) & opp
        t |= (t << 8) & opp
        t |= (t << 8) & opp
        t |= (t << 8) & opp
        t |= (t << 8) & opp
        if (t << 8) & me:
            f |= t
    # E
    t = (m << 1) & NOT_A & opp
    if t:
        t |= (t << 1) & NOT_A & opp
        t |= (t << 1) & NOT_A & opp
        t |= (t << 1) & NOT_A & opp
        t |= (t << 1) & NOT_A & opp
        t |= (t << 1) & NOT_A & opp
        if (t << 1) & NOT_A & me:
            f |= t
    # W
    t = (m >> 1) & NOT_H & opp
    if t:
        t |= (t >> 1) & NOT_H & opp
        t |= (t >> 1) & NOT_H & opp
        t |= (t >> 1) & NOT_H & opp
        t |= (t >> 1) & NOT_H & opp
        t |= (t >> 1) & NOT_H & opp
        if (t >> 1) & NOT_H & me:
            f |= t
    # NE
    t = (m >> 7) & NOT_A & opp
    if t:
        t |= (t >> 7) & NOT_A & opp
        t |= (t >> 7) & NOT_A & opp
        t |= (t >> 7) & NOT_A & opp
        t |= (t >> 7) & NOT_A & opp
        t |= (t >> 7) & NOT_A & opp
        if (t >> 7) & NOT_A & me:
            f |= t
    # NW
    t = (m >> 9) & NOT_H & opp
    if t:
        t |= (t >> 9) & NOT_H & opp
        t |= (t >> 9) & NOT_H & opp
        t |= (t >> 9) & NOT_H & opp
        t |= (t >> 9) & NOT_H & opp
        t |= (t >> 9) & NOT_H & opp
        if (t >> 9) & NOT_H & me:
            f |= t
    # SE
    t = (m << 9) & NOT_A & opp
    if t:
        t |= (t << 9) & NOT_A & opp
        t |= (t << 9) & NOT_A & opp
        t |= (t << 9) & NOT_A & opp
        t |= (t << 9) & NOT_A & opp
        t |= (t << 9) & NOT_A & opp
        if (t << 9) & NOT_A & me:
            f |= t
    # SW
    t = (m << 7) & NOT_H & opp
    if t:
        t |= (t << 7) & NOT_H & opp
        t |= (t << 7) & NOT_H & opp
        t |= (t << 7) & NOT_H & opp
        t |= (t << 7) & NOT_H & opp
        t |= (t << 7) & NOT_H & opp
        if (t << 7) & NOT_H & me:
            f |= t
    return f


def neighbors(x):
    return ((x >> 8) | (x << 8) | ((x >> 1) & NOT_H) | ((x << 1) & NOT_A)
            | ((x >> 7) & NOT_A) | ((x >> 9) & NOT_H)
            | ((x << 9) & NOT_A) | ((x << 7) & NOT_H)) & FULL


def stability(me, opp, occ, empty):
    if not (occ & EDGES):
        return 0, 0
    x = empty
    x |= ((x >> 1) & NOT_H) | ((x << 1) & NOT_A)
    x |= ((x >> 2) & NOT_GH) | ((x << 2) & NOT_AB)
    x |= ((x >> 4) & NOT_EFGH) | ((x << 4) & NOT_ABCD)
    sh = (~x & FULL) | EDGE_LR
    x = empty
    x |= (x >> 8) | (x << 8)
    x |= (x >> 16) | (x << 16)
    x |= (x >> 32) | (x << 32)
    sv = (~x & FULL) | EDGE_TB
    x = empty
    x |= ((x >> 7) & NOT_A) | ((x << 7) & NOT_H)
    x |= ((x >> 14) & NOT_AB) | ((x << 14) & NOT_GH)
    x |= ((x >> 28) & NOT_ABCD) | ((x << 28) & NOT_EFGH)
    sd1 = (~x & FULL) | EDGES
    x = empty
    x |= ((x >> 9) & NOT_H) | ((x << 9) & NOT_A)
    x |= ((x >> 18) & NOT_GH) | ((x << 18) & NOT_AB)
    x |= ((x >> 36) & NOT_EFGH) | ((x << 36) & NOT_ABCD)
    sd2 = (~x & FULL) | EDGES
    res = []
    for p in (me, opp):
        st = p & sh & sv & sd1 & sd2
        if st:
            while True:
                n = (p
                     & (sh | ((st >> 1) & NOT_H) | ((st << 1) & NOT_A))
                     & (sv | (st >> 8) | (st << 8))
                     & (sd1 | ((st >> 7) & NOT_A) | ((st << 7) & NOT_H))
                     & (sd2 | ((st >> 9) & NOT_H) | ((st << 9) & NOT_A)))
                if n == st:
                    break
                st = n
        res.append(popcount(st))
    return res[0], res[1]


def terminal_score(me, opp):
    d = popcount(me) - popcount(opp)
    if d > 0:
        return d * 100 + WIN
    if d < 0:
        return d * 100 - WIN
    return 0


def evaluate(me, opp, my_mv):
    op_mv = gen_moves(opp, me)
    my_mob = popcount(my_mv)
    op_mob = popcount(op_mv)
    if my_mob == 0 and op_mob == 0:
        return terminal_score(me, opp)
    occ = me | opp
    empty = ~occ & FULL
    empties = popcount(empty)
    my_pot = popcount(neighbors(opp) & empty)
    op_pot = popcount(neighbors(me) & empty)
    st_me, st_op = stability(me, opp, occ, empty)
    pos = 0
    for r in range(8):
        s = r << 3
        pos += ROWW[r][(me >> s) & 255] - ROWW[r][(opp >> s) & 255]
    for cb, adj in CORNER_ADJ:
        if (occ >> cb) & 1:
            for b, pen in adj:
                if (me >> b) & 1:
                    pos += pen
                elif (opp >> b) & 1:
                    pos -= pen
    disc = popcount(me) - popcount(opp)
    if empties > 44:
        wm, wp, ws, wq, wd, par = 90, 30, 120, 3, 0, 0
    elif empties > 20:
        wm, wp, ws, wq, wd, par = 70, 25, 150, 3, 5, 0
    else:
        wm, wp, ws, wq, wd, par = 40, 10, 180, 2, 30, 30
    score = (wm * (my_mob - op_mob) + wp * (my_pot - op_pot)
             + ws * (st_me - st_op) + wq * pos + wd * disc)
    if par and (empties & 1):
        score += par
    return score


def search(me, opp, depth, alpha, beta, my_mv):
    global nodes
    nodes += 1
    if (nodes & 63) == 0 and time.perf_counter() > deadline:
        raise Timeout()
    if my_mv == 0:
        op_mv = gen_moves(opp, me)
        if op_mv == 0:
            return terminal_score(me, opp)
        return -search(opp, me, depth, -beta, -alpha, op_mv)
    if depth <= 0:
        return evaluate(me, opp, my_mv)
    key = (me, opp)
    e = TT.get(key)
    tt_move = -1
    if e is not None:
        if e[0] >= depth:
            val = e[1]
            flag = e[2]
            if flag == 0:
                return val
            if flag == 1:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val
        tt_move = e[3]
    children = []
    mv = my_mv
    while mv:
        b = mv & -mv
        mv ^= b
        sq = b.bit_length() - 1
        f = get_flips(me, opp, sq)
        nme = me | b | f
        nopp = opp & ~f
        nmv = gen_moves(nopp, nme)
        o = popcount(nmv) * 10 - ORD[sq]
        if sq == tt_move:
            o -= 100000
        children.append((o, sq, nme, nopp, nmv))
    if len(children) > 1:
        children.sort()
    best = -INF
    best_move = -1
    a0 = alpha
    for o, sq, nme, nopp, nmv in children:
        v = -search(nopp, nme, depth - 1, -beta, -alpha, nmv)
        if v > best:
            best = v
            best_move = sq
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    if best <= a0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, best_move)
    return best


def choose_move(me, opp, my_mv):
    global deadline, nodes, TT
    if len(TT) > 400000:
        TT.clear()
    deadline = time.perf_counter() + TIME_BUDGET
    nodes = 0
    empties = popcount(~(me | opp) & FULL)
    children = []
    mv = my_mv
    while mv:
        b = mv & -mv
        mv ^= b
        sq = b.bit_length() - 1
        f = get_flips(me, opp, sq)
        nme = me | b | f
        nopp = opp & ~f
        nmv = gen_moves(nopp, nme)
        children.append((popcount(nmv) * 10 - ORD[sq], sq, nme, nopp, nmv))
    children.sort()
    best_move = children[0][1]
    if len(children) == 1:
        return best_move
    for depth in range(1, empties + 1):
        alpha = -INF
        beta = INF
        cur_best = None
        scored = []
        try:
            for ch in children:
                v = -search(ch[3], ch[2], depth - 1, -beta, -alpha, ch[4])
                scored.append((v, ch))
                if v > alpha:
                    alpha = v
                    cur_best = ch[1]
        except Timeout:
            break
        if cur_best is not None:
            best_move = cur_best
        scored.sort(key=lambda x: -x[0])
        children = [c for _, c in scored]
        if alpha >= WIN:
            break
        if depth >= empties:
            break
    return best_move


def to_bb(a):
    a = np.asarray(a).reshape(64)
    bb = 0
    for i in np.flatnonzero(a):
        bb |= 1 << int(i)
    return bb


def sq_to_str(sq):
    return "abcdefgh"[sq & 7] + str((sq >> 3) + 1)


def naive_move(you, opponent):
    dirs = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for r in range(8):
        for c in range(8):
            if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                for dr, dc in dirs:
                    rr, cc = r + dr, c + dc
                    n = 0
                    while 0 <= rr < 8 and 0 <= cc < 8 and int(opponent[rr][cc]) == 1:
                        rr += dr
                        cc += dc
                        n += 1
                    if n > 0 and 0 <= rr < 8 and 0 <= cc < 8 and int(you[rr][cc]) == 1:
                        return "abcdefgh"[c] + str(r + 1)
    return "pass"


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    try:
        me = to_bb(you)
        opp = to_bb(opponent)
        my_mv = gen_moves(me, opp)
        if my_mv == 0:
            return "pass"
        sq = choose_move(me, opp, my_mv)
        if sq is None or sq < 0 or not ((my_mv >> sq) & 1):
            sq = (my_mv & -my_mv).bit_length() - 1
        return sq_to_str(sq)
    except Exception:
        try:
            return naive_move(you, opponent)
        except Exception:
            return "pass"
