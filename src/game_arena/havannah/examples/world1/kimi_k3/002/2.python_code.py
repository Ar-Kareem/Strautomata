
import math
import random
import time

POP = [0] * 64
for _i in range(64):
    POP[_i] = bin(_i).count("1")

RAVE_K = 400.0
EXPL = 0.4
RAVE_DEPTH = 8
NODE_CAP = 240000
BIAS = 0.6
BUDGET = 0.86

NODE_COUNT = 0
ROOT = None
ROOT_OWNER = None


class Node:
    __slots__ = ("move", "pl", "w", "n", "children", "untried", "rave", "terminal")
    def __init__(self, move, pl):
        self.move = move
        self.pl = pl
        self.w = 0
        self.n = 0
        self.children = {}
        self.untried = None
        self.rave = {}
        self.terminal = None


def analyze(valid_mask):
    n = len(valid_mask)
    nn = n * n
    valid = [False] * nn
    for r in range(n):
        row = valid_mask[r]
        base = r * n
        for c in range(n):
            if row[c]:
                valid[base + c] = True
    NEIGH = [[] for _ in range(nn)]
    for r in range(n):
        for c in range(n):
            i = r * n + c
            if not valid[i]:
                continue
            if c & 1:
                ds = ((-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1))
            else:
                ds = ((-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1))
            nb = NEIGH[i]
            for dr, dc in ds:
                rr = r + dr
                cc = c + dc
                if 0 <= rr < n and 0 <= cc < n and valid[rr * n + cc]:
                    nb.append(rr * n + cc)
    deg = [len(NEIGH[i]) if valid[i] else 0 for i in range(nn)]
    CBITS = [0] * nn
    SBITS = [0] * nn
    BORDER = [False] * nn
    corners = [i for i in range(nn) if valid[i] and deg[i] == 3]
    ok = False
    if len(corners) == 6:
        try:
            corner_set = set(corners)
            border_cells = [i for i in range(nn) if valid[i] and 3 <= deg[i] <= 4]
            bset = set(border_cells)
            bneigh = {}
            for x in border_cells:
                bn = [y for y in NEIGH[x] if y in bset]
                if len(bn) != 2:
                    raise ValueError("bad border")
                bneigh[x] = bn
            start = corners[0]
            corner_id = {start: 0}
            cid = 1
            side = 0
            prev = start
            x = bneigh[start][0]
            target = len(border_cells) - 6
            assigned = 0
            guard = 0
            while assigned < target:
                guard += 1
                if guard > nn * 6:
                    raise ValueError("walk loop")
                if x in corner_set:
                    if x not in corner_id:
                        corner_id[x] = cid
                        cid += 1
                    side += 1
                else:
                    SBITS[x] = 1 << side
                    BORDER[x] = True
                    assigned += 1
                bn = bneigh[x]
                y = bn[0] if bn[0] != prev else bn[1]
                prev, x = x, y
            if assigned == target and side == 5 and len(corner_id) == 6:
                for x, k in corner_id.items():
                    CBITS[x] = 1 << k
                    BORDER[x] = True
                ok = True
            else:
                raise ValueError("walk mismatch")
        except Exception:
            SBITS = [0] * nn
            CBITS = [0] * nn
            BORDER = [False] * nn
            ok = False
    if not ok:
        cells = [i for i in range(nn) if valid[i]]
        if cells:
            co = {}
            sx = sy = sz = 0
            for i in cells:
                r, c = divmod(i, n)
                xq = c
                zq = r - (c + (c & 1)) // 2
                yq = -xq - zq
                co[i] = (xq, yq, zq)
                sx += xq; sy += yq; sz += zq
            m = float(len(cells))
            cx, cy, cz = sx / m, sy / m, sz / m
            R = 0.0
            for i in cells:
                xq, yq, zq = co[i]
                d = max(abs(xq - cx), abs(yq - cy), abs(zq - cz))
                if d > R:
                    R = d
            for i in cells:
                xq, yq, zq = co[i]
                d = (xq - cx, yq - cy, zq - cz)
                ad = (abs(d[0]), abs(d[1]), abs(d[2]))
                if max(ad) >= R - 0.5:
                    BORDER[i] = True
                    cnt = 0
                    for a in ad:
                        if a >= R - 0.5:
                            cnt += 1
                    if cnt >= 2:
                        az = ad.index(min(ad))
                        nxt = (az + 1) % 3
                        CBITS[i] = 1 << (az * 2 + (1 if d[nxt] > 0 else 0))
                    else:
                        ax = ad.index(max(ad))
                        SBITS[i] = 1 << (ax * 2 + (1 if d[ax] > 0 else 0))
    return valid, NEIGH, CBITS, SBITS, BORDER


def ring_win(cell, pocc, owner, NEIGH, BORDER):
    vis = bytearray(len(owner))
    for nb in NEIGH[cell]:
        if owner[nb] != pocc and not vis[nb]:
            stack = [nb]
            vis[nb] = 1
            touch = False
            while stack:
                x = stack.pop()
                if BORDER[x]:
                    touch = True
                    break
                for y in NEIGH[x]:
                    if not vis[y] and owner[y] != pocc:
                        vis[y] = 1
                        stack.append(y)
            if not touch:
                return True
    return False


def place(cell, pl, owner, emp, epos, par, cm, sm, NEIGH, CBITS, SBITS, BORDER):
    pocc = pl + 1
    owner[cell] = pocc
    j = epos[cell]
    last = emp[-1]
    emp[j] = last
    epos[last] = j
    emp.pop()
    epos[cell] = -1
    bc = CBITS[cell]
    bs = SBITS[cell]
    nneigh = 0
    roots = []
    for nb in NEIGH[cell]:
        if owner[nb] == pocc:
            nneigh += 1
            x = nb
            while par[x] != x:
                par[x] = par[par[x]]
                x = par[x]
            if x not in roots:
                roots.append(x)
    for x in roots:
        par[x] = cell
        bc |= cm[x]
        bs |= sm[x]
    cm[cell] = bc
    sm[cell] = bs
    if POP[bc] >= 2 or POP[bs] >= 3:
        return True
    if nneigh >= 2 and nneigh > len(roots):
        return ring_win(cell, pocc, owner, NEIGH, BORDER)
    return False


def find_wins(player, owner, emp, par, cm, sm, NEIGH, CBITS, SBITS, BORDER):
    pocc = player + 1
    res = []
    for cell in emp:
        bc = CBITS[cell]
        bs = SBITS[cell]
        nneigh = 0
        roots = []
        for nb in NEIGH[cell]:
            if owner[nb] == pocc:
                nneigh += 1
                x = nb
                while par[x] != x:
                    par[x] = par[par[x]]
                    x = par[x]
                if x not in roots:
                    roots.append(x)
        for x in roots:
            bc |= cm[x]
            bs |= sm[x]
        if POP[bc] >= 2 or POP[bs] >= 3:
            res.append(cell)
        elif nneigh >= 2 and nneigh > len(roots):
            owner[cell] = pocc
            if ring_win(cell, pocc, owner, NEIGH, BORDER):
                res.append(cell)
            owner[cell] = 0
    return res


def build_ufs(owner, n, NEIGH, CBITS, SBITS):
    nn = n * n
    par = [list(range(nn)), list(range(nn))]
    cm = [CBITS[:], CBITS[:]]
    sm = [SBITS[:], SBITS[:]]
    for cell in range(nn):
        o = owner[cell]
        if o:
            pl = o - 1
            parp = par[pl]; cmp_ = cm[pl]; smp = sm[pl]
            for nb in NEIGH[cell]:
                if owner[nb] == o:
                    x = nb
                    while parp[x] != x:
                        parp[x] = parp[parp[x]]
                        x = parp[x]
                    y = cell
                    while parp[y] != y:
                        parp[y] = parp[parp[y]]
                        y = parp[y]
                    if x != y:
                        parp[x] = y
                        cmp_[y] |= cmp_[x]
                        smp[y] |= smp[x]
    return par, cm, sm


def playout(pl, lm0, lm1, owner, emp, epos, p0, p1, c0, c1, s0, s1,
            NEIGH, CBITS, SBITS, BORDER, rnd, rr):
    pmoves = []
    while emp:
        cell = -1
        if rnd() < BIAS:
            lm = lm0 if pl == 0 else lm1
            cand = None
            if lm >= 0:
                for x in NEIGH[lm]:
                    if owner[x] == 0:
                        if cand is None:
                            cand = [x]
                        else:
                            cand.append(x)
            if cand is None:
                om = lm1 if pl == 0 else lm0
                if om >= 0:
                    for x in NEIGH[om]:
                        if owner[x] == 0:
                            if cand is None:
                                cand = [x]
                            else:
                                cand.append(x)
            if cand:
                cell = cand[rr(len(cand))]
        if cell < 0:
            cell = emp[rr(len(emp))]
        if pl == 0:
            won = place(cell, 0, owner, emp, epos, p0, c0, s0, NEIGH, CBITS, SBITS, BORDER)
            lm0 = cell
        else:
            won = place(cell, 1, owner, emp, epos, p1, c1, s1, NEIGH, CBITS, SBITS, BORDER)
            lm1 = cell
        pmoves.append((cell << 1) | pl)
        if won:
            return pl, pmoves
        pl ^= 1
    return -1, pmoves


def mcts(root, owner0, emp0, par, cm, sm, NEIGH, CBITS, SBITS, BORDER, t_end):
    global NODE_COUNT
    nn = len(owner0)
    epos0 = [-1] * nn
    for i, cell in enumerate(emp0):
        epos0[cell] = i
    p0r, p1r = par
    c0r, c1r = cm
    s0r, s1r = sm
    rnd = random.random
    rr = random.randrange
    sq = math.sqrt
    lg = math.log
    sims = 0
    while True:
        if (sims & 15) == 0 and time.perf_counter() > t_end:
            break
        sims += 1
        owner = owner0[:]
        emp = emp0[:]
        epos = epos0[:]
        p0 = p0r[:]; p1 = p1r[:]
        c0 = c0r[:]; c1 = c1r[:]
        s0 = s0r[:]; s1 = s1r[:]
        node = root
        path = [node]
        winner = -1
        pmoves = ()
        while True:
            term = node.terminal
            if term is not None:
                winner = term
                break
            if node.untried is None:
                node.untried = emp[:]
            if node.untried:
                if NODE_COUNT < NODE_CAP:
                    i = rr(len(node.untried))
                    mv = node.untried[i]
                    node.untried[i] = node.untried[-1]
                    node.untried.pop()
                    pl = node.pl ^ 1
                    child = Node(mv, pl)
                    NODE_COUNT += 1
                    node.children[mv] = child
                    path.append(child)
                    won = place(mv, pl, owner, emp, epos,
                                p0 if pl == 0 else p1,
                                c0 if pl == 0 else c1,
                                s0 if pl == 0 else s1,
                                NEIGH, CBITS, SBITS, BORDER)
                    if won:
                        child.terminal = pl
                        winner = pl
                    else:
                        if pl == 0:
                            lm0 = mv; lm1 = node.move
                        else:
                            lm1 = mv; lm0 = node.move
                        winner, pmoves = playout(pl ^ 1, lm0, lm1, owner, emp, epos,
                                                 p0, p1, c0, c1, s0, s1,
                                                 NEIGH, CBITS, SBITS, BORDER, rnd, rr)
                    break
                else:
                    pl = node.pl ^ 1
                    lm = node.move
                    winner, pmoves = playout(pl,
                                             lm if node.pl == 0 else -1,
                                             lm if node.pl == 1 else -1,
                                             owner, emp, epos, p0, p1, c0, c1, s0, s1,
                                             NEIGH, CBITS, SBITS, BORDER, rnd, rr)
                    break
            if node.children:
                lnn = lg(node.n)
                best = None
                bests = -1e18
                rv = node.rave
                for mv, ch in node.children.items():
                    cn = ch.n
                    ex = ch.w / cn
                    v = rv.get(mv)
                    if v is not None:
                        rn_ = v & 0xFFFFF
                        rw = v >> 20
                        beta = rn_ / (rn_ + cn + rn_ * cn / RAVE_K)
                        ex = ex * (1.0 - beta) + (rw / rn_) * beta
                    sc = ex + EXPL * sq(lnn / cn)
                    if sc > bests:
                        bests = sc
                        best = ch
                node = best
                path.append(node)
                if node.terminal is None:
                    if place(node.move, node.pl, owner, emp, epos,
                             p0 if node.pl == 0 else p1,
                             c0 if node.pl == 0 else c1,
                             s0 if node.pl == 0 else s1,
                             NEIGH, CBITS, SBITS, BORDER):
                        node.terminal = node.pl
                        winner = node.pl
                        break
                continue
            node.terminal = -1
            winner = -1
            break
        S0 = set()
        S1 = set()
        for code in pmoves:
            if code & 1:
                S1.add(code >> 1)
            else:
                S0.add(code >> 1)
        for idx in range(len(path) - 1, -1, -1):
            nd = path[idx]
            nd.n += 1
            if nd.pl == winner:
                nd.w += 1
            if idx < RAVE_DEPTH:
                tm = nd.pl ^ 1
                S = S0 if tm == 0 else S1
                if S:
                    rv = nd.rave
                    add = (1 << 20) if tm == winner else 0
                    for cell in S:
                        v = rv.get(cell)
                        if v is None:
                            rv[cell] = add | 1
                        else:
                            rv[cell] = v + add + 1
            if nd.move >= 0:
                if nd.pl == 0:
                    S0.add(nd.move)
                else:
                    S1.add(nd.move)


def policy(me, opp, valid_mask):
    global ROOT, ROOT_OWNER, NODE_COUNT
    n = len(valid_mask)
    try:
        valid, NEIGH, CBITS, SBITS, BORDER = analyze(valid_mask)
        nn = n * n
        owner = [0] * nn
        for rc in me:
            owner[rc[0] * n + rc[1]] = 1
        for rc in opp:
            owner[rc[0] * n + rc[1]] = 2
        emp0 = []
        for i in range(nn):
            if valid[i] and owner[i] == 0:
                emp0.append(i)
        if not emp0:
            for i in range(nn):
                if valid[i]:
                    return (i // n, i % n)
            return (0, 0)
        if not me and not opp:
            ROOT = None
            ROOT_OWNER = None
            cen = (n // 2) * n + n // 2
            if valid[cen]:
                return (n // 2, n // 2)
            return (emp0[0] // n, emp0[0] % n)
        par, cm, sm = build_ufs(owner, n, NEIGH, CBITS, SBITS)
        w0 = find_wins(0, owner, emp0, par[0], cm[0], sm[0], NEIGH, CBITS, SBITS, BORDER)
        if w0:
            mv = w0[0]
            ROOT = None
            ROOT_OWNER = None
            return (mv // n, mv % n)
        w1 = find_wins(1, owner, emp0, par[1], cm[1], sm[1], NEIGH, CBITS, SBITS, BORDER)
        if w1:
            mv = w1[0]
            return (mv // n, mv % n)
        newroot = None
        if ROOT is not None and ROOT_OWNER is not None:
            diff = [i for i in range(nn) if owner[i] != ROOT_OWNER[i]]
            if not diff:
                newroot = ROOT
            elif len(diff) == 2 and ROOT_OWNER[diff[0]] == 0 and ROOT_OWNER[diff[1]] == 0:
                a, b = diff
                if owner[a] == 1 and owner[b] == 2:
                    cus, cop = a, b
                elif owner[b] == 1 and owner[a] == 2:
                    cus, cop = b, a
                else:
                    cus = cop = -1
                if cus >= 0:
                    ch = ROOT.children.get(cus)
                    if ch is not None:
                        g = ch.children.get(cop)
                        if g is not None:
                            newroot = g
        ROOT = newroot
        if ROOT is None:
            ROOT = Node(-1, 1)
            NODE_COUNT = 0
        ROOT_OWNER = owner[:]
        t_end = time.perf_counter() + BUDGET
        mcts(ROOT, owner, emp0, par, cm, sm, NEIGH, CBITS, SBITS, BORDER, t_end)
        best = None
        bestn = -1
        bestw = -1
        for mv, ch in ROOT.children.items():
            if ch.terminal == ch.pl:
                return (mv // n, mv % n)
            if ch.n > bestn or (ch.n == bestn and ch.w > bestw):
                best = mv
                bestn = ch.n
                bestw = ch.w
        if best is None:
            best = emp0[random.randrange(len(emp0))]
        return (best // n, best % n)
    except Exception:
        try:
            occ = set()
            for rc in me:
                occ.add((rc[0], rc[1]))
            for rc in opp:
                occ.add((rc[0], rc[1]))
            for r in range(n):
                for c in range(n):
                    if valid_mask[r][c] and (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
    return (0, 0)
