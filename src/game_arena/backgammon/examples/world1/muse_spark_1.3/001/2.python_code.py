
def _apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, src, die):
    # src: 'B' or int
    if src == 'B':
        if my_bar <= 0:
            return None
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return None
        if opp_pts[dest] >= 2:
            return None
        n_my = my_pts[:]
        n_opp = opp_pts[:]
        n_my_bar = my_bar - 1
        n_opp_bar = opp_bar
        if n_opp[dest] == 1:
            n_opp[dest] = 0
            n_opp_bar += 1
        n_my[dest] += 1
        return (n_my, n_opp, n_my_bar, n_opp_bar, my_off)
    else:
        s = src
        if my_bar > 0:
            return None
        if s < 0 or s >= 24:
            return None
        if my_pts[s] <= 0:
            return None
        dest = s - die
        if dest >= 0:
            if opp_pts[dest] >= 2:
                return None
            n_my = my_pts[:]
            n_opp = opp_pts[:]
            n_my[s] -= 1
            n_opp_bar = opp_bar
            if n_opp[dest] == 1:
                n_opp[dest] = 0
                n_opp_bar += 1
            n_my[dest] += 1
            return (n_my, n_opp, my_bar, n_opp_bar, my_off)
        else:
            # bear off attempt
            if my_bar > 0:
                return None
            for i in range(6, 24):
                if my_pts[i] > 0:
                    return None
            if s < 0 or s >= 6:
                return None
            dist = s + 1
            if die == dist:
                n_my = my_pts[:]
                n_my[s] -= 1
                return (n_my, opp_pts[:], my_bar, opp_bar, my_off + 1)
            elif die > dist:
                for i in range(s + 1, 6):
                    if my_pts[i] > 0:
                        return None
                n_my = my_pts[:]
                n_my[s] -= 1
                return (n_my, opp_pts[:], my_bar, opp_bar, my_off + 1)
            else:
                return None

def _legal_sources(my_pts, opp_pts, my_bar, die):
    if my_bar > 0:
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return []
        if opp_pts[dest] >= 2:
            return []
        return ['B']
    res = []
    for s in range(24):
        if my_pts[s] <= 0:
            continue
        dest = s - die
        if dest >= 0:
            if opp_pts[dest] >= 2:
                continue
            res.append(s)
        else:
            # bear off check
            ok = True
            for i in range(6, 24):
                if my_pts[i] > 0:
                    ok = False
                    break
            if not ok:
                continue
            if s < 0 or s >= 6:
                continue
            dist = s + 1
            if die == dist:
                res.append(s)
            elif die > dist:
                higher = False
                for i in range(s + 1, 6):
                    if my_pts[i] > 0:
                        higher = True
                        break
                if not higher:
                    res.append(s)
                # else illegal
            else:
                continue
    return res

def _evaluate(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    pip_my = my_bar * 25
    for i in range(24):
        c = my_pts[i]
        if c:
            pip_my += c * (i + 1)
    pip_opp = opp_bar * 25
    for i in range(24):
        c = opp_pts[i]
        if c:
            pip_opp += c * (24 - i)
    score = float(pip_opp - pip_my)
    score += float(my_off - opp_off) * 12.0
    score += float(opp_bar) * 10.0 - float(my_bar) * 15.0

    # structure
    # precompute opp presence for threat
    # my points
    run = 0
    for i in range(24):
        c = my_pts[i]
        if c >= 2:
            bonus = 6.0
            if i < 6:
                bonus = 10.0
            elif i >= 18:
                bonus = 8.0
            elif 11 <= i <= 16:
                bonus = 7.0
            score += bonus
            if c > 3:
                score -= float(c - 3) * 4.0
            run += 1
        else:
            if run >= 2:
                score += float(run * run) * 1.5
            elif run >= 3:
                score += float(run) * 2.0
            run = 0
            if c == 1:
                # blot threat from opp (opp moves +)
                threat = 0.0
                # direct 1..6
                for d in range(1, 7):
                    s = i - d
                    if s >= 0 and opp_pts[s] > 0:
                        threat += 1.0
                # indirect 7..12 with lower weight
                for d in range(7, 13):
                    s = i - d
                    if s >= 0 and opp_pts[s] > 0:
                        threat += 0.4
                if opp_bar > 0 and i < 6:
                    threat += 1.0
                if threat <= 0.01:
                    score -= 2.0
                else:
                    pen = 4.0 + threat * 4.0
                    # blots in outer board more dangerous
                    if 6 <= i <= 17:
                        pen += 2.0
                    score -= pen
    if run >= 2:
        score += float(run * run) * 1.5

    # opp structure (negative for us)
    orun = 0
    for i in range(24):
        c = opp_pts[i]
        if c >= 2:
            pen = 5.0
            if 6 <= i <= 17:
                pen += 2.0
            score -= pen
            orun += 1
        else:
            if orun >= 2:
                score -= float(orun * orun) * 1.2
            orun = 0
            if c == 1:
                # opp blot: bonus if we can hit (we move -)
                can = False
                for d in range(1, 7):
                    s = i + d
                    if s < 24 and my_pts[s] > 0:
                        can = True
                        break
                if can:
                    score += 6.0
                else:
                    # far indirect?
                    can2 = False
                    for d in range(7, 13):
                        s = i + d
                        if s < 24 and my_pts[s] > 0:
                            can2 = True
                            break
                    if can2:
                        score += 3.0
                    else:
                        score += 1.0
    if orun >= 2:
        score -= float(orun * orun) * 1.2

    # anchor bonus
    has_anchor = False
    for i in range(18, 24):
        if my_pts[i] >= 2:
            has_anchor = True
            break
    if has_anchor:
        score += 4.0
    # home board strength
    home_made = 0
    for i in range(0, 6):
        if my_pts[i] >= 2:
            home_made += 1
    score += float(home_made) * 2.0
    opp_home_made = 0
    for i in range(18, 24):
        if opp_pts[i] >= 2:
            opp_home_made += 1
    score -= float(opp_home_made) * 2.0

    return score

def _tok(src):
    if src is None:
        return "P"
    if src == 'B':
        return "B"
    return "A%d" % (src,)

def policy(state: dict) -> str:
    try:
        my_pts = list(state['my_pts'])
        opp_pts = list(state['opp_pts'])
        my_bar = int(state['my_bar'])
        opp_bar = int(state['opp_bar'])
        my_off = int(state['my_off'])
        opp_off = int(state['opp_off'])
        dice = list(state.get('dice', []))
    except Exception:
        return "H:P,P"
    try:
        # pad / trim to 24
        if len(my_pts) != 24:
            # fix
            tmp = [0]*24
            for i in range(min(24, len(my_pts))):
                tmp[i] = int(my_pts[i])
            my_pts = tmp
        if len(opp_pts) != 24:
            tmp = [0]*24
            for i in range(min(24, len(opp_pts))):
                tmp[i] = int(opp_pts[i])
            opp_pts = tmp

        if len(dice) == 0:
            return "H:P,P"
        if len(dice) == 1:
            d = int(dice[0])
            srcs = _legal_sources(my_pts, opp_pts, my_bar, d)
            if not srcs:
                return "H:P,P"
            best_s = None
            best_v = -1e18
            best_res = None
            for s in srcs:
                r = _apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, s, d)
                if r is None:
                    continue
                n_my, n_opp, n_mbar, n_obar, n_moff = r
                v = _evaluate(n_my, n_opp, n_mbar, n_obar, n_moff, opp_off)
                # small tie-break: prefer higher point / hit
                if n_obar > opp_bar:
                    v += 2.0
                if v > best_v:
                    best_v = v
                    best_s = s
                    best_res = r
            if best_s is None:
                return "H:P,P"
            return "H:%s,P" % (_tok(best_s),)

        # len >=2 : use first two dice
        d0 = int(dice[0]); d1 = int(dice[1])
        hi = d0 if d0 >= d1 else d1
        lo = d1 if d0 >= d1 else d0
        if hi < 1 or hi > 6 or lo < 1 or lo > 6:
            return "H:P,P"
        orders = ['H'] if hi == lo else ['H', 'L']
        seqs = []  # (order,f1,f2,final_board tuple, num_moves)
        for order in orders:
            if order == 'H':
                die1, die2 = hi, lo
            else:
                die1, die2 = lo, hi
            srcs1 = _legal_sources(my_pts, opp_pts, my_bar, die1)
            cands1 = []
            if not srcs1:
                cands1 = [None]
            else:
                cands1 = srcs1
            for f1 in cands1:
                if f1 is None:
                    mid_my, mid_opp, mid_mbar, mid_obar, mid_moff = my_pts, opp_pts, my_bar, opp_bar, my_off
                    # need to copy for safety? keep as is
                    mid_my_c = mid_my[:]
                    mid_opp_c = mid_opp[:]
                else:
                    r1 = _apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, f1, die1)
                    if r1 is None:
                        continue
                    mid_my_c, mid_opp_c, mid_mbar, mid_obar, mid_moff = r1
                # second die sources from mid
                srcs2 = _legal_sources(mid_my_c, mid_opp_c, mid_mbar, die2)
                cands2 = []
                if not srcs2:
                    cands2 = [None]
                else:
                    cands2 = srcs2
                for f2 in cands2:
                    if f2 is None:
                        fin = (mid_my_c, mid_opp_c, mid_mbar, mid_obar, mid_moff)
                    else:
                        r2 = _apply_move(mid_my_c, mid_opp_c, mid_mbar, mid_obar, mid_moff, f2, die2)
                        if r2 is None:
                            continue
                        fin = r2
                    n_moves = (0 if f1 is None else 1) + (0 if f2 is None else 1)
                    seqs.append((order, f1, f2, fin, n_moves))
        if not seqs:
            return "H:P,P"
        max_n = max(s[4] for s in seqs)
        filt = [s for s in seqs if s[4] == max_n]
        if max_n == 1 and hi != lo:
            def plays_hi(s):
                order, f1, f2, _, _ = s
                if order == 'H':
                    return f1 is not None
                else:
                    return f2 is not None
            hi_seqs = [s for s in filt if plays_hi(s)]
            if hi_seqs:
                filt = hi_seqs
        # choose best by evaluation
        best = None
        best_v = -1e18
        for order, f1, f2, fin, nm in filt:
            n_my, n_opp, n_mbar, n_obar, n_moff = fin
            v = _evaluate(n_my, n_opp, n_mbar, n_obar, n_moff, opp_off)
            # tie-break bonuses: hits, making points, bearing off
            if n_obar > opp_bar:
                v += 1.0
            if n_moff > my_off:
                v += 1.0
            # prefer using more pips when equal? small
            if v > best_v:
                best_v = v
                best = (order, f1, f2)
        if best is None:
            # fallback to first
            order, f1, f2, _, _ = filt[0]
            best = (order, f1, f2)
        order, f1, f2 = best
        return "%s:%s,%s" % (order, _tok(f1), _tok(f2))
    except Exception:
        # last resort: try to find any move greedily
        try:
            dice2 = list(state.get('dice', []))
            if len(dice2) >= 2:
                hi2 = max(int(dice2[0]), int(dice2[1]))
                # try bar then points
                my_pts2 = list(state['my_pts'])
                opp_pts2 = list(state['opp_pts'])
                my_bar2 = int(state['my_bar'])
                cand = _legal_sources(my_pts2, opp_pts2, my_bar2, hi2)
                if cand:
                    s = cand[0]
                    return "H:%s,P" % (_tok(s),)
                lo2 = min(int(dice2[0]), int(dice2[1]))
                cand2 = _legal_sources(my_pts2, opp_pts2, my_bar2, lo2)
                if cand2:
                    s = cand2[0]
                    return "L:%s,P" % (_tok(s),)
            elif len(dice2) == 1:
                d = int(dice2[0])
                cand = _legal_sources(list(state['my_pts']), list(state['opp_pts']), int(state['my_bar']), d)
                if cand:
                    return "H:%s,P" % (_tok(cand[0]),)
        except Exception:
            pass
        return "H:P,P"
