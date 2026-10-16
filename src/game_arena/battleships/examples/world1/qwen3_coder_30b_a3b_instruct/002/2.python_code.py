
import random
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier handling (optional but nice)
    board = np.array(board)
    rows, cols = board.shape
    
    # First, let's look for any existing hits
    hit_positions = []
    for i in range(rows):
        for j in range(cols):
            if board[i, j] == 1:
                hit_positions.append((i, j))
    
    # If we have hits, try to extend from them in a logical way
    if hit_positions:
        # Try to find which direction to expand from
        # Or just pick an unexplored neighbor of a hit
        for row, col in hit_positions:
            # Look at all 4 adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                # Check if valid and unshot
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                    return (nr, nc)
    
    # If no shots have been taken yet, or no adjacent unexplored cells near hits,
    # pick a random unexplored cell
    unexplored_cells = []
    for i in range(rows):
        for j in range(cols):
            if board[i, j] == 0:
                unexplored_cells.append((i, j))
    
    if unexplored_cells:
        return random.choice(unexplored_cells)
    else:
        # This should not happen in a valid game, but just in case
        # Return any invalid cell - should never reach here
        return (0, 0)
