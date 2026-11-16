
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Ship lengths: one of each
    ship_sizes = [5, 4, 3, 3, 2]
    
    # Grid size
    n = 10
    
    # Initialize a score grid to count valid placements covering each cell
    score = [[0] * n for _ in range(n)]
    
    # For each ship size
    for size in ship_sizes:
        # Horizontal placements
        for r in range(n):
            for c in range(n - size + 1):
                # Check if placing ship at (r, c) to (r, c+size-1) is valid
                valid = True
                for dc in range(size):
                    if board[r][c + dc] == -1:  # miss, cannot place ship here
                        valid = False
                        break
                if not valid:
                    continue
                # If valid, increment score for each cell in this segment
                for dc in range(size):
                    score[r][c + dc] += 1
        
        # Vertical placements
        for r in range(n - size + 1):
            for c in range(n):
                valid = True
                for dr in range(size):
                    if board[r + dr][c] == -1:  # miss
                        valid = False
                        break
                if not valid:
                    continue
                for dr in range(size):
                    score[r + dr][c] += 1
    
    # Now, find unshot cells (board[r][c] == 0) with highest score
    best_score = -1
    best_cell = None
    
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:  # haven't shot here
                if score[r][c] > best_score:
                    best_score = score[r][c]
                    best_cell = (r, c)
    
    # If no unshot cell found (shouldn't happen in valid game), fallback
    if best_cell is None:
        # Find any unshot cell
        for r in range(n):
            for c in range(n):
                if board[r][c] == 0:
                    return (r, c)
    
    return best_cell
