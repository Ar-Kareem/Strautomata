
def policy(state):
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    dice = list(state['dice'])

    def try_move(s, src, die):
        my_p, opp_p, mb, mo, ob = s
        if mb > 0 and src != -1:
            return None
        if src == -1:
            if mb == 0: return None
            dest = 24 - die
            if dest < 0 or dest > 23: return None
            if opp_p[dest] >= 2: return None
            nmy = my_p[:]; nopp = opp_p[:]
            nmy[dest] += 1
            nob = ob
            if nopp[dest] == 1:
                nopp[dest] = 0; nob += 1
            return (nmy, nopp, mb - 1, mo, nob)
        if src < 0 or src > 23 or my_p[src] == 0: return None
        dest = src - die
        if dest < 0:
            if mb > 0: return None
            for i in range(6, 24):
                if my_p[i] > 0: return None
            if dest < -1:
                for i in range(src + 1, 6):
                    if my_p[i] > 0: return None
            nmy = my_p[:]; nmy[src] -= 1
            return (nmy, opp_p[:], mb, mo + 1, ob)
        if opp_p[dest] >= 2: return None
        nmy = my_p[:]; nopp = opp_p[:]
        nmy[src] -= 1; nmy[dest] += 1
        nob = ob
        if nopp[dest] == 1:
            nopp[dest] = 0; nob += 1
        return (nmy, nopp, mb, mo, nob)

    HIT = [0, 11, 12, 14, 15, 15, 17, 6, 6, 5, 3, 2, 3]

    def evaluate(s):
        my_p, opp_p, mb, mo, ob = s
        my_pip = 25 * mb
        for i in range(24):
            if my_p[i]: my_pip += (i + 1) * my_p[i]
        opp_pip = 25 * ob
        for i in range(24):
            if opp_p[i]: opp_pip += (24 - i) * opp_p[i]
        score = (opp_pip - my_pip)
        score += mo * 8
        score -= mb * 45
        score += ob * 22
        for i in range(24):
            v = my_p[i]
            if v >= 2:
                score += 3
                if i <= 5: score += 2
                if i in (3, 4, 6, 7): score += 2
                if i >= 18: score += 2
                if v >= 4: score -= (v - 3) * 1.5
        for i in range(24):
            if my_p[i] == 1:
                max_hit = 0
                for j in range(max(0, i - 12), i):
                    if opp_p[j] > 0:
                        p = HIT[i - j]
                        if p > max_hit: max_hit = p
                if ob > 0 and 0 <= i <= 5:
                    if 11 > max_hit: max_hit = 11
                cost = (i + 1) + 15
                score -= max_hit / 36.0 * cost * 0.6
        return score

    if not dice:
        return 'H:P,P'

    init = (my_pts, opp_pts, my_bar, my_off, opp_bar)

    if len(dice) == 1:
        orderings = [[dice[0]]]
    elif dice[0] == dice[1]:
        orderings = [[dice[0], dice[1]]]
    else:
        orderings = [[dice[0], dice[1]], [dice[1], dice[0]]]

    sequences = []
    for order in orderings:
        stack = [(init, 0, [])]
        while stack:
            s, idx, moves = stack.pop()
            if idx == len(order):
                sequences.append((order, moves, s)); continue
            d = order[idx]
            my_p, _, mb, _, _ = s
            any_move = False
            if mb > 0:
                ns = try_move(s, -1, d)
                if ns is not None:
                    any_move = True
                    stack.append((ns, idx + 1, moves + [-1]))
            else:
                for src in range(24):
                    if my_p[src] > 0:
                        ns = try_move(s, src, d)
                        if ns is not None:
                            any_move = True
                            stack.append((ns, idx + 1, moves + [src]))
            if not any_move:
                stack.append((s, idx + 1, moves + [None]))

    def pc(m): return sum(1 for x in m if x is not None)
    max_played = max(pc(sq[1]) for sq in sequences)
    sequences = [sq for sq in sequences if pc(sq[1]) == max_played]

    if max_played == 1 and len(dice) == 2 and dice[0] != dice[1]:
        higher = max(dice)
        filt = []
        for order, moves, s in sequences:
            for i, m in enumerate(moves):
                if m is not None:
                    if order[i] == higher:
                        filt.append((order, moves, s))
                    break
        if filt: sequences = filt

    if max_played > 0:
        np_first = [sq for sq in sequences if sq[1][0] is not None]
        if np_first: sequences = np_first

    best = None; best_sc = -1e18
    for sq in sequences:
        sc = evaluate(sq[2])
        if sc > best_sc:
            best_sc = sc; best = sq

    if best is None:
        return 'H:P,P'

    order, moves, _ = best

    def enc(m):
        if m is None: return 'P'
        if m == -1: return 'B'
        return 'A' + str(m)

    if len(dice) == 1:
        o = 'H'; f1 = enc(moves[0]); f2 = 'P'
    else:
        if dice[0] == dice[1]:
            o = 'H'
        else:
            higher = max(dice)
            o = 'H' if order[0] == higher else 'L'
        f1 = enc(moves[0])
        f2 = enc(moves[1]) if len(moves) > 1 else 'P'

    return o + ':' + f1 + ',' + f2
