
import time

_LOS = 1000000000
_INF = 1000000000000
_WIN_T = _LOS - 64

_DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
_POSD = (False, True, False, True, False, False, True, True)

# _RAYSP[s] = tuple of (ray_mask, is_increasing) for the 8 directions from s
_RAYSP = []
for _s in range(36):
    _r, _c = divmod(_s, 6)
    _rl = []
    for _d in range(8):
        _dr = _DIRS[_d][0]
        _dc = _DIRS[_d][1]
        _m = 0
        _rr = _r + _dr
        _cc = _c + _dc
        while 0 <= _rr < 6 and 0 <= _cc < 6:
            _m |= 1 << (_rr * 6 + _cc)
            _rr += _dr
            _cc += _dc
        if _m:
            _rl.append((_m, _POSD[_d]))
    _RAYSP.append(tuple(_rl))

_KING = []
for _s in range(36):
    _r, _c = divmod(_s, 6)
    _m = 0
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr != 0 or _dc != 0:
                _rr = _r + _dr
                _cc = _c + _dc
                if 0 <= _rr < 6 and 0 <= _cc < 6:
                    _m |= 1 << (_rr * 6 + _cc)
    _KING.append(_m)

_CENT = tuple(min(_s // 6, 5 - _s // 6) + min(_s % 6, 5 - _s % 6) for _s in range(36))

if hasattr(int, "bit_count"):
    def popcount(x):
        return x.bit_count()
else:
    def popcount(x):
        return bin(x).count("1")


class _TimeUp(Exception):
    pass


def _reach(bits, occ, _R=_RAYSP):
    """Bitmask of squares reachable in one queen move from any bit in bits."""
    res = 0
    while bits:
        lsb = bits & -bits
        bits ^= lsb
        for ray, pos in _R[lsb.bit_length() - 1]:
            bl = ray & occ
            if bl:
                if pos:
                    res |= ray & ((bl & -bl) - 1)
                else:
                    res |= ray & -(1 << bl.bit_length())
            else:
                res |= ray
    return res


def _layers2(t1, occ, _R=_RAYSP):
    """Bitmask of squares reachable within two queen moves (t1 expanded once)."""
    seen = t1
    m = t1
    while m:
        lsb = m & -m
        m ^= lsb
        for ray, pos in _R[lsb.bit_length() - 1]:
            bl = ray & occ
            if bl:
                if pos:
                    seen |= ray & ((bl & -bl) - 1)
                else:
                    seen |= ray & -(1 << bl.bit_length())
            else:
                seen |= ray
    return seen


def _cent(bits, _C=_CENT):
    s = 0
    while bits:
        lsb = bits & -bits
        bits ^= lsb
        s += _C[lsb.bit_length() - 1]
    return s


def _gen_all(p1, occ, _R=_RAYSP):
    """All legal full moves (from, to, arrow) for amazons in p1."""
    out = []
    m = p1
    while m:
        lsb = m & -m
        m ^= lsb
        s = lsb.bit_length() - 1
        base = occ & ~lsb
        for ray, pos in _R[s]:
            bl = ray & occ
            if bl:
                if pos:
                    rch = ray & ((bl & -bl) - 1)
                else:
                    rch = ray & -(1 << bl.bit_length())
            else:
                rch = ray
            rr = rch
            while rr:
                tlsb = rr & -rr
                rr ^= tlsb
                t = tlsb.bit_length() - 1
                occ2 = base | tlsb
                for ray2, pos2 in _R[t]:
                    bl2 = ray2 & occ2
                    if bl2:
                        if pos2:
                            am = ray2 & ((bl2 & -bl2) - 1)
                        else:
                            am = ray2 & -(1 << bl2.bit_length())
                    else:
                        am = ray2
                    aa = am
                    while aa:
                        alsb = aa & -aa
                        aa ^= alsb
                        out.append((s, t, alsb.bit_length() - 1))
    return out


def _gen_cands(pside, pother, occ, t1s, t1o, keep, cap, _R=_RAYSP, _K=_KING):
    """Candidate moves ordered by a cheap blocking heuristic."""
    out = []
    m = pside
    while m:
        lsb = m & -m
        m ^= lsb
        s = lsb.bit_length() - 1
        base = occ & ~lsb
        for ray, pos in _R[s]:
            bl = ray & occ
            if bl:
                if pos:
                    rch = ray & ((bl & -bl) - 1)
                else:
                    rch = ray & -(1 << bl.bit_length())
            else:
                rch = ray
            rr = rch
            while rr:
                tlsb = rr & -rr
                rr ^= tlsb
                t = tlsb.bit_length() - 1
                occ2 = base | tlsb
                arrs = []
                for ray2, pos2 in _R[t]:
                    bl2 = ray2 & occ2
                    if bl2:
                        if pos2:
                            am = ray2 & ((bl2 & -bl2) - 1)
                        else:
                            am = ray2 & -(1 << bl2.bit_length())
                    else:
                        am = ray2
                    aa = am
                    while aa:
                        alsb = aa & -aa
                        aa ^= alsb
                        h = 0
                        if alsb & t1o:
                            h += 8
                        if _K[alsb.bit_length() - 1] & pother:
                            h += 6
                        if alsb & t1s:
                            h -= 4
                        arrs.append((h, alsb))
                nar = len(arrs)
                if not nar:
                    continue
                if keep is not None and nar > keep:
                    arrs.sort(reverse=True)
                    del arrs[keep:]
                db = nar if nar < 14 else 14
                for h, alsb in arrs:
                    out.append((h * 4 + db, s, t, alsb.bit_length() - 1))
    out.sort(reverse=True)
    if cap is not None and len(out) > cap:
        del out[cap:]
    return out


def _board_vals(board):
    vals = None
    try:
        vals = []
        for r in range(6):
            row = board[r]
            for c in range(6):
                vals.append(int(row[c]))
        if len(vals) != 36:
            vals = None
    except Exception:
        vals = None
    if vals is None:
        try:
            vals = [int(board[i]) for i in range(36)]
        except Exception:
            vals = None
    return vals


def _is_legal(board, mv):
    """Independent legality check (separate from the search engine)."""
    try:
        if mv is None:
            return False
        f, t, a = mv
        if f < 0 or f > 35 or t < 0 or t > 35 or a < 0 or a > 35:
            return False
        vals = _board_vals(board)
        if vals is None:
            return False
        if vals[f] != 1:
            return False
        if f == t or t == a:
            return False
        fr, fc = divmod(f, 6)
        tr, tc = divmod(t, 6)
        if not (fr == tr or fc == tc or abs(fr - tr) == abs(fc - tc)):
            return False
        sr = (tr > fr) - (tr < fr)
        sc = (tc > fc) - (tc < fc)
        rr = fr + sr
        cc = fc + sc
        while rr != tr or cc != tc:
            if vals[rr * 6 + cc] != 0:
                return False
            rr += sr
            cc += sc
        if vals[t] != 0:
            return False
        vals[f] = 0
        vals[t] = 1
        if vals[a] != 0:
            return False
        ar, ac = divmod(a, 6)
        if not (tr == ar or tc == ac or abs(tr - ar) == abs(tc - ac)):
            return False
        sr = (ar > tr) - (ar < tr)
        sc = (ac > tc) - (ac < tc)
        rr = tr + sr
        cc = tc + sc
        while rr != ar or cc != ac:
            if vals[rr * 6 + cc] != 0:
                return False
            rr += sr
            cc += sc
        return True
    except Exception:
        return False


def _qt(vals, s):
    res = []
    r, c = divmod(s, 6)
    for dr, dc in _DIRS:
        rr = r + dr
        cc = c + dc
        while 0 <= rr < 6 and 0 <= cc < 6 and vals[rr * 6 + cc] == 0:
            res.append(rr * 6 + cc)
            rr += dr
            cc += dc
    return res


def _fallback_move(board):
    vals = _board_vals(board)
    if vals is None:
        return None
    for f in range(36):
        if vals[f] != 1:
            continue
        for t in _qt(vals, f):
            vals[f] = 0
            vals[t] = 1
            arrows = _qt(vals, t)
            vals[t] = 0
            vals[f] = 1
            if arrows:
                return (f, t, arrows[0])
    return None


class _Engine(object):
    def __init__(self, board, t0, deadline):
        vals = _board_vals(board)
        p1 = 0
        p2 = 0
        occ = 0
        if vals is not None:
            for i in range(36):
                v = vals[i]
                if v == 1:
                    p1 |= 1 << i
                    occ |= 1 << i
                elif v == 2:
                    p2 |= 1 << i
                    occ |= 1 << i
                elif v != 0:
                    occ |= 1 << i
        self.p1 = p1
        self.p2 = p2
        self.occ = occ
        self.t0 = t0
        self.deadline = deadline
        self.nodes = 0

    def search(self, depth, side, alpha, beta, ply):
        self.nodes += 1
        if not (self.nodes & 7) and time.perf_counter() > self.deadline:
            raise _TimeUp()
        if side == 1:
            pb = self.p1
            ob = self.p2
        else:
            pb = self.p2
            ob = self.p1
        occ = self.occ
        t1s = _reach(pb, occ)
        if not t1s:
            return -(_LOS - ply)  # side to move cannot move -> loses
        t1o = _reach(ob, occ)
        if depth <= 0:
            sc = (popcount(t1s) - popcount(t1o)) * 10
            if not t1o:
                sc += 1000
            return sc + _cent(pb) - _cent(ob)
        ms = popcount(t1s)
        if ms <= 10:
            keep = None
        else:
            keep = 2 if ply <= 2 else 1
        if ply == 1:
            cap = 28
        elif ply == 2:
            cap = 16
        elif ply == 3:
            cap = 12
        else:
            cap = 8
        moves = _gen_cands(pb, ob, occ, t1s, t1o, keep, cap)
        best = -_INF
        for h, f, t, a in moves:
            fb = 1 << f
            tb = 1 << t
            ab = 1 << a
            self.occ = (occ & ~fb) | tb | ab
            if side == 1:
                self.p1 = (pb & ~fb) | tb
            else:
                self.p2 = (pb & ~fb) | tb
            v = -self.search(depth - 1, 3 - side, -beta, -alpha, ply + 1)
            self.occ = (self.occ & ~(tb | ab)) | fb
            if side == 1:
                self.p1 = (self.p1 & ~tb) | fb
            else:
                self.p2 = (self.p2 & ~tb) | fb
            if v > best:
                best = v
                if v > alpha:
                    alpha = v
                    if alpha >= beta:
                        break
        if best == -_INF:
            return -(_LOS - ply)
        return best

    def run(self):
        t0 = self.t0
        now = time.perf_counter
        moves_all = _gen_all(self.p1, self.occ)
        if not moves_all:
            return None
        if len(moves_all) == 1:
            return moves_all[0]
        p2b = self.p2

        # ---------- Phase A: score every move (1-move territory) ----------
        scored = []
        n = 0
        for mv in moves_all:
            f, t, a = mv
            fb = 1 << f
            tb = 1 << t
            ab = 1 << a
            self.occ = (self.occ & ~fb) | tb | ab
            self.p1 = (self.p1 & ~fb) | tb
            t2m = _reach(p2b, self.occ)
            if not t2m:
                # opponent has no reply at all: immediate win
                self.occ = (self.occ & ~(tb | ab)) | fb
                self.p1 = (self.p1 & ~tb) | fb
                return mv
            t1m = _reach(self.p1, self.occ)
            m1 = popcount(t1m)
            sc = (m1 - popcount(t2m)) * 10 + _cent(self.p1) - _cent(p2b)
            if m1 == 0:
                sc -= 1000
            self.occ = (self.occ & ~(tb | ab)) | fb
            self.p1 = (self.p1 & ~tb) | fb
            scored.append((sc, f, t, a))
            n += 1
            if not (n & 15) and now() > self.deadline:
                break
        if not scored:
            return moves_all[0]
        scored.sort(reverse=True)

        # ---------- diverse pool of best moves ----------
        cnt = {}
        pool = []
        rest = []
        for it in scored:
            key = (it[1], it[2])
            c = cnt.get(key, 0)
            if c < 6 and len(pool) < 150:
                cnt[key] = c + 1
                pool.append(it)
            else:
                rest.append(it)

        # ---------- Phase A2: rescore pool with 2-move territory ----------
        pool2 = []
        n = 0
        for it in pool:
            f = it[1]
            t = it[2]
            a = it[3]
            fb = 1 << f
            tb = 1 << t
            ab = 1 << a
            self.occ = (self.occ & ~fb) | tb | ab
            self.p1 = (self.p1 & ~fb) | tb
            t2m = _reach(p2b, self.occ)
            t1m = _reach(self.p1, self.occ)
            m1 = popcount(t1m)
            m2 = popcount(t2m)
            sc = (m1 - m2) * 10
            sc += (popcount(_layers2(t1m, self.occ)) -
                   popcount(_layers2(t2m, self.occ))) * 2
            sc += _cent(self.p1) - _cent(p2b)
            if m1 == 0:
                sc -= 1000
            self.occ = (self.occ & ~(tb | ab)) | fb
            self.p1 = (self.p1 & ~tb) | fb
            pool2.append((sc, f, t, a))
            n += 1
            if not (n & 7) and now() > self.deadline:
                break
        pool2.sort(reverse=True)
        done = set((it[1], it[2], it[3]) for it in pool2)
        missed = [(it[1], it[2], it[3]) for it in pool
                  if (it[1], it[2], it[3]) not in done]
        order = ([(it[1], it[2], it[3]) for it in pool2] + missed +
                 [(it[1], it[2], it[3]) for it in rest])
        best = order[0]

        # ---------- Phase B: depth-2 verification walk ----------
        if now() < self.deadline - 0.005:
            vals = {}
            alpha = -_INF
            keys = set((mv[0], mv[1]) for mv in order)
            nk = len(keys)
            pf = 3
            if nk:
                q = 180 // nk
                if q > pf:
                    pf = q
            cnt = {}
            processed = 0
            soft = t0 + 0.42
            try:
                for mv in order:
                    key = (mv[0], mv[1])
                    c = cnt.get(key, 0)
                    if c >= pf:
                        continue
                    cnt[key] = c + 1
                    f, t, a = mv
                    fb = 1 << f
                    tb = 1 << t
                    ab = 1 << a
                    self.occ = (self.occ & ~fb) | tb | ab
                    self.p1 = (self.p1 & ~fb) | tb
                    v = -self.search(1, 2, -_INF, -alpha, 1)
                    self.occ = (self.occ & ~(tb | ab)) | fb
                    self.p1 = (self.p1 & ~tb) | fb
                    vals[mv] = v
                    if v > alpha:
                        alpha = v
                        best = mv
                        if v >= _WIN_T:
                            return mv
                    processed += 1
                    if processed >= 180 or now() > soft:
                        break
            except _TimeUp:
                return best
            if vals:
                bs = sorted(vals.keys(), key=lambda x: vals[x], reverse=True)
                order = bs + [mv for mv in order if mv not in vals]

        # ---------- Phases C..F: deeper beam searches ----------
        specs = ((3, 16, 0.58), (4, 10, 0.67), (5, 8, 0.70), (6, 6, 0.715))
        for depth, k, capf in specs:
            if now() > self.deadline - 0.005:
                break
            keys = set((mv[0], mv[1]) for mv in order)
            nk = len(keys)
            pf = 2
            if nk:
                q = -(-k // nk)
                if q > pf:
                    pf = q
            cnt = {}
            beam = []
            for mv in order:
                key = (mv[0], mv[1])
                c = cnt.get(key, 0)
                if c >= pf:
                    continue
                cnt[key] = c + 1
                beam.append(mv)
                if len(beam) >= k:
                    break
            if not beam:
                break
            alpha = -_INF
            vals2 = {}
            soft = t0 + capf
            try:
                for mv in beam:
                    f, t, a = mv
                    fb = 1 << f
                    tb = 1 << t
                    ab = 1 << a
                    self.occ = (self.occ & ~fb) | tb | ab
                    self.p1 = (self.p1 & ~fb) | tb
                    v = -self.search(depth - 1, 2, -_INF, -alpha, 1)
                    self.occ = (self.occ & ~(tb | ab)) | fb
                    self.p1 = (self.p1 & ~tb) | fb
                    vals2[mv] = v
                    if v > alpha:
                        alpha = v
                        best = mv
                        if v >= _WIN_T:
                            return mv
                    if now() > soft:
                        break
            except _TimeUp:
                return best
            if vals2:
                bs = sorted(vals2.keys(), key=lambda x: vals2[x], reverse=True)
                order = bs + [mv for mv in order if mv not in vals2]
        return best


def _fmt(mv):
    f, t, a = mv
    return "%d,%d:%d,%d:%d,%d" % (f // 6, f % 6, t // 6, t % 6, a // 6, a % 6)


def policy(board):
    t0 = time.perf_counter()
    try:
        eng = _Engine(board, t0, t0 + 0.72)
        mv = eng.run()
        if mv is not None and _is_legal(board, mv):
            return _fmt(mv)
    except Exception:
        pass
    try:
        mv2 = _fallback_move(board)
        if mv2 is not None:
            return _fmt(mv2)
    except Exception:
        pass
    return "0,1:1,1:1,2"
