
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier handling
    you_board = np.array(you)
    opponent_board = np.array(opponent)
    
    # Directions: U, R, D, L
    directions = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    dir_names = ['U', 'R', 'D', 'L']
    
    # Iterate through all positions
    for row in range(5):
        for col in range(6):
            # If this is my piece
            if you_board[row, col] == 1:
                # Check all 4 directions
                for i, (d_row, d_col) in enumerate(directions):
                    new_row, new_col = row + d_row, col + d_col
                    
                    # Check if destination is in bounds
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        # Check if destination has opponent piece
                        if opponent_board[new_row, new_col] == 1:
                            # This is a legal move
                            return f"{row},{col},{dir_names[i]}"
    
    # This should never happen according to problem statement
    # but just in case we return a fallback move
    raise Exception("No legal move found")
