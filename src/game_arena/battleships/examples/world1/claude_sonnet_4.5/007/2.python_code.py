
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy using hunt-and-target strategy.
    
    Strategy:
    1. If we have aligned hits (ship direction found), continue along that line
    2. If we have isolated hits, search adjacent cells
    3. Otherwise, use checkerboard pattern for efficient search
    """
    
    # Collect all hits
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
    
    if hits:
        # Priority 1: Check if we have aligned hits and continue in that direction
        for r, c in hits:
            for dr, dc in [(0, 1), (1, 0)]:  # Check right and down only (avoid duplicates)
                # Check if there's another hit in this direction
                if (r + dr, c + dc) in hits:
                    # Found aligned hits! Continue in both directions along this line
                    
                    # Search forward along the line
                    nr, nc = r + dr, c + dc
                    while 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                        nr, nc = nr + dr, nc + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        return (nr, nc)
                    
                    # Search backward along the line
                    nr, nc = r - dr, c - dc
                    while 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                        nr, nc = nr - dr, nc - dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        return (nr, nc)
        
        # Priority 2: No aligned hits found, explore around isolated hits
        for r, c in hits:
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # Priority 3: No active targets, use checkerboard search pattern
    # This is optimal because smallest ship is length 2
    for r in range(10):
        for c in range(10):
            if (r + c) % 2 == 0 and board[r][c] == 0:
                return (r, c)
    
    # Priority 4: Fill in remaining odd-parity cells
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # Should never reach here in a valid game
    return (0, 0)
