
import copy

def copy_state(state):
    return {
        'my_pts': state['my_pts'][:],
        'opp_pts': state['opp_pts'][:],
        'my_bar': state['my_bar'],
        'opp_bar': state['opp_bar'],
        'my_off': state['my_off'],
        'opp_off': state['opp_off'],
    }

def simulate_our_move(state, from_point, die):
    s = copy_state(state)
    if from_point == 'B':
        if s['my_bar'] == 0:
            return None
        entry = 24 - die
        if entry < 0 or entry > 23:
            return None
        if s['opp_pts'][entry] >= 2:
            return None
        s['my_bar'] -= 1
        if s['opp_pts'][entry] == 1:
            s['opp_pts'][entry] = 0
            s['opp_bar'] += 1
        s['my_pts'][entry] += 1
        return s
    else:
        p = from_point
        if p < 0 or p > 23:
            return None
        if s['my_pts'][p] == 0:
            return None
        all_in_home = all(s['my_pts'][i] == 0 for i in range(6, 24)) and s['my_bar'] == 0
        if all_in_home:
            dest = p - die
            if dest == 0:
                s['my_pts'][p] -= 1
                s['my_off'] += 1
                return s
            elif dest < 0:
                if any(s['my_pts'][i] > 0 for i in range(p+1, 24)):
                    return None
                s['my_pts'][p] -= 1
                s['my_off'] += 1
                return s
            else:
                if s['opp_pts'][dest] >= 2:
                    return None
                s['my_pts'][p] -= 1
                s['my_pts'][dest] += 1
                if s['opp_pts'][dest] == 1:
                    s['opp_pts'][dest] = 0
                    s['opp_bar'] += 1
                return s
        else:
            dest = p - die
            if dest < 0:
                return None
            if s['opp_pts'][dest] >= 2:
                return None
            s['my_pts'][p] -= 1
            s['my_pts'][dest] += 1
            if s['opp_pts'][dest] == 1:
                s['opp_pts'][dest] = 0
                s['opp_bar'] += 1
            return s

def simulate_opp_move(state, from_point, die):
    s = copy_state(state)
    if from_point == 'B':
        if s['opp_bar'] == 0:
            return None
        entry = die - 1
        if entry < 0 or entry > 23:
            return None
        if s['my_pts'][entry] >= 2:
            return None
        s['opp_bar'] -= 1
        if s['my_pts'][entry] == 1:
            s['my_pts'][entry] = 0
            s['my_bar'] += 1
        s['opp_pts'][entry] += 1
        return s
    else:
        p = from_point
        if p < 0 or p > 23:
            return None
        if s['opp_pts'][p] == 0:
            return None
        all_in_home = all(s['opp_pts'][i] == 0 for i in range(0, 18)) and s['opp_bar'] == 0
        if all_in_home:
            dest = p + die
            if dest == 23:
                s['opp_pts'][p] -= 1
                s['opp_off'] += 1
                return s
            elif dest > 23:
                if any(s['opp_pts'][i] > 0 for i in range(0, p)):
                    return None
                s['opp_pts'][p] -= 1
                s['opp_off'] += 1
                return s
            else:
                if s['my_pts'][dest] >= 2:
                    return None
                s['opp_pts'][p] -= 1
                s['opp_pts'][dest] += 1
                if s['my_pts'][dest] == 1:
                    s['my_pts'][dest] = 0
                    s['my_bar'] += 1
                return s
        else:
            dest = p + die
            if dest > 23:
                return None
            if s['my_pts'][dest] >= 2:
                return None
            s['opp_pts'][p] -= 1
            s['opp_pts'][dest] += 1
            if s['my_pts'][dest] == 1:
                s['my_pts'][dest] = 0
                s['my_bar'] += 1
            return s

def generate_sequences_for_order(state, die1, die2, player):
    sequences = []
    if player == 'my':
        bar = state['my_bar']
        pts = state['my_pts']
        opp_pts = state['opp_pts']
        simulate_move = simulate_our_move
    else:
        bar = state['opp_bar']
        pts = state['opp_pts']
        opp_pts = state['my_pts']
        simulate_move = simulate_opp_move

    move1_options = []
    if bar > 0:
        if player == 'my':
            entry = 24 - die1
        else:
            entry = die1 - 1
        if 0 <= entry <= 23 and opp_pts[entry] < 2:
            move1_options.append('B')
        else:
            move1_options.append('P')
    else:
        for p in range(24):
            if pts[p] > 0:
                s = simulate_move(state, p, die1)
                if s is not None:
                    move1_options.append(p)
        move1_options.append('P')

    for move1 in move1_options:
        if move1 == 'P':
            state1 = copy_state(state)
        else:
            state1 = simulate_move(state, move1, die1)
            if state1 is None:
                continue
        if player == 'my':
            bar1 = state1['my_bar']
            pts1 = state1['my_pts']
            opp_pts1 = state1['opp_pts']
        else:
            bar1 = state1['opp_bar']
            pts1 = state1['opp_pts']
            opp_pts1 = state1['my_pts']

        move2_options = []
        if bar1 > 0:
            if player == 'my':
                entry = 24 - die2
            else:
                entry = die2 - 1
            if 0 <= entry <= 23 and opp_pts1[entry] < 2:
                move2_options.append('B')
            else:
                move2_options.append('P')
        else:
            for p in range(24):
                if pts1[p] > 0:
                    s = simulate_move(state1, p, die2)
                    if s is not None:
                        move2_options.append(p)
            move2_options.append('P')

        for move2 in move2_options:
            if move2 == 'P':
                state2 = copy_state(state1)
            else:
                state2 = simulate_move(state1, move2, die2)
                if state2 is None:
                    continue
            sequences.append((move1, move2, state2, die1, die2))
    return sequences

def get_legal_moves(state, dice, player):
    d1, d2 = dice
    all_sequences = []
    orders = [(d1, d2)] if d1 == d2 else [(d1, d2), (d2, d1)]
    for die1, die2 in orders:
        seqs = generate_sequences_for_order(state, die1, die2, player)
        order_char = 'H' if die1 >= die2 else 'L'
        for move1, move2, final_state, die1_u, die2_u in seqs:
            all_sequences.append((order_char, move1, move2, final_state, die1_u, die2_u))
    if not all_sequences:
        return []
    def count_moves(seq):
        _, m1, m2, _, _, _ = seq
        return (0 if m1 == 'P' else 1) + (0 if m2 == 'P' else 1)
    max_moves = max(count_moves(s) for s in all_sequences)
    filtered = [s for s in all_sequences if count_moves(s) == max_moves]
    if max_moves == 1:
        higher_die = max(dice)
        has_higher = any(
            (m1 != 'P' and die1 == higher_die) or (m2 != 'P' and die2 == higher_die)
            for _, m1, m2, _, die1, die2 in filtered
        )
        if has_higher:
            filtered = [s for s in filtered if (
                (s[1] != 'P' and s[4] == higher_die) or (s[2] != 'P' and s[5] == higher_die)
            )]
        else:
            lower_die = min(dice)
            filtered = [s for s in filtered if (
                (s[1] != 'P' and s[4] == lower_die) or (s[2] != 'P' and s[5] == lower_die)
            )]
    return filtered

def evaluate(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    
    if my_off == 15:
        return 100000
    if opp_off == 15:
        return -100000
    
    my_pips = my_bar * 25 + sum(my_pts[i] * (i + 1) for i in range(24))
    opp_pips = opp_bar * 25 + sum(opp_pts[i] * (24 - i) for i in range(24))
    
    my_blots = sum(1 for i in range(24) if my_pts[i] == 1)
    opp_blots = sum(1 for i in range(24) if opp_pts[i] == 1)
    
    my_owned = sum(1 for i in range(24) if my_pts[i] >= 2)
    opp_owned = sum(1 for i in range(24) if opp_pts[i] >= 2)
    
    my_home_owned = sum(1 for i in range(0, 6) if my_pts[i] >= 2)
    opp_home_owned = sum(1 for i in range(18, 24) if opp_pts[i] >= 2)
    
    my_stacked = sum(max(0, my_pts[i] - 3) for i in range(24))
    opp_stacked = sum(max(0, opp_pts[i] - 3) for i in range(24))
    
    value = 0.0
    value += (opp_pips - my_pips) * 0.1
    value += (my_off - opp_off) * 1.0
    value += (opp_blots - my_blots) * 0.3
    value += (my_owned - opp_owned) * 0.2
    value += (my_home_owned - opp_home_owned) * 0.5
    value += (opp_bar - my_bar) * 0.5
    value += (opp_stacked - my_stacked) * 0.05
    return value

def format_move(order_char, move1, move2):
    def fmt(m):
        if m == 'P': return 'P'
        if m == 'B': return 'B'
        return f'A{m}'
    return f"{order_char}:{fmt(move1)},{fmt(move2)}"

ALL_ROLLS = []
for i in range(1, 7):
    for j in range(i, 7):
        if i == j:
            prob = 1.0/36.0
        else:
            prob = 2.0/36.0
        ALL_ROLLS.append(([i, j], prob))

def policy(state):
    dice = state['dice']
    if len(dice) != 2:
        return 'H:P,P'
    
    legal_moves = get_legal_moves(state, dice, 'my')
    if not legal_moves:
        return 'H:P,P'
    
    if len(legal_moves) == 1:
        m = legal_moves[0]
        return format_move(m[0], m[1], m[2])
    
    best_move = None
    best_value = -float('inf')
    
    for order_char, move1, move2, next_state, die1, die2 in legal_moves:
        total_value = 0.0
        for opp_dice, prob in ALL_ROLLS:
            opp_moves = get_legal_moves(next_state, opp_dice, 'opp')
            if not opp_moves:
                opp_best = evaluate(next_state)
            else:
                opp_best = min(evaluate(m[3]) for m in opp_moves)
            total_value += prob * opp_best
        if total_value > best_value:
            best_value = total_value
            best_move = (order_char, move1, move2)
    
    return format_move(best_move[0], best_move[1], best_move[2])
