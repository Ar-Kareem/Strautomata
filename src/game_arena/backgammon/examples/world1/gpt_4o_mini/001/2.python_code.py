
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    dice = state['dice']  # Could be one or two die

    # Sort dice to ensure we can differentiate between higher and lower easily
    dice.sort(reverse=True)
    
    legal_moves = []

    # Check if we need to move from the bar
    if my_bar > 0:
        for die in dice:
            move_from_bar = 'B'
            target_point = 24 - die  # From Bar to a target point
            if target_point < 24 and opp_pts[target_point] < 2:
                legal_moves.append(('B', target_point))
        # If we can only move from the bar, return the highest die move
        if legal_moves:
            return f'H:{legal_moves[0][0]},{legal_moves[0][1]}'  # Use the higher die
    
    # Bearing off case
    if my_off + sum(my_pts) == 15:  # all checkers in home board
        for die in dice:
            if die <= 5:  # Bearing off checks
                move_from = 24 - die
                if my_pts[move_from] > 0:
                    legal_moves.append((move_from,))
        if legal_moves:
            higher_move = legal_moves[0][0]
            return f'H:A{higher_move},P'  # Highest die bearing off
    
    # Regular moves
    for die in dice:
        for from_index in range(24):
            if my_pts[from_index] > 0:  # if we have checkers at this point
                target_index = from_index - die
                if target_index >= 0 and opp_pts[target_index] < 2:
                    legal_moves.append((from_index, target_index))

    # If we have valid moves
    if legal_moves:
        if len(legal_moves) >= 2:
            chosen_move = legal_moves[0]  # Select the first valid non-blocked move.
            return f'H:A{chosen_move[0]},A{chosen_move[1]}'
        elif len(legal_moves) == 1:
            chosen_move = legal_moves[0]
            return f'H:A{chosen_move[0]},P'

    return 'H:P,P'  # No legal moves, full pass
