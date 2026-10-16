
def policy(state: dict) -> str:
    my_pts = [int(x) for x in state['my_pts']]
    opp_pts = [int(x) for x in state['opp_pts']]
    my_bar = int(state['my_bar'])
    opp_bar = int(state['opp_bar'])
    my_off = int(state['my_off'])
    opp_off = int(state['opp_off'])
    dice = [int(d) for d in state['dice']]

    BAR = -1

    def all_home(M):
        for i in range(6, 24):
            if M[i]:
                return False
        return True

    def legal_sources(M, O, mb, d):
        # Returns list of sources (BAR=-1 or point index) legal for die d.
        if mb > 0:
            dest = 24 - d
            if 0 <= dest <= 23 and O[dest] < 2:
                return [BAR]
            return []
        res = []
        home = all_home(M)
        highest = -1
        if home:
            for i in range(5, -1, -1):
                if M[i]:
                    highest = i
                    break
        for i in range(24):
            if M[i] == 0:
                continue
            dest = i - d
            if dest >= 0:
                if O[dest] < 2:
                    res.append(i)
            else:
                if home:
                    if d == i + 1:
                        res.append(i)
                    elif d > i + 1 and i == highest:
                        res.append(i)
        return res

    def apply_move(M, O, mb, ob, mo, d, src):
        M2 = M[:]
        O2 = O[:]
        mb2, ob2, mo2 = mb, ob, mo
        if src == BAR:
            mb2 -= 1
            dest = 24 - d
            if O2[dest] == 1:
                O2[dest] = 0
                ob2 += 1
            M2[dest] += 1
            return M2, O2, mb2, ob2, mo2
        M2[src] -= 1
        dest = src - d
        if dest >= 0:
            if O2[dest] == 1:
                O2[dest] = 0
                ob2 += 1
            M2[dest] += 1
        else:
            mo2 += 1
        return M2, O2, mb2, ob2, mo2

    def evaluate(M, O, mb, ob, mo, oo):
        my_pip = 25 * mb
        opp_pip = 25 * ob
        for i in range(24):
            v = M[i]
            if v:
                my_pip += (i + 1) * v
            w = O[i]
            if w:
                opp_pip += (24 - i) * w

        score = 0.0
        score += (opp_pip - my_pip) * 1.0
        score += (mo - oo) * 40.0
        score += (ob - mb) * 20.0

        my_made = opp_made = 0
        my_home_made = opp_home_made = 0
        my_anchor = 0
        for i in range(24):
            if M[i] >= 2:
                my_made += 1
                if i <= 5:
                    my_home_made += 1
                if i >= 18:
                    my_anchor += 1
            if O[i] >= 2:
                opp_made += 1
                if i >= 18:
                    opp_home_made += 1
        score += (my_made - opp_made) * 3.0
        score += (my_home_made - opp_home_made) * 10.0
        score += my_anchor * 6.0
        # Key points: our 5-point (idx4), 4-point (idx3), bar point (idx6).
        if M[4] >= 2:
            score += 4.0
        if M[3] >= 2:
            score += 2.0
        if M[6] >= 2:
            score += 3.0

        # Prime (longest run of made points).
        run = best = 0
        for i in range(24):
            if M[i] >= 2:
                run += 1
                if run > best:
                    best = run
            else:
                run = 0
        if best >= 2:
            score += (best - 1) * 6.0
        run = besto = 0
        for i in range(24):
            if O[i] >= 2:
                run += 1
                if run > besto:
                    besto = run
            else:
                run = 0
        if besto >= 2:
            score -= (besto - 1) * 6.0

        # Blots and direct-shot exposure.
        my_blots = opp_blots = my_exp = opp_exp = 0
        for p in range(24):
            if M[p] == 1:
                my_blots += 1
                exp = False
                q0 = p - 6
                if q0 < 0:
                    q0 = 0
                for q in range(q0, p):
                    if O[q] > 0:
                        exp = True
                        break
                if not exp and ob > 0 and p <= 5:
                    exp = True
                if exp:
                    my_exp += 1
            if O[p] == 1:
                opp_blots += 1
                exp = False
                q1 = p + 6
                if q1 > 23:
                    q1 = 23
                for q in range(p + 1, q1 + 1):
                    if M[q] > 0:
                        exp = True
                        break
                if not exp and mb > 0 and p >= 18:
                    exp = True
                if exp:
                    opp_exp += 1
        score -= my_blots * 4.0
        score += opp_blots * 3.0
        score -= my_exp * 9.0
        score += opp_exp * 6.0
        return score

    def tok(src):
        return 'B' if src == BAR else 'A' + str(src)

    if len(dice) == 0:
        return "H:P,P"

    if len(dice) == 1:
        d = dice[0]
        srcs = legal_sources(my_pts, opp_pts, my_bar, d)
        if not srcs:
            return "H:P,P"
        best_s = None
        best_sc = -1e18
        for s in srcs:
            M2, O2, mb2, ob2, mo2 = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, d, s)
            sc = evaluate(M2, O2, mb2, ob2, mo2, opp_off)
            if sc > best_sc:
                best_sc = sc
                best_s = s
        return "H:" + tok(best_s) + ",P"

    hi = max(dice)
    lo = min(dice)
    if hi == lo:
        orders = ((hi, lo, 'H'),)
    else:
        orders = ((hi, lo, 'H'), (lo, hi, 'L'))

    best_two = None  # (score, order, sA, sB)
    for dA, dB, ordch in orders:
        srcsA = legal_sources(my_pts, opp_pts, my_bar, dA)
        for sA in srcsA:
            M1, O1, mb1, ob1, mo1 = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, dA, sA)
            srcsB = legal_sources(M1, O1, mb1, dB)
            for sB in srcsB:
                M2, O2, mb2, ob2, mo2 = apply_move(M1, O1, mb1, ob1, mo1, dB, sB)
                sc = evaluate(M2, O2, mb2, ob2, mo2, opp_off)
                if best_two is None or sc > best_two[0]:
                    best_two = (sc, ordch, sA, sB)

    if best_two is not None:
        _, ordch, sA, sB = best_two
        return ordch + ":" + tok(sA) + "," + tok(sB)

    # Cannot play both dice: must play the higher die if it has any move.
    hi_srcs = legal_sources(my_pts, opp_pts, my_bar, hi)
    if hi_srcs:
        best_s = None
        best_sc = -1e18
        for s in hi_srcs:
            M2, O2, mb2, ob2, mo2 = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, hi, s)
            sc = evaluate(M2, O2, mb2, ob2, mo2, opp_off)
            if sc > best_sc:
                best_sc = sc
                best_s = s
        return "H:" + tok(best_s) + ",P"
    if hi != lo:
        lo_srcs = legal_sources(my_pts, opp_pts, my_bar, lo)
        if lo_srcs:
            best_s = None
            best_sc = -1e18
            for s in lo_srcs:
                M2, O2, mb2, ob2, mo2 = apply_move(my_pts, opp_pts, my_bar, opp_bar, my_off, lo, s)
                sc = evaluate(M2, O2, mb2, ob2, mo2, opp_off)
                if sc > best_sc:
                    best_sc = sc
                    best_s = s
            return "L:" + tok(best_s) + ",P"
    return "H:P,P"
