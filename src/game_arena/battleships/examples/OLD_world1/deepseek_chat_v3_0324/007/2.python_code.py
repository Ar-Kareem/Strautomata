
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Find all hit cells that haven't been fully explored
    hit_cells = list(zip(*np.where(board_np == 1)))
    
    # Prioritize hits that have adjacent unexplored cells
    for (row, col) in hit_cells:
        # Check all four directions
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < 10 and 0 <= c < 10 and board_np[r, c] == 0:
                return (r, c)
    
    # If no adjacent hits found, use probabilistic targeting
    # Create probability map based on possible ship positions
    probability_map = np.zeros((10, 10))
    ship_sizes = [5, 4, 3, 3, 2]
    
    for size in ship_sizes:
        # Horizontal placements
        for i in range(10):
            for j in range(10 - size + 1):
                if np.all(board_np[i, j:j+size] <= 0):  # No misses (-1) in this segment
                    probability_map[i, j:j+size] += 1
        
        # Vertical placements
        for i in range(10 - size + 1):
            for j in range(10):
                if np.all(board_np[i:i+size, j] <= 0):
                    probability_map[i:i+size, j] += 1
    
    # Zero out already shot cells
    probability_map[board_np != 0] = 0
    
    # If probability map is all zeros, pick first available cell (shouldn't happen in valid game)
    if np.sum(probability_map) == 0:
        rows, cols = np.where(board_np == 0)
        return (rows[0], cols[0])
    
    # Find the cell with maximum probability
    max_prob = np.max(probability_map)
    candidates = np.argwhere(probability_map == max_prob)
    return tuple(candidates[0])
