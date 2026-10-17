
def policy(state: dict) -> str:
    # Handle bar moves first if checkers are on the bar
    if state['my_bar'] > 0:
        dice = state['dice']
        # Sort dice to check higher die first
        sorted_dice = sorted(dice, reverse=True)
        moves = []
        for die in sorted_dice:
            for point in range(24):
                if state['opp_pts'][point] < 2:  # Legal landing point
                    moves.append(f'B,{point}')
            if moves:
                break
        if moves:
            return f'H:{moves[0]}' if sorted_dice[0] == dice[0] else f'L:{moves[0]}'
        else:
            return 'H:P,P' if dice[0] == max(dice) else 'L:P,P'
    
    # Non-bar case: prioritize hits, bearing off, and point building
    dice = state['dice']
    if len(dice) == 2:
        # Check if both dice can be played
        both_possible = True
        for die in dice:
            found = False
            for point in range(24):
                if state['my_pts'][point] > 0:
                    dest = point - die
                    if dest < 0:  # Bearing off
                        if all(state['my_pts'][i] == 0 for i in range(6, 24)):
                            found = True
                    else:  # Standard move
                        if dest < 24 and state['opp_pts'][dest] < 2:
                            found = True
                    if found:
                        break
            if not found:
                both_possible = False
                break
        
        if both_possible:
            # Prioritize hits, then bearing off, then point building
            higher_die = max(dice)
            lower_die = min(dice)
            moves_higher = []
            moves_lower = []
            
            # Check for hits first
            for point in range(24):
                if state['my_pts'][point] > 0:
                    dest = point - higher_die
                    if dest < 0:  # Bearing off
                        if all(state['my_pts'][i] == 0 for i in range(6, 24)):
                            moves_higher.append(f'{point}')
                    else:  # Standard move
                        if dest < 24 and state['opp_pts'][dest] == 1:  # Hit
                            moves_higher.append(f'{point}')
            
            for point in range(24):
                if state['my_pts'][point] > 0:
                    dest = point - lower_die
                    if dest < 0:  # Bearing off
                        if all(state['my_pts'][i] == 0 for i in range(6, 24)):
                            moves_lower.append(f'{point}')
                    else:  # Standard move
                        if dest < 24 and state['opp_pts'][dest] == 1:  # Hit
                            moves_lower.append(f'{point}')
            
            # Use hits if available, else bearing off, else point building
            move_higher = next((f'{point}' for point in moves_higher), 'P')
            move_lower = next((f'{point}' for point in moves_lower), 'P')
            return f'H:{move_higher},{move_lower}'
        
        else:
            # Only one die can be played: use higher die
            die = max(dice)
            moves = []
            for point in range(24):
                if state['my_pts'][point] > 0:
                    dest = point - die
                    if dest < 0:  # Bearing off
                        if all(state['my_pts'][i] == 0 for i in range(6, 24)):
                            moves.append(f'{point}')
                    else:  # Standard move
                        if dest < 24 and state['opp_pts'][dest] < 2:
                            moves.append(f'{point}')
            return f'H:{moves[0]}' if moves else 'H:P,P'
    
    else:
        # Single die
        die = dice[0]
        moves = []
        for point in range(24):
            if state['my_pts'][point] > 0:
                dest = point - die
                if dest < 0:  # Bearing off
                    if all(state['my_pts'][i] == 0 for i in range(6, 24)):
                        moves.append(f'{point}')
                else:  # Standard move
                    if dest < 24 and state['opp_pts'][dest] < 2:
                        moves.append(f'{point}')
        return f'H:{moves[0]}' if moves else 'H:P,P'
