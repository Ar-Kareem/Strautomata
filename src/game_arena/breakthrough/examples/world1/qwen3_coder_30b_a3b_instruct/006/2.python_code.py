
import random
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Convert to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Determine direction: black moves down (decreasing row), white moves up (increasing row)
    direction = 1 if color == 'w' else -1
    
    # Helper function to check if a position is on the board
    def is_valid(row, col):
        return 0 <= row < 8 and 0 <= col < 8
    
    # Generate all legal moves for current player
    def generate_legal_moves():
        moves = []
        for (r, c) in me:
            # Move forward (one square)
            new_row = r + direction
            if is_valid(new_row, c) and (new_row, c) not in me_set and (new_row, c) not in opp_set:
                moves.append(((r, c), (new_row, c)))
                # Check if this move wins by reaching opponent home row
                if (color == 'w' and new_row == 7) or (color == 'b' and new_row == 0):
                    return moves  # Immediate win - return this move
            
            # Move diagonally forward to capture
            for dc in [-1, 1]:
                new_row = r + direction
                new_col = c + dc
                if is_valid(new_row, new_col) and (new_row, new_col) in opp_set:
                    moves.append(((r, c), (new_row, new_col)))
        
        return moves
    
    # Generate all legal moves for opponent (for checking win condition)
    def generate_opponent_moves():
        opp_moves = []
        opp_direction = -direction
        for (r, c) in opp:
            # Move forward
            new_row = r + opp_direction
            if is_valid(new_row, c) and (new_row, c) not in me_set and (new_row, c) not in opp_set:
                opp_moves.append(((r, c), (new_row, c)))
            # Move diagonally to capture
            for dc in [-1, 1]:
                new_row = r + opp_direction
                new_col = c + dc
                if is_valid(new_row, new_col) and (new_row, new_col) in me_set:
                    opp_moves.append(((r, c), (new_row, new_col)))
        return opp_moves
    
    # Check for immediate win conditions
    legal_moves = generate_legal_moves()
    
    # Check for captures that win
    for move in legal_moves:
        if move[1] in opp_set:
            # Can this capture win the game (remove all opponent pieces)?
            new_me = me_set.copy()
            new_opp = opp_set.copy()
            new_me.remove(move[0])
            new_me.add(move[1])
            new_opp.remove(move[1])
            if len(new_opp) == 0:
                return move
    
    # Check if any move brings us to home row (winning condition)
    for move in legal_moves:
        (from_row, from_col), (to_row, to_col) = move
        if (color == 'w' and to_row == 7) or (color == 'b' and to_row == 0):
            return move
    
    # If we have no winning move, prefer capturing moves first
    capture_moves = []
    non_capture_moves = []
    
    for move in legal_moves:
        if move[1] in opp_set:
            capture_moves.append(move)
        else:
            non_capture_moves.append(move)
    
    # Prefer captures if available
    if capture_moves:
        # Prefer captures that are safe and have best positional value
        best_move = max(capture_moves, key=lambda m: capture_value(m, me_set, opp_set, color))
        return best_move
    
    # If no captures, prefer moves with highest mobility
    if non_capture_moves:
        # Evaluate based on mobility (number of follow-up moves available)
        def move_mobility(move):
            (from_row, from_col), (to_row, to_col) = move
            count = 0
            # Check how many moves the new position could lead to
            for dc in [-1, 0, 1]:
                new_row = to_row + direction
                new_col = to_col + dc
                if is_valid(new_row, new_col):
                    if (new_row, new_col) not in me_set:
                        count += 1
            return count
        
        best_move = max(non_capture_moves, key=move_mobility)
        return best_move
    
    # Fallback: pick a random legal move if none found in above processing
    # This scenario shouldn't happen in normal gameplay
    return random.choice(legal_moves)

def capture_value(move, me_set, opp_set, color):
    """Assign a value to a capture move based on position and safety"""
    # Capturing is good, so give bonus to captures
    (from_row, from_col), (to_row, to_col) = move
    value = 10  # Base capture value
    
    # Prefer captures that move closer to opponent home row
    if color == 'w':
        value += (7 - to_row) * 2  # Move towards row 7
    else:
        value += to_row * 2  # Move towards row 0
    
    # Prefer captures that are less likely to be recaptured
    # If capture is from a more centralized position, it's safer
    value += 10 - abs(to_col - 3.5)  # Center position preferred
    
    return value
