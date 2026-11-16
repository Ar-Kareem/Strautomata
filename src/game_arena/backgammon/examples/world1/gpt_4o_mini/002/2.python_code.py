
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    dice = state['dice']

    # Sort dice to determine higher and lower die
    high_die, low_die = sorted(dice, reverse=True)
    
    # If we have checkers on the bar, we must re-enter first.
    if my_bar > 0:
        # Check if we can move from the bar
        bar_moves = []
        for point in range(24):
            if point >= high_die and opp_pts[point] < 2:
                bar_moves.append(f'H:B,A{point}')  # High die first
            if point >= low_die and opp_pts[point] < 2:
                bar_moves.append(f'L:B,A{point}')  # Low die second
        if bar_moves:
            return bar_moves[0]  # Return the first legal bar move we find

    # We are in the normal game phase, no checkers on the bar
    moves = []
    
    for i in range(24):  # Iterate over all points
        if my_pts[i] > 0:  # If we have checkers here
            # Calculate target positions based on dice
            for d in (high_die, low_die):
                target = i - d
                if target >= 0 and opp_pts[target] < 2:  # Must not hit two or more opponent checkers
                    if d == high_die:
                        moves.append(f'H:A{i},A{target}')  # High die move
                    else:
                        moves.append(f'L:A{i},A{target}')  # Low die move
                        
            # If we have two checkers here, consider double moving
            if my_pts[i] > 1:
                for d1 in (high_die, low_die):
                    for d2 in (high_die, low_die):
                        if d1 != d2:  # Must use both dice differently
                            target1 = i - d1
                            target2 = i - d2
                            if target1 >= 0 and opp_pts[target1] < 2 and target2 >= 0 and opp_pts[target2] < 2:
                                moves.append(f'H:A{i},A{target1},A{target2}')  # Using high and low dies in any order
                                moves.append(f'L:A{i},A{target1},A{target2}')
    
    if moves:
        # Return the first legal move found
        return moves[0]
    
    # If no moves possible, we must pass
    return 'H:P,P'
