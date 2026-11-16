
def _moves_for_die(my, opp, my_bar, d):
    """Return list of legal FROM tokens ('B' or int point) for a single die."""
    res = []
    if my_bar > 0:
        t = 24 - d
        if opp[t] < 2:
            res.append('B')
        return res
    can_bear = not any(my[6:])
    for s in range(24):
        if my[s] == 0:
            continue
        t = s - d
        if t >= 0:
            if opp[t] < 2:
                res.append(s)
        elif can_bear:
            if d == s + 1:
                res.append(s)
            elif d > s + 1:
                ok = True
                for x in range(s + 1, 6):
                    if my[x]:
                        ok = False
                        break
                if ok:
                    res.append(s)
    return res


def _apply(my, opp, my_bar, my_off, opp_bar, frm, d):
    """Apply one checker move; returns (my, opp, my_bar, my_off, opp_bar)."""
    my = my[:]
    opp = opp[:]
    if frm == 'B':
        my_bar -= 1
        t = 24 - d
    else:
        my[frm] -= 1
        t = frm - d
        if t < 0:
            my_off += 1
            return (my, opp, my_bar, my_off, opp_bar)
    if opp[t] == 1:
        opp[t] = 0
        opp_bar += 1
    my[t] += 1
    return (my, opp, my_bar, my_off, opp_bar)


def _gen_ordered(my, opp, my_bar, my_off, opp_bar, d1, d2):
    """Generate all legal move sequences for an ordered pair of dice (d2 may be None)."""
    out = []
    for f1 in _moves_for_die(my, opp, my_bar, d1):
        st = _apply(my, opp, my_bar, my_off, opp_bar, f1, d1)
        if d2 is None:
            out.append(([f1], st))
            continue
        fs = _moves_for_die(st[0], st[1], st[2], d2)
        if not fs:
            out.append(([f1], st))
        else:
            for f2 in fs:
                st2 = _apply(st[0], st[1], st[2], st[3], st[4], f2, d2)
                out.append(([f1, f2], st2))
    return out


def _evaluate(my, opp, my_bar, my_off, opp_bar, opp_off):
    """Static position evaluation from our perspective (higher is better)."""
    val = 40.0 * (my_off - opp_off) + 10.0 * (opp_bar - my_bar)
    my_pip = 25 * my_bar
    opp_pip = 25 * opp_bar
    my_run = 0   # consecutive made points (prime length)
    opp_run = 0
    for i in range(24):
        m = my[i]
        o = opp[i]
        my_pip += m * (i + 1)
        opp_pip += o * (i + 1)

        if m >= 2:
            w = 4.0
            if i <= 5:      # made point in our home board (closing)
                w += 3.0
            elif i >= 18:   # anchor in opponent's home board
                w += 5.0
            val += w
            my_run += 1
        else:
            if my_run >= 2:
                val += (my_run - 1) * 1.5
            my_run = 0
            if m == 1:
                val -= 5.0  # our blot

        if o >= 2:
            w = 4.0
            if i >= 18:     # opponent home-board point
                w += 3.0
            elif i <= 5:    # opponent anchor in our home board
                w += 5.0
            val -= w
            opp_run += 1
        else:
            if opp_run >= 2:
                val -= (opp_run - 1) * 1.5
            opp_run = 0
            if o == 1:
                val += 5.0  # vulnerable opponent blot

    val += 1.2 * (opp_pip - my_pip)
    return val


def _tok(frm):
    if frm == 'B':
        return 'B'
    return 'A' + str(frm)


def policy(state: dict) -> str:
    my = list(state['my_pts'])
    opp = list(state['opp_pts'])
    my_bar = state['my_bar']
    my_off = state['my_off']
    opp_bar = state['opp_bar']
    opp_off = state['opp_off']
    dice = state.get('dice') or []

    candidates = []  # (order_char, moves_list, final_state_tuple)

    if len(dice) == 1:
        d = dice[0]
        for ml, st in _gen_ordered(my, opp, my_bar, my_off, opp_bar, d, None):
            candidates.append(('H', ml, st))
    elif len(dice) >= 2:
        hi = max(dice[0], dice[1])
        lo = min(dice[0], dice[1])
        for ml, st in _gen_ordered(my, opp, my_bar, my_off, opp_bar, hi, lo):
            candidates.append(('H', ml, st))
        if hi != lo:
            for ml, st in _gen_ordered(my, opp, my_bar, my_off, opp_bar, lo, hi):
                candidates.append(('L', ml, st))

    if not candidates:
        return "H:P,P"

    # Forced-dice rules: use as many dice as possible; if only one die can be
    # used, prefer the higher die when possible.
    max_len = max(len(ml) for _, ml, _ in candidates)
    filtered = [c for c in candidates if len(c[1]) == max_len]
    if max_len == 1:
        hi_first = [c for c in filtered if c[0] == 'H']
        if hi_first:
            filtered = hi_first

    best = max(filtered, key=lambda c: _evaluate(c[2][0], c[2][1], c[2][2],
                                                 c[2][3], c[2][4], opp_off))
    order, ml, _ = best
    t1 = _tok(ml[0])
    t2 = _tok(ml[1]) if len(ml) > 1 else 'P'
    return order + ':' + t1 + ',' + t2
