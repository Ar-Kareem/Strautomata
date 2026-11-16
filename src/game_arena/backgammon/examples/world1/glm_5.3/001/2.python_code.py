
import time

_W = (1.2, 1.2, 1.8, 2.2, 2.8, 2.2,
      2.4, 1.6, 1.2, 1.0, 0.9, 0.8,
      0.7, 0.4, 0.4, 0.4, 0.4, 0.4,
      0.7, 1.0, 1.5, 1.5, 0.9, 0.6)

_ROLLS = tuple([(i, i, 1.0) for i in range(1, 7)] +
               [(i, j, 2.0) for i in range(2, 7) for j in range(1, i)])


def _single_moves(a, b, a_bar, die):
    """Legal single moves for the 23->0 mover.
    Move = (from, dest, hit); from == -1 means bar, dest == -1 means bear off."""
    res = []
    if a_bar:
        dest = 24 - die
        if b[dest] < 2:
            res.append((-1, dest, 1 if b[dest] else 0))
        return res
    home_all = -1
    for p in range(23, -1, -1):
        if not a[p]:
            continue
        dest = p - die
        if dest >= 0:
            if b[dest] < 2:
                res.append((p, dest, 1 if b[dest] else 0))
        else:
            # bear-off attempt (p <= 5)
            if home_all < 0:
                home_all = 1
                for i in range(6, 24):
                    if a[i]:
                        home_all = 0
                        break
            if home_all:
                if die == p + 1:
                    res.append((p, -1, 0))
                else:
                    # overshoot allowed only if no checkers on higher home points
                    ok = 1
                    for i in range(p + 1, 6):
                        if a[i]:
                            ok = 0
                            break
                    if ok:
                        res.append((p, -1, 0))
    return res


def _gen_sequences(a, b, a_bar, b_bar, a_off, hi, lo):
    """All legal 2-die sequences (both orders), deduped by final position.
    Returns (order_char, from1, from2, a', b', a_bar', b_bar', a_off')."""
    seqs = []
    seen = set()
    if hi == lo:
        orders = (('H', hi, lo),)
    else:
        orders = (('H', hi, lo), ('L', lo, hi))
    for och, d1, d2 in orders:
        for m1 in _single_moves(a, b, a_bar, d1):
            f1, e1, h1 = m1
            if f1 < 0:
                ab1 = a_bar - 1
            else:
                a[f1] -= 1
                ab1 = a_bar
            bb1 = b_bar
            ao1 = a_off
            if e1 < 0:
                ao1 = a_off + 1
            else:
                if h1:
                    b[e1] = 0
                    bb1 = b_bar + 1
                a[e1] += 1
            for m2 in _single_moves(a, b, ab1, d2):
                f2, e2, h2 = m2
                if f2 < 0:
                    ab2 = ab1 - 1
                else:
                    a[f2] -= 1
                    ab2 = ab1
                bb2 = bb1
                ao2 = ao1
                if e2 < 0:
                    ao2 = ao1 + 1
                else:
                    if h2:
                        b[e2] = 0
                        bb2 = bb1 + 1
                    a[e2] += 1
                ta = bytes(a)
                tb = bytes(b)
                key = (ta, tb, ab2, bb2, ao2)
                if key not in seen:
                    seen.add(key)
                    seqs.append((och, f1, f2, ta, tb, ab2, bb2, ao2))
                # undo move 2
                if f2 >= 0:
                    a[f2] += 1
                if e2 >= 0:
                    a[e2] -= 1
                    if h2:
                        b[e2] = 1
            # undo move 1
            if f1 >= 0:
                a[f1] += 1
            if e1 >= 0:
                a[e1] -= 1
                if h1:
                    b[e1] = 1
    return seqs


def _single_final(a, b, a_bar, b_bar, a_off, mv):
    f, e, h = mv
    a2 = bytearray(a)
    b2 = bytearray(b)
    if f < 0:
        ab2 = a_bar - 1
    else:
        a2[f] -= 1
        ab2 = a_bar
    bb2 = b_bar
    ao2 = a_off
    if e < 0:
        ao2 = a_off + 1
    else:
        if h:
            b2[e] = 0
            bb2 = b_bar + 1
        a2[e] += 1
    return bytes(a2), bytes(b2), ab2, bb2, ao2


def _side(a, b, a_bar, b_bar, a_off, b_off):
    """Terms for the side that owns 'a' (mover 23->0, home 0..5)."""
    pip = 25 * a_bar
    for i in range(24):
        x = a[i]
        if x:
            pip += x * (i + 1)
    home_made = 0
    opp_home_made = 0
    for i in range(6):
        if a[i] > 1:
            home_made += 1
        if b[23 - i] > 1:
            opp_home_made += 1
    W = _W
    struct = 0.0
    best_prime = 0.0
    run_len = 0
    run_trap = 0
    cumb = b_bar
    for i in range(24):
        if a[i] > 1:
            struct += W[i]
            if run_len == 0:
                run_trap = cumb
            run_len += 1
        else:
            if run_len:
                t = run_trap if run_trap < 12 else 12
                bonus = run_len * t * 0.55
                if bonus > best_prime:
                    best_prime = bonus
                run_len = 0
            cumb += b[i]
    if run_len:
        t = run_trap if run_trap < 12 else 12
        bonus = run_len * t * 0.55
        if bonus > best_prime:
            best_prime = bonus
    tact = 0.0
    # risk of my blots
    for i in range(24):
        if a[i] == 1:
            nd = 0
            for d in range(1, 7):
                j = i - d
                if j >= 0 and b[j]:
                    nd += 1
            if b_bar and i < 6:
                nd += 1
            if nd > 6:
                nd = 6
            p = 1.0 - (6 - nd) * (6 - nd) / 36.0
            ni = 0
            for k in range(7, 13):
                j = i - k
                if j >= 0 and b[j]:
                    ni += 1
            if ni:
                p += (1.0 - p) * 0.055 * (ni if ni < 4 else 4)
                if p > 1.0:
                    p = 1.0
            tact -= 0.85 * p * (28 - i + 2.2 * opp_home_made)
    # value of attacking opponent blots
    for i in range(24):
        if b[i] == 1:
            nd = 0
            for d in range(1, 7):
                j = i + d
                if j < 24 and a[j]:
                    nd += 1
            if a_bar and i > 17:
                nd += 1
            if nd > 6:
                nd = 6
            p = 1.0 - (6 - nd) * (6 - nd) / 36.0
            ni = 0
            for k in range(7, 13):
                j = i + k
                if j < 24 and a[j]:
                    ni += 1
            if ni:
                p += (1.0 - p) * 0.055 * (ni if ni < 4 else 4)
                if p > 1.0:
                    p = 1.0
            tact += 0.85 * p * (5 + i + 2.2 * home_made)
    # mobility lost to opponent blockades
    mob = 0.0
    for i in range(1, 24):
        x = a[i]
        if x:
            lo = i - 6
            if lo < 0:
                lo = 0
            cnt = 0
            for r in range(lo, i):
                if b[r] > 1:
                    cnt += 1
            if cnt:
                mob += 0.15 * x * cnt
    barv = b_bar * (3.5 + 1.8 * home_made) - a_bar * (3.5 + 1.8 * opp_home_made)
    return pip, struct, best_prime, tact, barv, mob


def _eval(a, b, a_bar, b_bar, a_off, b_off):
    """Value from the perspective of the side owning 'a' (mover 23->0)."""
    maxA = -1
    for i in range(23, -1, -1):
        if a[i]:
            maxA = i
            break
    minB = 24
    for i in range(24):
        if b[i]:
            minB = i
            break
    if a_bar or b_bar or maxA > minB:
        sA = _side(a, b, a_bar, b_bar, a_off, b_off)
        sB = _side(b[::-1], a[::-1], b_bar, a_bar, b_off, a_off)
        lead = sB[0] - sA[0]
        v = (lead + 8.0 * (a_off - b_off)
             + (sA[1] - sB[1]) + (sA[2] - sB[2]) + (sA[3] - sB[3])
             + (sA[4] - sB[4]) + (sB[5] - sA[5]))
        if b_off == 0 and lead > 25:
            v += 3.0
        if a_off == 0 and lead < -25:
            v -= 3.0
        return v
    # pure race
    pipA = 0
    pipB = 0
    for i in range(24):
        x = a[i]
        if x:
            pipA += x * (i + 1)
        y = b[i]
        if y:
            pipB += y * (24 - i)
    lead = pipB - pipA + 25 * (b_bar - a_bar)
    v = lead + 8.0 * (a_off - b_off)
    if b_off == 0 and lead > 25:
        v += 3.0
    if a_off == 0 and lead < -25:
        v -= 3.0
    return v


def _opp_finals(oa, ob, oab, obb, oao, hi, lo):
    """Final states (in the mover's frame) reachable by a legal action."""
    seqs = _gen_sequences(oa, ob, oab, obb, oao, hi, lo)
    if seqs:
        return [(s[3], s[4], s[5], s[6], s[7]) for s in seqs]
    m = _single_moves(oa, ob, oab, hi)
    if m:
        return [_single_final(oa, ob, oab, obb, oao, mv) for mv in m]
    if hi != lo:
        m = _single_moves(oa, ob, oab, lo)
        if m:
            return [_single_final(oa, ob, oab, obb, oao, mv) for mv in m]
    return None


def _refine(cand, deadline, bo):
    """2-ply expectimax: average over opponent rolls of their best reply."""
    fa = cand[4]
    fb = cand[5]
    fab = cand[6]
    fbb = cand[7]
    fao = cand[8]
    oa = bytearray(fb[::-1])   # opponent's checkers in their own frame
    ob = bytearray(fa[::-1])   # my checkers in their frame
    oab = fbb
    obb = fab
    oao = bo
    obo = fao
    total = 0.0
    for rhi, rlo, w in _ROLLS:
        if time.time() > deadline:
            return None
        fins = _opp_finals(oa, ob, oab, obb, oao, rhi, rlo)
        if not fins:
            total -= w * _eval(oa, ob, oab, obb, oao, obo)
        else:
            bestv = None
            for F in fins:
                fv = _eval(F[0], F[1], F[2], F[3], F[4], obo)
                if bestv is None or fv > bestv:
                    bestv = fv
            total -= w * bestv
    return total / 36.0


def _fmt(c):
    f1 = c[2]
    f2 = c[3]
    t1 = 'B' if f1 < 0 else 'A%d' % f1
    if f2 is None:
        t2 = 'P'
    elif f2 < 0:
        t2 = 'B'
    else:
        t2 = 'A%d' % f2
    return '%s:%s,%s' % (c[1], t1, t2)


def _core(state, t0):
    raw_my = state['my_pts']
    raw_op = state['opp_pts']
    a = bytearray(24)
    b = bytearray(24)
    n = len(raw_my) if raw_my is not None else 0
    m = len(raw_op) if raw_op is not None else 0
    for i in range(24):
        if i < n:
            a[i] = int(raw_my[i]) & 255
        if i < m:
            b[i] = int(raw_op[i]) & 255
    ab = int(state['my_bar'])
    bb = int(state['opp_bar'])
    ao = int(state['my_off'])
    bo = int(state['opp_off'])
    dice = state.get('dice')
    if not dice:
        return 'H:P,P'
    hi = max(dice)
    lo = min(dice)
    if hi > 6:
        hi = 6
    if hi < 1:
        hi = 1
    if lo > 6:
        lo = 6
    if lo < 1:
        lo = 1
    if lo > hi:
        lo = hi
    seqs = _gen_sequences(a, b, ab, bb, ao, hi, lo)
    cands = []
    if seqs:
        # both dice must be played
        for s in seqs:
            v = _eval(s[3], s[4], s[5], s[6], s[7], bo)
            cands.append((v, s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]))
    else:
        mv = _single_moves(a, b, ab, hi)
        och = 'H'
        if not mv and hi != lo:
            mv = _single_moves(a, b, ab, lo)
            och = 'L'
        if not mv:
            return 'H:P,P'
        for mm in mv:
            fa, fb2, fab, fbb, fao = _single_final(a, b, ab, bb, ao, mm)
            v = _eval(fa, fb2, fab, fbb, fao, bo)
            cands.append((v, och, mm[0], None, fa, fb2, fab, fbb, fao))
    if len(cands) == 1:
        return _fmt(cands[0])
    cands.sort(key=lambda c: c[0], reverse=True)
    deadline = t0 + 0.72
    ref = {}
    K = len(cands)
    if K > 14:
        K = 14
    for idx in range(K):
        if time.time() > deadline:
            break
        r = _refine(cands[idx], deadline, bo)
        if r is None:
            break
        ref[idx] = r
    if ref:
        bi = max(ref, key=lambda i: (ref[i], cands[i][0]))
        return _fmt(cands[bi])
    return _fmt(cands[0])


def _simple(state):
    a = bytearray(int(x) & 255 for x in state['my_pts'])
    b = bytearray(int(x) & 255 for x in state['opp_pts'])
    ab = int(state['my_bar'])
    dice = state.get('dice') or []
    if not dice:
        return 'H:P,P'
    hi = max(dice)
    lo = min(dice)
    if hi > 6:
        hi = 6
    if hi < 1:
        hi = 1
    if lo > 6:
        lo = 6
    if lo < 1:
        lo = 1
    seqs = _gen_sequences(a, b, ab, int(state['opp_bar']), int(state['my_off']), hi, lo)
    if seqs:
        s = seqs[0]
        t1 = 'B' if s[1] < 0 else 'A%d' % s[1]
        t2 = 'B' if s[2] < 0 else 'A%d' % s[2]
        return '%s:%s,%s' % (s[0], t1, t2)
    mvs = _single_moves(a, b, ab, hi)
    if mvs:
        f = mvs[0][0]
        return 'H:%s,P' % ('B' if f < 0 else 'A%d' % f)
    if hi != lo:
        mvs = _single_moves(a, b, ab, lo)
        if mvs:
            f = mvs[0][0]
            return 'L:%s,P' % ('B' if f < 0 else 'A%d' % f)
    return 'H:P,P'


def policy(state):
    t0 = time.time()
    try:
        return _core(state, t0)
    except Exception:
        pass
    try:
        return _simple(state)
    except Exception:
        pass
    return 'H:P,P'
