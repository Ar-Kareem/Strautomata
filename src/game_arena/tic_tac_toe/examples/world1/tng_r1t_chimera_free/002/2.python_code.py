
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Check for immediate win
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Check row, column, and diagonals after placing 1
                row = sum(board[i])
                col = sum(board[x][j] for x in range(3))
                diag1 = sum(board[x][x] for x in range(3)) if i == j else 0
                diag2 = sum(board[x][2-x] for x in range(3)) if i + j == 2 else 0
                if row == 2 or col == 2 or diag1 == 2 or diag2 == 2:
                    return (i, j)
    
    # Block opponent's immediate win
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                row = sum(board[i])
                col = sum(board[x][j] for x in range(3))
                diag1 = sum(board[x][x] for x in range(3)) if i == j else 0
                diag2 = sum(board[x][2-x] for x in range(3)) if i + j == 2 else 0
                if row == -2 or col == -2 or diag1 == -2 or diag2 == -2:
                    return (i, j)
    
    # Take center if available
    if board[1][1] == 0:
        return (1, 1)
    
    # Take any corner
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)
    
    # Take any edge
    edges = [(0,1), (1,0), (1,2), (2,1)]
    for i, j in edges:
        if board[i][j] == 0:
            return (i, j)
    
    # Default (shouldn't be reached in valid game)
    return (0, 0)
