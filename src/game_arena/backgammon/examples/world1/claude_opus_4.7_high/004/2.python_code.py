
def policy(state):
    my_pts = list(state['my_pts'])
    opp_pts = list(state['opp_pts'])
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = list(state['dice'])

    init_state = (tuple(my_pts), tuple(opp_pts), my_bar, opp_bar, my_off)

    def apply_move(st, frm, die):
        mp, op, mb, ob, mo = st
        mp = list(mp); op = list(op)
        if frm == 'B':
            if mb <= 0: return None
            dest = 24 - die
            if dest < 0 or dest > 23: return None
            if op[dest] >= 2: return None
            mb -= 1
            if op[dest] == 1:
                op[dest] = 0
                ob += 1
            mp[dest] += 1
            return (tuple(mp), tuple(op), mb, ob, mo)
        if mb > 0: return None
        p = frm
        if p < 0 or p > 23 or mp[p] <= 0: return None
        dest = p - die
        if dest < 0:
            for i in range(6, 24):
                if mp[i] > 0: return None
            if die > p + 1:
                for i in range(p+1, 6):
                    if mp[i] > 0: return None
            mp[p] -= 1
            return (tuple(mp), tuple(op), mb, ob, mo + 1)
        else:
            if op[dest] >= 2: return None
            mp[p] -= 1
            if op[dest] == 1:
                op[dest] = 0
                ob += 1
            mp[dest] += 1
            return (tuple(mp), tuple(op), mb, ob, mo)

    def enum_sources(st):
        mp, op, mb, ob, mo = st
        if mb > 0:
            yield 'B', 'B'
            return
        for i in range(24):
            if mp[i] > 0:
                yield i, f'A{i}'

    def evaluate(st):
        mp, op, mb, ob, mo = st
        my_pip = mb * 25
        for i in range(24):
            my_pip += mp[i] * (i + 1)
        opp_pip = ob * 25
        for i in range(24):
            opp_pip += op[i] * (24 - i)

        score = float(opp_pip - my_pip)
        score -= mb * 20
        score += ob * 18
        score += mo * 4
        score -= (15 - mo) * 0  # bias toward bearing off

        for i in range(24):
            n = mp[i]
            if n == 1:
                shots = 0
                for j in range(max(0, i-6), i):
                    if op[j] > 0:
                        shots += 1
                if ob > 0 and i <= 5:
                    shots += 2
                penalty = 2.0 + shots * 1.8
                if i >= 18:
                    penalty *= 1.3
                score -= penalty
            elif n >= 2:
                bonus = 1.5
                if i <= 5:
                    bonus = 3.0
                    if i == 4: bonus = 5.5
                    elif i == 3: bonus = 4.0
                    elif i == 2: bonus = 3.2
                elif i == 6: bonus = 4.5
                elif i == 7: bonus = 3.2
                if n > 3:
                    bonus -= (n - 3) * 0.7
                score += bonus
            if op[i] == 1:
                score += 0.6

        consec = 0; best_prime = 0
        for i in range(24):
            if mp[i] >= 2:
                consec += 1
                if consec > best_prime: best_prime = consec
            else:
                consec = 0
        score += best_prime * 1.5
        if best_prime >= 5: score += 8
        if best_prime >= 6: score += 15

        return score

    if not dice:
        return 'H:P,P'

    all_moves = []

    if len(dice) == 1:
        d = dice[0]
        for frm, tok in enum_sources(init_state):
            ns = apply_move(init_state, frm, d)
            if ns is not None:
                all_moves.append((f'H:{tok},P', ns))
        if not all_moves:
            return 'H:P,P'
    else:
        d1, d2 = dice
        high = max(d1, d2)
        low = min(d1, d2)
        is_double = (d1 == d2)

        two_move = []
        high_only = []
        low_only = []

        orderings = [(high, 'H', low)]
        if not is_double:
            orderings.append((low, 'L', high))

        for first_die, order_char, second_die in orderings:
            for frm1, tok1 in enum_sources(init_state):
                s1 = apply_move(init_state, frm1, first_die)
                if s1 is None: continue
                found_second = False
                for frm2, tok2 in enum_sources(s1):
                    s2 = apply_move(s1, frm2, second_die)
                    if s2 is None: continue
                    found_second = True
                    two_move.append((f'{order_char}:{tok1},{tok2}', s2))
                if not found_second:
                    if first_die == high:
                        high_only.append((f'{order_char}:{tok1},P', s1))
                    else:
                        low_only.append((f'{order_char}:{tok1},P', s1))

        if two_move:
            all_moves = two_move
        elif high_only:
            all_moves = high_only
        elif low_only:
            all_moves = low_only
        else:
            return 'H:P,P'

    best_score = -1e18
    best_str = all_moves[0][0]
    for move_str, ns in all_moves:
        s = evaluate(ns)
        if s > best_score:
            best_score = s
            best_str = move_str

    return best_str
