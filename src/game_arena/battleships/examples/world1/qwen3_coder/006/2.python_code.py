
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    grid = np.array(board)
    
    # Find all hit positions
    hits = np.where(grid == 1)
    hit_positions = list(zip(hits[0], hits[1]))
    
    # If we have hits, try to sink those ships first
    if hit_positions:
        # Look for adjacent cells to hit positions
        for row, col in hit_positions:
            # Check if this hit is part of a ship we're already working on
            # Look for connected hits (horizontal or vertical)
            connected_hits = find_connected_hits(grid, row, col)
            
            # Get potential target cells around this hit/ship segment
            targets = []
            if len(connected_hits) == 1:
                # Single hit - check all 4 directions
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                for dr, dc in directions:
                    r, c = row + dr, col + dc
                    if 0 <= r < 10 and 0 <= c < 10 and grid[r, c] == 0:
                        targets.append((r, c))
            else:
                # Multiple connected hits - determine orientation
                # Sort by row and column to determine direction
                connected_hits.sort()
                if connected_hits[0][0] == connected_hits[1][0]:
                    # Horizontal ship - check left and right
                    min_col = min(pos[1] for pos in connected_hits)
                    max_col = max(pos[1] for pos in connected_hits)
                    row = connected_hits[0][0]
                    if min_col > 0 and grid[row, min_col - 1] == 0:
                        targets.append((row, min_col - 1))
                    if max_col < 9 and grid[row, max_col + 1] == 0:
                        targets.append((row, max_col + 1))
                else:
                    # Vertical ship - check up and down
                    min_row = min(pos[0] for pos in connected_hits)
                    max_row = max(pos[0] for pos in connected_hits)
                    col = connected_hits[0][1]
                    if min_row > 0 and grid[min_row - 1, col] == 0:
                        targets.append((min_row - 1, col))
                    if max_row < 9 and grid[max_row + 1, col] == 0:
                        targets.append((max_row + 1, col))
            
            # Return first valid target
            if targets:
                return targets[0]
    
    # No current targets - use checkerboard search pattern
    # Ships must intersect even-sum cells (row+col even)
    even_cells = []
    odd_cells = []
    
    for row in range(10):
        for col in range(10):
            if grid[row, col] == 0:  # Unknown cell
                if (row + col) % 2 == 0:
                    even_cells.append((row, col))
                else:
                    odd_cells.append((row, col))
    
    # Prefer even cells for initial search (more efficient)
    if even_cells:
        return even_cells[0]
    elif odd_cells:
        return odd_cells[0]
    
    # Fallback (shouldn't happen in normal play)
    for row in range(10):
        for col in range(10):
            if grid[row, col] == 0:
                return (row, col)
    
    # This should never happen
    return (0, 0)

def find_connected_hits(grid, start_row, start_col):
    """Find all connected hit cells (part of the same ship)"""
    connected = []
    queue = deque([(start_row, start_col)])
    visited = set()
    
    while queue:
        row, col = queue.popleft()
        if (row, col) in visited:
            continue
        visited.add((row, col))
        
        if 0 <= row < 10 and 0 <= col < 10 and grid[row, col] == 1:
            connected.append((row, col))
            # Add adjacent cells to queue
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                queue.append((row + dr, col + dc))
    
    return connected
