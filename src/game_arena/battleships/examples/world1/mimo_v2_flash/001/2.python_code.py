
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Smart Battleship AI that hunts efficiently and targets systematically.
    """
    # Helper functions
    def is_valid(r, c):
        return 0 <= r < 10 and 0 <= c < 10
    
    def get_adjacent_cells(r, c):
        """Get valid adjacent cells (up, down, left, right)"""
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        cells = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if is_valid(nr, nc) and board[nr][nc] == 0:
                cells.append((nr, nc))
        return cells
    
    def find_hit_patterns():
        """Find all hits and their connected patterns"""
        visited = set()
        hit_groups = []
        
        for r in range(10):
            for c in range(10):
                if board[r][c] == 1 and (r, c) not in visited:
                    # BFS to find connected hits
                    group = []
                    queue = [(r, c)]
                    visited.add((r, c))
                    
                    while queue:
                        cr, cc = queue.pop(0)
                        group.append((cr, cc))
                        
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = cr + dr, cc + dc
                            if is_valid(nr, nc) and board[nr][nc] == 1 and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
                    
                    hit_groups.append(group)
        
        return hit_groups
    
    def get_potential_ship_length(group):
        """Estimate minimum and maximum possible ship length for a hit group"""
        # Find bounding box
        min_r = min(r for r, c in group)
        max_r = max(r for r, c in group)
        min_c = min(c for r, c in group)
        max_c = max(c for r, c in group)
        
        # Check if horizontal, vertical, or unknown
        if min_r == max_r:  # Horizontal
            orientation = 'H'
            current_length = max_c - min_c + 1
        elif min_c == max_c:  # Vertical
            orientation = 'V'
            current_length = max_r - min_r + 1
        else:  # Diagonal (shouldn't happen but handle it)
            orientation = 'D'
            current_length = len(group)
        
        return current_length, orientation, (min_r, max_r, min_c, max_c)
    
    # Step 1: Find all hit groups
    hit_groups = find_hit_patterns()
    
    # Step 2: If we have active hits, target them
    if hit_groups:
        # Prioritize groups with fewer adjacent options (more likely to be part of a small ship)
        for group in hit_groups:
            current_length, orientation, bounds = get_potential_ship_length(group)
            
            # Get all potential cells to try around this group
            potential_cells = []
            for r, c in group:
                potential_cells.extend(get_adjacent_cells(r, c))
            
            # Remove duplicates
            potential_cells = list(set(potential_cells))
            
            if potential_cells:
                # If we have 2+ hits in a line, try extending in both directions
                if len(group) >= 2:
                    if orientation == 'H':
                        # Try left and right of the group
                        left_col = bounds[2] - 1
                        right_col = bounds[3] + 1
                        row = bounds[0]
                        
                        if is_valid(row, left_col) and board[row][left_col] == 0:
                            return (row, left_col)
                        if is_valid(row, right_col) and board[row][right_col] == 0:
                            return (row, right_col)
                    
                    elif orientation == 'V':
                        # Try up and down of the group
                        top_row = bounds[0] - 1
                        bottom_row = bounds[1] + 1
                        col = bounds[2]
                        
                        if is_valid(top_row, col) and board[top_row][col] == 0:
                            return (top_row, col)
                        if is_valid(bottom_row, col) and board[bottom_row][col] == 0:
                            return (bottom_row, col)
                
                # Otherwise, just try any adjacent cell
                return potential_cells[0]
        
        # Fallback: shouldn't reach here if we have hits and they have adjacent cells
        # but just in case, find any hit and try adjacent
        for r in range(10):
            for c in range(10):
                if board[r][c] == 1:
                    adj = get_adjacent_cells(r, c)
                    if adj:
                        return adj[0]
    
    # Step 3: Hunt mode - use a checkerboard pattern
    # We want to maximize coverage, so we'll use multiple checkerboard offsets
    # to ensure we can hit ships of various lengths efficiently
    
    # Define several checkerboard patterns
    patterns = [
        lambda r, c: (r + c) % 2 == 0,  # Standard checkerboard
        lambda r, c: (r + c) % 2 == 1,  # Alternate checkerboard
        lambda r, c: (r + 2*c) % 3 == 0,  # Three-color pattern
        lambda r, c: (r + 2*c) % 3 == 1,
        lambda r, c: (r + 2*c) % 3 == 2,
    ]
    
    # Try each pattern and return the first valid cell
    for pattern in patterns:
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0 and pattern(r, c):
                    return (r, c)
    
    # Final fallback: just find any unexplored cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # Should never reach here if board has any 0s
    raise ValueError("No legal moves available")
