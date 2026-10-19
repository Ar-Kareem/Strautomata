
import numpy as np
from collections import defaultdict
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    n = len(grid)
    
    # Find all unknown cells (0)
    unknown_cells = []
    for i in range(n):
        for j in range(n):
            if grid[i, j] == 0:
                unknown_cells.append((i, j))
    
    if not unknown_cells:
        # Should not happen in normal gameplay
        return (0, 0)
    
    # Check for hits that might be part of a ship
    hit_cells = []
    for i in range(n):
        for j in range(n):
            if grid[i, j] == 1:
                hit_cells.append((i, j))
    
    # If we have hits, look for potential ship segments
    if hit_cells:
        # Try to expand from hit cells - prioritize adjacent unknown cells
        adjacent_unknown = set()
        for i, j in hit_cells:
            # Check all 4 adjacent cells
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n and grid[ni, nj] == 0:
                    adjacent_unknown.add((ni, nj))
        
        if adjacent_unknown:
            # Prioritize cells adjacent to existing hits
            # We want to continue attacking the same ship
            # Let's check if the adjacent unknown cells have potential
            # by looking at patterns that might form a ship
            
            # Filter to prefer cells that are in the same row or column as hits
            # but not already examined
            preferred_cells = []
            for i, j in adjacent_unknown:
                # Prefer those closer to existing hits
                min_distance = min(abs(i - hit_i) + abs(j - hit_j) 
                                 for hit_i, hit_j in hit_cells)
                preferred_cells.append((min_distance, i, j))
            
            # Sort by minimum distance and choose the closest
            preferred_cells.sort()
            if preferred_cells:
                return (preferred_cells[0][1], preferred_cells[0][2])
    
    # If no clear pattern, prefer center areas or use random selection from unknown
    # to avoid getting stuck in corners
    center = n // 2
    center_region = []
    for i in range(n):
        for j in range(n):
            if grid[i, j] == 0:
                distance_to_center = abs(i - center) + abs(j - center)
                if distance_to_center <= 3:  # 3 steps from center
                    center_region.append((distance_to_center, i, j))
    
    # Prefer cells closer to center if they're unknown
    if center_region:
        center_region.sort()
        # Choose randomly among the closest ones to center (add some randomness)
        min_dist = center_region[0][0]
        candidates = [(i, j) for d, i, j in center_region if d == min_dist]
        return random.choice(candidates)
    
    # Otherwise just pick a random unknown cell
    return random.choice(unknown_cells)
