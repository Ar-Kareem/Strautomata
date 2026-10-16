
def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Precompute base board values for central control
    base_board_value = [[0] * 8 for _ in range(8)]
    for r in range(8):
        for c in range(8):
            if (r + c) % 2 == 1:  # dark square
                if 2 <= r <= 5 and 2 <= c <= 5:
                    base_board_value[r][c] = 3
                elif 1 <= r <= 6 and 1 <= c <= 6:
                    base_board_value[r][c] = 2
                else:
                    base_board_value[r][c] = 1
            else:
                base_board_value[r][c] = 0
    
    # Create sets for quick lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    my_pieces = my_men_set | my_kings_set
    opponent_pieces = opp_men_set | opp_kings_set
    occupied_set = my_pieces | opponent_pieces
    
    moves = []
    
    # Generate moves for men
    for (r, c) in my_men:
        # Directions: black moves down (negative row), white moves up (positive row)
        directions = [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]
        
        for (dr, dc) in directions:
            # Regular move
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) not in occupied_set:
                is_promotion = (color == 'b' and new_r == 0) or (color == 'w' and new_r == 7)
                moves.append(((r, c), (new_r, new_c), False, 0, is_promotion))
            
            # Capture move
            mid_r, mid_c = r + dr, c + dc
            if 0 <= mid_r < 8 and 0 <= mid_c < 8 and (mid_r, mid_c) in opponent_pieces:
                land_r, land_c = r + 2 * dr, c + 2 * dc
                if 0 <= land_r < 8 and 0 <= land_c < 8 and (land_r, land_c) not in occupied_set:
                    captured_value = 3 if (mid_r, mid_c) in opp_kings_set else 1
                    is_promotion = (color == 'b' and land_r == 0) or (color == 'w' and land_r == 7)
                    moves.append(((r, c), (land_r, land_c), True, captured_value, is_promotion))
    
    # Generate moves for kings
    for (r, c) in my_kings:
        directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for (dr, dc) in directions:
            # Regular move
            new_r, new_c = r + dr, c + dc
            if 0 <= new_r < 8 and 0 <= new_c < 8 and (new_r, new_c) not in occupied_set:
                moves.append(((r, c), (new_r, new_c), False, 0, False))
            
            # Capture move
            mid_r, mid_c = r + dr, c + dc
            if 0 <= mid_r < 8 and 0 <= mid_c < 8 and (mid_r, mid_c) in opponent_pieces:
                land_r, land_c = r + 2 * dr, c + 2 * dc
                if 0 <= land_r < 8 and 0 <= land_c < 8 and (land_r, land_c) not in occupied_set:
                    captured_value = 3 if (mid_r, mid_c) in opp_kings_set else 1
                    moves.append(((r, c), (land_r, land_c), True, captured_value, False))
    
    # Separate capture and non-capture moves
    capture_moves = [m for m in moves if m[2]]  # m[2] is is_capture
    non_capture_moves = [m for m in moves if not m[2]]
    
    def calculate_value(move, base_board_value, color):
        from_pos, to_pos, is_capture, captured_value, is_promotion = move
        r, c = to_pos
        
        # Central control value
        central_value = base_board_value[r][c]
        
        # Row advancement bonus
        row_bonus = (7 - r) if color == 'b' else r
        
        # Base value
        value = central_value + row_bonus
        
        # Add capture value if applicable
        if is_capture:
            value += captured_value
        
        # Promotion bonus
        if is_promotion:
            value += 100
        
        return value
    
    if capture_moves:
        # Must make a capture if available
        best_move = max(capture_moves, key=lambda m: calculate_value(m, base_board_value, color))
    elif non_capture_moves:
        best_move = max(non_capture_moves, key=lambda m: calculate_value(m, base_board_value, color))
    else:
        # No moves available (shouldn't happen in valid game states)
        # Return a dummy move to avoid crash
        return ((0, 0), (0, 0))
    
    from_pos, to_pos = best_move[0], best_move[1]
    return (from_pos, to_pos)
