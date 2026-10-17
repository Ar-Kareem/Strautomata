
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = 10
    # Convert board to numpy array for easier handling
    import numpy as np
    board_array = np.array(board)
    
    # Find all hit positions
    hits = np.where(board_array == 1)
    hit_positions = list(zip(hits[0], hits[1]))
    
    # If we have hits, try to sink the ship
    if hit_positions:
        # For each hit, check adjacent cells for possible continuation
        for r, c in hit_positions:
            # Check if this hit is part of a known ship orientation
            directions_checked = []
            
            # Check if we can determine direction from adjacent hits
            adjacent_hits = []
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board_array[nr, nc] == 1:
                    adjacent_hits.append((nr, nc))
            
            # If we have adjacent hits, we know the orientation
            if adjacent_hits:
                if len(adjacent_hits) == 1:
                    # Continue in the same direction
                    ar, ac = adjacent_hits[0]
                    dr, dc = ar - r, ac - c
                    
                    # Check both directions along this line
                    targets = []
                    for mul in [1, -1]:
                        nr, nc = r + mul * dr, c + mul * dc
                        if 0 <= nr < n and 0 <= nc < n and board_array[nr, nc] == 0:
                            targets.append((nr, nc))
                    
                    if targets:
                        return random.choice(targets)
                else:
                    # Multiple adjacent hits - continue at ends
                    # Find the ends of the ship
                    ship_cells = [(r, c)] + adjacent_hits
                    # Sort to find orientation
                    if all(rc[0] == r for rc in ship_cells):  # Horizontal
                        ship_cells.sort(key=lambda x: x[1])
                        # Check left and right ends
                        targets = []
                        left = (ship_cells[0][0], ship_cells[0][1] - 1)
                        right = (ship_cells[-1][0], ship_cells[-1][1] + 1)
                        for nr, nc in [left, right]:
                            if 0 <= nr < n and 0 <= nc < n and board_array[nr, nc] == 0:
                                targets.append((nr, nc))
                        if targets:
                            return random.choice(targets)
                    elif all(rc[1] == c for rc in ship_cells):  # Vertical
                        ship_cells.sort(key=lambda x: x[0])
                        # Check top and bottom ends
                        targets = []
                        top = (ship_cells[0][0] - 1, ship_cells[0][1])
                        bottom = (ship_cells[-1][0] + 1, ship_cells[-1][1])
                        for nr, nc in [top, bottom]:
                            if 0 <= nr < n and 0 <= nc < n and board_array[nr, nc] == 0:
                                targets.append((nr, nc))
                        if targets:
                            return random.choice(targets)
            
            # If we can't determine direction or the above didn't work, try all adjacent unknown cells
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < n and 0 <= nc < n and board_array[nr, nc] == 0:
                    return (nr, nc)
    
    # If no hits or no adjacent unknown cells, use a checkerboard pattern for initial searching
    # This targets every other cell to efficiently find ships
    checkerboard_positions = []
    for r in range(n):
        for c in range(n):
            if (r + c) % 2 == 0 and board_array[r, c] == 0:
                checkerboard_positions.append((r, c))
    
    if checkerboard_positions:
        return random.choice(checkerboard_positions)
    
    # If no checkerboard positions, pick any remaining unknown cell
    unknown_positions = []
    for r in range(n):
        for c in range(n):
            if board_array[r, c] == 0:
                unknown_positions.append((r, c))
    
    if unknown_positions:
        return random.choice(unknown_positions)
    
    # Fallback (should never happen in a valid game)
    for r in range(n):
        for c in range(n):
            if board_array[r, c] == 0:
                return (r, c)
    
    # Should never reach here
    return (0, 0)
