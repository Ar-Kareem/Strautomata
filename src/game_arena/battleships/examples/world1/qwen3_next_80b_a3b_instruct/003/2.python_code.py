
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define directions: up, down, left, right
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    # Find all hits (value == 1)
    hits = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))
    
    # If there are any hits, try to target adjacent unknown cells
    if hits:
        # For each hit, check adjacent cells for unknowns
        candidates = []
        for hit_row, hit_col in hits:
            for dr, dc in directions:
                nr, nc = hit_row + dr, hit_col + dc
                if 0 <= nr < 10 and 0 <= nc < 10:
                    if board[nr][nc] == 0:  # unknown, not fired yet
                        candidates.append((nr, nc))
        
        # If we have adjacent candidates, pick one
        if candidates:
            # Choose the first candidate (could be improved with probability, but simple is safe)
            return candidates[0]
    
    # If no adjacent candidates, or no hits at all, use checkerboard search
    # Only target cells where (row + col) % 2 == 0 to reduce search space by half
    # (Since any ship of length >=2 must cover at least one such cell)
    candidates = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:  # unknown cell
                if (i + j) % 2 == 0:  # checkerboard pattern
                    candidates.append((i, j))
    
    # If no checkerboard candidates exist (unlikely), fallback to any unknown
    if not candidates:
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    return (i, j)
    
    # Return the first candidate (deterministic for consistency)
    return candidates[0]
