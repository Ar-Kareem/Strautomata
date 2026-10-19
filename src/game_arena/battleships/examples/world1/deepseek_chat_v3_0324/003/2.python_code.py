
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    rows, cols = board.shape
    
    # First, check for any existing hits that need follow-up
    hit_positions = np.argwhere(board == 1)
    
    if len(hit_positions) > 0:
        # Try to find adjacent hits to determine ship orientation
        for (r, c) in hit_positions:
            # Check horizontal possibilities
            if c > 0 and board[r, c-1] == 1:
                # Try to extend right
                if c < cols - 1 and board[r, c+1] == 0:
                    return (r, c+1)
                # Try to extend left
                if c > 1 and board[r, c-2] == 0:
                    return (r, c-2)
            # Check vertical possibilities
            if r > 0 and board[r-1, c] == 1:
                # Try to extend down
                if r < rows - 1 and board[r+1, c] == 0:
                    return (r+1, c)
                # Try to extend up
                if r > 1 and board[r-2, c] == 0:
                    return (r-2, c)
            
            # If single hit, check all adjacent cells
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 0:
                    return (nr, nc)
    
    # If no hits to follow up, create probability density
    heatmap = np.zeros((rows, cols))
    ship_sizes = [5, 4, 3, 3, 2]  # Remaining ship sizes (simplified)
    
    for size in ship_sizes:
        # Check horizontal placements
        for r in range(rows):
            for c in range(cols - size + 1):
                if np.all(board[r, c:c+size] <= 0):  # No hits or misses in this segment
                    heatmap[r, c:c+size] += 1
        
        # Check vertical placements
        for c in range(cols):
            for r in range(rows - size + 1):
                if np.all(board[r:r+size, c] <= 0):  # No hits or misses in this segment
                    heatmap[r:r+size, c] += 1
    
    # Zero out already fired cells
    heatmap[board != 0] = 0
    
    if np.max(heatmap) > 0:
        # Find all cells with max probability
        max_val = np.max(heatmap)
        candidates = np.argwhere(heatmap == max_val)
        # Randomly select among best candidates
        r, c = random.choice(candidates)
        return (r, c)
    else:
        # Fallback to random selection if no good probability found
        unknown = np.argwhere(board == 0)
        return tuple(random.choice(unknown))
