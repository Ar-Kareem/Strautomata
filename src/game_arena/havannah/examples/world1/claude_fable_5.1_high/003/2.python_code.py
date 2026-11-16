
import time
import heapq

INF = 99
_GEO_CACHE = {}
_POP = [bin(i).count('1') for i in range(64)]
TIME_LIMIT = 0.72


class _Geo:
    pass


def _build(valid, R, C):
    colmin = [None] * C
    colmax = [None] * C
    for c in range(C):
        rs = [r for r in range(R) if valid[r][c]]
        if rs:
            colmin[c] = rs[0]
            colmax[c] = rs[-1]
    idx = [[-1] * C for _ in range(R)]
    cells = []
    for r in range(R):
        for c in range(C):
            if valid[r][c]:
                idx[r][c] = len(cells)
                cells.append((r, c))
    N = len(cells)
    mode = 'geo'
    for c in range(C - 1):
        if colmin[c] is not None and colmin[c + 1] is not None:
            if ((colmin[c] + colmax[c]) - (colmin[c + 1] + colmax[c + 1])) % 2 == 0:
                mode = 'axial'
                break
    nbr6 = []
    nbrs = []
    for i, (r, c) in enumerate(cells):
        lst = []
        if mode == 'geo':
            d = colmin[c] + colmax[c]
            p = 2 * r - d
            dirs = [(p - 2, c), (p - 1, c + 1), (p + 1, c + 1), (p + 2, c), (p + 1, c - 1), (p - 1, c - 1)]
            for pp, cc in dirs:
                j = -1
                if 0 <= cc < C and colmin[cc] is not None:
                    dd = colmin[cc] + colmax[cc]
                    if (pp + dd) % 2 == 0:
                        rr = (pp + dd) // 2
                        if 0 <= rr < R and valid[rr][cc]:
                            j = idx[rr][cc]
                lst.append(j)
        else:
            dirs = [(r - 1, c), (r, c + 1), (r + 1, c + 1), (r + 1, c), (r, c - 1), (r - 1, c - 1)]
            for rr, cc in dirs:
                j = -1
                if 0 <= rr < R and 0 <= cc < C and valid[rr][cc]:
                    j = idx[rr][cc]
                lst.append(j)
        nbr6.append(lst)
        nbrs.append([j for j in lst if j >= 0])
    deg = [len(nbrs[i]) for i in range(N)]
    ccols = [c for c in range(C) if colmin[c] is not None]
    cmin = ccols[0]
    cmax = ccols[-1]
    mid = (cmin + cmax) / 2.0
    center_col = max(ccols, key=lambda c: (colmax[c] - colmin[c], -abs(c - mid)))
    corner_id = [-1] * N
    edge_id = [-1] * N
    corners = [i for i in range(N) if deg[i] == 3]
    for k, i in enumerate(corners[:6]):
        corner_id[i] = k
    for i, (r, c) in enumerate(cells):
        if deg[i] >= 6 or corner_id[i] >= 0:
            continue
        if c == cmin:
            e = 0
        elif c == cmax:
            e = 1
        elif c < center_col:
            e = 2 if r == colmin[c] else 3
        else:
            e = 4 if r == colmin[c] else 5
        edge_id[i] = e
    ebit = [(1 << edge_id[i]) if edge_id[i] >= 0 else 0 for i in range(N)]
    cbit = [(1 << corner_id[i]) if corner_id[i] >= 0 else 0 for i in range(N)]
    edge_cells = [[] for _ in range(6)]
    for i in range(N):
        if edge_id[i] >= 0:
            edge_cells[edge_id[i]].append(i)
    corner_cells = corners[:6]
    crow = int(round((colmin[center_col] + colmax[center_col]) / 2.0))
    center = idx[crow][center_col]
    if center < 0:
        center = 0
    cent = [INF] * N
    cent[center] = 0
    q = [center]
    qi = 0
    while qi < len(q):
        u = q[qi]
        qi += 1
        for v in nbrs[u]:
            if cent[v] == INF:
                cent[v] = cent[u] + 1
                q.append(v)
    G = _Geo()
    G.R = R
    G.C = C
    G.N = N
    G.idx = idx
    G.cells = cells
    G.nbr6 = nbr6
    G.nbrs = nbrs
    G.ebit = ebit
    G.cbit = cbit
    G.edge_cells = edge_cells
    G.corner_cells = corner_cells
    G.center = center
    G.cent = cent
    return G


def _get_geo(valid_mask):
    R = len(valid_mask)
    C = len(valid_mask[0])
    key = tuple(tuple(bool(valid_mask[r][c]) for c in range(C)) for r in range(R))
    g = _GEO_CACHE.get(key)
    if g is None:
        g = _build(key, R, C)
        _GEO_CACHE.clear()
        _GEO_CACHE[key] = g
    return g


def _label(G, color, p):
    N = G.N
    nbrs = G.nbrs
    ebit = G.ebit
    cbit = G.cbit
    gid = [-1] * N
    groups = []
    for i in range(N):
        if color[i] == p and gid[i] < 0:
            g = len(groups)
            gid[i] = g
            em = 0
            cm = 0
            libs = set()
            stack = [i]
            while stack:
                u = stack.pop()
                em |= ebit[u]
                cm |= cbit[u]
                for v in nbrs[u]:
                    cv = color[v]
                    if cv == p:
                        if gid[v] < 0:
                            gid[v] = g
                            stack.append(v)
                    elif cv == 0:
                        libs.add(v)
            groups.append((em, cm, list(libs)))
    return gid, groups


def _is_win(G, color, p, x, gid, groups):
    em = G.ebit[x]
    cm = G.cbit[x]
    seen = []
    for v in G.nbrs[x]:
        if color[v] == p:
            g = gid[v]
            if g not in seen:
                seen.append(g)
                em |= groups[g][0]
                cm |= groups[g][1]
    if _POP[em] >= 3 or _POP[cm] >= 2:
        return True
    if not seen:
        return False
    seq = []
    for v in G.nbr6[x]:
        if v >= 0 and color[v] == p:
            seq.append(gid[v])
        else:
            seq.append(-1)
    for g in seen:
        runs = 0
        for k in range(6):
            if seq[k] == g and seq[k - 1] != g:
                runs += 1
        if runs >= 2:
            return True
    return False


def _two_dist(G, color, p, gid, groups, seeds, touch):
    N = G.N
    nbrs = G.nbrs
    ng = len(groups)
    NN = N + ng
    d = [INF] * NN
    cnt = [0] * NN
    done = [False] * NN
    heap = []
    for g in range(ng):
        if touch[g]:
            d[N + g] = 0
            heap.append((0, N + g))
    for s in seeds:
        if color[s] == 0:
            d[s] = 1
            heap.append((1, s))
    heapq.heapify(heap)
    push = heapq.heappush
    pop = heapq.heappop
    while heap:
        du, u = pop(heap)
        if done[u]:
            continue
        done[u] = True
        if u >= N:
            for v in groups[u - N][2]:
                if color[v] == 0 and not done[v]:
                    cnt[v] += 2
                    if d[v] == INF:
                        d[v] = du + 1
                        push(heap, (du + 1, v))
        else:
            seen = None
            for v in nbrs[u]:
                cv = color[v]
                if cv == 0:
                    if not done[v]:
                        cnt[v] += 1
                        if cnt[v] >= 2 and d[v] == INF:
                            d[v] = du + 1
                            push(heap, (du + 1, v))
                elif cv == p:
                    g = N + gid[v]
                    if not done[g]:
                        if seen is None:
                            seen = [g]
                        elif g in seen:
                            continue
                        else:
                            seen.append(g)
                        cnt[g] += 1
                        if cnt[g] >= 2 and d[g] == INF:
                            d[g] = du
                            push(heap, (du, g))
    return d


def _analyze(G, color, p, gid, groups):
    N = G.N
    ng = len(groups)
    E = []
    for e in range(6):
        touch = [(gr[0] >> e) & 1 for gr in groups]
        E.append(_two_dist(G, color, p, gid, groups, G.edge_cells[e], touch))
    Cs = []
    for j in range(6):
        touch = [(gr[1] >> j) & 1 for gr in groups]
        seeds = [G.corner_cells[j]] if j < len(G.corner_cells) else []
        Cs.append(_two_dist(G, color, p, gid, groups, seeds, touch))
    E0, E1, E2, E3, E4, E5 = E
    C0, C1, C2, C3, C4, C5 = Cs
    mv = [300] * N
    best = 999
    vals = []
    for y in range(N):
        if color[y] != 0:
            continue
        a = sorted((E0[y], E1[y], E2[y], E3[y], E4[y], E5[y]))
        f = a[0] + a[1] + a[2] - 2
        b = sorted((C0[y], C1[y], C2[y], C3[y], C4[y], C5[y]))
        bb = b[0] + b[1] - 1
        m = f if f < bb else bb
        if m > 60:
            m = 60
        mv[y] = m
        vals.append(m)
        if m < best:
            best = m
    for g in range(ng):
        k = N + g
        a = sorted((E0[k], E1[k], E2[k], E3[k], E4[k], E5[k]))
        f = a[0] + a[1] + a[2]
        b = sorted((C0[k], C1[k], C2[k], C3[k], C4[k], C5[k]))
        bb = b[0] + b[1]
        m = f if f < bb else bb
        if m > 60:
            m = 60
        vals.append(m)
        if m < best:
            best = m
    if best > 60:
        best = 60
    soft = 0
    for m in vals:
        if m <= best + 1:
            soft += 1
    return best, soft, mv


def _count_wins(G, color, p, gid, groups, limit=2):
    nbrs = G.nbrs
    wins = 0
    for w in range(G.N):
        if color[w] != 0:
            continue
        adj = False
        for v in nbrs[w]:
            if color[v] == p:
                adj = True
                break
        if adj and _is_win(G, color, p, w, gid, groups):
            wins += 1
            if wins >= limit:
                break
    return wins


def _policy(me, opp, valid_mask, t0):
    G = _get_geo(valid_mask)
    N = G.N
    nbrs = G.nbrs
    cells = G.cells
    idx = G.idx
    color = [0] * N
    for (r, c) in me:
        r = int(r); c = int(c)
        if 0 <= r < G.R and 0 <= c < G.C and idx[r][c] >= 0:
            color[idx[r][c]] = 1
    for (r, c) in opp:
        r = int(r); c = int(c)
        if 0 <= r < G.R and 0 <= c < G.C and idx[r][c] >= 0:
            color[idx[r][c]] = 2
    empties = [i for i in range(N) if color[i] == 0]
    if not empties:
        raise RuntimeError("no empties")
    if len(me) + len(opp) == 0:
        if color[G.center] == 0:
            return cells[G.center]
        return cells[empties[0]]

    gid1, gr1 = _label(G, color, 1)
    gid2, gr2 = _label(G, color, 2)

    adj1 = []
    adj2 = []
    for x in empties:
        a1 = False
        a2 = False
        for v in nbrs[x]:
            cv = color[v]
            if cv == 1:
                a1 = True
            elif cv == 2:
                a2 = True
        if a1:
            adj1.append(x)
        if a2:
            adj2.append(x)

    # 1. immediate win
    for x in adj1:
        if _is_win(G, color, 1, x, gid1, gr1):
            return cells[x]
    # 2. block immediate opponent win
    oppwins = [x for x in adj2 if _is_win(G, color, 2, x, gid2, gr2)]
    if len(oppwins) == 1:
        return cells[oppwins[0]]

    # 3. base analysis
    Tm, softm, mvm = _analyze(G, color, 1, gid1, gr1)
    To, softo, mvo = _analyze(G, color, 2, gid2, gr2)

    if oppwins:
        cand = oppwins
    else:
        pre = {}
        for x in empties:
            p = min(mvm[x] - Tm, mvo[x] - To)
            for v in nbrs[x]:
                if color[v]:
                    p -= 0.5
                    break
            p += 0.02 * G.cent[x]
            pre[x] = p
        cand = sorted(empties, key=lambda x: pre[x])

        # 4. opponent double-threat detection
        zs = list(adj2)
        zset = set(zs)
        for x in sorted(empties, key=lambda x: mvo[x]):
            if len(zs) >= 50:
                break
            if x not in zset:
                zs.append(x)
                zset.add(x)
        zs.sort(key=lambda x: mvo[x])
        zs = zs[:50]
        dangerous = {}
        for z in zs:
            if time.time() - t0 > 0.30:
                break
            color[z] = 2
            g2, grz = _label(G, color, 2)
            ws = []
            for w in range(N):
                if color[w] != 0:
                    continue
                adj = False
                for v in nbrs[w]:
                    if color[v] == 2:
                        adj = True
                        break
                if adj and _is_win(G, color, 2, w, g2, grz):
                    ws.append(w)
                    if len(ws) >= 3:
                        break
            color[z] = 0
            if len(ws) >= 2:
                dangerous[z] = ws
        if dangerous:
            def neutral(m):
                for z, ws in dangerous.items():
                    if m == z:
                        continue
                    if len(ws) == 2 and m in ws:
                        continue
                    return False
                return True
            filt = [x for x in cand if neutral(x)]
            if filt:
                cand = filt
        cand = cand[:60]

    # 5. evaluate candidates
    best = None
    bestsc = -1e18
    cent = G.cent
    for x in cand:
        if best is not None and time.time() - t0 > TIME_LIMIT:
            break
        color[x] = 1
        g1, grx = _label(G, color, 1)
        wins = _count_wins(G, color, 1, g1, grx, 2)
        if wins >= 2 and not oppwins:
            color[x] = 0
            return cells[x]
        Tm2, sm2, _ = _analyze(G, color, 1, g1, grx)
        To2, so2, _ = _analyze(G, color, 2, gid2, gr2)
        color[x] = 0
        sc = (To2 - Tm2) + 0.03 * (min(sm2, 10) - min(so2, 10)) - 0.01 * cent[x]
        if wins == 1:
            sc += 0.3
        if sc > bestsc:
            bestsc = sc
            best = x
    if best is None:
        best = cand[0]
    return cells[best]


def policy(me, opp, valid_mask):
    t0 = time.time()
    try:
        mv = _policy(me, opp, valid_mask, t0)
        r, c = int(mv[0]), int(mv[1])
        occ = set((int(a), int(b)) for a, b in me) | set((int(a), int(b)) for a, b in opp)
        if valid_mask[r][c] and (r, c) not in occ:
            return (r, c)
    except Exception:
        pass
    occ = set((int(a), int(b)) for a, b in me) | set((int(a), int(b)) for a, b in opp)
    R = len(valid_mask)
    for r in range(R):
        for c in range(len(valid_mask[r])):
            if valid_mask[r][c] and (r, c) not in occ:
                return (r, c)
    return (0, 0)
