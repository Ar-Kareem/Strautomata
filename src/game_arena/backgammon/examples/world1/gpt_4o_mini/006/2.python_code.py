
def policy(state: dict) -> str:
    from itertools import product

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    dice = state['dice']
    
    # Sort dice to retrieve higher and lower values
    dice.sort(reverse=True)
    
    # Check for moves from the bar
    if my_bar > 0:
        moves = []
        for die in dice:
            # Attempt to move from bar to any valid point (0 to 23)
            for point in range(len(opp_pts)):
                if opp_pts[point] < 2:  # Can move if opponent has less than 2 checkers
                    moves.append(f'H:B,{point}' if die == dice[0] else f'L:B,{point}')
        if moves:
            return moves[0]  # Return the first available move (higher die first)
    
    # If no checkers are on the bar, consider moving from regular points
    moves = []
    for die in dice:
        for point in range(len(my_pts)):
            if my_pts[point] > 0:  # Check for points occupied by our checkers
                destination = point - die  # Calculate destination point
                if 0 <= destination < len(opp_pts) and opp_pts[destination] < 2:  # Valid move
                    moves.append(f'H:{point},{destination}' if die == dice[0] else f'L:{point},{destination}')
    
    if moves:
        return moves[0]  # Return the first move found

    return 'H:P,P'  # If there are no available moves, return a pass
