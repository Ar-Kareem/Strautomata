
def policy(you, opponent) -> str:
    # Find all empty cells with their centrality (distance squared from center)
    empty = []
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                row_1 = r + 1
                col_1 = c + 1
                centrality = (row_1 - 3.5)**2 + (col_1 - 3.5)**2
                empty.append((centrality, row_1, col_1))
    
    # Sort by centrality (most central first) and select first
    empty.sort()
    placed_row, placed_col = empty[0][1], empty[0][2]
    
    # Count marbles in each quadrant
    quad_counts = [
        sum(you[r][c] for r in range(3) for c in range(3)),      # Quadrant 0
        sum(you[r][c] for r in range(3) for c in range(3, 6)),   # Quadrant 1
        sum(you[r][c] for r in range(3, 6) for c in range(3)),   # Quadrant 2
        sum(you[r][c] for r in range(3, 6) for c in range(3, 6)) # Quadrant 3
    ]
    
    # Select quadrant with most marbles (break ties with lower index)
    max_count = max(quad_counts)
    candidates = [i for i in range(4) if quad_counts[i] == max_count]
    quad = candidates[0]
    
    # Rotate clockwise
    direction = 'R'
    
    return f"{placed_row},{placed_col},{quad},{direction}"
