
def policy(state: dict) -> str:
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    opp_bar = state['opp_bar']
    dice = state['dice']

    # If no dice rolled, pass
    if not dice:
        return "H:P,P"

    # Sort dice to handle order
    dice_sorted = sorted(dice, reverse=True)
    high_die = dice_sorted[0]
    low_die = dice_sorted[1] if len(dice_sorted) > 1 else 0

    # Helper function to check if a point is safe to move to
    def is_safe_move(from_pt, die_value):
        if from_pt == 'B':
            # Re-entering from bar: target is 24 - die_value (engine handles direction)
            target = 24 - die_value
            if target < 0 or target >= 24:
                return False
            return opp_pts[target] < 2
        else:
            # Moving from a point
            from_idx = int(from_pt[1:])
            if my_pts[from_idx] == 0:
                return False
            # Calculate target (engine handles direction)
            target = from_idx - die_value if from_idx >= 18 else from_idx + die_value
            if target < 0 or target >= 24:
                return False
            return opp_pts[target] < 2

    # Helper function to check if we can bear off
    def can_bear_off():
        # Check if all checkers are in home board (points 0-5 for me)
        return all(count == 0 for count in my_pts[6:])

    # Case 1: Checkers on bar - must re-enter first
    if my_bar > 0:
        # Try to re-enter with higher die first
        if is_safe_move('B', high_die):
            # Try to find a second move if we have two dice
            if len(dice) == 2:
                # Look for any safe move with the lower die
                for i in range(24):
                    if my_pts[i] > 0 and is_safe_move(f"A{i}", low_die):
                        return f"H:B,A{i}"
                # If no second move, just move from bar
                return f"H:B,P"
            else:
                return f"H:B,P"
        elif len(dice) == 2 and is_safe_move('B', low_die):
            return f"L:B,P"
        else:
            return "H:P,P"

    # Case 2: Bearing off if possible
    if can_bear_off():
        # Find the highest point with checkers
        for i in range(5, -1, -1):
            if my_pts[i] > 0:
                # Try to bear off with higher die
                if i + 1 <= high_die:
                    if len(dice) == 2:
                        # Look for second bear off
                        for j in range(5, -1, -1):
                            if j != i and my_pts[j] > 0 and j + 1 <= low_die:
                                return f"H:A{i},A{j}"
                        # If no second bear off, try to move within home board
                        for j in range(24):
                            if my_pts[j] > 0 and is_safe_move(f"A{j}", low_die):
                                return f"H:A{i},A{j}"
                        return f"H:A{i},P"
                    else:
                        return f"H:A{i},P"
                elif len(dice) == 2 and i + 1 <= low_die:
                    return f"L:A{i},P"

    # Case 3: Normal moves - look for hits first
    # Try to hit opponent's blots with higher die
    for i in range(24):
        if my_pts[i] > 0:
            # Calculate target (engine handles direction)
            target = i - high_die if i >= 18 else i + high_die
            if 0 <= target < 24 and opp_pts[target] == 1:
                # Found a hit opportunity
                if len(dice) == 2:
                    # Look for any safe second move
                    for j in range(24):
                        if j != i and my_pts[j] > 0 and is_safe_move(f"A{j}", low_die):
                            return f"H:A{i},A{j}"
                    return f"H:A{i},P"
                else:
                    return f"H:A{i},P"

    # Case 4: Safe moves - try to advance checkers
    # Try to move with higher die first
    for i in range(24):
        if my_pts[i] > 0 and is_safe_move(f"A{i}", high_die):
            if len(dice) == 2:
                # Look for any safe second move
                for j in range(24):
                    if j != i and my_pts[j] > 0 and is_safe_move(f"A{j}", low_die):
                        return f"H:A{i},A{j}"
                return f"H:A{i},P"
            else:
                return f"H:A{i},P"

    # Case 5: If only one die can be played, try lower die
    if len(dice) == 2:
        for i in range(24):
            if my_pts[i] > 0 and is_safe_move(f"A{i}", low_die):
                return f"L:A{i},P"

    # If no moves possible
    return "H:P,P"
