
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Check all possible edges for legal moves
    for row in range(5):
        for col in range(5):
            # Check horizontal moves
            if row < 4 and horizontal[row, col] == 0:  # horizontal edge check
                # Make the move temporarily
                horizontal[row, col] = 1
                completed_boxes = check_boxes(horizontal, vertical, capture)
                # Undo the move
                horizontal[row, col] = 0
                if completed_boxes:
                    return f"{row},{col},H"
            
            # Check vertical moves
            if col < 4 and vertical[row, col] == 0:  # vertical edge check
                # Make the move temporarily
                vertical[row, col] = 1
                completed_boxes = check_boxes(horizontal, vertical, capture)
                # Undo the move
                vertical[row, col] = 0
                if completed_boxes:
                    return f"{row},{col},V"
    
    # If no capture moves are found, make a non-risky move
    for row in range(5):
        for col in range(5):
            if row < 4 and horizontal[row, col] == 0:
                return f"{row},{col},H"
            if col < 4 and vertical[row, col] == 0:
                return f"{row},{col},V"

def check_boxes(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> int:
    boxes_captured = 0
    for r in range(4):
        for c in range(4):
            if capture[r, c] == 0:
                # Check if all four edges are drawn
                if (horizontal[r, c] != 0 and
                    horizontal[r + 1, c] != 0 and
                    vertical[r, c] != 0 and
                    vertical[r, c + 1] != 0):
                    capture[r, c] = 1
                    boxes_captured += 1
    return boxes_captured
