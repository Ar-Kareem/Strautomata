
def _tok(f):
    if f == 'B':
        return 'B'
    if f == 'P' or f is None:
        return 'P'
    return f"A{f}"

def _all_home(my_pts, my_bar):
    if my_bar != 0:
        return False
    for i in range(6, 24):
        if my_pts[i] != 0:
            return False
    return True

def _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, frm, die):
    # returns new tuple or None if illegal
    # frm: 'B' or int 0..23
    n_my = list(my_pts)
    n_opp = list(opp_pts)
    n_my_bar = my_bar
    n_opp_bar = opp_bar
    n_my_off = my_off
    n_opp_off = opp_off
    if frm == 'B':
        if n_my_bar <= 0:
            return None
        dest = 24 - die
        if dest < 0 or dest >= 24:
            return None
        if n_opp[dest] >= 2:
            return None
        n_my_bar -= 1
        if n_opp[dest] == 1:
            n_opp[dest] = 0
            n_opp_bar += 1
            n_my[dest] = n_my[dest] + 1 if dest >= 0 else 0
            # actually dest always on board here
        else:
            n_my[dest] += 1
        return (n_my, n_opp, n_my_bar, n_opp_bar, n_my_off, n_opp_off)
    else:
        idx = frm
        if idx < 0 or idx >= 24:
            return None
        if n_my[idx] <= 0:
            return None
        dest = idx - die
        if dest >= 0:
            if n_opp[dest] >= 2:
                return None
            n_my[idx] -= 1
            if n_opp[dest] == 1:
                n_opp[dest] = 0
                n_opp_bar += 1
                n_my[dest] += 1
            else:
                n_my[dest] += 1
            return (n_my, n_opp, n_my_bar, n_opp_bar, n_my_off, n_opp_off)
        else:
            # bear off attempt
            if not _all_home(n_my, n_my_bar):
                return None
            need = idx + 1
            if need == die:
                n_my[idx] -= 1
                n_my_off += 1
                return (n_my, n_opp, n_my_bar, n_opp_bar, n_my_off, n_opp_off)
            elif need < die:
                # overshoot only if no higher home checkers
                for k in range(idx + 1, 6):
                    if n_my[k] > 0:
                        return None
                n_my[idx] -= 1
                n_my_off += 1
                return (n_my, n_opp, n_my_bar, n_opp_bar, n_my_off, n_opp_off)
            else:
                return None

def _legal_froms(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, die):
    res = []
    if my_bar > 0:
        r = _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, 'B', die)
        if r is not None:
            res.append('B')
        return res
    for i in range(24):
        if my_pts[i] > 0:
            r = _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, i, die)
            if r is not None:
                res.append(i)
    return res

def _evaluate(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off):
    score = 0.0
    score += (my_off - opp_off) * 25.0
    score += (opp_bar - my_bar) * 25.0
    my_pip = my_bar * 25
    opp_pip = opp_bar * 25
    for i, c in enumerate(my_pts):
        if c:
            my_pip += (i + 1) * c
    for i, c in enumerate(opp_pts):
        if c:
            opp_pip += (24 - i) * c
    score += (opp_pip - my_pip) * 1.0
    # made points and key points
    for i in range(24):
        mc = my_pts[i]
        oc = opp_pts[i]
        if mc >= 2:
            score += 4.0
            if i < 6:
                score += 3.0
            if i == 4 or i == 3 or i == 6:
                score += 2.0
            if i >= 18:
                score += 3.0
        elif mc == 1:
            score -= 2.0
        if oc >= 2:
            score -= 4.0
            if i >= 18:
                score -= 2.0
            if i < 6:
                score -= 1.0
        elif oc == 1:
            score += 1.0
    for i in range(24):
        if my_pts[i] > 3:
            score -= (my_pts[i] - 3) * 2.5
        if opp_pts[i] > 3:
            score += (opp_pts[i] - 3) * 1.0
    # prime
    def _run(pts):
        best = 0
        cur = 0
        for v in pts:
            if v >= 2:
                cur += 1
                if cur > best:
                    best = cur
            else:
                cur = 0
        return best
    mr = _run(my_pts)
    opr = _run(opp_pts)
    if mr >= 3:
        score += (mr - 2) * 4.0
    if opr >= 3:
        score -= (opr - 2) * 4.0
    # blot hit risk for us
    if opp_bar > 0:
        for i in range(6):
            if my_pts[i] == 1:
                score -= 10.0
    else:
        opp_pos = [j for j in range(24) if opp_pts[j] > 0]
        if opp_pos:
            for i in range(24):
                if my_pts[i] == 1:
                    s = set()
                    for j in opp_pos:
                        d = i - j
                        if 1 <= d <= 6:
                            s.add(d)
                    k = len(s)
                    if k > 0:
                        p = 1.0 - ((6.0 - k) / 6.0) ** 2
                        score -= p * 18.0
    # chance for us to hit opp blots
    if my_bar == 0:
        my_pos = [k2 for k2 in range(24) if my_pts[k2] > 0]
        if my_pos:
            for j in range(24):
                if opp_pts[j] == 1:
                    s = set()
                    for k2 in my_pos:
                        d = k2 - j
                        if 1 <= d <= 6:
                            s.add(d)
                    kk = len(s)
                    if kk > 0:
                        p = 1.0 - ((6.0 - kk) / 6.0) ** 2
                        score += p * 4.0
    return score

def _enumerate_candidates(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice):
    # returns list of (action_str, board_tuple, dice_used_values_list)
    if len(dice) == 0:
        init = (list(my_pts), list(opp_pts), my_bar, opp_bar, my_off, opp_off)
        return [("H:P,P", init, [])]
    if len(dice) == 1:
        d = dice[0]
        opts = _legal_froms(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d)
        if not opts:
            init = (list(my_pts), list(opp_pts), my_bar, opp_bar, my_off, opp_off)
            return [("H:P,P", init, [])]
        out = []
        for f in opts:
            nb = _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, f, d)
            if nb is None:
                continue
            act = f"H:{_tok(f)},P"
            out.append((act, nb, [d]))
        if not out:
            init = (list(my_pts), list(opp_pts), my_bar, opp_bar, my_off, opp_off)
            return [("H:P,P", init, [])]
        return out
    # len 2
    hi = dice[0] if dice[0] >= dice[1] else dice[1]
    lo = dice[1] if dice[0] >= dice[1] else dice[0]
    if hi == lo:
        orders = [('H', hi, lo)]
    else:
        orders = [('H', hi, lo), ('L', lo, hi)]
    cands = []
    for oc, d1, d2 in orders:
        firsts = _legal_froms(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d1)
        if not firsts:
            seconds = _legal_froms(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, d2)
            if not seconds:
                init = (list(my_pts), list(opp_pts), my_bar, opp_bar, my_off, opp_off)
                cands.append((f"{oc}:P,P", init, []))
            else:
                for s2 in seconds:
                    nb = _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, s2, d2)
                    if nb is None:
                        continue
                    cands.append((f"{oc}:P,{_tok(s2)}", nb, [d2]))
        else:
            for f1 in firsts:
                b1 = _apply_single(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, f1, d1)
                if b1 is None:
                    continue
                b1_my, b1_opp, b1_mbar, b1_obar, b1_moff, b1_ooff = b1
                seconds = _legal_froms(b1_my, b1_opp, b1_mbar, b1_obar, b1_moff, b1_ooff, d2)
                if not seconds:
                    cands.append((f"{oc}:{_tok(f1)},P", b1, [d1]))
                else:
                    for s2 in seconds:
                        b2 = _apply_single(b1_my, b1_opp, b1_mbar, b1_obar, b1_moff, b1_ooff, s2, d2)
                        if b2 is None:
                            continue
                        cands.append((f"{oc}:{_tok(f1)},{_tok(s2)}", b2, [d1, d2]))
    # dedup by action string keep first
    seen = {}
    for a, b, u in cands:
        if a not in seen:
            seen[a] = (a, b, u)
    cands = list(seen.values())
    if not cands:
        init = (list(my_pts), list(opp_pts), my_bar, opp_bar, my_off, opp_off)
        return [("H:P,P", init, [])]
    # max dice rule
    def _cnt(c):
        act = c[0]
        parts = act.split(":")[1].split(",")
        return (0 if parts[0] == "P" else 1) + (0 if parts[1] == "P" else 1)
    m = max(_cnt(c) for c in cands)
    cands = [c for c in cands if _cnt(c) == m]
    if m == 1:
        # keep only those using hi if any
        def _uses_hi(c):
            act, _, used = c
            if not used:
                return False
            return used[0] == hi
        any_hi = any(_uses_hi(c) for c in cands)
        if any_hi:
            cands = [c for c in cands if _uses_hi(c)]
    if m == 0:
        return [("H:P,P", (list(my_pts), list(opp_pts), my_bar, opp_bar, my_off, opp_off), [])]
    return cands

def policy(state: dict) -> str:
    try:
        my_pts = list(state['my_pts'])
        opp_pts = list(state['opp_pts'])
        my_bar = int(state['my_bar'])
        opp_bar = int(state['opp_bar'])
        my_off = int(state['my_off'])
        opp_off = int(state['opp_off'])
        dice = list(state['dice'])
        # sanitize dice
        dice = [int(d) for d in dice if 1 <= int(d) <= 6]
        if len(dice) > 2:
            dice = dice[:2]
        if len(dice) == 0:
            return "H:P,P"
        cands = _enumerate_candidates(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice)
        if len(cands) == 1:
            return cands[0][0]
        # score
        best_a = cands[0][0]
        best_s = -1e18
        # prefer H and non-P first on ties
        for act, board, used in cands:
            b_my, b_opp, b_mbar, b_obar, b_moff, b_ooff = board
            s = _evaluate(b_my, b_opp, b_mbar, b_obar, b_moff, b_ooff)
            # tiny tie-break: prefer making points / hitting, prefer H, prefer first non-P
            if act[0] == 'H':
                s += 0.001
            parts = act.split(":")[1].split(",")
            if parts[0] != "P":
                s += 0.0005
            # prefer more advanced? no
            if s > best_s:
                best_s = s
                best_a = act
        return best_a
    except Exception:
        try:
            # emergency fallback: try to find any legal single/double move
            my_pts = list(state.get('my_pts', [0]*24))
            opp_pts = list(state.get('opp_pts', [0]*24))
            my_bar = int(state.get('my_bar', 0))
            opp_bar = int(state.get('opp_bar', 0))
            my_off = int(state.get('my_off', 0))
            opp_off = int(state.get('opp_off', 0))
            dice = list(state.get('dice', []))
            dice = [int(d) for d in dice if 1 <= int(d) <= 6][:2]
            if len(dice) == 0:
                return "H:P,P"
            cands = _enumerate_candidates(my_pts, opp_pts, my_bar, opp_bar, my_off, opp_off, dice)
            if cands:
                # return first with max dice (already filtered)
                # prefer H:P,P if pass
                for c in cands:
                    if c[0] == "H:P,P":
                        return "H:P,P"
                return cands[0][0]
        except Exception:
            pass
        return "H:P,P"
