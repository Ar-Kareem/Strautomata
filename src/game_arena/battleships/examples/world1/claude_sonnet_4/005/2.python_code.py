
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Find unfired cells and hits
    unfired = []
    hits = []
    
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                unfired.append((i, j))
            elif board[i][j] == 1:
                hits.append((i, j))
    
    # Priority 1: Continue attacking along known ship orientations
    for hit_r, hit_c in hits:
        # Check if this hit is part of a line of hits (horizontal or vertical)
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        
        for dr, dc in directions:
            # Look for adjacent hits in this direction
            nr, nc = hit_r + dr, hit_c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                # Found a line! Continue in both directions
                # First try extending the line
                r, c = nr, nc
                while 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 1:
                    r, c = r + dr, c + dc
                
                if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
                    return (r, c)
                
                # Try the opposite direction from the original hit
                r, c = hit_r - dr, hit_c - dc
                if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
                    return (r, c)
    
    # Priority 2: Attack adjacent to isolated hits
    for hit_r, hit_c in hits:
        # Check if this is an isolated hit (no adjacent hits)
        adjacent_hits = 0
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = hit_r + dr, hit_c + dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                adjacent_hits += 1
        
        if adjacent_hits == 0:  # Isolated hit
            # Target adjacent unfired cells
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = hit_r + dr, hit_c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # Priority 3: Use checkerboard pattern for search
    # This is efficient because ships are at least 2 cells long
    checkerboard_unfired = [(r, c) for r, c in unfired if (r + c) % 2 == 0]
    if checkerboard_unfired:
        # Pick the one closest to center for better distribution
        center_r, center_c = 4.5, 4.5
        best_cell = min(checkerboard_unfired, 
                       key=lambda pos: (pos[0] - center_r)**2 + (pos[1] - center_c)**2)
        return best_cell
    
    # Priority 4: Fill in remaining cells
    if unfired:
        return unfired[0]
    
    # Should never reach here in a valid game
    return (0, 0)
