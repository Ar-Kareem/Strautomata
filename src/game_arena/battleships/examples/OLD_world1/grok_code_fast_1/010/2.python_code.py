
def policy(board: list[list[int]]) -> tuple[int, int]:
    n = 10
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    candidates = set()
    
    # Find potential targets near hits
    for i in range(n):
        for j in range(n):
            if board[i][j] == 1:
                for di, dj in directions:
                    ni, nj = i + di, j + dj
                    if 0 <= ni < n and 0 <= nj < n and board[ni][nj] == 0:
                        candidates.add((ni, nj))
    
    # Prioritize potential targets
    if candidates:
        return min(candidates)
    
    # Otherwise, hunt mode: shoot the top-left unknown cell
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0:
                return (i, j)
