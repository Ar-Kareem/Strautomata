
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    # Sort dice for higher and lower die
    dice.sort(reverse=True)

    # Function to check if a point is blocked (occupied by 2 or more opponent checkers)
    def is_blocked(point):
        return opp_pts[point] >= 2

    # If we have checkers on the bar, we must move them first
    if my_bar > 0:
        for die in dice:
            target_index = 24 - die  # Entry point from bar is treated as position 24
            if target_index >= 0 and not is_blocked(target_index):
                # Move from bar to the valid target point
                return f'H:B,P' if die == dice[0] else f'L:B,P'
        
    # If no checkers on the bar, proceed with regular moves
    moves = []
    
    # Attempting to move checkers according to the dice rolls
    for die in dice:
        for start in range(23, -1, -1):  # Check from the furthest point back to 0
            if my_pts[start] > 0:  # If we have checkers at this point
                target = start - die
                if target >= 0 and not is_blocked(target):
                    moves.append(start)

    # Prepare to return the move
    if len(moves) >= 2:
        return f'H:{moves[0]},{moves[1]}'
    elif len(moves) == 1:
        return f'H:{moves[0]},P'  # if only one valid move
    else:
        return 'H:P,P'  # If no moves are available
