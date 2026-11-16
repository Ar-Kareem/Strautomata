
def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Advanced Checkers AI using minimax with alpha-beta pruning
    """
    
    # Convert lists to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    def is_valid_square(row, col):
        return 0 <= row <= 7 and 0 <= col <= 7
    
    def get_all_moves(men, kings, opp_men_s, opp_kings_s, is_my_turn):
        """Generate all legal moves including captures"""
        captures = []
        regular_moves = []
        
        all_occupied = men | kings | opp_men_s | opp_kings_s
        
        # Direction based on color
        if is_my_turn:
            man_dirs = [(1, -1), (1, 1)] if color == 'w' else [(-1, -1), (-1, 1)]
        else:
            man_dirs = [(1, -1), (1, 1)] if color == 'b' else [(-1, -1), (-1, 1)]
        
        king_dirs = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
        
        # Check men
        for (r, c) in men:
            # Check captures for men
            for dr, dc in man_dirs:
                mid_r, mid_c = r + dr, c + dc
                land_r, land_c = r + 2*dr, c + 2*dc
                
                if is_valid_square(land_r, land_c) and (land_r, land_c) not in all_occupied:
                    if (mid_r, mid_c) in opp_men_s or (mid_r, mid_c) in opp_kings_s:
                        captures.append(((r, c), (land_r, land_c)))
            
            # Regular moves for men
            for dr, dc in man_dirs:
                new_r, new_c = r + dr, c + dc
                if is_valid_square(new_r, new_c) and (new_r, new_c) not in all_occupied:
                    regular_moves.append(((r, c), (new_r, new_c)))
        
        # Check kings
        for (r, c) in kings:
            # Check captures for kings
            for dr, dc in king_dirs:
                mid_r, mid_c = r + dr, c + dc
                land_r, land_c = r + 2*dr, c + 2*dc
                
                if is_valid_square(land_r, land_c) and (land_r, land_c) not in all_occupied:
                    if (mid_r, mid_c) in opp_men_s or (mid_r, mid_c) in opp_kings_s:
                        captures.append(((r, c), (land_r, land_c)))
            
            # Regular moves for kings
            for dr, dc in king_dirs:
                new_r, new_c = r + dr, c + dc
                if is_valid_square(new_r, new_c) and (new_r, new_c) not in all_occupied:
                    regular_moves.append(((r, c), (new_r, new_c)))
        
        # Return captures if available (mandatory), otherwise regular moves
        return captures if captures else regular_moves
    
    def apply_move(move, men, kings, opp_men_s, opp_kings_s, is_my_turn):
        """Apply a move and return new state"""
        (fr, fc), (tr, tc) = move
        
        new_men = men.copy()
        new_kings = kings.copy()
        new_opp_men = opp_men_s.copy()
        new_opp_kings = opp_kings_s.copy()
        
        # Move the piece
        is_king = (fr, fc) in kings
        
        if (fr, fc) in men:
            new_men.remove((fr, fc))
        else:
            new_kings.remove((fr, fc))
        
        # Check for capture
        if abs(tr - fr) == 2:
            mid_r, mid_c = (fr + tr) // 2, (fc + tc) // 2
            new_opp_men.discard((mid_r, mid_c))
            new_opp_kings.discard((mid_r, mid_c))
        
        # Check for promotion
        promotion_row = 7 if color == 'w' else 0
        opponent_promotion_row = 0 if color == 'w' else 7
        
        if is_my_turn:
            if is_king or tr == promotion_row:
                new_kings.add((tr, tc))
            else:
                new_men.add((tr, tc))
        else:
            if is_king or tr == opponent_promotion_row:
                new_opp_kings.add((tr, tc))
            else:
                new_opp_men.add((tr, tc))
        
        return new_men, new_kings, new_opp_men, new_opp_kings
    
    def evaluate(men, kings, opp_men_s, opp_kings_s):
        """Evaluate board position"""
        # Material
        my_material = len(men) * 100 + len(kings) * 310
        opp_material = len(opp_men_s) * 100 + len(opp_kings_s) * 310
        
        # Positional bonuses
        my_pos = 0
        for r, c in men:
            # Advancement bonus
            advance = r if color == 'w' else (7 - r)
            my_pos += advance * 5
            # Center control
            if 2 <= c <= 5:
                my_pos += 3
        
        for r, c in kings:
            # Center control for kings
            if 2 <= r <= 5 and 2 <= c <= 5:
                my_pos += 10
        
        opp_pos = 0
        for r, c in opp_men_s:
            advance = r if color == 'b' else (7 - r)
            opp_pos += advance * 5
            if 2 <= c <= 5:
                opp_pos += 3
        
        for r, c in opp_kings_s:
            if 2 <= r <= 5 and 2 <= c <= 5:
                opp_pos += 10
        
        return (my_material + my_pos) - (opp_material + opp_pos)
    
    def minimax(men, kings, opp_men_s, opp_kings_s, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning"""
        if depth == 0:
            return evaluate(men, kings, opp_men_s, opp_kings_s), None
        
        if maximizing:
            moves = get_all_moves(men, kings, opp_men_s, opp_kings_s, True)
            if not moves:
                return -99999, None
            
            max_eval = -999999
            best_move = moves[0]
            
            for move in moves:
                new_men, new_kings, new_opp_men, new_opp_kings = apply_move(
                    move, men, kings, opp_men_s, opp_kings_s, True
                )
                eval_score, _ = minimax(new_men, new_kings, new_opp_men, new_opp_kings, 
                                       depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            moves = get_all_moves(opp_men_s, opp_kings_s, men, kings, False)
            if not moves:
                return 99999, None
            
            min_eval = 999999
            best_move = moves[0]
            
            for move in moves:
                new_opp_men, new_opp_kings, new_men, new_kings = apply_move(
                    move, opp_men_s, opp_kings_s, men, kings, False
                )
                eval_score, _ = minimax(new_men, new_kings, new_opp_men, new_opp_kings,
                                       depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    # Search for best move
    _, best_move = minimax(my_men_set, my_kings_set, opp_men_set, opp_kings_set, 
                           6, -999999, 999999, True)
    
    # Fallback: if no move found, get any legal move
    if best_move is None:
        moves = get_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, True)
        if moves:
            best_move = moves[0]
    
    return best_move
