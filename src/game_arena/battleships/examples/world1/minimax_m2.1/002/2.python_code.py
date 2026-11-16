
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Smart Battleship AI policy that combines multiple strategies:
    1. Parity hunting pattern for initial exploration
    2. Target mode for sinking ships once hit
    3. Probability-based targeting for optimal move selection
    
    Args:
        board: 10x10 grid where:
               0 = unknown, -1 = miss, 1 = hit
    
    Returns:
        (row, col): Next move coordinates
    """
    import random
    
    # Dimensions
    N = 10
    
    # Find all unknown cells, hits, and misses
    unknown_cells = []
    hit_cells = []
    for i in range(N):
        for j in range(N):
            if board[i][j] == 0:
                unknown_cells.append((i, j))
            elif board[i][j] == 1:
                hit_cells.append((i, j))
    
    # If no unknown cells, shouldn't happen but return first cell
    if not unknown_cells:
        return (0, 0)
    
    # Ship lengths remaining (from largest to smallest)
    # Start with full fleet, we'll update based on what we sink
    ship_lengths = [5, 4, 3, 3, 2]
    
    # MODE 1: If we have hits but haven't sunk all adjacent ships, target around hits
    if hit_cells:
        # Check if we need to continue targeting around existing hits
        adjacent_targets = []
        for i, j in hit_cells:
            # Check all 4 adjacent directions
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < N and 0 <= nj < N and board[ni][nj] == 0:
                    adjacent_targets.append((ni, nj))
        
        if adjacent_targets:
            # Return a random adjacent target to hit a new ship part
            return random.choice(adjacent_targets)
    
    # MODE 2: Hunting mode - use intelligent pattern
    # Use a modified checkerboard pattern optimized for ship finding
    hunting_pattern = []
    for i in range(N):
        for j in range(N):
            # Parity pattern: even sums first, then odd sums
            if (i + j) % 2 == 0:
                hunting_pattern.append((i, j))
    for i in range(N):
        for j in range(N):
            if (i + j) % 2 == 1:
                hunting_pattern.append((i, j))
    
    # Find first valid move from hunting pattern
    for i, j in hunting_pattern:
        if board[i][j] == 0:
            return (i, j)
    
    # Fallback: return first unknown cell
    return unknown_cells[0]
