
import collections

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Convert stone positions to a 19x19 grid
    grid = [[0] * 19 for _ in range(19)]
    for (r, c) in me:
        grid[r-1][c-1] = 1
    for (r, c) in opponent:
        grid[r-1][c-1] = 2
    
    # Generate all possible moves (including pass)
    moves = [(r, c) for r in range(1, 20) for c in range(1, 20)]
    moves.append((0, 0))
    
    best_move = None
    best_score = -float('inf')
    
    for move in moves:
        r, c = move
        if r == 0 and c == 0:  # Pass is always legal
            legal = True
        else:
            if grid[r-1][c-1] != 0:  # Not an empty point
                continue
            # Place stone temporarily
            grid[r-1][c-1] = 1
            # Check for self-capture
            legal = not any(group_has_zero_liberties(grid, 1))
            grid[r-1][c-1] = 0  # Undo move
        
        if not legal:
            continue
        
        # Simulate move and capture opponent stones
        grid[r-1][c-1] = 1
        grid = capture_stones(grid)
        score = evaluate_board(grid)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
        
        grid[r-1][c-1] = 0  # Undo move
    
    return (best_move, memory)

def group_has_zero_liberties(grid, player):
    """Check if any group of `player` has zero liberties"""
    visited = [[False] * 19 for _ in range(19)]
    for i in range(19):
        for j in range(19):
            if grid[i][j] == player and not visited[i][j]:
                group = []
                queue = collections.deque([(i, j)])
                visited[i][j] = True
                while queue:
                    x, y = queue.popleft()
                    group.append((x, y))
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and not visited[nx][ny] and grid[nx][ny] == player:
                            visited[nx][ny] = True
                            queue.append((nx, ny))
                # Check liberties
                for (x, y) in group:
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and grid[nx][ny] == 0:
                            break
                else:
                    return True
    return False

def capture_stones(grid):
    """Remove opponent stones with zero liberties"""
    visited = [[False] * 19 for _ in range(19)]
    for i in range(19):
        for j in range(19):
            if grid[i][j] == 2 and not visited[i][j]:
                group = []
                queue = collections.deque([(i, j)])
                visited[i][j] = True
                while queue:
                    x, y = queue.popleft()
                    group.append((x, y))
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and not visited[nx][ny] and grid[nx][ny] == 2:
                            visited[nx][ny] = True
                            queue.append((nx, ny))
                # Check liberties
                for (x, y) in group:
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and grid[nx][ny] == 0:
                            break
                else:
                    for (x, y) in group:
                        grid[x][y] = 0
    return grid

def evaluate_board(grid):
    """Evaluate board state using heuristic scoring"""
    visited = [[False] * 19 for _ in range(19)]
    opponent_score = 0
    my_score = 0
    
    # Score opponent groups with 1 liberty
    for i in range(19):
        for j in range(19):
            if grid[i][j] == 2 and not visited[i][j]:
                group = []
                queue = collections.deque([(i, j)])
                visited[i][j] = True
                while queue:
                    x, y = queue.popleft()
                    group.append((x, y))
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and not visited[nx][ny] and grid[nx][ny] == 2:
                            visited[nx][ny] = True
                            queue.append((nx, ny))
                liberties = 0
                for (x, y) in group:
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and grid[nx][ny] == 0:
                            liberties += 1
                if liberties == 1:
                    opponent_score += 10
    
    # Score my groups (size - liberties)
    for i in range(19):
        for j in range(19):
            if grid[i][j] == 1 and not visited[i][j]:
                group = []
                queue = collections.deque([(i, j)])
                visited[i][j] = True
                while queue:
                    x, y = queue.popleft()
                    group.append((x, y))
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and not visited[nx][ny] and grid[nx][ny] == 1:
                            visited[nx][ny] = True
                            queue.append((nx, ny))
                size = len(group)
                liberties = 0
                for (x, y) in group:
                    for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 19 and 0 <= ny < 19 and grid[nx][ny] == 0:
                            liberties += 1
                my_score += size - liberties
    
    return my_score - opponent_score
