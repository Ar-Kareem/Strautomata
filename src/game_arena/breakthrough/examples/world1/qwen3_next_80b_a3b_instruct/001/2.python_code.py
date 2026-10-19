
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert lists to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Determine direction and home row based on color
    if color == 'b':
        # Black moves downward (decreasing row index: 7->6->...->0)
        direction = -1
        home_row = 0  # Black wins by reaching row 0
    else:  # color == 'w'
        # White moves upward (increasing row index: 0->1->...->7)
        direction = 1
        home_row = 7  # White wins by reaching row 7
    
    # List of all possible moves
    possible_moves = []
    
    # For each of my pieces, check possible moves
    for r, c in me:
        # Forward straight move
        new_r = r + direction
        new_c = c
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            if (new_r, new_c) not in me_set and (new_r, new_c) not in opp_set:
                # Straight move to empty square
                possible_moves.append(((r, c), (new_r, new_c)))
        
        # Forward diagonal moves (left and right)
        for dc in [-1, 1]:
            new_r = r + direction
            new_c = c + dc
            if 0 <= new_r <= 7 and 0 <= new_c <= 7:
                if (new_r, new_c) in opp_set:
                    # Capture move
                    possible_moves.append(((r, c), (new_r, new_c)))
                elif (new_r, new_c) not in me_set:
                    # Diagonal move to empty square
                    possible_moves.append(((r, c), (new_r, new_c)))
    
    # If no moves available, return arbitrary (but should not happen in valid game state)
    if not possible_moves:
        # Fallback: should not occur per problem constraints
        return ((me[0][0], me[0][1]), (me[0][0], me[0][1]))
    
    # Prioritize winning moves
    winning_moves = [move for move in possible_moves if move[1][0] == home_row]
    if winning_moves:
        return winning_moves[0]
    
    # Prioritize capture moves
    capture_moves = [move for move in possible_moves if move[1] in opp_set]
    if capture_moves:
        # Among captures, prefer the one that gets us closer to home row
        # For black (direction=-1), lower row is better → pick the move with smallest new_r
        # For white (direction=1), higher row is better → pick the move with largest new_r
        if color == 'b':
            # Black: want to minimize row number
            best_capture = min(capture_moves, key=lambda x: x[1][0])
        else:
            # White: want to maximize row number
            best_capture = max(capture_moves, key=lambda x: x[1][0])
        return best_capture
    
    # If no captures, prioritize forward progress
    forward_moves = [move for move in possible_moves if move[1][1] == move[0][1]]  # straight forward
    diagonal_moves = [move for move in possible_moves if move[1][1] != move[0][1]]  # diagonal forward
    
    # Prefer straight forward moves over diagonal (generally safer)
    if forward_moves:
        # Among forward moves, pick the one that moves the most toward home row
        if color == 'b':
            best_forward = min(forward_moves, key=lambda x: x[1][0])
        else:
            best_forward = max(forward_moves, key=lambda x: x[1][0])
        return best_forward
    
    # If no straight, use diagonal
    if diagonal_moves:
        if color == 'b':
            best_diagonal = min(diagonal_moves, key=lambda x: x[1][0])
        else:
            best_diagonal = max(diagonal_moves, key=lambda x: x[1][0])
        return best_diagonal
    
    # Fallback: any legal move (should not reach here due to above logic)
    return possible_moves[0]
