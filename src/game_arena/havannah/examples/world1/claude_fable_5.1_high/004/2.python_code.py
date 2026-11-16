
import numpy as np
import math
import time
from itertools import combinations

INF = 1000000
B = 0.6
MU = 1.15
RING_W = 0.7
CW = 0.006
K1 = 22
T1 = 3
T2 = 5

_GEO = {}


class Geo:
    def __init__(self, V):
        R, C = V.shape
        self.R, self.C = R, C
        cells = [(r, c) for r in range(R) for c in range(C) if V[r, c]]
        N = len(cells)
        self.N = N
        self.cells = cells
        idx = {p: i for i, p in enumerate(cells)}
        self.idx = idx
        s3 = math.sqrt(3) / 2.0
        pos = {}
        cand = {}
        if R == C and V[0, 0] and V[R - 1, C - 1]:
            dirs = [(0, 1), (1, 1), (1, 0), (0, -1), (-1, -1), (-1, 0)]
            for (r, c) in cells:
                pos[(r, c)] = (c - 0.5 * r, r * s3)
                cand[(r, c)] = [(r + a, c + b) for a, b in dirs]
        elif R == C and V[0, C - 1] and V[R - 1, 0]:
            dirs = [(0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1), (1, 0)]
            for (r, c) in cells:
                pos[(r, c)] = (c + 0.5 * r, r * s3)
                cand[(r, c)] = [(r + a, c + b) for a, b in dirs]
        else:
            sc = self._offset_shifts(V)
            mode = 'col'
            sr = None
            if sc is None:
                sr = self._offset_shifts(np.ascontiguousarray(V.T))
                if sr is not None:
                    mode = 'row'
                else:
                    sc = [0.5 if c % 2 == 0 else 0.0 for c in range(C)]
            if mode == 'col':
                for (r, c) in cells:
                    pos[(r, c)] = (c * s3, r + sc[c])
                    lst = [(r - 1, c), (r + 1, c)]
                    for c2 in (c - 1, c + 1):
                        if 0 <= c2 < C:
                            d = sc[c2] - sc[c]
                            if d > 1e-9:
                                lst += [(r - 1, c2), (r, c2)]
                            elif d < -1e-9:
                                lst += [(r, c2), (r + 1, c2)]
                            else:
                                lst += [(r - 1, c2), (r, c2), (r + 1, c2)]
                    cand[(r, c)] = lst
            else:
                for (r, c) in cells:
                    pos[(r, c)] = (c + sr[r], r * s3)
                    lst = [(r, c - 1), (r, c + 1)]
                    for r2 in (r - 1, r + 1):
                        if 0 <= r2 < R:
                            d = sr[r2] - sr[r]
                            if d > 1e-9:
                                lst += [(r2, c - 1), (r2, c)]
                            elif d < -1e-9:
                                lst += [(r2, c), (r2, c + 1)]
                            else:
                                lst += [(r2, c - 1), (r2, c), (r2, c + 1)]
                    cand[(r, c)] = lst
        nb0 = []
        for i, p in enumerate(cells):
            lst = []
            for q in cand[p]:
                j = idx.get(q)
                if j is not None and j != i and j not in lst:
                    lst.append(j)
            nb0.append(lst)
        sets = [set(l) for l in nb0]
        nbrs = [[j for j in nb0[i] if i in sets[j]] for i in range(N)]
        P = [pos[p] for p in cells]
        ref = None
        for i in range(N):
            if len(nbrs[i]) == 6:
                j = nbrs[i][0]
                ref = math.atan2(P[j][1] - P[i][1], P[j][0] - P[i][0])
                break
        if ref is None:
            ref = 0.0
        twopi = 2 * math.pi
        cyc = []
        for i in range(N):
            slots = [-1] * 6
            extra = []
            for j in nbrs[i]:
                ang = math.atan2(P[j][1] - P[i][1], P[j][0] - P[i][0])
                s = int(round(((ang - ref) % twopi) / (math.pi / 3))) % 6
                if slots[s] == -1:
                    slots[s] = j
                else:
                    extra.append(j)
            for j in extra:
                for k in range(6):
                    if slots[k] == -1:
                        slots[k] = j
                        break
            cyc.append(slots)
            nbrs[i] = [j for j in slots if j >= 0]
        self.nbrs = nbrs
        self.cyc = cyc
        self.nbr_arr = np.array([[j if j >= 0 else N for j in slots] for slots in cyc], dtype=np.int64)
        deg = [len(l) for l in nbrs]
        self.is_border = [d < 6 for d in deg]
        corners = [i for i in range(N) if deg[i] == 3]
        self.corners = corners
        corner_bit = [0] * N
        for k, i in enumerate(corners):
            corner_bit[i] = 1 << k
        self.corner_bit = corner_bit
        edge_set = set(i for i in range(N) if deg[i] < 6 and deg[i] != 3)
        edge_id = [-1] * N
        edges = []
        for i in sorted(edge_set):
            if edge_id[i] != -1:
                continue
            comp = []
            stack = [i]
            edge_id[i] = len(edges)
            while stack:
                x = stack.pop()
                comp.append(x)
                for y in nbrs[x]:
                    if y in edge_set and edge_id[y] == -1:
                        edge_id[y] = len(edges)
                        stack.append(y)
            edges.append(comp)
        self.edges = edges
        edge_bit = [0] * N
        for e, comp in enumerate(edges):
            for i in comp:
                edge_bit[i] = 1 << e
        self.edge_bit = edge_bit
        nc = len(corners)
        ne = len(edges)
        self.nc = nc
        self.ne = ne
        bits = min(16, max(6, nc, ne))
        self.pop = [bin(i).count('1') for i in range(1 << bits)]
        pairs = list(combinations(range(nc), 2))
        self.pk = np.array([a for a, b in pairs], dtype=np.int64)
        self.pl = np.array([b for a, b in pairs], dtype=np.int64)
        triples = list(combinations(range(ne), 3))
        self.ta = np.array([a for a, b, c in triples], dtype=np.int64)
        self.tb = np.array([b for a, b, c in triples], dtype=np.int64)
        self.tc = np.array([c for a, b, c in triples], dtype=np.int64)
        self.nsrc = nc + ne
        Pa = np.array(P, dtype=np.float64)
        cen = Pa.mean(axis=0)
        d = np.sqrt(((Pa - cen) ** 2).sum(axis=1))
        self.center = int(np.argmin(d))
        mx = d.max() if d.max() > 0 else 1.0
        self.centr = 1.0 - d / mx

    def _offset_shifts(self, V):
        R, C = V.shape
        center = (R - 1) / 2.0
        counts = V.sum(axis=0)
        if counts.max() == counts.min():
            return None
        shifts = [0.0] * C
        prev = None
        for c in range(C):
            rows = np.nonzero(V[:, c])[0]
            if len(rows) == 0:
                continue
            if rows[-1] - rows[0] + 1 != len(rows):
                return None
            sh = center - (rows[0] + rows[-1]) / 2.0
            if abs(sh * 2 - round(sh * 2)) > 1e-9:
                return None
            shifts[c] = sh
            if prev is not None and abs(abs(sh - prev) - 0.5) > 1e-9:
                return None
            prev = sh
        return shifts

    def dist_maps(self, cost):
        N = self.N
        S = self.nsrc
        D = np.full((S, N + 1), INF, dtype=np.int64)
        for k, ci in enumerate(self.corners):
            D[k, ci] = cost[ci]
        for e, cl in enumerate(self.edges):
            D[self.nc + e, cl] = cost[cl]
        costb = cost[None, :]
        nbr = self.nbr_arr
        cur = D[:, :N]
        for _ in range(400):
            M = D[:, nbr].min(axis=2) + costb
            np.minimum(M, INF, out=M)
            new = np.minimum(cur, M)
            if np.array_equal(new, cur):
                break
            D[:, :N] = new
            cur = D[:, :N]
        return cur.copy()

    def ring_costs(self, bnp, P):
        Pm = np.concatenate([(bnp == P).astype(np.int64), np.array([0], dtype=np.int64)])
        Om = np.concatenate([(bnp == 3 - P).astype(np.int64), np.array([1], dtype=np.int64)])
        nbP = Pm[self.nbr_arr].sum(axis=1)
        nbO = Om[self.nbr_arr].sum(axis=1)
        return np.where(nbO == 0, 6 - nbP, INF)

    def cost_of(self, bnp, P):
        return np.where(bnp == P, 0, np.where(bnp == 0, 1, INF)).astype(np.int64)

    def side_score(self, bnp, P):
        cost = self.cost_of(bnp, P)
        D = self.dist_maps(cost)
        nc = self.nc
        Dc = D[:nc]
        De = D[nc:]
        s = 0.0
        if len(self.pk):
            br = (Dc[self.pk] + Dc[self.pl] - cost[None, :]).min(axis=1)
            s += (B ** np.clip(br, 0, 60)).sum()
        if len(self.ta):
            fk = (De[self.ta] + De[self.tb] + De[self.tc] - 2 * cost[None, :]).min(axis=1)
            s += (B ** np.clip(fk, 0, 60)).sum()
        rc = self.ring_costs(bnp, P)
        s += RING_W * (B ** np.clip(rc, 0, 60)).sum()
        return s, D, cost

    def via_values(self, bnp, P, D):
        nc = self.nc
        Dc = D[:nc]
        De = D[nc:]
        val = np.zeros(self.N)
        if len(self.pk):
            vb = Dc[self.pk] + Dc[self.pl] - 2
            val += (B ** np.clip(vb, 0, 60)).sum(axis=0)
        if len(self.ta):
            vf = De[self.ta] + De[self.tb] + De[self.tc] - 3
            val += (B ** np.clip(vf, 0, 60)).sum(axis=0)
        rc = self.ring_costs(bnp, P)
        rv = np.concatenate([B ** np.clip(rc - 1, 0, 60), np.array([0.0])])
        val += RING_W * rv[self.nbr_arr].sum(axis=1)
        return val

    def prescore(self, bnp):
        total = np.zeros(self.N)
        for P in (1, 2):
            cost = self.cost_of(bnp, P)
            D = self.dist_maps(cost)
            total += self.via_values(bnp, P, D)
        return total


def get_geo(valid_mask):
    V = np.asarray(valid_mask, dtype=bool)
    key = (V.shape, V.tobytes())
    g = _GEO.get(key)
    if g is None:
        g = Geo(V)
        _GEO[key] = g
    return g


def build_uf(g, board, P):
    N = g.N
    parent = list(range(N))
    gE = [0] * N
    gC = [0] * N
    eb = g.edge_bit
    cb = g.corner_bit
    nbrs = g.nbrs

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(N):
        if board[i] == P:
            gE[i] = eb[i]
            gC[i] = cb[i]
    for i in range(N):
        if board[i] == P:
            for j in nbrs[i]:
                if j > i and board[j] == P:
                    a = find(i)
                    b = find(j)
                    if a != b:
                        parent[a] = b
                        gE[b] |= gE[a]
                        gC[b] |= gC[a]
    return parent, gE, gC, find


def ring_check(g, board, P, w):
    board[w] = P
    nbrs = g.nbrs
    isb = g.is_border
    visited = bytearray(g.N)
    found = False
    for n in nbrs[w]:
        if board[n] != P and not visited[n]:
            stack = [n]
            visited[n] = 1
            reached = False
            while stack:
                x = stack.pop()
                if isb[x]:
                    reached = True
                    break
                for y in nbrs[x]:
                    if board[y] != P and not visited[y]:
                        visited[y] = 1
                        stack.append(y)
            if not reached:
                found = True
                break
    board[w] = 0
    return found


def wins_at(g, board, P, w, uf):
    parent, gE, gC, find = uf
    E = g.edge_bit[w]
    Cm = g.corner_bit[w]
    seen = ()
    nbrs = g.nbrs
    for j in nbrs[w]:
        if board[j] == P:
            r = find(j)
            if r not in seen:
                seen = seen + (r,)
                E |= gE[r]
                Cm |= gC[r]
    pop = g.pop
    if pop[Cm] >= 2 or pop[E] >= 3:
        return True
    isb = g.is_border
    for j in nbrs[w]:
        if board[j] == P and not isb[j]:
            ok = True
            for k in nbrs[j]:
                if k != w and board[k] != P:
                    ok = False
                    break
            if ok:
                return True
    cyc = g.cyc[w]
    last = cyc[5]
    prevP = (last >= 0 and board[last] == P)
    arcs = 0
    for j in cyc:
        cur = (j >= 0 and board[j] == P)
        if prevP and not cur:
            arcs += 1
        prevP = cur
    if arcs >= 2:
        return ring_check(g, board, P, w)
    return False


def wins_after(g, board, P, m, limit=2):
    board[m] = P
    uf = build_uf(g, board, P)
    find = uf[3]
    rm = find(m)
    nbrs = g.nbrs
    res = []
    for w in range(g.N):
        if board[w] != 0:
            continue
        adj = False
        for j in nbrs[w]:
            if board[j] == P and find(j) == rm:
                adj = True
                break
        if adj and wins_at(g, board, P, w, uf):
            res.append(w)
            if len(res) >= limit:
                break
    board[m] = 0
    return res


def near(g, board, P):
    N = g.N
    mark = bytearray(N)
    nbrs = g.nbrs
    for i in range(N):
        if board[i] == P:
            for j in nbrs[i]:
                mark[j] = 1
                for k in nbrs[j]:
                    mark[k] = 1
    return [i for i in range(N) if mark[i] and board[i] == 0]


def _policy(me, opp, valid_mask):
    t0 = time.time()
    g = get_geo(valid_mask)
    N = g.N
    idx = g.idx
    cells = g.cells
    board = [0] * N
    for p in me:
        i = idx.get((int(p[0]), int(p[1])))
        if i is not None:
            board[i] = 1
    for p in opp:
        i = idx.get((int(p[0]), int(p[1])))
        if i is not None:
            board[i] = 2
    empties = [i for i in range(N) if board[i] == 0]
    if not empties:
        raise RuntimeError("no empty")
    if len(me) == 0 and len(opp) == 0 and board[g.center] == 0:
        return cells[g.center]

    ufm = build_uf(g, board, 1)
    for w in empties:
        if wins_at(g, board, 1, w, ufm):
            return cells[w]
    ufo = build_uf(g, board, 2)
    opp_wins = [w for w in empties if wins_at(g, board, 2, w, ufo)]
    if len(opp_wins) == 1:
        return cells[opp_wins[0]]

    cands = None
    if len(opp_wins) >= 2:
        cands = opp_wins
    else:
        t_tac = t0 + 0.30
        for m in near(g, board, 1):
            if time.time() > t_tac:
                break
            if len(wins_after(g, board, 1, m)) >= 2:
                return cells[m]
        dset = []
        t_tac2 = t0 + 0.45
        for o in near(g, board, 2):
            if time.time() > t_tac2:
                break
            if len(wins_after(g, board, 2, o)) >= 2:
                dset.append(o)
        if len(dset) == 1:
            return cells[dset[0]]
        if dset:
            cands = dset

    bnp = np.array(board, dtype=np.int64)
    pre = g.prescore(bnp)
    centr = g.centr

    def key(i):
        return -(pre[i] + CW * centr[i])

    if cands is None:
        cands = sorted(empties, key=key)[:K1]
    else:
        cands = sorted(cands, key=key)[:K1]

    results = []
    t_1ply = t0 + 0.62
    for m in cands:
        if results and time.time() > t_1ply:
            break
        bnp[m] = 1
        sm, Dm, cm = g.side_score(bnp, 1)
        so, Do, co = g.side_score(bnp, 2)
        v = sm - MU * so + CW * centr[m]
        bnp[m] = 0
        results.append((v, m, Dm, Do))
    if not results:
        return cells[cands[0]]
    results.sort(key=lambda x: -x[0])
    best_m = results[0][1]

    t_2ply = t0 + 0.86
    final = []
    if len(results) > 1:
        for (v, m, Dm, Do) in results[:T1]:
            if time.time() > t_2ply:
                break
            bnp[m] = 1
            rv = g.via_values(bnp, 1, Dm) + g.via_values(bnp, 2, Do)
            reps = [i for i in range(N) if bnp[i] == 0]
            reps.sort(key=lambda i: -(rv[i] + CW * centr[i]))
            reps = reps[:T2]
            worst = None
            complete = True
            for o in reps:
                if time.time() > t_2ply:
                    complete = False
                    break
                bnp[o] = 2
                sm2, _, _ = g.side_score(bnp, 1)
                so2, _, _ = g.side_score(bnp, 2)
                v2 = MU * sm2 - so2 + CW * centr[m]
                bnp[o] = 0
                if worst is None or v2 < worst:
                    worst = v2
            bnp[m] = 0
            if complete and worst is not None:
                final.append((worst, m))
    if len(final) >= 2:
        final.sort(key=lambda x: -x[0])
        best_m = final[0][1]
    return cells[best_m]


def policy(me, opp, valid_mask):
    try:
        r, c = _policy(me, opp, valid_mask)
        return (int(r), int(c))
    except Exception:
        V = np.asarray(valid_mask, dtype=bool)
        occ = set((int(p[0]), int(p[1])) for p in list(me) + list(opp))
        R, C = V.shape
        best = None
        bd = None
        for r in range(R):
            for c in range(C):
                if V[r, c] and (r, c) not in occ:
                    d = abs(r - (R - 1) / 2) + abs(c - (C - 1) / 2)
                    if bd is None or d < bd:
                        bd = d
                        best = (r, c)
        if best is None:
            return (0, 0)
        return (int(best[0]), int(best[1]))
