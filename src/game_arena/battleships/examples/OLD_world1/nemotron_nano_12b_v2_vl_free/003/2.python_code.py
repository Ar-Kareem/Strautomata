
def policy(board):
    # Find all candidate cells adjacent to hits and calculate their score
    candidates = []
    for i in range(10):
        for j in range(10):
            if board[i][j] != 0:
                continue  # Skip known cells (hits or misses)
            score = 0
            # Check adjacent cells for hits
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                x, y = i + dx, j + dy
                if 0 <= x < 10 and 0 <= y < 10 and board[x][y] == 1:
                    score += 1
            candidates.append((-score, i, j))  # Negative for min-heap effect

    # If there are candidates, choose the one with the highest priority
    if candidates:
        candidates.sort()
        _, row, col = candidates[0]
        return (row, col)
    else:
        # Fallback: select the first unknown cell in row-major order
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    return (i, j)
    # Fallback to (0,0) if all else fails (shouldn't happen)
    return (0, 0)
