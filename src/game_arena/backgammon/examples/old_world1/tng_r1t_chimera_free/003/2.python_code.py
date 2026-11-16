
def policy(state: dict) -> str:
    import numpy as np

    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    dice = state['dice']

    # Handle bar checkers first
    if state['my_bar'] > 0:
        possible_dice = []
        sorted_dice = sorted(dice, reverse=True)
        for die in sorted_dice:
            target_point = 24 - die  # Opponent's home board (18-23)
            if 18 <= target_point <= 23 and opp_pts[target_point] < 2:
                possible_dice.append(die)
        
        if not possible_dice:
            return "H:P,P" if len(dice) == 2 else "H:P"
        
        used = []
        for die in sorted_dice:
            if die in possible_dice and len(used) < len(dice):
                used.append(die)
        
        if len(used) == 1:
            order = 'H' if used[0] == max(dice) else 'L'
            return f"{order}:B,P"
        else:
            order = 'H' if used[0] >= used[-1] else 'L'
            return f"{order}:B,B"
    
    # No bar checkers - find regular moves
    # Prefer moving highest points first
    candidate_moves = []
    
    # Try both die orders (H and L)
    die_orders = []
    if len(dice) == 2:
        die_orders.append((max(dice), min(dice)))
        die_orders.append((min(dice), max(dice)))
    else:
        die_orders.append((dice[0], None))
    
    best_eval = -np.inf
    best_move = "H:P,P"
    for d1, d2 in die_orders:
        from1, from2 = None, None
        # Find highest point for d1
        for p in range(23, -1, -1):
            if my_pts[p] > 0:
                from1 = p
                break
        # Find next highest for d2
        if d2 is not None:
            for p in range(23, -1, -1):
                if my_pts[p] > 0 and p != from1:
                    from2 = p
                    break

        if from1 is None:
            continue  # No move possible

        eval = from1 + (from2 if from2 is not None else 0)
        if eval > best_eval:
            order = 'H' if d1 == max(dice) else 'L'
            move_str = f"{order}:A{from1}" + (f",A{from2}" if from2 is not None else ",P")
            best_move = move_str
            best_eval = eval

    return best_move if best_eval != -np.inf else "H:P,P"
