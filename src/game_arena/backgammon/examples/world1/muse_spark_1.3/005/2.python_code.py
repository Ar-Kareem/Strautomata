
def _copy_board(state):
    return {
        'my_pts': list(state['my_pts']),
        'opp_pts': list(state['opp_pts']),
        'my_bar': int(state['my_bar']),
        'opp_bar': int(state['opp_bar']),
        'my_off': int(state['my_off']),
        'opp_off': int(state['opp_off']),
    }

def _can_bear_off(b):
    if b['my_bar'] != 0:
        return False
    # all remaining checkers in 0..5
    for i in range(6, 24):
        if b['my_pts'][i] != 0:
            return False
    return True

def _legal_single(b, die):
    # returns list of FROM tokens: 'B' or int 0..23
    res = []
    if b['my_bar'] > 0:
        e = 24 - die
        if 0 <= e < 24 and b['opp_pts'][e] < 2:
            res.append('B')
        return res
    can_off = _can_bear_off(b)
    for s in range(24):
        if b['my_pts'][s] <= 0:
            continue
        dest = s - die
        if dest >= 0:
            if b['opp_pts'][dest] >= 2:
                continue
            res.append(s)
        else:
            # bear off attempt
            if not can_off:
                continue
            dist = s + 1
            if die == dist:
                res.append(s)
            elif die > dist:
                # only if no checkers on higher home points
                higher = False
                for h in range(s + 1, 6):
                    if b['my_pts'][h] > 0:
                        higher = True
                        break
                if not higher:
                    res.append(s)
                # else illegal
            # else die < dist cannot happen when dest<0? dest<0 => s<die => dist<=die, so covered
    return res

def _apply_move(b, frm, die):
    # assume legal (except 'P'), returns new board
    nb = {
        'my_pts': list(b['my_pts']),
        'opp_pts': list(b['opp_pts']),
        'my_bar': b['my_bar'],
        'opp_bar': b['opp_bar'],
        'my_off': b['my_off'],
        'opp_off': b['opp_off'],
    }
    if frm == 'P':
        return nb
    if frm == 'B':
        # must have bar checker
        if nb['my_bar'] <= 0:
            return None
        e = 24 - die
        if nb['opp_pts'][e] >= 2:
            return None
        nb['my_bar'] -= 1
        if nb['opp_pts'][e] == 1:
            nb['opp_pts'][e] = 0
            nb['opp_bar'] += 1
            nb['my_pts'][e] += 1
        else:
            nb['my_pts'][e] += 1
        return nb
    else:
        s = int(frm)
        if nb['my_pts'][s] <= 0:
            return None
        dest = s - die
        nb['my_pts'][s] -= 1
        if dest >= 0:
            if nb['opp_pts'][dest] >= 2:
                return None
            if nb['opp_pts'][dest] == 1:
                nb['opp_pts'][dest] = 0
                nb['opp_bar'] += 1
                nb['my_pts'][dest] += 1
            else:
                nb['my_pts'][dest] += 1
        else:
            # bear off
            nb['my_off'] += 1
        return nb

def _fmt_token(frm):
    if frm == 'P':
        return 'P'
    if frm == 'B':
        return 'B'
    return f'A{int(frm)}'

def _enumerate_legal(state):
    dice = list(state.get('dice', []))
    b0 = _copy_board(state)
    if len(dice) == 0:
        return [('H', 'P', 'P', b0)]
    if len(dice) == 1:
        d = int(dice[0])
        moves = _legal_single(b0, d)
        if not moves:
            return [('H', 'P', 'P', b0)]
        out = []
        for m in moves:
            nb = _apply_move(b0, m, d)
            if nb is not None:
                out.append(('H', m, 'P', nb))
        if not out:
            return [('H', 'P', 'P', b0)]
        return out
    # len >=2, use first two
    high = int(max(dice[0], dice[1]))
    low = int(min(dice[0], dice[1]))
    all_lines = []  # (order,f1,f2,board_after,count,used_die_for_single)
    for order, first, second in (('H', high, low), ('L', low, high)):
        first_opts = _legal_single(b0, first)
        if first_opts:
            first_cands = list(first_opts) + ['P']
        else:
            first_cands = ['P']
        for f1 in first_cands:
            if f1 == 'P':
                b1 = _copy_board(b0) if False else {'my_pts': list(b0['my_pts']), 'opp_pts': list(b0['opp_pts']), 'my_bar': b0['my_bar'], 'opp_bar': b0['opp_bar'], 'my_off': b0['my_off'], 'opp_off': b0['opp_off']}
                # b1 is copy of b0
                b1 = {'my_pts': list(b0['my_pts']), 'opp_pts': list(b0['opp_pts']), 'my_bar': b0['my_bar'], 'opp_bar': b0['opp_bar'], 'my_off': b0['my_off'], 'opp_off': b0['opp_off']}
            else:
                b1 = _apply_move(b0, f1, first)
                if b1 is None:
                    continue
            second_opts = _legal_single(b1, second)
            if second_opts:
                second_cands = list(second_opts) + ['P']
            else:
                second_cands = ['P']
            for f2 in second_cands:
                if f2 == 'P':
                    b2 = b1
                else:
                    b2 = _apply_move(b1, f2, second)
                    if b2 is None:
                        continue
                cnt = (0 if f1 == 'P' else 1) + (0 if f2 == 'P' else 1)
                all_lines.append((order, f1, f2, b2, cnt, first, second))
    if not all_lines:
        return [('H', 'P', 'P', b0)]
    max_c = max(l[4] for l in all_lines)
    cand = [l for l in all_lines if l[4] == max_c]
    if max_c == 1 and high != low:
        # keep only lines using high die
        def uses_high(l):
            order, f1, f2 = l[0], l[1], l[2]
            if order == 'H':
                # f1 is high, f2 is low
                if f1 != 'P':
                    return True  # high used
                else:
                    return False  # low used
            else:
                # L: f1 low, f2 high
                if f1 != 'P':
                    return False
                else:
                    return True
        high_cand = [l for l in cand if uses_high(l)]
        if high_cand:
            cand = high_cand
    elif max_c == 0:
        return [('H', 'P', 'P', b0)]
    # deduplicate to (order,f1,f2)
    seen = set()
    uniq = []
    for order, f1, f2, b2, cnt, _, _ in cand:
        key = (order, str(f1), str(f2))
        if key in seen:
            continue
        seen.add(key)
        uniq.append((order, f1, f2, b2))
    return uniq

def _evaluate(b):
    my_pts = b['my_pts']
    opp_pts = b['opp_pts']
    my_bar = b['my_bar']
    opp_bar = b['opp_bar']
    my_off = b['my_off']
    opp_off = b['opp_off']
    my_pip = my_bar * 25
    opp_pip = opp_bar * 25
    for i, c in enumerate(my_pts):
        if c:
            my_pip += (i + 1) * c
    for i, c in enumerate(opp_pts):
        if c:
            opp_pip += (24 - i) * c
    score = float(opp_pip - my_pip) * 1.0
    score += float(my_off - opp_off) * 12.0
    score -= float(my_bar) * 25.0
    score += float(opp_bar) * 15.0
    # blot vulnerability: my blot hittable?
    # precompute opp occupancy for direct shots
    my_blot_pen = 0.0
    my_made = 0
    my_home_made = 0
    stack_pen = 0
    cur = 0
    maxprime = 0
    for i, c in enumerate(my_pts):
        if c == 1:
            vulnerable = False
            if opp_bar > 0 and i < 6:
                vulnerable = True
            else:
                # direct shot by opp from behind (opp moves +)
                lo = max(0, i - 6)
                for j in range(lo, i):
                    if opp_pts[j] > 0:
                        vulnerable = True
                        break
            if vulnerable:
                my_blot_pen += 12.0
                # extra if in opp home / outer where many attackers?
                if i >= 12:
                    my_blot_pen += 2.0
            else:
                my_blot_pen += 2.0
        elif c >= 2:
            my_made += 1
            if i < 6:
                my_home_made += 1
            cur += 1
            if cur > maxprime:
                maxprime = cur
            if c > 2:
                stack_pen += (c - 2)
        else:
            # c == 0 breaks prime
            cur = 0
            # need to handle cur reset correctly: above counts consecutive made
            # but blots/empty break; we already handle made increment, so reset
        if c == 0 or c == 1:
            # prime broken (only >=2 continues)
            # cur already managed: if not >=2, reset
            if c < 2:
                cur = 0
    # fix prime calc: recompute cleanly for correctness
    best = 0
    run = 0
    for c in my_pts:
        if c >= 2:
            run += 1
            if run > best:
                best = run
        else:
            run = 0
    maxprime = best
    opp_blot_bonus = 0.0
    opp_made = 0
    opp_run = 0
    opp_best = 0
    for i, c in enumerate(opp_pts):
        if c == 1:
            # can we hit? my checker ahead (greater index) within 6?
            hittable = False
            hi = min(24, i + 7)
            for j in range(i + 1, hi):
                if my_pts[j] > 0:
                    hittable = True
                    break
            if hittable:
                opp_blot_bonus += 7.0
            else:
                opp_blot_bonus += 3.0
        elif c >= 2:
            opp_made += 1
            opp_run += 1
            if opp_run > opp_best:
                opp_best = opp_run
        else:
            opp_run = 0
        if c < 2 and c != 1:
            pass
    # need correct opp prime reset for blots too
    opp_best = 0
    r = 0
    for c in opp_pts:
        if c >= 2:
            r += 1
            if r > opp_best:
                opp_best = r
        else:
            r = 0
    score -= my_blot_pen
    score += opp_blot_bonus
    score += my_made * 3.0
    score += my_home_made * 5.0
    score += maxprime * maxprime * 1.2
    score -= stack_pen * 1.0
    score -= opp_made * 2.0
    score -= opp_best * opp_best * 0.8
    # anchor in opp home
    anchored = False
    for i in range(18, 24):
        if my_pts[i] >= 2:
            anchored = True
            break
    if anchored:
        score += 7.0
    # containment when opp on bar: extra for closed home
    if opp_bar > 0:
        score += my_home_made * 4.0
    # race vs contact: if no contact, pip matters more (already)
    return score

def policy(state: dict) -> str:
    try:
        cands = _enumerate_legal(state)
        if len(cands) == 1:
            o, f1, f2, _ = cands[0]
            return f"{o}:{_fmt_token(f1)},{_fmt_token(f2)}"
        best = None
        best_s = None
        for o, f1, f2, b2 in cands:
            s = _evaluate(b2)
            # tiny tie-breaker: prefer hits / off / making points: use off and bar diff
            # add microscopic bonus for bearing off and hitting to break ties deterministically
            s += (b2['my_off'] * 0.001) + (b2['opp_bar'] * 0.001)
            # prefer higher FROM for determinism? add small
            if best_s is None or s > best_s:
                best_s = s
                best = (o, f1, f2)
        if best is None:
            return "H:P,P"
        o, f1, f2 = best
        return f"{o}:{_fmt_token(f1)},{_fmt_token(f2)}"
    except Exception:
        try:
            dice = list(state.get('dice', []))
            my_bar = int(state.get('my_bar', 0))
            if len(dice) == 0:
                return "H:P,P"
            if len(dice) == 1:
                d = int(dice[0])
                b0 = _copy_board(state)
                m = _legal_single(b0, d)
                if not m:
                    return "H:P,P"
                return f"H:{_fmt_token(m[0])},P"
            high = int(max(dice))
            low = int(min(dice))
            b0 = _copy_board(state)
            # try to play both greedily H then L
            for order, first, second in (('H', high, low), ('L', low, high)):
                f1o = _legal_single(b0, first)
                if not f1o:
                    continue
                for f1 in f1o:
                    b1 = _apply_move(b0, f1, first)
                    if b1 is None:
                        continue
                    f2o = _legal_single(b1, second)
                    if f2o:
                        return f"{order}:{_fmt_token(f1)},{_fmt_token(f2o[0])}"
            # try single high
            for order, d in (('H', high), ('L', low)):
                # need correct order mapping for single: H uses high, L uses low
                pass
            fh = _legal_single(b0, high)
            if fh:
                return f"H:{_fmt_token(fh[0])},P"
            fl = _legal_single(b0, low)
            if fl:
                return f"L:{_fmt_token(fl[0])},P"
            return "H:P,P"
        except Exception:
            return "H:P,P"
