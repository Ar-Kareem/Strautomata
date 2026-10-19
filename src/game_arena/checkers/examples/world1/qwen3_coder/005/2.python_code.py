
import collections

def policy(my_men, my_kings, opp_men, opp_kings, color):
    # Convert lists to sets for faster lookup
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    all_opp = opp_men_set | opp_kings_set
    all_my = my_men_set | my_kings_set
    
    # Define direction based on color
    if color == 'b':  # black moves down (decreasing row)
        directions = [(-1, -1), (-1, 1)]
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    else:  # white moves up (increasing row)
        directions = [(1, -1), (1, 1)]
        king_directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    # Function to check if a position is on the board
    def is_valid(row, col):
        return 0 <= row <= 7 and 0 <= col <= 7 and (row + col) % 2 == 1
    
    # Function to get all possible moves for a piece
    def get_moves(piece_row, piece_col, is_king):
        moves = []
        dirs = king_directions if is_king else directions
        
        # Check for captures first (mandatory)
        for dr, dc in dirs:
            # Check if we can capture
            jump_row, jump_col = piece_row + dr*2, piece_col + dc*2
            mid_row, mid_col = piece_row + dr, piece_col + dc
            
            if is_valid(jump_row, jump_col) and (jump_row, jump_col) not in all_my and (mid_row, mid_col) in all_opp:
                moves.append((piece_row, piece_col, jump_row, jump_col, True))  # True indicates capture
        
        # If no captures available, check regular moves
        if not moves:
            for dr, dc in dirs:
                new_row, new_col = piece_row + dr, piece_col + dc
                if is_valid(new_row, new_col) and (new_row, new_col) not in all_my and (new_row, new_col) not in all_opp:
                    moves.append((piece_row, piece_col, new_row, new_col, False))  # False indicates no capture
        
        return moves
    
    # Function to find all capture sequences (using DFS for multiple jumps)
    def find_captures(piece_row, piece_col, is_king, visited_opp=None):
        if visited_opp is None:
            visited_opp = set()
        
        captures = []
        dirs = king_directions if is_king else directions
        
        for dr, dc in dirs:
            jump_row, jump_col = piece_row + dr*2, piece_col + dc*2
            mid_row, mid_col = piece_row + dr, piece_col + dc
            
            if is_valid(jump_row, jump_col) and (jump_row, jump_col) not in all_my and (mid_row, mid_col) in all_opp and (mid_row, mid_col) not in visited_opp:
                # Found a capture, recursively check for more
                new_visited = visited_opp | {(mid_row, mid_col)}
                further_captures = find_captures(jump_row, jump_col, is_king, new_visited)
                
                if further_captures:
                    # Add this capture to each of the further capture sequences
                    for seq in further_captures:
                        captures.append([(piece_row, piece_col, jump_row, jump_col)] + seq)
                else:
                    # This is the end of a capture sequence
                    captures.append([(piece_row, piece_col, jump_row, jump_col)])
        
        return captures
    
    # Get all possible moves
    all_moves = []
    
    # Check for captures first (mandatory)
    capture_sequences = []
    for piece_row, piece_col in my_men:
        captures = find_captures(piece_row, piece_col, False)
        capture_sequences.extend(captures)
    
    for piece_row, piece_col in my_kings:
        captures = find_captures(piece_row, piece_col, True)
        capture_sequences.extend(captures)
    
    # If there are captures, we must make one of them
    if capture_sequences:
        # Find the capture sequence that captures the most pieces
        max_captures = max(len(seq) for seq in capture_sequences)
        best_sequences = [seq for seq in capture_sequences if len(seq) == max_captures]
        # Just take the first best sequence
        chosen_sequence = best_sequences[0]
        # Return the first move of the sequence
        move = chosen_sequence[0]
        return ((move[0], move[1]), (move[2], move[3]))
    
    # No captures available, consider regular moves
    # Score moves based on strategic value
    scored_moves = []
    
    # Evaluate moves for regular pieces
    for piece_row, piece_col in my_men:
        moves = get_moves(piece_row, piece_col, False)
        for move in moves:
            from_row, from_col, to_row, to_col, is_capture = move
            score = 0
            
            # Encourage advancement
            if color == 'b':  # black, moving down
                score += (from_row - to_row) * 2  # Reward moving down
            else:  # white, moving up
                score += (to_row - from_row) * 2  # Reward moving up
            
            # Encourage moving toward center
            center_dist_before = abs(from_row - 3.5) + abs(from_col - 3.5)
            center_dist_after = abs(to_row - 3.5) + abs(to_col - 3.5)
            score += (center_dist_before - center_dist_after) * 0.5
            
            # Reward getting to king row
            if not is_king:
                if color == 'b' and to_row == 0:
                    score += 10
                elif color == 'w' and to_row == 7:
                    score += 10
            
            scored_moves.append((score, (from_row, from_col), (to_row, to_col)))
    
    # Evaluate moves for kings
    for piece_row, piece_col in my_kings:
        moves = get_moves(piece_row, piece_col, True)
        for move in moves:
            from_row, from_col, to_row, to_col, is_capture = move
            score = 0
            
            # Encourage moving toward center
            center_dist_before = abs(from_row - 3.5) + abs(from_col - 3.5)
            center_dist_after = abs(to_row - 3.5) + abs(to_col - 3.5)
            score += (center_dist_before - center_dist_after) * 0.5
            
            # Kings have high mobility, use them to control the board
            score += 1  # Small bonus for king movement
            
            scored_moves.append((score, (from_row, from_col), (to_row, to_col)))
    
    # Sort moves by score descending
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    
    # Return the highest scoring move
    if scored_moves:
        _, from_pos, to_pos = scored_moves[0]
        return (from_pos, to_pos)
    
    # Fallback: return any valid move
    for piece_row, piece_col in my_men:
        moves = get_moves(piece_row, piece_col, False)
        if moves:
            move = moves[0]
            return ((move[0], move[1]), (move[2], move[3]))
    
    for piece_row, piece_col in my_kings:
        moves = get_moves(piece_row, piece_col, True)
        if moves:
            move = moves[0]
            return ((move[0], move[1]), (move[2], move[3]))
    
    # Should not happen in a legal game state
    # But if we must return something, just return the first piece to itself
    if my_men:
        return (my_men[0], my_men[0])
    elif my_kings:
        return (my_kings[0], my_kings[0])
    else:
        # Should be impossible
        return ((0, 0), (0, 0))
