
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert the board to a numpy array for easier manipulation
    board = np.array(board)
    
    # Find all unknown cells
    unknown_cells = np.argwhere(board == 0)
    
    # If there are no unknown cells, return a random unknown cell (should not happen in a valid game)
    if len(unknown_cells) == 0:
        return (0, 0)
    
    # Find all hit cells
    hit_cells = np.argwhere(board == 1)
    
    # If there are hits, try to find the next cell in the same ship
    if len(hit_cells) > 0:
        # For each hit cell, check the adjacent cells
        for hit in hit_cells:
            row, col = hit
            # Check up, down, left, right
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                new_row, new_col = row + dr, col + dc
                # If the adjacent cell is unknown, return it
                if 0 <= new_row < 10 and 0 <= new_col < 10 and board[new_row, new_col] == 0:
                    return (new_row, new_col)
    
    # If no adjacent unknown cells found, use a pattern-based approach for the hunt phase
    # Use a checkerboard pattern to efficiently cover the board
    # Start with the pattern that has the highest probability of hitting a ship
    # The pattern is based on the fact that ships cannot overlap and must be placed in straight lines
    # We use a 2x2 pattern that covers the board efficiently
    # The pattern is: (0,0), (0,2), (0,4), (0,6), (0,8), (1,1), (1,3), (1,5), (1,7), (1,9), ...
    pattern_cells = []
    for row in range(10):
        for col in range(10):
            if (row + col) % 2 == 0:
                if board[row, col] == 0:
                    pattern_cells.append((row, col))
    
    # If there are pattern cells, return a random one
    if len(pattern_cells) > 0:
        return random.choice(pattern_cells)
    
    # If no pattern cells found, return a random unknown cell
    return random.choice(unknown_cells)
