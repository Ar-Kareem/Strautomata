
import numpy as np
from collections import defaultdict

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # First, check for any available boxes we can complete (chain capture)
    move = find_capture_move(horizontal, vertical)
    if move:
        return move
    
    # Collect all possible legal moves and evaluate them
    legal_moves = get_legal_moves(horizontal, vertical)
    
    # Remove moves that would give opponent an immediate box
    safe_moves = []
    for move in legal_moves:
        if not would_give_box(move, horizontal, vertical):
            safe_moves.append(move)
    
    # If there are safe moves, evaluate them, otherwise choose any legal move
    if safe_moves:
        move_scores = []
        for move in safe_moves:
            temp_h = horizontal.copy()
            temp_v = vertical.copy()
            temp_c = capture.copy()
            row, col, dir = parse_move(move)
            if dir == 'H':
                temp_h[row, col] = 1
            else:
                temp_v[row, col] = 1
            
            # Simple evaluation: prioritize center moves and creating chains
            center_score = 4 - (abs(row - 2) + abs(col - 2))
            threat_score = count_potential_threats(row, col, dir, temp_h, temp_v)
            move_scores.append((center_score + threat_score * 0.5, move))
        
        # Sort by score and pick the best
        move_scores.sort(reverse=True, key=lambda x: x[0])
        return move_scores[0][1]
    elif legal_moves:
        # If no safe moves, choose one that creates the fewest immediate threats
        threat_counts = []
        for move in legal_moves:
            temp_h = horizontal.copy()
            temp_v = vertical.copy()
            threat_counts.append((count_created_threats(move, temp_h, temp_v), move))
        threat_counts.sort(key=lambda x: x[0])
        return threat_counts[0][1]
    
    # Fallback (shouldn't happen if game isn't over)
    return "0,0,H"

def parse_move(move_str):
    parts = move_str.split(',')
    return int(parts[0]), int(parts[1]), parts[2]

def find_capture_move(horizontal, vertical):
    # Check all possible moves to see if they complete a box
    for row in range(5):
        for col in range(5):
            # Check horizontal moves
            if horizontal[row, col] == 0:
                # Check if completing a box to the top or bottom
                if row > 0 and (vertical[row-1, col] != 0 and horizontal[row-1, col] != 0 and vertical[row-1, col+1] != 0):
                    return f"{row},{col},H"
                if row < 4 and (vertical[row, col] != 0 and horizontal[row+1, col] != 0 and vertical[row, col+1] != 0):
                    return f"{row},{col},H"
            
            # Check vertical moves
            if vertical[row, col] == 0:
                # Check if completing a box to the left or right
                if col > 0 and (horizontal[row, col-1] != 0 and vertical[row, col-1] != 0 and horizontal[row+1, col-1] != 0):
                    return f"{row},{col},V"
                if col < 4 and (horizontal[row, col] != 0 and vertical[row, col+1] != 0 and horizontal[row+1, col] != 0):
                    return f"{row},{col},V"
    return None

def get_legal_moves(horizontal, vertical):
    moves = []
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                moves.append(f"{row},{col},H")
            if vertical[row, col] == 0:
                moves.append(f"{row},{col},V")
    return moves

def would_give_box(move, horizontal, vertical):
    row, col, dir = parse_move(move)
    if dir == 'H':
        # Check box above
        if row > 0:
            sides = 0
            sides += horizontal[row-1, col] != 0  # top horizontal
            sides += vertical[row-1, col] != 0    # left vertical
            sides += vertical[row-1, col+1] != 0  # right vertical
            if sides >= 2:
                return True
        # Check box below
        if row < 4:
            sides = 0
            sides += horizontal[row+1, col] != 0  # bottom horizontal
            sides += vertical[row, col] != 0      # left vertical
            sides += vertical[row, col+1] != 0    # right vertical
            if sides >= 2:
                return True
    else:  # V
        # Check box to left
        if col > 0:
            sides = 0
            sides += vertical[row, col-1] != 0    # left vertical
            sides += horizontal[row, col-1] != 0  # top horizontal
            sides += horizontal[row+1, col-1] != 0 # bottom horizontal
            if sides >= 2:
                return True
        # Check box to right
        if col < 4:
            sides = 0
            sides += vertical[row, col+1] != 0    # right vertical
            sides += horizontal[row, col] != 0    # top horizontal
            sides += horizontal[row+1, col] != 0  # bottom horizontal
            if sides >= 2:
                return True
    return False

def count_potential_threats(row, col, dir, horizontal, vertical):
    count = 0
    if dir == 'H':
        # Horizontal edges can threaten two boxes (top and bottom)
        if row > 0:
            if (horizontal[row-1, col] != 0) + (vertical[row-1, col] != 0) + (vertical[row-1, col+1] != 0) == 2:
                count += 1
        if row < 4:
            if (horizontal[row+1, col] != 0) + (vertical[row, col] != 0) + (vertical[row, col+1] != 0) == 2:
                count += 1
    else:  # V
        # Vertical edges can threaten two boxes (left and right)
        if col > 0:
            if (vertical[row, col-1] != 0) + (horizontal[row, col-1] != 0) + (horizontal[row+1, col-1] != 0) == 2:
                count += 1
        if col < 4:
            if (vertical[row, col+1] != 0) + (horizontal[row, col] != 0) + (horizontal[row+1, col] != 0) == 2:
                count += 1
    return count

def count_created_threats(move, horizontal, vertical):
    row, col, dir = parse_move(move)
    if dir == 'H':
        horizontal[row, col] = 1
    else:
        vertical[row, col] = 1
    
    threats = 0
    # Count number of boxes that would be 3-sided after this move
    for r in range(4):
        for c in range(4):
            sides = 0
            sides += horizontal[r, c] != 0   # top
            sides += horizontal[r+1, c] != 0 # bottom
            sides += vertical[r, c] != 0     # left
            sides += vertical[r, c+1] != 0   # right
            if sides == 3:
                threats += 1
    return threats
