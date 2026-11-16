
import numpy as np
from itertools import product

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    size = board.shape[0]
    
    # If there are hits, target adjacent cells
    hit_positions = np.argwhere(board == 1)
    if len(hit_positions) > 0:
        for (r, c) in hit_positions:
            # Check adjacent cells (up, down, left, right)
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size and board[nr, nc] == 0:
                    return (nr, nc)
    
    # If no hits, use probability density based on possible ship placements
    ship_lengths = [5, 4, 3, 3, 2]
    prob = np.zeros((size, size))
    
    for length in ship_lengths:
        # Horizontal placements
        for r in range(size):
            for c in range(size - length + 1):
                if np.all(board[r, c:c+length] <= 0):  # No misses or hits blocking
                    prob[r, c:c+length] += 1
        
        # Vertical placements
        for r in range(size - length + 1):
            for c in range(size):
                if np.all(board[r:r+length, c] <= 0):  # No misses or hits blocking
                    prob[r:r+length, c] += 1
    
    # Mask already fired cells
    prob[board != 0] = 0
    
    # If no valid moves left (shouldn't happen if game isn't over), fallback to first unknown
    if np.sum(prob) == 0:
        unknown = np.argwhere(board == 0)
        if len(unknown) > 0:
            return tuple(unknown[0])
        else:
            return (0, 0)  # Should never happen
    
    # Find cell with highest probability
    max_prob = np.max(prob)
    candidates = np.argwhere(prob == max_prob)
    return tuple(candidates[np.random.choice(len(candidates))])
