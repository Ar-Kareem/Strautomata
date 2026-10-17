
import numpy as np

def is_capture(horizontal, vertical, capture, row, col, direction):
    if direction == 'H':
        # Checking if drawing the horizontal edge hits a box
        if row > 0 and horizontal[row-1, col] == 0 and vertical[row-1, col] == 1 and vertical[row-1, col+1] == 1:
            return True
        if row < 4 and horizontal[row, col] == 0 and vertical[row, col] == 1 and vertical[row, col+1] == 1:
            return True
    elif direction == 'V':
        # Checking if drawing the vertical edge hits a box
        if col > 0 and vertical[row, col-1] == 0 and horizontal[row, col-1] == 1 and horizontal[row+1, col-1] == 1:
            return True
        if col < 4 and vertical[row, col] == 0 and horizontal[row, col] == 1 and horizontal[row+1, col] == 1:
            return True
    return False

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    moves = []
    
    # Check for possible horizontal and vertical moves
    for i in range(5):
        for j in range(5):
            if horizontal[i, j] == 0 and is_capture(horizontal, vertical, capture, i, j, 'H'):
                return f"{i},{j},H"
            if vertical[i, j] == 0 and is_capture(horizontal, vertical, capture, i, j, 'V'):
                return f"{i},{j},V"
    
    # No immediate captures found, gather all moves
    for i in range(5):
        for j in range(5):
            if horizontal[i, j] == 0:
                moves.append((i, j, 'H'))
            if vertical[i, j] == 0:
                moves.append((i, j, 'V'))
    
    # Play a move while avoiding creating a box with 3 sides filled
    for move in moves:
        i, j, direction = move
        if direction == 'H':
            if (i > 0 and horizontal[i-1, j] == 1 and vertical[i-1, j] == 1 and vertical[i-1, j+1] == 1) or (i < 4 and horizontal[i, j] == 1 and vertical[i, j] == 1 and vertical[i, j+1] == 1):
                continue  # This move would allow opponent to score in next round
        elif direction == 'V':
            if (j > 0 and vertical[i, j-1] == 1 and horizontal[i, j-1] == 1 and horizontal[i+1, j-1] == 1) or (j < 4 and vertical[i, j] == 1 and horizontal[i, j] == 1 and horizontal[i+1, j] == 1):
                continue  # This move would allow opponent to score in next round
        
        # Make a legal move here
        return f"{i},{j},{direction}"

    # Fallback, this shouldn't normally happen (there's always at least one available move)
    return "0,0,H"

