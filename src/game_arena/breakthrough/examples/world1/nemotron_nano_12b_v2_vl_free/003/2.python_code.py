
def policy(me, opp, color):
    # Convert to sets for fast lookups
    my_set = set(me)
    opp_set = set(opp)
    
    # Determine direction and promotion row
    dr = 1 if color == 'w' else -1
    promotion_row = 7 if color == 'w' else 0
    
    # Generate all possible moves
    possible_moves = []
    for (r, c) in me:
        # Straight forward move
        new_r = r + dr
        new_c = c
        if 0 <= new_r < 8 and 0 <= new_c < 8:
            target = (new_r, new_c)
            if target not in my_set and target not in opp_set:
                move = ( (r, c), (new_r, new_c) )
                possible_moves.append(move)
                # Immediate return if promotion
                if new_r == promotion_row:
                    return move
        
        # Left diagonal
        new_r = r + dr
        new_c = c - 1
        if 0 <= new_r < 8 and 0 <= new_c < 8:
            target = (new_r, new_c)
            if target not in my_set:
                move = ( (r, c), (new_r, new_c) )
                possible_moves.append(move)
                if new_r == promotion_row:
                    return move
        
        # Right diagonal
        new_c = c + 1
        if 0 <= new_r < 8 and 0 <= new_c < 8:
            target = (new_r, new_c)
            if target not in my_set:
                move = ( (r, c), (new_r, new_c) )
                possible_moves.append(move)
                if new_r == promotion_row:
                    return move
    
    # If no promotions, look for all moves
    promotion_moves = [move for move in possible_moves if move[1][0] == promotion_row]
    if promotion_moves:
        return promotion_moves[0]
    
    # Next: capture moves
    capture_moves = [move for move in possible_moves if move[1] in opp_set]
    if capture_moves:
        return captures[0]
    
    # No captures, return first valid move
    return possible_moves[0] if possible_moves else None
