
import time
import random
from collections import deque

import numpy as np

_INF = 999
_GEOM = None
_GEOM_KEY = None


class _G:
    pass


def _neighbors_for(N, valid, rule):
    """Hex adjacency. rule 1: column parity; rule 2: row parity.
    Odd columns/rows: side neighbours shifted up; even: shifted down."""
    neigh = [()] * (N * N)
    for r in range(N):
        for c in range(N):
            if not valid[r][c]:
                continue
            odd = (c & 1) if rule == 1 else (r & 1)
            if odd:
                offs = ((-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1))
            else:
                offs = ((-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1))
            ns = []
            for dr, dc in offs:
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N and valid[rr][cc]:
                    ns.append(rr * N + cc)
            neigh[r * N + c] = tuple(ns)
    return neigh


def _build(mask):
    g = _G()
    N = mask.shape[0]
    g.N = N
    g.NN = N * N
    valid = [[bool(mask[r][c]) for c in range(N)] for r in range(N)]
    g.valid_list = [r * N + c for r in range(N) for c in range(N) if valid[r][c]]
    border_set_expect = 6 * max(1, (N - 1) // 2 - 1 + 1)  # not used strictly
    # pick the adjacency convention matching a proper hex board
    best_key = None
    best_neigh = None
    n_side = (N + 1) // 2
    exp_edge = 6 * (n_side - 2) if n_side >= 2 else 0
    for rule in (1, 2):
        neigh = _neighbors_for(N, valid, rule)
        degs = [len(neigh[c]) for c in g.valid_list]
        n3 = sum(1 for d in degs if d == 3)
        n4 = sum(1 for d in degs if d == 4)
        n6 = sum(1 for d in degs if d == 6)
        nbad = sum(1 for d in degs if d < 3)
        key = (1 if (n3 == 6 and n4 == exp_edge and nbad == 0) else 0,
               -nbad, n3 == 6, n6)
        key = (key[0], key[1], 1 if n3 == 6 else 0, n6)
        if best_key is None or key > best_key:
            best_key = key
            best_neigh = neigh
    g.neigh = best_neigh
    degs = {c: len(g.neigh[c]) for c in g.valid_list}
    g.border = [c for c in g.valid_list if degs[c] < 6]
    border_set = set(g.border)
    g.corners = [c for c in g.border if degs[c] == min(degs[c2] for c2 in g.border)]
    g.corners = sorted(g.corners)[:6]
    g.corner_mask = [0] * (N * N)
    g.edge_mask = [0] * (N * N)
    g.edges = [[] for _ in range(6)]
    for i, c in enumerate(g.corners):
        g.corner_mask[c] = 1 << i
    g.ok = False
    if len(g.corners) == 6:
        bneigh = {c: [n for n in g.neigh[c] if n in border_set] for c in g.border}
        start = min(g.corners)
        order = []
        prev, cur = -1, start
        for _ in range(len(g.border) + 5):
            order.append(cur)
            nxts = [n for n in bneigh[cur] if n != prev]
            if not nxts:
                break
            nxt = nxts[0]
            if nxt == start:
                break
            prev, cur = cur, nxt
        corner_set = set(g.corners)
        corder = [c for c in order if c in corner_set]
        if len(corder) == 6 and len(order) == len(g.border):
            for i, c in enumerate(corder):
                g.corner_mask[c] = 1 << i
            pos = {c: i for i, c in enumerate(order)}
            cpos = [pos[c] for c in corder]
            L = len(order)
            for k in range(6):
                a, b = cpos[k], cpos[(k + 1) % 6]
                i = (a + 1) % L
                while i != b:
                    cell = order[i]
                    g.edge_mask[cell] = 1 << k
                    g.edges[k].append(cell)
                    i = (i + 1) % L
            g.ok = all(len(e) > 0 for e in g.edges)
    # centrality: BFS distance from border
    g.dist_border = [_INF] * (N * N)
    dq = deque(g.border)
    for c in g.border:
        g.dist_border[c] = 0
    while dq:
        cur = dq.popleft()
        dc = g.dist_border[cur] + 1
        for n in g.neigh[cur]:
            if g.dist_border[n] == _INF:
                g.dist_border[n] = dc
                dq.append(n)
    g.center = max(g.valid_list, key=lambda c: g.dist_border[c])
    g.V = len(g.valid_list)
    return g


def _get_geom(mask):
    global _GEOM, _GEOM_KEY
    key = (mask.shape, mask.tobytes())
    if _GEOM is None or _GEOM_KEY != key:
        _GEOM = _build(mask)
        _GEOM_KEY = key
    return _GEOM


def _check_win(g, board, p, x, pcount):
    """Did player p just win by placing at x? (bridge / fork / ring)"""
    neigh = g.neigh
    seen = {x}
    stack = [x]
    cm = g.corner_mask[x]
    em = g.edge_mask[x]
    while stack:
        cur = stack.pop()
        for n in neigh[cur]:
            if board[n] == p and n not in seen:
                seen.add(n)
                stack.append(n)
                cm |= g.corner_mask[n]
                em |= g.edge_mask[n]
    if bin(cm).count('1') >= 2:
        return True
    if bin(em).count('1') >= 3:
        return True
    # ring, case A: some cell (x or a p-neighbour) is now fully surrounded by p
    fn = 0
    for n in neigh[x]:
        if board[n] == p:
            fn += 1
    seeds = [x] + [n for n in neigh[x] if board[n] == p]
    for s in seeds:
        if len(neigh[s]) == 6:
            ok = True
            for n in neigh[s]:
                if board[n] != p:
                    ok = False
                    break
            if ok:
                return True
    if fn < 2:
        return False
    # ring, case B: flood fill from border over non-p cells; anything unreached is enclosed
    visited = bytearray(g.NN)
    stack2 = []
    for c in g.border:
        if board[c] != p:
            visited[c] = 1
            stack2.append(c)
    cnt = 0
    total = g.V - pcount
    while stack2:
        cur = stack2.pop()
        cnt += 1
        for n in neigh[cur]:
            if not visited[n] and board[n] != p:
                visited[n] = 1
                stack2.append(n)
    return cnt < total


def _pot(g, board, p):
    """0-1 BFS distance transform: cells needed to connect each cell to p's network."""
    dist = [_INF] * g.NN
    dq = deque()
    for c in g.valid_list:
        if board[c] == p:
            dist[c] = 0
            dq.append(c)
    q = 3 - p
    neigh = g.neigh
    app, apl, pop = dq.append, dq.appendleft, dq.popleft
    while dq:
        cur = pop()
        dc = dist[cur]
        for n in neigh[cur]:
            b = board[n]
            if b == q:
                continue
            nd = dc if b == p else dc + 1
            if nd < dist[n]:
                dist[n] = nd
                if b == p:
                    apl(n)
                else:
                    app(n)
    return dist


def _evaluate(g, board):
    d1 = _pot(g, board, 1)
    d2 = _pot(g, board, 2)
    infl = 0
    for c in g.valid_list:
        a, b = d1[c], d2[c]
        if a < b:
            infl += 1
        elif b < a:
            infl -= 1
    if not g.ok:
        return 0.5 * infl
    e1 = sorted(min(min(d1[c] for c in e), 25) for e in g.edges)
    e2 = sorted(min(min(d2[c] for c in e), 25) for e in g.edges)
    f1 = e1[0] + e1[1] + e1[2]
    f2 = e2[0] + e2[1] + e2[2]
    cd1 = sorted(min(d1[c], 25) for c in g.corners)
    cd2 = sorted(min(d2[c], 25) for c in g.corners)
    br1 = cd1[0] + cd1[1]
    br2 = cd2[0] + cd2[1]
    return 12.0 * (f2 - f1) + 10.0 * (br2 - br1) + 0.5 * infl


def _adj_empty(g, board, p):
    s = set()
    for c in g.valid_list:
        if board[c] == p:
            for n in g.neigh[c]:
                if board[n] == 0:
                    s.add(n)
    return s


def _wins_for(g, board, p, cells, pcount):
    res = []
    for x in cells:
        board[x] = p
        if _check_win(g, board, p, x, pcount + 1):
            res.append(x)
        board[x] = 0
    return res


def _quick(g, board, c, p):
    q = 3 - p
    am = ao = 0
    for n in g.neigh[c]:
        b = board[n]
        if b == p:
            am += 1
        elif b == q:
            ao += 1
    s = 5.0 * am + 3.0 * ao + 0.25 * g.dist_border[c]
    if g.edge_mask[c]:
        s += 2.0
    if g.corner_mask[c]:
        s += 1.0
    return s


def _label(g, board, p):
    comp = [-1] * g.NN
    n = 0
    for c in g.valid_list:
        if board[c] == p and comp[c] < 0:
            comp[c] = n
            stack = [c]
            while stack:
                cur = stack.pop()
                for m in g.neigh[cur]:
                    if board[m] == p and comp[m] < 0:
                        comp[m] = n
                        stack.append(m)
            n += 1
    return comp


def policy(me, opp, valid_mask):
    t0 = time.time()
    deadline = t0 + 0.80
    mask = np.asarray(valid_mask, dtype=bool)
    g = _get_geom(mask)
    N = g.N
    board = [0] * g.NN
    for rc in me:
        board[int(rc[0]) * N + int(rc[1])] = 1
    for rc in opp:
        board[int(rc[0]) * N + int(rc[1])] = 2
    counts = [0, len(me), len(opp)]

    def ret(x):
        r, c = divmod(x, N)
        return (int(r), int(c))

    legal = [c for c in g.valid_list if board[c] == 0]
    if not legal:
        return ret(g.valid_list[0])
    if len(legal) == 1:
        return ret(legal[0])
    if counts[1] == 0:
        if board[g.center] == 0:
            return ret(g.center)
        return ret(max(legal, key=lambda c: g.dist_border[c]))

    my_adj = _adj_empty(g, board, 1)
    opp_adj = _adj_empty(g, board, 2)

    # 1. immediate win
    mw = _wins_for(g, board, 1, my_adj, counts[1])
    if mw:
        bestm, bv = mw[0], -1e18
        for m in mw:
            board[m] = 1
            v = _evaluate(g, board)
            board[m] = 0
            if v > bv:
                bv, bestm = v, m
        return ret(bestm)

    # 2. block opponent's immediate wins
    ow = _wins_for(g, board, 2, opp_adj, counts[2])
    if ow:
        bestm, bv = ow[0], -1e18
        for m in ow:
            board[m] = 1
            v = _evaluate(g, board)
            board[m] = 0
            if v > bv:
                bv, bestm = v, m
        return ret(bestm)

    # candidate generation: cells within distance 2 of any stone
    cand = set()
    for c in g.valid_list:
        if board[c] != 0:
            for n in g.neigh[c]:
                if board[n] == 0:
                    cand.add(n)
    if not cand:
        cand = set(legal)
    ext = set(cand)
    for c in cand:
        for n in g.neigh[c]:
            if board[n] == 0:
                ext.add(n)
    cand = ext

    comp1 = _label(g, board, 1)
    comp2 = _label(g, board, 2)

    def rscore(c):
        s = _quick(g, board, c, 1)
        jm = len({comp1[n] for n in g.neigh[c] if board[n] == 1})
        jo = len({comp2[n] for n in g.neigh[c] if board[n] == 2})
        if jm >= 2:
            s += 14.0 * (jm - 1)
        if jo >= 2:
            s += 8.0 * (jo - 1)
        return s

    my_cands = sorted(cand, key=rscore, reverse=True)[:12]
    opp_cands = sorted(cand, key=lambda c: _quick(g, board, c, 2), reverse=True)[:12]

    if time.time() > deadline:
        return ret(my_cands[0] if my_cands else legal[0])

    # 3a. create an unblockable double threat
    my_double = []
    for m in my_cands:
        board[m] = 1
        counts[1] += 1
        if not _wins_for(g, board, 2, _adj_empty(g, board, 2), counts[2]):
            thr = _wins_for(g, board, 1, _adj_empty(g, board, 1), counts[1])
            if len(thr) >= 2:
                my_double.append(m)
        counts[1] -= 1
        board[m] = 0
        if time.time() > deadline:
            break
    if my_double:
        bestm, bv = my_double[0], -1e18
        for m in my_double:
            board[m] = 1
            v = _evaluate(g, board)
            board[m] = 0
            if v > bv:
                bv, bestm = v, m
        return ret(bestm)

    # 3b. prevent opponent's double threat
    opp_double = []
    for o in opp_cands:
        board[o] = 2
        counts[2] += 1
        if not _wins_for(g, board, 1, _adj_empty(g, board, 1), counts[1]):
            ot = _wins_for(g, board, 2, _adj_empty(g, board, 2), counts[2])
            if len(ot) >= 2:
                opp_double.append(o)
        counts[2] -= 1
        board[o] = 0
        if time.time() > deadline:
            break
    if opp_double:
        bestm, bv = opp_double[0], -1e18
        for m in opp_double:
            board[m] = 1
            v = _evaluate(g, board)
            board[m] = 0
            if v > bv:
                bv, bestm = v, m
        return ret(bestm)

    # 4. two-ply minimax with tactical leaf detection
    best = None
    bv = -1e18
    for m in my_cands:
        if time.time() > deadline and best is not None:
            break
        board[m] = 1
        counts[1] += 1
        ow2 = _wins_for(g, board, 2, _adj_empty(g, board, 2), counts[2])
        if ow2:
            v = -1e16
        else:
            oc = _adj_empty(g, board, 2) | _adj_empty(g, board, 1)
            oc = sorted(oc, key=lambda c: _quick(g, board, c, 2), reverse=True)[:8]
            worst = 1e18
            for o in oc:
                board[o] = 2
                counts[2] += 1
                if _check_win(g, board, 2, o, counts[2]):
                    leaf = -1e15
                elif _wins_for(g, board, 1, _adj_empty(g, board, 1), counts[1]):
                    leaf = 1e15
                else:
                    ot = _wins_for(g, board, 2, _adj_empty(g, board, 2), counts[2])
                    if len(ot) >= 2:
                        leaf = -1e14
                    else:
                        leaf = _evaluate(g, board) - 6.0 * len(ot)
                counts[2] -= 1
                board[o] = 0
                if leaf < worst:
                    worst = leaf
                if worst <= bv:
                    break
            v = worst
        counts[1] -= 1
        board[m] = 0
        v += random.random() * 1e-3
        if v > bv:
            bv, best = v, m

    if best is None:
        best = my_cands[0] if my_cands else legal[0]
    return ret(best)
