
def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    import collections

    # Board representation
    board = {}
    for pos in my_men:
        board[pos] = ('my', 'man')
    for pos in my_kings:
        board[pos] = ('my', 'king')
    for pos in opp_men:
        board[pos] = ('opp', 'man')
    for pos in opp_kings:
        board[pos] = ('opp', 'king')

    # Generate all possible moves
    def get_moves_for_piece(piece_pos, piece_type, is_my_piece=True):
        moves = []
        r, c = piece_pos
        is_king = piece_type == 'king'
        
        # Define move directions
        if is_king:
            directions = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        else:
            if color == 'b':  # Black moves down (decreasing row)
                directions = [(-1, -1), (-1, 1)]
            else:  # White moves up (increasing row)
                directions = [(1, 1), (1, -1)]
        
        # Check for captures
        for dr, dc in directions:
            # Jump over opponent piece
            mid_r, mid_c = r + dr, c + dc
            jump_r, jump_c = r + 2*dr, c + 2*dc
            
            # Check if mid position is opponent and jump position is empty
            if (0 <= mid_r <= 7 and 0 <= mid_c <= 7 and 
                (mid_r + mid_c) % 2 == 0 and  # dark square
                board.get((mid_r, mid_c), (None, None))[0] == 'opp' and
                0 <= jump_r <= 7 and 0 <= jump_c <= 7 and 
                (jump_r + jump_c) % 2 == 0 and  # dark square
                (jump_r, jump_c) not in board):
                moves.append(('capture', (r, c), (jump_r, jump_c), (mid_r, mid_c)))
        
        # If no captures yet, check for simple moves
        if not any(m[0] == 'capture' for m in moves):
            for dr, dc in directions:
                new_r, new_c = r + dr, c + dc
                if (0 <= new_r <= 7 and 0 <= new_c <= 7 and 
                    (new_r + new_c) % 2 == 0 and  # dark square
                    (new_r, new_c) not in board):
                    moves.append(('move', (r, c), (new_r, new_c)))
        
        return moves

    # Get all possible moves
    all_moves = []
    for pos in my_men:
        all_moves.extend(get_moves_for_piece(pos, 'man'))
    for pos in my_kings:
        all_moves.extend(get_moves_for_piece(pos, 'king'))

    # If no moves, return a dummy move (should not happen in a real game)
    if not all_moves:
        return ((0, 0), (0, 0))

    # Separate captures and regular moves
    captures = [m for m in all_moves if m[0] == 'capture']
    
    # If captures are available, must take one
    if captures:
        # For simplicity, just take the first capture (in real implementation, 
        # we might want to look for multi-captures)
        # But let's find the capture sequence that captures the most pieces
        def find_capture_sequences(start_pos):
            sequences = []
            def dfs(current_pos, sequence, captured_positions):
                moves_from_here = get_moves_for_piece(current_pos, 
                                                    'king' if current_pos in my_kings else 'man')
                captures_from_here = [m for m in moves_from_here if m[0] == 'capture' 
                                    and m[3] not in captured_positions]  # Not already captured
                if not captures_from_here:
                    sequences.append(sequence)
                    return
                for cap in captures_from_here:
                    _, _, next_pos, captured_pos = cap
                    dfs(next_pos, sequence + [cap], captured_positions | {captured_pos})
            
            dfs(start_pos, [], set())
            return sequences
        
        # Find all possible capture sequences
        best_capture_move = None
        max_captures = 0
        
        # Check captures from each piece
        capture_pieces = set(m[1] for m in captures)
        for piece_pos in capture_pieces:
            sequences = find_capture_sequences(piece_pos)
            for seq in sequences:
                if len(seq) > max_captures:
                    max_captures = len(seq)
                    best_capture_move = seq[0]  # First move of best sequence
        
        # If we found a multi-capture, use it, otherwise just use a single capture
        if best_capture_move:
            return (best_capture_move[1], best_capture_move[2])
        else:
            # Fallback to first capture
            capture = captures[0]
            return (capture[1], capture[2])
    
    # No captures - evaluate regular moves
    regular_moves = [m for m in all_moves if m[0] == 'move']
    
    # Evaluate moves based on promotion, safety, center control, advancement
    def evaluate_move(move):
        _, from_pos, to_pos = move
        from_r, from_c = from_pos
        to_r, to_c = to_pos
        
        score = 0
        
        # Promotion opportunity
        if from_pos in my_men:  # Only men can be promoted
            if color == 'b' and to_r == 0:
                score += 100  # Promotion
            elif color == 'w' and to_r == 7:
                score += 100  # Promotion
                
        # Advancement
        if color == 'b':  # Moving down
            score += (from_r - to_r) * 5
        else:  # Moving up
            score += (to_r - from_r) * 5
            
        # Center control (columns 2,3,4,5 are considered central)
        if 2 <= to_c <= 5:
            score += 3
            
        # Avoid edges
        if to_c == 0 or to_c == 7:
            score -= 2
            
        return score
    
    # Sort moves by evaluation score
    regular_moves.sort(key=evaluate_move, reverse=True)
    
    # Return the best move
    if regular_moves:
        best_move = regular_moves[0]
        return (best_move[1], best_move[2])
    else:
        # Should not happen, but just in case
        return ((0, 0), (0, 0))
