
def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Advanced Checkers AI with minimax search and strategic evaluation
    """
    
    # Convert lists to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    all_my_pieces = my_men_set | my_kings_set
    all_opp_pieces = opp_men_set | opp_kings_set
    all_pieces = all_my_pieces | all_opp_pieces
    
    # Direction setup
    if color == 'w':
        man_dirs = [(1, -1), (1, 1)]  # White moves up
        promotion_row = 7
    else:
        man_dirs = [(-1, -1), (-1, 1)]  # Black moves down
        promotion_row = 0
    
    king_dirs = [(1, -1), (1, 1), (-1, -1), (-1, 1)]
    
    def is_valid(r, c):
        return 0 <= r <= 7 and 0 <= c <= 7
    
    def get_captures(piece, is_king, visited=None):
        """Recursively find all capture sequences from a piece"""
        if visited is None:
            visited = set()
        
        visited.add(piece)
        directions = king_dirs if is_king else man_dirs
        captures = []
        
        for dr, dc in directions:
            mid_r, mid_c = piece[0] + dr, piece[1] + dc
            land_r, land_c = piece[0] + 2*dr, piece[1] + 2*dc
            
            if is_valid(land_r, land_c) and (land_r, land_c) not in visited:
                # Check if there's an opponent piece to capture
                if (mid_r, mid_c) in all_opp_pieces and (land_r, land_c) not in all_pieces:
                    # Found a capture
                    new_pos = (land_r, land_c)
                    # Check for multi-jump
                    further_captures = get_captures(new_pos, is_king, visited.copy())
                    
                    if further_captures:
                        for seq in further_captures:
                            captures.append([(piece, new_pos)] + seq)
                    else:
                        captures.append([(piece, new_pos)])
        
        return captures
    
    def get_all_captures():
        """Get all possible capture moves"""
        all_captures = []
        
        for piece in my_men_set:
            capture_seqs = get_captures(piece, False)
            for seq in capture_seqs:
                # Return the first and last position of the sequence
                all_captures.append((seq[0][0], seq[-1][1], len(seq)))
        
        for piece in my_kings_set:
            capture_seqs = get_captures(piece, True)
            for seq in capture_seqs:
                all_captures.append((seq[0][0], seq[-1][1], len(seq)))
        
        return all_captures
    
    def get_simple_moves():
        """Get all non-capture moves"""
        moves = []
        
        for piece in my_men_set:
            for dr, dc in man_dirs:
                new_r, new_c = piece[0] + dr, piece[1] + dc
                if is_valid(new_r, new_c) and (new_r, new_c) not in all_pieces:
                    moves.append((piece, (new_r, new_c)))
        
        for piece in my_kings_set:
            for dr, dc in king_dirs:
                new_r, new_c = piece[0] + dr, piece[1] + dc
                if is_valid(new_r, new_c) and (new_r, new_c) not in all_pieces:
                    moves.append((piece, (new_r, new_c)))
        
        return moves
    
    def evaluate_position(my_m, my_k, opp_m, opp_k):
        """Evaluate board position"""
        score = 0
        
        # Material count
        score += len(my_m) * 3 + len(my_k) * 5
        score -= len(opp_m) * 3 + len(opp_k) * 5
        
        # Positional bonuses
        for piece in my_m:
            # Advancement bonus
            if color == 'w':
                score += piece[0] * 0.2
                if piece[0] == 6:  # Close to promotion
                    score += 1
            else:
                score += (7 - piece[0]) * 0.2
                if piece[0] == 1:
                    score += 1
            
            # Center control
            if 2 <= piece[1] <= 5:
                score += 0.3
        
        for piece in my_k:
            # Kings in center
            if 2 <= piece[0] <= 5 and 2 <= piece[1] <= 5:
                score += 0.5
        
        return score
    
    def minimax(my_m, my_k, opp_m, opp_k, depth, is_maximizing, alpha, beta):
        """Minimax with alpha-beta pruning"""
        if depth == 0:
            return evaluate_position(my_m, my_k, opp_m, opp_k)
        
        # Generate moves based on current player
        my_m_set = set(my_m)
        my_k_set = set(my_k)
        opp_m_set = set(opp_m)
        opp_k_set = set(opp_k)
        
        all_my = my_m_set | my_k_set
        all_opp = opp_m_set | opp_k_set
        all_pcs = all_my | all_opp
        
        # Simple move generation for minimax
        moves = []
        directions = man_dirs if is_maximizing else ([(1, -1), (1, 1)] if color == 'b' else [(-1, -1), (-1, 1)])
        
        for piece in my_m_set:
            for dr, dc in directions:
                new_pos = (piece[0] + dr, piece[1] + dc)
                if is_valid(new_pos[0], new_pos[1]) and new_pos not in all_pcs:
                    moves.append((piece, new_pos, False))
        
        for piece in my_k_set:
            for dr, dc in king_dirs:
                new_pos = (piece[0] + dr, piece[1] + dc)
                if is_valid(new_pos[0], new_pos[1]) and new_pos not in all_pcs:
                    moves.append((piece, new_pos, False))
        
        if not moves:
            return -10000 if is_maximizing else 10000
        
        if is_maximizing:
            max_eval = -float('inf')
            for from_pos, to_pos, _ in moves:
                new_my_m = [p if p != from_pos else to_pos for p in my_m if p != from_pos]
                new_my_k = list(my_k)
                if from_pos in my_m_set and to_pos[0] == promotion_row:
                    new_my_k.append(to_pos)
                elif from_pos in my_k_set:
                    new_my_k = [p if p != from_pos else to_pos for p in my_k]
                
                eval_score = minimax(opp_m, opp_k, new_my_m, new_my_k, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for from_pos, to_pos, _ in moves:
                new_my_m = [p if p != from_pos else to_pos for p in my_m if p != from_pos]
                new_my_k = list(my_k)
                
                eval_score = minimax(opp_m, opp_k, new_my_m, new_my_k, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Get captures first (mandatory)
    captures = get_all_captures()
    
    if captures:
        # Choose best capture
        best_capture = max(captures, key=lambda x: x[2])
        return (best_capture[0], best_capture[1])
    
    # Get simple moves
    moves = get_simple_moves()
    
    if not moves:
        # No legal moves (shouldn't happen in valid game)
        return ((0, 0), (0, 0))
    
    # Evaluate moves
    best_move = None
    best_score = -float('inf')
    
    for from_pos, to_pos in moves:
        # Simulate move
        new_my_m = list(my_men_set - {from_pos})
        new_my_k = list(my_kings_set)
        
        if from_pos in my_men_set:
            if to_pos[0] == promotion_row:
                new_my_k.append(to_pos)
            else:
                new_my_m.append(to_pos)
        else:
            new_my_k = list(my_kings_set - {from_pos})
            new_my_k.append(to_pos)
        
        score = evaluate_position(new_my_m, new_my_k, list(opp_men_set), list(opp_kings_set))
        
        if score > best_score:
            best_score = score
            best_move = (from_pos, to_pos)
    
    return best_move
