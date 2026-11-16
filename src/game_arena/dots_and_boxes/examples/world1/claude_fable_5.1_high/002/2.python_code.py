
import numpy as np
import time

INF = 10 ** 9
EXACT_DEPTH = 1000

if hasattr(int, "bit_count"):
    def bc(x):
        return x.bit_count()
else:
    def bc(x):
        return bin(x).count("1")

# Internal indexing: H(r,c) r in 0..4, c in 0..3 ; V(r,c) r in 0..3, c in 0..4
H_IDX = [[r * 4 + c for c in range(4)] for r in range(5)]
V_IDX = [[20 + r * 5 + c for c in range(5)] for r in range(4)]
EDGE_RC = [None] * 40
for r in range(5):
    for c in range(4):
        EDGE_RC[H_IDX[r][c]] = ('H', r, c)
for r in range(4):
    for c in range(5):
        EDGE_RC[V_IDX[r][c]] = ('V', r, c)

BOX_EDGES = []
BOX_MASK = []
EDGE_BOXES = [[] for _ in range(40)]
for r in range(4):
    for c in range(4):
        es = [H_IDX[r][c], H_IDX[r + 1][c], V_IDX[r][c], V_IDX[r][c + 1]]
        BOX_EDGES.append(es)
        m = 0
        for e in es:
            m |= 1 << e
        BOX_MASK.append(m)
        for e in es:
            EDGE_BOXES[e].append(len(BOX_EDGES) - 1)
FULL = (1 << 40) - 1
EDGE_BIT = [1 << e for e in range(40)]

TT = {}


class Timeout(Exception):
    pass


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.hcount = 0

    def gen_moves(self, mask, sides, depth):
        caps = []
        noncaps = []
        for e in range(40):
            if not (mask & EDGE_BIT[e]):
                g = 0
                for b in EDGE_BOXES[e]:
                    if sides[b] == 3:
                        g += 1
                if g:
                    caps.append((g, e))
                else:
                    noncaps.append(e)
        if caps:
            caps.sort(reverse=True)
            moves = caps
            for e in noncaps:
                adj2 = False
                for b in EDGE_BOXES[e]:
                    if sides[b] == 2:
                        adj2 = True
                        break
                if not adj2:
                    continue
                nm = mask | EDGE_BIT[e]
                ok = True
                for b in range(16):
                    if bc(nm & BOX_MASK[b]) == 3:
                        miss = (BOX_MASK[b] & ~nm).bit_length() - 1
                        ob = -1
                        for y in EDGE_BOXES[miss]:
                            if y != b:
                                ob = y
                        if ob < 0 or bc(nm & BOX_MASK[ob]) != 3:
                            ok = False
                            break
                if ok:
                    moves.append((0, e))
            return moves
        if depth <= 0:
            return None
        safe = []
        unsafe = []
        for e in noncaps:
            k = 0
            for b in EDGE_BOXES[e]:
                if sides[b] == 2:
                    k += 1
            if k:
                unsafe.append((k, e))
            else:
                safe.append((0, e))
        unsafe.sort()
        return safe + [(0, e) for k, e in unsafe]

    def heuristic(self, mask, sides):
        self.hcount += 1
        S = 0
        for e in range(40):
            if not (mask & EDGE_BIT[e]):
                ok = True
                for b in EDGE_BOXES[e]:
                    if sides[b] > 1:
                        ok = False
                        break
                if ok:
                    S += 1
        visited = [False] * 16
        L = 0
        P = 0
        ctrl_total = 0
        for b in range(16):
            if sides[b] == 2 and not visited[b]:
                visited[b] = True
                stack = [b]
                n = 0
                cyc = True
                while stack:
                    x = stack.pop()
                    n += 1
                    nb = 0
                    for e in BOX_EDGES[x]:
                        if not (mask & EDGE_BIT[e]):
                            for y in EDGE_BOXES[e]:
                                if y != x and sides[y] == 2:
                                    nb += 1
                                    if not visited[y]:
                                        visited[y] = True
                                        stack.append(y)
                    if nb < 2:
                        cyc = False
                if cyc:
                    P += 1
                    ctrl_total += n
                elif n >= 3:
                    L += 1
                    ctrl_total += n
        if L + P == 0:
            margin = 0.0
        else:
            margin = ctrl_total - 4 * L - 8 * P + (4 if L > 0 else 8)
            if margin < 0:
                margin = 0.0
        if S == 0:
            return -0.8 * margin
        elif S % 2 == 1:
            return 0.5 * margin
        else:
            return -0.5 * margin

    def negamax(self, mask, depth, alpha, beta):
        if mask == FULL:
            return 0
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()
        ent = TT.get(mask)
        tt_move = -1
        if ent is not None:
            td, tv, tf, tm = ent
            if td >= depth:
                if tf == 0:
                    if td < EXACT_DEPTH:
                        self.hcount += 1
                    return tv
                elif tf == 1:
                    if tv >= beta:
                        if td < EXACT_DEPTH:
                            self.hcount += 1
                        return tv
                else:
                    if tv <= alpha:
                        if td < EXACT_DEPTH:
                            self.hcount += 1
                        return tv
            tt_move = tm
        sides = [bc(mask & bm) for bm in BOX_MASK]
        moves = self.gen_moves(mask, sides, depth)
        if moves is None:
            return self.heuristic(mask, sides)
        if tt_move >= 0:
            for i in range(len(moves)):
                if moves[i][1] == tt_move:
                    if i:
                        mv = moves.pop(i)
                        moves.insert(0, mv)
                    break
        h0 = self.hcount
        best = -INF
        bestmove = -1
        a = alpha
        for g, e in moves:
            nm = mask | EDGE_BIT[e]
            if g:
                v = g + self.negamax(nm, depth, a - g, beta - g)
            else:
                v = -self.negamax(nm, depth - 1, -beta, -a)
            if v > best:
                best = v
                bestmove = e
                if v > a:
                    a = v
                    if a >= beta:
                        break
        if best <= alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        sd = EXACT_DEPTH if self.hcount == h0 else depth
        TT[mask] = (sd, best, flag, bestmove)
        return best


def count_safe(mask, sides):
    S = 0
    for e in range(40):
        if not (mask & EDGE_BIT[e]):
            ok = True
            for b in EDGE_BOXES[e]:
                if sides[b] > 1:
                    ok = False
                    break
            if ok:
                S += 1
    return S


def root_search(mask, deadline):
    S = Searcher(deadline)
    sides = [bc(mask & bm) for bm in BOX_MASK]
    moves = S.gen_moves(mask, sides, 1)
    if not moves:
        return None

    def key(mv):
        g, e = mv
        nm = mask | EDGE_BIT[e]
        ns = [bc(nm & bm) for bm in BOX_MASK]
        k3 = 0
        for b in EDGE_BOXES[e]:
            if ns[b] == 3:
                k3 += 1
        Sp = count_safe(nm, ns)
        return (-g, k3, -Sp, e)

    moves.sort(key=key)
    best_move = moves[0][1]
    if len(moves) == 1:
        return best_move
    depth = 1
    empties = 40 - bc(mask)
    while depth <= empties:
        h0 = S.hcount
        a = -INF
        bm = -1
        try:
            for g, e in moves:
                nm = mask | EDGE_BIT[e]
                if nm == FULL:
                    v = g
                elif g:
                    v = g + S.negamax(nm, depth, a - g, INF)
                else:
                    v = -S.negamax(nm, depth - 1, -INF, -a)
                if v > a:
                    a = v
                    bm = e
        except Timeout:
            break
        if bm >= 0:
            best_move = bm
        if S.hcount == h0:
            break
        depth += 1
        moves.sort(key=lambda mv: 0 if mv[1] == bm else 1)
    return best_move


def lookup(horizontal, vertical, conv, kind, r, c):
    hT, vT = conv
    if kind == 'H':
        return int(horizontal[c, r]) if hT else int(horizontal[r, c])
    else:
        return int(vertical[c, r]) if vT else int(vertical[r, c])


def edge_name(conv, e):
    hT, vT = conv
    kind, r, c = EDGE_RC[e]
    if kind == 'H':
        return ("%d,%d,H" % (c, r)) if hT else ("%d,%d,H" % (r, c))
    else:
        return ("%d,%d,V" % (c, r)) if vT else ("%d,%d,V" % (r, c))


def build_mask(horizontal, vertical, conv):
    mask = 0
    for e in range(40):
        kind, r, c = EDGE_RC[e]
        if lookup(horizontal, vertical, conv, kind, r, c) != 0:
            mask |= EDGE_BIT[e]
    return mask


def convention_violations(horizontal, vertical, capture, conv):
    mask = build_mask(horizontal, vertical, conv)
    viol = 0
    for b in range(16):
        full = (mask & BOX_MASK[b]) == BOX_MASK[b]
        cap = int(capture[b // 4, b % 4]) != 0
        if full != cap:
            viol += 1
    # unaddressed cells should be zero
    hT, vT = conv
    addressedH = set()
    addressedV = set()
    for e in range(40):
        kind, r, c = EDGE_RC[e]
        if kind == 'H':
            addressedH.add((c, r) if hT else (r, c))
        else:
            addressedV.add((c, r) if vT else (r, c))
    for i in range(5):
        for j in range(5):
            if (i, j) not in addressedH and int(horizontal[i, j]) != 0:
                viol += 1
            if (i, j) not in addressedV and int(vertical[i, j]) != 0:
                viol += 1
    return viol, mask


def simple_move(mask, conv):
    sides = [bc(mask & bm) for bm in BOX_MASK]
    best = None
    bestkey = None
    for e in range(40):
        if mask & EDGE_BIT[e]:
            continue
        g = 0
        k = 0
        for b in EDGE_BOXES[e]:
            if sides[b] == 3:
                g += 1
            elif sides[b] == 2:
                k += 1
        key = (-g, k, e)
        if bestkey is None or key < bestkey:
            bestkey = key
            best = e
    if best is None:
        return None
    return edge_name(conv, best)


def any_empty(horizontal, vertical):
    for i in range(5):
        for j in range(5):
            if int(horizontal[i, j]) == 0:
                return "%d,%d,H" % (i, j)
    for i in range(5):
        for j in range(5):
            if int(vertical[i, j]) == 0:
                return "%d,%d,V" % (i, j)
    return "0,0,H"


def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    start = time.perf_counter()
    horizontal = np.asarray(horizontal)
    vertical = np.asarray(vertical)
    capture = np.asarray(capture)
    try:
        if len(TT) > 1500000:
            TT.clear()
        convs = [(False, False), (False, True), (True, False), (True, True)]
        best_conv = None
        best_v = None
        best_mask = 0
        for conv in convs:
            v, m = convention_violations(horizontal, vertical, capture, conv)
            if best_v is None or v < best_v:
                best_v = v
                best_conv = conv
                best_mask = m
        conv = best_conv
        mask = best_mask
        if mask == FULL:
            return any_empty(horizontal, vertical)
        deadline = start + 0.6
        move = None
        try:
            move = root_search(mask, deadline)
        except Exception:
            move = None
        if move is None or (mask & EDGE_BIT[move]):
            s = simple_move(mask, conv)
            if s is None:
                return any_empty(horizontal, vertical)
            return s
        name = edge_name(conv, move)
        # final legality check
        parts = name.split(',')
        r, c, d = int(parts[0]), int(parts[1]), parts[2]
        if d == 'H':
            if int(horizontal[r, c]) != 0:
                return any_empty(horizontal, vertical)
        else:
            if int(vertical[r, c]) != 0:
                return any_empty(horizontal, vertical)
        return name
    except Exception:
        return any_empty(horizontal, vertical)
