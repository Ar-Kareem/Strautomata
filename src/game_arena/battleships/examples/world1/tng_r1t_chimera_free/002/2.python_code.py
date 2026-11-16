
import math

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Collect all candidate cells adjacent to hits
    candidates = set()
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 0:
                        candidates.add((ni, nj))
    
    if candidates:
        # Score each candidate based on adjacent hits and distance from center
        scored = []
        center = (4.5, 4.5)
        for (i, j) in candidates:
            score = 0
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + dx, j + dy
                if 0 <= ni < 10 and 0 <= nj < 10 and board[ni][nj] == 1:
                    score += 1
            distance = math.hypot(i - center[0], j - center[1])
            scored.append((-score, distance, i, j))
        
        # Sort by score (descending), then distance (ascending)
        scored.sort()
        return (scored[0][2], scored[0][3])
    
    # Search pattern: prioritize even (i+j) cells, closer to center first
    search_list = []
    center = (4.5, 4.5)
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                parity = (i + j) % 2
                distance = math.hypot(i - center[0], j - center[1])
                search_list.append((parity, distance, i, j))
    
    # Sort by parity (even first), then distance
    search_list.sort()
    if search_list:
        return (search_list[0][2], search_list[0][3])
    
    # Fallback: any remaining cell (shouldn't reach here in valid game)
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)
