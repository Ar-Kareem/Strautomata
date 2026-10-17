
def policy(state: dict) -> str:
    """Generate the optimal move for Backgammon given the state."""
    my_pts = state['my_pts']
    opp_pts = state['opp_pts']
    my_bar = state['my_bar']
    my_off = state['my_off']
    dice = state['dice']
    
    # Prioritize rerolling the highest die first
    sorted_dice = sorted(dice, reverse=True)
    
    # Handle re-entry from bar if any checkers are there
    if my_bar > 0:
        # Use higher die first for re-entry
        dice_sorted = [sorted_dice[0], sorted_dice[1]] if len(sorted_dice) == 2 else []
        first_die = dice_sorted[0]
        second_die = dice_sorted[1] if len(dice_sorted) > 1 else 0
        
        # Assume re-entry is possible and move as far as possible
        return f"H:B,A{23 - first_die}"
    
    # Check for possible hits
    possible_hits = []
    for step, d in enumerate(sorted_dice, 1):
        for from_pos in range(24):
            if my_pts[from_pos] >= 1:
                to_pos = (from_pos + d) if step == 1 else (from_pos + d)
                if to_pos < 24 and opp_pts[to_pos] == 1:
                    possible_hits.append((to_pos, from_pos, d))
    
    if possible_hits:
        # Select the move that hits the farthest or any valid hit
        possible_hits.sort(key=lambda x: x[0], reverse=True)
        hit_move = possible_hits[0]
        total_moves = []
        total_moves.append(('H', f"A{hit_move[1]}"))
        if len(dice) == 2:
            remaining_die = dice[0] if dice[0] != hit_move[2] else dice[1]
            # Try to move the same checker again if possible
            total_moves.append(('L', f"A{hit_move[1] + hit_move[0]}"))
            return ",".join(f"{order}:{from_str}" for order, from_str in total_moves)
        return ':'.join(f"{order}:{from_str}" for order, from_str in total_moves)
    
    # Fallback: move forward as much as possible
    return f"H:A0,A{1 if len(dice) == 1 else 2}"
