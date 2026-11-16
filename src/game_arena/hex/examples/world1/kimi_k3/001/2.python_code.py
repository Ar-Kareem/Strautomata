
import time
import numpy as np

N = 11
NN = N * N
SRC = NN          # supernode for one goal edge
DST = NN + 1      # supernode for the opposite goal edge
NT = NN + 2
BIG = 1e6         # conductance used for "zero resistance" links
INF = 1e9         # weight of a blocked (opponent) cell

# Hex adjacency: all 8 neighbors except (i-1,j-1) and (i+1,j+1)
_NEI = ((-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0))


def _build_edges():
    eu, ev = [], []
    for i in range(N):
        for j in range(N):
            u = i * N + j
            for di, dj in _NEI:
                ni, nj = i + di, j + dj
                if 0 <= ni < N and 0 <= nj < N:
                    v = ni * N + nj
                    if u < v:
                        eu.append(u)
                        ev.append(v)
    return np.array(eu), np.array(ev)


_EU, _EV = _build_edges()
_TOP = np.arange(N)
_BOT = np.arange(NN - N, NN)
_LEFT = np.arange(0, NN, N)
_RIGHT = np.arange(N - 1, NN, N)
_BOT_SET = frozenset(_BOT.tolist())
_RIGHT_SET = frozenset(_RIGHT.tolist())
_CENT = np.array([-(abs(i - 5) + abs(j - 5)) for i in range(N) for j in range(N)])


def _won(stones, extra, color):
    """True if stones + extra cell connects the player's two sides."""
    if color == 'b':
        seeds = [u for u in range(N) if u in stones or u == extra]
        targets = _BOT_SET
    else:
        seeds = [u for u in range(0, NN, N) if u in stones or u == extra]
        targets = _RIGHT_SET
    if not seeds:
        return False
    seen = set(seeds)
    stack = list(seeds)
    while stack:
        u = stack.pop()
        if u in targets:
            return True
        i, j = divmod(u, N)
        for di, dj in _NEI:
            ni, nj = i + di, j + dj
            if 0 <= ni < N and 0 <= nj < N:
                v = ni * N + nj
                if v not in seen and (v in stones or v == extra):
                    seen.add(v)
                    stack.append(v)
    return False


def _resistance(w, bsrc, bdst):
    """Effective resistance between the two goal supernodes.

    w: length-121 array of cell weights (0=own, 1=empty, INF=opponent).
    """
    s = w[_EU] + w[_EV]
    c = np.where(s <= 0.0, BIG, 1.0 / np.maximum(s, 1e-12))
    L = np.zeros((NT, NT))
    np.add.at(L, (_EU, _EU), c)
    np.add.at(L, (_EV, _EV), c)
    np.add.at(L, (_EU, _EV), -c)
    np.add.at(L, (_EV, _EU), -c)
    ws = w[bsrc]
    cs = np.where(ws <= 0.0, BIG, 1.0 / np.maximum(ws, 1e-12))
    np.add.at(L, (bsrc, bsrc), cs)
    np.add.at(L, (bsrc, SRC), -cs)
    np.add.at(L, (SRC, bsrc), -cs)
    L[SRC, SRC] += cs.sum()
    wd = w[bdst]
    cd = np.where(wd <= 0.0, BIG, 1.0 / np.maximum(wd, 1e-12))
    np.add.at(L, (bdst, bdst), cd)
    np.add.at(L, (bdst, DST), -cd)
    np.add.at(L, (DST, bdst), -cd)
    L[DST, DST] += cd.sum()
    # Inject 1A at SRC, ground DST -> R = V(SRC)
    A = L[:DST, :DST]
    I = np.zeros(DST)
    I[SRC] = 1.0
    try:
        V = np.linalg.solve(A, I)
    except np.linalg.LinAlgError:
        return 1e9
    return V[SRC]


def _evalpos(my, op, bsrc, bdst, osrc, odst):
    """Score = opponent resistance - my resistance (higher is better for me)."""
    w1 = np.ones(NN)
    w2 = np.ones(NN)
    lm = list(my)
    lo = list(op)
    if lm:
        w1[lm] = 0.0
        w2[lm] = INF
    if lo:
        w1[lo] = INF
        w2[lo] = 0.0
    r1 = _resistance(w1, bsrc, bdst)
    r2 = _resistance(w2, osrc, odst)
    return r2 - r1


def policy(me, opp, color):
    t0 = time.time()
    try:
        c = color.lower()[0]
    except Exception:
        c = 'b'
    my = set()
    for r, cc in me:
        my.add(int(r) * N + int(cc))
    op = set()
    for r, cc in opp:
        op.add(int(r) * N + int(cc))
    occ = my | op
    empt = [u for u in range(NN) if u not in occ]
    if not empt:
        return (0, 0)
    if len(empt) == 1:
        u = empt[0]
        return (u // N, u % N)
    try:
        if not occ:
            return (5, 5)  # opening: center
        oc = 'w' if c == 'b' else 'b'
        if c == 'b':
            bsrc, bdst, osrc, odst = _TOP, _BOT, _LEFT, _RIGHT
        else:
            bsrc, bdst, osrc, odst = _LEFT, _RIGHT, _TOP, _BOT

        # 1) Immediate winning move
        if len(my) >= 10:
            for m in empt:
                if _won(my, m, c):
                    return (m // N, m % N)

        # 2) Forced block of opponent's immediate winning move
        threats = []
        if len(op) >= 10:
            threats = [m for m in empt if _won(op, m, oc)]
        if threats:
            if len(threats) == 1:
                m = threats[0]
                return (m // N, m % N)
            bestm, bestv = threats[0], -1e18
            for m in threats:
                v = _evalpos(my | {m}, op, bsrc, bdst, osrc, odst)
                if v > bestv:
                    bestv, bestm = v, m
            return (bestm // N, bestm % N)

        # 3) 1-ply resistance evaluation of every legal move
        scores = []
        for m in empt:
            v = _evalpos(my | {m}, op, bsrc, bdst, osrc, odst)
            scores.append((v + 1e-7 * _CENT[m], m))
        scores.sort(reverse=True)
        best_m = scores[0][1]

        # 4) 2-ply: for my top moves, assume the opponent's best reply
        K = min(10, len(scores))
        M = min(18, len(scores))
        replies = [m for _, m in scores[:M]]
        best_val = -1e18
        for _, m in scores[:K]:
            if time.time() - t0 > 0.72:
                break
            my2 = my | {m}
            worst = 1e18
            for n in replies:
                if n == m:
                    continue
                v = _evalpos(my2, op | {n}, bsrc, bdst, osrc, odst)
                if v < worst:
                    worst = v
            if worst > best_val:
                best_val = worst
                best_m = m
        return (best_m // N, best_m % N)
    except Exception:
        u = empt[0]
        return (u // N, u % N)
