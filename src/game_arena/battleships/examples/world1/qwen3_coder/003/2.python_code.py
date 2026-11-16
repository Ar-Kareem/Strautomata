
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to tuples for easier handling
    board = [tuple(row) for row in board]
    
    # Find all hit positions (value = 1)
    hits = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
    
    # If we have hits, look for adjacent unknown cells to continue the attack
    if hits:
        # For each hit, check adjacent cells
        for r, c in hits:
            # Check in all four directions
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                # Check if the adjacent cell is within bounds and unknown
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # If no hits to follow up on or no hits at all, use checkerboard pattern for efficiency
    # This prioritizes cells that could contain ships based on their lengths
    # Even row + even col OR odd row + odd col pattern increases chances of hitting ships
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:  # unknown cell
                # Prefer checkerboard pattern
                if (r + c) % 2 == 0:
                    return (r, c)
    
    # Fallback to any unknown cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    # This should never happen in a valid game
    raise RuntimeError("No valid moves available")
