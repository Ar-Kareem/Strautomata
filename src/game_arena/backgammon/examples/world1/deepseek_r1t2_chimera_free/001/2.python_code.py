
import copy

def can_bear_off(state):
    """Check if all checkers are in the home board (points 0-5) and no checkers on bar."""
    if state['my_bar'] > 0:
        return False
    for i in range(6, 24):
        if state['my_pts'][i] > 0:
            return False
    return True

def apply_single_move(state, source, die):
    """Apply a single move from source using the die roll, returning a new state."""
    new_state = copy.deepcopy(state)
    if source == 'B':
        p = 24 - die
        if new_state['my_bar'] == 0:
            return new_state  # Invalid move
        new_state['my_bar'] -= 1
        if new_state['opp_pts'][p] == 1:
            new_state['opp_pts'][p] = 0
            new_state['opp_bar'] += 1
        new_state['my_pts'][p] += 1
    elif source.startswith('A'):
        i = int(source[1:])
        if new_state['my_pts'][i] == 0:
            return new_state  # Invalid move
        new_state['my_pts'][i] -= 1
        j = i - die
        if j < 0:
            new_state['my_off'] += 1
        else:
            if new_state['opp_pts'][j] == 1:
                new_state['opp_pts'][j] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][j] += 1
    # No action for 'P'
    return new_state

def policy(state):
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    if len(dice) == 0:
        return "H:P,P"  # No moves possible
    
    dice_sorted = sorted(dice, reverse=True)
    higher = dice_sorted[0]
    lower = dice_sorted[1] if len(dice) > 1 else higher
    
    best_order = 'H'
    best_from1 = 'P'
    best_from2 = 'P'
    best_total_score = -99999
    
    for order in ['H', 'L'] if len(dice) > 1 else ['H']:
        if order == 'H':
            die1, die2 = higher, lower
        else:
            die1, die2 = lower, higher
        
        # Evaluate die1 moves
        temp_state1 = copy.deepcopy(state)
        moves1 = []
        score1 = -1000
        from1 = 'P'
        
        if my_bar > 0:
            p = 24 - die1
            if 0 <= p < 24 and temp_state1['opp_pts'][p] <= 1:
                hit_bonus = 1.5 if temp_state1['opp_pts'][p] == 1 else 0
                blot_penalty = 1 if (temp_state1['my_pts'][p] == 0 and p >= 6) else 0
                score = hit_bonus - blot_penalty + die1 * 0.1
                moves1.append(('B', score))
        else:
            for i in range(24):
                if temp_state1['my_pts'][i] == 0:
                    continue
                j = i - die1
                if j < 0:
                    if can_bear_off(temp_state1):
                        blot_change = -1 if (temp_state1['my_pts'][i] == 1 and i >= 6) else 0
                        score = 3 + blot_change
                        moves1.append((f"A{i}", score))
                else:
                    if opp_pts[j] > 1:
                        continue
                    hit_bonus = 1.5 if opp_pts[j] == 1 else 0
                    blot_change = 0
                    if temp_state1['my_pts'][i] == 1 and i >= 6:
                        blot_change -= 1  # Remove blot
                    if temp_state1['my_pts'][j] == 0 and j >= 6:
                        blot_change += 1  # Create blot
                    score = hit_bonus - blot_change + die1 * 0.1
                    moves1.append((f"A{i}", score))
        
        if not moves1:
            moves1.append(('P', -1000))
        from1, score1 = max(moves1, key=lambda x: x[1])
        
        # Apply die1 move
        temp_state2 = apply_single_move(temp_state1, from1, die1)
        
        # Evaluate die2 moves
        if len(dice) == 1:
            from2, score2 = 'P', 0
        else:
            move2 = []
            score2 = -1000
            if temp_state2['my_bar'] > 0:
                p = 24 - die2
                if 0 <= p < 24 and temp_state2['opp_pts'][p] <= 1:
                    hit_bonus = 1.5 if temp_state2['opp_pts'][p] == 1 else 0
                    blot_penalty = 1 if (temp_state2['my_pts'][p] == 0 and p >= 6) else 0
                    score = hit_bonus - blot_penalty + die2 * 0.1
                    move2.append(('B', score))
            else:
                for i in range(24):
                    if temp_state2['my_pts'][i] == 0:
                        continue
                    j = i - die2
                    if j < 0:
                        if can_bear_off(temp_state2):
                            blot_change = -1 if (temp_state2['my_pts'][i] == 1 and i >= 6) else 0
                            score = 2 + blot_change
                            move2.append((f"A{i}", score))
                    else:
                        if temp_state2['opp_pts'][j] > 1:
                            continue
                        hit_bonus = 1.5 if temp_state2['opp_pts'][j] == 1 else 0
                        blot_change = 0
                        if temp_state2['my_pts'][i] == 1 and i >= 6:
                            blot_change -= 1
                        if temp_state2['my_pts'][j] == 0 and j >= 6:
                            blot_change += 1
                        score = hit_bonus - blot_change + die2 * 0.1
                        move2.append((f"A{i}", score))
            
            if not move2:
                move2.append(('P', -1000))
            from2, score2 = max(move2, key=lambda x: x[1])
        
        total_score = score1 + score2
        if total_score > best_total_score:
            best_total_score = total_score
            best_order = order
            best_from1 = from1
            best_from2 = from2
    
    return f"{best_order}:{best_from1},{best_from2}"
