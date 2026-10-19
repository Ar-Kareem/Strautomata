
HOME_VAL = [1.0, 1.5, 2.5, 3.0, 3.5, 3.0]
ANCHOR_VAL = {17: 2.0, 18: 3.0, 19: 3.5, 20: 3.5, 21: 2.5, 22: 1.5, 23: 1.0}
PRIME_BONUS = {3: 2.0, 4: 5.0, 5: 9.0, 6: 15.0}


def tok(m):
    return 'B' if m == -1 else 'A%d' % m


def gen_single(my, opp, my_bar, d):
    moves = []
    if my_bar > 0:
        if opp[24 - d] < 2:
            moves.append(-1)
        return moves
    all_home = True
    for p in range(6, 24):
        if my[p]:
            all_home = False
            break
    for p in range(24):
        if my[p] == 0:
            continue
        dest = p - d
        if dest >= 0:
            if opp[dest] < 2:
                moves.append(p)
        elif all_home:
            if dest == -1:
                moves.append(p)
            else:
                higher = False
                for q in range(p + 1, 6):
                    if my[q]:
                        higher = True
                        break
                if not higher:
                    moves.append(p)
    return moves


def apply_move(my, opp, my_bar, opp_bar, my_off, src, d):
    my = list(my)
    opp = list(opp)
    if src == -1:
        my_bar -= 1
        dest = 24 - d
    else:
        my[src] -= 1
        dest = src - d
    if dest < 0:
        my_off += 1
    else:
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1
    return (my, opp, my_bar, opp_bar, my_off)


def hit_count(p, my, opp, opp_bar):
    def present(src):
        if src >= 0:
            return opp[src] > 0
        return src == -1 and opp_bar > 0

    def open_(idx):
        return 0 <= idx < 24 and my[idx] < 2

    cnt = 0
    for d1 in range(1, 7):
        for d2 in range(1, 7):
            hit = False
            if d1 != d2:
                for a, b in ((d1, d2), (d2, d1)):
                    src = p - a
                    if present(src):
                        if opp_bar == 0 or src == -1:
                            hit = True
                            break
                        if opp_bar == 1 and open_(b - 1):
                            hit = True
                            break
                if not hit:
                    src = p - d1 - d2
                    if present(src):
                        if src == -1:
                            if opp_bar == 1 and (open_(d1 - 1) or open_(d2 - 1)):
                                hit = True
                        elif opp_bar == 0 and (open_(p - d1) or open_(p - d2)):
                            hit = True
            else:
                d = d1
                for k in range(1, 5):
                    src = p - k * d
                    if src < -1:
                        break
                    if present(src):
                        ok = True
                        for j in range(1, k):
                            if not open_(p - j * d):
                                ok = False
                                break
                        if ok:
                            if src == -1:
                                if opp_bar - 1 + k <= 4:
                                    hit = True
                            else:
                                if opp_bar == 0:
                                    hit = True
                                elif opp_bar + k <= 4 and open_(d - 1):
                                    hit = True
                    if hit:
                        break
            if hit:
                cnt += 1
    return cnt


def evaluate(my, opp, my_bar, opp_bar, my_off, opp_off):
    if my_off >= 15:
        return 1e6
    my_pip = 25 * my_bar
    opp_pip = 25 * opp_bar
    my_back = 24 if my_bar else -1
    opp_front = -1 if opp_bar else 24
    for p in range(24):
        m = my[p]
        o = opp[p]
        if m:
            my_pip += (p + 1) * m
            if my_bar == 0 and p > my_back:
                my_back = p
        if o:
            opp_pip += (24 - p) * o
            if opp_bar == 0 and p < opp_front:
                opp_front = p
    race = opp_pip - my_pip
    contact = my_back > opp_front
    if not contact:
        score = race + 3.0 * my_off
        outside = 0
        for p in range(6, 24):
            outside += my[p]
        score -= 1.5 * outside
        for p in range(6):
            if my[p] > 3:
                score -= 0.3 * (my[p] - 3)
        return score

    score = 1.0 * race
    my_home_made = 0
    for p in range(6):
        if my[p] >= 2:
            my_home_made += 1
    opp_home_made = 0
    for p in range(18, 24):
        if opp[p] >= 2:
            opp_home_made += 1
    opp_behind = [0] * 25
    c = opp_bar
    for p in range(24):
        opp_behind[p] = c
        c += opp[p]
    opp_behind[24] = c

    race_factor = 1.0 + max(-30.0, min(60.0, race)) / 80.0
    for p in range(24):
        if my[p] == 1 and opp_behind[p] > 0:
            hc = hit_count(p, my, opp, opp_bar)
            if hc:
                cost = (24 - p) + 4.0 + 2.5 * opp_home_made
                if p >= 18:
                    cost *= 0.6
                score -= (hc / 36.0) * cost * race_factor

    made = [my[p] >= 2 for p in range(24)]
    for p in range(24):
        if not made[p]:
            continue
        behind = opp_behind[p]
        if p <= 5:
            v = HOME_VAL[p]
            if behind > 0:
                v *= 1.5
                if opp_bar:
                    v += 1.0
            else:
                v *= 0.4
        elif p <= 11:
            v = (3.0 if p == 6 else 1.5) if behind > 0 else 0.4
        elif p <= 16:
            v = 1.0 if behind > 0 else 0.3
        else:
            v = ANCHOR_VAL[p] if behind > 0 else 0.3
        score += v

    run = 0
    best = 0
    best_end = -1
    for p in range(24):
        if made[p]:
            run += 1
            if run > best:
                best = run
                best_end = p
        else:
            run = 0
    if best >= 3:
        start = best_end - best + 1
        if opp_behind[start] > 0:
            score += PRIME_BONUS[min(best, 6)]

    if opp_bar:
        pf = (my_home_made / 6.0) ** 2
        score += opp_bar * (3.0 + 1.5 * my_home_made) + 12.0 * pf * opp_bar
    if my_bar:
        pf = (opp_home_made / 6.0) ** 2
        score -= my_bar * (3.0 + 1.5 * opp_home_made) + 12.0 * pf * my_bar

    back = 0
    for p in range(18, 24):
        back += my[p]
    if back > 2:
        score -= 1.5 * (back - 2)
    for p in range(12, 24):
        if my[p]:
            blk = 0
            for q in range(max(0, p - 6), p):
                if opp[q] >= 2:
                    blk += 1
            if blk >= 2:
                score -= 0.6 * my[p] * (blk - 1)

    for p in range(24):
        if my[p] > 4:
            score -= 0.5 * (my[p] - 4)
    if opp_behind[6] > 0:
        deep = my[0] + my[1]
        if deep > 2:
            score -= 0.3 * (deep - 2)

    for q in range(24):
        if opp[q] == 1:
            shot = False
            if my_bar == 0:
                for p in range(q + 1, min(24, q + 7)):
                    if my[p]:
                        shot = True
                        break
            elif q >= 18:
                shot = True
            if shot:
                score += 0.8 + (0.7 if q <= 5 else 0.0)
    return score


def candidates(my, opp, my_bar, opp_bar, my_off, dice):
    cands = []
    base = (my, opp, my_bar, opp_bar, my_off)
    if len(dice) == 0:
        return [(0, False, 'H:P,P', base)], False
    if len(dice) == 1:
        d = dice[0]
        ms = gen_single(my, opp, my_bar, d)
        if not ms:
            return [(0, False, 'H:P,P', base)], False
        for m in ms:
            s = apply_move(my, opp, my_bar, opp_bar, my_off, m, d)
            cands.append((1, True, 'H:%s,P' % tok(m), s))
        return cands, False
    hi = max(dice[0], dice[1])
    lo = min(dice[0], dice[1])
    orders = [('H', hi, lo)]
    if hi != lo:
        orders.append(('L', lo, hi))
    for oc, d1, d2 in orders:
        m1s = gen_single(my, opp, my_bar, d1)
        if not m1s:
            m2s = gen_single(my, opp, my_bar, d2)
            if not m2s:
                cands.append((0, False, oc + ':P,P', base))
            else:
                for m2 in m2s:
                    s = apply_move(my, opp, my_bar, opp_bar, my_off, m2, d2)
                    cands.append((1, d2 == hi, '%s:P,%s' % (oc, tok(m2)), s))
        else:
            for m1 in m1s:
                s1 = apply_move(my, opp, my_bar, opp_bar, my_off, m1, d1)
                m2s = gen_single(s1[0], s1[1], s1[2], d2)
                if not m2s:
                    cands.append((1, d1 == hi, '%s:%s,P' % (oc, tok(m1)), s1))
                else:
                    for m2 in m2s:
                        s2 = apply_move(s1[0], s1[1], s1[2], s1[3], s1[4], m2, d2)
                        cands.append((2, True, '%s:%s,%s' % (oc, tok(m1), tok(m2)), s2))
    return cands, hi != lo


def filter_cands(cands, distinct):
    maxc = max(c[0] for c in cands)
    cands = [c for c in cands if c[0] == maxc]
    if maxc == 1 and distinct:
        hic = [c for c in cands if c[1]]
        if hic:
            cands = hic
    return cands


def read_state(state):
    my = [int(x) for x in state['my_pts']]
    opp = [int(x) for x in state['opp_pts']]
    my_bar = int(state.get('my_bar', 0))
    opp_bar = int(state.get('opp_bar', 0))
    my_off = int(state.get('my_off', 0))
    opp_off = int(state.get('opp_off', 0))
    dice = [int(x) for x in state.get('dice', [])]
    return my, opp, my_bar, opp_bar, my_off, opp_off, dice


def _policy(state):
    my, opp, my_bar, opp_bar, my_off, opp_off, dice = read_state(state)
    cands, distinct = candidates(my, opp, my_bar, opp_bar, my_off, dice)
    cands = filter_cands(cands, distinct)
    best_s = None
    best_v = None
    cache = {}
    for cnt, uh, s, st in cands:
        key = (tuple(st[0]), tuple(st[1]), st[2], st[3], st[4])
        if key in cache:
            v = cache[key]
        else:
            v = evaluate(st[0], st[1], st[2], st[3], st[4], opp_off)
            cache[key] = v
        pref = 0 if ':P,' in s else 1
        if best_v is None or (v, pref) > best_v:
            best_v = (v, pref)
            best_s = s
    return best_s


def _fallback(state):
    my, opp, my_bar, opp_bar, my_off, opp_off, dice = read_state(state)
    cands, distinct = candidates(my, opp, my_bar, opp_bar, my_off, dice)
    cands = filter_cands(cands, distinct)
    for c in cands:
        if ':P,' not in c[2]:
            return c[2]
    return cands[0][2]


def policy(state):
    try:
        r = _policy(state)
        if r:
            return r
    except Exception:
        pass
    try:
        return _fallback(state)
    except Exception:
        return 'H:P,P'
