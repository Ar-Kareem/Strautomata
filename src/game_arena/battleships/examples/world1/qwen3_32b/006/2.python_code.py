
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Generate candidates for the targeting phase
    candidates = set()
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:  # Hit detected
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:  # Up, Down, Left, Right
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                        candidates.add((ni, nj))
    if candidates:
        # Sort by row-major order for tie-breaking
        candidates = sorted(candidates, key=lambda p: (p[0], p[1]))
        best_score = -1
        best_candidate = None
        for x, y in candidates:
            # Calculate max ship length if this cell were hit
            count_left = 0
            j = y - 1
            while j >= 0 and board[x][j] == 1:
                count_left += 1
                j -= 1
            count_right = 0
            j = y + 1
            while j < 10 and board[x][j] == 1:
                count_right += 1
                j += 1
            count_up = 0
            i = x - 1
            while i >= 0 and board[i][y] == 1:
                count_up += 1
                i -= 1
            count_down = 0
            i = x + 1
            while i < 10 and board[i][y] == 1:
                count_down += 1
                i += 1
            max_len = max(count_left, count_right, count_up, count_down) + 1
            if max_len > best_score:
                best_score = max_len
                best_candidate = (x, y)
        return best_candidate
    else:
        # Compute probability grid for the hunting phase
        prob_grid = [[0] * 10 for _ in range(10)]
        ship_lengths = [5, 4, 3, 3, 2]
        for L in ship_lengths:
            # Horizontal placements
            for i in range(10):
                for j in range(10 - L + 1):
                    valid = True
                    for dj in range(L):
                        if board[i][j + dj] == -1:
                            valid = False
                            break
                    if valid:
                        for dj in range(L):
                            ni, nj = i, j + dj
                            if board[ni][nj] == 0:
                                prob_grid[ni][nj] += 1
            # Vertical placements
            for j in range(10):
                for i in range(10 - L + 1):
                    valid = True
                    for di in range(L):
                        if board[i + di][j] == -1:
                            valid = False
                            break
                    if valid:
                        for di in range(L):
                            ni, nj = i + di, j
                            if board[ni][nj] == 0:
                                prob_grid[ni][nj] += 1
        # Find cell with max probability (row-major tie-breaker)
        max_prob = -1
        best_cell = (0, 0)
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    if prob_grid[i][j] > max_prob:
                        max_prob = prob_grid[i][j]
                        best_cell = (i, j)
                    elif prob_grid[i][j] == max_prob:
                        if i < best_cell[0] or (i == best_cell[0] and j < best_cell[1]):
                            best_cell = (i, j)
        return best_cell
