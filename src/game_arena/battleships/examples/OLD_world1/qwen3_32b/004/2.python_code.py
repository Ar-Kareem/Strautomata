
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Step 1: Find candidates adjacent to hits
    candidates = []
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:  # Hit detected
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < 10 and 0 <= nj < 10:
                        if board[ni][nj] == 0:
                            candidates.append((ni, nj))
    # Remove duplicates
    candidates = list(set(candidates))
    
    # Step 2: Compute probability grid
    prob_grid = [[0]*10 for _ in range(10)]
    ship_lengths = [5,4,3,3,2]
    for length in ship_lengths:
        # Check horizontal placements
        for row in range(10):
            max_col = 10 - length
            for col in range(0, max_col + 1):
                # Check if this horizontal placement is valid (no misses)
                valid = True
                for k in range(col, col + length):
                    if board[row][k] == -1:
                        valid = False
                        break
                if valid:
                    # Add to probability grid for unshot cells
                    for k in range(col, col + length):
                        if board[row][k] == 0:
                            prob_grid[row][k] += 1
        # Check vertical placements
        for col in range(10):
            max_row = 10 - length
            for row in range(0, max_row + 1):
                valid = True
                for k in range(row, row + length):
                    if board[k][col] == -1:
                        valid = False
                        break
                if valid:
                    for k in range(row, row + length):
                        if board[k][col] == 0:
                            prob_grid[k][col] += 1
    
    # Step 3: Choose cell based on candidates or max probability
    if candidates:
        # Find in candidates the cell with highest probability
        max_prob = -1
        best_cell = None
        for (i, j) in candidates:
            current_prob = prob_grid[i][j]
            if current_prob > max_prob:
                max_prob = current_prob
                best_cell = (i, j)
        return best_cell
    else:
        # Find the cell with maximum probability among unshot cells
        max_prob = -1
        best_cell = None
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    current_prob = prob_grid[i][j]
                    if current_prob > max_prob or (current_prob == max_prob and best_cell is None):
                        max_prob = current_prob
                        best_cell = (i, j)
        return best_cell
