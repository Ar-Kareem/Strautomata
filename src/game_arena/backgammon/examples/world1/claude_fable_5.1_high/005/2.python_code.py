
POINT_VAL = {
    0: 1.5, 1: 2.5, 2: 4.0, 3: 6.0, 4: 7.0, 5: 5.0,
    6: 5.0, 7: 3.0, 8: 2.0, 9: 1.5, 10: 1.5, 11: 1.5,
    12: 2.5, 13: 1.0, 14: 1.0, 15: 1.0, 16: 1.5, 17: 2.0,
    18: 3.0, 19: 4.5, 20: 4.0, 21: 2.5, 22: 1.5, 23: 1.0,
}
PRIME_BONUS = {3: 2.0, 4: 5.0, 5: 9.0, 6: 14.0}


def _apply(my, opp, bar, obar, off, frm, d):
    my = list(my)
    opp = list(opp)
    if frm == -1:
        if bar == 0:
            return None
        dest = 24 - d
        if opp[dest] >= 2:
            return None
        bar -= 1
        my[dest] += 1
        if opp[dest] == 1:
            opp[dest] = 0
            obar += 1
        return (my, opp, bar, obar, off)
    if bar > 0:
        return None
    if my[frm] <= 0:
        return None
    dest = frm - d
    if dest >= 0:
        if opp[dest] >= 2:
            return None
        my[frm] -= 1
        my[dest] += 1
        if opp[dest] == 1:
            opp[dest] = 0
            obar += 1
        return (my, opp, bar, obar, off)
    for i in range(6, 24):
        if my[i] > 0:
            return None
    if dest < -1:
        for i in range(frm + 1, 6):
            if my[i] > 0:
                return None
    my[frm] -= 1
    off += 1
    return (my, opp, bar, obar, off)


def _sources(my, bar):
    if bar > 0:
        return [-1]
    return [p for p in range(24) if my[p] > 0]


def _gen(my, opp, bar, obar, off, dice):
    results = []
    if len(dice) == 0:
        return results
    if len(dice) == 1:
        d = dice[0]
        for f in _sources(my, bar):
            r = _apply(my, opp, bar, obar, off, f, d)
            if r is not None:
                results.append((1, 'H', f, None, r))
        return results
    a, b = max(dice[0], dice[1]), min(dice[0], dice[1])
    orders = [('H', a, b)] if a == b else [('H', a, b), ('L', b, a)]
    for oc, d1, d2 in orders:
        for f1 in _sources(my, bar):
            r1 = _apply(my, opp, bar, obar, off, f1, d1)
            if r1 is None:
                continue
            any2 = False
            for f2 in _sources(r1[0], r1[2]):
                r2 = _apply(r1[0], r1[1], r1[2], r1[3], r1[4], f2, d2)
                if r2 is None:
                    continue
                any2 = True
                results.append((2, oc, f1, f2, r2))
            if not any2:
                results.append((1, oc, f1, None, r1))
    return results


def _can_hit(p, a, b, opp, obar, blocked):
    if obar == 0:
        if p - a >= 0 and opp[p - a] > 0:
            return True
        if p - b >= 0 and opp[p - b] > 0:
            return True
        if a != b:
            s = p - a - b
            if s >= 0 and opp[s] > 0 and ((not blocked[p - a]) or (not blocked[p - b])):
                return True
        else:
            k = 2
            while k <= 4:
                src = p - k * a
                if src < 0:
                    break
                ok = True
                for j in range(1, k):
                    if blocked[p - j * a]:
                        ok = False
                        break
                if not ok:
                    break
                if opp[src] > 0:
                    return True
                k += 1
        return False
    else:
        ea, eb = a - 1, b - 1
        if ea == p or eb == p:
            return True
        if a != b:
            if obar >= 2:
                return False
            if not blocked[ea]:
                if ea + b == p:
                    return True
                if p - b >= 0 and opp[p - b] > 0:
                    return True
            if not blocked[eb]:
                if eb + a == p:
                    return True
                if p - a >= 0 and opp[p - a] > 0:
                    return True
            return False
        else:
            e = a - 1
            if blocked[e]:
                return False
            remaining = 4 - obar
            if remaining <= 0:
                return False
            for k in range(1, remaining + 1):
                if e + k * a == p:
                    ok = True
                    for j in range(1, k):
                        if blocked[e + j * a]:
                            ok = False
                            break
                    if ok:
                        return True
                src = p - k * a
                if src >= 0 and opp[src] > 0:
                    ok = True
                    for j in range(1, k):
                        if blocked[p - j * a]:
                            ok = False
                            break
                    if ok:
                        return True
            return False


def _hit_prob(p, blocked, opp, obar):
    cnt = 0
    for a in range(1, 7):
        for b in range(a, 7):
            if _can_hit(p, a, b, opp, obar, blocked):
                cnt += 1 if a == b else 2
    return cnt / 36.0


def _race_eval(my, bar, off):
    my_pips = sum((p + 1) * my[p] for p in range(24)) + 25 * bar
    s = -my_pips + 3.0 * off
    outside = sum(my[6:])
    s -= 1.0 * outside
    s -= 0.3 * max(0, my[0] - 2) + 0.15 * max(0, my[1] - 2)
    for p in range(24):
        if my[p] > 4:
            s -= 0.1 * (my[p] - 4)
    return s


def _eval(my, opp, bar, obar, off):
    my_pips = sum((p + 1) * my[p] for p in range(24)) + 25 * bar
    opp_pips = sum((24 - q) * opp[q] for q in range(24)) + 25 * obar

    my_max = -1
    if bar > 0:
        my_max = 24
    else:
        for p in range(23, -1, -1):
            if my[p] > 0:
                my_max = p
                break
    opp_min = 24
    if obar > 0:
        opp_min = -1
    else:
        for q in range(24):
            if opp[q] > 0:
                opp_min = q
                break
    contact = my_max > opp_min
    if not contact:
        return _race_eval(my, bar, off)

    score = (opp_pips - my_pips) * 1.0
    score += 2.0 * off

    opp_behind = [False] * 24
    acc = obar > 0
    for i in range(24):
        opp_behind[i] = acc
        if opp[i] > 0:
            acc = True

    blocked = [my[i] >= 2 for i in range(24)]
    ohome = sum(1 for q in range(18, 24) if opp[q] >= 2)
    mhome = sum(1 for p in range(6) if my[p] >= 2)

    for i in range(24):
        if my[i] >= 2:
            v = POINT_VAL[i]
            if not opp_behind[i]:
                v *= 0.15
            score += v

    opp_back = obar + sum(opp[0:6])
    score += mhome * 1.0 * min(opp_back, 3)

    for q in range(24):
        if opp[q] > 0:
            cnt = 0
            for i in range(q + 1, min(q + 7, 24)):
                if blocked[i]:
                    cnt += 1
            score += 0.6 * cnt * min(opp[q], 2)

    # prime bonus
    i = 0
    while i < 24:
        if blocked[i]:
            j = i
            while j + 1 < 24 and blocked[j + 1]:
                j += 1
            length = j - i + 1
            if length >= 3 and opp_behind[i]:
                score += PRIME_BONUS.get(min(length, 6), 0.0)
            i = j + 1
        else:
            i += 1

    for p in range(24):
        if my[p] > 0:
            cnt = 0
            for i in range(max(p - 6, 0), p):
                if opp[i] >= 2:
                    cnt += 1
            score -= 0.5 * cnt * my[p]

    score += obar * (4.0 + 2.5 * mhome)
    score -= bar * (4.0 + 2.5 * ohome)

    for p in range(24):
        if my[p] == 1 and opp_behind[p]:
            hp = _hit_prob(p, blocked, opp, obar)
            if hp > 0:
                cost = (24 - p) + 6.0 + 3.0 * ohome
                score -= hp * cost

    for p in range(24):
        if my[p] > 3:
            score -= 0.5 * (my[p] - 3)
    score -= 0.7 * my[0] + 0.4 * my[1]
    return score


def _tok(f):
    if f is None:
        return 'P'
    if f == -1:
        return 'B'
    return 'A%d' % f


def _policy(state):
    my = [int(x) for x in state['my_pts']]
    opp = [int(x) for x in state['opp_pts']]
    bar = int(state.get('my_bar', 0))
    obar = int(state.get('opp_bar', 0))
    off = int(state.get('my_off', 0))
    dice = [int(d) for d in state.get('dice', [])]
    if len(dice) > 2:
        dice = dice[:2]
    results = _gen(my, opp, bar, obar, off, dice)
    if not results:
        return "H:P,P"
    maxn = max(r[0] for r in results)
    cands = [r for r in results if r[0] == maxn]
    if maxn == 1 and len(dice) == 2:
        hi = [r for r in cands if r[1] == 'H']
        if hi:
            cands = hi
        else:
            cands = [r for r in cands if r[1] == 'L']
    best = None
    best_score = None
    seen = {}
    for r in cands:
        st = r[4]
        key = (tuple(st[0]), tuple(st[1]), st[2], st[3], st[4])
        if key in seen:
            sc = seen[key]
        else:
            try:
                sc = _eval(st[0], st[1], st[2], st[3], st[4])
            except Exception:
                sc = 0.0
            seen[key] = sc
        if best_score is None or sc > best_score:
            best_score = sc
            best = r
    n, oc, f1, f2, _ = best
    if n == 2:
        return "%s:%s,%s" % (oc, _tok(f1), _tok(f2))
    return "%s:%s,P" % (oc, _tok(f1))


def policy(state):
    try:
        return _policy(state)
    except Exception:
        try:
            my = [int(x) for x in state['my_pts']]
            opp = [int(x) for x in state['opp_pts']]
            bar = int(state.get('my_bar', 0))
            obar = int(state.get('opp_bar', 0))
            off = int(state.get('my_off', 0))
            dice = [int(d) for d in state.get('dice', [])][:2]
            results = _gen(my, opp, bar, obar, off, dice)
            if not results:
                return "H:P,P"
            maxn = max(r[0] for r in results)
            cands = [r for r in results if r[0] == maxn]
            if maxn == 1 and len(dice) == 2:
                hi = [r for r in cands if r[1] == 'H']
                if hi:
                    cands = hi
            n, oc, f1, f2, _ = cands[0]
            if n == 2:
                return "%s:%s,%s" % (oc, _tok(f1), _tok(f2))
            return "%s:%s,P" % (oc, _tok(f1))
        except Exception:
            return "H:P,P"
