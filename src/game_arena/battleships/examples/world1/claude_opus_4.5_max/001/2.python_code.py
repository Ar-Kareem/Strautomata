
def policy(board: list[list[int]]) -> tuple[int, int]:
    ROWS, COLS = 10, 10
    SHIPS = [5, 4, 3, 3, 2]
    
    def in_bounds(r, c):
        return 0 <= r < ROWS and 0 <= c < COLS
    
    # ===== TARGET MODE =====
    # Find the best cell to shoot adjacent to existing hits
    best_target = None
    best_priority = -1
    
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != 1:
                continue
            
            # Check each direction from this hit
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                
                # Skip if out of bounds or not unknown
                if not in_bounds(nr, nc) or board[nr][nc] != 0:
                    continue
                
                # Count consecutive hits in the opposite direction
                line_len = 1
                br, bc = r - dr, c - dc
                while in_bounds(br, bc) and board[br][bc] == 1:
                    line_len += 1
                    br, bc = br - dr, bc - dc
                
                # Update best target if this has higher priority
                if line_len > best_priority:
                    best_priority = line_len
                    best_target = (nr, nc)
    
    if best_target:
        return best_target
    
    # ===== HUNT MODE =====
    # Calculate probability density for each unknown cell
    prob = [[0] * COLS for _ in range(ROWS)]
    
    for ship_len in SHIPS:
        # Try horizontal placements
        for r in range(ROWS):
            for c in range(COLS - ship_len + 1):
                # Check if placement is valid (no miss cells)
                if all(board[r][c + i] != -1 for i in range(ship_len)):
                    for i in range(ship_len):
                        if board[r][c + i] == 0:
                            prob[r][c + i] += 1
        
        # Try vertical placements
        for r in range(ROWS - ship_len + 1):
            for c in range(COLS):
                if all(board[r + i][c] != -1 for i in range(ship_len)):
                    for i in range(ship_len):
                        if board[r + i][c] == 0:
                            prob[r + i][c] += 1
    
    # Find the best cell with highest probability
    # Tie-breaker: prefer cells closer to the center
    best_cell = None
    best_prob = -1
    best_dist = float('inf')
    
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] != 0:
                continue
            
            dist = abs(r - 4.5) + abs(c - 4.5)
            
            if prob[r][c] > best_prob or (prob[r][c] == best_prob and dist < best_dist):
                best_prob = prob[r][c]
                best_dist = dist
                best_cell = (r, c)
    
    if best_cell:
        return best_cell
    
    # Fallback: return any unknown cell
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)
