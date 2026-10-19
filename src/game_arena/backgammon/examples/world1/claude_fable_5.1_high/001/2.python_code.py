
import time

ROLLS = []
for _a in range(1, 7):
    for _b in range(_a, 7):
        ROLLS.append((_a, _b, 1 if _a == _b else 2))

POINT_VAL = [1.0, 1.5, 2.2, 3.0, 3.5, 3.2, 3.0, 2.2, 1.2, 1.0, 1.0, 1.0,
             0.6, 0.6, 0.6, 0.6, 0.8, 1.0, 2.5, 2.5, 2.5, 1.5, 1.0, 0.6]


def tok(src):
    return 'B' if src == 'B' else 'A%d' % src


def single_moves(mp, op, bar, d):
    res = []
    if bar > 0:
        dest = 24 - d
        if op[dest] < 2:
            res.append(('B', dest))
        return res
    can_bear = True
    for i in range(6, 24):
        if mp[i]:
            can_bear = False
            break
    for p in range(24):
        if mp[p] == 0:
            continue
        dest = p - d
        if dest >= 0:
            if op[dest] < 2:
                res.append((p, dest))
        elif can_bear:
            if dest == -1:
                res.append((p, -1))
            else:
                ok = True
                for i in range(p + 1, 6):
                    if mp[i]:
                        ok = False
                        break
                if ok:
                    res.append((p, -1))
    return res


def apply_move(mp, op, bar, obar, off, mv):
    src, dest = mv
    mp = list(mp)
    op = list(op)
    if src == 'B':
        bar -= 1
    else:
        mp[src] -= 1
    if dest < 0:
        off += 1
    else:
        if op[dest] == 1:
            op[dest] = 0
            obar += 1
        mp[dest] += 1
    return mp, op, bar, obar, off


def legal_actions(mp, op, mb, ob, moff, dice):
    """Return list of (action_string, (mp, op, mb, ob, moff))."""
    base = (list(mp), list(op), mb, ob, moff)
    if len(dice) == 0:
        return [('H:P,P', base)]
    if len(dice) == 1:
        d = dice[0]
        ms = single_moves(mp, op, mb, d)
        if not ms:
            return [('H:P,P', base)]
        out = []
        seen = set()
        for mv in ms:
            st = apply_move(mp, op, mb, ob, moff, mv)
            key = (tuple(st[0]), tuple(st[1]), st[2], st[3], st[4])
            if key in seen:
                continue
            seen.add(key)
            out.append(('H:%s,P' % tok(mv[0]), st))
        return out
    d1, d2 = dice[0], dice[1]
    hi, lo = max(d1, d2), min(d1, d2)
    orders = [(hi, lo, 'H')]
    if hi != lo:
        orders.append((lo, hi, 'L'))
    out = []
    seen = set()
    for first, second, oc in orders:
        for m1 in single_moves(mp, op, mb, first):
            s1 = apply_move(mp, op, mb, ob, moff, m1)
            for m2 in single_moves(s1[0], s1[1], s1[2], second):
                s2 = apply_move(s1[0], s1[1], s1[2], s1[3], s1[4], m2)
                key = (tuple(s2[0]), tuple(s2[1]), s2[2], s2[3], s2[4])
                if key in seen:
                    continue
                seen.add(key)
                out.append(('%s:%s,%s' % (oc, tok(m1[0]), tok(m2[0])), s2))
    if out:
        return out
    for d, oc in ((hi, 'H'), (lo, 'L')):
        ms = single_moves(mp, op, mb, d)
        if ms:
            for mv in ms:
                st = apply_move(mp, op, mb, ob, moff, mv)
                key = (tuple(st[0]), tuple(st[1]), st[2], st[3], st[4])
                if key in seen:
                    continue
                seen.add(key)
                out.append(('%s:%s,P' % (oc, tok(mv[0])), st))
            return out
    return [('H:P,P', base)]


def hit_prob(p, dists, blocked):
    hits = 0
    for a, b, w in ROLLS:
        if a in dists or b in dists:
            hits += w
        elif a != b:
            if (a + b) in dists and ((p - a) not in blocked or (p - b) not in blocked):
                hits += w
        else:
            if (p - a) in blocked:
                continue
            if 2 * a in dists:
                hits += w
            elif (p - 2 * a) not in blocked:
                if 3 * a in dists:
                    hits += w
                elif 4 * a in dists and (p - 3 * a) not in blocked:
                    hits += w
    return hits / 36.0


def side_score(A, B, a_bar, b_bar, exposure):
    """A moves 23->0 (home 0..5); B moves 0->23 (home 18..23, enters at d-1)."""
    s = 0.0
    Bpos = [i for i in range(24) if B[i] > 0]
    if b_bar > 0:
        b_min = -1
    else:
        b_min = Bpos[0] if Bpos else 24
    blocked = set()
    for i in range(24):
        if A[i] >= 2:
            blocked.add(i)
    b_home_pts = 0
    for i in range(18, 24):
        if B[i] >= 2:
            b_home_pts += 1
    a_home_pts = 0
    for i in range(6):
        if A[i] >= 2:
            a_home_pts += 1
    # made points
    for i in blocked:
        v = POINT_VAL[i]
        if not (b_min < i):
            v *= 0.3
        s += v
    # board strength vs opponent on bar
    if b_bar > 0:
        s += a_home_pts * 1.5 * min(b_bar, 2)
        if a_home_pts == 6:
            s += 10.0 * b_bar
    # prime
    best_len = 0
    best_start = 0
    cur = 0
    start = 0
    for i in range(18):
        if i in blocked and b_min < i:
            if cur == 0:
                start = i
            cur += 1
            if cur > best_len:
                best_len = cur
                best_start = start
        else:
            cur = 0
    if best_len >= 3:
        trapped = b_bar
        for j in range(best_start):
            trapped += B[j]
        if trapped > 0:
            s += 0.5 * best_len * best_len * min(trapped, 2)
    elif best_len == 2:
        s += 0.8
    # blots
    for i in range(24):
        if A[i] == 1:
            dists = set()
            for q in Bpos:
                if q < i:
                    dists.add(i - q)
            if b_bar > 0:
                dists.add(i + 1)
            if not dists:
                continue
            ph = hit_prob(i, dists, blocked)
            if ph > 0:
                cost = (24 - i) * 0.6 + 3.0 + 1.2 * b_home_pts
                s -= exposure * ph * cost
    # own bar
    if a_bar > 0:
        s -= a_bar * (2.0 + 1.5 * b_home_pts)
        if b_home_pts == 6:
            s -= 10.0 * a_bar
    # stacking
    for i in range(24):
        if A[i] > 4:
            s -= 0.4 * (A[i] - 4)
    # back checkers
    back = a_bar
    for i in range(18, 24):
        back += A[i]
    if back > 2:
        s -= 1.0 * (back - 2)
    return s


def evaluate(mp, op, mb, ob, moff, ooff):
    """Value from perspective of the side that just moved (mp). op is on roll."""
    if moff >= 15:
        return 10000.0
    if ooff >= 15:
        return -10000.0
    my_pip = 25 * mb
    opp_pip = 25 * ob
    my_max = 24 if mb else -1
    opp_min = -1 if ob else 24
    for i in range(24):
        c = mp[i]
        if c:
            my_pip += (i + 1) * c
            if i > my_max:
                my_max = i
        c = op[i]
        if c:
            opp_pip += (24 - i) * c
            if i < opp_min:
                opp_min = i
    if my_max <= opp_min:
        # pure race
        s = (opp_pip - my_pip) * 1.0 + 2.0 * (moff - ooff)
        s -= 0.3 * mp[0] + 0.15 * mp[1]
        s += 0.3 * op[23] + 0.15 * op[22]
        out_m = 0
        for i in range(6, 24):
            out_m += mp[i]
        out_o = 0
        for i in range(0, 18):
            out_o += op[i]
        s -= 0.5 * out_m
        s += 0.5 * out_o
        return s
    s = 0.75 * (opp_pip - my_pip)
    s += side_score(mp, op, mb, ob, 1.0)
    s -= side_score(op[::-1], mp[::-1], ob, mb, 0.45)
    return s


def expected_opp_value(mp, op, mb, ob, moff, ooff, deadline):
    omp = op[::-1]
    oop = mp[::-1]
    total = 0.0
    for a, b, w in ROLLS:
        if time.time() > deadline:
            return None
        acts = legal_actions(omp, oop, ob, mb, ooff, [a, b])
        best = None
        for act, st in acts:
            v = evaluate(st[0], st[1], st[2], st[3], st[4], moff)
            if best is None or v > best:
                best = v
        total += w * best
    return total / 36.0


def policy(state):
    t0 = time.time()
    try:
        mp = list(state['my_pts'])
        op = list(state['opp_pts'])
        mb = int(state.get('my_bar', 0))
        ob = int(state.get('opp_bar', 0))
        moff = int(state.get('my_off', 0))
        ooff = int(state.get('opp_off', 0))
        dice = list(state.get('dice', []))
        acts = legal_actions(mp, op, mb, ob, moff, dice)
        if len(acts) == 1:
            return acts[0][0]
        scored = []
        for act, st in acts:
            v = evaluate(st[0], st[1], st[2], st[3], st[4], ooff)
            scored.append((v, act, st))
        scored.sort(key=lambda x: -x[0])
        best_act = scored[0][1]
        budget = 0.4
        hard_deadline = t0 + 0.65
        limit = min(len(scored), 8)
        cutoff = scored[0][0] - 12.0
        results = []
        for i in range(limit):
            if time.time() - t0 > budget:
                break
            v1, act, st = scored[i]
            if v1 < cutoff:
                break
            ev = expected_opp_value(st[0], st[1], st[2], st[3], st[4], ooff, hard_deadline)
            if ev is None:
                break
            results.append((-ev + 0.05 * v1, act))
        if results:
            results.sort(key=lambda x: -x[0])
            return results[0][1]
        return best_act
    except Exception:
        try:
            acts = legal_actions(list(state['my_pts']), list(state['opp_pts']),
                                 int(state.get('my_bar', 0)), int(state.get('opp_bar', 0)),
                                 int(state.get('my_off', 0)), list(state.get('dice', [])))
            return acts[0][0]
        except Exception:
            return 'H:P,P'
