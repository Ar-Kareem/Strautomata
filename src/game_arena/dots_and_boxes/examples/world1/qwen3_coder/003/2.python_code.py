
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # First, look for immediate captures (boxes with 3 sides already filled)
    for row in range(4):
        for col in range(4):
            # If box is not yet captured
            if capture[row, col] == 0:
                sides_filled = 0
                sides = []
                
                # Check top edge
                if horizontal[row, col] != 0:
                    sides_filled += 1
                else:
                    sides.append((row, col, 'H'))
                
                # Check bottom edge
                if horizontal[row + 1, col] != 0:
                    sides_filled += 1
                else:
                    sides.append((row + 1, col, 'H'))
                
                # Check left edge
                if vertical[row, col] != 0:
                    sides_filled += 1
                else:
                    sides.append((row, col, 'V'))
                
                # Check right edge
                if vertical[row, col + 1] != 0:
                    sides_filled += 1
                else:
                    sides.append((row, col + 1, 'V'))
                
                # If 3 sides are filled, we can capture this box
                if sides_filled == 3 and len(sides) == 1:
                    r, c, d = sides[0]
                    return f"{r},{c},{d}"
    
    # No immediate captures, so avoid creating 3-sided boxes for opponent
    # Look for moves that don't create vulnerable boxes
    safe_moves = []
    neutral_moves = []
    
    # Check all possible horizontal moves
    for row in range(5):
        for col in range(4):  # Only 4 horizontal edges per row
            if horizontal[row, col] == 0:  # Edge is available
                move = (row, col, 'H')
                creates_vulnerable = False
                
                # Check if this move would create a box with 3 sides
                # Check box above (if exists)
                if 0 <= row - 1 < 4:
                    if is_vulnerable_box(row - 1, col, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                # Check box below (if exists)
                if 0 <= row < 4:
                    if is_vulnerable_box(row, col, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                if not creates_vulnerable:
                    safe_moves.append(move)
                else:
                    neutral_moves.append(move)
    
    # Check all possible vertical moves
    for row in range(4):  # Only 4 vertical edges per column
        for col in range(5):
            if vertical[row, col] == 0:  # Edge is available
                move = (row, col, 'V')
                creates_vulnerable = False
                
                # Check if this move would create a box with 3 sides
                # Check box to the left (if exists)
                if 0 <= col - 1 < 4:
                    if is_vulnerable_box(row, col - 1, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                # Check box to the right (if exists)
                if 0 <= col < 4:
                    if is_vulnerable_box(row, col, horizontal, vertical, capture):
                        creates_vulnerable = True
                
                if not creates_vulnerable:
                    safe_moves.append(move)
                else:
                    neutral_moves.append(move)
    
    # Choose a move
    if safe_moves:
        # Randomly choose from safe moves
        chosen_move = safe_moves[0]
        return f"{chosen_move[0]},{chosen_move[1]},{chosen_move[2]}"
    elif neutral_moves:
        # Randomly choose from neutral moves
        chosen_move = neutral_moves[0]
        return f"{chosen_move[0]},{chosen_move[1]},{chosen_move[2]}"
    else:
        # Fallback: find any legal move
        # Check horizontal edges
        for row in range(5):
            for col in range(4):
                if horizontal[row, col] == 0:
                    return f"{row},{col},H"
        
        # Check vertical edges
        for row in range(4):
            for col in range(5):
                if vertical[row, col] == 0:
                    return f"{row},{col},V"
    
    # Should never reach here if there are legal moves
    return "0,0,H"

def is_vulnerable_box(box_row, box_col, horizontal, vertical, capture):
    """Check if a box would have 3 sides filled after a move"""
    # If box is already captured, it's not vulnerable
    if capture[box_row, box_col] != 0:
        return False
    
    # Count how many sides are already filled
    sides_filled = 0
    
    # Top edge
    if horizontal[box_row, box_col] != 0:
        sides_filled += 1
    
    # Bottom edge
    if horizontal[box_row + 1, box_col] != 0:
        sides_filled += 1
    
    # Left edge
    if vertical[box_row, box_col] != 0:
        sides_filled += 1
    
    # Right edge
    if vertical[box_row, box_col + 1] != 0:
        sides_filled += 1
    
    # If exactly 3 sides are filled, the box is vulnerable
    return sides_filled == 3
