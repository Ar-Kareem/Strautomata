
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert to numpy arrays for easier handling
    you_board = np.array(you)
    opponent_board = np.array(opponent)
    
    # Directions: up, right, down, left
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]
    
    # Find all your pieces
    for row in range(5):
        for col in range(6):
            if you_board[row, col] == 1:
                # Check all four directions
                for dr, dc, direction in directions:
                    new_row, new_col = row + dr, col + dc
                    # Check if destination is within bounds and contains opponent piece
                    if 0 <= new_row < 5 and 0 <= new_col < 6:
                        if opponent_board[new_row, new_col] == 1:
                            # This is a legal move
                            return f"{row},{col},{direction}"
    
    # This should never be reached according to problem statement
    # but just in case, return the first possible move
    raise ValueError("No legal move found")
