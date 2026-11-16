
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Identify all legal moves
    legal_moves = []
    
    # Check all horizontal edges (5 rows, 4 cols)
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
    
    # Check all vertical edges (4 rows, 5 cols)
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    
    # Filter moves that would complete a box (immediate capture)
    capture_moves = []
    for row, col, direction in legal_moves:
        if direction == 'H':
            # Complete box to the left or right
            if col - 1 >= 0:  # Left box
                left = (horizontal[row, col-1] != 0 and 
                       horizontal[row-1, col-1] != 0 and 
                       vertical[row, col-1] != 0)
            else:
                left = False
            if col + 1 < 4:  # Right box
                right = (horizontal[row, col+1] != 0 and 
                        horizontal[row+1, col+1] != 0 and 
                        vertical[row+1, col+1] != 0)
            else:
                right = False
            if left or right:
                capture_moves.append((row, col, 'H'))
        else:  # direction == 'V'
            # Complete box above or below
            if row - 1 >= 0:  # Above box
                above = (vertical[row-1, col] != 0 and 
                        horizontal[row-1, col] != 0 and 
                        horizontal[row-1, col+1] != 0)
            else:
                above = False
            if row + 1 < 4:  # Below box
                below = (vertical[row+1, col] != 0 and 
                        horizontal[row+1, col] != 0 and 
                        horizontal[row+1, col+1] != 0)
            else:
                below = False
            if above or below:
                capture_moves.append((row, col, 'V'))
    
    # Prefer capture moves if available
    if capture_moves:
        # Prefer moves that will not let the opponent capture multiple boxes
        # Avoid moves that result in a box with 3 sides already formed (opponent's chance to complete it)
        safe_capture_moves = []
        for row, col, direction in capture_moves:
            if direction == 'H':
                is_safe = True
                if col + 1 < 4:
                    # Check if right side of the next box would be 3-sided
                    if (horizontal[row, col+1] != 0 and 
                        horizontal[row+1, col+1] != 0 and 
                        vertical[row+1, col+1] != 0):
                        is_safe = False
                if row - 1 >= 0:
                    # Check if left side of the previous box would be 3-sided
                    if (horizontal[row-1, col] != 0 and 
                        horizontal[row-1, col+1] != 0 and 
                        vertical[row-1, col+1] != 0):
                        is_safe = False
                if is_safe:
                    safe_capture_moves.append((row, col, 'H'))
            else:  # direction == 'V'
                is_safe = True
                if row + 1 < 4:
                    # Check if bottom side of the next box would be 3-sided
                    if (vertical[row+1, col] != 0 and 
                        horizontal[row+1, col] != 0 and 
                        horizontal[row+1, col+1] != 0):
                        is_safe = False
                if col - 1 >= 0:
                    # Check if left side of the previous box would be 3-sided
                    if (vertical[row, col-1] != 0 and 
                        horizontal[row, col-1] != 0 and 
                        horizontal[row, col] != 0):
                        is_safe = False
                if is_safe:
                    safe_capture_moves.append((row, col, 'V'))
        
        # If there are safe capture moves, choose one at random
        if safe_capture_moves:
            choice = random.choice(safe_capture_moves)
            return f"{choice[0]},{choice[1]},{choice[2]}"
        else:
            # If no safe capture moves, just pick any
            choice = random.choice(capture_moves)
            return f"{choice[0]},{choice[1]},{choice[2]}"
    
    # If no capture moves, pick a safe move
    safe_moves = []
    for row, col, direction in legal_moves:
        if direction == 'H':
            # Skip corners
            if row == 0 and col == 0 or row == 0 and col == 3:
                continue
            # Don't allow a three-side box for the opponent
            # Check if the horizontal edge is already part of a near-complete box (3 sides filled)
            # This part can be expanded or refined for better evaluation
            safe_moves.append((row, col, 'H'))
        else:  # direction == 'V'
            # Skip corners
            if col == 0 and row == 0 or col == 4 and row == 0:
                continue
            safe_moves.append((row, col, 'V'))
    
    # If there are any safe moves
    if safe_moves:
        choice = random.choice(safe_moves)
        return f"{choice[0]},{choice[1]},{choice[2]}"
    
    # Fallback: pick any legal move
    choice = random.choice(legal_moves)
    return f"{choice[0]},{choice[1]},{choice[2]}"
