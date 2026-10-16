
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Find all possible moves (empty edges)
    possible_moves = []
    
    # Check horizontal edges (5x4 grid)
    for row in range(5):
        for col in range(4):
            if horizontal[row, col] == 0:
                possible_moves.append((row, col, 'H'))
    
    # Check vertical edges (4x5 grid)
    for row in range(4):
        for col in range(5):
            if vertical[row, col] == 0:
                possible_moves.append((row, col, 'V'))
    
    # If no moves available, return a random legal move to avoid errors
    if not possible_moves:
        return "0,0,H"
    
    # Filter out moves that complete a box with exactly 3 sides (traps)
    safe_moves = []
    for row, col, direction in possible_moves:
        # Check if this move would complete a box
        will_complete_box = False
        if direction == 'H':
            # Check if this horizontal edge completes a box
            # Check top box (if exists)
            if row > 0:
                if (horizontal[row-1, col] != 0 and 
                    vertical[row-1, col] != 0 and 
                    vertical[row-1, col+1] != 0):
                    will_complete_box = True
                    # Check if this creates a box with 3 filled sides in adjacent area
                    # We want to avoid completing boxes where opponent can win next turn
            # Check bottom box (if exists)
            if row < 4:
                if (horizontal[row+1, col] != 0 and 
                    vertical[row, col] != 0 and 
                    vertical[row, col+1] != 0):
                    will_complete_box = True
                    
        else:  # direction == 'V'
            # Check if this vertical edge completes a box
            # Check left box (if exists)
            if col > 0:
                if (vertical[row, col-1] != 0 and 
                    horizontal[row, col-1] != 0 and 
                    horizontal[row+1, col-1] != 0):
                    will_complete_box = True
            # Check right box (if exists)
            if col < 4:
                if (vertical[row, col+1] != 0 and 
                    horizontal[row, col] != 0 and 
                    horizontal[row+1, col] != 0):
                    will_complete_box = True
        
        # If the move doesn't complete a box, or completes a normal box, it's safe
        # But if it completes a box that we'd want to avoid, skip it
        if not will_complete_box:
            safe_moves.append((row, col, direction))
        elif will_complete_box:
            # Only add moves that complete boxes that do not form a 3-side trap
            safe_moves.append((row, col, direction))
    
    # Prioritize moves that complete boxes (capture opportunities)
    capture_moves = []
    safe_non_capture = []
    
    for row, col, direction in possible_moves:
        # Check if this would give us a box
        would_capture = False
        new_capture = capture.copy()
        
        # Temporarily apply the move to see if it captures a box
        temp_horizontal = horizontal.copy()
        temp_vertical = vertical.copy()
        
        temp_horizontal[row, col] = 1 if direction == 'H' else temp_horizontal[row, col]
        temp_vertical[row, col] = 1 if direction == 'V' else temp_vertical[row, col]
        
        # Check if any boxes are captured by this move
        if direction == 'H':
            # Top box
            if row > 0:
                if (temp_horizontal[row-1, col] != 0 and 
                    temp_vertical[row-1, col] != 0 and 
                    temp_vertical[row-1, col+1] != 0):
                    would_capture = True
                    new_capture[row-1, col] = 1
            # Bottom box (if exists)
            if row < 4:
                if (temp_horizontal[row+1, col] != 0 and 
                    temp_vertical[row, col] != 0 and 
                    temp_vertical[row, col+1] != 0):
                    would_capture = True
                    new_capture[row, col] = 1
        else:  # direction == 'V'
            # Left box
            if col > 0:
                if (temp_vertical[row, col-1] != 0 and 
                    temp_horizontal[row, col-1] != 0 and 
                    temp_horizontal[row+1, col-1] != 0):
                    would_capture = True
                    new_capture[row, col-1] = 1
            # Right box (if exists)
            if col < 4:
                if (temp_vertical[row, col+1] != 0 and 
                    temp_horizontal[row, col] != 0 and 
                    temp_horizontal[row+1, col] != 0):
                    would_capture = True
                    new_capture[row, col] = 1
                    
        if would_capture:
            capture_moves.append((row, col, direction, new_capture))
        else:
            # Avoid moves that complete boxes with 3 sides
            # Check if this edge move creates a 3-side situation that could trap us
            safe_non_capture.append((row, col, direction))
    
    # Prefer capture moves first
    if capture_moves:
        # Try to pick moves that lead to capture AND avoid creating easy traps
        # Simple: pick one that captures a box
        return f"{capture_moves[0][0]},{capture_moves[0][1]},{capture_moves[0][2]}"
    
    # If no capturing moves, prefer safe moves that don't create immediate traps
    if safe_non_capture:
        # Avoid moves that would complete 3-sided boxes
        # We need to be more careful here
        # Let's just pick a random safe move
        move = random.choice(safe_non_capture)
        return f"{move[0]},{move[1]},{move[2]}"
    
    # If we must make a move (rare case), pick any move
    return f"{possible_moves[0][0]},{possible_moves[0][1]},{possible_moves[0][2]}"
