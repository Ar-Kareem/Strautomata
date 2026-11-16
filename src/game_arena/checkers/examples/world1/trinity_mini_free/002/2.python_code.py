
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction based on color
    direction = -1 if color == 'b' else 1
    
    # Check for capturing moves
    for piece in my_men + my_kings:
        r, c = piece
        # Determine valid directions based on piece type
        directions = [(direction, 1), (direction, -1)] if piece in my_men else [(1,1), (1,-1), (-1,1), (-1,-1)]
        
        for dr, dc in directions:
            target_r = r + dr
            target_c = c + dc
            # Check if target is within bounds
            if not (0 <= target_r < 8 and 0 <= target_c < 8):
                continue
            # Check if target is opponent's piece
            if (target_r, target_c) in opp_men or (target_r, target_c) in opp_kings:
                # Check if landing square is empty
                landing_r = target_r + dr
                landing_c = target_c + dc
                if 0 <= landing_r < 8 and 0 <= landing_c < 8:
                    if (landing_r, landing_c) not in my_men and (landing_r, landing_c) not in my_kings:
                        return ((r, c), (landing_r, landing_c))
    
    # Check for non-capturing moves if no captures available
    for piece in my_men + my_kings:
        r, c = piece
        directions = [(direction, 1), (direction, -1)] if piece in my_men else [(1,1), (1,-1), (-1,1), (-1,-1)]
        
        for dr, dc in directions:
            target_r = r + dr
            target_c = c + dc
            if not (0 <= target_r < 8 and 0 <= target_c < 8):
                continue
            if (target_r, target_c) not in my_men and (target_r, target_c) not in my_kings:
                return ((r, c), (target_r, target_c))
    
    # Fallback: return a dummy move (should not occur in valid games)
    return ((0, 0), (0, 0))
