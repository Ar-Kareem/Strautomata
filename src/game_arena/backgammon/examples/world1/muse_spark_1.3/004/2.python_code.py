
import time

def _try_apply_inplace(my_pts, opp_pts, my_bar, opp_bar, my_off, frm, die):
    # my_pts, opp_pts are already copied lists, mutated only on success
    # returns (new_my_bar, new_opp_bar, new_my_off, success)
    if frm == 'B':
        if my_bar <= 0:
            return my_bar, opp_bar, my_off, False
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return my_bar, opp_bar, my_off, False
        if opp_pts[dest] >= 2:
            return my_bar, opp_bar, my_off, False
        my_bar -= 1
        if opp_pts[dest] == 1:
            opp_pts[dest] = 0
            opp_bar += 1
        my_pts[dest] += 1
        return my_bar, opp_bar, my_off, True
    else:
        try:
            i = int(frm[1:])
        except:
            return my_bar, opp_bar, my_off, False
        if i < 0 or i >= 24:
            return my_bar, opp_bar, my_off, False
        if my_bar > 0:
            return my_bar, opp_bar, my_off, False
        if my_pts[i] == 0:
            return my_bar, opp_bar, my_off, False
        dest = i - die
        if dest >= 0:
            if opp_pts[dest] >= 2:
                return my_bar, opp_bar, my_off, False
            my_pts[i] -= 1
            if opp_pts[dest] == 1:
                opp_pts[dest] = 0
                opp_bar += 1
            my_pts[dest] += 1
            return my_bar, opp_bar, my_off, True
        else:
            # bear off attempt
            if my_bar != 0:
                return my_bar, opp_bar, my_off, False
            for k in range(6, 24):
                if my_pts[k] != 0:
                    return my_bar, opp_bar, my_off, False
            if dest == -1:
                my_pts[i] -= 1
                my_off += 1
                return my_bar, opp_bar, my_off, True
            else:  # dest < -1 overshoot: only highest occupied
                for k in range(5, i, -1):
                    if my_pts[k] != 0:
                        return my_bar, opp_bar, my_off, False
                my_pts[i] -= 1
                my_off += 1
                return my_bar, opp_bar, my_off, True

def _gen_legal(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, dice):
    # returns list of (order,f1,f2, n_my,n_opp,n_bar,n_obar,n_off)
    if dice is None:
        dice = []
    dice = list(dice)
    if len(dice) == 0:
        return [('H', 'P', 'P', my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0)]
    if len(dice) == 1:
        d0 = dice[0]
        res = []
        if my_bar0 > 0:
            opts = ['B', 'P']
        else:
            opts = ['A%d' % i for i in range(24) if my_pts0[i] > 0] + ['P']
        for f1 in opts:
            if f1 == 'P':
                res.append(('H', 'P', 'P', my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0))
            else:
                nm = my_pts0[:]; no = opp_pts0[:]
                nb, nob, noff, ok = _try_apply_inplace(nm, no, my_bar0, opp_bar0, my_off0, f1, d0)
                if not ok:
                    continue
                res.append(('H', f1, 'P', nm, no, nb, nob, noff))
        # filter max played
        if not res:
            return [('H', 'P', 'P', my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0)]
        maxp = 0
        for _, f1, _, _, _, _, _, _ in res:
            p = 0 if f1 == 'P' else 1
            if p > maxp:
                maxp = p
        filt = [r for r in res if (0 if r[1] == 'P' else 1) == maxp]
        return filt
    if len(dice) > 2:
        dice = dice[:2]
    a, b = dice[0], dice[1]
    if a == b:
        orders = [('H', a, b)]
    else:
        hi = a if a > b else b
        lo = b if a > b else a
        orders = [('H', hi, lo), ('L', lo, hi)]
    all_seq = []
    for order, d0, d1 in orders:
        if my_bar0 > 0:
            first_opts = ['B', 'P']
        else:
            first_opts = ['A%d' % i for i in range(24) if my_pts0[i] > 0] + ['P']
        for f1 in first_opts:
            if f1 == 'P':
                mid_my = my_pts0[:]; mid_opp = opp_pts0[:]
                mid_bar = my_bar0; mid_obar = opp_bar0; mid_off = my_off0
            else:
                mid_my = my_pts0[:]; mid_opp = opp_pts0[:]
                mid_bar, mid_obar, mid_off, ok = _try_apply_inplace(mid_my, mid_opp, my_bar0, opp_bar0, my_off0, f1, d0)
                if not ok:
                    continue
                # mid_my/mid_opp already mutated
            if mid_bar > 0:
                second_opts = ['B', 'P']
            else:
                second_opts = ['A%d' % i for i in range(24) if mid_my[i] > 0] + ['P']
            for f2 in second_opts:
                if f2 == 'P':
                    # copy to avoid aliasing across iterations
                    fm = mid_my[:]; fo = mid_opp[:]
                    all_seq.append((order, f1, f2, fm, fo, mid_bar, mid_obar, mid_off, d0, d1))
                else:
                    fm = mid_my[:]; fo = mid_opp[:]
                    nb, nob, noff, ok2 = _try_apply_inplace(fm, fo, mid_bar, mid_obar, mid_off, f2, d1)
                    if not ok2:
                        continue
                    all_seq.append((order, f1, f2, fm, fo, nb, nob, noff, d0, d1))
    if not all_seq:
        return [('H', 'P', 'P', my_pts0[:], opp_pts0[:], my_bar0, opp_bar0, my_off0)]
    # must-play-both filter
    maxp = 0
    for s in all_seq:
        p = (0 if s[1] == 'P' else 1) + (0 if s[2] == 'P' else 1)
        if p > maxp:
            maxp = p
    filt = [s for s in all_seq if (0 if s[1] == 'P' else 1) + (0 if s[2] == 'P' else 1) == maxp]
    if maxp == 1 and a != b:
        # must play higher
        best_used = -1
        for s in filt:
            _, f1, f2, _, _, _, _, _, d0, d1 = s
            if f1 != 'P' and f2 == 'P':
                used = d0
            elif f1 == 'P' and f2 != 'P':
                used = d1
            else:
                used = -1
            if used > best_used:
                best_used = used
        if best_used >= 0:
            filt2 = []
            for s in filt:
                _, f1, f2, _, _, _, _, _, d0, d1 = s
                if f1 != 'P' and f2 == 'P':
                    used = d0
                elif f1 == 'P' and f2 != 'P':
                    used = d1
                else:
                    used = -1
                if used == best_used:
                    filt2.append(s)
            if filt2:
                filt = filt2
    # strip dice info
    out = []
    for s in filt:
        out.append((s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7]))
    return out

def _static_eval(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    pip_my = my_bar * 25
    pip_opp = opp_bar * 25
    for i in range(24):
        n = my_pts[i]
        if n:
            pip_my += n * (i + 1)
        m = opp_pts[i]
        if m:
            pip_opp += m * (24 - i)
    s = 0.0
    s += (my_off - opp_off) * 55.0
    s += (pip_opp - pip_my) * 1.2
    s += -14.0 * my_bar + 12.0 * opp_bar
    # made / blot / stack
    my_run = 0
    my_best = 0
    cur = 0
    opp_run = 0
    opp_best = 0
    ocur = 0
    for i in range(24):
        n = my_pts[i]
        if n == 1:
            s -= 7.0
            # extra blot in home when not bearing off is riskier
            if 6 <= i <= 17:
                s -= 1.0
            cur = 0
        elif n >= 2:
            s += 5.0
            if n > 3:
                s -= (n - 3) * 4.5
            if i <= 5:
                s += 4.0
                if i == 4:
                    s += 6.0
                if i == 3:
                    s += 3.0
                if i == 5:
                    s += 3.0
            if i == 6:
                s += 5.0
            if i >= 18:
                s += 3.0
                if i == 19:
                    s += 9.0
                if i == 18:
                    s += 4.0
            if i == 17:
                s += 2.0
            cur += 1
            if cur > my_best:
                my_best = cur
        else:
            cur = 0
        m = opp_pts[i]
        if m == 1:
            s += 4.0
            ocur = 0
        elif m >= 2:
            s -= 5.0
            if i >= 18:
                s -= 4.0
            if i <= 5:
                s -= 3.5
            ocur += 1
            if ocur > opp_best:
                opp_best = ocur
        else:
            ocur = 0
    if my_best >= 2:
        s += my_best * my_best * 1.6
    if opp_best >= 2:
        s -= opp_best * opp_best * 1.8
    # shot danger for our blots
    if opp_bar > 0:
        for i in range(0, 6):
            if my_pts[i] == 1:
                s -= 13.0
    else:
        # precompute opp presence
        # for each blot look back 1..6
        for i in range(24):
            if my_pts[i] == 1:
                hit = False
                cnt = 0
                lo = i - 6
                if lo < 0:
                    lo = 0
                for j in range(lo, i):
                    if opp_pts[j] > 0:
                        hit = True
                        cnt += 1
                if hit:
                    # blots far ahead with many attackers worse
                    pen = 10.0 + cnt * 2.0
                    # blots in home that opp must still pass are slightly less urgent if opp far?
                    # increase penalty if blot is in outer boards
                    if i <= 5:
                        pen += 2.0
                    s -= pen
    # containment: opp on bar and we hold points in our home/opp entry
    if opp_bar > 0:
        closed = 0
        for i in range(18, 24):
            if my_pts[i] >= 2:
                closed += 1
        # actually opp enters at 24-die = 18..23? No opp enters at 0..5.
        # correct: opp entry is 0..5, so holding home blocks
        closed_home = 0
        for i in range(0, 6):
            if my_pts[i] >= 2:
                closed_home += 1
        s += closed_home * 3.0
    return s

def _opp_best_for_dice(o_pts, m_pts, o_bar, m_bar, o_off, m_off, dice, m_pts_for_eval, o_pts_for_eval, m_bar_e, o_bar_e, m_off_e, o_off_e):
    # generate opp legal moves, return min eval from our perspective
    # o_pts etc are opponent's "my" perspective
    seqs = _gen_legal(o_pts, m_pts, o_bar, m_bar, o_off, dice)
    best = None
    for (_, _, _, nm_o, nm_m, nb_o, nb_m, noff_o) in seqs:
        # map back: nm_o is new opp pts, nm_m is new my pts
        v = _static_eval(nm_m, nm_o, nb_m, nb_o, m_off_e, noff_o if False else o_off_e if False else 0)
        # need correct offs: my off unchanged, opp off = noff_o
        # recompute properly:
        v = _static_eval(nm_m, nm_o, nb_m, nb_o, m_off_e, noff_o)
        if best is None or v < best:
            best = v
    if best is None:
        return _static_eval(m_pts_for_eval, o_pts_for_eval, m_bar_e, o_bar_e, m_off_e, o_off_e)
    return best

def policy(state: dict) -> str:
    try:
        my_pts0 = list(state['my_pts'])
        opp_pts0 = list(state['opp_pts'])
        my_bar0 = int(state['my_bar'])
        opp_bar0 = int(state['opp_bar'])
        my_off0 = int(state['my_off'])
        opp_off0 = int(state['opp_off'])
        dice = list(state.get('dice', []))
    except Exception:
        return "H:P,P"
    try:
        t0 = time.time()
        if len(dice) == 0:
            return "H:P,P"
        seqs = _gen_legal(my_pts0, opp_pts0, my_bar0, opp_bar0, my_off0, dice)
        if not seqs:
            return "H:P,P"
        if len(seqs) == 1:
            o, f1, f2, _, _, _, _, _ = seqs[0]
            return "%s:%s,%s" % (o, f1, f2)
        # static scores
        scored = []
        for s in seqs:
            o, f1, f2, nm, no, nb, nob, noff = s
            v = _static_eval(nm, no, nb, nob, noff, opp_off0)
            scored.append((v, s))
        scored.sort(key=lambda x: x[0], reverse=True)
        # if many, keep top for lookahead
        K = 8 if len(scored) > 8 else len(scored)
        top = scored[:K]
        # if race / no contact, skip deep search (static enough) - still do quick expected if time
        # do expected opponent reply for top candidates
        best_move = scored[0][1]
        best_exp = scored[0][0]
        # only do 2-ply if contact and time allows
        # detect contact: any overlapping ranges
        try:
            # quick contact check
            contact = False
            for i in range(24):
                if my_pts0[i] > 0:
                    for j in range(24):
                        if opp_pts0[j] > 0:
                            # if they haven't passed each other, contact possible
                            # opp moves up, my moves down: contact if j < i+6 or so? simplified: if both not borne off and not separated
                            pass
                    break
            # always do expected but with time limit
            use_search = True
            # if huge pip and no blots, static is fine; still search is cheap
            exps = []
            for v_static, s in top:
                if time.time() - t0 > 0.75:
                    break
                o, f1, f2, nm, no, nb, nob, noff = s
                total = 0.0
                # 21 dice combos
                for a in range(1, 7):
                    for b in range(a, 7):
                        w = 1 if a == b else 2
                        d = [a, b] if a == b else [a, b]
                        # opp perspective lists: opp is "my"
                        # need copies
                        o_pts = no[:]
                        m_pts = nm[:]
                        bv = _opp_best_for_dice(o_pts, m_pts, nob, nb, opp_off0, noff, d, m_pts, o_pts, nb, nob, noff, opp_off0)
                        total += w * bv
                exp = total / 36.0
                # blend static and expected to stabilize (expected dominates)
                exps.append((exp, s))
            if exps:
                exps.sort(key=lambda x: x[0], reverse=True)
                best_exp_s = exps[0][1]
                return "%s:%s,%s" % (best_exp_s[0], best_exp_s[1], best_exp_s[2])
            else:
                o, f1, f2, _, _, _, _, _ = best_move
                return "%s:%s,%s" % (o, f1, f2)
        except Exception:
            o, f1, f2, _, _, _, _, _ = scored[0][1]
            return "%s:%s,%s" % (o, f1, f2)
    except Exception:
        try:
            # emergency fallback: try to find any stepwise move for higher die
            d = dice[0] if len(dice) > 0 else 1
            if my_bar0 > 0:
                dest = 24 - d
                if dest >= 0 and dest < 24 and opp_pts0[dest] < 2:
                    hi = max(dice) if len(dice) >= 2 else d
                    lo = min(dice) if len(dice) >= 2 else d
                    # guess order
                    if len(dice) >= 2 and d == hi:
                        return "H:B,P"
                    elif len(dice) >= 2:
                        return "L:B,P"
                    else:
                        return "H:B,P"
            for i in range(24):
                if my_pts0[i] > 0:
                    dest = i - d
                    if dest >= 0 and opp_pts0[dest] < 2:
                        return "H:A%d,P" % i
                    if dest < 0:
                        # bear off possible?
                        ok = True
                        if my_bar0 != 0:
                            ok = False
                        else:
                            for k in range(6, 24):
                                if my_pts0[k] != 0:
                                    ok = False
                                    break
                        if ok:
                            return "H:A%d,P" % i
            return "H:P,P"
        except Exception:
            return "H:P,P"
