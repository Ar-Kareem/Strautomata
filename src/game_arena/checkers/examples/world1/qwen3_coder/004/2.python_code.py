
import collections

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Convert lists to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    all_opp_pieces = opp_men_set | opp_kings_set
    all_my_pieces = my_men_set | my_kings_set
    
    # Determine direction based on color
    if color == 'b':  # Black moves down (decreasing row numbers)
        directions = [(-1, -1), (-1, 1)]  # Down-left, down-right
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:  # White moves up (increasing row numbers)
        directions = [(1, -1), (1, 1)]   # Up-left, up-right
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    def is_valid_square(row, col):
        return 0 <= row <= 7 and 0 <= col <= 7 and (row + col) % 2 == 1
    
    def get_all_capture_sequences():
        """Get all possible capture sequences"""
        capture_sequences = []
        
        # Check captures for men
        for piece in my_men_set:
            sequences = get_piece_capture_sequences(piece, directions, False)
            capture_sequences.extend(sequences)
            
        # Check captures for kings
        for piece in my_kings_set:
            sequences = get_piece_capture_sequences(piece, king_directions, True)
            capture_sequences.extend(sequences)
            
        return capture_sequences
    
    def get_piece_capture_sequences(start_pos, dirs, is_king):
        """Get all capture sequences starting from start_pos"""
        sequences = []
        
        def dfs(current_pos, visited, path, captured):
            added_move = False
            row, col = current_pos
            
            # Try all directions
            for dr, dc in dirs:
                # Check capture possibility
                mid_row, mid_col = row + dr, col + dc
                jump_row, jump_col = row + 2*dr, col + 2*dc
                
                # Check if middle square has opponent piece and jump square is empty
                if (is_valid_square(mid_row, mid_col) and 
                    (mid_row, mid_col) in all_opp_pieces and 
                    (mid_row, mid_col) not in captured and
                    is_valid_square(jump_row, jump_col) and 
                    (jump_row, jump_col) not in all_my_pieces and
                    (jump_row, jump_col) not in all_opp_pieces and
                    (jump_row, jump_col) not in visited):
                    
                    added_move = True
                    new_visited = visited | {(jump_row, jump_col)}
                    new_captured = captured | {(mid_row, mid_col)}
                    new_path = path + [((row, col), (jump_row, jump_col))]
                    dfs((jump_row, jump_col), new_visited, new_path, new_captured)
            
            # If no more captures possible, add sequence to results
            if not added_move and len(path) > 0:
                sequences.append((path, len(captured)))
        
        dfs(start_pos, {start_pos}, [], set())
        return sequences
    
    # First, check for captures
    capture_sequences = get_all_capture_sequences()
    
    if capture_sequences:
        # Find sequences that capture maximum number of pieces
        max_captures = max(seq[1] for seq in capture_sequences)
        best_sequences = [seq[0] for seq in capture_sequences if seq[1] == max_captures]
        # Return first move of first best sequence
        return best_sequences[0][0]
    
    # If no captures, evaluate regular moves
    def get_regular_moves():
        moves = []
        
        # Regular moves for men
        for piece in my_men_set:
            row, col = piece
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                if (is_valid_square(new_row, new_col) and 
                    (new_row, new_col) not in all_my_pieces and
                    (new_row, new_col) not in all_opp_pieces):
                    moves.append((piece, (new_row, new_col)))
        
        # Regular moves for kings
        for piece in my_kings_set:
            row, col = piece
            for dr, dc in king_directions:
                new_row, new_col = row + dr, col + dc
                if (is_valid_square(new_row, new_col) and 
                    (new_row, new_col) not in all_my_pieces and
                    (new_row, new_col) not in all_opp_pieces):
                    moves.append((piece, (new_row, new_col)))
        
        return moves
    
    def evaluate_move(move):
        """Evaluate move based on various heuristics"""
        from_pos, to_pos = move
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        score = 0
        
        # Bonus for king promotion
        if from_pos in my_men_set:
            if color == 'b' and to_row == 0:
                score += 100  # Promote to king
            elif color == 'w' and to_row == 7:
                score += 100  # Promote to king
                
        # Bonus for advancing forward
        if color == 'b':  # Moving down
            if to_row < from_row:
                score += 5 * (from_row - to_row)  # More bonus for moving further down
        else:  # Moving up
            if to_row > from_row:
                score += 5 * (to_row - from_row)  # More bonus for moving further up
        
        # Control center bonus
        if 2 <= to_row <= 5 and 2 <= to_col <= 5:
            score += 3
            
        # Avoid edges slightly
        if to_col == 0 or to_col == 7:
            score -= 2
            
        return score
    
    # Get all regular moves
    regular_moves = get_regular_moves()
    
    if regular_moves:
        # Evaluate all moves and pick the best one
        best_move = None
        best_score = float('-inf')
        
        for move in regular_moves:
            score = evaluate_move(move)
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move
    else:
        # Fallback: should not happen in a valid game state
        # But if it does, just return a valid move if somehow exists
        for piece in my_men_set:
            return (piece, piece)  # This would be invalid but satisfies return type
        for piece in my_kings_set:
            return (piece, piece)  # This would be invalid but satisfies return type
