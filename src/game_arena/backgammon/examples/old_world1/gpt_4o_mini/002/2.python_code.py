
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    dice = sorted(state['dice'], reverse=True)  # Sort dice from largest to smallest

    # Step 1: Re-enter from the Bar if there are any checkers on the bar
    if my_bar > 0:
        for die in dice:
            entry_point = 24 - die  # Points for re-entering
            if opp_pts[entry_point] < 2:  # Must not land on an opposing block
                if die == dice[0]:  # Use higher die first
                    return f'H:B,A{entry_point}'
                else:  # Use lower die second
                    return f'L:B,A{entry_point}'

    # Step 2: Check if we can bear off
    if my_off + sum(my_pts[18:24]) == 15:  # All in home area
        bear_off_moves = []
        for die in dice:
            bear_off_point = 24 - die
            if my_pts[bear_off_point] > 0:  # We can bear off from this point
                bear_off_moves.append(bear_off_point)

        if bear_off_moves:
            # Prefer the highest die for the first move
            return f'H:A{bear_off_moves[0]},P' if len(dice) == 1 else f'H:A{bear_off_moves[0]},A{bear_off_moves[1]}'

    # Step 3: Make the best moves from occupied points
    moves = []
    for die in dice:
        for pt in range(24):
            if my_pts[pt] > 0:  # There's a checker here to move
                target = pt - die  # Calculate where we can move
                if target >= 0 and opp_pts[target] < 2:  # Valid move
                    moves.append((pt, target))
                    if len(moves) == 2:  # Only offer two moves
                        break
        if len(moves) >= 2:
            break

    # Step 4: Generate move string accordingly
    if not moves:
        return 'H:P,P'  # No moves possible

    if len(moves) == 1:
        first_move = moves[0]
        return f'H:A{first_move[0]},P'  # Assuming H order since this is only one die
    
    # If we have two valid moves
    first_move, second_move = moves[0], moves[1]
    return f'H:A{first_move[0]},A{second_move[0]}'
