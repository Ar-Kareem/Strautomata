
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect all unshot cells (0s)
    unshot = [ (r, c) for r in range(10) for c in range(10) if board[r][c] == 0 ]
    
    # Check for cells adjacent to existing hits (exploitation)
    candidates = []
    for (r, c) in unshot:
        hit_adjacent = False
        hit_count = 0  # Count adjacent hits for prioritization
        
        # Check up
        if r > 0 and board[r-1][c] == 1:
            hit_adjacent = True
            hit_count += 1
        # Check down
        if r < 9 and board[r+1][c] == 1:
            hit_adjacent = True
            hit_count += 1
        # Check left
        if c > 0 and board[r][c-1] == 1:
            hit_adjacent = True
            hit_count += 1
        # Check right
        if c < 9 and board[r][c+1] == 1:
            hit_adjacent = True
            hit_count += 1
        
        if hit_adjacent:
            # Store negative hit count for descending sort
            candidates.append( (-hit_count, r, c) )
    
    # Prioritize cells with the most adjacent hits
    if candidates:
        candidates.sort()  # Sorts by (-count, r, c) → highest count first
        return (candidates[0][1], candidates[0][2])
    
    # Exploration phase: use checkerboard pattern
    # Sort by (r+c) parity, then row, then column
    unshot_sorted = sorted(unshot, key=lambda cell: ((cell[0] + cell[1]) % 2, cell[0], cell[1]))
    return unshot_sorted[0]
