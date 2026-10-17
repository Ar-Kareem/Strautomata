
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    def can_capture(row, col):
        # Check if the box at (row, col) can be captured
        return (horizontal[row, col] != 0 and
                horizontal[row + 1, col] != 0 and
                vertical[row, col] != 0 and
                vertical[row, col + 1] != 0)

    def check_three_sides(row, col):
        # Count how many sides are filled for box (row, col)
        filled_sides = 0
        if horizontal[row, col] != 0:
            filled_sides += 1
        if horizontal[row + 1, col] != 0:
            filled_sides += 1
        if vertical[row, col] != 0:
            filled_sides += 1
        if vertical[row, col + 1] != 0:
            filled_sides += 1
        return filled_sides

    # First, check for capture moves
    for row in range(4):
        for col in range(4):
            if can_capture(row, col):
                # Prioritize capturing the box
                if horizontal[row, col] == 0:  # Highlight if we can fill horizontal
                    return f"{row},{col},H"
                if vertical[row, col] == 0:  # Highlight if we can fill vertical
                    return f"{row},{col},V"

    # If no captures, select a move not leading to opponent's captures
    for row in range(4):
        for col in range(4):
            if horizontal[row, col] == 0:
                if check_three_sides(row, col) < 3:  # Avoid creating a potential box
                    return f"{row},{col},H"
            if vertical[row, col] == 0:
                if check_three_sides(row, col) < 3:  # Avoid creating a potential box
                    return f"{row},{col},V"

    # If nothing else, just take any legal move (should not happen)
    for row in range(5):
        for col in range(5):
            if horizontal[row, col] == 0:
                return f"{row},{col},H"
            if vertical[row, col] == 0:
                return f"{row},{col},V"

    # Fallback (Should not hit this if the game is valid)
    return "0,0,H"
