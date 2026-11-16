
def policy(my_men, my_kings, opp_men, opp_kings, color):
    directions = []
    
    if color == 'b':  # Black moves down
        directions = [(-1, -1), (-1, 1)]  # Down-left, Down-right
    else:  # White moves up
        directions = [(1, -1), (1, 1)]  # Up-left, Up-right
    
    all_pieces = my_men + my_kings
    
    def is_valid_square(row, col):
        return 0 <= row < 8 and 0 <= col < 8 and (row + col) % 2 == 1
    
    def get_captures(pos):
        captures = []
        for dr, dc in directions:
            # Possible capture square
            jump_row = pos[0] + 2 * dr
            jump_col = pos[1] + 2 * dc
            # Landing (jumping over an opponent piece)
            mid_row = pos[0] + dr
            mid_col = pos[1] + dc
            
            if is_valid_square(jump_row, jump_col):
                if (mid_row, mid_col) in opp_men or (mid_row, mid_col) in opp_kings:
                    captures.append(((pos[0], pos[1]), (jump_row, jump_col)))
        
        return captures
    
    def get_moves(pos):
        moves = []
        for dr, dc in directions:
            new_row = pos[0] + dr
            new_col = pos[1] + dc
            if is_valid_square(new_row, new_col) and (new_row, new_col) not in all_pieces:
                moves.append(((pos[0], pos[1]), (new_row, new_col)))
        return moves
    
    best_capture = None
    all_captures = []
    
    # Gather all available captures
    for piece in all_pieces:
        all_captures.extend(get_captures(piece))
    
    if all_captures:
        # Prioritize the first capture available
        best_capture = all_captures[0]
    
    if best_capture:
        return best_capture
    
    # If no captures are available, consider normal moves
    all_moves = []
    for piece in all_pieces:
        all_moves.extend(get_moves(piece))
    
    if all_moves:
        # Return the first available move (could be improved by evaluating board state)
        return all_moves[0]
    
    # Fallback (should not happen in a valid game state)
    return None
