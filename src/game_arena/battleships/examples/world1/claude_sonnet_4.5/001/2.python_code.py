
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy.
    
    Strategy:
    1. If we have hits, enter "target mode" - explore adjacent cells
    2. Prioritize extending lines of consecutive hits
    3. Otherwise, use checkerboard pattern for efficient hunting
    """
    
    # Collect all hit positions
    hits = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.add((r, c))
    
    # Target mode: we have hits to follow up on
    if hits:
        # Priority 1: Extend known lines of hits
        for r, c in hits:
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in hits:
                    # Found adjacent hits - we have a line
                    # Try extending forward
                    ext_r, ext_c = nr + dr, nc + dc
                    if 0 <= ext_r < 10 and 0 <= ext_c < 10 and board[ext_r][ext_c] == 0:
                        return (ext_r, ext_c)
                    # Try extending backward
                    ext_r, ext_c = r - dr, c - dc
                    if 0 <= ext_r < 10 and 0 <= ext_c < 10 and board[ext_r][ext_c] == 0:
                        return (ext_r, ext_c)
        
        # Priority 2: Explore cells adjacent to any hit
        for r, c in hits:
            for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # Hunt mode: use checkerboard pattern
    # Since smallest ship is size 2, every ship covers at least one checkerboard cell
    for r in range(10):
        for c in range(10):
            if (r + c) % 2 == 0 and board[r][c] == 0:
                return (r, c)
    
    # Fill in remaining odd-parity cells
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # Fallback (should never reach here in valid game)
    return (0, 0)
