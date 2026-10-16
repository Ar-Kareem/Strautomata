
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    # Extracting the dice rolls and ensuring they are sorted
    dice.sort(reverse=True)
    die1, die2 = dice[0], dice[1] if len(dice) > 1 else (dice[0], 0)

    if my_bar > 0:
        # We must move a checker from the bar
        potential_moves = []
        for i in range(24):
            if opp_pts[i] < 2:  # Can land only where there are less than 2 opponent checkers
                potential_moves.append(f'B,A{i}')
        
        if potential_moves:
            return f'H:{potential_moves[0]},{potential_moves[0]}'  # Move the same checker again

    # If no bar moves, check if we can bear off
    if sum(my_pts[0:6]) == sum(my_pts):  # All checkers in the home board
        # Attempt to bear off the highest positioned checker first
        highest_checker = None
        for i in range(5, -1, -1):
            if my_pts[i] > 0:
                highest_checker = i
                break

        if highest_checker is not None:
            if highest_checker >= die1:
                return f'H:P,P'
            elif highest_checker >= die2:
                return f'H:A{highest_checker},P'
            else:
                return f'H:P,A{highest_checker}'

    # Normal moves if no bearing off
    moves = []
    
    for start in range(24):
        if my_pts[start] > 0:  # There are checkers to move from this point
            # Check move with the higher die
            target_high = start + die1
            if target_high < 24 and opp_pts[target_high] < 2:
                moves.append(f'A{start},A{target_high}')
            
            # Check move with the lower die (if valid)
            if die2 > 0:  # Only check if moving is possible
                target_low = start + die2
                if target_low < 24 and opp_pts[target_low] < 2:
                    moves.append(f'A{start},A{target_low}')

    if moves:
        return f'H:{moves[0]},{moves[0]}'  # Prefer the first valid move

    return 'H:P,P'  # No moves possible
