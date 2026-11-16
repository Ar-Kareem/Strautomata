
import numpy as np
import time

try:
    (1).bit_count()
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')


def _H(r, c):
    return r * 4 + c


def _V(r, c):
    return 20 + r * 5 + c


BOX_EDGES = []
for _i in range(4):
    for _j in range(4):
        BOX_EDGES.append((_H(_i, _j), _H(_i + 1, _j), _V(_i, _j), _V(_i, _j + 1)))
BOXMASK = [(1 << a) | (1 << b) | (1 << c) | (1 << d) for (a, b, c, d) in BOX_EDGES]
_eb = [[] for _ in range(40)]
for _b, _es in enumerate(BOX_EDGES):
    for _e in _es:
        _eb[_e].append(_b)
EDGE_BOXES = [tuple(x) for x in _eb]
FULL = (1 << 40) - 1
INF = 10 ** 9


def edge_to_str(e, transposed):
    if e < 20:
        r, c = divmod(e, 4)
        d = 'H'
    else:
        r, c = divmod(e - 20, 5)
        d = 'V'
    if transposed:
        d = 'V' if d == 'H' else 'H'
    return "%d,%d,%s" % (r, c, d)


def hedge_safe(e):
    if e < 20:
        return e < 16
    return (e - 20) % 5 <= 3


class _Timeout(Exception):
    pass


class Searcher:
    def __init__(self, deadline):
        self.deadline = deadline
        self.tt = {}
        self.nodes = 0
        self.heur = 0
        self.partial = None

    def analyze(self, mask, counts):
        free = FULL & ~mask
        seen = 0
        comps = []
        for b0 in range(16):
            if counts[b0] != 2 or (seen >> b0) & 1:
                continue
            seen |= 1 << b0
            stack = [b0]
            boxes = []
            ground = []
            inner = []
            openend = False
            while stack:
                b = stack.pop()
                boxes.append(b)
                for e in BOX_EDGES[b]:
                    if not (free >> e) & 1:
                        continue
                    obs = EDGE_BOXES[e]
                    if len(obs) == 1:
                        ground.append(e)
                    else:
                        o = obs[1] if obs[0] == b else obs[0]
                        if counts[o] == 2:
                            inner.append(e)
                            if not (seen >> o) & 1:
                                seen |= 1 << o
                                stack.append(o)
                        else:
                            openend = True
            comps.append((boxes, ground, inner, openend))
        return comps

    def gen(self, mask, counts, depth):
        free = FULL & ~mask
        cap_mark = 0
        bad_mark = 0
        for b in range(16):
            c = counts[b]
            if c == 3:
                cap_mark |= BOXMASK[b]
            elif c == 2:
                bad_mark |= BOXMASK[b]
        cap_mark &= free
        safe_mask = free & ~cap_mark & ~bad_mark
        moves = []
        if cap_mark:
            m = cap_mark
            while m:
                lsb = m & -m
                e = lsb.bit_length() - 1
                m ^= lsb
                nc = 0
                for b in EDGE_BOXES[e]:
                    if counts[b] == 3:
                        nc += 1
                moves.append((e, nc, 0))
            dd = 0
            for b in range(16):
                if counts[b] == 3:
                    ubit = BOXMASK[b] & free
                    if not ubit:
                        continue
                    obs = EDGE_BOXES[ubit.bit_length() - 1]
                    if len(obs) == 2:
                        y = obs[1] if obs[0] == b else obs[0]
                        if counts[y] == 2:
                            fbit = (BOXMASK[y] & free) ^ ubit
                            if fbit and not (fbit & cap_mark):
                                dd |= fbit
            while dd:
                lsb = dd & -dd
                e = lsb.bit_length() - 1
                dd ^= lsb
                moves.append((e, 0, 0))
            return moves, None
        comps = self.analyze(mask, counts)
        if safe_mask:
            if depth <= 0 and popcount(safe_mask) > 2:
                return None, comps
            m = safe_mask
            while m:
                lsb = m & -m
                e = lsb.bit_length() - 1
                m ^= lsb
                moves.append((e, 0, 1))
            for boxes, ground, inner, openend in comps:
                if openend:
                    continue
                if ground:
                    moves.append((ground[0], 0, 1))
                    if len(boxes) == 2 and inner:
                        moves.append((inner[0], 0, 1))
                elif inner:
                    moves.append((min(inner), 0, 1))
            return moves, comps
        anyfree = False
        for c in counts:
            if c <= 1:
                anyfree = True
                break
        if anyfree:
            if depth <= 0:
                return None, comps
            m = free
            while m:
                lsb = m & -m
                e = lsb.bit_length() - 1
                m ^= lsb
                moves.append((e, 0, 1))
            return moves, comps
        comps_sorted = sorted(comps, key=lambda cp: len(cp[0]))
        for boxes, ground, inner, openend in comps_sorted:
            if ground:
                if len(boxes) == 2 and inner:
                    moves.append((inner[0], 0, 0))
                moves.append((ground[0], 0, 0))
            elif inner:
                moves.append((min(inner), 0, 0))
        if not moves:
            m = free
            while m:
                lsb = m & -m
                e = lsb.bit_length() - 1
                m ^= lsb
                moves.append((e, 0, 1))
        return moves, comps

    def heuristic(self, mask, counts, comps):
        R = 40 - popcount(mask)
        B = 0
        F = 0
        for c in counts:
            if c < 4:
                B += 1
                if c <= 1:
                    F += 1
        L = 0
        longsum = 0
        loops = 0
        loopsum = 0
        for boxes, ground, inner, openend in comps:
            s = len(boxes)
            if (not openend) and (not ground):
                loops += 1
                loopsum += s
            elif s >= 3:
                L += 1
                longsum += s
        if L >= 1:
            est = longsum + loopsum - 4 * L - 8 * loops + 4
            par = L - 1
        elif loops >= 1:
            est = loopsum - 8 * loops + 8
            par = 0
        else:
            est = 0.5
            par = 0
        if est < 0.75:
            est = 0.75
        mover_ctrl = ((R - B + par) & 1) == 0
        conf = 0.4 + 0.6 * (16 - F) / 16.0
        val = est * conf
        return val if mover_ctrl else -val

    def search(self, mask, counts, depth, alpha, beta):
        if mask == FULL:
            return 0
        self.nodes += 1
        if (self.nodes & 63) == 0 and time.time() > self.deadline:
            raise _Timeout()
        ent = self.tt.get(mask)
        bm = -1
        if ent is not None:
            d, v, flag, bm = ent
            if d >= depth:
                if flag == 0:
                    if d < 100:
                        self.heur += 1
                    return v
                if flag == 1:
                    if v >= beta:
                        if d < 100:
                            self.heur += 1
                        return v
                else:
                    if v <= alpha:
                        if d < 100:
                            self.heur += 1
                        return v
        heur0 = self.heur
        moves, comps = self.gen(mask, counts, depth)
        if moves is None:
            self.heur += 1
            return self.heuristic(mask, counts, comps)
        if bm >= 0:
            for i in range(len(moves)):
                if moves[i][0] == bm:
                    if i:
                        moves.insert(0, moves.pop(i))
                    break
        best = -INF
        bestmove = moves[0][0]
        a0 = alpha
        for e, nc, dec in moves:
            nmask = mask | (1 << e)
            ncounts = counts[:]
            for b in EDGE_BOXES[e]:
                ncounts[b] += 1
            if nc:
                v = nc + self.search(nmask, ncounts, depth, alpha - nc, beta - nc)
            else:
                v = -self.search(nmask, ncounts, depth - dec, -beta, -alpha)
            if v > best:
                best = v
                bestmove = e
                if v > alpha:
                    alpha = v
                    if alpha >= beta:
                        break
        exact = (self.heur == heur0)
        sd = 100 if exact else depth
        if best <= a0:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[mask] = (sd, best, flag, bestmove)
        return best

    def root(self, mask, counts, depth, prev_vals):
        moves, comps = self.gen(mask, counts, max(depth, 1))
        if not moves:
            return None
        if prev_vals:
            moves.sort(key=lambda mv: -prev_vals.get(mv[0], -INF))
        alpha = -INF
        vals = {}
        best = -INF
        bestmove = None
        self.partial = None
        for e, nc, dec in moves:
            nmask = mask | (1 << e)
            ncounts = counts[:]
            for b in EDGE_BOXES[e]:
                ncounts[b] += 1
            a = alpha - 1e-3 if alpha > -INF else -INF
            if nc:
                v = nc + self.search(nmask, ncounts, depth, a - nc, INF)
            else:
                v = -self.search(nmask, ncounts, depth - dec, -INF, -a)
            vals[e] = v
            if v > best:
                best = v
                bestmove = e
                if v > alpha:
                    alpha = v
            self.partial = (best, bestmove, dict(vals))
        return best, bestmove, vals


def _fallback_string(Hm, Vm):
    for r in range(5):
        for c in range(4):
            if Hm[r, c] == 0:
                return "%d,%d,H" % (r, c)
    for r in range(4):
        for c in range(5):
            if Vm[r, c] == 0:
                return "%d,%d,V" % (r, c)
    for r in range(5):
        for c in range(5):
            if Hm[r, c] == 0:
                return "%d,%d,H" % (r, c)
            if Vm[r, c] == 0:
                return "%d,%d,V" % (r, c)
    return "0,0,H"


def policy(horizontal, vertical, capture):
    t0 = time.time()
    deadline = t0 + 0.7
    Hm = np.zeros((5, 5), dtype=int)
    Vm = np.zeros((5, 5), dtype=int)
    try:
        h = np.asarray(horizontal)
        Hm[:min(5, h.shape[0]), :min(5, h.shape[1])] = h[:5, :5]
        v = np.asarray(vertical)
        Vm[:min(5, v.shape[0]), :min(5, v.shape[1])] = v[:5, :5]
    except Exception:
        pass

    std_ev = bool(np.any(Hm[4, :4] != 0) or np.any(Vm[:4, 4] != 0))
    alt_ev = bool(np.any(Hm[:4, 4] != 0) or np.any(Vm[4, :4] != 0))
    transposed = alt_ev and not std_ev
    detected = std_ev or alt_ev
    if transposed:
        Hs, Vs = Vm, Hm
    else:
        Hs, Vs = Hm, Vm

    mask = 0
    for r in range(5):
        for c in range(4):
            if Hs[r, c] != 0:
                mask |= 1 << _H(r, c)
    for r in range(4):
        for c in range(5):
            if Vs[r, c] != 0:
                mask |= 1 << _V(r, c)

    if mask == FULL:
        return _fallback_string(Hm, Vm)

    counts = [popcount(mask & bm) for bm in BOXMASK]
    S = Searcher(deadline)
    final_vals = None
    try:
        prev = None
        for depth in range(1, 64):
            h0 = S.heur
            res = S.root(mask, counts, depth, prev)
            if res is None:
                break
            best, bestmove, vals = res
            final_vals = dict(vals)
            prev = vals
            if S.heur == h0:
                break
    except _Timeout:
        if S.partial is not None and S.partial[1] is not None:
            pbest, pmove, pvals = S.partial
            if final_vals is None:
                final_vals = {}
            for e, vv in pvals.items():
                final_vals[e] = vv
    except Exception:
        pass

    chosen = None
    if final_vals:
        bestkey = None
        for e, v in final_vals.items():
            adj = v
            if (not detected) and (not hedge_safe(e)):
                adj -= 0.5
            mx = 0
            for b in EDGE_BOXES[e]:
                if counts[b] > mx:
                    mx = counts[b]
            key = (adj, -mx, -e)
            if bestkey is None or key > bestkey:
                bestkey = key
                chosen = e

    if chosen is None:
        # quick heuristic fallback
        try:
            moves, comps = S.gen(mask, counts, 1)
        except Exception:
            moves = None
        if moves:
            caps = [m for m in moves if m[1] > 0]
            if caps:
                chosen = caps[0][0]
            else:
                free = FULL & ~mask
                cand = None
                for e, nc, dec in moves:
                    safe = True
                    for b in EDGE_BOXES[e]:
                        if counts[b] == 2:
                            safe = False
                    if safe:
                        cand = e
                        break
                if cand is None:
                    cand = moves[0][0]
                chosen = cand
        else:
            free = FULL & ~mask
            if free:
                chosen = (free & -free).bit_length() - 1

    if chosen is None:
        return _fallback_string(Hm, Vm)

    s = edge_to_str(chosen, transposed)
    try:
        parts = s.split(',')
        r = int(parts[0])
        c = int(parts[1])
        d = parts[2]
        arr = Hm if d == 'H' else Vm
        if 0 <= r < 5 and 0 <= c < 5 and arr[r, c] == 0:
            return s
    except Exception:
        pass
    return _fallback_string(Hm, Vm)
