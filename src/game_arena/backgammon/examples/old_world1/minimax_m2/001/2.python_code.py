
import random

def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    my_off = state['my_off']
    opp_off = state['opp_off']
    dice = state['dice']
    
    # If no dice, pass
    if not dice:
        return "H:P,P"
    
    # Determine movement direction based on checker positions
    has_0_5 = any(my_pts[i] > 0 for i in range(6))
    has_18_23 = any(my_pts[i] > 0 for i in range(18, 24))
    
    if has_0_5 and not has_18_23:
        # Player 2: moving towards decreasing indices
        direction = -1
    elif has_18_23 and not has_0_5:
        # Player 1: moving towards increasing indices
        direction = 1
    else:
        # Ambiguous or both sides: assume increasing
        direction = 1
    
    # If checkers on bar, must move from bar
    if my_bar > 0:
        # Use higher die first if possible
        sorted_dice = sorted(dice, reverse=True)
        if len(dice) == 2:
            return "H:B,B"
        else:
            return "H:B,P"
    
    # Generate list of from-points based on direction
    from_points = []
    if direction == 1:
        # Increasing: prioritize high points
        for i in range(23, -1, -1):
            if my_pts[i] > 0:
                from_points.append(i)
    else:
        # Decreasing: prioritize low points
        for i in range(0, 24):
            if my_pts[i] > 0:
                from_points.append(i)
    
    # If no from-points, pass
    if not from_points:
        return "H:P,P"
    
    # Use higher die first
    sorted_dice = sorted(dice, reverse=True)
    from1 = f"A{from_points[0]}"
    
    if len(dice) == 2:
        if len(from_points) > 1:
            from2 = f"A{from_points[1]}"
        else:
            from2 = "P"
        return f"H:{from1},{from2}"
    else:
        return f"H:{from1},P"
