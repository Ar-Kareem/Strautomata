
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    import random
    
    def get_legal_moves(pieces, opp_pieces, is_white):
        moves = []
        opp_set = set(opp_pieces)
        all_pieces = set(pieces) | opp_set
        
        direction = 1 if is_white else -1
        goal_row = 7 if is_white else 0
        
        for piece in pieces:
            row, col = piece
            
            # Forward move
            new_row = row + direction
            if 0 <= new_row <= 7:
                target = (new_row, col)
                if target not in all_pieces:
                    moves.append((piece, target))
            
            # Diagonal moves (both forward diagonals)
            for dc in [-1, 1]:
                new_col = col + dc
                if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                    target = (new_row, new_col)
                    # Can move diagonally if empty or contains opponent piece
                    if target not in all_pieces or target in opp_set:
                        moves.append((piece, target))
        
        return moves
    
    def evaluate_position(my_pieces, opp_pieces, is_white):
        if not opp_pieces:
            return 10000
        if not my_pieces:
            return -10000
        
        score = 0
        
        # Piece count
        score += (len(my_pieces) - len(opp_pieces)) * 100
        
        goal_row = 7 if is_white else 0
        opp_goal_row = 0 if is_white else 7
        
        # Advancement score
        for piece in my_pieces:
            row, col = piece
            if is_white:
                advancement = row
            else:
                advancement = 7 - row
            score += advancement * 15
            
            # Center control bonus
            center_distance = abs(col - 3.5)
            score += (3.5 - center_distance) * 5
            
            # Check for passed pawns
            is_passed = True
            if is_white:
                for opp_row, opp_col in opp_pieces:
                    if opp_row > row and abs(opp_col - col) <= 1:
                        is_passed = False
                        break
            else:
                for opp_row, opp_col in opp_pieces:
                    if opp_row < row and abs(opp_col - col) <= 1:
                        is_passed = False
                        break
            if is_passed:
                score += 30
        
        # Opponent advancement penalty
        for piece in opp_pieces:
            row, col = piece
            if is_white:
                advancement = 7 - row
            else:
                advancement = row
            score -= advancement * 15
        
        return score
    
    def minimax(my_pieces, opp_pieces, depth, alpha, beta, is_maximizing, is_white):
        if depth == 0:
            return evaluate_position(my_pieces, opp_pieces, is_white), None
        
        moves = get_legal_moves(my_pieces, opp_pieces, is_white)
        if not moves:
            return -10000 if is_maximizing else 10000, None
        
        # Move ordering: prioritize captures and forward moves
        def move_priority(move):
            from_pos, to_pos = move
            priority = 0
            if to_pos in opp_pieces:
                priority += 1000  # Captures first
            if is_white and to_pos[0] > from_pos[0]:
                priority += 100
            elif not is_white and to_pos[0] < from_pos[0]:
                priority += 100
            return -priority
        
        moves.sort(key=move_priority)
        
        best_move = moves[0]
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in moves:
                from_pos, to_pos = move
                
                # Check for immediate win
                goal_row = 7 if is_white else 0
                if to_pos[0] == goal_row:
                    return 10000, move
                
                # Make move
                new_my_pieces = [p for p in my_pieces if p != from_pos]
                new_my_pieces.append(to_pos)
                new_opp_pieces = [p for p in opp_pieces if p != to_pos]
                
                eval_score, _ = minimax(new_opp_pieces, new_my_pieces, depth - 1, alpha, beta, False, not is_white)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                from_pos, to_pos = move
                
                # Make move
                new_my_pieces = [p for p in my_pieces if p != from_pos]
                new_my_pieces.append(to_pos)
                new_opp_pieces = [p for p in opp_pieces if p != to_pos]
                
                eval_score, _ = minimax(new_opp_pieces, new_my_pieces, depth - 1, alpha, beta, True, not is_white)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    is_white = (color == 'w')
    
    # Search with depth 3
    _, best_move = minimax(me, opp, 3, float('-inf'), float('inf'), True, is_white)
    
    if best_move is None:
        # Fallback: return any legal move
        moves = get_legal_moves(me, opp, is_white)
        if moves:
            best_move = moves[0]
        else:
            # Emergency fallback
            best_move = ((me[0][0], me[0][1]), (me[0][0], me[0][1]))
    
    return best_move
