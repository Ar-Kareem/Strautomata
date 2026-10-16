
import numpy as np

def policy(board):
    # Define the 8 queen directions: orthogonal and diagonal
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    # Find all your amazons (value 1)
    your_amazons = np.where(board == 1)
    your_amazons = list(zip(your_amazons[0], your_amazons[1]))
    
    # Collect all legal moves as tuples: (from_row, from_col, to_row, to_col, arrow_row, arrow_col)
    legal_moves = []
    
    # For each of your amazons
    for fr, fc in your_amazons:
        # Try moving in each direction
        for dr, dc in directions:
            # Try each possible step in this direction (1 to 5 squares, since board is 6x6)
            for step in range(1, 6):
                to_r, to_c = fr + dr * step, fc + dc * step
                
                # Check bounds
                if to_r < 0 or to_r >= 6 or to_c < 0 or to_c >= 6:
                    break  # Out of bounds, can't go further in this direction
                
                # Check if target square is empty (must be 0, not blocked or opponent)
                if board[to_r, to_c] != 0:
                    break  # Blocked by piece or arrow; can't jump over so stop here
                
                # Now simulate: amazon moves to (to_r, to_c), so (fr,fc) is now empty
                # We now shoot an arrow from (to_r, to_c) in any direction up to 5 steps
                
                # Try all 8 directions for the arrow
                for adr, adc in directions:
                    for arrow_step in range(1, 6):
                        ar, ac = to_r + adr * arrow_step, to_c + adc * arrow_step
                        
                        # Check bounds for arrow
                        if ar < 0 or ar >= 6 or ac < 0 or ac >= 6:
                            break  # Arrow out of bounds, stop in this direction
                        
                        # Arrow must land on empty square. Note: the old position (fr,fc) is now empty and can be passed through!
                        # So check if (ar, ac) is not occupied by any piece or existing arrow
                        if board[ar, ac] != 0:
                            # Stop in this direction if blocked (but NOT if it's the vacated square? 
                            # Wait: we are only checking the original board. But we are allowed to shoot through (fr,fc) if it's on the line!
                            # So we must check if (ar, ac) is blocked by ANY piece or arrow in the ORIGINAL board,
                            # EXCEPT we treat (fr, fc) as now empty. So if (ar, ac) is exactly (fr, fc), it's allowed.
                            if (ar, ac) == (fr, fc):
                                # This is allowed! The vacated square is no longer blocked.
                                legal_moves.append((fr, fc, to_r, to_c, ar, ac))
                            else:
                                # It's another blocked square, so arrow is blocked
                                break  # Stop in this direction
                        else:
                            # Empty square: valid arrow shot
                            legal_moves.append((fr, fc, to_r, to_c, ar, ac))
    
    # We must return a legal move. If for any reason we have none, we have a fallback (but problem states it won't happen)
    if not legal_moves:
        # Fallback: try to find any move that satisfies the minimal constraint as a last resort
        # This should never occur per problem statement, but we must return something
        for fr, fc in your_amazons:
            for dr, dc in directions:
                for step in range(1, 6):
                    to_r, to_c = fr + dr * step, fc + dc * step
                    if 0 <= to_r < 6 and 0 <= to_c < 6 and board[to_r, to_c] == 0:
                        # Use first arrow shot possible: try moving one square and arrow one square in same direction
                        ar, ac = to_r + dr, to_c + dc
                        if 0 <= ar < 6 and 0 <= ac < 6 and board[ar, ac] == 0:
                            return f"{fr},{fc}:{to_r},{to_c}:{ar},{ac}"
        # If still nothing, pick an arbitrary move (shouldn't happen)
        return "0,0:0,1:0,2"
    
    # For simplicity, return the first legal move. More sophisticated policies could score moves,
    # but since we must always return a legal move and time is limited, first is safe and correct.
    fr, fc, to_r, to_c, ar, ac = legal_moves[0]
    return f"{fr},{fc}:{to_r},{to_c}:{ar},{ac}"
