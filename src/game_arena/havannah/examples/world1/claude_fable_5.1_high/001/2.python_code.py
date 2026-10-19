
import math
import time

INF = float('inf')
WIN = 1e6
CAP = 60
K1 = 18
T2 = 4
R2 = 7
TIME_BUDGET = 0.6


class _Topo(object):
    pass


_TOPO = None
_TOPO_KEY = None


def _nbr_fns():
    def off_odd_col(r, c):
        if c & 1:
            return [(r - 1, c), (r - 1, c + 1), (r, c + 1), (r + 1, c), (r, c - 1), (r - 1, c - 1)]
        return [(r - 1, c), (r, c + 1), (r + 1, c + 1), (r + 1, c), (r + 1, c - 1), (r, c - 1)]

    def off_even_col(r, c):
        if not (c & 1):
            return [(r - 1, c), (r - 1, c + 1), (r, c + 1), (r + 1, c), (r, c - 1), (r - 1, c - 1)]
        return [(r - 1, c), (r, c + 1), (r + 1, c + 1), (r + 1, c), (r + 1, c - 1), (r, c - 1)]

    def axial_a(r, c):
        return [(r, c + 1), (r - 1, c + 1), (r - 1, c), (r, c - 1), (r + 1, c - 1), (r + 1, c)]

    def axial_b(r, c):
        return [(r, c + 1), (r + 1, c + 1), (r + 1, c), (r, c - 1), (r - 1, c - 1), (r - 1, c)]

    def off_odd_row(r, c):
        if r & 1:
            return [(r, c + 1), (r - 1, c), (r - 1, c - 1), (r, c - 1), (r + 1, c - 1), (r + 1, c)]
        return [(r, c + 1), (r - 1, c + 1), (r - 1, c), (r, c - 1), (r + 1, c), (r + 1, c + 1)]

    def off_even_row(r, c):
        if not (r & 1):
            return [(r, c + 1), (r - 1, c), (r - 1, c - 1), (r, c - 1), (r + 1, c - 1), (r + 1, c)]
        return [(r, c + 1), (r - 1, c + 1), (r - 1, c), (r, c - 1), (r + 1, c), (r + 1, c + 1)]

    return [off_odd_col, off_even_col, axial_a, axial_b, off_odd_row, off_even_row]


def _get_topo(valid_mask):
    global _TOPO, _TOPO_KEY
    rows = len(valid_mask)
    cols = len(valid_mask[0])
    cells = []
    for r in range(rows):
        row = valid_mask[r]
        for c in range(cols):
            if row[c]:
                cells.append((r, c))
    key = (rows, cols, tuple(cells))
    if _TOPO is not None and _TOPO_KEY == key:
        return _TOPO
    M = len(cells)
    idx = {}
    for i, cell in enumerate(cells):
        idx[cell] = i
    n = None
    for k in range(1, 60):
        if 3 * k * k - 3 * k + 1 == M:
            n = k
    fns = _nbr_fns()
    chosen = None
    first_sym = None
    for fn in fns:
        nb = [[idx.get(p, -1) for p in fn(r, c)] for (r, c) in cells]
        sym = True
        for i, lst in enumerate(nb):
            for j in lst:
                if j >= 0 and i not in nb[j]:
                    sym = False
                    break
            if not sym:
                break
        if not sym:
            continue
        if first_sym is None:
            first_sym = nb
        if n is not None:
            deg = [6 - lst.count(-1) for lst in nb]
            if deg.count(3) == 6 and deg.count(4) == 6 * (n - 2) and deg.count(6) == M - 6 - 6 * (n - 2):
                chosen = nb
                break
    if chosen is None:
        if first_sym is not None:
            chosen = first_sym
        else:
            chosen = [[idx.get(p, -1) for p in fns[0](r, c)] for (r, c) in cells]
    nv = [[j for j in lst if j >= 0] for lst in chosen]
    deg = [len(l) for l in nv]
    mind = min(deg) if M > 0 else 0
    corners = [i for i in range(M) if deg[i] == mind][:6]
    cornerset = set(corners)
    edge_set = set(i for i in range(M) if deg[i] < 6 and i not in cornerset)
    side_of = {}
    sides = []
    for i in sorted(edge_set):
        if i in side_of:
            continue
        sid = len(sides)
        comp = []
        stack = [i]
        side_of[i] = sid
        while stack:
            u = stack.pop()
            comp.append(u)
            for v in nv[u]:
                if v in edge_set and v not in side_of:
                    side_of[v] = sid
                    stack.append(v)
        sides.append(comp)
    cell_edge = [0] * M
    cell_corner = [0] * M
    for i, s in side_of.items():
        cell_edge[i] = 1 << s
    for k, c in enumerate(corners):
        cell_corner[c] = 1 << k
    # depth from border
    depth = [-1] * M
    frontier = [i for i in range(M) if deg[i] < 6]
    for i in frontier:
        depth[i] = 0
    d = 0
    while frontier:
        nxt = []
        for u in frontier:
            for v in nv[u]:
                if depth[v] < 0:
                    depth[v] = d + 1
                    nxt.append(v)
        frontier = nxt
        d += 1
    for i in range(M):
        if depth[i] < 0:
            depth[i] = 0
    T = _Topo()
    T.M = M
    T.cells = cells
    T.idx = idx
    T.nbrs = chosen
    T.nv = nv
    T.sides = sides
    T.corners = corners
    T.cell_edge = cell_edge
    T.cell_corner = cell_corner
    T.depth = depth
    _TOPO = T
    _TOPO_KEY = key
    return T


def _popcount(x):
    return bin(x).count('1')


def _analyze(T, board, P):
    M = T.M
    nv = T.nv
    ce = T.cell_edge
    cc = T.cell_corner
    lab = [-1] * M
    ge = []
    gc = []
    ga = []
    for i in range(M):
        if board[i] == P and lab[i] < 0:
            gid = len(ge)
            lab[i] = gid
            stack = [i]
            em = 0
            cm = 0
            adj = set()
            while stack:
                u = stack.pop()
                em |= ce[u]
                cm |= cc[u]
                for v in nv[u]:
                    b = board[v]
                    if b == P:
                        if lab[v] < 0:
                            lab[v] = gid
                            stack.append(v)
                    elif b == 0:
                        adj.add(v)
            ge.append(em)
            gc.append(cm)
            ga.append(list(adj))
    return lab, ge, gc, ga


def _wins_at(T, board, P, x, lab, ge, gc):
    em = T.cell_edge[x]
    cm = T.cell_corner[x]
    ns = T.nbrs[x]
    own = [0] * 6
    seen = set()
    total = 0
    for k in range(6):
        nn = ns[k]
        if nn >= 0 and board[nn] == P:
            own[k] = 1
            total += 1
            g = lab[nn]
            if g not in seen:
                seen.add(g)
                em |= ge[g]
                cm |= gc[g]
    if _popcount(em) >= 3 or _popcount(cm) >= 2:
        return True
    if total >= 2:
        if total == 6:
            return True
        start = own.index(0)
        arcs = []
        prev = 0
        for k in range(1, 7):
            i = (start + k) % 6
            if own[i]:
                if not prev:
                    arcs.append(lab[ns[i]])
                prev = 1
            else:
                prev = 0
        if len(arcs) >= 2 and len(arcs) != len(set(arcs)):
            return True
    nv = T.nv
    for nn in nv[x]:
        if board[nn] == P and len(nv[nn]) == 6:
            full = True
            for m in nv[nn]:
                if m != x and board[m] != P:
                    full = False
                    break
            if full:
                return True
    return False


def _two_dist(nadj, M, num_nodes, seeds):
    d = [INF] * num_nodes
    cnt = [0] * num_nodes
    done = [False] * num_nodes
    buckets = [[] for _ in range(CAP + 2)]
    for node, d0 in seeds:
        if d0 < d[node]:
            d[node] = d0
            buckets[d0].append(node)
    for dv in range(CAP + 1):
        bk = buckets[dv]
        k = 0
        while k < len(bk):
            u = bk[k]
            k += 1
            if done[u] or d[u] != dv:
                continue
            done[u] = True
            for v in nadj[u]:
                if done[v]:
                    continue
                cnt[v] += 1
                if cnt[v] == 2:
                    nd = dv + (1 if v < M else 0)
                    if nd < d[v]:
                        d[v] = nd
                        if nd <= CAP:
                            buckets[nd].append(v)
    return d


def _fields(T, board, P, lab, ga):
    M = T.M
    nv = T.nv
    ng = len(ga)
    num_nodes = M + ng
    nadj = [None] * num_nodes
    for u in range(M):
        if board[u] == 0:
            lst = []
            seen = None
            for w in nv[u]:
                b = board[w]
                if b == 0:
                    lst.append(w)
                elif b == P:
                    v = M + lab[w]
                    if seen is None:
                        seen = set()
                        seen.add(v)
                        lst.append(v)
                    elif v not in seen:
                        seen.add(v)
                        lst.append(v)
            nadj[u] = lst
        else:
            nadj[u] = []
    for g in range(ng):
        nadj[M + g] = ga[g]
    res = []
    for side in T.sides:
        seeds = []
        for s in side:
            b = board[s]
            if b == P:
                seeds.append((M + lab[s], 0))
            elif b == 0:
                seeds.append((s, 1))
        res.append(_two_dist(nadj, M, num_nodes, seeds))
    opp = 3 - P
    for c in T.corners:
        seeds = []
        b = board[c]
        if b != opp:
            if b == P:
                nc = M + lab[c]
                dc = 0
            else:
                nc = c
                dc = 1
            seeds.append((nc, dc))
            for v in nv[c]:
                bv = board[v]
                if bv == P:
                    seeds.append((M + lab[v], dc))
                elif bv == 0:
                    seeds.append((v, dc + 1))
        res.append(_two_dist(nadj, M, num_nodes, seeds))
    return res


def _hub(T, board, ng, D):
    M = T.M
    num_nodes = M + ng
    ne = len(T.sides)
    edgeD = D[:ne]
    cornD = D[ne:]
    mincost = INF
    pot = 0.0
    hub = [INF] * M
    for node in range(num_nodes):
        if node < M:
            if board[node] != 0:
                continue
            adjf = 2
            adjb = 1
        else:
            adjf = 0
            adjb = 0
        e = sorted([dd[node] for dd in edgeD])
        if len(e) >= 3:
            f = e[0] + e[1] + e[2] - adjf
        else:
            f = INF
        c = sorted([dd[node] for dd in cornD])
        if len(c) >= 2:
            bcost = c[0] + c[1] - adjb
        else:
            bcost = INF
        cost = f if f < bcost else bcost
        if cost < INF:
            if cost < mincost:
                mincost = cost
            pot += 2.0 ** (-cost)
        if node < M:
            hub[node] = cost
    if mincost == INF:
        mincost = 60.0
    return mincost, pot, hub


def _evaluate(T, board, to_move):
    M = T.M
    lab1, ge1, gc1, ga1 = _analyze(T, board, 1)
    lab2, ge2, gc2, ga2 = _analyze(T, board, 2)
    empties = [i for i in range(M) if board[i] == 0]
    w1 = [x for x in empties if _wins_at(T, board, 1, x, lab1, ge1, gc1)]
    w2 = [x for x in empties if _wins_at(T, board, 2, x, lab2, ge2, gc2)]
    if to_move == 1:
        if w1:
            return WIN, w1
        if len(w2) >= 2:
            return -WIN, w2
    else:
        if w2:
            return -WIN, w2
        if len(w1) >= 2:
            return WIN, w1
    D1 = _fields(T, board, 1, lab1, ga1)
    D2 = _fields(T, board, 2, lab2, ga2)
    m1, p1, hub1 = _hub(T, board, len(ga1), D1)
    m2, p2, hub2 = _hub(T, board, len(ga2), D2)
    score = (m2 - m1) + 0.5 * (math.log(p1 + 1e-12, 2) - math.log(p2 + 1e-12, 2))
    if len(w1) == 1:
        score += 0.4
    if len(w2) == 1:
        score -= 0.4
    if to_move == 1 and len(w2) == 1:
        cands = list(w2)
    elif to_move == 2 and len(w1) == 1:
        cands = list(w1)
    else:
        own_hub = hub1 if to_move == 1 else hub2
        oth_hub = hub2 if to_move == 1 else hub1
        depth = T.depth
        scored = []
        for x in empties:
            a = own_hub[x]
            b = oth_hub[x]
            if a > 90:
                a = 90
            if b > 90:
                b = 90
            scored.append((-a - 1.0 * b + 0.05 * depth[x], x))
        scored.sort(reverse=True)
        cands = [x for _, x in scored]
    return score, cands


def _policy(me, opp, valid_mask, t0):
    T = _get_topo(valid_mask)
    M = T.M
    board = [0] * M
    for p in me:
        i = T.idx.get((int(p[0]), int(p[1])))
        if i is not None:
            board[i] = 1
    for p in opp:
        i = T.idx.get((int(p[0]), int(p[1])))
        if i is not None:
            board[i] = 2
    empties = [i for i in range(M) if board[i] == 0]
    if not empties:
        raise ValueError("no moves")
    if len(empties) == M:
        best = max(empties, key=lambda i: T.depth[i])
        return T.cells[best]
    lab1, ge1, gc1, ga1 = _analyze(T, board, 1)
    lab2, ge2, gc2, ga2 = _analyze(T, board, 2)
    w1 = [x for x in empties if _wins_at(T, board, 1, x, lab1, ge1, gc1)]
    if w1:
        return T.cells[w1[0]]
    w2 = [x for x in empties if _wins_at(T, board, 2, x, lab2, ge2, gc2)]
    if len(w2) == 1:
        return T.cells[w2[0]]
    deadline = t0 + TIME_BUDGET
    if len(w2) >= 2:
        root_cands = list(w2)
    else:
        _, cands0 = _evaluate(T, board, 1)
        root_cands = cands0[:K1]
    if not root_cands:
        return T.cells[max(empties, key=lambda i: T.depth[i])]
    results = []
    for x in root_cands:
        board[x] = 1
        s, oc = _evaluate(T, board, 2)
        board[x] = 0
        results.append((s, x, oc))
        if s >= WIN:
            break
        if time.time() > deadline:
            break
    results.sort(key=lambda t: -t[0])
    if results[0][0] >= WIN or len(results) == 1:
        return T.cells[results[0][1]]
    final = []
    for (s, x, oc) in results[:T2]:
        if s <= -WIN:
            break
        if time.time() > deadline:
            break
        board[x] = 1
        worst = WIN * 2
        completed = True
        for y in oc[:R2]:
            board[y] = 2
            s2, _ = _evaluate(T, board, 1)
            board[y] = 0
            if s2 < worst:
                worst = s2
            if worst <= -WIN:
                break
            if time.time() > deadline:
                completed = False
                break
        board[x] = 0
        if completed or not final:
            final.append((worst, s, x))
        if not completed:
            break
    if final:
        final.sort(key=lambda t: (-t[0], -t[1]))
        return T.cells[final[0][2]]
    return T.cells[results[0][1]]


def policy(me, opp, valid_mask):
    t0 = time.time()
    try:
        r, c = _policy(me, opp, valid_mask, t0)
        r = int(r)
        c = int(c)
        occ = set((int(p[0]), int(p[1])) for p in me) | set((int(p[0]), int(p[1])) for p in opp)
        if valid_mask[r][c] and (r, c) not in occ:
            return (r, c)
    except Exception:
        pass
    occ = set((int(p[0]), int(p[1])) for p in me) | set((int(p[0]), int(p[1])) for p in opp)
    rows = len(valid_mask)
    cols = len(valid_mask[0])
    best = None
    bd = 1e18
    for r in range(rows):
        for c in range(cols):
            if valid_mask[r][c] and (r, c) not in occ:
                d = (r - (rows - 1) / 2.0) ** 2 + (c - (cols - 1) / 2.0) ** 2
                if d < bd:
                    bd = d
                    best = (r, c)
    return best
