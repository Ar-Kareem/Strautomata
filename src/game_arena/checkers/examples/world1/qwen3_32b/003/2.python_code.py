
def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Convert to sets for faster lookups
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    # Generate all possible captures
    all_captures = []
    
    def get_captures(r, c, is_king, opp_men_set, opp_kings_set):
        captures = []
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if color == 'b':
                directions = [(-1, -1), (-1, 1)]
            else:
                directions = [(1, -1), (1, 1)]
        for dr, dc in directions:
            jump_r = r + dr
            jump_c = c + dc
            land_r = r + 2*dr
            land_c = c + 2*dc
            if not (0 <= land_r < 8 and 0 <= land_c < 8):
                continue
            jumped_square = (jump_r, jump_c)
            is_opponent = jumped_square in opp_men_set or jumped_square in opp_kings_set
            if not is_opponent:
                continue
            land_square = (land_r, land_c)
            is_empty = land_square not in my_men_set and land_square not in my_kings_set and land_square not in opp_men_set and land_square not in opp_kings_set
            if not is_empty:
                continue
            
            # Copy opponent sets and remove captured piece
            new_opp_men = set(opp_men_set)
            new_opp_kings = set(opp_kings_set)
            if jumped_square in new_opp_men:
                new_opp_men.remove(jumped_square)
            elif jumped_square in new_opp_kings:
                new_opp_kings.remove(jumped_square)
            
            # Check if piece becomes a king
            new_is_king = is_king
            if not is_king:
                if (color == 'b' and land_r == 0) or (color == 'w' and land_r == 7):
                    new_is_king = True
            
            next_captures = get_captures(land_r, land_c, new_is_king, new_opp_men, new_opp_kings)
            
            if next_captures:
                for (next_from, next_to), count in next_captures:
                    captures.append((( (r,c), next_to ), count + 1))
            else:
                captures.append((((r,c), (land_r, land_c)), 1))
        return captures
    
    for piece in my_men + my_kings:
        r, c = piece
        is_king = piece in my_kings_set
        captures = get_captures(r, c, is_king, opp_men_set, opp_kings_set)
        all_captures.extend(captures)
    
    # Tie-break captures using a simple heuristic
    def evaluate_capture(move):
        from_pos, to_pos = move
        if color == 'b':
            return -to_pos[0]  # Prefer lower rows for black
        else:
            return to_pos[0]   # Prefer higher rows for white
    
    if all_captures:
        all_captures.sort(key=lambda x: (-x[1], -evaluate_capture(x[0])))
        return all_captures[0][0]
    
    # No captures - generate all non-capturing moves
    all_moves = []
    
    def generate_moves(r, c, is_king):
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            if color == 'b':
                directions = [(-1, -1), (-1, 1)]
            else:
                directions = [(1, -1), (1, 1)]
        
        moves = []
        for dr, dc in directions:
            new_r = r + dr
            new_c = c + dc
            if not (0 <= new_r < 8 and 0 <= new_c < 8):
                continue
            new_square = (new_r, new_c)
            if new_square in my_men_set or new_square in my_kings_set or new_square in opp_men_set or new_square in opp_kings_set:
                continue
            
            becomes_king = False
            if not is_king:
                if (color == 'b' and new_r == 0) or (color == 'w' and new_r == 7):
                    becomes_king = True
                    moves.append(((r, c), new_square, 'king'))
                else:
                    moves.append(((r, c), new_square, 'man'))
            else:
                moves.append(((r, c), new_square, 'king'))
        return moves
    
    for piece in my_men + my_kings:
        r, c = piece
        is_king = piece in my_kings_set
        for move in generate_moves(r, c, is_king):
            all_moves.append(move)
    
    if not all_moves:
        return ((0, 0), (0, 0))  # Should not happen in valid game
    
    # Evaluate moves to find best one
    best_move = None
    best_score = -float('inf')
    
    for move in all_moves:
        from_pos, to_pos, move_type = move
        curr_my_men = len(my_men)
        curr_my_kings = len(my_kings)
        
        if move_type == 'king':
            new_my_men = curr_my_men - 1
            new_my_kings = curr_my_kings + 1
        else:
            new_my_men = curr_my_men
            new_my_kings = curr_my_kings
        
        my_score = new_my_men + 2 * new_my_kings
        opp_score = len(opp_men) + 2 * len(opp_kings)
        score = my_score - opp_score
        
        # Add bonus for center control
        center_row = 3.5
        center_bonus = 1 / (abs(to_pos[0] - center_row) + 1)
        score += center_bonus * 0.1
        
        if score > best_score or (score == best_score and best_move is None):
            best_score = score
            best_move = (from_pos, to_pos)
    
    return best_move
