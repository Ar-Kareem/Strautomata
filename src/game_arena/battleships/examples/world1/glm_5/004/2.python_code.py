
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    grid = np.array(board, dtype=int)
    rows, cols = 10, 10
    fleet = [5, 4, 3, 3, 2]
    
    # Helper to get neighbors
    def get_neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc

    # 1. Analyze the board for hits and sunk ships
    visited = np.zeros_like(grid, dtype=bool)
    live_hits = []
    sunk_lengths = []
    
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1 and not visited[r, c]:
                # BFS to find connected component of hits
                component = []
                q = deque([(r, c)])
                visited[r, c] = True
                has_unknown_neighbor = False
                
                while q:
                    cr, cc = q.popleft()
                    component.append((cr, cc))
                    
                    for nr, nc in get_neighbors(cr, cc):
                        if grid[nr, nc] == 1 and not visited[nr, nc]:
                            visited[nr, nc] = True
                            q.append((nr, nc))
                        elif grid[nr, nc] == 0:
                            has_unknown_neighbor = True
                
                if has_unknown_neighbor:
                    live_hits.append(component)
                else:
                    sunk_lengths.append(len(component))

    # 2. Target Mode
    # If we have live hits, focus fire
    for component in live_hits:
        # Check if component is linear
        rows_set = {p[0] for p in component}
        cols_set = {p[1] for p in component}
        is_linear = len(rows_set) == 1 or len(cols_set) == 1
        
        targets = []
        
        if is_linear and len(component) > 1:
            # Prioritize ends of the line
            is_horiz = (len(rows_set) == 1)
            
            if is_horiz:
                component.sort(key=lambda x: x[1])
                ends = [component[0], component[-1]]
                # Check left of start
                r, c = ends[0]
                if c - 1 >= 0 and grid[r, c - 1] == 0:
                    targets.append((r, c - 1))
                # Check right of end
                r, c = ends[1]
                if c + 1 < cols and grid[r, c + 1] == 0:
                    targets.append((r, c + 1))
            else:
                # Vertical
                component.sort(key=lambda x: x[0])
                ends = [component[0], component[-1]]
                # Check above start
                r, c = ends[0]
                if r - 1 >= 0 and grid[r - 1, c] == 0:
                    targets.append((r - 1, c))
                # Check below end
                r, c = ends[1]
                if r + 1 < rows and grid[r + 1, c] == 0:
                    targets.append((r + 1, c))
            
            if targets:
                return targets[0]

        # If single hit, non-linear, or line ends blocked, check all neighbors
        # We iterate component to find any adjacent 0
        for r, c in component:
            for nr, nc in get_neighbors(r, c):
                if grid[nr, nc] == 0:
                    return (nr, nc)

    # 3. Hunt Mode (Probability Density Map)
    # Determine remaining ships
    remaining_ships = list(fleet)
    # Simple deduction: remove ships that match sunk component lengths
    # Note: This assumes sunk ships are correctly identified isolated blocks
    for length in sunk_lengths:
        if length in remaining_ships:
            remaining_ships.remove(length)
            
    # Calculate heatmap
    heatmap = np.zeros((rows, cols), dtype=float)
    
    for L in remaining_ships:
        # Horizontal placements
        for r in range(rows):
            for c in range(cols - L + 1):
                # Check if placement is valid (all cells must be 0 or 1, but we only score 0s)
                # Valid placement if no misses (-1)
                slice_r = grid[r, c:c+L]
                if np.all(slice_r != -1):
                    # Add score to unknown cells
                    for k in range(L):
                        if grid[r, c+k] == 0:
                            heatmap[r, c+k] += 1
                        
        # Vertical placements
        for c in range(cols):
            for r in range(rows - L + 1):
                slice_r = grid[r:r+L, c]
                if np.all(slice_r != -1):
                    for k in range(L):
                        if grid[r+k, c] == 0:
                            heatmap[r+k, c] += 1

    # Mask hits and misses (should be 0 prob anyway, but safety)
    heatmap[grid != 0] = -1
    
    # Find max probability
    if np.max(heatmap) > 0:
        # Find all max indices
        max_val = np.max(heatmap)
        indices = np.argwhere(heatmap == max_val)
        # Pick one (deterministically, first one)
        r, c = indices[0]
        return (int(r), int(c))
    
    # 4. Fallback
    # If heatmap is empty (no ships left? or logic error), fire at any 0
    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 0:
                return (r, c)

    return (0, 0)
