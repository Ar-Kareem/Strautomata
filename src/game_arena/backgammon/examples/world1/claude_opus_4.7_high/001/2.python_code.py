
def policy(state: dict) -> str:
    my = list(state['my_pts'])
    opp = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = list(state['dice'])

    def all_home(m, b):
        if b > 0: return False
        for i in range(6, 24):
            if m[i] > 0: return False
        return True

    def legal_froms(m, o, b, die):
        result = []
        if b > 0:
            target = 24 - die
            if 0 <= target <= 23 and o[target] < 2:
                result.append('B')
            return result
        ah = all_home(m, b)
        highest = -1
        if ah:
            for q in range(5, -1, -1):
                if m[q] > 0:
                    highest = q
                    break
        for p in range(24):
            if m[p] <= 0: continue
            t = p - die
            if t >= 0:
                if o[t] < 2:
                    result.append('A' + str(p))
            else:
                if ah:
                    if p == die - 1:
                        result.append('A' + str(p))
                    elif p < die - 1 and p == highest:
                        result.append('A' + str(p))
        return result

    def apply_move(m, o, b, ob, moff, frm, die):
        m = list(m); o = list(o)
        if frm == 'B':
            b -= 1
            t = 24 - die
            if o[t] == 1:
                o[t] = 0; ob += 1
            m[t] += 1
        else:
            p = int(frm[1:])
            m[p] -= 1
            t = p - die
            if t >= 0:
                if o[t] == 1:
                    o[t] = 0; ob += 1
                m[t] += 1
            else:
                moff += 1
        return (m, o, b, ob, moff)

    def evaluate(m, o, b, ob, moff):
        score = 0.0
        my_pip = b * 25
        for i in range(24):
            my_pip += m[i] * (i + 1)
        opp_pip = ob * 25
        for i in range(24):
            opp_pip += o[i] * (24 - i)
        score -= my_pip
        score += opp_pip
        score += moff * 8
        score -= opp_off * 8
        score += ob * 28
        score -= b * 32
        for i in range(24):
            if m[i] == 1:
                risk = 0
                for j in range(max(0, i - 6), i):
                    if o[j] > 0:
                        risk += 1
                if ob > 0 and 0 <= i <= 5:
                    risk += 2
                if i <= 5:
                    score -= risk * 7
                else:
                    score -= risk * 6
        for i in range(24):
            if m[i] >= 2:
                if i <= 5:
                    score += 7
                elif i <= 7:
                    score += 5
                elif i <= 12:
                    score += 3
                elif i <= 17:
                    score += 1
                else:
                    score += 3
        consec = 0
        bp = 0
        for i in range(13):
            if m[i] >= 2:
                consec += 1
                bp = max(bp, consec)
            else:
                consec = 0
        score += bp * bp
        for i in range(24):
            if m[i] > 4:
                score -= (m[i] - 4) * 2
        for i in range(24):
            if o[i] == 1:
                score += 1
        return score

    if not dice:
        return "H:P,P"

    results = []

    if len(dice) == 1:
        die = dice[0]
        froms = legal_froms(my, opp, my_bar, die)
        if not froms:
            return "H:P,P"
        for f in froms:
            ns = apply_move(my, opp, my_bar, opp_bar, my_off, f, die)
            results.append((ns, "H:" + f + ",P", 1))
    else:
        high = max(dice)
        low = min(dice)
        if high == low:
            orderings = [('H', high, low)]
        else:
            orderings = [('H', high, low), ('L', low, high)]

        two_move_found = False
        for oc, d1, d2 in orderings:
            froms1 = legal_froms(my, opp, my_bar, d1)
            for f1 in froms1:
                s1 = apply_move(my, opp, my_bar, opp_bar, my_off, f1, d1)
                m1, o1, b1, ob1, mo1 = s1
                froms2 = legal_froms(m1, o1, b1, d2)
                if froms2:
                    two_move_found = True
                    for f2 in froms2:
                        ns = apply_move(m1, o1, b1, ob1, mo1, f2, d2)
                        results.append((ns, oc + ":" + f1 + "," + f2, 2))

        if not two_move_found:
            froms_h = legal_froms(my, opp, my_bar, high)
            if froms_h:
                for f in froms_h:
                    ns = apply_move(my, opp, my_bar, opp_bar, my_off, f, high)
                    results.append((ns, "H:" + f + ",P", 1))
            else:
                froms_l = legal_froms(my, opp, my_bar, low)
                if froms_l:
                    for f in froms_l:
                        ns = apply_move(my, opp, my_bar, opp_bar, my_off, f, low)
                        results.append((ns, "L:" + f + ",P", 0))

    if not results:
        return "H:P,P"

    max_pri = max(r[2] for r in results)
    results = [r for r in results if r[2] == max_pri]

    best = None
    best_s = -1e18
    for ns, ms, pri in results:
        m, o, b, ob, mo = ns
        s = evaluate(m, o, b, ob, mo)
        if s > best_s:
            best_s = s
            best = ms

    return best if best else "H:P,P"
