
def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Create sets for fast lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    occupied = my_men_set | my_kings_set | opp_men_set | opp_kings_set
    
    capture_moves = []
    
    # Helper to check if square is dark
    def is_dark(r, c):
        return (r + c) % 2 == 1
    
    # Generate capture moves for men
    man_dirs = [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
    for (r, c) in my_men:
        for dr, dc in man_dirs:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2*dr, c + 2*dc
            if (0 <= r2 < 8 and 0 <= c2 < 8 and 
                is_dark(r1, c1) and is_dark(r2, c2) and
                (r1, c1) in opp_men_set and (r2, c2) not in occupied):
                capture_moves.append(((r, c), (r2, c2)))
    
    # Generate capture moves for kings
    king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    for (r, c) in my_kings:
        for dr, dc in king_dirs:
            r1, c1 = r + dr, c + dc
            r2, c2 = r + 2*dr, c + 2*dc
            if (0 <= r2 < 8 and 0 <= c2 < 8 and 
                is_dark(r1, c1) and is_dark(r2, c2) and
                (r1, c1) in opp_men_set and (r2, c2) not in occupied):
                capture_moves.append(((r, c), (r2, c2)))
    
    # If captures exist, choose the best capture
    if capture_moves:
        best_move = None
        best_score = -1
        for (from_sq, to_sq) in capture_moves:
            from_r, from_c = from_sq
            to_r, to_c = to_sq
            
            # Calculate score for this capture
            score = 0
            mid_r, mid_c = (from_r + to_r) // 2, (from_c + to_c) // 2
            
            # Priority for capturing opponent kings
            if (mid_r, mid_c) in opp_kings_set:
                score += 200  # Higher value for kings
            else:
                score += 100   # Value for men
            
            # Promotion bonus for men that reach last row
            if (from_r, from_c) in my_men_set:
                if color == 'b' and to_r == 0:
                    score += 150  # Promotion is very valuable
                elif color == 'w' and to_r == 7:
                    score += 150
            
            # Prefer capturing when multiple options available
            if score > best_score:
                best_score = score
                best_move = (from_sq, to_sq)
        
        return best_move
    
    # No captures: generate non-capturing moves
    non_capture_moves = []
    
    # Non-capturing moves for men
    for (r, c) in my_men:
        for dr, dc in man_dirs:
            new_r, new_c = r + dr, c + dc
            if (0 <= new_r < 8 and 0 <= new_c < 8 and 
                is_dark(new_r, new_c) and (new_r, new_c) not in occupied):
                non_capture_moves.append(((r, c), (new_r, new_c)))
    
    # Non-capturing moves for kings
    for (r, c) in my_kings:
        for dr, dc in king_dirs:
            new_r, new_c = r + dr, c + dc
            if (0 <= new_r < 8 and 0 <= new_c < 8 and 
                is_dark(new_r, new_c) and (new_r, new_c) not in occupied):
                non_capture_moves.append(((r, c), (new_r, new_c)))
    
    # Choose best non-capturing move
    if non_capture_moves:
        best_move = None
        best_score = -1
        for (from_sq, to_sq) in non_capture_moves:
            from_r, from_c = from_sq
            to_r, to_c = to_sq
            
            score = 0
            
            # Promotion is highest priority
            if (from_r, from_c) in my_men_set:
                if color == 'b' and to_r == 0:
                    score += 1000  # Very high for promotion
                elif color == 'w' and to_r == 7:
                    score += 1000
            
            # Center squares are generally safer
            if 2 <= to_r <= 5 and 2 <= to_c <= 5:
                score += 10
            
            # Prefer moving forward (away from starting row)
            if color == 'b' and from_r > to_r:
                score += 5
            elif color == 'w' and from_r < to_r:
                score += 5
            
            # Avoid moving to edge squares unless necessary
            if to_c == 1 or to_c == 6:
                score -= 3
            
            if score > best_score:
                best_score = score
                best_move = (from_sq, to_sq)
        
        return best_move
    
    # No legal moves (shouldn't happen in valid states)
    return ((0, 0), (0, 1))  # Fallback move
