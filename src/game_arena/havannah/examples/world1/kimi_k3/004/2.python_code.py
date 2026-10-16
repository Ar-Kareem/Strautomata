
import time
import math
import random

N = 15
CELLS = N * N
TOT = CELLS + 12  # +6 corner virtual nodes, +6 edge virtual nodes
OFF = ((-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1))

_geom_cache = {}


def _build_geom(mask):
    valid = [False] * CELLS
    for r in range(N):
        row = mask[r]
        base = r * N
        for c in range(N):
            if row[c]:
                valid[base + c] = True
    valid_list = [i for i in range(CELLS) if valid[i]]
    V = len(valid_list)
    NEIGH = [()] * CELLS
    for v in valid_list:
        r, c = divmod(v, N)
        ns = []
        for dr, dc in OFF:
            rr = r + dr
            cc = c + dc
            if 0 <= rr < N and 0 <= cc < N and valid[rr * N + cc]:
                ns.append(rr * N + cc)
        NEIGH[v] = tuple(ns)
    bset = set()
    for v in valid_list:
        if len(NEIGH[v]) < 6:
            bset.add(v)
    corners = [v for v in bset if len(NEIGH[v]) == 3]
    CORNER = [-1] * CELLS
    EDGE = [-1] * CELLS
    BOUNDARY = sorted(bset)
    if len(corners) == 6:
        start = min(corners)
        order = [start]
        prev = -1
        cur = start
        while True:
            nxts = [u for u in NEIGH[cur] if u in bset and u != prev]
            if not nxts:
                break
            nxt = nxts[0]
            if nxt == start:
                break
            order.append(nxt)
            prev, cur = cur, nxt
            if len(order) > CELLS:
                break
        cset = set(corners)
        cpos = [i for i, v in enumerate(order) if v in cset]
        L = len(order)
        if len(cpos) == 6:
            for k in range(6):
                CORNER[order[cpos[k]]] = k
                a = cpos[k]
                bb = cpos[(k + 1) % 6]
                i = (a + 1) % L
                while i != bb:
                    EDGE[order[i]] = k
                    i = (i + 1) % L
    DIST2 = [()] * CELLS
    for v in valid_list:
        s = set(NEIGH[v])
        for u in NEIGH[v]:
            s.update(NEIGH[u])
        s.discard(v)
        DIST2[v] = tuple(sorted(s))
    center = 7 * N + 7
    if not valid[center]:
        center = valid_list[V // 2]
    cr, cc = divmod(center, N)
    CENT = [0] * CELLS
    for v in valid_list:
        r, c = divmod(v, N)
        dr = r - cr
        dc = c - cc
        CENT[v] = -((abs(dr) + abs(dc) + abs(dr - dc)) // 2)
    return (valid_list, V, NEIGH, CORNER, EDGE, BOUNDARY, DIST2, CENT,
            center, corners)


def _geom(mask):
    try:
        key = mask.tobytes()
    except AttributeError:
        key = repr(mask)
    g = _geom_cache.get(key)
    if g is None:
        _geom_cache.clear()
        g = _build_geom(mask)
        _geom_cache[key] = g
    return g


def _find(par, x):
    while par[x] != x:
        par[x] = par[par[x]]
        x = par[x]
    return x


def _build_uf(b, p, valid_list, NEIGH, CORNER, EDGE):
    par = list(range(TOT))
    for v in valid_list:
        if b[v] == p:
            for u in NEIGH[v]:
                if b[u] == p:
                    ru = _find(par, u)
                    rv = _find(par, v)
                    if ru != rv:
                        par[ru] = rv
            ci = CORNER[v]
            if ci >= 0:
                ru = _find(par, 225 + ci)
                rv = _find(par, v)
                if ru != rv:
                    par[ru] = rv
            ei = EDGE[v]
            if ei >= 0:
                ru = _find(par, 231 + ei)
                rv = _find(par, v)
                if ru != rv:
                    par[ru] = rv
    return par


def _ring(b, p, target, NEIGH, BOUNDARY):
    # True iff some non-p cell is unreachable from the boundary (enclosed).
    seen = bytearray(CELLS)
    stack = []
    cnt = 0
    for v in BOUNDARY:
        if b[v] != p and not seen[v]:
            seen[v] = 1
            cnt += 1
            stack.append(v)
    while stack:
        x = stack.pop()
        for u in NEIGH[x]:
            if b[u] != p and not seen[u]:
                seen[u] = 1
                cnt += 1
                stack.append(u)
        if cnt >= target:
            return False
    return cnt < target


def _place_win(b, par, v, p, target, NEIGH, CORNER, EDGE, BOUNDARY):
    # b[v] must already be p. Mutates par (unions). Returns True if p wins.
    roots = []
    for u in NEIGH[v]:
        if b[u] == p:
            x = u
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            roots.append(x)
    ci = CORNER[v]
    ei = EDGE[v]
    rset = set(roots)
    nsignals = len(rset) + (1 if ci >= 0 else 0) + (1 if ei >= 0 else 0)
    cyc = len(roots) >= 2 and len(rset) < len(roots)
    for ru in roots:
        par[ru] = v
    if ci >= 0:
        x = 225 + ci
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        par[x] = v
    if ei >= 0:
        x = 231 + ei
        while par[x] != x:
            par[x] = par[par[x]]
            x = par[x]
        par[x] = v
    if nsignals >= 2:
        seenr = []
        for i in range(6):
            x = 225 + i
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            if x in seenr:
                return True  # bridge
            seenr.append(x)
        er = []
        for i in range(6):
            x = 231 + i
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            er.append(x)
        for x in er:
            if er.count(x) >= 3:
                return True  # fork
    if cyc:
        return _ring(b, p, target, NEIGH, BOUNDARY)
    return False


def _find_wins(b, p, empties, base_par, pc, V, NEIGH, CORNER, EDGE, BOUNDARY):
    wins = []
    target = V - pc - 1
    for v in empties:
        for u in NEIGH[v]:
            if b[u] == p:
                break
        else:
            continue  # no friendly neighbor: cannot win
        par = base_par[:]
        b[v] = p
        if _place_win(b, par, v, p, target, NEIGH, CORNER, EDGE, BOUNDARY):
            wins.append(v)
        b[v] = 0
    return wins


def _cands(b, occ, emp, NEIGH, DIST2):
    if len(emp) <= 50:
        return emp[:]
    cs = set()
    for v in occ:
        cs.update(DIST2[v])
    out = [v for v in cs if b[v] == 0]
    if not out:
        out = emp[:]
    return out


def _order(b, cands, p, NEIGH, CENT):
    q = 3 - p
    scored = []
    for v in cands:
        fn = 0
        en = 0
        for u in NEIGH[v]:
            w = b[u]
            if w == p:
                fn += 1
            elif w == q:
                en += 1
        scored.append((2.0 * fn + en + 0.15 * CENT[v] + random.random() * 0.05, v))
    scored.sort()
    return [v for _, v in scored]


def _rollout(b, par1, par2, emp, pos, p, pc1, pc2, mvs,
             NEIGH, CORNER, EDGE, BOUNDARY, V, local_p):
    last = -1
    rnd = random.random
    rr = random.randrange
    while emp:
        v = -1
        if last >= 0 and rnd() < local_p:
            opts = [u for u in NEIGH[last] if b[u] == 0]
            if opts:
                v = opts[rr(len(opts))]
        if v < 0:
            v = emp[rr(len(emp))]
        i = pos[v]
        l = emp[-1]
        emp[i] = l
        pos[l] = i
        emp.pop()
        pos[v] = -1
        b[v] = p
        mvs.append((p, v))
        if p == 1:
            pc1 += 1
            pc = pc1
            par = par1
        else:
            pc2 += 1
            pc = pc2
            par = par2
        if _place_win(b, par, v, p, V - pc, NEIGH, CORNER, EDGE, BOUNDARY):
            return p
        last = v
        p = 3 - p
    return 0


class _Node:
    __slots__ = ('move', 'children', 'untried', 'n', 'w', 'an', 'aw', 'term')

    def __init__(self, move):
        self.move = move
        self.children = []
        self.untried = None
        self.n = 0
        self.w = 0.0
        self.an = 0
        self.aw = 0.0
        self.term = False


def _policy(me, opp, valid_mask):
    t0 = time.time()
    deadline = t0 + 0.90
    (valid_list, V, NEIGH, CORNER, EDGE, BOUNDARY, DIST2, CENT,
     center, corners) = _geom(valid_mask)
    b = [-1] * CELLS
    for v in valid_list:
        b[v] = 0
    for rc in me:
        b[int(rc[0]) * N + int(rc[1])] = 1
    for rc in opp:
        b[int(rc[0]) * N + int(rc[1])] = 2
    empties = [v for v in valid_list if b[v] == 0]
    if not empties:
        return (7, 7)
    if len(empties) == 1:
        return divmod(empties[0], N)
    pos0 = [-1] * CELLS
    for i, v in enumerate(empties):
        pos0[v] = i
    pc1 = len(me)
    pc2 = len(opp)
    base1 = _build_uf(b, 1, valid_list, NEIGH, CORNER, EDGE)
    base2 = _build_uf(b, 2, valid_list, NEIGH, CORNER, EDGE)
    # 1) immediate win
    w1 = _find_wins(b, 1, empties, base1, pc1, V, NEIGH, CORNER, EDGE, BOUNDARY)
    if w1:
        return divmod(w1[0], N)
    # 2) block opponent's immediate win
    w2 = _find_wins(b, 2, empties, base2, pc2, V, NEIGH, CORNER, EDGE, BOUNDARY)
    if w2:
        bestv = max(w2, key=lambda v: sum(1 for u in NEIGH[v] if b[u] == 1))
        return divmod(bestv, N)
    occ = [v for v in valid_list if b[v] != 0]
    if not occ:
        return divmod(center, N)
    cands = _cands(b, occ, empties, NEIGH, DIST2)
    if len(empties) > 50:
        extra = set(cands)
        for cv in corners:
            extra.update(DIST2[cv])
        cands = [v for v in extra if b[v] == 0]
    if not cands:
        cands = empties[:]
    if len(cands) == 1:
        return divmod(cands[0], N)

    root = _Node(-1)
    root.untried = _order(b, cands, 1, NEIGH, CENT)
    C_EXP = 0.35
    K_RAVE = 700.0
    LOCAL_P = 0.30
    log = math.log
    sqrt = math.sqrt
    it = 0
    while True:
        if (it & 31) == 0 and time.time() >= deadline:
            break
        it += 1
        bb = b[:]
        p1 = base1[:]
        p2 = base2[:]
        emp = empties[:]
        pos = pos0[:]
        occit = occ[:]
        root.n += 1
        node = root
        path = [root]
        mvs = []
        p = 1
        c1 = pc1
        c2 = pc2
        winner = 0
        while True:
            ut = node.untried
            if ut is None:
                ut = _order(bb, _cands(bb, occit, emp, NEIGH, DIST2),
                            p, NEIGH, CENT)
                node.untried = ut
            if ut:
                v = ut.pop()
                i = pos[v]
                l = emp[-1]
                emp[i] = l
                pos[l] = i
                emp.pop()
                pos[v] = -1
                bb[v] = p
                occit.append(v)
                mvs.append((p, v))
                if p == 1:
                    c1 += 1
                    pc = c1
                    par = p1
                else:
                    c2 += 1
                    pc = c2
                    par = p2
                child = _Node(v)
                node.children.append(child)
                path.append(child)
                if _place_win(bb, par, v, p, V - pc,
                              NEIGH, CORNER, EDGE, BOUNDARY):
                    child.term = True
                    winner = p
                else:
                    winner = _rollout(bb, p1, p2, emp, pos, 3 - p, c1, c2,
                                      mvs, NEIGH, CORNER, EDGE, BOUNDARY,
                                      V, LOCAL_P)
                break
            chs = node.children
            if not chs:
                winner = 0
                break
            logn = log(node.n)
            beta = sqrt(K_RAVE / (3.0 * node.n + K_RAVE))
            best = None
            bs = -1e18
            for ch in chs:
                if ch.term:
                    best = ch
                    break
                ex = ch.w / ch.n
                am = ch.aw / ch.an if ch.an else 0.5
                val = (1.0 - beta) * ex + beta * am + C_EXP * sqrt(logn / ch.n)
                if val > bs:
                    bs = val
                    best = ch
            node = best
            path.append(node)
            v = node.move
            i = pos[v]
            l = emp[-1]
            emp[i] = l
            pos[l] = i
            emp.pop()
            pos[v] = -1
            bb[v] = p
            occit.append(v)
            mvs.append((p, v))
            if p == 1:
                c1 += 1
                pc = c1
                par = p1
            else:
                c2 += 1
                pc = c2
                par = p2
            if _place_win(bb, par, v, p, V - pc,
                          NEIGH, CORNER, EDGE, BOUNDARY):
                node.term = True
                winner = p
                break
            p = 3 - p
        # backpropagate
        for k in range(1, len(path)):
            nd = path[k]
            nd.n += 1
            if mvs[k - 1][0] == winner:
                nd.w += 1.0
        later1 = set()
        later2 = set()
        lp = len(path)
        for idx in range(len(mvs) - 1, -1, -1):
            pl, mv = mvs[idx]
            if pl == 1:
                later1.add(mv)
                lat = later1
            else:
                later2.add(mv)
                lat = later2
            if idx < lp:
                rw = 1.0 if pl == winner else 0.0
                for ch in path[idx].children:
                    if ch.move in lat:
                        ch.an += 1
                        ch.aw += rw

    best = None
    for ch in root.children:
        if ch.term:
            best = ch
            break
        if best is None or ch.n > best.n or (ch.n == best.n and ch.w > best.w):
            best = ch
    if best is None or best.move < 0:
        v = root.untried[-1] if root.untried else cands[0]
    else:
        v = best.move
    if b[v] != 0:
        v = empties[0]
    return divmod(v, N)


def policy(me, opp, valid_mask):
    try:
        return _policy(me, opp, valid_mask)
    except Exception:
        try:
            occ = set()
            for rc in me:
                occ.add((int(rc[0]), int(rc[1])))
            for rc in opp:
                occ.add((int(rc[0]), int(rc[1])))
            for r in range(N):
                for c in range(N):
                    if valid_mask[r][c] and (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
        return (7, 7)
