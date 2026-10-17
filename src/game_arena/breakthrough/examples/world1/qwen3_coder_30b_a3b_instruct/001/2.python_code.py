
import numpy as np
from collections import defaultdict
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Convert to arrays for easier manipulation
    me_positions = np.array(me)
    opp_positions = np.array(opp)
    
    # Determine player colors and home rows
    if color == 'b':
        my_color = 'b'
        opp_color = 'w'
        my_home_row = 7
        opp_home_row = 0
    else:
        my_color = 'w'
        opp_color = 'b'
        my_home_row = 0
        opp_home_row = 7
        
    # Check for win conditions
    if len(opp_positions) == 0:
        # All opponent pieces captured - win!
        return get_best_move(me_positions, opp_positions, my_color, my_home_row, opp_home_row, True)
    
    # Check if we have any piece in opponent's home row
    if my_color == 'b':
        if np.any(me_positions[:, 0] == 7):
            # Win! We have a piece in opponent's home row
            return get_best_move(me_positions, opp_positions, my_color, my_home_row, opp_home_row, True)
    else:
        if np.any(me_positions[:, 0] == 0):
            # Win! We have a piece in opponent's home row
            return get_best_move(me_positions, opp_positions, my_color, my_home_row, opp_home_row, True)
    
    # Try to make a reasonable move with iterative deepening
    return get_best_move(me_positions, opp_positions, my_color, my_home_row, opp_home_row, False)

def get_best_move(me_positions, opp_positions, my_color, my_home_row, opp_home_row, force_win):
    # Try forced moves first (captures)
    captured_moves = []
    regular_moves = []
    
    # Generate all legal moves
    for pos in me_positions:
        row, col = pos
        if my_color == 'b':
            # Black pieces move upward (decreasing row)
            # Forward move
            if row > 0 and not any((row-1, col) == (r, c) for r, c in opp_positions):
                regular_moves.append(((row, col), (row-1, col)))
            # Diagonal captures to the left
            if row > 0 and col > 0 and any((row-1, col-1) == (r, c) for r, c in opp_positions):
                captured_moves.append(((row, col), (row-1, col-1)))
            # Diagonal captures to the right
            if row > 0 and col < 7 and any((row-1, col+1) == (r, c) for r, c in opp_positions):
                captured_moves.append(((row, col), (row-1, col+1)))
        else:
            # White pieces move downward (increasing row)
            # Forward move
            if row < 7 and not any((row+1, col) == (r, c) for r, c in opp_positions):
                regular_moves.append(((row, col), (row+1, col)))
            # Diagonal captures to the left
            if row < 7 and col > 0 and any((row+1, col-1) == (r, c) for r, c in opp_positions):
                captured_moves.append(((row, col), (row+1, col-1)))
            # Diagonal captures to the right
            if row < 7 and col < 7 and any((row+1, col+1) == (r, c) for r, c in opp_positions):
                captured_moves.append(((row, col), (row+1, col+1)))
    
    # If any captures are available, prefer them
    if captured_moves:
        # Prioritize captures that bring pieces closer to opponent home row
        best_capture = captured_moves[0]
        max_advancement = 0
        
        for from_pos, to_pos in captured_moves:
            advancement = get_advancement_distance(to_pos[0], my_color, opp_home_row)
            if advancement > max_advancement:
                max_advancement = advancement
                best_capture = (from_pos, to_pos)
                
        return best_capture
    
    # If no captures, choose best regular move
    if regular_moves:
        best_move = regular_moves[0]
        max_advancement = 0
        for from_pos, to_pos in regular_moves:
            advancement = get_advancement_distance(to_pos[0], my_color, opp_home_row)
            if advancement > max_advancement:
                max_advancement = advancement
                best_move = (from_pos, to_pos)
        return best_move
    
    # Fallback to any legal move
    # Generate all possible moves (even if they're not ideal)
    all_moves = []
    for pos in me_positions:
        row, col = pos
        if my_color == 'b':
            # Black pieces move upward (decreasing row)
            # Forward move
            if row > 0 and not any((row-1, col) == (r, c) for r, c in opp_positions):
                all_moves.append(((row, col), (row-1, col)))
            # Diagonal captures to the left
            if row > 0 and col > 0 and any((row-1, col-1) == (r, c) for r, c in opp_positions):
                all_moves.append(((row, col), (row-1, col-1)))
            # Diagonal captures to the right
            if row > 0 and col < 7 and any((row-1, col+1) == (r, c) for r, c in opp_positions):
                all_moves.append(((row, col), (row-1, col+1)))
        else:
            # White pieces move downward (increasing row)
            # Forward move
            if row < 7 and not any((row+1, col) == (r, c) for r, c in opp_positions):
                all_moves.append(((row, col), (row+1, col)))
            # Diagonal captures to the left
            if row < 7 and col > 0 and any((row+1, col-1) == (r, c) for r, c in opp_positions):
                all_moves.append(((row, col), (row+1, col-1)))
            # Diagonal captures to the right
            if row < 7 and col < 7 and any((row+1, col+1) == (r, c) for r, c in opp_positions):
                all_moves.append(((row, col), (row+1, col+1)))
    
    if all_moves:
        return all_moves[0]
        
    # If no moves available, return a dummy move (this shouldn't happen in valid games)
    return ((me_positions[0][0], me_positions[0][1]), (me_positions[0][0], me_positions[0][1]))

def get_advancement_distance(row, color, opp_home_row):
    """How much has a piece advanced?"""
    if color == 'b':
        # Black moves from bottom (row 7) towards top (row 0) 
        return 7 - row
    else:
        # White moves from top (row 0) towards bottom (row 7)
        return row
