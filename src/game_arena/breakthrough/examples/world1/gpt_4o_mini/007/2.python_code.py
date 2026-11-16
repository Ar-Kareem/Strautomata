
def policy(me, opp, color):
    directions = {
        'b': [(1, 0), (1, -1), (1, 1)],  # black moves down
        'w': [(-1, 0), (-1, -1), (-1, 1)]  # white moves up
    }
    
    possible_moves = []
    
    # Create a set for faster look-up of opponent positions
    opp_set = set(opp)
    
    for (from_row, from_col) in me:
        for dr, dc in directions[color]:
            to_row = from_row + dr
            to_col = from_col + dc
            
            # Check if the move is within bounds
            if 0 <= to_row < 8 and 0 <= to_col < 8:
                if (to_row, to_col) in opp_set:
                    # Capture move
                    possible_moves.append(((from_row, from_col), (to_row, to_col)))
                elif (to_row, to_col) not in me:
                    # Move to empty space
                    possible_moves.append(((from_row, from_col), (to_row, to_col)))

    # Prioritize capturing moves over advancing
    capturing_moves = [move for move in possible_moves if move[1] in opp_set]
    if capturing_moves:
        # Return the first capturing move found
        return capturing_moves[0]
    
    # If there are no capturing moves, return the first legal move found
    if possible_moves:
        return possible_moves[0]
    
    # If no moves are possible (shouldn't happen in a legal game), return None
    return None
