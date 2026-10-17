
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Smart Breakthrough policy with minimax evaluation and strategic heuristics.
    """
    
    def get_legal_moves(pieces, opponent_pieces, is_white):
        """Generate all legal moves for the given pieces."""
        moves = []
        opp_set = set(opponent_pieces)
        all_pieces = set(pieces) | opp_set
        
        direction = 1 if is_white else -1
        target_row = 7 if is_white else 0
        
        for row, col in pieces:
            # Forward move
            new_row = row + direction
            if 0 <= new_row <= 7:
                if (new_row, col) not in all_pieces:
                    moves.append(((row, col), (new_row, col)))
                
                # Diagonal captures or empty diagonal moves
                for dc in [-1, 1]:
                    new_col = col + dc
                    if 0 <= new_col <= 7:
                        target = (new_row, new_col)
                        if target in opp_set:  # Capture
                            moves.append(((row, col), target))
                        elif target not in all_pieces:  # Empty diagonal
                            moves.append(((row, col), target))
        
        return moves
    
    def evaluate_position(my_pieces, opp_pieces, is_white):
        """Evaluate the board position from current player's perspective."""
        if not opp_pieces:
            return 10000  # Won by capturing all
        if not my_pieces:
            return -10000  # Lost all pieces
        
        target_row = 7 if is_white else 0
        opp_target_row = 0 if is_white else 7
        
        # Check for immediate win
        for row, col in my_pieces:
            if row == target_row:
                return 10000
        for row, col in opp_pieces:
            if row == opp_target_row:
                return -10000
        
        score = 0
        
        # Material count (very important)
        score += (len(my_pieces) - len(opp_pieces)) * 100
        
        # Progress evaluation
        for row, col in my_pieces:
            if is_white:
                distance = row  # Higher is better for white
                progress = distance * distance  # Exponential reward
            else:
                distance = 7 - row  # Lower is better for black
                progress = distance * distance
            
            score += progress
            
            # Bonus for very advanced pieces
            if distance >= 5:
                score += 50
            
            # Small center control bonus
            if 2 <= col <= 5:
                score += 2
        
        # Opponent's progress (negative)
        for row, col in opp_pieces:
            if is_white:
                distance = 7 - row
                progress = distance * distance
            else:
                distance = row
                progress = distance * distance
            
            score -= progress
            
            if distance >= 5:
                score -= 50
        
        return score
    
    def minimax(my_pieces, opp_pieces, is_white, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate_position(my_pieces, opp_pieces, is_white if maximizing else not is_white)
        
        moves = get_legal_moves(my_pieces, opp_pieces, is_white if maximizing else not is_white)
        if not moves:
            return -10000 if maximizing else 10000
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                from_pos, to_pos = move
                new_my = [p for p in my_pieces if p != from_pos]
                new_my.append(to_pos)
                new_opp = [p for p in opp_pieces if p != to_pos]
                
                eval_score = minimax(new_opp, new_my, not is_white, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                from_pos, to_pos = move
                new_opp = [p for p in opp_pieces if p != from_pos]
                new_opp.append(to_pos)
                new_my = [p for p in my_pieces if p != to_pos]
                
                eval_score = minimax(new_my, new_opp, is_white, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    is_white = (color == 'w')
    target_row = 7 if is_white else 0
    
    # Get all legal moves
    legal_moves = get_legal_moves(me, opp, is_white)
    
    if not legal_moves:
        # Should never happen, but return a safe default
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))
    
    # Check for immediate winning moves
    for move in legal_moves:
        if move[1][0] == target_row:
            return move
    
    # Evaluate all moves with minimax
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for move in legal_moves:
        from_pos, to_pos = move
        new_me = [p for p in me if p != from_pos]
        new_me.append(to_pos)
        new_opp = [p for p in opp if p != to_pos]
        
        # Use 2-ply search
        score = minimax(new_opp, new_me, not is_white, 1, -float('inf'), float('inf'), False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
