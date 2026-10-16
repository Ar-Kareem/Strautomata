
def _can_bear_off(my_pts, my_bar):
    if my_bar != 0:
        return False
    for i in range(6, 24):
        if my_pts[i] != 0:
            return False
    return True

def _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, die, frm):
    # returns (n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off) or None
    # frm: 'B' or 'A<i>'
    if frm == 'B':
        if my_bar <= 0:
            return None
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return None
        if opp_pts[dest] >= 2:
            return None
        n_my_pts = my_pts[:]
        n_opp_pts = opp_pts[:]
        n_my_bar = my_bar - 1
        n_opp_bar = opp_bar
        n_my_off = my_off
        if n_opp_pts[dest] == 1:
            n_opp_pts[dest] = 0
            n_opp_bar += 1
        n_my_pts[dest] += 1
        return (n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off)
    else:
        # 'A<i>'
        try:
            idx = int(frm[1:])
        except:
            return None
        if idx < 0 or idx >= 24:
            return None
        if my_bar > 0:
            return None
        if my_pts[idx] <= 0:
            return None
        dest = idx - die
        n_my_pts = my_pts[:]
        n_opp_pts = opp_pts[:]
        n_my_bar = my_bar
        n_opp_bar = opp_bar
        n_my_off = my_off
        if dest >= 0:
            if n_opp_pts[dest] >= 2:
                return None
            n_my_pts[idx] -= 1
            if n_opp_pts[dest] == 1:
                n_opp_pts[dest] = 0
                n_opp_bar += 1
            n_my_pts[dest] += 1
            return (n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off)
        else:
            # bear off attempt
            if not _can_bear_off(my_pts, my_bar):
                return None
            if dest == -1:
                n_my_pts[idx] -= 1
                n_my_off += 1
                return (n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off)
            else:
                # need no checkers above idx in home
                for k in range(idx + 1, 6):
                    if my_pts[k] > 0:
                        return None
                n_my_pts[idx] -= 1
                n_my_off += 1
                return (n_my_pts, n_opp_pts, n_my_bar, n_opp_bar, n_my_off)

def _has_any_move(my_pts, opp_pts, my_bar, opp_bar, my_off, die):
    if my_bar > 0:
        r = _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, die, 'B')
        return r is not None
    for i in range(24):
        if my_pts[i] > 0:
            r = _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, die, 'A%d' % i)
            if r is not None:
                return True
    return False

def _evaluate(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    my_pip = my_bar * 25
    opp_pip = opp_bar * 25
    for i, c in enumerate(my_pts):
        if c:
            my_pip += (i + 1) * c
    for i, c in enumerate(opp_pts):
        if c:
            opp_pip += (24 - i) * c
    # contact detection
    if my_bar > 0 or opp_bar > 0:
        contact = True
    else:
        max_my = -1
        min_opp = 24
        for i, c in enumerate(my_pts):
            if c > 0:
                max_my = i
        for i, c in enumerate(opp_pts):
            if c > 0:
                min_opp = i
                break
        if max_my == -1 or min_opp == 24:
            contact = False
        else:
            contact = not (max_my < min_opp)
    if not contact:
        # pure race
        return 60.0 * (my_off - opp_off) + 2.0 * (opp_pip - my_pip)
    # contact features
    my_blots = 0
    opp_blots = 0
    for c in my_pts:
        if c == 1:
            my_blots += 1
    for c in opp_pts:
        if c == 1:
            opp_blots += 1
    # exposed blots
    my_exposed = 0
    if opp_bar > 0:
        for i in range(0, 6):
            if my_pts[i] == 1:
                my_exposed += 1
    else:
        for i in range(24):
            if my_pts[i] == 1:
                hit = False
                for d in range(1, 7):
                    j = i - d
                    if j >= 0 and opp_pts[j] > 0:
                        hit = True
                        break
                if hit:
                    my_exposed += 1
    opp_hittable = 0
    if my_bar > 0:
        for j in range(18, 24):
            if opp_pts[j] == 1:
                opp_hittable += 1
    else:
        for j in range(24):
            if opp_pts[j] == 1:
                hit = False
                for d in range(1, 7):
                    k = j + d
                    if k < 24 and my_pts[k] > 0:
                        hit = True
                        break
                if hit:
                    opp_hittable += 1
    my_made = 0
    opp_made = 0
    for c in my_pts:
        if c >= 2:
            my_made += 1
    for c in opp_pts:
        if c >= 2:
            opp_made += 1
    # longest prime
    def longest_prime(pts):
        best = 0
        cur = 0
        for i in range(24):
            if pts[i] >= 2:
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0
        return best
    my_prime = longest_prime(my_pts)
    opp_prime = longest_prime(opp_pts)
    my_home_made = 0
    for i in range(0, 6):
        if my_pts[i] >= 2:
            my_home_made += 1
    my_anchor = 0
    for i in range(18, 24):
        if my_pts[i] >= 2:
            my_anchor += 1
    stack_waste = 0
    for c in my_pts:
        if c > 3:
            stack_waste += (c - 3)
    score = 0.0
    score += 55.0 * (my_off - opp_off)
    score += 48.0 * (opp_bar - my_bar)
    score += 1.0 * (opp_pip - my_pip)
    score += -6.0 * my_blots + 4.0 * opp_blots
    score += -11.0 * my_exposed + 3.0 * opp_hittable
    score += 3.0 * (my_made - opp_made)
    score += 3.0 * (my_prime - opp_prime)
    score += 4.0 * my_home_made
    score += 5.0 * my_anchor
    score += -2.0 * stack_waste
    # key points for player moving 23->0, home 0-5
    if len(my_pts) > 6:
        if my_pts[4] >= 2:
            score += 8.0
        if my_pts[3] >= 2:
            score += 4.0
        if my_pts[5] >= 2:
            score += 4.0
        if my_pts[6] >= 2:
            score += 5.0
        if my_pts[11] >= 2:
            score += 2.0
        if my_pts[12] >= 2:
            score += 2.0
    # penalize opp prime near our path slightly extra
    # small bonus for bearing off checkers stacked low: prefer fewer points occupied in bearoff?
    return score

def _enumerate_legal(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, opp_off0, dice):
    # returns list of (order, f1, f2, board_tuple)
    if len(dice) == 0:
        return [('H', 'P', 'P', (my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0))]
    if len(dice) == 1:
        d = dice[0]
        actions = []
        # try all f1
        candidates = ['P', 'B'] + ['A%d' % i for i in range(24)]
        for f1 in candidates:
            if f1 == 'P':
                if _has_any_move(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, d):
                    continue
                actions.append(('H', 'P', 'P', (my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0)))
            else:
                r = _apply_single(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, d, f1)
                if r is not None:
                    actions.append(('H', f1, 'P', r))
        if not actions:
            actions.append(('H', 'P', 'P', (my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0)))
        # filter max used
        maxu = 0
        for _, f1, f2, _ in actions:
            u = (0 if f1 == 'P' else 1) + (0 if f2 == 'P' else 1)
            if u > maxu:
                maxu = u
        filt = []
        for a in actions:
            _, f1, f2, _ = a
            u = (0 if f1 == 'P' else 1) + (0 if f2 == 'P' else 1)
            if u == maxu:
                filt.append(a)
        return filt
    # len 2
    d0, d1 = dice[0], dice[1]
    hi = d0 if d0 >= d1 else d1
    lo = d1 if d0 >= d1 else d0
    is_double = (d0 == d1)
    orders = ['H'] if is_double else ['H', 'L']
    all_from = ['P', 'B'] + ['A%d' % i for i in range(24)]
    actions = []
    for order in orders:
        die1 = hi if order == 'H' else lo
        die2 = lo if order == 'H' else hi
        for f1 in all_from:
            # step1
            if f1 == 'P':
                if _has_any_move(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, die1):
                    continue
                b1 = (my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0)
            else:
                r1 = _apply_single(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, die1, f1)
                if r1 is None:
                    continue
                b1 = r1
            my1, opp1, bar1, obar1, off1 = b1
            for f2 in all_from:
                if f2 == 'P':
                    if _has_any_move(my1, opp1, bar1, obar1, off1, die2):
                        continue
                    b2 = b1
                    actions.append((order, f1, f2, b2))
                else:
                    r2 = _apply_single(my1, opp1, bar1, obar1, off1, die2, f2)
                    if r2 is None:
                        continue
                    actions.append((order, f1, f2, r2))
    if not actions:
        return [('H', 'P', 'P', (my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0))]
    maxu = 0
    for _, f1, f2, _ in actions:
        u = (0 if f1 == 'P' else 1) + (0 if f2 == 'P' else 1)
        if u > maxu:
            maxu = u
    filt = [a for a in actions if ((0 if a[1] == 'P' else 1) + (0 if a[2] == 'P' else 1)) == maxu]
    if maxu == 1 and not is_double:
        # must use higher die
        higher_actions = []
        for (order, f1, f2, b) in filt:
            if order == 'H':
                # die1=hi, die2=lo
                uses_hi = (f1 != 'P')
            else:
                uses_hi = (f2 != 'P')
            if uses_hi:
                higher_actions.append((order, f1, f2, b))
        if higher_actions:
            filt = higher_actions
    return filt

def policy(state: dict) -> str:
    try:
        my_pts0 = list(state['my_pts'])
        opp_pts0 = list(state['opp_pts'])
        my_bar0 = int(state['my_bar'])
        opp_bar0 = int(state['opp_bar'])
        my_off0 = int(state['my_off'])
        opp_off0 = int(state['opp_off'])
        dice = list(state['dice'])
    except Exception:
        return "H:P,P"
    try:
        # sanitize
        if len(my_pts0) != 24:
            return "H:P,P"
        if len(opp_pts0) != 24:
            return "H:P,P"
        # clamp dice to 0-2 dice 1..6
        ndice = []
        for d in dice[:2]:
            try:
                di = int(d)
            except:
                continue
            if 1 <= di <= 6:
                ndice.append(di)
        dice = ndice
        actions = _enumerate_legal(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, opp_off0, dice)
        best = None
        best_score = None
        for (order, f1, f2, b) in actions:
            my1, opp1, bar1, obar1, off1 = b
            s = _evaluate(my1, opp1, bar1, obar1, off1, opp_off0)
            # tiny preference for H and for hitting (more opp bar) to break ties deterministically
            s += 0.001 * (obar1 - opp_bar0)
            if best_score is None or s > best_score:
                best_score = s
                best = (order, f1, f2)
        if best is None:
            return "H:P,P"
        return "%s:%s,%s" % best
    except Exception:
        # last resort: try to find any single legal move greedily
        try:
            if len(dice) == 0:
                return "H:P,P"
            if len(dice) == 1:
                d = dice[0]
                if my_bar0 > 0:
                    r = _apply_single(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, d, 'B')
                    if r is not None:
                        return "H:B,P"
                for i in range(24):
                    if my_pts0[i] > 0:
                        r = _apply_single(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, d, 'A%d' % i)
                        if r is not None:
                            return "H:A%d,P" % i
                return "H:P,P"
            else:
                # try H first move higher
                hi = max(dice)
                lo = min(dice)
                # try to find any legal with hi then lo
                cands = ['B'] + ['A%d' % i for i in range(23, -1, -1)]
                for f1 in cands:
                    r1 = None
                    try:
                        r1 = _apply_single(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, hi, f1)
                    except:
                        r1 = None
                    if r1 is not None:
                        return "H:%s,P" % f1
                for f1 in cands:
                    r1 = None
                    try:
                        r1 = _apply_single(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, lo, f1)
                    except:
                        r1 = None
                    if r1 is not None:
                        return "L:%s,P" % f1
                return "H:P,P"
        except:
            return "H:P,P"
