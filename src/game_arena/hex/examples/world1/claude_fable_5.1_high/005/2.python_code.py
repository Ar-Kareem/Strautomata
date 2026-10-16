
import numpy as np
import time
from math import log

N = 11
NN = N * N
EPS = 0.05
LEAK = 1e-7
TIME_LIMIT = 0.8

OFFS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
NEIGH = [[] for _ in range(NN)]
_eu = []
_ev = []
for _r in range(N):
    for _c in range(N):
        _u = _r * N + _c
        for _dr, _dc in OFFS:
            _rr, _cc = _r + _dr, _c + _dc
            if 0 <= _rr < N and 0 <= _cc < N:
                _v = _rr * N + _cc
                NEIGH[_u].append(_v)
                if _v > _u:
                    _eu.append(_u)
                    _ev.append(_v)
EU = np.array(_eu)
EV = np.array(_ev)
TOP = np.arange(N)
BOT = np.arange(NN - N, NN)
DIAG = np.arange(NN)


def resistance(cells):
    # cells: flat numpy array, 1 = own stone (connect top-bottom), -1 = blocked, 0 = empty
    r = np.where(cells == 1, EPS, 1.0)
    ok = cells != -1
    g = np.where(ok[EU] & ok[EV], 2.0 / (r[EU] + r[EV]), 0.0)
    L = np.zeros((NN, NN))
    L[EU, EV] = -g
    L[EV, EU] = -g
    diag = np.bincount(EU, weights=g, minlength=NN) + np.bincount(EV, weights=g, minlength=NN)
    gtop = np.where(ok[TOP], 2.0 / r[TOP], 0.0)
    gbot = np.where(ok[BOT], 2.0 / r[BOT], 0.0)
    diag[TOP] += gtop
    diag[BOT] += gbot
    diag += LEAK
    L[DIAG, DIAG] = diag
    rhs = np.zeros(NN)
    rhs[TOP] = gtop
    try:
        v = np.linalg.solve(L, rhs)
    except Exception:
        return 1e6
    I = float(np.sum(gtop * (1.0 - v[TOP])))
    if not np.isfinite(I) or I <= 1e-12:
        return 1e6
    return 1.0 / I


def evaluate(b):
    me_cells = b.ravel()
    opp_cells = (-b.T).ravel()
    rm = resistance(me_cells)
    ro = resistance(opp_cells)
    return log(max(rm, 1e-12)) - log(max(ro, 1e-12))


def connected_tb(cells):
    seen = [False] * NN
    stack = [i for i in range(N) if cells[i] == 1]
    for i in stack:
        seen[i] = True
    while stack:
        u = stack.pop()
        if u >= NN - N:
            return True
        for v in NEIGH[u]:
            if not seen[v] and cells[v] == 1:
                seen[v] = True
                stack.append(v)
    return False


def policy(me, opp, color):
    t0 = time.time()
    b = np.zeros((N, N), dtype=np.int64)
    for (r, c) in me:
        if color == 'b':
            b[r, c] = 1
        else:
            b[c, r] = 1
    for (r, c) in opp:
        if color == 'b':
            b[r, c] = -1
        else:
            b[c, r] = -1

    def out(m):
        return (int(m[0]), int(m[1])) if color == 'b' else (int(m[1]), int(m[0]))

    empties = [(r, c) for r in range(N) for c in range(N) if b[r, c] == 0]
    if not empties:
        return (0, 0)
    if len(me) == 0 and len(opp) == 0:
        return out((5, 5))

    try:
        # immediate win
        for (r, c) in empties:
            b[r, c] = 1
            win = connected_tb(b.ravel().tolist())
            b[r, c] = 0
            if win:
                return out((r, c))

        # opponent threats
        threats = []
        for (r, c) in empties:
            b[r, c] = -1
            thr = connected_tb((-b.T).ravel().tolist())
            b[r, c] = 0
            if thr:
                threats.append((r, c))
        if len(threats) == 1:
            return out(threats[0])

        cand = threats if threats else empties

        # 1-ply evaluation of my moves
        scores = {}
        for m in cand:
            b[m] = 1
            scores[m] = evaluate(b)
            b[m] = 0
        order = sorted(cand, key=lambda m: scores[m])
        best = order[0]
        if threats:
            return out(best)
        if time.time() - t0 > 0.4:
            return out(best)

        # 1-ply evaluation of opponent moves (to rank replies)
        oscores = {}
        for m in empties:
            b[m] = -1
            oscores[m] = evaluate(b)
            b[m] = 0
        oorder = sorted(empties, key=lambda m: -oscores[m])
        replies = oorder[:10]
        for m in order[:5]:
            if m not in replies:
                replies.append(m)

        # pruned 2-ply minimax
        K = 8
        best2 = None
        bestval = float('inf')
        for m in order[:K]:
            if time.time() - t0 > TIME_LIMIT:
                break
            b[m] = 1
            worst = -float('inf')
            for rp in replies:
                if rp == m:
                    continue
                if time.time() - t0 > TIME_LIMIT:
                    worst = float('inf')
                    break
                b[rp] = -1
                s = evaluate(b)
                b[rp] = 0
                if s > worst:
                    worst = s
                if worst >= bestval:
                    break
            b[m] = 0
            if worst < bestval:
                bestval = worst
                best2 = m
        if best2 is not None:
            return out(best2)
        return out(best)
    except Exception:
        # safety fallback: any legal cell, prefer center-ish
        empties.sort(key=lambda m: abs(m[0] - 5) + abs(m[1] - 5))
        return out(empties[0])
