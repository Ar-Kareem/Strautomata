
import numpy as np
import random

def get_all_legal_moves(horizontal, vertical, capture):
    moves = []
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                moves.append(f"{r},{c},H")
            if vertical[r, c] == 0:
                moves.append(f"{r},{c},V")
    return moves

def does_move_capture(horizontal, vertical, capture, move):
    parts = move.split(',')
    r, c, dir_ = int(parts[0]), int(parts[1]), parts[2]
    captured = False
    if dir_ == 'H':
        # Check affected boxes
        if r < 4:
            # Box (r, c): horiz r,c, horiz r+1,c, vert r,c, vert r,c+1
            if (horizontal[r+1, c] != 0 and vertical[r, c] != 0 and vertical[r, c+1] != 0 and capture[r, c] == 0):
                captured = True
        if r > 0:
            # Box (r-1, c): horiz r-1,c, horiz r,c, vert r-1,c, vert r-1,c+1
            if (horizontal[r-1, c] != 0 and vertical[r-1, c] != 0 and vertical[r-1, c+1] != 0 and capture[r-1, c] == 0):
                captured = True
    elif dir_ == 'V':
        # Check affected boxes
        if c < 4:
            # Box (r, c): horiz r,c, horiz r+1,c, vert r,c, vert r,c+1
            if (horizontal[r, c] != 0 and horizontal[r+1, c] != 0 and vertical[r, c+1] != 0 and capture[r, c] == 0):
                captured = True
        if c > 0:
            # Box (r, c-1): horiz r,c-1, horiz r+1,c-1, vert r,c-1, vert r,c
            if (horizontal[r, c-1] != 0 and horizontal[r+1, c-1] != 0 and vertical[r, c-1] != 0 and capture[r, c-1] == 0):
                captured = True
    return captured

def is_threatening(horizontal, vertical, capture, move):
    # Simulate the move and check for any box with exactly 3 sides
    parts = move.split(',')
    r, c, dir_ = int(parts[0]), int(parts[1]), parts[2]
    temp_h = horizontal.copy()
    temp_v = vertical.copy()
    if dir_ == 'H':
        temp_h[r, c] = 1
    else:
        temp_v[r, c] = 1
    # Check each box
    for i in range(4):
        for j in range(4):
            sides = 0
            if temp_h[i, j] != 0: sides += 1  # bottom
            if temp_h[i+1, j] != 0: sides += 1  # top
            if temp_v[i, j] != 0: sides += 1  # left
            if temp_v[i, j+1] != 0: sides += 1  # right
            if sides == 3:
                return True
    return False

def count_box_sides_influenced(horizontal, vertical, capture, move):
    # Count boxes influenced (potential threat metric)
    parts = move.split(',')
    r, c, dir_ = int(parts[0]), int(parts[1]), parts[2]
    temp_h = horizontal.copy()
    temp_v = vertical.copy()
    if dir_ == 'H':
        temp_h[r, c] = 1
    else:
        temp_v[r, c] = 1
    influenced = 0
    for i in range(4):
        for j in range(4):
            if (i == r and j == c) or (dir_ == 'V' and i == r and j == c-1) or (dir_ == 'H' and i == r-1 and j == c) or (dir_ == 'H' and i == r and j == c):
                sides = 0
                if temp_h[i, j] != 0: sides += 1
                if temp_h[i+1, j] != 0: sides += 1
                if temp_v[i, j] != 0: sides += 1
                if temp_v[i, j+1] != 0: sides += 1
                if sides >= 3:  # Could lead to threats or captures later
                    influenced += 1
    return influenced

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    legal_moves = get_all_legal_moves(horizontal, vertical, capture)
    if not legal_moves:
        raise ValueError("No legal moves available")  # Should not happen
    
    # Prioritize captures
    capturing_moves = [m for m in legal_moves if does_move_capture(horizontal, vertical, capture, m)]
    if capturing_moves:
        return random.choice(capturing_moves)
    
    # Else, prefer safe moves (no threats)
    safe_moves = [m for m in legal_moves if not is_threatening(horizontal, vertical, capture, m)]
    if safe_moves:
        return random.choice(safe_moves)
    
    # Else, defensive: choose move influencing fewest high-side boxes
    def sort_key(m):
        return (count_box_sides_influenced(horizontal, vertical, capture, m), random.random())  # Tiebreak randomly
    legal_moves.sort(key=sort_key)
    return legal_moves[0]
