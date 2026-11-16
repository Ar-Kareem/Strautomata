
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert lists to 2D numpy arrays for easier indexing
    you = np.array(you).reshape(5, 6)
    opponent = np.array(opponent).reshape(5, 6)
    
    # Define direction offsets: U, R, D, L
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dir_names = ['U', 'R', 'D', 'L']
    
    # Scan board row by row, column by column
    for row in range(5):
        for col in range(6):
            # Check if this cell has your piece
            if you[row, col] == 1:
                # Check each direction
                for idx, (dr, dc) in enumerate(directions):
                    new_row, new_col = row + dr, col + dc
                    # Check bounds
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        # Check if opponent piece is there
                        if opponent[new_row, new_col] == 1:
                            return f"{row},{col},{dir_names[idx]}"
    
    # According to the problem, there is always at least one legal move.
    # So we should never reach here.
    # But for completeness and safety, return a dummy move (should not happen).
    return "0,0,U"
