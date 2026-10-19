
import random
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    n = len(grid)
    
    # Find all unknown cells (0)
    unknown_cells = [(i, j) for i in range(n) for j in range(n) if grid[i, j] == 0]
    
    if not unknown_cells:
        # This shouldn't happen in a valid game state
        return (random.randint(0, n-1), random.randint(0, n-1))
    
    # If we have hits, try to find adjacent cells to continue hitting
    hit_cells = [(i, j) for i in range(n) for j in range(n) if grid[i, j] == 1]
    
    if hit_cells:
        # Look for cells adjacent to hits that are unknown
        potential_targets = set()
        
        # For each hit cell, check all adjacent cells
        for r, c in hit_cells:
            # Check all four adjacent cells
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and grid[nr, nc] == 0:
                    potential_targets.add((nr, nc))
        
        # If we have potential adjacent targets, choose one
        if potential_targets:
            # Prioritize cells that are connected to more hits
            # (but for simplicity, just choose randomly from adjacent ones)
            return random.choice(list(potential_targets))
    
    # If no hits or no adjacent unknown cells, choose a random unknown cell
    return random.choice(unknown_cells)
