
import copy

def policy(state):
    # Handle bar case
    if state['my_bar'] > 0:
        return handle_bar_case(state)
    # Handle normal moves
    return handle_board_case(state)

def can_bear(state):
    # Check if all checkers are in home board and no bar
    if state['my_bar'] > 0:
        return False
    for i in range(18):
        if state['my_pts'][i] > 0:
            return False
    return True

def handle_bar_case(state):
    dice = sorted(state['dice'], reverse=True)
    if len(dice) == 0:
        return "H:P,P"
    
    higher_die = dice[0]
    h_point = higher_die - 1
    # Check if higher die can enter
    if state['opp_pts'][h_point] < 2:
        if len(dice) == 1:
            return f"H:B,P"
        else:
            lower_die = dice[1]
            l_point = lower_die - 1
            # Handle second die
            if state['my_bar'] > 1 and state['opp_pts'][l_point] < 2:
                return f"H:B,B"
            # After re-entering with higher die, try second move
            simulated_state = copy.deepcopy(state)
            simulated_state['my_bar'] -= 1
            simulated_state['my_pts'][h_point] += 1
            # If opp had single checker on h_point, it's hit
            if state['opp_pts'][h_point] == 1:
                simulated_state['opp_pts'][h_point] = 0
                simulated_state['opp_bar'] += 1
            # Now check if bar is clear for non-bar move
            if simulated_state['my_bar'] == 0:
                # Try moving the entered checker with lower die
                dest = h_point - lower_die
                if dest >= 0 and simulated_state['opp_pts'][dest] < 2:
                    return f"H:B,A{h_point}"
                # Try bearing off if possible
                if dest < 0 and can_bear(simulated_state):
                    return f"H:B,A{h_point}"
            # Default to passing second die
            return f"H:B,P"
    else:
        if len(dice) > 1:
            # Try lower die if higher fails
            lower_die = dice[1]
            l_point = lower_die - 1
            if state['opp_pts'][l_point] < 2:
                return f"L:B,P"
    
    # No legal entry, pass
    return "H:P,P"

def handle_board_case(state):
    # Try bearing off first
    if can_bear(state):
        dice = sorted(state['dice'], reverse=True)
        for die in dice:
            for s in range(23, 17, -1):
                if state['my_pts'][s] > 0:
                    if s - die < 18 or s - die < 0:  # Valid bear off
                        if len(dice) == 1:
                            return f"H:A{s},P"
                        else:
                            # Try second die on same checker if possible
                            die2 = min(dice)
                            if die2 <= s - 17 or s - die - die2 < 18:
                                return f"H:A{s},A{s}"
                            # Find another point for second die
                            for s2 in range(23, 17, -1):
                                if state['my_pts'][s2] > 0 and (s2 != s or state['my_pts'][s] > 1):
                                    return f"H:A{s},A{s2}"
                            return f"H:A{s},P"
        
    # Non bear-off moves
    dice = sorted(state['dice'], reverse=True)
    # Find safe moves prioritizing progression
    for s in range(24):  # Farthest checkers first
        if state['my_pts'][s] > 0:
            # Higher die first
            dest = s - dice[0]
            if dest >= 0 and state['opp_pts'][dest] < 2:
                if len(dice) == 1:
                    return f"H:A{s},P"
                else:
                    # Second die: try same checker if possible
                    dest2 = s - dice[0] - dice[1]
                    if dest2 >= 0 and state['opp_pts'][dest2] < 2:
                        return f"H:A{s},A{s}"
                    # Try different checker
                    for s2 in range(24):
                        if state['my_pts'][s2] > 0 and (s2 != s or state['my_pts'][s] > 1):
                            dest2 = s2 - dice[1]
                            if dest2 >= 0 and state['opp_pts'][dest2] < 2:
                                return f"H:A{s},A{s2}"
                    # Fallback to single move
                    return f"H:A{s},P"
    
    # No safe moves, pass
    return "H:P,P"
