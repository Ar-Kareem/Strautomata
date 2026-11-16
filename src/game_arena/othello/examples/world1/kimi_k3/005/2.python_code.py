

import time
import numpy as np

FULL = (1 << 64) - 1
NA = 0xFEFEFEFEFEFEFEFE          # files b..h (exclude file a)
NH = 0x7F7F7F7F7F7F7F7F          # files a..g (exclude file h)
PMASK = {1: NA, 7: NH, 8: FULL, 9: NA}
NMASK = {1: NH, 7: NA, 8: FULL, 9: NH}
OFF = (1, -1, 7, -7, 8, -8, 9, -9)

pop = int.bit_count if hasattr(int, "bit_count") else (lambda x: bin(x).count("1"))

def sft(x, o):
    if o > 0:
        return (x << o) & PMASK[o]
    return (x >> (-o)) & NMASK[-o]

def mobility(me, opp, E):
    m = 0
    for o in OFF:
        x = sft(me, -o) & opp
        x |= sft(x, -o) & opp
        x |= sft(x, -o) & opp
        x |= sft(x, -o) & opp
        x |= sft(x, -o) & opp
        x |= sft(x, -o) & opp
        m |= sft(x, -o) & E
    return m

def flips(me, opp, b):
    f = 0
    for o in OFF:
        x = sft(b, o) & opp
        x |= sft(x, o) & opp
        x |= sft(x, o) & opp
        x |= sft(x, o) & opp
        x |= sft(x, o) & opp
        x |= sft(x, o) & opp
        x |= sft(x, o) & opp
        if sft(x, o) & me:
            f |= x
    return f

W = [
    100, -25, 10, 5, 5, 10, -25, 100,
    -25, -50, 0, 0, 0, 0, -50, -25,
    10, 0, 5, 0, 0, 5, 0, 10,
    5, 0, 0, 0, 0, 0, 0, 5,
    5, 0, 0, 0, 0, 0, 0, 5,
    10, 0, 5, 0, 0, 5, 0, 10,
    -25, -50, 0, 0, 0, 0, -50, -25,
    100, -25, 10, 5, 5, 10, -25, 100]
ORDER = W

ROWSC = []
for r in range(8):
    t = [0] * 256
    for byte in range(256):
        s = 0
        for c in range(8):
            if byte >> c & 1:
                s += W[8 * r + c]
        t[byte] = s
    ROWSC.append(t)

# corner bit, X bit, combined C bits
CORNERS = [
    (1 << 0, 1 << 9, (1 << 1) | (1 << 8)),
    (1 << 7, 1 << 14, (1 << 6) | (1 << 15)),
    (1 << 56, 1 << 49, (1 << 48) | (1 << 57)),
    (1 << 63, 1 << 54, (1 << 62) | (1 << 55))]

INF = 1 << 30
WIN = 100000

def terminal(me, opp):
    d = pop(me) - pop(opp)
    if d > 0:
        return WIN + d
    if d < 0:
        return -WIN + d
    return 0

def evaluate(me, opp, E, m):
    s = 0
    for r in range(8):
        sh = 8 * r
        s += ROWSC[r][(me >> sh) & 255] - ROWSC[r][(opp >> sh) & 255]
    mo = mobility(opp, me, E)
    s += 14 * (pop(m) - pop(mo))
    pm = 0
    po = 0
    for o in OFF:
        pm |= sft(opp, o)
        po |= sft(me, o)
    s += 2 * (pop(pm & E) - pop(po & E))
    for cb, xb, cc in CORNERS:
        if me & cb:
            s += 45
        elif opp & cb:
            s -= 45
        else:
            if me & xb:
                s -= 30
            if opp & xb:
                s += 30
            if me & cc:
                s -= 8
            if opp & cc:
                s += 8
    s += 2 * (pop(me) - pop(opp))
    return s

class Abort(Exception):
    pass

tt = {}
nodes = 0
deadline = 0.0

def search(me, opp, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 2047) == 0 and time.perf_counter() > deadline:
        raise Abort()
    aorig = alpha
    bestmove = -1
    entry = tt.get((me, opp))
    if entry is not None:
        d, v, fl, bm = entry
        if d >= depth and ply > 0:
            if fl == 0:
                return v
            if fl == 1 and v >= beta:
                return v
            if fl == 2 and v <= alpha:
                return v
        if bm >= 0:
            bestmove = bm
    E = FULL & ~(me | opp)
    if E == 0:
        return terminal(me, opp)
    m = mobility(me, opp, E)
    if m == 0:
        if mobility(opp, me, E) == 0:
            return terminal(me, opp)
        return -search(opp, me, depth, -beta, -alpha, ply + 1)
    if depth == 0:
        return evaluate(me, opp, E, m)
    mv = []
    mm = m
    while mm:
        b = mm & -mm
        mm ^= b
        sq = b.bit_length() - 1
        mv.append((ORDER[sq], b, sq))
    mv.sort(key=lambda t: -t[0])
    if bestmove >= 0:
        for i, t in enumerate(mv):
            if t[2] == bestmove:
                mv.insert(0, mv.pop(i))
                break
    best = -INF
    a = alpha
    bests = mv[0][2]
    for _, b, sq in mv:
        f = flips(me, opp, b)
        val = -search(opp & ~f, me | b | f, depth - 1, -beta, -a, ply + 1)
        if val > best:
            best = val
            bests = sq
        if best > a:
            a = best
        if a >= beta:
            break
    if best <= aorig:
        fl = 2
    elif best >= beta:
        fl = 1
    else:
        fl = 0
    tt[(me, opp)] = (depth, best, fl, bests)
    return best

def tobits(a):
    idx = np.nonzero(a.reshape(64))[0]
    b = 0
    for i in idx:
        b |= 1 << int(i)
    return b

def mstr(sq):
    return chr(97 + (sq & 7)) + str((sq >> 3) + 1)

def policy(you, opponent):
    global deadline, nodes
    deadline = time.perf_counter() + 0.95
    nodes = 0
    me = tobits(you)
    opp = tobits(opponent)
    E = FULL & ~(me | opp)
    m = mobility(me, opp, E)
    if m == 0:
        return "pass"
    mv = []
    mm = m
    while mm:
        b = mm & -mm
        mm ^= b
        sq = b.bit_length() - 1
        mv.append((ORDER[sq], b, sq))
    mv.sort(key=lambda t: -t[0])
    if len(mv) == 1:
        return mstr(mv[0][2])
    best = mv[0][2]
    depth = 2
    while depth <= 64:
        try:
            search(me, opp, depth, -INF, INF, 0)
            e = tt.get((me, opp))
            if e is not None and e[3] >= 0:
                best = e[3]
        except Abort:
            break
        depth += 1
    return mstr(best)

