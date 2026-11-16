
import time
import random

INF = 10 ** 9
WIN = 1000000

DIRS = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
# line kind per direction: 0=row, 1=col, 2=diag(r-c), 3=anti(r+c)
KINDS = (2, 1, 3, 0, 0, 3, 1, 2)

NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
FULL64 = (1 << 64) - 1

try:
    (1).bit_count
    def popcount(x):
        return x.bit_count()
except AttributeError:
    _POPT = [0] * 256
    for _i in range(1, 256):
        _POPT[_i] = _POPT[_i >> 1] + (_i & 1)
    def popcount(x):
        c = 0
        while x:
            c += _POPT[x & 255]
            x >>= 8
        return c

# ---------------- Precomputed geometry tables ----------------
RAY = []    # RAY[i][d] = list of squares along direction d from square i
CIDX = []   # CIDX[i][d] = index into line-count array for (square, direction)
NEIGH = []  # NEIGH[i] = 8-neighbour squares of i
CENT4 = []  # centrality bonus (integer)
for i in range(64):
    r = i >> 3
    c = i & 7
    base_idx = (r, 8 + c, 23 + r - c, 31 + r + c)
    rays = []
    cidx = []
    for d in range(8):
        dr, dc = DIRS[d]
        ray = []
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            ray.append((nr << 3) | nc)
            nr += dr
            nc += dc
        rays.append(ray)
        cidx.append(base_idx[KINDS[d]])
    RAY.append(rays)
    CIDX.append(cidx)
    lst = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                lst.append((nr << 3) | nc)
    NEIGH.append(lst)
    a = r - 3.5
    if a < 0: a = -a
    e = c - 3.5
    if e < 0: e = -e
    CENT4.append(int(4 * (3.5 - (a if a > e else e))))

_rng = random.Random(987654321)
ZOBR = [[_rng.getrandbits(64), _rng.getrandbits(64)] for _ in range(64)]
SIDE_BIT = _rng.getrandbits(64)

TT = {}
deadline = 0.0
nodes = 0

class SearchTimeout(Exception):
    pass

def check_time():
    global nodes
    nodes += 1
    if (nodes & 511) == 0 and time.time() >= deadline:
        raise SearchTimeout

# ---------------- Bitboard connectivity ----------------
def dilate(bb):
    x = bb | ((bb & NOT_H) << 1) | ((bb & NOT_A) >> 1) | ((bb << 8) & FULL64) | (bb >> 8)
    x |= ((bb & NOT_H) >> 7) | ((bb & NOT_A) >> 9) | (((bb & NOT_H) << 9) & FULL64) | (((bb & NOT_A) << 7) & FULL64)
    return x

def bb_connected(bb, n):
    if n <= 1:
        return True
    group = bb & (-bb)
    while True:
        g = group | (dilate(group) & bb)
        if g == group:
            return group == bb
        group = g

def bb_components(bb):
    comps = 0
    largest = 0
    rem = bb
    while rem:
        comps += 1
        group = rem & (-rem)
        while True:
            g = group | (dilate(group) & rem)
            if g == group:
                break
            group = g
        rem &= ~group
        sz = popcount(group)
        if sz > largest:
            largest = sz
    return comps, largest

# ---------------- Evaluation ----------------
def quality(bb, n):
    if n == 0:
        return 0.0
    comps, largest = bb_components(bb)
    m = bb
    cr = []
    cc = []
    sr = 0
    sc = 0
    while m:
        lsb = m & (-m)
        i = lsb.bit_length() - 1
        m ^= lsb
        r = i >> 3
        c = i & 7
        cr.append(r)
        cc.append(c)
        sr += r
        sc += c
    mr = sr / n
    mc = sc / n
    disp = 0.0
    cent = 0.0
    for k in range(n):
        r = cr[k]
        c = cc[k]
        dr = r - mr
        dc = c - mc
        disp += dr * dr + dc * dc
        a = r - 3.5
        if a < 0: a = -a
        e = c - 3.5
        if e < 0: e = -e
        cent += 3.5 - (a if a > e else e)
    disp /= n
    cent /= n
    return -100.0 * comps + 18.0 * largest - 6.0 * disp + 3.0 * cent

def evaluate(bb1, bb2, player):
    q1 = quality(bb1, popcount(bb1))
    q2 = quality(bb2, popcount(bb2))
    return q1 - q2 if player == 1 else q2 - q1

# ---------------- Move generation ----------------
def compute_counts(bb_all):
    C = [0] * 46
    m = bb_all
    while m:
        lsb = m & (-m)
        i = lsb.bit_length() - 1
        m ^= lsb
        r = i >> 3
        c = i & 7
        C[r] += 1
        C[8 + c] += 1
        C[23 + r - c] += 1
        C[31 + r + c] += 1
    return C

def gen_moves(b, player, my_bb, C):
    opp = -player
    moves = []
    m = my_bb
    while m:
        lsb = m & (-m)
        i = lsb.bit_length() - 1
        m ^= lsb
        cidx = CIDX[i]
        rays = RAY[i]
        for d in range(8):
            steps = C[cidx[d]]
            ray = rays[d]
            if steps > len(ray):
                continue
            t = ray[steps - 1]
            ok = True
            for k in range(steps - 1):
                if b[ray[k]] == opp:
                    ok = False
                    break
            if not ok:
                continue
            v = b[t]
            if v == player:
                continue
            sc = CENT4[t]
            if v == opp:
                sc += 1000
            adj = 0
            for j in NEIGH[t]:
                if j != i and b[j] == player:
                    adj += 1
            sc += adj * 25
            moves.append((sc, i, t))
    moves.sort(key=lambda x: x[0], reverse=True)
    return moves

# ---------------- Search ----------------
def negamax(b, bb1, bb2, player, depth, alpha, beta, ply, h):
    check_time()
    key = (h ^ SIDE_BIT) if player == -1 else h
    e = TT.get(key)
    ttmove = -1
    if e is not None:
        ed, ev, ef, em = e
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
        ttmove = em
    if depth == 0:
        return evaluate(bb1, bb2, player)
    if player == 1:
        my_bb = bb1
        op_bb = bb2
        pi = 1
        cpi = 0
    else:
        my_bb = bb2
        op_bb = bb1
        pi = 0
        cpi = 1
    C = compute_counts(bb1 | bb2)
    moves = gen_moves(b, player, my_bb, C)
    if not moves:
        return -(WIN - ply)
    if ttmove >= 0:
        mf = ttmove >> 8
        mt = ttmove & 255
        for idx in range(len(moves)):
            if moves[idx][1] == mf and moves[idx][2] == mt:
                moves.insert(0, moves.pop(idx))
                break
    alpha0 = alpha
    best = -INF
    bm = -1
    npieces = popcount(my_bb)
    for sc, i, t in moves:
        captured = b[t]
        b[i] = 0
        b[t] = player
        nmy = my_bb ^ (1 << i) ^ (1 << t)
        nh = h ^ ZOBR[i][pi] ^ ZOBR[t][pi]
        if captured:
            nop = op_bb ^ (1 << t)
            nh ^= ZOBR[t][cpi]
        else:
            nop = op_bb
        if bb_connected(nmy, npieces):
            val = WIN - ply - 1                     # mover connected -> mover wins
        elif captured and bb_connected(nop, popcount(nop)):
            val = -(WIN - ply - 1)                  # capture connected the opponent -> bad
        else:
            if player == 1:
                val = -negamax(b, nmy, nop, -1, depth - 1, -beta, -alpha, ply + 1, nh)
            else:
                val = -negamax(b, nop, nmy, 1, depth - 1, -beta, -alpha, ply + 1, nh)
        b[t] = captured
        b[i] = player
        if val > best:
            best = val
            bm = (i << 8) | t
        if val > alpha:
            alpha = val
            if alpha >= beta:
                break
    if best <= alpha0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, bm)
    return best

def root_search(b, bb1, bb2, depth, h, prev_best, C):
    moves = gen_moves(b, 1, bb1, C)
    if prev_best is not None:
        pf, pt = prev_best
        for idx in range(len(moves)):
            if moves[idx][1] == pf and moves[idx][2] == pt:
                moves.insert(0, moves.pop(idx))
                break
    best = None
    bestval = -INF
    alpha = -INF
    npieces = popcount(bb1)
    for sc, i, t in moves:
        check_time()
        captured = b[t]
        b[i] = 0
        b[t] = 1
        nmy = bb1 ^ (1 << i) ^ (1 << t)
        nh = h ^ ZOBR[i][1] ^ ZOBR[t][1]
        if captured:
            nop = bb2 ^ (1 << t)
            nh ^= ZOBR[t][0]
        else:
            nop = bb2
        if bb_connected(nmy, npieces):
            val = WIN
        elif captured and bb_connected(nop, popcount(nop)):
            val = -WIN
        else:
            val = -negamax(b, nmy, nop, -1, depth - 1, -INF, -alpha, 1, nh)
        b[t] = captured
        b[i] = 1
        if val > bestval:
            bestval = val
            best = (i, t)
        if val > alpha:
            alpha = val
        if bestval >= WIN - 5:
            break
    return best, bestval

def fallback_move(b):
    for i in range(64):
        if b[i] == 1:
            r = i >> 3
            c = i & 7
            return "%d,%d:%d,%d" % (r, c, r, c)
    return "0,0:0,0"

# ---------------- Required API ----------------
def policy(board):
    global deadline, nodes, TT
    b = [0] * 64
    for r in range(8):
        rw = board[r]
        base = r << 3
        for c in range(8):
            b[base + c] = int(rw[c])
    bb1 = 0
    bb2 = 0
    h = 0
    for i in range(64):
        v = b[i]
        if v == 1:
            bb1 |= 1 << i
            h ^= ZOBR[i][1]
        elif v == -1:
            bb2 |= 1 << i
            h ^= ZOBR[i][0]
    C = compute_counts(bb1 | bb2)
    moves = gen_moves(b, 1, bb1, C)
    if not moves:
        return fallback_move(b)
    if len(moves) == 1:
        _, i, t = moves[0]
        return "%d,%d:%d,%d" % (i >> 3, i & 7, t >> 3, t & 7)
    TT = {}
    nodes = 0
    start = time.time()
    deadline = start + 0.85
    best = None
    try:
        for depth in range(1, 65):
            mv, val = root_search(b, bb1, bb2, depth, h, best, C)
            if mv is not None:
                best = mv
            if val >= WIN - 5:
                break
            if time.time() >= deadline - 0.02:
                break
    except SearchTimeout:
        pass
    if best is None:
        best = (moves[0][1], moves[0][2])
    i, t = best
    return "%d,%d:%d,%d" % (i >> 3, i & 7, t >> 3, t & 7)
