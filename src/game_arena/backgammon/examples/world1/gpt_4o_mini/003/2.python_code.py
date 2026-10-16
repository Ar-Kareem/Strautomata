
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    # Sort the dice for ease of reference
    sorted_dice = sorted(dice)
    high_die = sorted_dice[-1]
    low_die = sorted_dice[0]
    
    # Check if we have checkers on the bar
    if my_bar > 0:
        return f'H:B,P' if high_die <= 5 else f'L:B,P'
    
    # Generate possible moves
    moves = []
    
    # First, we look for potential bearing off if applicable
    if all(pt == 0 for pt in my_pts[:18]):  # If we're in the home quadrant
        # Check if we can bear off
        for pt in range(23, -1, -1):
            if my_pts[pt] > 0:
                if pt >= high_die and my_pts[pt - high_die] > 0:
                    moves.append(f'H:A{pt},P')  # Bear off with high die
                if pt >= low_die and my_pts[pt - low_die] > 0:
                    moves.append(f'L:A{pt},P')  # Bear off with low die
                break  # We only need to consider the first checker available for bearing off
    
    # Else, check for normal moves
    # Trying to explore both dice usage
    for pt in range(23, -1, -1):
        if my_pts[pt] > 0:
            # Move using high die
            target_high = pt - high_die
            if target_high >= 0 and opp_pts[target_high] < 2:
                moves.append(f'H:A{pt},P')
            # Move using low die
            target_low = pt - low_die
            if target_low >= 0 and opp_pts[target_low] < 2:
                moves.append(f'L:A{pt},P')

    # Determine action from available moves
    if moves:
        return moves[0]  # Return the first available move found
    
    # In the case no moves are available
    return 'H:P,P'  # Pass move
