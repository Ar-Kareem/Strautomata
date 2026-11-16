
from collections import deque

# ---------- geometry cache (per board size) ----------
_GEO = {}

def _build(N, valid_mask):
    valid = [[bool(valid_mask[r][c]) for c in range(N)] for r in range(N)]
    idx = [[r * N + c for c in range(N)] for r in range(N)]
    coord = [(r, c) for r in range(N) for c in range(N)]

    DIRS = ((-1, 0), (1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1))
    total = N * N
    neigh = [[] for _ in range(total)]
    deg = [0] * total
    boundary = [False] * total
    for r in range(N):
        for c in range(N):
            i = idx[r][c]
            if not valid[r][c]:
                continue
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and valid[nr][nc]:
                    neigh[i].append(idx[nr][nc])
            deg[i] = len(neigh[i])
            boundary[i] = deg[i] < 6

    # side length for hex inscribed in N x N (N odd) -> classic Havannah base (N+1)/2
    s = (N + 1) // 2
    mid = s - 1
    corner_coords = [(0, 0), (0, mid), (mid, N - 1),
                     (N - 1, N - 1), (N - 1, mid), (mid, 0)]
    corner_of = [-1] * total
    cset = set()
    for k, (r, c) in enumerate(corner_coords):
        if 0 <= r < N and 0 <= c < N and valid[r][c]:
            corner_of[idx[r][c]] = k
            cset.add(idx[r][c])

    # side bits for non-corner edge cells (6 sides, clockwise); corners count as 0
    snc = [0] * total    # fork-relevant edge bits (non-corner only)
    for r in range(N):
        for c in range(N):
            i = idx[r][c]
            if not valid[r][c] or corner_of[i] >= 0:
                continue
            b = 0
            if r == 0: b |= 1 << 0                 # top
            if r == N - 1: b |= 1 << 3             # bottom
            if r <= mid and c == 0: b |= 1 << 5    # upper-left
            if r >= mid and c == r - mid: b |= 1 << 4   # lower-left
            if r <= mid and c == r + mid: b |= 1 << 1   # upper-right
            if r >= mid and c == N - 1: b |= 1 << 2     # lower-right
            snc[i] = b

    def pc(x):
        return bin(x).count('1')

    return dict(N=N, valid=valid, idx=idx, coord=coord, neigh=neigh, deg=deg,
                boundary=boundary, snc=snc, corner_of=corner_of,
                corner_coords=corner_coords, cset=cset, pc=pc, total=total)

def _geo(N, valid_mask):
    key = N
    if key not in _GEO:
        _GEO[key] = _build(N, valid_mask)
    return _GEO[key]

def policy(me, opp, valid_mask):
    N = len(valid_mask)
    G = _geo(N, valid_mask)
    valid, idx, coord = G['valid'], G['idx'], G['coord']
    neigh, deg, boundary = G['neigh'], G['deg'], G['boundary']
    snc, corner_of, pc = G['snc'], G['corner_of'], G['pc']

    M = set(idx[r][c] for r, c in me if valid[r][c])
    O = set(idx[r][c] for r, c in opp if valid[r][c])
    empties = [i for i in range(G['total']) if valid[coord[i][0]][coord[i][1]] and i not in M and i not in O]
    if not empties:
        # fallback (game already over) - return any valid cell
        for i in range(G['total']):
            r, c = coord[i]
            if valid[r][c]:
                return (r, c)
        return (0, 0)

    # ---------- exact win test for a stone set P ----------
    def components(P):
        parent = {i: i for i in P}
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
        for i in P:
            for j in neigh[i]:
                if j in P:
                    union(i, j)
        agg = {}
        for i in P:
            r = find(i)
            d = agg.setdefault(r, [0, 0, 0])  # snc_or, cornerbits, size
            d[0] |= snc[i]
            cb = corner_of[i]
            if cb >= 0:
                d[1] |= 1 << cb
            d[2] += 1
        return agg, find

    def wins(P):
        if not P:
            return False
        agg, _ = components(P)
        for (sor, cor, sz) in agg.values():
            if pc(cor) >= 2:      # bridge: two corners in one component
                return True
            if pc(sor) >= 3:      # fork: three edges (corners excluded)
                return True
        # ring: some cell not in P is cut off from the border by P
        visited = bytearray(G['total'])
        dq = deque()
        for i in range(G['total']):
            r, c = coord[i]
            if valid[r][c] and boundary[i] and i not in P and not visited[i]:
                visited[i] = 1
                dq.append(i)
        while dq:
            i = dq.popleft()
            for j in neigh[i]:
                if not visited[j] and j not in P:
                    visited[j] = 1
                    dq.append(j)
        for i in range(G['total']):
            r, c = coord[i]
            if valid[r][c] and i not in P and not visited[i]:
                return True   # enclosed region -> P ring
        return False

    def near(P):  # one-move win can only be on an empty cell adjacent to P
        out = set()
        for i in P:
            for j in neigh[i]:
                if valid[coord[j][0]][coord[j][1]] and j not in M and j not in O:
                    out.add(j)
        return list(out)

    # 1) immediate win
    cand_self = near(M) if M else []
    for e in cand_self:
        if wins(M | {e}):
            r, c = coord[e]
            return (r, c)

    # 2) opponent immediate wins -> must block
    threats = []
    cand_opp = near(O) if O else []
    for e in cand_opp:
        if wins(O | {e}):
            threats.append(e)
    pool = threats if threats else empties

    # ---------- heuristic connectivity value ----------
    def comp_value(sor, cor, sz):
        rs, rc = pc(sor), pc(cor)
        v = sz * 2.0 + rs * 22.0 + rc * 30.0
        if rs >= 2:
            v += 35.0
        if rs >= 3:
            v += 400.0
        if rc >= 2:
            v += 500.0
        if rs == 1 and rc >= 1:
            v += 10.0
        return v

    def prep(P):
        if not P:
            return {}, None
        agg, find = components(P)
        vals = {}
        for r, (sor, cor, sz) in agg.items():
            vals[r] = (sor, cor, sz, comp_value(sor, cor, sz))
        return vals, find

    Mvals, Mfind = prep(M)
    Ovals, Ofind = prep(O)

    def gain(P, vals, findf, e):
        # value added if player P places on empty cell e
        roots = set()
        for j in neigh[e]:
            if j in P:
                roots.add(findf(j))
        sor = snc[e]
        cb = corner_of[e]
        cor = (1 << cb) if cb >= 0 else 0
        sz = 1
        old = 0.0
        for r in roots:
            s0, c0, z0, v0 = vals[r]
            sor |= s0
            cor |= c0
            sz += z0
            old += v0
        return comp_value(sor, cor, sz) - old

    best = pool[0]
    bestsc = -1e18
    for e in pool:
        g_self = gain(M, Mvals, Mfind, e)
        g_opp = gain(O, Ovals, Ofind, e)          # value we deny the opponent
        sc = g_self + 0.95 * g_opp + 0.5 * deg[e]  # small centrality bias
        if sc > bestsc:
            bestsc = sc
            best = e
    r, c = coord[best]
    return (r, c)
