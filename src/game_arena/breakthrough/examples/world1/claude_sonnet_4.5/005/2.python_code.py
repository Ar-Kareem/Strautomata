
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    import random
    
    # Direction based on color
    direction = -1 if color == 'b' else 1
    goal_row = 0 if color == 'b' else 7
    
    def get_legal_moves(pieces, opp_set, direction, goal_row):
        """Generate all legal moves for the given pieces."""
        moves = []
        for r, c in pieces:
            # Forward move
            new_r = r + direction
            if 0 <= new_r <= 7 and (new_r, c) not in opp_set and (new_r, c) not in pieces:
                moves.append(((r, c), (new_r, c)))
            
            # Diagonal moves (can be empty or capture)
            for dc in [-1, 1]:
                new_c = c + dc
                if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                    pos = (new_r, new_c)
                    if pos not in pieces:  # Not our own piece
                        moves.append(((r, c), (new_r, new_c)))
        
        return moves
    
    def evaluate(my_pieces, opp_pieces, my_color):
        """Evaluate the board position."""
        if not opp_pieces:
            return 100000
        if not my_pieces:
            return -100000
        
        my_dir = -1 if my_color == 'b' else 1
        my_goal = 0 if my_color == 'b' else 7
        opp_goal = 7 if my_color == 'b' else 0
        
        # Check for immediate win
        for r, c in my_pieces:
            if r == my_goal:
                return 100000
        for r, c in opp_pieces:
            if r == opp_goal:
                return -100000
        
        score = 0
        
        # Piece count (very important)
        score += (len(my_pieces) - len(opp_pieces)) * 200
        
        # Advancement score (exponential growth as pieces get closer)
        for r, c in my_pieces:
            if my_color == 'b':
                progress = 7 - r
            else:
                progress = r
            score += progress ** 2 * 3
            
            # Extra bonus for very advanced pieces
            if progress >= 6:
                score += 500
            elif progress >= 5:
                score += 200
            
            # Center control bonus
            if 2 <= c <= 5:
                score += 5
        
        for r, c in opp_pieces:
            if my_color == 'b':
                progress = r
            else:
                progress = 7 - r
            score -= progress ** 2 * 3
            
            if progress >= 6:
                score -= 500
            elif progress >= 5:
                score -= 200
            
            if 2 <= c <= 5:
                score -= 5
        
        return score
    
    def minimax(my_pieces, opp_pieces, depth, alpha, beta, maximizing, my_color):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate(my_pieces, opp_pieces, my_color), None
        
        my_set = set(my_pieces)
        opp_set = set(opp_pieces)
        
        if maximizing:
            my_dir = -1 if my_color == 'b' else 1
            my_goal = 0 if my_color == 'b' else 7
            
            moves = get_legal_moves(my_pieces, opp_set, my_dir, my_goal)
            if not moves:
                return -100000, None
            
            # Move ordering: prioritize captures and forward moves
            def move_priority(move):
                (fr, fc), (tr, tc) = move
                priority = 0
                if (tr, tc) in opp_set:
                    priority += 1000  # Captures first
                priority += abs(tr - fr) * 100  # Forward moves
                return -priority
            
            moves.sort(key=move_priority)
            
            max_eval = float('-inf')
            best_move = None
            
            for move in moves:
                (fr, fc), (tr, tc) = move
                
                # Check for immediate win
                if tr == my_goal:
                    return 100000, move
                
                # Make move
                new_my = [p for p in my_pieces if p != (fr, fc)] + [(tr, tc)]
                new_opp = [p for p in opp_pieces if p != (tr, tc)]
                
                eval_score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, False, my_color)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            opp_dir = 1 if my_color == 'b' else -1
            opp_goal = 7 if my_color == 'b' else 0
            
            moves = get_legal_moves(opp_pieces, my_set, opp_dir, opp_goal)
            if not moves:
                return 100000, None
            
            min_eval = float('inf')
            
            for move in moves[:20]:  # Limit opponent moves for speed
                (fr, fc), (tr, tc) = move
                
                if tr == opp_goal:
                    return -100000, move
                
                new_opp = [p for p in opp_pieces if p != (fr, fc)] + [(tr, tc)]
                new_my = [p for p in my_pieces if p != (tr, tc)]
                
                eval_score, _ = minimax(new_my, new_opp, depth - 1, alpha, beta, True, my_color)
                
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, None
    
    # Get legal moves
    opp_set = set(opp)
    moves = get_legal_moves(me, opp_set, direction, goal_row)
    
    if not moves:
        # Should never happen, but return a safe default
        return ((me[0][0], me[0][1]), (me[0][0] + direction, me[0][1]))
    
    # Use minimax to find best move
    depth = 3 if len(me) + len(opp) > 20 else 4
    _, best_move = minimax(me, opp, depth, float('-inf'), float('inf'), True, color)
    
    if best_move is None:
        best_move = moves[0]
    
    return best_move
