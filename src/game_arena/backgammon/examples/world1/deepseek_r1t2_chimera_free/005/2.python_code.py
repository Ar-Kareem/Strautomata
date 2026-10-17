
import copy

def policy(state):
    dice = state['dice']
    if not dice:
        return "H:P,P"

    # Function to check bearing off eligibility
    def can_bear_off(state):
        return all(state['my_pts'][i] == 0 for i in range(18))

    # Get possible from points for given die
    def possible_from(die, state, bar_check=False):
        points = []
        # Bar moves
        if bar_check and state['my_bar'] > 0:
            target = 23 - die
            if 0 <= target < 24 and state['opp_pts'][target] < 2:
                points.append('B')
        # Regular moves
        for i in range(24):
            if state['my_pts'][i] == 0:
                continue
            dest = i - die
            if dest >= 0:
                if state['opp_pts'][dest] < 2:
                    points.append(i)
            else:  # Bearing off
                if can_bear_off(state):
                    if die == i + 1 or (die > i + 1 and all(state['my_pts'][j] == 0 for j in range(i + 1, 24))):
                        points.append(i)
        return points

    # Simulate move's effect on state
    def apply_move(s, from_point, die):
        new_state = copy.deepcopy(s)
        if from_point == 'B':
            target = 23 - die
            new_state['my_bar'] -= 1
            if new_state['opp_pts'][target] == 1:
                new_state['opp_pts'][target] = 0
                new_state['opp_bar'] += 1
            new_state['my_pts'][target] += 1
        else:
            dest = from_point - die
            new_state['my_pts'][from_point] -= 1
            if dest >= 0:
                if new_state['opp_pts'][dest] == 1:
                    new_state['opp_pts'][dest] = 0
                    new_state['opp_bar'] += 1
                new_state['my_pts'][dest] += 1
            else:
                new_state['my_off'] += 1
        return new_state

    # Evaluate state quality
    def evaluate(s):
        score = 0
        # Base scoring components
        score += s['my_off'] * 1000  # Maximize borne off
        score -= s['my_bar'] * 300  # Penalize bar checkers
        score += s['opp_bar'] * 200  # Reward opponent on bar
        
        # Point control evaluation
        for i in range(24):
            if s['my_pts'][i] == 1:
                score -= 75  # Penalize blots
            elif s['my_pts'][i] >= 2:
                score += 40  # Reward made points
            if i >= 18:  # Home board bonuses
                if s['my_pts'][i] >= 2:
                    score += 25
                elif s['my_pts'][i] == 1:
                    score -= 25
        
        # Progress calculation
        for i in range(24):
            score += (24 - i) * s['my_pts'][i]  # Favor closer to bear off
        
        return score

    # Bar checker handling
    if state['my_bar'] > 0:
        dice_sorted = sorted(dice, reverse=True)
        for die in dice_sorted:
            targets = possible_from(die, state, bar_check=True)
            if 'B' in targets:
                used_dice = [die]
                remaining_dice = [d for d in dice if d != die]
                # Handle multi-move scenario
                if not remaining_dice:
                    return "H:B,P" if die == max(dice) else f"{['L','H'][die==min(dice)]}:B,P"
                
                # Find best second move
                second_die = remaining_dice[0]
                best_second = None
                best_score = -float('inf')
                
                # Simulate bar move
                interim_state = apply_move(state, 'B', die)
                
                # Check bar move second if possible
                if state['my_bar'] > 1:
                    bar_options = possible_from(second_die, interim_state, bar_check=True)
                    if 'B' in bar_options:
                        return "H:B,B" if die > second_die else "L:B,B"
                
                # Regular second move
                options = possible_from(second_die, interim_state)
                for opt in options:
                    final_state = apply_move(interim_state, opt, second_die)
                    sc = evaluate(final_state)
                    if sc > best_score:
                        best_score = sc
                        best_second = opt
                
                if best_second is not None:
                    order = 'H' if die == max(dice) else 'L'
                    return f"{order}:B,A{best_second}"
                else:
                    return "H:B,P" if die == max(dice) else "L:B,P"
        return "H:P,P"

    # No bar checkers - find optimal move sequence
    best_score = -float('inf')
    best_action = "H:P,P"
    orders = ['H'] if len(dice) == 1 else ['H','L']
    
    for order in orders:
        if order == 'H' and len(dice) > 1:
            die1, die2 = max(dice), min(dice)
        elif order == 'L':
            die1, die2 = min(dice), max(dice)
        else:
            die1, die2 = dice[0], None

        # First move options
        first_options = possible_from(die1, state)
        for f1 in first_options:
            temp_state = apply_move(state, f1, die1)
            current_action = [f1]
            
            if die2 is None:
                sc = evaluate(temp_state)
                action_str = f"{order}:A{f1},P"
                if sc > best_score:
                    best_score = sc
                    best_action = action_str
                continue
            
            # Second move options
            second_options = possible_from(die2, temp_state)
            for f2 in second_options:
                final_state = apply_move(temp_state, f2, die2)
                sc = evaluate(final_state)
                action_str = f"{order}:A{f1},A{f2}"
                if sc > best_score:
                    best_score = sc
                    best_action = action_str

            # Single move fallback if two aren't possible
            sc = evaluate(temp_state)
            action_str = f"{order}:A{f1},P"
            if sc > best_score and not second_options:
                best_score = sc
                best_action = action_str

    return best_action
