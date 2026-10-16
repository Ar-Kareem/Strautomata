
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Step 1: Find all hit positions
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # Step 2: If there are hits, try to expand from them
    if hits:
        # Try to find a direction (horizontal or vertical) from existing hits
        # Check each hit for adjacent unfired cells that could extend a ship
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
        for (r, c) in hits:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10:
                    if board[nr][nc] == 0:  # Unfired cell
                        # Check if this cell continues a line of hits
                        # Look opposite direction: if there's a hit behind, this is continuation
                        prev_r, prev_c = r - dr, c - dc
                        if 0 <= prev_r < 10 and 0 <= prev_c < 10:
                            if board[prev_r][prev_c] == 1:
                                # This direction is already active, prioritize continuation
                                return (nr, nc)
                        # If no backward hit, this is a new front—still try, but lower priority?
                        # But try immediate neighbors of hits first
                        return (nr, nc)
        
        # If all adjacent to hits are invalid, fall back to scanning (should not happen often)
    
    # Step 3: No hits or no available adjacent cells — use a smart scanning pattern
    # Use a diagonal scan with step 2, avoiding redundant shots
    # But since smallest ship is length 2, we can skip some cells
    # Efficient: check every other cell in diagonal pattern
    # We'll sweep in an order that covers board efficiently
    for step in range(0, 20):
        for r in range(10):
            c = step - r
            if 0 <= c < 10:
                if board[r][c] == 0:
                    return (r, c)
    
    # Final fallback: scan row by row (should theoretically not be needed)
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # This should never happen if there's a valid move
    return (0, 0)
