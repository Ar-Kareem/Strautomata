
import random
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Targeting policy for Battleship game.
    Returns (row, col) of next shot.
    """
    SIZE = 10
    # Ship lengths remaining (we don't know which are sunk, but we can infer)
    # We'll work with the standard set
    SHIPS = [5, 4, 3, 3, 2]
    
    # Helper function to get cell value safely
    def get_cell(r, c):
        if 0 <= r < SIZE and 0 <= c < SIZE:
            return board[r][c]
        return None
    
    # Phase 1: Check for hits that might be part of unsunk ships
    # We look for hits (1) that have at least one adjacent unknown (0)
    hits = []
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 1:
                # Check if this hit has any adjacent unknown cells
                # If all adjacent are misses (-1) or hits (1), ship might be sunk
                # But we can't be sure, so we check for unknowns
                adj_unknown = False
                for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nr, nc = r + dr, c + dc
                    val = get_cell(nr, nc)
                    if val == 0:
                        adj_unknown = True
                        break
                if adj_unknown:
                    hits.append((r, c))
    
    # If we have hits to pursue
    if hits:
        # Try to find a line of hits
        # Group hits by connected components
        visited = set()
        components = []
        
        for hit in hits:
            if hit in visited:
                continue
            # BFS to find connected hits
            stack = [hit]
            component = set()
            while stack:
                r, c = stack.pop()
                if (r, c) in component:
                    continue
                component.add((r, c))
                visited.add((r, c))
                # Check adjacent hits
                for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                    nr, nc = r + dr, c + dc
                    if get_cell(nr, nc) == 1 and (nr, nc) not in component:
                        stack.append((nr, nc))
            
            if len(component) >= 2:
                components.append(list(component))
        
        # If we have connected hits (line)
        if components:
            # Process each component
            for component in components:
                if len(component) >= 2:
                    # Check if they're in a line horizontally or vertically
                    rows = sorted({r for r, c in component})
                    cols = sorted({c for r, c in component})
                    
                    # Horizontal line
                    if len(rows) == 1:
                        # All in same row
                        row = rows[0]
                        cols_sorted = sorted([c for r, c in component if r == row])
                        # Check left and right extensions
                        left_col = min(cols_sorted) - 1
                        right_col = max(cols_sorted) + 1
                        
                        # Try left
                        if get_cell(row, left_col) == 0:
                            return (row, left_col)
                        # Try right
                        if get_cell(row, right_col) == 0:
                            return (row, right_col)
                    
                    # Vertical line
                    if len(cols) == 1:
                        # All in same column
                        col = cols[0]
                        rows_sorted = sorted([r for r, c in component if c == col])
                        # Check up and down extensions
                        up_row = min(rows_sorted) - 1
                        down_row = max(rows_sorted) + 1
                        
                        # Try up
                        if get_cell(up_row, col) == 0:
                            return (up_row, col)
                        # Try down
                        if get_cell(down_row, col) == 0:
                            return (down_row, col)
        
        # If no line found or couldn't extend line, fire at adjacent unknown of any hit
        # Prioritize hits that have fewer adjacent unknowns (to localize)
        candidates = []
        for r, c in hits:
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                nr, nc = r + dr, c + dc
                if get_cell(nr, nc) == 0:
                    candidates.append((nr, nc))
        
        if candidates:
            # Choose randomly from candidates
            return random.choice(candidates)
    
    # Phase 2: No hits to pursue, use probability density
    # We'll compute a simple probability heatmap
    heatmap = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    
    # For each cell, compute how many ship placements could include it
    # We'll use a simplified approach that's faster
    
    # First, get all unknown cells
    unknown_cells = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    
    # If very few unknown cells, just pick one
    if len(unknown_cells) <= 5:
        return random.choice(unknown_cells)
    
    # Generate all possible ship placements
    # We'll do this for each ship length
    ship_placements_count = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
    
    for length in SHIPS:
        # Horizontal placements
        for r in range(SIZE):
            for c in range(SIZE - length + 1):
                # Check if this placement is possible (no misses in the way)
                valid = True
                for k in range(length):
                    if board[r][c + k] == -1:  # Miss blocks placement
                        valid = False
                        break
                if valid:
                    # Add to heatmap
                    for k in range(length):
                        if board[r][c + k] == 0:  # Only count unknown cells
                            ship_placements_count[r][c + k] += 1
        
        # Vertical placements
        for r in range(SIZE - length + 1):
            for c in range(SIZE):
                valid = True
                for k in range(length):
                    if board[r + k][c] == -1:  # Miss blocks placement
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        if board[r + k][c] == 0:
                            ship_placements_count[r + k][c] += 1
    
    # Also add bonus for cells that are far from misses
    # And for cells that follow a checkerboard pattern (good for hunting)
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                # Checkerboard bonus (hunting pattern)
                if (r + c) % 2 == 0:
                    heatmap[r][c] += 2
                
                # Distance from misses bonus
                min_dist_to_miss = float('inf')
                for mr in range(SIZE):
                    for mc in range(SIZE):
                        if board[mr][mc] == -1:
                            dist = abs(mr - r) + abs(mc - c)
                            min_dist_to_miss = min(min_dist_to_miss, dist)
                
                if min_dist_to_miss < float('inf'):
                    heatmap[r][c] += min(5, min_dist_to_miss)
    
    # Combine ship placements count with heatmap
    max_score = -1
    best_cells = []
    
    for r in range(SIZE):
        for c in range(SIZE):
            if board[r][c] == 0:
                score = ship_placements_count[r][c] * 10 + heatmap[r][c]
                if score > max_score:
                    max_score = score
                    best_cells = [(r, c)]
                elif score == max_score:
                    best_cells.append((r, c))
    
    # Choose randomly among best cells
    return random.choice(best_cells) if best_cells else random.choice(unknown_cells)
