
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    grid = np.array(board)
    n = len(grid)
    
    # Find all unknown cells (0)
    unknown_cells = np.where(grid == 0)
    unknown_coords = list(zip(unknown_cells[0], unknown_cells[1]))
    
    if not unknown_coords:
        # No unknown cells - this shouldn't happen in normal gameplay
        return (0, 0)
    
    # If no hits yet, shoot in center or a strategic location
    hits = np.where(grid == 1)
    if len(hits[0]) == 0:
        # Prefer center area for first shots
        center_candidates = [(4,4), (4,5), (5,4), (5,5)]
        for r, c in center_candidates:
            if (r, c) in unknown_coords:
                return (r, c)
        # Fallback to any unknown cell
        return unknown_coords[0]
    
    # Look for hits that might be part of a ship
    # Find all hit cells
    hit_coords = list(zip(hits[0], hits[1]))
    
    # Try to find adjacent unknown cells to hits (potential ship continuation)
    potential_targets = set()
    
    # For each hit cell, check adjacent cells
    for r, c in hit_coords:
        # Check up, down, left, right
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            # Check if it's within bounds and unknown
            if 0 <= nr < n and 0 <= nc < n and grid[nr, nc] == 0:
                potential_targets.add((nr, nc))
    
    # If we found potential continuation targets, shoot there
    if potential_targets:
        # Prefer targets near existing hits
        # For diversity, we'll pick a random one in the potential targets
        # but prioritize those adjacent to multiple hits if possible
        return list(potential_targets)[0]
    
    # If no continuation targets, pick a random unknown cell
    # But prefer center if it's available
    center = (n//2, n//2)
    if center in unknown_coords:
        return center
    
    # Otherwise, pick first unknown cell
    return unknown_coords[0]
