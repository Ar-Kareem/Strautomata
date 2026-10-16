
import numpy as np
import time

class _Timeout(Exception):
    pass

INF = 10 ** 6
FULL = (1 << 40) - 1


def _hidx(r, c):
    return r * 4 + c


def _vidx(r, c):
    return 20 + r * 5 + c


BOX_EDGES = []
for _r in range(4):
    for _c in range(4):
        BOX_EDGES.append((_hidx(_r, _c), _hidx(_r + 1, _c), _vidx(_r, _c), _vidx(_r, _c + 1)))
_eb = [[] for _ in range(40)]
for _b, _es in enumerate(BOX_EDGES):
    for _e in _es:
        _eb[_e].append(_b)
EDGE_BOXES = [tuple(x) for x in _eb]
EDGE_B0 = [x[0] for x in _eb]
EDGE_B1 = [x[1] if len(x) > 1 else 16 for x in _eb]
EDGE_RC = {}
for _r in range(5):
    for _c in range(4):
        EDGE_RC[_hidx(_r, _c)] = (_r, _c, 'H')
for _r in range(4):
    for _c in range(5):
        EDGE_RC[_vidx(_r, _c)] = (_r, _c, 'V')

_TT = {}


class Solver:
    def __init__(self, mask, counts, deadline, tt):
        self.mask = mask
        self.counts = counts
        self.captured = sum(1 for b in range(16) if counts[b] == 4)
        self.deadline = deadline
        self.tt = tt
        self.nodes = 0
        self.leaf_used = False

    def make(self, e):
        self.mask |= (1 << e)
        counts = self.counts
        gain = 0
        for b in EDGE_BOXES[e]:
            counts[b] += 1
            if counts[b] == 4:
                gain += 1
        self.captured += gain
        return gain

    def unmake(self, e, gain):
        self.mask ^= (1 << e)
        counts = self.counts
        for b in EDGE_BOXES[e]:
            counts[b] -= 1
        self.captured -= gain

    def classify(self):
        mask = self.mask
        counts = self.counts
        capt = []
        safe = []
        unsafe = []
        for e in range(40):
            if (mask >> e) & 1:
                continue
            c0 = counts[EDGE_B0[e]]
            c1 = counts[EDGE_B1[e]]
            m = c0 if c0 > c1 else c1
            if m == 3:
                capt.append(e)
            elif m == 2:
                unsafe.append(e)
            else:
                safe.append(e)
        return capt, safe, unsafe

    def pick_capture(self, capt):
        counts = self.counts
        for e in capt:
            if counts[EDGE_B0[e]] != 2 and counts[EDGE_B1[e]] != 2:
                return e
        return capt[0]

    def all_paired(self):
        mask = self.mask
        counts = self.counts
        for b in range(16):
            if counts[b] == 3:
                for e in BOX_EDGES[b]:
                    if not (mask >> e) & 1:
                        o = EDGE_B0[e]
                        if o == b:
                            o = EDGE_B1[e]
                        if counts[o] != 3:
                            return False
                        break
        return True

    def declines(self, safe, unsafe):
        if self.all_paired():
            cands = unsafe + safe
        else:
            cands = unsafe
        res = []
        for e in cands:
            g = self.make(e)
            if g == 0 and self.all_paired():
                res.append(e)
            self.unmake(e, g)
        return res

    def small_sacrifices(self, unsafe):
        counts = self.counts
        mask = self.mask
        comp = [-1] * 17
        sizes = []
        for b in range(16):
            if counts[b] == 2 and comp[b] < 0:
                cid = len(sizes)
                comp[b] = cid
                stack = [b]
                sz = 0
                while stack:
                    x = stack.pop()
                    sz += 1
                    for e in BOX_EDGES[x]:
                        if (mask >> e) & 1:
                            continue
                        y = EDGE_B0[e]
                        if y == x:
                            y = EDGE_B1[e]
                        if y < 16 and counts[y] == 2 and comp[y] < 0:
                            comp[y] = cid
                            stack.append(y)
                sizes.append(sz)
        res = []
        for e in unsafe:
            ok = True
            for b in (EDGE_B0[e], EDGE_B1[e]):
                if b < 16 and counts[b] == 2 and sizes[comp[b]] > 2:
                    ok = False
            if ok:
                res.append(e)
        return res

    def evaluate(self):
        mask = self.mask
        counts = self.counts
        visited = [False] * 16
        k = 0
        loops = 0
        long_total = 0
        loop_total = 0
        for b in range(16):
            if counts[b] == 2 and not visited[b]:
                visited[b] = True
                stack = [b]
                size = 0
                is_loop = True
                while stack:
                    x = stack.pop()
                    size += 1
                    for e in BOX_EDGES[x]:
                        if (mask >> e) & 1:
                            continue
                        y = EDGE_B0[e]
                        if y == x:
                            y = EDGE_B1[e]
                        if y == 16 or counts[y] != 2:
                            is_loop = False
                        elif not visited[y]:
                            visited[y] = True
                            stack.append(y)
                if is_loop:
                    loops += 1
                    loop_total += size
                elif size >= 3:
                    k += 1
                    long_total += size
        e_rem = 40 - bin(mask).count('1')
        b_rem = 16 - self.captured
        dc = k - 1 if k > 0 else 0
        control = ((e_rem - b_rem + dc) & 1) == 0
        if k > 0:
            gifts = 2 * (k - 1) + 4 * loops
        elif loops > 0:
            gifts = 4 * (loops - 1)
        else:
            gifts = 0
        net = long_total + loop_total - 2 * gifts
        if net < 0:
            net = 0
        val = net + 0.3
        return val if control else -val

    def negamax(self, depth, alpha, beta):
        self.nodes += 1
        if (self.nodes & 127) == 0 and time.time() > self.deadline:
            raise _Timeout()
        mask = self.mask
        if mask == FULL:
            return 0
        ent = self.tt.get(mask)
        if ent is not None and ent[0] >= depth:
            val = ent[1]
            flag = ent[2]
            if flag == 0:
                return val
            if flag == 1:
                if val >= beta:
                    return val
            else:
                if val <= alpha:
                    return val
        capt, safe, unsafe = self.classify()
        exact = not safe
        if capt:
            moves = [self.pick_capture(capt)]
            moves.extend(self.declines(safe, unsafe))
        elif safe:
            if depth <= 0:
                self.leaf_used = True
                return self.evaluate()
            counts = self.counts
            safe.sort(key=lambda e: counts[EDGE_B0[e]] + counts[EDGE_B1[e]])
            moves = safe
            if len(safe) <= 4 and unsafe:
                moves = safe + self.small_sacrifices(unsafe)
        else:
            moves = unsafe
        cost = 0 if exact else 1
        orig_alpha = alpha
        best = -INF
        for e in moves:
            gain = self.make(e)
            if gain:
                v = gain + self.negamax(depth, alpha - gain, beta - gain)
            else:
                v = -self.negamax(depth - cost, -beta, -alpha)
            self.unmake(e, gain)
            if v > best:
                best = v
                if v > alpha:
                    alpha = v
                    if alpha >= beta:
                        break
        if best <= orig_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[mask] = (99 if exact else depth, best, flag)
        return best

    def root_moves(self, undet):
        capt, safe, unsafe = self.classify()
        counts = self.counts
        if capt:
            moves = [self.pick_capture(capt)] + self.declines(safe, unsafe)
        elif safe:
            def key(e):
                r, c, d = EDGE_RC[e]
                pen = 0
                if undet and ((d == 'H' and r == 4) or (d == 'V' and c == 4)):
                    pen = 1
                return (pen, counts[EDGE_B0[e]] + counts[EDGE_B1[e]])
            safe.sort(key=key)
            moves = list(safe)
            if len(safe) <= 4 and unsafe:
                moves += self.small_sacrifices(unsafe)
        else:
            moves = list(unsafe)
        return moves, (not safe)

    def choose(self, start, undet):
        moves, exact_root = self.root_moves(undet)
        if not moves:
            return None
        if len(moves) == 1:
            return moves[0]
        best_move = moves[0]
        depth = 1
        while True:
            self.leaf_used = False
            scores = {}
            alpha = -INF
            beta = INF
            cur_best = None
            cur_val = -INF
            try:
                for e in moves:
                    gain = self.make(e)
                    if gain:
                        v = gain + self.negamax(depth, alpha - gain, beta - gain)
                    else:
                        v = -self.negamax(depth - (0 if exact_root else 1), -beta, -alpha)
                    self.unmake(e, gain)
                    scores[e] = v
                    if v > cur_val:
                        cur_val = v
                        cur_best = e
                    if v > alpha:
                        alpha = v
            except _Timeout:
                break
            best_move = cur_best
            moves.sort(key=lambda e: -scores.get(e, -INF))
            if exact_root or not self.leaf_used:
                break
            if time.time() - start > 0.3:
                break
            depth += 1
            if depth > 60:
                break
        return best_move


def _greedy(solver):
    capt, safe, unsafe = solver.classify()
    if capt:
        return solver.pick_capture(capt)
    if safe:
        return safe[0]
    best = None
    bestg = 99
    for e in unsafe:
        g = solver.make(e)
        seq = []
        total = 0
        while True:
            c2, _, _ = solver.classify()
            if not c2:
                break
            g2 = solver.make(c2[0])
            seq.append((c2[0], g2))
            total += g2
        for (x, gx) in reversed(seq):
            solver.unmake(x, gx)
        solver.unmake(e, g)
        if total < bestg:
            bestg = total
            best = e
    return best


def _name(e, hT, vT):
    r, c, d = EDGE_RC[e]
    if d == 'H':
        if hT:
            return "%d,%d,H" % (c, r)
        return "%d,%d,H" % (r, c)
    else:
        if vT:
            return "%d,%d,V" % (c, r)
        return "%d,%d,V" % (r, c)


def _policy(horizontal, vertical, capture, start):
    global _TT
    H = np.asarray(horizontal)
    V = np.asarray(vertical)
    hT = False
    vT = False
    if H.shape == (5, 5):
        if np.any(H[:, 4] != 0) and not np.any(H[4, :4] != 0):
            hT = True
    if V.shape == (5, 5):
        if np.any(V[4, :] != 0) and not np.any(V[:4, 4] != 0):
            vT = True
    Hm = H.T if hT else H
    Vm = V.T if vT else V
    undet = (not hT) and (not vT) and (not np.any(H[4, :4] != 0)) and (not np.any(V[:4, 4] != 0))

    mask = 0
    for r in range(5):
        for c in range(4):
            if Hm[r, c] != 0:
                mask |= 1 << _hidx(r, c)
    for r in range(4):
        for c in range(5):
            if Vm[r, c] != 0:
                mask |= 1 << _vidx(r, c)
    counts = [0] * 17
    for b in range(16):
        cnt = 0
        for e in BOX_EDGES[b]:
            if (mask >> e) & 1:
                cnt += 1
        counts[b] = cnt

    legal = [e for e in range(40) if not (mask >> e) & 1]
    if not legal:
        return "0,0,H"

    if len(_TT) > 1500000:
        _TT = {}

    deadline = start + 0.8
    solver = Solver(mask, list(counts), deadline, _TT)
    move = None
    try:
        move = solver.choose(start, undet)
    except Exception:
        move = None
    if move is None or (mask >> move) & 1:
        solver2 = Solver(mask, list(counts), start + 5.0, {})
        try:
            move = _greedy(solver2)
        except Exception:
            move = None
    if move is None or (mask >> move) & 1:
        move = legal[0]
    return _name(move, hT, vT)


def policy(horizontal, vertical, capture):
    start = time.time()
    try:
        return _policy(horizontal, vertical, capture, start)
    except Exception:
        H = np.asarray(horizontal)
        V = np.asarray(vertical)
        for r in range(5):
            for c in range(4):
                if H[r, c] == 0:
                    return "%d,%d,H" % (r, c)
        for r in range(4):
            for c in range(5):
                if V[r, c] == 0:
                    return "%d,%d,V" % (r, c)
        return "0,0,H"
