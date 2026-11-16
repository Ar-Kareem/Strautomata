
def policy(state: dict) -> str:
    # Sort dice in descending order for higher die priority
    dice = sorted(state['dice'], reverse=True)
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    
    # Handle bar moves first
    if my_bar > 0:
        for die in dice:
            for point in range(24):
                if my_pts[point] > 0:
                    dest = point + die
                    if dest > 23:
                        continue
                    # Check if destination is legal (not occupied by 2+ opponent checkers)
                    if opp_pts[dest] < 2:
                        # Use higher die first for bar moves
                        return f"H:B,{point}"
        # If no bar moves found, pass
        return "H:P,P"
    
    # Check if all checkers are in home board (0-5)
    if all(my_pts[i] == 0 for i in range(6, 24)):
        # Bearing off
        for die in dice:
            for point in range(6):
                if my_pts[point] > 0:
                    if point + die >= 6:
                        # Use higher die first for bearing off
                        return f"H:{point},P"
        # If no bearing off moves, pass
        return "H:P,P"
    
    # Process moves from points
    for die in dice:
        for point in range(24):
            if my_pts[point] > 0:
                dest = point + die
                if dest > 23:
                    continue
                # Check if destination is legal (not occupied by 2+ opponent checkers)
                if opp_pts[dest] < 2:
                    # Prefer hitting opponent blots
                    if opp_pts[dest] == 1:
                        return f"H:{point},P"
                    # Prefer moving towards home board
                    elif dest < point:
                        return f"H:{point},P"
        # If no moves found for this die, try lower die
        for point in range(24):
            if my_pts[point] > 0:
                dest = point + die
                if dest > 23:
                    continue
                if opp_pts[dest] < 2:
                    return f"L:{point},P"
    
    # No legal moves found
    return "H:P,P"
