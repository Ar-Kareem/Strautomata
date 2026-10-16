
def _apply_move(state, frm, die):
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']

    if my_bar > 0 and frm != 'B':
        return None

    if frm == 'B':
        if my_bar == 0:
            return None
        to = 24 - die
        if not (0 <= to <= 23):
            return None
        if opp_pts[to] >= 2:
            return None
        my_bar -= 1
        if opp_pts[to] == 1:
            opp_pts[to] = 0
            opp_bar += 1
        my_pts[to] += 1
    else:
        p = frm
        if not (0 <= p <= 23) or my_pts[p] == 0:
            return None
        to = p - die
        if to >= 0:
            if opp_pts[to] >= 2:
                return None
            my_pts[p] -= 1
            if opp_pts[to] == 1:
                opp_pts[to] = 0
                opp_bar += 1
            my_pts[to] += 1
        else:
            if my_bar > 0:
                return None
            for i in range(6, 24):
                if my_pts[i] > 0:
                    return None
            if to == -1:
                my_pts[p] -= 1
                my_off += 1
            else:
                for i in range(p + 1, 6):
                    if my_pts[i] > 0:
                        return None
                my_pts[p] -= 1
                my_off += 1

    return {'my_pts': my_pts, 'opp_pts': opp_pts, 'my_bar': my_bar,
            'opp_bar': opp_bar, 'my_off': my_off, 'opp_off': opp_off}


def _try_singles(state, die):
    results = []
    if state['my_bar'] > 0:
        ns = _apply_move(state, 'B', die)
        if ns is not None:
            results.append(('B', ns))
        return results
    for p in range(24):
        if state['my_pts'][p] > 0:
            ns = _apply_move(state, p, die)
            if ns is not None:
                results.append(('A' + str(p), ns))
    return results


def _enumerate(state, dice):
    if len(dice) == 0:
        return [('H:P,P', state)]

    if len(dice) == 1:
        d = dice[0]
        singles = _try_singles(state, d)
        if singles:
            return [('H:' + frm + ',P', ns) for frm, ns in singles]
        return [('H:P,P', state)]

    d1, d2 = dice[0], dice[1]
    high = max(d1, d2)
    low = min(d1, d2)

    both = []
    orders = [(high, 'H')]
    if high != low:
        orders.append((low, 'L'))

    for first_die, order in orders:
        second_die = d1 + d2 - first_die
        firsts = _try_singles(state, first_die)
        for frm1, s1 in firsts:
            seconds = _try_singles(s1, second_die)
            for frm2, s2 in seconds:
                both.append((order + ':' + frm1 + ',' + frm2, s2))

    if both:
        return both

    high_only = _try_singles(state, high)
    if high_only:
        return [('H:' + frm + ',P', ns) for frm, ns in high_only]

    low_only = _try_singles(state, low)
    if low_only:
        return [('L:' + frm + ',P', ns) for frm, ns in low_only]

    return [('H:P,P', state)]


def _evaluate(state):
    score = 0.0
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']

    score += state['my_off'] * 20.0
    score -= state['opp_off'] * 20.0

    my_pip = sum((i + 1) * my_pts[i] for i in range(24)) + 25 * state['my_bar']
    opp_pip = sum((24 - i) * opp_pts[i] for i in range(24)) + 25 * state['opp_bar']

    score -= my_pip * 0.35
    score += opp_pip * 0.35

    score += state['opp_bar'] * 12.0
    score -= state['my_bar'] * 12.0

    # Count opponent checkers remaining that could hit
    opp_has_contact = any(opp_pts[i] > 0 for i in range(24))

    for p in range(24):
        n = my_pts[p]
        if n == 1:
            danger = 0.0
            if state['opp_bar'] > 0 and p < 6:
                # opponent entering could hit directly
                danger += 10.0
            for opp_p in range(p):
                if opp_pts[opp_p] > 0:
                    dist = p - opp_p
                    if 1 <= dist <= 6:
                        danger += 5.0
                    elif dist <= 12:
                        danger += 1.5
            # Blots deep in our home board matter less if opponent can't reach
            if p < 6 and not any(opp_pts[i] > 0 for i in range(p)) and state['opp_bar'] == 0:
                danger = 0
            score -= danger
        elif n >= 2:
            bonus = 3.0
            if p <= 5:
                bonus = 5.5 if p == 4 else 5.0  # 5-point extra valuable
            elif p <= 7:
                bonus = 4.5
            elif p <= 11:
                bonus = 3.5
            score += bonus
            if n > 3:
                score -= (n - 3) * 1.5  # stacking penalty

    # Prime bonus
    consec = 0
    max_consec = 0
    for p in range(11, -1, -1):
        if my_pts[p] >= 2:
            consec += 1
            if consec > max_consec:
                max_consec = consec
        else:
            consec = 0
    if max_consec >= 3:
        score += max_consec * max_consec * 0.8

    # Anchor bonus in opponent's home
    for p in range(18, 24):
        if my_pts[p] >= 2:
            score += 2.0

    # If no contact, race mode - pure pip count dominates
    if not opp_has_contact or not any(my_pts[i] > 0 for i in range(24)):
        pass

    return score


def policy(state):
    try:
        dice = list(state.get('dice', []))
        dice = [d for d in dice if d > 0]
        moves = _enumerate(state, dice)
        if not moves:
            return 'H:P,P'
        best_score = -1e18
        best_move = moves[0][0]
        for mv, ns in moves:
            sc = _evaluate(ns)
            if sc > best_score:
                best_score = sc
                best_move = mv
        return best_move
    except Exception:
        return 'H:P,P'
