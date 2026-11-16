
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Simulate placing a marker here
                temp = [row.copy() for row in board]
                temp[i][j] = 1
                # Check all possible lines for a win
                lines = [
                    [temp[0][0], temp[0][1], temp[0][2]],  # Row 0
                    [temp[1][0], temp[1][1], temp[1][2]],  # Row 1
                    [temp[2][0], temp[2][1], temp[2][2]],  # Row 2
                    [temp[0][0], temp[1][0], temp[2][0]],  # Column 0
                    [temp[0][1], temp[1][1], temp[2][1]],  # Column 1
                    [temp[0][2], temp[1][2], temp[2][2]],  # Column 2
                    [temp[0][0], temp[1][1], temp[2][2]],  # Diagonal 1
                    [temp[0][2], temp[1][1], temp[2][0]]   # Diagonal 2
                ]
                if any(all(cell == 1 for cell in line) for line in lines):
                    return (i, j)
    
    # Check for blocking opponent's win
    lines = [
        [(0,0), (0,1), (0,2)],  # Rows
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        [(0,0), (1,0), (2,0)],  # Columns
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        [(0,0), (1,1), (2,2)],  # Diagonals
        [(0,2), (1,1), (2,0)]
    ]
    for line in lines:
        count_opp = 0
        block_pos = None
        for x, y in line:
            if board[x][y] == -1:
                count_opp += 1
            elif board[x][y] == 0:
                block_pos = (x, y)
        if count_opp == 2 and block_pos is not None:
            return block_pos
    
    # Strategic moves: center > corners > edges
    if board[1][1] == 0:
        return (1, 1)
    # Check corners
    for corner in [(0,0), (0,2), (2,0), (2,2)]:
        if board[corner[0]][corner[1]] == 0:
            return corner
    # Check edges
    for edge in [(0,1), (1,0), (1,2), (2,1)]:
        if board[edge[0]][edge[1]] == 0:
            return edge
    
    # Fallback (should never be reached as board is full)
    return (-1, -1)
