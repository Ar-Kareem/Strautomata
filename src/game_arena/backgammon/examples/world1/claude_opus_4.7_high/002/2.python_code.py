
HIT_PROB = {
    1: 11, 2: 12, 3: 14, 4: 15, 5: 15, 6: 17,
    7: 6, 8: 6, 9: 5, 10: 3, 11: 2, 12: 3,
    15: 1, 16: 1, 18: 1, 20: 1, 24: 1
}


def apply_die(my_pts, opp_pts, my_bar, my_off, d):
    results = []
    if my_bar > 0:
        entry = 24 - d
        if 0 <= entry < 24 and opp_pts[entry] < 2:
            new_my = list(my_pts)
            new_opp = list(opp_pts)
            ob = 0
            new_my[entry] += 1
            if new_opp[entry] == 1:
                new_opp[entry] = 0
                ob = 1
            results.append(('B', new_my, new_opp, my_bar - 1, my_off, ob))
        return results

    all_home = all(my_pts[i] == 0 for i in range(6, 24))

    for p in range(24):
        if my_pts[p] == 0:
            continue
        target = p - d
        if target >= 0:
            if opp_pts[target] < 2:
                new_my = list(my_pts)
                new_opp = list(opp_pts)
                ob = 0
                new_my[p] -= 1
                new_my[target] += 1
                if new_opp[target] == 1:
                    new_opp[target] = 0
                    ob = 1
                results.append(('A' + str(p), new_my, new_opp, my_bar, my_off, ob))
        else:
            if not all_home or p > 5:
                continue
            if p == d - 1:
                new_my = list(my_pts)
                new_my[p] -= 1
                results.append(('A' + str(p), new_my, list(opp_pts), my_bar, my_off + 1, 0))
            elif p < d - 1:
                is_highest = all(my_pts[i] == 0 for i in range(p + 1, 6))
                if is_highest:
                    new_my = list(my_pts)
                    new_my[p] -= 1
                    results.append(('A' + str(p), new_my, list(opp_pts), my_bar, my_off + 1, 0))
    return results


def enumerate_moves(my_pts, opp_pts, my_bar, my_off, opp_bar, dice, high):
    if len(dice) == 0:
        return []

    if len(dice) == 1:
        d = dice[0]
        results = apply_die(my_pts, opp_pts, my_bar, my_off, d)
        moves = []
        for (tok, mp, op, mb, mo, ob) in results:
            moves.append(('H:' + tok + ',P', (mp, op, mb, mo, opp_bar + ob)))
        return moves

    is_double = dice[0] == dice[1]
    orderings = [(dice[0], dice[1])] if is_double else [(dice[0], dice[1]), (dice[1], dice[0])]

    full_moves = {}
    partial_high = {}
    partial_low = {}

    for (da, db) in orderings:
        first = apply_die(my_pts, opp_pts, my_bar, my_off, da)
        for (tok1, mp1, op1, mb1, mo1, ob1) in first:
            second = apply_die(mp1, op1, mb1, mo1, db)
            order = 'H' if da == high else 'L'
            if not second:
                ms = order + ':' + tok1 + ',P'
                st = (mp1, op1, mb1, mo1, opp_bar + ob1)
                if da == high:
                    partial_high[ms] = st
                else:
                    partial_low[ms] = st
            else:
                for (tok2, mp2, op2, mb2, mo2, ob2) in second:
                    ms = order + ':' + tok1 + ',' + tok2
                    full_moves[ms] = (mp2, op2, mb2, mo2, opp_bar + ob1 + ob2)

    if full_moves:
        return list(full_moves.items())
    if partial_high:
        return list(partial_high.items())
    if partial_low:
        return list(partial_low.items())
    return []


def evaluate(st):
    my_pts, opp_pts, my_bar, my_off, opp_bar = st
    opp_off = 15 - sum(opp_pts) - opp_bar

    score = 0.0
    score += my_off * 10.0
    score -= opp_off * 10.0
    score -= my_bar * 8.0
    score += opp_bar * 6.0

    my_pip = sum((p + 1) * my_pts[p] for p in range(24)) + my_bar * 25
    opp_pip = sum((24 - p) * opp_pts[p] for p in range(24)) + opp_bar * 25
    score += (opp_pip - my_pip) * 0.15

    # Blot danger
    for p in range(24):
        if my_pts[p] == 1:
            danger = 0.0
            if opp_bar > 0:
                if 0 <= p <= 5:
                    danger = HIT_PROB.get(p + 1, 0) / 36.0
            else:
                total = 0.0
                for q in range(p):
                    if opp_pts[q] > 0:
                        dist = p - q
                        total += HIT_PROB.get(dist, 0) / 36.0
                danger = min(total, 1.0)
            weight = 5.0
            if p <= 5:
                weight = 6.0
            score -= danger * weight

    # Points made
    for p in range(24):
        c = my_pts[p]
        if c >= 2:
            if p <= 5:
                score += 2.5
            elif p == 7:
                score += 2.2  # bar point
            elif p <= 8:
                score += 1.8
            elif p <= 11:
                score += 1.0
            else:
                score += 0.3
        if c > 4:
            score -= (c - 4) * 0.5

    # Prime bonus
    consecutive = 0
    max_consec = 0
    for p in range(12):
        if my_pts[p] >= 2:
            consecutive += 1
            if consecutive > max_consec:
                max_consec = consecutive
        else:
            consecutive = 0
    score += max_consec * 0.7

    # Anchor in opp home
    for p in range(18, 24):
        if my_pts[p] >= 2:
            score += 1.2

    # Builder bonus - checkers in midfield to make points
    for p in range(6, 12):
        if my_pts[p] >= 1:
            score += 0.1

    return score


def policy(state):
    try:
        my_pts = list(state['my_pts'])
        opp_pts = list(state['opp_pts'])
        my_bar = int(state['my_bar'])
        opp_bar = int(state['opp_bar'])
        my_off = int(state['my_off'])
        dice = list(state['dice'])

        if not dice:
            return 'H:P,P'

        high = max(dice)

        moves = enumerate_moves(my_pts, opp_pts, my_bar, my_off, opp_bar, dice, high)

        if not moves:
            return 'H:P,P'

        best = moves[0][0]
        best_score = -1e18
        for ms, st in moves:
            s = evaluate(st)
            if s > best_score:
                best_score = s
                best = ms

        return best
    except Exception:
        return 'H:P,P'
