
ROLLS = [(a, b, 1 if a == b else 2) for a in range(1, 7) for b in range(a, 7)]

# value of a made point by absolute index (I move 23 -> 0, home = 0..5)
PV = [2.0, 3.0, 4.0, 6.0, 8.0, 5.0,
      6.0, 4.0, 3.0, 2.0, 2.0, 1.5,
      2.0, 1.0, 1.0, 1.0, 1.0, 3.0,
      4.0, 5.0, 4.0, 2.5, 1.5, 1.0]


def tok(s):
    return 'B' if s == 'B' else "A%d" % s


def legal_single(my, opp, my_bar, d):
    moves = []
    if my_bar > 0:
        dest = 24 - d
        if opp[dest] < 2:
            moves.append('B')
        return moves
    all_home = True
    for i in range(6, 24):
        if my[i]:
            all_home = False
            break
    for p in range(24):
        if my[p] == 0:
            continue
        dest = p - d
        if dest >= 0:
            if opp[dest] < 2:
                moves.append(p)
        else:
            if all_home:
                if dest == -1:
                    moves.append(p)
                else:
                    ok = True
                    for q in range(p + 1, 6):
                        if my[q]:
                            ok = False
                            break
                    if ok:
                        moves.append(p)
    return moves


def apply_move(my, opp, my_bar, my_off, opp_bar, src, d):
    my = my[:]
    opp = opp[:]
    if src == 'B':
        my_bar -= 1
        dest = 24 - d
    else:
        my[src] -= 1
        dest = src - d
    if dest < 0:
        my_off += 1
    else:
        if opp[dest] == 1:
            opp[dest] = 0
            opp_bar += 1
        my[dest] += 1
    return my, opp, my_bar, my_off, opp_bar


def can_hit(p, a, b, att, att_bar, blocked):
    def src(q):
        return q >= 0 and att[q] > 0
    if att_bar == 0:
        if src(p - a) or src(p - b):
            return True
        if a != b:
            q = p - a - b
            if src(q) and ((not blocked[q + a]) or (not blocked[q + b])):
                return True
        else:
            q = p - 2 * a
            if src(q) and not blocked[q + a]:
                return True
            q = p - 3 * a
            if src(q) and not blocked[q + a] and not blocked[q + 2 * a]:
                return True
            q = p - 4 * a
            if src(q) and not blocked[q + a] and not blocked[q + 2 * a] and not blocked[q + 3 * a]:
                return True
        return False
    elif att_bar == 1:
        if p == a - 1 or p == b - 1:
            return True
        if a != b:
            if not blocked[a - 1]:
                if src(p - b) or p == a - 1 + b:
                    return True
            if not blocked[b - 1]:
                if src(p - a) or p == b - 1 + a:
                    return True
        else:
            if not blocked[a - 1]:
                for k in (1, 2, 3):
                    q = p - k * a
                    if q < -1:
                        break
                    ok = (q >= 0 and att[q] > 0) or (q == a - 1)
                    if ok:
                        clear = True
                        for j in range(1, k):
                            if blocked[q + j * a]:
                                clear = False
                                break
                        if clear:
                            return True
        return False
    else:
        if p == a - 1 or p == b - 1:
            return True
        if a == b and att_bar == 2 and not blocked[a - 1]:
            for k in (1, 2):
                q = p - k * a
                if q < -1:
                    break
                ok = (q >= 0 and att[q] > 0) or (q == a - 1)
                if ok:
                    clear = True
                    for j in range(1, k):
                        if blocked[q + j * a]:
                            clear = False
                            break
                    if clear:
                        return True
        return False


def hit_risk(defn, att, att_bar, tempo):
    # attacker moves upward (index increasing) and enters from bar at die-1
    blots = []
    if att_bar == 0:
        amin = 24
        for i in range(24):
            if att[i]:
                amin = i
                break
        if amin == 24:
            return 0.0
        for p in range(amin + 1, 24):
            if defn[p] == 1:
                blots.append(p)
    else:
        for p in range(24):
            if defn[p] == 1:
                blots.append(p)
    if not blots:
        return 0.0
    blocked = [c >= 2 for c in defn]
    total = 0.0
    for a, b, w in ROLLS:
        best = 0.0
        extra = 0.0
        for p in blots:
            if can_hit(p, a, b, att, att_bar, blocked):
                c = (24 - p) + tempo
                if c > best:
                    extra += best
                    best = c
                else:
                    extra += c
        if best:
            total += w * (best + 0.4 * extra)
    return total / 36.0


def evaluate(my, opp, my_bar, my_off, opp_bar, opp_off):
    my_pips = my_bar * 25
    opp_pips = opp_bar * 25
    my_max = 24 if my_bar > 0 else -1
    opp_min = -1 if opp_bar > 0 else 24
    for i in range(24):
        c = my[i]
        if c:
            my_pips += c * (i + 1)
            if i > my_max:
                my_max = i
        c = opp[i]
        if c:
            opp_pips += c * (24 - i)
            if i < opp_min:
                opp_min = i
    score = float(opp_pips - my_pips)
    contact = my_max > opp_min
    if not contact:
        score += 2.5 * (my_off - opp_off)
        outside = 0
        for i in range(6, 24):
            outside += my[i]
        score -= 1.0 * outside
        for i in range(6):
            if my[i] > 3:
                score -= 0.5 * (my[i] - 3)
        return score

    my_home_pts = 0
    for i in range(6):
        if my[i] >= 2:
            my_home_pts += 1
    opp_home_pts = 0
    for i in range(18, 24):
        if opp[i] >= 2:
            opp_home_pts += 1
    made = [c >= 2 for c in my]
    omade = [c >= 2 for c in opp]

    score += 2.0 * (my_off - opp_off)

    n_opp_back = opp_bar
    for j in range(0, 9):
        n_opp_back += opp[j]
    mult = 0.4 + 0.3 * min(n_opp_back, 4)
    if mult > 1.3:
        mult = 1.3

    for i in range(24):
        if my[i] >= 2:
            v = PV[i]
            if i <= 8:
                v *= mult
            score += v

    if opp_bar:
        score += opp_bar * (4.0 + 2.0 * my_home_pts)
        if my_home_pts == 6:
            score += 12.0 * opp_bar
    if my_bar:
        score -= my_bar * (3.0 + 2.0 * opp_home_pts)

    # blocking opponent checkers
    for j in range(24):
        if opp[j] and j < my_max:
            b = 0
            for k in range(j + 1, min(j + 7, 24)):
                if made[k]:
                    b += 1
            if b:
                bonus = 0.5 * b
                if b >= 4:
                    bonus += 1.5
                if b >= 5:
                    bonus += 2.0
                score += opp[j] * bonus
    # my checkers trapped
    for i in range(24):
        if my[i] and i > opp_min:
            b = 0
            for k in range(max(i - 6, 0), i):
                if omade[k]:
                    b += 1
            if b:
                pen = 0.5 * b
                if b >= 4:
                    pen += 1.5
                if b >= 5:
                    pen += 2.0
                score -= my[i] * pen

    back = my_bar
    for i in range(18, 24):
        back += my[i]
    if back > 2:
        score -= 1.5 * (back - 2)
    if back == 1 and my_bar == 0:
        score -= 1.0

    for i in range(24):
        c = my[i]
        if c > 4:
            score -= 0.7 * (c - 4)
    for i in (0, 1):
        if my[i] > 2:
            score -= 1.5 * (my[i] - 2)
    if my[2] > 3:
        score -= 0.5 * (my[2] - 3)

    run = 0
    best_run = 0
    for i in range(0, 13):
        if made[i]:
            run += 1
            if run > best_run:
                best_run = run
        else:
            run = 0
    if best_run >= 3 and n_opp_back > 0:
        score += 1.5 * (best_run - 2) ** 2

    tempo = 5.0 + 2.5 * opp_home_pts
    if opp_home_pts >= 5:
        tempo += 6.0
    score -= hit_risk(my, opp, opp_bar, tempo)

    tempo2 = 5.0 + 2.5 * my_home_pts
    threat = hit_risk(opp[::-1], my[::-1], my_bar, tempo2)
    score += 0.3 * threat
    return score


def gen_candidates(my, opp, my_bar, my_off, opp_bar, dice):
    hi, lo = max(dice), min(dice)
    if hi == lo:
        orders = [('H', hi, lo)]
    else:
        orders = [('H', hi, lo), ('L', lo, hi)]
    full = []
    partial = []
    for o, d1, d2 in orders:
        for s1 in legal_single(my, opp, my_bar, d1):
            st1 = apply_move(my, opp, my_bar, my_off, opp_bar, s1, d1)
            m1, o1, b1, off1, ob1 = st1
            seconds = legal_single(m1, o1, b1, d2)
            if seconds:
                for s2 in seconds:
                    st2 = apply_move(m1, o1, b1, off1, ob1, s2, d2)
                    full.append(("%s:%s,%s" % (o, tok(s1), tok(s2)), st2))
            else:
                partial.append((o, "%s:%s,P" % (o, tok(s1)), st1))
    if full:
        return full
    if partial:
        hp = [(s, st) for o, s, st in partial if o == 'H']
        if hp:
            return hp
        return [(s, st) for o, s, st in partial]
    return []


def _policy(state):
    my = list(state['my_pts'])
    opp = list(state['opp_pts'])
    my_bar = int(state['my_bar'])
    opp_bar = int(state['opp_bar'])
    my_off = int(state['my_off'])
    opp_off = int(state['opp_off'])
    dice = list(state['dice'])
    if len(dice) == 0:
        return "H:P,P"
    if len(dice) == 1:
        d = dice[0]
        moves = legal_single(my, opp, my_bar, d)
        if not moves:
            return "H:P,P"
        cands = []
        for s in moves:
            st = apply_move(my, opp, my_bar, my_off, opp_bar, s, d)
            cands.append(("H:%s,P" % tok(s), st))
    else:
        cands = gen_candidates(my, opp, my_bar, my_off, opp_bar, dice)
        if not cands:
            return "H:P,P"
    best_move = cands[0][0]
    try:
        best_score = None
        cache = {}
        for mv, st in cands:
            m, o, b, off, ob = st
            key = (tuple(m), tuple(o), b, off, ob)
            if key in cache:
                sc = cache[key]
            else:
                sc = evaluate(m, o, b, off, ob, opp_off)
                cache[key] = sc
            if best_score is None or sc > best_score:
                best_score = sc
                best_move = mv
    except Exception:
        pass
    return best_move


def policy(state):
    try:
        return _policy(state)
    except Exception:
        try:
            my = list(state['my_pts'])
            opp = list(state['opp_pts'])
            dice = list(state['dice'])
            if len(dice) >= 2:
                c = gen_candidates(my, opp, int(state['my_bar']), int(state['my_off']),
                                   int(state['opp_bar']), dice)
                if c:
                    return c[0][0]
            elif len(dice) == 1:
                mv = legal_single(my, opp, int(state['my_bar']), dice[0])
                if mv:
                    return "H:%s,P" % tok(mv[0])
        except Exception:
            pass
        return "H:P,P"
