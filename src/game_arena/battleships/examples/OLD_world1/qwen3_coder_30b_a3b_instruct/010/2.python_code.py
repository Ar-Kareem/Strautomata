
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    n = len(grid)
    
    # Find all cells that are unknown (0)
    unknown_cells = list(zip(*np.where(grid == 0)))
    
    # If no unknown cells, return any cell (should not happen in normal play)
    if not unknown_cells:
        return (0, 0)
    
    # Find all hit cells (1)
    hit_cells = list(zip(*np.where(grid == 1)))
    
    # If we have hits, try to find adjacent cells to continue attacking
    if hit_cells:
        # Check if there are any adjacent hits forming part of a ship
        # First, try to find ships (sequences of hits in a straight line)
        # For each hit, try to look in all 4 directions
        for r, c in hit_cells:
            # For each direction (up, down, left, right)
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                # Check if there's a sequence in this direction
                start_r, start_c = r, c
                # Extend in the reverse direction to find the start
                while 0 <= start_r - dr < n and 0 <= start_c - dc < n and grid[start_r - dr, start_c - dc] == 1:
                    start_r -= dr
                    start_c -= dc
                
                # Now count how long the ship segment is
                length = 0
                temp_r, temp_c = start_r, start_c
                while 0 <= temp_r < n and 0 <= temp_c < n and grid[temp_r, temp_c] == 1:
                    length += 1
                    temp_r += dr
                    temp_c += dc
                
                # If we have a ship segment of length >= 2, we look for adjacent cells
                # that are not hits but are still unknown and in this line
                if length >= 2:
                    # Try to find the adjacent empty cells in this direction
                    # from the start of the segment
                    temp_r, temp_c = start_r - dr, start_c - dc
                    if 0 <= temp_r < n and 0 <= temp_c < n and grid[temp_r, temp_c] == 0:
                        return (temp_r, temp_c)
                    
                    temp_r, temp_c = start_r + dr * length, start_c + dc * length
                    if 0 <= temp_r < n and 0 <= temp_c < n and grid[temp_r, temp_c] == 0:
                        return (temp_r, temp_c)
        
        # If no ship extensions found, look for cells adjacent to any hit (1)
        # Define adjacent cells (up, down, left, right)
        adj_dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        for r, c in hit_cells:
            for dr, dc in adj_dirs:
                new_r, new_c = r + dr, c + dc
                # Check boundaries
                if 0 <= new_r < n and 0 <= new_c < n:
                    # If it's unknown (0), we should target it
                    if grid[new_r, new_c] == 0:
                        return (new_r, new_c)
    
    # No hits yet, apply a simple strategy
    # Try to find the center of unknown regions, or just pick the first unknown
    
    # Use a heuristic: prioritize the center of the board to spread search
    # and avoid isolated edges
    center = (n//2, n//2)
    center_r, center_c = center
    
    # Look for cells in the radius around the center that are unknown
    # Check in increasing order by Manhattan distance from center
    for distance in range(n):
        for r in range(max(0, center_r - distance), min(n, center_r + distance + 1)):
            for c in range(max(0, center_c - distance), min(n, center_c + distance + 1)):
                # if cell is unknown, and satisfies distance criteria
                if grid[r, c] == 0:
                    # Make sure Manhattan distance matches our current ring
                    if abs(r - center_r) + abs(c - center_c) == distance:
                        return (r, c)
    
    # Fallback for edge case (shouldn't happen)
    return unknown_cells[0]

