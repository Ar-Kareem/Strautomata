
import math
import random
import time

N = 11
SIZE = N * N
CENTER = (N // 2) * N + (N // 2)


def _build_nei():
    table = []
    for r in range(N):
        for c in range(N):
            ns = []
            if c > 0:
                ns.append(r * N + c - 1)
            if c < N - 1:
                ns.append(r * N + c + 1)
            if r > 0:
                ns.append((r - 1) * N + c)
                if c < N - 1:
                    ns.append((r - 1) * N + c + 1)
            if r < N - 1:
                ns.append((r + 1) * N + c)
                if c > 0:
                    ns.append((r + 1) * N + c - 1)
            table.append(tuple(ns))
    return table


NEI = _build_nei()

# Edge bit masks: black connects row 0 <-> row N-1, white col 0 <-> col N-1.
EBIT_B = [0] * SIZE
EBIT_W = [0] * SIZE
for _r in range(N):
    for _c in range(N):
        _i = _r * N + _c
        if _r == 0:
            EBIT_B[_i] = 1
        elif _r == N - 1:
            EBIT_B[_i] = 2
        if _c == 0:
            EBIT_W[_i] = 1
        elif _c == N - 1:
            EBIT_W[_i] = 2

EXPLORE = 0.30
RAVE_K = 1000.0
RAVE_CAP = 32
LOCAL_P = 0.60
TIME_LIMIT = 0.88


class Node(object):
    __slots__ = ('visits', 'children', 'untried', 'w', 'n', 'rw', 'rv',
                 'player', 'terminal')

    def __init__(self, player, untried):
        self.visits = 0
        self.children = {}   # move -> Node
        self.untried = untried
        self.w = {}          # move -> wins (for self.player)
        self.n = {}          # move -> visits
        self.rw = {}         # move -> RAVE wins
        self.rv = {}         # move -> RAVE visits
        self.player = player
        self.terminal = 0


def build_uf(board):
    """Union-find over cells; mask[root] bits mark which of the two edges
    (of that component's color) the component touches."""
    parent = list(range(SIZE))
    mask = [0] * SIZE

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(SIZE):
        v = board[i]
        if not v:
            continue
        ri = find(i)
        for nb in NEI[i]:
            if board[nb] == v:
                rn = find(nb)
                if rn != ri:
                    parent[rn] = ri
                    mask[ri] |= mask[rn]
        mask[ri] |= EBIT_B[i] if v == 1 else EBIT_W[i]
    return parent, mask


def winning_moves(board, parent, mask, col):
    """Empty cells where placing a `col` stone immediately connects both sides."""
    ebit = EBIT_B if col == 1 else EBIT_W
    res = []

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for m in range(SIZE):
        if board[m]:
            continue
        bits = ebit[m]
        if bits != 3:
            for nb in NEI[m]:
                if board[nb] == col:
                    bits |= mask[find(nb)]
                    if bits == 3:
                        break
        if bits == 3:
            res.append(m)
    return res


def simulate(root, rboard, rparent, rmask, rempties, rwhere, oc):
    board = rboard[:]
    parent = rparent[:]
    mask = rmask[:]
    empties = rempties[:]
    where = rwhere[:]
    nei = NEI
    ebit_b = EBIT_B
    ebit_w = EBIT_W
    xc = 3 - oc

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    node = root
    path = [node]
    edges = []    # (player, move) from tree descent
    pmoves = []   # (player, move) from playout
    winner = 0

    # ---- selection ----
    while True:
        if node.terminal:
            winner = node.terminal
            break
        if node.untried:
            break
        children = node.children
        if not children:
            break
        nvis = node.visits
        logn = math.log(nvis) if nvis > 1 else 0.0
        beta = math.sqrt(RAVE_K / (3.0 * nvis + RAVE_K))
        wd = node.w
        ndn = node.n
        rwd = node.rw
        rvd = node.rv
        best = -1
        bestsc = -1e30
        for m in children:
            nv = ndn.get(m)
            if not nv:
                sc = 1e30
            else:
                q = wd.get(m, 0) / nv
                rvv = rvd.get(m, 0)
                if rvv:
                    q = (1.0 - beta) * q + beta * (rwd.get(m, 0) / rvv)
                sc = q + EXPLORE * math.sqrt(logn / nv)
            if sc > bestsc:
                bestsc = sc
                best = m
        if best < 0:
            break
        m = best
        pl = node.player
        col = oc if pl == 1 else xc
        board[m] = col
        ri = find(m)
        for nb in nei[m]:
            if board[nb] == col:
                rn = find(nb)
                if rn != ri:
                    parent[rn] = ri
                    mask[ri] |= mask[rn]
        mask[ri] |= ebit_b[m] if col == 1 else ebit_w[m]
        ii = where[m]
        e = empties[-1]
        empties[ii] = e
        where[e] = ii
        empties.pop()
        edges.append((pl, m))
        node = children[m]
        path.append(node)
        if mask[ri] == 3:
            winner = pl
            break

    # ---- expansion ----
    if winner == 0 and not node.terminal and node.untried:
        ut = node.untried
        ui = random.randrange(len(ut))
        m = ut[ui]
        ut[ui] = ut[-1]
        ut.pop()
        pl = node.player
        col = oc if pl == 1 else xc
        board[m] = col
        ri = find(m)
        for nb in nei[m]:
            if board[nb] == col:
                rn = find(nb)
                if rn != ri:
                    parent[rn] = ri
                    mask[ri] |= mask[rn]
        mask[ri] |= ebit_b[m] if col == 1 else ebit_w[m]
        ii = where[m]
        e = empties[-1]
        empties[ii] = e
        where[e] = ii
        empties.pop()
        child = Node(3 - pl, list(empties))
        node.children[m] = child
        node.n[m] = 0
        node.w[m] = 0
        edges.append((pl, m))
        path.append(child)
        node = child
        if mask[ri] == 3:
            winner = pl
            child.terminal = pl

    # ---- playout (locally biased random) ----
    if winner == 0:
        pl = node.player
        last = edges[-1][1] if edges else -1
        rnd = random.random
        rrg = random.randrange
        while True:
            L = len(empties)
            if L == 0:
                winner = pl
                break
            m = -1
            if last >= 0 and rnd() < LOCAL_P:
                cands = None
                for nb in nei[last]:
                    if board[nb] == 0:
                        if cands is None:
                            cands = [nb]
                        else:
                            cands.append(nb)
                if cands is not None:
                    m = cands[rrg(len(cands))]
            if m < 0:
                m = empties[rrg(L)]
            col = oc if pl == 1 else xc
            board[m] = col
            ri = find(m)
            for nb in nei[m]:
                if board[nb] == col:
                    rn = find(nb)
                    if rn != ri:
                        parent[rn] = ri
                        mask[ri] |= mask[rn]
            mask[ri] |= ebit_b[m] if col == 1 else ebit_w[m]
            ii = where[m]
            e = empties[-1]
            empties[ii] = e
            where[e] = ii
            empties.pop()
            pmoves.append((pl, m))
            if mask[ri] == 3:
                winner = pl
                break
            last = m
            pl = 3 - pl

    # ---- backpropagation (UCT + RAVE) ----
    le = len(edges)
    npm = len(pmoves)
    for i in range(len(path) - 1, -1, -1):
        nd = path[i]
        nd.visits += 1
        pl = nd.player
        if i < le:
            p, m = edges[i]
            ndn = nd.n
            ndn[m] = ndn.get(m, 0) + 1
            if p == winner:
                ndw = nd.w
                ndw[m] = ndw.get(m, 0) + 1
        rvd = nd.rv
        rwd = nd.rw
        cnt = 0
        for j in range(i, le):
            p2, m2 = edges[j]
            if p2 == pl:
                rvd[m2] = rvd.get(m2, 0) + 1
                if p2 == winner:
                    rwd[m2] = rwd.get(m2, 0) + 1
                cnt += 1
                if cnt >= RAVE_CAP:
                    break
        if cnt < RAVE_CAP:
            for k in range(npm):
                p2, m2 = pmoves[k]
                if p2 == pl:
                    rvd[m2] = rvd.get(m2, 0) + 1
                    if p2 == winner:
                        rwd[m2] = rwd.get(m2, 0) + 1
                    cnt += 1
                    if cnt >= RAVE_CAP:
                        break


G_ROOT = None
G_BOARD = None
G_COLOR = None


def policy(me, opp, color):
    global G_ROOT, G_BOARD, G_COLOR
    try:
        t0 = time.perf_counter()
        deadline = t0 + TIME_LIMIT
        oc = 1 if color in ('b', 'B') else 2
        xc = 3 - oc
        board = [0] * SIZE
        for rc in me:
            board[rc[0] * N + rc[1]] = oc
        for rc in opp:
            board[rc[0] * N + rc[1]] = xc
        empties = [i for i in range(SIZE) if board[i] == 0]
        if not empties:
            return (0, 0)
        if len(empties) == 1:
            G_ROOT = None
            G_BOARD = None
            G_COLOR = color
            m = empties[0]
            return (m // N, m % N)
        # Opening: grab the center.
        if len(me) + len(opp) <= 2 and board[CENTER] == 0:
            G_ROOT = None
            G_BOARD = None
            G_COLOR = color
            return (CENTER // N, CENTER % N)

        parent, mask = build_uf(board)

        # Immediate win.
        wm = winning_moves(board, parent, mask, oc)
        if wm:
            G_ROOT = None
            G_BOARD = None
            G_COLOR = color
            m = wm[0]
            return (m // N, m % N)
        # Forced block of a unique immediate threat.
        bm = winning_moves(board, parent, mask, xc)
        if len(bm) == 1:
            G_ROOT = None
            G_BOARD = None
            G_COLOR = color
            m = bm[0]
            return (m // N, m % N)

        # Try to reuse the subtree from our previous search.
        root = None
        if G_ROOT is not None and G_BOARD is not None and G_COLOR == color:
            gb = G_BOARD
            diff = 0
            dm = -1
            ok = True
            for i in range(SIZE):
                a = board[i]
                b = gb[i]
                if a != b:
                    if b == 0 and a == xc:
                        diff += 1
                        dm = i
                    else:
                        ok = False
                        break
            if ok and diff == 1:
                ch = G_ROOT.children.get(dm)
                if ch is not None and not ch.terminal and ch.player == 1:
                    root = ch
        if root is None:
            root = Node(1, list(empties))

        where = [0] * SIZE
        for idx in range(len(empties)):
            where[empties[idx]] = idx

        sims = 0
        while True:
            simulate(root, board, parent, mask, empties, where, oc)
            sims += 1
            if (sims & 31) == 0 and time.perf_counter() >= deadline:
                break

        # Robust choice: most visited child, ties by win rate.
        best_m = -1
        best_n = -1
        best_q = -1.0
        ndn = root.n
        wd = root.w
        for m in root.children:
            nv = ndn.get(m, 0)
            if nv > best_n:
                best_n = nv
                best_m = m
                best_q = (wd.get(m, 0) / nv) if nv else 0.0
            elif nv == best_n and nv > 0:
                q = wd.get(m, 0) / nv
                if q > best_q:
                    best_q = q
                    best_m = m
        if best_m < 0:
            best_m = empties[random.randrange(len(empties))]

        child = root.children.get(best_m)
        if child is not None and not child.terminal:
            G_ROOT = child
            nb2 = board[:]
            nb2[best_m] = oc
            G_BOARD = nb2
            G_COLOR = color
        else:
            G_ROOT = None
            G_BOARD = None
            G_COLOR = color
        return (best_m // N, best_m % N)
    except Exception:
        # Never return an illegal move.
        try:
            occ = set(me) | set(opp)
            for r in range(N):
                for c in range(N):
                    if (r, c) not in occ:
                        return (r, c)
        except Exception:
            pass
    return (0, 0)
