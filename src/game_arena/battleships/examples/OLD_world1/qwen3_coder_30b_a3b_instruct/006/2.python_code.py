
import random
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    n = len(board)
    
    # Find all cells that haven't been fired at yet
    unknown_cells = []
    hit_cells = []
    
    for i in range(n):
        for j in range(n):
            if grid[i, j] == 0:
                unknown_cells.append((i, j))
            elif grid[i, j] == 1:
                hit_cells.append((i, j))
    
    # If no hits yet, use basic strategy
    if len(hit_cells) == 0:
        # Try to avoid edges to maximize chances of hits
        # Prefer center areas
        candidate_cells = []
        for i in range(2, n-2):
            for j in range(2, n-2):
                if grid[i, j] == 0:
                    candidate_cells.append((i, j))
        
        # If no center cells, use all unknown
        if not candidate_cells:
            candidate_cells = unknown_cells
            
        # Prioritize positions near center
        center = (n//2, n//2)
        best_cell = candidate_cells[0]
        min_dist = float('inf')
        
        for cell in candidate_cells:
            dist = abs(cell[0] - center[0]) + abs(cell[1] - center[1])
            if dist < min_dist:
                min_dist = dist
                best_cell = cell
                
        return best_cell
    
    # If we have hits, try to find connected hits to sink ships
    # Look for horizontal or vertical patterns in hits
    
    # Try to expand from existing hits
    for hit_row, hit_col in hit_cells:
        # Check adjacent cells (up, down, left, right)
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            new_row, new_col = hit_row + dr, hit_col + dc
            # Check if the cell is within bounds and unknown
            if 0 <= new_row < n and 0 <= new_col < n and grid[new_row, new_col] == 0:
                return (new_row, new_col)
    
    # If no adjacent unknown cells to hits, pick a random unknown cell
    if unknown_cells:
        return random.choice(unknown_cells)
    
    # If all cells are hit/miss, return a random valid cell (shouldn't happen in practice)
    return (random.randint(0, n-1), random.randint(0, n-1))
