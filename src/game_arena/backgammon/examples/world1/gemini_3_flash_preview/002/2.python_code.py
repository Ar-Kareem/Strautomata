
import random

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if not dice:
        return "H:P,P"

    # Sort dice to identify High and Low
    d_list = sorted(dice, reverse=True)
    high_d = d_list[0]
    low_d = d_list[-1] if len(d_list) > 1 else None

    def get_legal_moves():
        legals = []
        orders = ['H', 'L'] if len(dice) == 2 and dice[0] != dice[1] else ['H']
        
        for order in orders:
            d1 = high_d if order == 'H' else low_d
            d2 = low_d if order == 'H' else high_d
            
            # Try first move
            m1_starts = get_valid_starts(state, d1)
            for s1 in m1_starts:
                temp_state = simulate_move(state, s1, d1)
                if d2 is not None:
                    m2_starts = get_valid_starts(temp_state, d2)
                    for s2 in m2_starts:
                        legals.append((order, s1, s2))
                else:
                    legals.append((order, s1, 'P'))
        
        if not legals:
            return [("H", "P", "P")]
        return legals

    def get_valid_starts(curr_state, die):
        starts = []
        m_pts = curr_state['my_pts']
        o_pts = curr_state['opp_pts']
        m_bar = curr_state['my_bar']
        
        if m_bar > 0:
            target = 24 - die
            if o_pts[target] < 2:
                return ['B']
            return []

        # Check if bearing off is allowed
        can_bear_off = m_bar == 0 and sum(m_pts[6:]) == 0
        
        for i in range(24):
            if m_pts[i] > 0:
                target = i - die
                if target >= 0:
                    if o_pts[target] < 2:
                        starts.append(f"A{i}")
                elif can_bear_off:
                    # Specific bearing off logic (simplification)
                    if target == -1 or (target < -1 and sum(m_pts[i+1:6]) == 0):
                        starts.append(f"A{i}")
        return starts

    def simulate_move(curr_state, start, die):
        new_state = {
            'my_pts': list(curr_state['my_pts']),
            'opp_pts': list(curr_state['opp_pts']),
            'my_bar': curr_state['my_bar'],
            'opp_bar': curr_state['opp_bar']
        }
        if start == 'P': return new_state
        if start == 'B':
            new_state['my_bar'] -= 1
            target = 24 - die
        else:
            idx = int(start[1:])
            new_state['my_pts'][idx] -= 1
            target = idx - die
        
        if target >= 0:
            if new_state['opp_pts'][target] == 1:
                new_state['opp_pts'][target] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][target] += 1
        return new_state

    def evaluate(order, s1, s2):
        score = 0
        # Basic heuristic
        fs1 = 24 if s1 == 'B' else (int(s1[1:]) if s1 != 'P' else 0)
        fs2 = 24 if s2 == 'B' else (int(s2[1:]) if s2 != 'P' else 0)
        
        # Reward movement
        score += (fs1 + fs2) * 0.1
        
        # Simulate and check board
        st1 = simulate_move(state, s1, high_d if order == 'H' else low_d)
        st2 = simulate_move(st1, s2, low_d if order == 'H' else high_d)
        
        # Reward hitting
        score += st2['opp_bar'] * 10
        
        # Reward making points (2+ checkers)
        for p in st2['my_pts']:
            if p >= 2: score += 1.5
            if p == 1: score -= 0.5 # Penalty for blots
            
        # Reward bearing off
        if s1 != 'P' and int(s1[1:]) - (high_d if order == 'H' else low_d) < 0: score += 5
        if s2 != 'P' and int(s2[1:]) - (low_d if order == 'H' else high_d) < 0: score += 5

        return score

    all_moves = get_legal_moves()
    best_move = all_moves[0]
    best_score = -9999
    
    for m in all_moves:
        s = evaluate(m[0], m[1], m[2])
        if s > best_score:
            best_score = s
            best_move = m
            
    return f"{best_move[0]}:{best_move[1]},{best_move[2]}"
