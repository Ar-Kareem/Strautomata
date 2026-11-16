
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Initialize variables to track the potential moves
    potential_moves = []
    
    # Check all possible moves in the 4x4 grid (resulting in a 5x5 grid for edges)
    for row in range(5):
        for col in range(5):
            # Horizontal move
            if row < 4 and horizontal[row, col] == 0:  # ensure within bounds
                # Check if this move completes any boxes
                if (capture[row, col] == 0 and 
                    (row > 0 and capture[row-1, col] == 1 and horizontal[row-1, col] == 1 and vertical[row-1, col] == 1) and 
                    (row < 4 and horizontal[row, col] == 0 and vertical[row, col] == 1)):
                    # This move completes a box
                    potential_moves.append((row, col, 'H'))
                    
            # Vertical move
            if col < 4 and vertical[row, col] == 0:  # ensure within bounds
                # Check if this move completes any boxes
                if (capture[row, col] == 0 and 
                    (col > 0 and capture[row, col-1] == 1 and horizontal[row, col-1] == 1 and vertical[row, col-1] == 1) and 
                    (col < 4 and capture[row, col+1] == 1 and horizontal[row, col] == 1 and vertical[row, col] == 0)):
                    # This move completes a box
                    potential_moves.append((row, col, 'V'))

    # If any moves can capture a box, prioritize those
    if potential_moves:
        chosen_move = potential_moves[0]
        return f"{chosen_move[0]},{chosen_move[1]},{chosen_move[2]}"

    # If no moves capture, find a safe legal move
    for row in range(5):
        for col in range(5):
            if row < 4 and horizontal[row, col] == 0:
                # Check if this is a safe move (not creating a three-sided box)
                if not (row > 0 and horizontal[row-1, col] == 1 and 
                        vertical[row-1, col] == 1 and vertical[row, col] == 1):
                    return f"{row},{col},H"
            if col < 4 and vertical[row, col] == 0:
                # Check if this is a safe move (not creating a three-sided box)
                if not (col > 0 and horizontal[row, col-1] == 1 and 
                        vertical[row, col-1] == 1 and horizontal[row, col] == 1):
                    return f"{row},{col},V"
    
    # Fallback: If absolutely no moves found, return a default safe move
    return "0,0,H"  # This should never be reached if the game is played correctly

