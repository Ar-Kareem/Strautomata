
import numpy as np
import math
import time

N = 11
NC = N * N
SRC = NC
SNK = NC + 1
R_OWN = 0.02
G_BIG = 2.0 / (2 * R_OWN)   # conductance of an own-own link (= 50)
LEAK = 1e-6


def _idx(i, j):
    return i * N + j


def _inb(i, j):
    return 0 <= i < N and 0 <= j < N


_NDIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
NEIGHBORS = []
for i in range(N):
    for j in range(N):
        NEIGHBORS.append([_idx(i + di, j + dj) for di, dj in _NDIRS if _inb(i + di, j + dj)])

_BDIRS = [((-2, 1), (-1, 0), (-1, 1)), ((-1, 2), (-1, 1), (0, 1)), ((1, 1), (0, 1), (1, 0)),
          ((2, -1), (1, -1), (1, 0)), ((1, -2), (0, -1), (1, -1)), ((-1, -1), (-1, 0), (0, -1))]
BRIDGE_PARTNERS = []
for i in range(N):
    for j in range(N):
        lst = []
        for (d, c1, c2) in _BDIRS:
            a, b = i + d[0], j + d[1]
            if _inb(a, b) and _inb(i + c1[0], j + c1[1]) and _inb(i + c2[0], j + c2[1]):
                lst.append(_idx(a, b))
        BRIDGE_PARTNERS.append(lst)

_e1, _e2 = [], []
for i in range(N):
    for j in range(N):
        for di, dj in [(-1, 1), (0, 1), (1, 0)]:
            a, b = i + di, j + dj
            if _inb(a, b):
                _e1.append(_idx(i, j))
                _e2.append(_idx(a, b))
E1 = np.array(_e1, dtype=np.int64)
E2 = np.array(_e2, dtype=np.int64)

_ba, _bb, _bc1, _bc2 = [], [], [], []
for i in range(N):
    for j in range(N):
        for (d, c1, c2) in _BDIRS[:3]:
            a, b = i + d[0], j + d[1]
            p1 = (i + c1[0], j + c1[1])
            p2 = (i + c2[0], j + c2[1])
            if _inb(a, b) and _inb(*p1) and _inb(*p2):
                _ba.append(_idx(i, j))
                _bb.append(_idx(a, b))
                _bc1.append(_idx(*p1))
                _bc2.append(_idx(*p2))
BA = np.array(_ba, dtype=np.int64)
BB = np.array(_bb, dtype=np.int64)
BC1 = np.array(_bc1, dtype=np.int64)
BC2 = np.array(_bc2, dtype=np.int64)

TOP = np.arange(N, dtype=np.int64)
BOT = np.arange(NC - N, NC, dtype=np.int64)
LEFT = np.arange(0, NC, N, dtype=np.int64)
RIGHT = np.arange(N - 1, NC, N, dtype=np.int64)


def _build_templates(color):
    tc, tc1, tc2, tn = [], [], [], []
    if color == 'b':
        for j in range(N - 1):
            tc.append(_idx(1, j)); tc1.append(_idx(0, j)); tc2.append(_idx(0, j + 1)); tn.append(SRC)
        for j in range(1, N):
            tc.append(_idx(N - 2, j)); tc1.append(_idx(N - 1, j - 1)); tc2.append(_idx(N - 1, j)); tn.append(SNK)
    else:
        for i in range(N - 1):
            tc.append(_idx(i, 1)); tc1.append(_idx(i, 0)); tc2.append(_idx(i + 1, 0)); tn.append(SRC)
        for i in range(1, N):
            tc.append(_idx(i, N - 2)); tc1.append(_idx(i - 1, N - 1)); tc2.append(_idx(i, N - 1)); tn.append(SNK)
    return (np.array(tc, dtype=np.int64), np.array(tc1, dtype=np.int64),
            np.array(tc2, dtype=np.int64), np.array(tn, dtype=np.int64))


TEMPL_B = _build_templates('b')
TEMPL_W = _build_templates('w')
_DIAG = np.arange(NC + 2)


def resistance(own, opp, color):
    r = np.ones(NC)
    r[own] = R_OWN
    emp = ~(own | opp)
    g = 2.0 / (r[E1] + r[E2])
    g[opp[E1] | opp[E2]] = 0.0
    A = np.zeros((NC + 2, NC + 2))
    A[E1, E2] = g
    A[E2, E1] = g
    if color == 'b':
        S, T, TEMP = TOP, BOT, TEMPL_B
    else:
        S, T, TEMP = LEFT, RIGHT, TEMPL_W
    gs = 2.0 / r[S]
    gs[opp[S]] = 0.0
    A[S, SRC] = gs
    A[SRC, S] = gs
    gt = 2.0 / r[T]
    gt[opp[T]] = 0.0
    A[T, SNK] = gt
    A[SNK, T] = gt
    m = own[BA] & own[BB] & emp[BC1] & emp[BC2]
    if m.any():
        a = BA[m]; b = BB[m]
        A[a, b] = G_BIG
        A[b, a] = G_BIG
    tc, tc1, tc2, tn = TEMP
    m = own[tc] & emp[tc1] & emp[tc2]
    if m.any():
        cc = tc[m]; nn = tn[m]
        A[cc, nn] = G_BIG
        A[nn, cc] = G_BIG
    deg = A.sum(axis=1)
    deg[:NC] += LEAK
    L = np.diag(deg) - A
    Lint = L[:NC, :NC]
    rhs = -L[:NC, SRC]
    try:
        v = np.linalg.solve(Lint, rhs)
    except Exception:
        return 1e6
    cur = L[SRC, SRC] + L[SRC, :NC] @ v
    if not np.isfinite(cur) or cur <= 1e-9:
        return 1e6
    return float(min(1.0 / cur, 1e6))


def evaluate(myb, opb, c, oc):
    rm = resistance(myb, opb, c)
    ro = resistance(opb, myb, oc)
    return math.log(ro) - math.log(rm)


def has_won(b, color):
    if color == 'b':
        stack = [j for j in range(N) if b[j]]
        seen = set(stack)
        while stack:
            k = stack.pop()
            if k >= NC - N:
                return True
            for nb in NEIGHBORS[k]:
                if b[nb] and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return False
    else:
        stack = [i * N for i in range(N) if b[i * N]]
        seen = set(stack)
        while stack:
            k = stack.pop()
            if k % N == N - 1:
                return True
            for nb in NEIGHBORS[k]:
                if b[nb] and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return False


def _policy(me, opp, color, t0):
    c = str(color).strip().lower()[0]
    if c not in ('b', 'w'):
        c = 'b'
    oc = 'w' if c == 'b' else 'b'
    myb = np.zeros(NC, dtype=bool)
    opb = np.zeros(NC, dtype=bool)
    for (i, j) in me:
        myb[_idx(int(i), int(j))] = True
    for (i, j) in opp:
        opb[_idx(int(i), int(j))] = True
    empties = [k for k in range(NC) if not myb[k] and not opb[k]]
    if not empties:
        raise RuntimeError("no empty")
    if len(empties) == NC:
        return (5, 5)

    # immediate win
    for e in empties:
        myb[e] = True
        w = has_won(myb, c)
        myb[e] = False
        if w:
            return (e // N, e % N)
    # block immediate opponent win
    threats = []
    for e in empties:
        opb[e] = True
        if has_won(opb, oc):
            threats.append(e)
        opb[e] = False
    if threats:
        e = threats[0]
        return (e // N, e % N)

    # 1-ply for my moves
    score1 = {}
    for e in empties:
        myb[e] = True
        score1[e] = evaluate(myb, opb, c, oc)
        myb[e] = False
        if time.time() - t0 > 0.6:
            break
    if len(score1) < len(empties):
        best = max(score1, key=lambda k: score1[k])
        return (best // N, best % N)
    order = sorted(empties, key=lambda e: -score1[e])
    t1 = time.time()
    per = (t1 - t0) / max(1, len(empties))
    remaining = 0.85 - (t1 - t0)

    oppscore = None
    if per * len(empties) < remaining * 0.45:
        oppscore = {}
        for e in empties:
            opb[e] = True
            oppscore[e] = evaluate(myb, opb, c, oc)
            opb[e] = False
    if oppscore is not None:
        opp_order = sorted(empties, key=lambda e: oppscore[e])
    else:
        opp_order = order

    t2 = time.time()
    remaining = 0.85 - (t2 - t0)
    n_evals = int(remaining / per) if per > 0 else 400
    if n_evals < 20:
        return (order[0] // N, order[0] % N)
    K = max(2, min(14, n_evals // 22))
    cands = order[:K]
    base = set(opp_order[:14]) | set(order[:8])

    best = order[0]
    bestval = -float('inf')
    for m in cands:
        if time.time() - t0 > 0.8:
            break
        rep = set(base) | set(NEIGHBORS[m]) | set(BRIDGE_PARTNERS[m])
        rep.discard(m)
        rep = [r for r in rep if (not myb[r]) and (not opb[r])]
        if oppscore is not None:
            rep.sort(key=lambda r: oppscore[r])
        else:
            rep.sort(key=lambda r: -score1[r])
        myb[m] = True
        worst = float('inf')
        complete = True
        for r in rep:
            if time.time() - t0 > 0.85:
                complete = False
                break
            opb[r] = True
            v = evaluate(myb, opb, c, oc)
            opb[r] = False
            if v < worst:
                worst = v
            if worst <= bestval:
                break
        myb[m] = False
        if not complete:
            break
        val = worst + 0.02 * score1[m]
        if val > bestval:
            bestval = val
            best = m
    return (int(best // N), int(best % N))


def policy(me, opp, color):
    t0 = time.time()
    try:
        mv = _policy(me, opp, color, t0)
        r, cc = int(mv[0]), int(mv[1])
        occ = set((int(a), int(b)) for a, b in me) | set((int(a), int(b)) for a, b in opp)
        if 0 <= r < N and 0 <= cc < N and (r, cc) not in occ:
            return (r, cc)
    except Exception:
        pass
    occ = set((int(a), int(b)) for a, b in me) | set((int(a), int(b)) for a, b in opp)
    center_order = sorted(((i, j) for i in range(N) for j in range(N)),
                          key=lambda p: abs(p[0] - 5) + abs(p[1] - 5))
    for p in center_order:
        if p not in occ:
            return p
    return (0, 0)
