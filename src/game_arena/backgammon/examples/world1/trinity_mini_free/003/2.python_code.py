
def policy(state: dict) -> str:
    # Extract state variables
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # Sort dice in descending order
    dice_sorted = sorted(dice, reverse=True)
    
    # Check for bar moves
    if my_bar > 0:
        for die in dice_sorted:
            for point in range(24):
                if my_pts[point] > 0:
                    continue
                # Check if moving from bar to point is legal
                if point < 6:  # Home board
                    if opp_pts[point] < 2:
                        return f"H:{point},{point}" if die == max(dice) else f"L:{point},{point}"
                else:
                    if opp_pts[point] < 2:
                        return f"H:{point},{point}" if die == max(dice) else f"L:{point},{point}"
    
    # Check for bearing off (only if all checkers in home board)
    if all(my_pts[i] == 0 for i in range(6)):
        for die in dice_sorted:
            for point in range(6):
                if my_pts[point] > 0 and point + die >= 24:
                    return f"H:{point},{point}" if die == max(dice) else f"L:{point},{point}"
    
    # Move towards home board
    for die in dice_sorted:
        for point in range(23, -1, -1):
            if my_pts[point] > 0:
                dest = point - die
                if dest < 0:
                    dest = 0
                if dest < 6:  # Home board
                    if opp_pts[dest] < 2:
                        return f"H:{point},{point}" if die == max(dice) else f"L:{point},{point}"
                else:
                    if opp_pts[dest] < 2:
                        return f"H:{point},{point}" if die == max(dice) else f"L:{point},{point}"
    
    # Block opponent's points
    for die in dice_sorted:
        for point in range(23, -1, -1):
            if my_pts[point] > 0:
                dest = point - die
                if dest < 0:
                    dest = 0
                if dest < 6:  # Home board
                    if opp_pts[dest] == 1:
                        return f"H:{point},{point}" if die == max(dice) else f"L:{point},{point}"
                else:
                    if opp_pts[dest] == 1:
                        return f"H:{point},{point}" if die == max(dice) else f"L:{point},{point}"
    
    return "H:P,P"
