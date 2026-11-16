
import numpy as np

def policy(board):
    """Return (row, col) to shoot next."""
    board = np.array(board)
    rows, cols = board.shape
    
    # Helper to check if a cell is within bounds
    def in_bounds(r, c):
        return 0 <= r < rows and 0 <= c < cols
    
    # Directions: up, down, left, right
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Step 1: Find all hits (value 1)
    hit_positions = list(zip(*np.where(board == 1)))
    
    # Step 2: Identify active hits (hits with at least one unknown neighbor)
    active_hits = []
    for r, c in hit_positions:
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr, nc] == 0:
                active_hits.append((r, c))
                break
    
    # If there are active hits, enter target mode
    if active_hits:
        # Group active hits into connected components (orthogonal adjacency)
        visited = set()
        components = []
        for hit in active_hits:
            if hit in visited:
                continue
            # BFS to find connected component
            stack = [hit]
            comp = set()
            while stack:
                cur = stack.pop()
                if cur in comp:
                    continue
                comp.add(cur)
                r, c = cur
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in active_hits and (nr, nc) not in comp:
                        stack.append((nr, nc))
            visited.update(comp)
            components.append(list(comp))
        
        # For each component, determine possible target cells
        target_candidates = []
        for comp in components:
            if len(comp) == 1:
                # Single hit: target all unknown neighbors
                r, c = comp[0]
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr, nc] == 0:
                        target_candidates.append((nr, nc))
            else:
                # Multiple hits: assume they form a line
                # Check if all share same row (horizontal) or same column (vertical)
                rows_in_comp = {r for r, c in comp}
                cols_in_comp = {c for r, c in comp}
                if len(rows_in_comp) == 1:
                    # Horizontal line
                    row = next(iter(rows_in_comp))
                    cols = sorted([c for r, c in comp])
                    left_col = cols[0]
                    right_col = cols[-1]
                    # Left extension
                    if left_col - 1 >= 0 and board[row, left_col - 1] == 0:
                        target_candidates.append((row, left_col - 1))
                    # Right extension
                    if right_col + 1 < cols and board[row, right_col + 1] == 0:
                        target_candidates.append((row, right_col + 1))
                elif len(cols_in_comp) == 1:
                    # Vertical line
                    col = next(iter(cols_in_comp))
                    rows = sorted([r for r, c in comp])
                    top_row = rows[0]
                    bottom_row = rows[-1]
                    # Top extension
                    if top_row - 1 >= 0 and board[top_row - 1, col] == 0:
                        target_candidates.append((top_row - 1, col))
                    # Bottom extension
                    if bottom_row + 1 < rows and board[bottom_row + 1, col] == 0:
                        target_candidates.append((bottom_row + 1, col))
                else:
                    # L-shaped or unusual; fall back to targeting around each hit
                    for r, c in comp:
                        for dr, dc in dirs:
                            nr, nc = r + dr, c + dc
                            if in_bounds(nr, nc) and board[nr, nc] == 0:
                                target_candidates.append((nr, nc))
        
        # Remove duplicates and choose the first candidate
        if target_candidates:
            # Optionally, we could shuffle or prioritize, but first is fine
            return target_candidates[0]
    
    # Hunt mode: no active hits
    # Compute heat map (probability density) for each unknown cell
    heat = np.zeros((rows, cols), dtype=int)
    ship_lengths = [5, 4, 3, 3, 2]
    
    for length in ship_lengths:
        # Horizontal placements
        for r in range(rows):
            for c in range(cols - length + 1):
                # Check if placement is valid: no misses in the segment
                valid = True
                for k in range(length):
                    if board[r, c + k] == -1:  # miss makes placement invalid
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        if board[r, c + k] == 0:  # only increment for unknown cells?
                            heat[r, c + k] += 1
        # Vertical placements
        for r in range(rows - length + 1):
            for c in range(cols):
                valid = True
                for k in range(length):
                    if board[r + k, c] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(length):
                        if board[r + k, c] == 0:
                            heat[r + k, c] += 1
    
    # Now find the unknown cell with highest heat
    unknown_positions = list(zip(*np.where(board == 0)))
    if not unknown_positions:
        # Should not happen, but fallback
        for r in range(rows):
            for c in range(cols):
                if board[r, c] == 0:
                    return (r, c)
    
    # Choose cell with maximum heat; break ties by row then column
    best_cell = unknown_positions[0]
    best_heat = heat[best_cell]
    for pos in unknown_positions[1:]:
        if heat[pos] > best_heat:
            best_heat = heat[pos]
            best_cell = pos
        elif heat[pos] == best_heat:
            # Tie-breaking: smaller row, then smaller column
            if pos[0] < best_cell[0] or (pos[0] == best_cell[0] and pos[1] < best_cell[1]):
                best_cell = pos
    
    return best_cell
