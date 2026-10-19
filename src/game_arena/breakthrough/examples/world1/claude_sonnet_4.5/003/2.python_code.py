
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    import random
    
    # Direction based on color
    direction = -1 if color == 'b' else 1
    goal_row = 0 if color == 'b' else 7
    
    def get_legal_moves(pieces, opp_set, dir):
        """Generate all legal moves for given pieces."""
        moves = []
        for r, c in pieces:
            # Forward move
            nr = r + dir
            if 0 <= nr <= 7 and (nr, c) not in opp_set and (nr, c) not in pieces:
                moves.append(((r, c), (nr, c)))
            
            # Diagonal moves (can be empty or capture)
            for dc in [-1, 1]:
                nc = c + dc
                if 0 <= nr <= 7 and 0 <= nc <= 7:
                    if (nr, nc) not in pieces:  # Empty or opponent
                        moves.append(((r, c), (nr, nc)))
        
        return moves
    
    def evaluate(my_pieces, opp_pieces, color):
        """Evaluate board position."""
        if not opp_pieces:
            return 10000
        if not my_pieces:
            return -10000
        
        my_set = set(my_pieces)
        opp_set = set(opp_pieces)
        dir = -1 if color == 'b' else 1
        my_goal = 0 if color == 'b' else 7
        opp_goal = 7 if color == 'b' else 0
        
        score = 0
        
        # Material advantage (very important)
        score += (len(my_pieces) - len(opp_pieces)) * 100
        
        # Progress toward goal
        for r, c in my_pieces:
            progress = abs(r - my_goal)
            score += (7 - progress) * 10
            
            # Big bonus for pieces close to goal
            if progress <= 1:
                score += 200
        
        # Opponent progress (negative)
        for r, c in opp_pieces:
            progress = abs(r - opp_goal)
            score -= (7 - progress) * 10
            
            if progress <= 1:
                score -= 200
        
        # Center control bonus
        for r, c in my_pieces:
            if 2 <= c <= 5:
                score += 5
        
        return score
    
    def minimax(my_pieces, opp_pieces, depth, alpha, beta, maximizing, color):
        """Minimax with alpha-beta pruning."""
        my_set = set(my_pieces)
        opp_set = set(opp_pieces)
        dir = -1 if color == 'b' else 1
        opp_color = 'w' if color == 'b' else 'b'
        opp_dir = -dir
        
        # Check terminal conditions
        if depth == 0:
            return evaluate(my_pieces, opp_pieces, color), None
        
        if maximizing:
            moves = get_legal_moves(my_pieces, opp_set, dir)
            
            if not moves:
                return -10000, None
            
            # Check for immediate win
            for move in moves:
                if move[1][0] == (0 if color == 'b' else 7):
                    return 10000, move
            
            # Move ordering: captures and forward moves first
            def move_priority(m):
                score = 0
                if m[1] in opp_set:
                    score += 1000  # Captures
                progress = abs(m[1][0] - (0 if color == 'b' else 7))
                score += (7 - progress) * 10
                return -score
            
            moves.sort(key=move_priority)
            
            max_eval = float('-inf')
            best_move = moves[0]
            
            for move in moves:
                # Apply move
                new_my = [p for p in my_pieces if p != move[0]]
                new_my.append(move[1])
                new_opp = [p for p in opp_pieces if p != move[1]]
                
                eval_score, _ = minimax(new_opp, new_my, depth - 1, alpha, beta, False, opp_color)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            moves = get_legal_moves(my_pieces, opp_set, dir)
            
            if not moves:
                return 10000, None
            
            # Check for opponent immediate win
            for move in moves:
                if move[1][0] == (0 if color == 'b' else 7):
                    return -10000, move
            
            min_eval = float('inf')
            best_move = moves[0]
            
            for move in moves:
                new_my = [p for p in my_pieces if p != move[0]]
                new_my.append(move[1])
                new_opp = [p for p in opp_pieces if p != move[1]]
                
                eval_score, _ = minimax(new_opp, new_my, depth - 1, alpha, beta, True, opp_color)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    # Get all legal moves as fallback
    opp_set = set(opp)
    legal_moves = get_legal_moves(me, opp_set, direction)
    
    if not legal_moves:
        # Should never happen in valid game state
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))
    
    # Check for immediate win
    for move in legal_moves:
        if move[1][0] == goal_row:
            return move
    
    # Use minimax to find best move
    depth = 3  # Adjust based on performance
    _, best_move = minimax(me, opp, depth, float('-inf'), float('inf'), True, color)
    
    if best_move is None:
        best_move = random.choice(legal_moves)
    
    return best_move
