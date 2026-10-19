
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Targeting Phase: Find all candidate cells adjacent to hits
    hits = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))
    
    target_candidates = []
    for i, j in hits:
        for dx, dy in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
            x, y = i + dx, j + dy
            if 0 <= x < 10 and 0 <= y < 10 and board[x][y] == 0:
                target_candidates.append((x, y))
    
    if target_candidates:
        max_adj_hits = -1
        best_candidate = None
        best_dist = float('inf')
        for x, y in target_candidates:
            adj_hits = 0
            for dx2, dy2 in [(-1, 0), (1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx2, y + dy2
                if 0 <= nx < 10 and 0 <= ny < 10 and board[nx][ny] == 1:
                    adj_hits += 1
            dist = (x - 5)**2 + (y - 5)**2  # Distance to center
            if adj_hits > max_adj_hits or (adj_hits == max_adj_hits and dist < best_dist):
                max_adj_hits = adj_hits
                best_candidate = (x, y)
                best_dist = dist
        return best_candidate
    
    # Hunting Phase: Checkerboard pattern with even parity, closest to center first
    hunting_cells = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0 and (i + j) % 2 == 0:
                hunting_cells.append((i, j))
    
    # If no even parity cells, switch to odd parity
    if not hunting_cells:
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0 and (i + j) % 2 == 1:
                    hunting_cells.append((i, j))
    
    # Find the closest to center
    if hunting_cells:
        best_cell = None
        min_dist = float('inf')
        for x, y in hunting_cells:
            dist = (x - 5)**2 + (y - 5)**2
            if dist < min_dist:
                min_dist = dist
                best_cell = (x, y)
        return best_cell
    
    # Fallback: Shouldn't be reached in valid games
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)  # All cells covered (unlikely)
