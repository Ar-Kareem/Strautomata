
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Define grid size
    GRID_SIZE = 4

    # Function to check for box completion
    def box_completed(row, col):
        return (horizontal[row, col] != 0 and horizontal[row + 1, col] != 0 and
                vertical[row, col] != 0 and vertical[row, col + 1] != 0)

    # Check for immediate box captures
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE):
            if capture[r, c] == 0:  # The box is unclaimed
                if horizontal[r, c] == 0:  # Complete the top edge
                    if box_completed(r, c):
                        return f"{r},{c},H"  # Capture the box
                if horizontal[r + 1, c] == 0:  # Complete the bottom edge
                    if box_completed(r + 1, c):
                        return f"{r + 1},{c},H"  # Capture the box
                if vertical[r, c] == 0:  # Complete the left edge
                    if box_completed(r, c):
                        return f"{r},{c},V"  # Capture the box
                if vertical[r, c + 1] == 0:  # Complete the right edge
                    if box_completed(r, c + 1):
                        return f"{r},{c + 1},V"  # Capture the box

    # If no immediate captures are found, choose a safe move
    for r in range(GRID_SIZE + 1):
        for c in range(GRID_SIZE + 1):
            if r < GRID_SIZE and horizontal[r, c] == 0:
                horizontal[r, c] = 1  # Temporarily mark the edge
                if box_completed(r, c):
                    horizontal[r, c] = 0  # Undo temp marking, don't create a box
                    continue  # Skip this move
                else:
                    horizontal[r, c] = 0  # Undo temp marking
                    return f"{r},{c},H"

            if c < GRID_SIZE and vertical[r, c] == 0:
                vertical[r, c] = 1  # Temporarily mark the edge
                if box_completed(r, c):
                    vertical[r, c] = 0  # Undo temp marking, don't create a box
                    continue  # Skip this move
                else:
                    vertical[r, c] = 0  # Undo temp marking
                    return f"{r},{c},V"

    # Fallback: If all edges seem dangerous, just pick the first available edge
    for r in range(GRID_SIZE + 1):
        for c in range(GRID_SIZE + 1):
            if r < GRID_SIZE and horizontal[r, c] == 0:
                return f"{r},{c},H"
            if c < GRID_SIZE and vertical[r, c] == 0:
                return f"{r},{c},V"

    # In theory we shouldn't reach this point due to game constraints
    return "0,0,H"  # Default legal move (shouldn't reach here)

