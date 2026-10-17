
import collections

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Create a 11x11 grid representation
    grid = [[0] * 11 for _ in range(11)]
    for (i, j) in me:
        grid[i][j] = 1  # Player's stones
    for (i, j) in opp:
        grid[i][j] = 2  # Opponent's stones
    
    # Directions for adjacency (hex grid neighbors)
    dirs = [(-1, 0), (-1, 1), (0, 1), (1, 0), (1, -1), (0, -1)]
    
    # Compute original connected components of player's stones
    def compute_components(grid):
        visited = [[False] * 11 for _ in range(11)]
        components = 0
        for i in range(11):
            for j in range(11):
                if grid[i][j] == 1 and not visited[i][j]:
                    components += 1
                    queue = collections.deque([(i, j)])
                    visited[i][j] = True
                    while queue:
                        x, y = queue.popleft()
                        for dx, dy in dirs:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 11 and 0 <= ny < 11 and grid[nx][ny] == 1 and not visited[nx][ny]:
                                visited[nx][ny] = True
                                queue.append((nx, ny))
        return components
    
    orig_components = compute_components(grid)
    
    # Check for moves that connect two player groups
    best_move = None
    for i in range(11):
        for j in range(11):
            if grid[i][j] != 0:
                continue
            new_grid = [row[:] for row in grid]
            new_grid[i][j] = 1
            new_components = compute_components(new_grid)
            if new_components < orig_components:
                best_move = (i, j)
                break
        if best_move:
            break
    
    # If no connecting move, block opponent's potential connection
    if not best_move:
        for i in range(11):
            for j in range(11):
                if grid[i][j] != 0:
                    continue
                # Count adjacent opponent stones
                count_opp = 0
                for dx, dy in dirs:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 11 and 0 <= nj < 11 and grid[ni][nj] == 2:
                        count_opp += 1
                # Count adjacent player stones
                count_me = 0
                for dx, dy in dirs:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 11 and 0 <= nj < 11 and grid[ni][nj] == 1:
                        count_me += 1
                # Prefer moves blocking opponent over extending player
                if count_opp > 0 and (best_move is None or count_opp > count_opp_best):
                    best_move = (i, j)
                    count_opp_best = count_opp
                    count_me_best = count_me
            if best_move:
                break
    
    # If no blocking move, extend player's connections
    if not best_move:
        for i in range(11):
            for j in range(11):
                if grid[i][j] != 0:
                    continue
                count_me = 0
                for dx, dy in dirs:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 11 and 0 <= nj < 11 and grid[ni][nj] == 1:
                        count_me += 1
                if best_move is None or count_me > count_me_best:
                    best_move = (i, j)
                    count_me_best = count_me
    
    return best_move if best_move else (0, 0)
