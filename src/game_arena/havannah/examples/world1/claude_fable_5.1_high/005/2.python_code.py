
import time, math
from collections import deque

INF = 99
_POW = [2.0 ** (-v) for v in range(400)]
_BOARD = None
_BKEY = None


def _make_systems():
    def colOddUp(r, c):
        if c & 1:
            return ((r-1, c), (r+1, c), (r-1, c-1), (r, c-1), (r-1, c+1), (r, c+1))
        return ((r-1, c), (r+1, c), (r, c-1), (r+1, c-1), (r, c+1), (r+1, c+1))

    def axA(r, c):
        return ((r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c+1), (r+1, c-1))

    def axB(r, c):
        return ((r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c-1), (r+1, c+1))

    def colEvenUp(r, c):
        if not (c & 1):
            return ((r-1, c), (r+1, c), (r-1, c-1), (r, c-1), (r-1, c+1), (r, c+1))
        return ((r-1, c), (r+1, c), (r, c-1), (r+1, c-1), (r, c+1), (r+1, c+1))

    def rowOddLeft(r, c):
        if r & 1:
            return ((r, c-1), (r, c+1), (r-1, c-1), (r-1, c), (r+1, c-1), (r+1, c))
        return ((r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c+1))

    def rowEvenLeft(r, c):
        if not (r & 1):
            return ((r, c-1), (r, c+1), (r-1, c-1), (r-1, c), (r+1, c-1), (r+1, c))
        return ((r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c+1))

    return [colOddUp, axA, axB, colEvenUp, rowOddLeft, rowEvenLeft]


def _build(valid):
    N = len(valid)
    M = len(valid[0])
    cells = []
    idx = {}
    for r in range(N):
        for c in range(M):
            if valid[r][c]:
                idx[(r, c)] = len(cells)
                cells.append((r, c))
    n = len(cells)
    s = int(round((3 + math.sqrt(max(12 * n - 3, 0))) / 6))
    hexnum = (3 * s * s - 3 * s + 1 == n)
    systems = _make_systems()
    chosen = None
    for sysf in systems:
        nb = []
        for (r, c) in cells:
            nb.append([idx[p] for p in sysf(r, c) if p in idx])
        degs = [len(l) for l in nb]
        d3 = degs.count(3); d4 = degs.count(4); d6 = degs.count(6)
        if d3 + d4 + d6 == n and d3 == 6 and (not hexnum or d4 == 6 * (s - 2)):
            chosen = nb
            break
    if chosen is None:
        sysf = systems[0]
        chosen = [[idx[p] for p in sysf(r, c) if p in idx] for (r, c) in cells]
    nbrs = chosen
    degs = [len(l) for l in nbrs]
    boundary = [i for i in range(n) if degs[i] < 6]
    interior = [i for i in range(n) if degs[i] == 6]
    corner = [i for i in range(n) if degs[i] == 3][:12]
    corner_of = [-1] * n
    for k, i in enumerate(corner):
        corner_of[i] = k
    isb = [False] * n
    for i in boundary:
        isb[i] = True
    edge_of = [-1] * n
    E = 0
    for i in boundary:
        if edge_of[i] == -1 and corner_of[i] == -1:
            edge_of[i] = E
            st = [i]
            while st:
                c = st.pop()
                for m in nbrs[c]:
                    if isb[m] and corner_of[m] == -1 and edge_of[m] == -1:
                        edge_of[m] = E
                        st.append(m)
            E += 1
    Eu = min(E, 12)
    edge_src = [[] for _ in range(Eu)]
    for i in range(n):
        e = edge_of[i]
        if 0 <= e < Eu:
            edge_src[e].append(i)
    corner_src = [[i] for i in corner]
    depth = [INF] * n
    dq = deque()
    for b in boundary:
        depth[b] = 0
        dq.append(b)
    while dq:
        c = dq.popleft()
        for m in nbrs[c]:
            if depth[m] > depth[c] + 1:
                depth[m] = depth[c] + 1
                dq.append(m)
    return dict(n=n, cells=cells, idx=idx, nbrs=nbrs, boundary=boundary, interior=interior,
                corner_of=corner_of, edge_of=edge_of, edge_src=edge_src, corner_src=corner_src,
                depth=depth)


def _bfs(src, zero, blk, nbrs, n):
    d = [INF] * n
    dq = deque()
    for s in src:
        if not blk[s]:
            d[s] = 0
            dq.append(s)
    pop = dq.popleft; ap = dq.append; apl = dq.appendleft
    while dq:
        c = pop()
        dc = d[c]
        if zero[c]:
            for m in nbrs[c]:
                if dc < d[m] and not blk[m]:
                    d[m] = dc
                    apl(m)
        else:
            nd = dc + 1
            for m in nbrs[c]:
                if nd < d[m] and not blk[m]:
                    d[m] = nd
                    ap(m)
    return d


def _eval_side(owner, P, Q, B):
    n = B['n']; nbrs = B['nbrs']
    zero = [o == P for o in owner]
    blk = [o == Q for o in owner]
    ed = [_bfs(src, zero, blk, nbrs, n) for src in B['edge_src']]
    cd = [_bfs(src, zero, blk, nbrs, n) for src in B['corner_src']]
    E = len(ed); K = len(cd)
    best = INF * 3; threats = 0; soft = 0.0
    vals = [INF * 3] * n
    BIG = INF * 3
    for c in range(n):
        if blk[c]:
            continue
        add = 0 if zero[c] else 1
        v = BIG
        if E >= 3:
            a = sorted([m[c] for m in ed])
            v = a[0] + a[1] + a[2]
        if K >= 2:
            b = sorted([m[c] for m in cd])
            t = b[0] + b[1]
            if t < v:
                v = t
        v += add
        vals[c] = v
        if v < best:
            best = v
        if add and v == 1:
            threats += 1
        if v < 60:
            soft += _POW[v]
    return best, threats, soft, vals


def _ring_pot(owner, P, Q, B):
    best = 0
    nbrs = B['nbrs']
    for c in B['interior']:
        if owner[c] == P:
            continue
        cp = 0; cq = 0
        for m in nbrs[c]:
            o = owner[m]
            if o == P:
                cp += 1
            elif o == Q:
                cq += 1
        if cq == 0 and cp >= 4:
            v = cp - 3
            if v > best:
                best = v
    return best


def _check_win(owner, P, x, B):
    nbrs = B['nbrs']; n = B['n']
    corner_of = B['corner_of']; edge_of = B['edge_of']
    ing = [False] * n
    ing[x] = True
    st = [x]
    cm = 0; em = 0; size = 0
    while st:
        c = st.pop()
        size += 1
        k = corner_of[c]
        if k >= 0:
            cm |= 1 << k
        e = edge_of[c]
        if e >= 0:
            em |= 1 << e
        for m in nbrs[c]:
            if owner[m] == P and not ing[m]:
                ing[m] = True
                st.append(m)
    if bin(cm).count('1') >= 2 or bin(em).count('1') >= 3:
        return True
    if size < 6:
        return False
    for c in [x] + list(nbrs[x]):
        if ing[c]:
            nb = nbrs[c]
            if len(nb) == 6 and all(ing[m] for m in nb):
                return True
    seen = ing[:]
    st = []
    for b in B['boundary']:
        if not seen[b]:
            seen[b] = True
            st.append(b)
    while st:
        c = st.pop()
        for m in nbrs[c]:
            if not seen[m]:
                seen[m] = True
                st.append(m)
    return not all(seen)


def _score(x, owner, B, opp_wins, adjm, depth):
    owner[x] = 1
    mb, mt, ms, _ = _eval_side(owner, 1, 2, B)
    ob, ot, os_, _ = _eval_side(owner, 2, 1, B)
    rm = _ring_pot(owner, 1, 2, B)
    ro = _ring_pot(owner, 2, 1, B)
    owner[x] = 0
    ex = len(opp_wins - {x}) if opp_wins else 0
    if ex > 0 or ot > 0:
        sc = -10000.0 + 4.0 * (ob - mb)
        if x in opp_wins:
            sc += 1.0
    elif mt >= 2:
        sc = 5000.0 + (ob - mb)
    else:
        sc = 4.0 * (ob - mb) + 1.0 * (ms - os_) + (0.6 if mt == 1 else 0.0) + 0.5 * rm - 0.8 * ro
    sc += 0.04 * depth[x] + 0.1 * adjm[x]
    return sc


def _policy(me, opp, valid_mask, t0):
    global _BOARD, _BKEY
    N = len(valid_mask); M = len(valid_mask[0])
    valid = [[bool(valid_mask[r][c]) for c in range(M)] for r in range(N)]
    key = tuple(tuple(row) for row in valid)
    if _BKEY != key or _BOARD is None:
        _BOARD = _build(valid)
        _BKEY = key
    B = _BOARD
    idx = B['idx']; n = B['n']; cells = B['cells']; nbrs = B['nbrs']; depth = B['depth']
    owner = [0] * n
    for (r, c) in me:
        i = idx.get((int(r), int(c)))
        if i is not None:
            owner[i] = 1
    for (r, c) in opp:
        i = idx.get((int(r), int(c)))
        if i is not None:
            owner[i] = 2
    empties = [i for i in range(n) if owner[i] == 0]
    if not empties:
        return None
    if not me and not opp:
        best = max(empties, key=lambda i: depth[i])
        return cells[best]
    adjm = [0] * n; adjo = [0] * n
    for i in range(n):
        if owner[i] == 1:
            for m in nbrs[i]:
                adjm[m] += 1
        elif owner[i] == 2:
            for m in nbrs[i]:
                adjo[m] += 1
    for x in empties:
        if adjm[x] > 0:
            owner[x] = 1
            w = _check_win(owner, 1, x, B)
            owner[x] = 0
            if w:
                return cells[x]
    opp_wins = set()
    for x in empties:
        if adjo[x] > 0:
            owner[x] = 2
            w = _check_win(owner, 2, x, B)
            owner[x] = 0
            if w:
                opp_wins.add(x)
    if len(opp_wins) == 1:
        return cells[next(iter(opp_wins))]
    mb0, mt0, ms0, myv = _eval_side(owner, 1, 2, B)
    ob0, ot0, os0, opv = _eval_side(owner, 2, 1, B)
    if opp_wins:
        cand = list(opp_wins)
    else:
        scored = []
        for x in empties:
            ch = -min(myv[x], opv[x]) + 0.3 * adjm[x] + 0.15 * adjo[x] + 0.03 * depth[x]
            scored.append((ch, x))
        scored.sort(reverse=True)
        cand = [x for _, x in scored[:32]]
    best = None; bs = -1e18
    for x in cand:
        if best is not None and time.perf_counter() - t0 > 0.68:
            break
        sc = _score(x, owner, B, opp_wins, adjm, depth)
        if sc > bs:
            bs = sc
            best = x
    if best is None:
        best = cand[0]
    return cells[best]


def policy(me, opp, valid_mask):
    t0 = time.perf_counter()
    N = len(valid_mask); M = len(valid_mask[0])
    occ = set((int(r), int(c)) for (r, c) in list(me) + list(opp))
    res = None
    try:
        res = _policy(me, opp, valid_mask, t0)
    except Exception:
        res = None
    if res is not None:
        r, c = int(res[0]), int(res[1])
        if 0 <= r < N and 0 <= c < M and bool(valid_mask[r][c]) and (r, c) not in occ:
            return (r, c)
    # fallback: first legal cell (prefer central)
    bestc = None; bd = -1
    for r in range(N):
        for c in range(M):
            if bool(valid_mask[r][c]) and (r, c) not in occ:
                d = -abs(r - N // 2) - abs(c - M // 2)
                if d > bd:
                    bd = d
                    bestc = (r, c)
    return bestc
