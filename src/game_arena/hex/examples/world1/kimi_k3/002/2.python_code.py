
import time
import math
import random

random.seed(0xC0FFEE)

N = 11
NN = N * N
BLACK = 1
WHITE = 2


def _precompute():
    neigh = []
    rc = []
    for i in range(NN):
        r, c = divmod(i, N)
        rc.append((r, c))
        ns = []
        for dr, dc in ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                ns.append(rr * N + cc)
        neigh.append(tuple(ns))
    # Bridge patterns: (endpoint offset, carrier1 offset, carrier2 offset)
    bridges = (
        ((-1, -1), (-1, 0), (0, -1)),
        ((1, 1), (1, 0), (0, 1)),
        ((-2, 1), (-1, 0), (-1, 1)),
        ((2, -1), (1, 0), (1, -1)),
        ((-1, 2), (0, 1), (-1, 1)),
        ((1, -2), (0, -1), (1, -1)),
    )
    carrier = [[] for _ in range(NN)]
    for i in range(NN):
        r, c = rc[i]
        for (bdr, bdc), (x1, y1), (x2, y2) in bridges:
            br, bc = r + bdr, c + bdc
            a1, b1 = r + x1, c + y1
            a2, b2 = r + x2, c + y2
            if (0 <= br < N and 0 <= bc < N and 0 <= a1 < N and 0 <= b1 < N
                    and 0 <= a2 < N and 0 <= b2 < N):
                b = br * N + bc
                i1 = a1 * N + b1
                i2 = a2 * N + b2
                carrier[i1].append((i, b, i2))
                carrier[i2].append((i, b, i1))
    return neigh, rc, tuple(tuple(x) for x in carrier)


NEIGH, RC, CARRIER = _precompute()


def _find(p, x):
    while p[x] != x:
        p[x] = p[p[x]]
        x = p[x]
    return x


def _union(p, s, a, b):
    a = _find(p, a)
    b = _find(p, b)
    if a != b:
        if s[a] < s[b]:
            a, b = b, a
        p[b] = a
        s[a] += s[b]


def _apply(cells, ufb, szb, ufw, szw, empties, pos, m, color):
    """Place `color` at m, update structures; return True if it wins."""
    cells[m] = color
    if color == BLACK:
        uf, sz = ufb, szb
        r = m // N
        if r == 0:
            _union(uf, sz, m, NN)
        elif r == N - 1:
            _union(uf, sz, m, NN + 1)
    else:
        uf, sz = ufw, szw
        cc = m % N
        if cc == 0:
            _union(uf, sz, m, NN)
        elif cc == N - 1:
            _union(uf, sz, m, NN + 1)
    for n in NEIGH[m]:
        if cells[n] == color:
            _union(uf, sz, m, n)
    i = pos[m]
    l = empties[-1]
    empties[i] = l
    pos[l] = i
    empties.pop()
    pos[m] = -1
    return _find(uf, NN) == _find(uf, NN + 1)


def _simulate(cells, ufb, szb, ufw, szw, empties, pos, tm, seq):
    """Random playout with bridge-defense and locality bias. Returns winner."""
    last = seq[-1] if seq else -1
    rand = random.random
    rr = random.randrange
    car = CARRIER
    nei = NEIGH
    while empties:
        m = -1
        if last >= 0:
            cand = -1
            for (a, b, o) in car[last]:
                if cells[o] == 0 and cells[a] == tm and cells[b] == tm:
                    if cand < 0 or rr(2):
                        cand = o
            if cand >= 0:
                m = cand
            elif rand() < 0.35:
                nbs = nei[last]
                n = nbs[rr(len(nbs))]
                if cells[n] == 0:
                    m = n
        if m < 0:
            m = empties[rr(len(empties))]
        won = _apply(cells, ufb, szb, ufw, szw, empties, pos, m, tm)
        seq.append(m)
        if won:
            return tm
        last = m
        tm = 3 - tm
    return 0


def _ordered(cells, empties, my, oc):
    """Order empty moves heuristically (best at END of returned list)."""
    scored = []
    car = CARRIER
    nei = NEIGH
    for e in empties:
        s = 0.0
        for n in nei[e]:
            v = cells[n]
            if v == my:
                s += 3.0
            elif v == oc:
                s += 2.0
        for (a, b, o) in car[e]:
            va = cells[a]
            if va != 0 and va == cells[b]:
                vo = cells[o]
                if va == my:
                    s += 6.0 if vo == oc else 2.0
                else:
                    s += 2.0 if vo == 0 else 1.0
        r, c = RC[e]
        s -= (abs(r - 5) + abs(c - 5)) * 0.01
        scored.append((s, e))
    scored.sort()
    return [e for _, e in scored]


def _winning_moves(cells, uf, empties, color):
    """Empty cells where `color` wins immediately by playing there."""
    rt = _find(uf, NN)
    rb = _find(uf, NN + 1)
    if rt == rb:
        return []
    res = []
    isb = color == BLACK
    for e in empties:
        if isb:
            hit_t = e < N
            hit_b = e >= NN - N
        else:
            hit_t = (e % N == 0)
            hit_b = (e % N == N - 1)
        for n in NEIGH[e]:
            if cells[n] == color:
                rep = _find(uf, n)
                if rep == rt:
                    hit_t = True
                elif rep == rb:
                    hit_b = True
        if hit_t and hit_b:
            res.append(e)
    return res


class Node:
    __slots__ = ('move', 'to_move', 'visits', 'wins', 'children',
                 'untried', 'rave', 'winner')

    def __init__(self, move, to_move, winner=0):
        self.move = move
        self.to_move = to_move
        self.visits = 0
        self.wins = 0
        self.children = {}
        self.untried = None
        self.rave = {}
        self.winner = winner


SAVE = None
RAVE_K = 500.0
RAVE_DEPTH = 12
CE = 0.30
BUDGET = 0.85


def policy(me, opp, color):
    try:
        mv = _policy(me, opp, color)
        occ = set(map(tuple, me)) | set(map(tuple, opp))
        r, c = mv
        if 0 <= r < N and 0 <= c < N and (r, c) not in occ:
            return mv
    except Exception:
        pass
    occ = set(map(tuple, me)) | set(map(tuple, opp))
    cells_order = sorted(
        ((r, c) for r in range(N) for c in range(N)),
        key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))
    for rc in cells_order:
        if rc not in occ:
            return rc
    return (0, 0)


def _policy(me, opp, color):
    global SAVE
    my = BLACK if color == 'b' else WHITE
    oc = 3 - my

    cells = [0] * NN
    for (r, c) in me:
        cells[r * N + c] = my
    for (r, c) in opp:
        cells[r * N + c] = oc

    ufb = list(range(NN + 2))
    szb = [1] * (NN + 2)
    ufw = list(range(NN + 2))
    szw = [1] * (NN + 2)
    for i in range(NN):
        v = cells[i]
        if v:
            if v == BLACK:
                uf, sz = ufb, szb
                if i < N:
                    _union(uf, sz, i, NN)
                elif i >= NN - N:
                    _union(uf, sz, i, NN + 1)
            else:
                uf, sz = ufw, szw
                cm = i % N
                if cm == 0:
                    _union(uf, sz, i, NN)
                elif cm == N - 1:
                    _union(uf, sz, i, NN + 1)
            for n in NEIGH[i]:
                if cells[n] == v:
                    _union(uf, sz, i, n)

    empties = [i for i in range(NN) if cells[i] == 0]
    if not empties:
        return (0, 0)
    pos = [-1] * NN
    for k, e in enumerate(empties):
        pos[e] = k
    if len(empties) == 1:
        SAVE = None
        return RC[empties[0]]

    uf_my = ufb if my == BLACK else ufw
    uf_op = ufw if my == BLACK else ufb

    # Immediate win
    wm = _winning_moves(cells, uf_my, empties, my)
    if wm:
        SAVE = None
        return RC[wm[0]]
    # Immediate block
    bm = _winning_moves(cells, uf_op, empties, oc)
    if bm:
        SAVE = None
        return RC[bm[0]]

    # Opening
    if not me:
        SAVE = None
        for cand in ((5, 5), (4, 5), (5, 4), (4, 6), (5, 6), (6, 5), (6, 4)):
            if cells[cand[0] * N + cand[1]] == 0:
                return cand

    # Try to reuse previous search tree
    root = None
    if SAVE is not None:
        try:
            snode, scells, scol = SAVE
            if scol == color:
                diff = -1
                ok = True
                for i in range(NN):
                    sv = scells[i]
                    v = cells[i]
                    if sv == my:
                        if v != my:
                            ok = False
                            break
                    elif sv == oc:
                        if v != oc:
                            ok = False
                            break
                    else:
                        if v == oc:
                            if diff < 0:
                                diff = i
                            else:
                                ok = False
                                break
                        elif v == my:
                            ok = False
                            break
                if ok and diff >= 0:
                    ch = snode.children.get(diff)
                    if ch is None:
                        ch = Node(diff, my)
                        snode.children[diff] = ch
                        if snode.untried and diff in snode.untried:
                            snode.untried.remove(diff)
                    if ch.to_move == my:
                        root = ch
        except Exception:
            root = None
    if root is None:
        root = Node(-1, my)

    sqrt = math.sqrt
    log = math.log
    start = time.time()
    deadline = start + BUDGET
    it = 0

    while True:
        it += 1
        if it > 4 and (it & 15) == 1 and time.time() > deadline:
            break
        c = cells[:]
        ub = ufb[:]
        sb = szb[:]
        uw = ufw[:]
        sw = szw[:]
        em = empties[:]
        ps = pos[:]

        node = root
        tm = my
        path = [node]
        seq = []

        # --- tree descent ---
        while True:
            if node.winner:
                break
            ut = node.untried
            if ut is None:
                ut = _ordered(c, em, tm, 3 - tm)
                node.untried = ut
            if ut:
                m = ut.pop()
                won = _apply(c, ub, sb, uw, sw, em, ps, m, tm)
                ch = node.children.get(m)
                if ch is None:
                    ch = Node(m, 3 - tm, tm if won else 0)
                    node.children[m] = ch
                seq.append(m)
                path.append(ch)
                node = ch
                tm = 3 - tm
                break
            # selection
            V = node.visits
            logV = log(V + 1.0)
            beta = sqrt(RAVE_K / (3.0 * V + RAVE_K))
            omb = 1.0 - beta
            rd = node.rave
            bests = -1e18
            bestm = -1
            bestch = None
            for m2, ch2 in node.children.items():
                cw = ch2.winner
                if cw:
                    sc = 1e9 if cw == tm else -1e9
                else:
                    cn = ch2.visits
                    ex = 1.0 - ch2.wins / cn
                    rv = rd.get(m2)
                    if rv is not None:
                        ex = omb * ex + beta * (rv[0] / rv[1])
                    sc = ex + CE * sqrt(logV / cn)
                if sc > bests:
                    bests = sc
                    bestm = m2
                    bestch = ch2
            if bestch is None:
                break
            _apply(c, ub, sb, uw, sw, em, ps, bestm, tm)
            seq.append(bestm)
            path.append(bestch)
            node = bestch
            tm = 3 - tm
            if node.winner:
                break

        winner = node.winner
        if not winner:
            winner = _simulate(c, ub, sb, uw, sw, em, ps, tm, seq)
        if not winner:
            winner = oc  # cannot happen in Hex; safe default

        # --- backpropagation ---
        for nd in path:
            nd.visits += 1
            if nd.to_move == winner:
                nd.wins += 1
        L = len(seq)
        if L:
            plen = len(path)
            if plen > RAVE_DEPTH:
                plen = RAVE_DEPTH
            for k2 in range(plen):
                nd = path[k2]
                rd = nd.rave
                tw = nd.to_move
                add = 1 if winner == tw else 0
                get = rd.get
                for j in range(k2, L):
                    m3 = seq[j]
                    e2 = get(m3)
                    if e2 is None:
                        rd[m3] = [add, 1]
                    else:
                        e2[0] += add
                        e2[1] += 1

    # --- final move selection: most-visited robust child ---
    best_m = None
    best_key = None
    best_ch = None
    for m, ch in root.children.items():
        if ch.winner == my:
            key = (2, ch.visits, 0.0)
        elif ch.winner == oc:
            key = (0, ch.visits, 0.0)
        else:
            cn = ch.visits
            key = (1, cn, -ch.wins / (cn or 1))
        if best_key is None or key > best_key:
            best_key = key
            best_m = m
            best_ch = ch
    if best_m is None:
        if root.untried:
            best_m = root.untried[-1]
        else:
            best_m = empties[0]
        best_ch = None

    if best_ch is not None:
        cc = cells[:]
        cc[best_m] = my
        SAVE = (best_ch, tuple(cc), color)
    else:
        SAVE = None
    return RC[best_m]
