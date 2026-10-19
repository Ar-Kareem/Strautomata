
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Get all legal moves
    legal_moves = []
    for row in range(5):
        for col in range(5):
            # Check horizontal edges
            if row < 4 and horizontal[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            # Check vertical edges
            if col < 4 and vertical[row, col] == 0:
                legal_moves.append((row, col, 'V'))
    
    # If no legal moves, return a dummy move (shouldn't happen in valid state)
    if not legal_moves:
        return "0,0,H"
    
    # Try to find immediate capture moves first (complete a box)
    capture_moves = []
    for row, col, direction in legal_moves:
        # Simulate drawing the edge to see if it captures boxes
        temp_horizontal = horizontal.copy()
        temp_vertical = vertical.copy()
        temp_capture = capture.copy()
        
        # Mark the edge as drawn
        if direction == 'H':
            temp_horizontal[row, col] = 1
        else:  # direction == 'V'
            temp_vertical[row, col] = 1
        
        # Check if this move captures any boxes
        captured = False
        # Check boxes that would be affected by this edge
        if direction == 'H':
            # Horizontal edge affects boxes above and below
            if row > 0:  # Check box above
                if (temp_horizontal[row-1, col] != 0 and 
                    temp_horizontal[row, col] != 0 and 
                    temp_vertical[row-1, col] != 0 and 
                    temp_vertical[row-1, col+1] != 0):
                    temp_capture[row-1, col] = 1
                    captured = True
            if row < 4:  # Check box below
                if (temp_horizontal[row, col] != 0 and 
                    temp_horizontal[row+1, col] != 0 and 
                    temp_vertical[row, col] != 0 and 
                    temp_vertical[row, col+1] != 0):
                    temp_capture[row, col] = 1
                    captured = True
        else:  # direction == 'V'
            # Vertical edge affects boxes left and right
            if col > 0:  # Check box to the left
                if (temp_vertical[row, col-1] != 0 and 
                    temp_vertical[row, col] != 0 and 
                    temp_horizontal[row, col-1] != 0 and 
                    temp_horizontal[row+1, col-1] != 0):
                    temp_capture[row, col-1] = 1
                    captured = True
            if col < 4:  # Check box to the right
                if (temp_vertical[row, col] != 0 and 
                    temp_vertical[row, col+1] != 0 and 
                    temp_horizontal[row, col] != 0 and 
                    temp_horizontal[row+1, col] != 0):
                    temp_capture[row, col] = 1
                    captured = True
        
        # If this move captures at least one box, consider it a capture move
        if captured:
            capture_moves.append((row, col, direction))
    
    # If we have capture moves, prefer the ones that capture the most boxes
    if capture_moves:
        # Prioritize moves that capture more boxes
        return f"{capture_moves[0][0]},{capture_moves[0][1]},{capture_moves[0][2]}"
    
    # If no capture moves, avoid creating 3-sided boxes for opponent
    # Check for moves that could give opponent a 3-sided box
    safe_moves = []
    for row, col, direction in legal_moves:
        # Make a temporary copy of the game state
        temp_horizontal = horizontal.copy()
        temp_vertical = vertical.copy()
        
        # Mark the edge as drawn temporarily
        if direction == 'H':
            temp_horizontal[row, col] = 1
        else:  # direction == 'V'
            temp_vertical[row, col] = 1
        
        # Check if this creates a 3-sided box for opponent
        unsafe = False
        if direction == 'H':
            # Check boxes above and below
            for box_row, box_col in [(row-1, col), (row, col)]:
                if 0 <= box_row < 4 and 0 <= box_col < 4:
                    # Check if this box would have 3 sides completed (and it's not captured)
                    sides = 0
                    if temp_horizontal[box_row, box_col] != 0:
                        sides += 1
                    if temp_horizontal[box_row+1, box_col] != 0:
                        sides += 1
                    if temp_vertical[box_row, box_col] != 0:
                        sides += 1
                    if temp_vertical[box_row, box_col+1] != 0:
                        sides += 1
                    
                    # Check if 3 sides and not already captured by us
                    if sides == 3:
                        unsafe = True
                        break
        else:  # direction == 'V'
            # Check boxes to left and right
            for box_row, box_col in [(row, col-1), (row, col)]:
                if 0 <= box_row < 4 and 0 <= box_col < 4:
                    # Check if this box would have 3 sides completed
                    sides = 0
                    if temp_horizontal[box_row, box_col] != 0:
                        sides += 1
                    if temp_horizontal[box_row+1, box_col] != 0:
                        sides += 1
                    if temp_vertical[box_row, box_col] != 0:
                        sides += 1
                    if temp_vertical[box_row, box_col+1] != 0:
                        sides += 1
                    
                    # Check if 3 sides and not already captured by us
                    if sides == 3:
                        unsafe = True
                        break
        
        if not unsafe:
            safe_moves.append((row, col, direction))
    
    # Prefer safe moves
    if safe_moves:
        return f"{safe_moves[0][0]},{safe_moves[0][1]},{safe_moves[0][2]}"
    
    # If all moves create a 3-sided box for opponent, pick a random legal one
    chosen_move = random.choice(legal_moves)
    return f"{chosen_move[0]},{chosen_move[1]},{chosen_move[2]}"
