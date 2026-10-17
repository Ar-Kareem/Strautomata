
import numpy as np
from collections import deque
import time

INF = 10 ** 9
_GEO_CACHE = {}
K_CANDS = 12


class _Geo:
    pass


def _scheme_fns():
    def off_odd_up(r, c):
        d = -1 if (c % 2) else 1
        return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1), (r + d, c - 1), (r + d, c + 1))

    def off_even_up(r, c):
        d = 1 if (c % 2) else -1
        return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1), (r + d, c - 1), (r + d, c + 1))

    def axial_a(r, c):
        return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1), (r - 1, c - 1), (r + 1, c + 1))

    def axial_b(r, c):
        return ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1), (r - 1, c + 1), (r + 1, c - 1))

    def roff_odd_left(r, c):
        d = -1 if (r % 2) else 1
        return ((r, c - 1), (r, c + 1), (r - 1, c), (r + 1, c), (r - 1, c + d), (r + 1, c + d))

    def roff_even_left(r, c):
        d = 1 if (r % 2) else -1
        return ((r, c - 1), (r, c + 1), (r - 1, c), (r + 1, c), (r - 1, c + d), (r + 1, c + d))

    return [off_odd_up, off_even_up, axial_a, axial_b, roff_odd_left, roff_even_left]


def _build_nbrs(cells, idx, fn):
    nbrs = []
    for (r, c) in cells:
        lst = []
        for rc in fn(r, c):
            j = idx.get(rc)
            if j is not None:
                lst.append(j)
        nbrs.append(lst)
    return nbrs


def _validate(nbrs):
    M = len(nbrs)
    if M < 7:
        return None
    for i in range(M):
        for j in nbrs[i]:
            if i not in nbrs[j]:
                return None
    deg = [len(n) for n in nbrs]
    for d in deg:
        if d not in (3, 4, 6):
            return None
    corners = [i for i in range(M) if deg[i] == 3]
    if len(corners) != 6:
        return None
    seen = [False] * M
    seen[0] = True
    st = [0]
    cnt = 1
    while st:
        u = st.pop()
        for v in nbrs[u]:
            if not seen[v]:
                seen[v] = True
                cnt += 1
                st.append(v)
    if cnt != M:
        return None
    edge_id = [-1] * M
    ne = 0
    for i in range(M):
        if deg[i] == 4 and edge_id[i] < 0:
            edge_id[i] = ne
            st = [i]
            while st:
                u = st.pop()
                for v in nbrs[u]:
                    if deg[v] == 4 and edge_id[v] < 0:
                        edge_id[v] = ne
                        st.append(v)
            ne += 1
    if ne != 6:
        return None
    return corners, edge_id, ne


def _fallback_geo(nbrs):
    M = len(nbrs)
    sets = [set(n) for n in nbrs]
    for i in range(M):
        for j in list(sets[i]):
            sets[j].add(i)
    nbrs = [sorted(s) for s in sets]
    deg = [len(n) for n in nbrs]
    order = sorted(range(M), key=lambda i: (deg[i], i))
    corners = [i for i in order if deg[i] < 6][:6]
    cset = set(corners)
    edge_id = [-1] * M
    ne = 0
    for i in range(M):
        if deg[i] < 6 and i not in cset and edge_id[i] < 0:
            edge_id[i] = ne
            st = [i]
            while st:
                u = st.pop()
                for v in nbrs[u]:
                    if deg[v] < 6 and v not in cset and edge_id[v] < 0:
                        edge_id[v] = ne
                        st.append(v)
            ne += 1
    return nbrs, corners, edge_id, ne


def _make_geo(valid_mask):
    vm = np.asarray(valid_mask).astype(bool)
    rows, cols = vm.shape
    cells = [(r, c) for r in range(rows) for c in range(cols) if vm[r, c]]
    idx = {rc: i for i, rc in enumerate(cells)}
    M = len(cells)
    chosen = None
    for fn in _scheme_fns():
        nbrs = _build_nbrs(cells, idx, fn)
        res = _validate(nbrs)
        if res is not None:
            chosen = (nbrs, res[0], res[1], res[2])
            break
    if chosen is None:
        nbrs = _build_nbrs(cells, idx, _scheme_fns()[0])
        chosen = _fallback_geo(nbrs)
    nbrs, corners, edge_id, ne = chosen
    g = _Geo()
    g.M = M
    g.cells = cells
    g.idx = idx
    g.nbrs = nbrs
    g.corners = corners
    g.is_corner = [False] * M
    for k in corners:
        g.is_corner[k] = True
    g.edge_id = edge_id
    g.n_edges = ne
    g.edge_cells = [[] for _ in range(ne)]
    for i in range(M):
        if edge_id[i] >= 0:
            g.edge_cells[edge_id[i]].append(i)
    g.edge_near = [[] for _ in range(ne)]
    for i in range(M):
        cnts = {}
        for v in nbrs[i]:
            e = edge_id[v]
            if e >= 0 and e != edge_id[i]:
                cnts[e] = cnts.get(e, 0) + 1
        for e, k in cnts.items():
            if k >= 2:
                g.edge_near[e].append(i)
    nsets = [set(n) for n in nbrs]
    tb = [[] for _ in range(M)]
    for u in range(M):
        nu = nbrs[u]
        for ai in range(len(nu)):
            a = nu[ai]
            for bi in range(ai + 1, len(nu)):
                b = nu[bi]
                if b in nsets[a]:
                    for w in nsets[a] & nsets[b]:
                        if w != u and w not in nsets[u]:
                            tb[u].append((w, a, b))
    g.tb = tb
    g.border = [i for i in range(M) if len(nbrs[i]) < 6]
    depth = [-1] * M
    dq = deque()
    for b in g.border:
        depth[b] = 0
        dq.append(b)
    while dq:
        u = dq.popleft()
        for v in nbrs[u]:
            if depth[v] < 0:
                depth[v] = depth[u] + 1
                dq.append(v)
    g.depth = [d if d >= 0 else 0 for d in depth]
    return g


def _get_geo(valid_mask):
    vm = np.asarray(valid_mask).astype(bool)
    key = (vm.shape, vm.tobytes())
    g = _GEO_CACHE.get(key)
    if g is None:
        g = _make_geo(vm)
        _GEO_CACHE[key] = g
    return g


def _components(state, P, g):
    M = g.M
    nbrs = g.nbrs
    edge_id = g.edge_id
    is_corner = g.is_corner
    cid = [-1] * M
    comps = []
    for i in range(M):
        if state[i] == P and cid[i] < 0:
            k = len(comps)
            cid[i] = k
            st = [i]
            members = []
            edges = set()
            corners = 0
            while st:
                u = st.pop()
                members.append(u)
                e = edge_id[u]
                if e >= 0:
                    edges.add(e)
                if is_corner[u]:
                    corners += 1
                for v in nbrs[u]:
                    if state[v] == P and cid[v] < 0:
                        cid[v] = k
                        st.append(v)
            comps.append((members, edges, corners))
    return cid, comps


def _wins(state, P, x, cid, comps, g):
    nbrs = g.nbrs
    edges = set()
    corners = 0
    pn = 0
    cids = []
    e = g.edge_id[x]
    if e >= 0:
        edges.add(e)
    if g.is_corner[x]:
        corners = 1
    for v in nbrs[x]:
        if state[v] == P:
            pn += 1
            k = cid[v]
            if k not in cids:
                cids.append(k)
                edges |= comps[k][1]
                corners += comps[k][2]
    if len(edges) >= 3 or corners >= 2:
        return True
    if pn < 2:
        return False
    M = g.M
    inG = bytearray(M)
    inG[x] = 1
    gsize = 1
    for k in cids:
        mem = comps[k][0]
        for u in mem:
            inG[u] = 1
        gsize += len(mem)
    for y in (x,) + tuple(nbrs[x]):
        nb = nbrs[y]
        if len(nb) == 6:
            ok = True
            for z in nb:
                if not inG[z]:
                    ok = False
                    break
            if ok:
                return True
    vis = bytearray(M)
    cnt = 0
    st = []
    for b in g.border:
        if not inG[b] and not vis[b]:
            vis[b] = 1
            cnt += 1
            st.append(b)
    while st:
        u = st.pop()
        for v in nbrs[u]:
            if not vis[v] and not inG[v]:
                vis[v] = 1
                cnt += 1
                st.append(v)
    return cnt < M - gsize


def _win_cells_after(state, P, x, g):
    cid, comps = _components(state, P, g)
    c0 = cid[x]
    libs = set()
    nbrs = g.nbrs
    for u in comps[c0][0]:
        for v in nbrs[u]:
            if state[v] == 0:
                libs.add(v)
    return [y for y in libs if _wins(state, P, y, cid, comps, g)]


def _bfs(src, c, nbrs, tb, state, M):
    dist = [INF] * M
    dq = deque()
    for s, cs in src:
        if cs < dist[s]:
            dist[s] = cs
            if cs:
                dq.append(s)
            else:
                dq.appendleft(s)
    pop = dq.popleft
    push = dq.append
    pushl = dq.appendleft
    while dq:
        u = pop()
        du = dist[u]
        for v in nbrs[u]:
            cv = c[v]
            nd = du + cv
            if nd < dist[v]:
                dist[v] = nd
                if cv:
                    push(v)
                else:
                    pushl(v)
        for w, a, b in tb[u]:
            if not state[a] and not state[b]:
                cw = c[w]
                nd = du + cw
                if nd < dist[w]:
                    dist[w] = nd
                    if cw:
                        push(w)
                    else:
                        pushl(w)
    return dist


def _potential(state, P, g):
    M = g.M
    nbrs = g.nbrs
    tb = g.tb
    edge_id = g.edge_id
    c = [0 if s == P else (1 if s == 0 else INF) for s in state]
    edists = []
    for e in range(g.n_edges):
        src = [(i, c[i]) for i in g.edge_cells[e] if c[i] < INF]
        for i in g.edge_near[e]:
            if c[i] < INF:
                k = 0
                for v in nbrs[i]:
                    if edge_id[v] == e and state[v] == 0:
                        k += 1
                if k >= 2:
                    src.append((i, c[i]))
        edists.append(_bfs(src, c, nbrs, tb, state, M))
    cdists = []
    for k in g.corners:
        src = [(k, c[k])] if c[k] < INF else []
        cdists.append(_bfs(src, c, nbrs, tb, state, M))
    cost = [float(INF)] * M
    m = float(INF)
    ne = len(edists)
    nc = len(cdists)
    for i in range(M):
        ci = c[i]
        if ci >= INF:
            continue
        if ne >= 3:
            ed = sorted(d[i] for d in edists)
            fork = ed[0] + ed[1] + ed[2] - 2 * ci
        else:
            fork = INF
        if nc >= 2:
            cd = sorted(d[i] for d in cdists)
            br = cd[0] + cd[1] - ci
            if br >= INF:
                bridge = float(INF)
            else:
                bridge = br + 0.35 * br * br
        else:
            bridge = float(INF)
        v = fork if fork < bridge else bridge
        cost[i] = v
        if v < m:
            m = v
    cnt_m = 0
    cnt_m1 = 0
    for i in range(M):
        v = cost[i]
        if v <= m + 0.01:
            cnt_m += 1
        elif v <= m + 1.01:
            cnt_m1 += 1
    return m, cnt_m, cnt_m1, cost


def _f(m, cm, cm1):
    if m > 1e8:
        m = 60.0
    return m - 0.1 * min(cm, 5) - 0.02 * min(cm1, 10)


def _opp_double_threats(state, g, my_wc, deadline, costO, limit, find_all):
    nbrs = g.nbrs
    near = set()
    for s in range(g.M):
        if state[s] == 2:
            for v in nbrs[s]:
                if state[v] == 0:
                    near.add(v)
                    for w in nbrs[v]:
                        if state[w] == 0:
                            near.add(w)
    if my_wc:
        near &= set(my_wc)
    order = sorted(near, key=lambda y: costO[y])[:limit]
    found = []
    for y in order:
        if time.time() > deadline:
            break
        state[y] = 2
        wc = _win_cells_after(state, 2, y, g)
        state[y] = 0
        if len(wc) >= 2:
            found.append(y)
            if not find_all:
                break
    return found


def _policy(me, opp, valid_mask, t0):
    g = _get_geo(valid_mask)
    M = g.M
    state = [0] * M
    for r, c in me:
        i = g.idx.get((int(r), int(c)))
        if i is not None:
            state[i] = 1
    for r, c in opp:
        i = g.idx.get((int(r), int(c)))
        if i is not None and state[i] == 0:
            state[i] = 2
    empties = [i for i in range(M) if state[i] == 0]
    if not empties:
        return None
    cid1, comps1 = _components(state, 1, g)
    for x in empties:
        if _wins(state, 1, x, cid1, comps1, g):
            return g.cells[x]
    cid2, comps2 = _components(state, 2, g)
    oppwins = [x for x in empties if _wins(state, 2, x, cid2, comps2, g)]
    if len(oppwins) == 1:
        return g.cells[oppwins[0]]
    mM, cm, cm1, costM = _potential(state, 1, g)
    mO, co, co1, costO = _potential(state, 2, g)
    depth = g.depth
    if oppwins:
        cands = list(oppwins)
    else:
        def pre(x):
            return (costM[x] - mM) + (costO[x] - mO) - 0.01 * depth[x]
        order = sorted(empties, key=pre)
        cands = order[:K_CANDS]
        if time.time() - t0 < 0.3:
            near = set()
            for s in range(M):
                if state[s] == 1:
                    for v in g.nbrs[s]:
                        if state[v] == 0:
                            near.add(v)
                            for w in g.nbrs[v]:
                                if state[w] == 0:
                                    near.add(w)
            near -= set(cands)
            for x in sorted(near, key=lambda y: costM[y])[:40]:
                if time.time() - t0 > 0.32:
                    break
                state[x] = 1
                wc = _win_cells_after(state, 1, x, g)
                state[x] = 0
                if len(wc) >= 2:
                    return g.cells[x]
        if time.time() - t0 < 0.34:
            ys = _opp_double_threats(state, g, [], t0 + 0.4, costO, 40, True)
            for y in ys:
                if y in cands:
                    cands.remove(y)
                cands.insert(0, y)
    results = []
    for x in cands:
        el = time.time() - t0
        if el > 0.6 and len(results) >= 3:
            break
        state[x] = 1
        m1, a1, b1, _ = _potential(state, 1, g)
        m2, a2, b2, _ = _potential(state, 2, g)
        wc = _win_cells_after(state, 1, x, g)
        state[x] = 0
        fm = _f(m1, a1, b1)
        fo = _f(m2, a2, b2)
        score = fo - fm + 0.005 * depth[x]
        if len(wc) >= 2:
            score += 1000.0
        elif len(wc) == 1:
            score += 0.25
        results.append((score, x, wc))
    if not results:
        return g.cells[cands[0]]
    results.sort(key=lambda t: -t[0])
    if results[0][0] >= 1000.0:
        return g.cells[results[0][1]]
    for score, x, wc in results[:3]:
        if time.time() - t0 > 0.78:
            break
        state[x] = 1
        dz = _opp_double_threats(state, g, wc, t0 + 0.85, costO, 40, False)
        state[x] = 0
        if not dz:
            return g.cells[x]
    return g.cells[results[0][1]]


def _fallback_move(me, opp, valid_mask):
    vm = np.asarray(valid_mask).astype(bool)
    occ = set()
    for r, c in list(me) + list(opp):
        occ.add((int(r), int(c)))
    cands = [(r, c) for r in range(vm.shape[0]) for c in range(vm.shape[1])
             if vm[r, c] and (r, c) not in occ]
    if not cands:
        return (0, 0)
    cr, cc = vm.shape[0] / 2.0, vm.shape[1] / 2.0
    cands.sort(key=lambda p: abs(p[0] - cr) + abs(p[1] - cc))
    return cands[0]


def policy(me, opp, valid_mask):
    t0 = time.time()
    try:
        mv = _policy(me, opp, valid_mask, t0)
        if mv is not None:
            r, c = int(mv[0]), int(mv[1])
            vm = np.asarray(valid_mask).astype(bool)
            occ = set((int(a), int(b)) for a, b in list(me) + list(opp))
            if vm[r, c] and (r, c) not in occ:
                return (r, c)
    except Exception:
        pass
    return _fallback_move(me, opp, valid_mask)
