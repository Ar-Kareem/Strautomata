
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    rows, cols = board.shape
    
    # First, check if we have any hits to target
    hit_positions = np.argwhere(board == 1)
    
    if len(hit_positions) > 0:
        # We have hits - try to sink the ship
        for (r, c) in hit_positions:
            # Check neighboring cells for potential ship continuation
            neighbors = [
                (r-1, c), (r+1, c), (r, c-1), (r, c+1)
            ]
            
            # Filter valid neighbors that are unknown and inside the board
            valid_neighbors = [
                (nr, nc) for (nr, nc) in neighbors
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0
            ]
            
            if valid_neighbors:
                return valid_neighbors[0]
    
    # No current hits to target - use probability-based hunting
    # Create probability density considering all possible ship positions
    prob = np.zeros((rows, cols))
    
    # Ships to consider: lengths 2, 3, 3, 4, 5
    ship_lengths = [2, 3, 3, 4, 5]
    
    for length in ship_lengths:
        # Horizontal ships
        for r in range(rows):
            for c in range(cols - length + 1):
                if np.all(board[r, c:c+length] <= 0):
                    prob[r, c:c+length] += 1
        
        # Vertical ships
        for c in range(cols):
            for r in range(rows - length + 1):
                if np.all(board[r:r+length, c] <= 0):
                    prob[r:r+length, c] += 1
    
    # Zero out already attempted positions
    prob[board != 0] = 0
    
    # If no probability left (shouldn't happen in valid game), pick first available
    if np.max(prob) == 0:
        available = np.argwhere(board == 0)
        return tuple(available[0])
    
    # Return position with highest probability
    max_prob_pos = np.unravel_index(np.argmax(prob), prob.shape)
    return (max_prob_pos[0], max_prob_pos[1])
