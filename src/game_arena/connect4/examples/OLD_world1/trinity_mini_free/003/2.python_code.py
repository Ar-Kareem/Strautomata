
def policy(board: list[list[int]]) -> int:
    rows = 6
    cols = 7
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    # Check for winning moves
    for i in range(rows):
        for j in range(cols):
            if board[i][j] == 0:
                for dx, dy in directions:
                    count = 0
                    for step in range(1, 4):
                        ni = i + dx * step
                        nj = j + dy * step
                        if 0 <= ni < rows and 0 <= nj < cols:
                            if board[ni][nj] == 1:
                                count += 1
                        else:
                            break
                    if count == 3:
                        return j
    
    # Check for blocking moves
    for i in range(rows):
        for j in range(cols):
            if board[i][j] == 0:
                for dx, dy in directions:
                    count = 0
                    for step in range(1, 4):
                        ni = i + dx * step
                        nj = j + dy * step
                        if 0 <= ni < rows and 0 <= nj < cols:
                            if board[ni][nj] == -1:
                                count += 1
                        else:
                            break
                    if count == 3:
                        return j
    
    # Heuristic: prioritize center columns (2, 3, 4) then edges (1, 5) then corners (0, 6)
    for col in [3, 2, 4, 1, 5, 0, 6]:
        for i in range(rows - 1, -1, -1):
            if board[i][col] == 0:
                return col
    
    return 0
