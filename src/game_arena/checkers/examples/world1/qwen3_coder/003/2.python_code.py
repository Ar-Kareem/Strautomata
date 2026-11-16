
import random

def policy(my_men, my_kings, opp_men, opp_kings, color):
    def get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color):
        moves = []
        # Combine all pieces
        my_pieces = my_men + my_kings
        opp_pieces = opp_men + opp_kings
        
        # Check for captures first (mandatory)
        captures = []
        for r, c in my_pieces:
            piece_type = 'king' if (r, c) in my_kings else 'man'
            captures.extend(get_captures(r, c, piece_type, my_pieces, opp_pieces, color))
        
        if captures:
            return captures
            
        # If no captures, get regular moves
        for r, c in my_pieces:
            piece_type = 'king' if (r, c) in my_kings else 'man'
            moves.extend(get_regular_moves(r, c, piece_type, my_pieces, opp_pieces, color))
            
        return moves if moves else [((0,0),(0,0))] # Fallback
    
    def get_regular_moves(r, c, piece_type, my_pieces, opp_pieces, color):
        moves = []
        directions = []
        
        if piece_type == 'king':
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:  # man
            if color == 'b':  # black moves down (decreasing row)
                directions = [(-1, -1), (-1, 1)]
            else:  # white moves up (increasing row)
                directions = [(1, -1), (1, 1)]
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7 and (nr + nc) % 2 == 1:  # valid dark square
                if (nr, nc) not in my_pieces and (nr, nc) not in opp_pieces:
                    moves.append(((r, c), (nr, nc)))
        
        return moves
    
    def get_captures(r, c, piece_type, my_pieces, opp_pieces, color):
        captures = []
        directions = []
        
        if piece_type == 'king':
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:  # man
            if color == 'b':  # black moves down (decreasing row)
                directions = [(-1, -1), (-1, 1)]
            else:  # white moves up (increasing row)
                directions = [(1, -1), (1, 1)]
        
        for dr, dc in directions:
            # Check if there's an opponent piece to jump over
            nr, nc = r + dr, c + dc
            if (nr, nc) in opp_pieces:
                # Check if we can land after the jump
                landing_r, landing_c = r + 2*dr, c + 2*dc
                if (0 <= landing_r <= 7 and 0 <= landing_c <= 7 and 
                    (landing_r + landing_c) % 2 == 1 and
                    (landing_r, landing_c) not in my_pieces and 
                    (landing_r, landing_c) not in opp_pieces):
                    captures.append(((r, c), (landing_r, landing_c)))
        
        return captures
    
    def make_move(board_state, move):
        # Simplified board state update for minimax
        # In a real implementation, you'd need to handle captures, king promotion, etc.
        return board_state
    
    def evaluate_position(my_men, my_kings, opp_men, opp_kings, color):
        # Simple evaluation function
        score = 0
        score += len(my_men) * 100
        score += len(my_kings) * 300
        score -= len(opp_men) * 100
        score -= len(opp_kings) * 300
        
        # Positional bonuses
        for r, c in my_men:
            # Bonus for advancing (getting closer to becoming king)
            if color == 'b':
                score += (7 - r) * 5
            else:
                score += r * 5
                
            # Bonus for center control
            if 2 <= r <= 5 and 2 <= c <= 5:
                score += 10
        
        for r, c in my_kings:
            # Kings are valuable for mobility
            score += 20
            
        return score
    
    def minimax(depth, maximizing, my_men, my_kings, opp_men, opp_kings, alpha, beta, color):
        if depth == 0:
            return evaluate_position(my_men, my_kings, opp_men, opp_kings, color), None
        
        moves = get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color)
        
        if not moves:
            if maximizing:
                return -10000, None
            else:
                return 10000, None
        
        best_move = None
        
        if maximizing:
            max_eval = float('-inf')
            for move in moves:
                # Simulate the move
                new_my_men, new_my_kings, new_opp_men, new_opp_kings = simulate_move(
                    move, my_men[:], my_kings[:], opp_men[:], opp_kings[:], color)
                
                eval_score, _ = minimax(depth - 1, False, new_opp_men, new_opp_kings, 
                                         new_my_men, new_my_kings, alpha, beta, 'b' if color == 'w' else 'w')
                
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
                # Simulate the move
                new_opp_men, new_opp_kings, new_my_men, new_my_kings = simulate_move(
                    move, opp_men[:], opp_kings[:], my_men[:], my_kings[:], 'b' if color == 'w' else 'w')
                
                eval_score, _ = minimax(depth - 1, True, new_my_men, new_my_kings, 
                                        new_opp_men, new_opp_kings, alpha, beta, color)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                    
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    def simulate_move(move, mover_men, mover_kings, opp_men, opp_kings, mover_color):
        # Create copies
        new_mover_men = mover_men[:]
        new_mover_kings = mover_kings[:]
        new_opp_men = opp_men[:]
        new_opp_kings = opp_kings[:]
        
        from_pos, to_pos = move
        
        # Remove piece from old position
        if from_pos in new_mover_men:
            new_mover_men.remove(from_pos)
        elif from_pos in new_mover_kings:
            new_mover_kings.remove(from_pos)
            
        # Add piece to new position
        # Check for promotion
        if (from_pos in mover_men or from_pos in mover_kings):  # Was a man
            if mover_color == 'b' and to_pos[0] == 0:
                new_mover_kings.append(to_pos)  # Promote to king
            elif mover_color == 'w' and to_pos[0] == 7:
                new_mover_kings.append(to_pos)  # Promote to king
            else:
                if from_pos in mover_men:
                    new_mover_men.append(to_pos)
                else:
                    new_mover_kings.append(to_pos)
        
        # Check for capture
        dr = to_pos[0] - from_pos[0]
        dc = to_pos[1] - from_pos[1]
        if abs(dr) == 2 and abs(dc) == 2:  # This was a capture
            capture_r = from_pos[0] + dr//2
            capture_c = from_pos[1] + dc//2
            
            # Remove captured piece
            if (capture_r, capture_c) in new_opp_men:
                new_opp_men.remove((capture_r, capture_c))
            elif (capture_r, capture_c) in new_opp_kings:
                new_opp_kings.remove((capture_r, capture_c))
                
        return new_mover_men, new_mover_kings, new_opp_men, new_opp_kings
    
    # Get all legal moves
    all_moves = get_all_possible_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not all_moves:
        # Must return a legal move - fallback
        return ((0,0), (0,0))
    
    # If only one move, take it
    if len(all_moves) == 1:
        return all_moves[0]
    
    # Otherwise use minimax
    try:
        _, best_move = minimax(4, True, my_men, my_kings, opp_men, opp_kings, 
                              float('-inf'), float('inf'), color)
        if best_move:
            return best_move
    except:
        pass
    
    # Fallback to random legal move
    return random.choice(all_moves)
