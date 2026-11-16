
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Check all possible edge moves
    possible_moves = []
    
    # Horizontal moves
    for r in range(5):
        for c in range(4):
            if horizontal[r, c] == 0:  # Edge is free
                # Check if putting here completes any boxes
                boxes_completed = 0
                if r > 0 and capture[r-1, c] == 0:  # Top box
                    if vertical[r-1, c] and vertical[r-1, c-1] and horizontal[r-1, c]:
                        boxes_completed += 1
                if r < 4 and capture[r, c] == 0:  # Bottom box
                    if vertical[r, c] and vertical[r, c-1] and horizontal[r, c]:
                        boxes_completed += 1

                if boxes_completed > 0:
                    return f"{r},{c},H"  # Completing a box

                possible_moves.append((r, c, 'H'))

    # Vertical moves
    for r in range(4):
        for c in range(5):
            if vertical[r, c] == 0:  # Edge is free
                # Check if putting here completes any boxes
                boxes_completed = 0
                if c > 0 and capture[r, c-1] == 0:  # Left box
                    if horizontal[r, c-1] and horizontal[r-1, c-1] and vertical[r, c-1]:
                        boxes_completed += 1
                if c < 4 and capture[r, c] == 0:  # Right box
                    if horizontal[r, c] and horizontal[r-1, c] and vertical[r, c]:
                        boxes_completed += 1
                
                if boxes_completed > 0:
                    return f"{r},{c},V"  # Completing a box

                possible_moves.append((r, c, 'V'))

    # If no captures or blocks are found, just select a legal move
    for move in possible_moves:
        r, c, orientation = move
        if orientation == 'H':
            return f"{r},{c},H"
        else:
            return f"{r},{c},V"

    # If still no moves found, default to a valid entry
    return "0,0,H"  # This should not actually occur, as there should always be a legal move.
