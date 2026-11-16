
def policy(board: list[list[int]]) -> tuple[int, int]:
    lines = [
        # Rows
        [(0,0), (0,1), (0,2)],
        [(1,0), (1,1), (1,2)],
        [(2,0), (2,1), (2,2)],
        # Columns
        [(0,0), (1,0), (2,0)],
        [(0,1), (1,1), (2,1)],
        [(0,2), (1,2), (2,2)],
        # Diagonals
        [(0,0), (1,1), (2,2)],
        [(0,2), (1,1), (2,0)],
    ]

    # Check for immediate win
    for line in lines:
        values = [board[i][j] for (i,j) in line]
        if sum(values) == 2 and 0 in values:
            for (i,j) in line:
                if board[i][j] == 0:
                    return (i,j)
    
    # Check for opponent's immediate win
    for line in lines:
        values = [board[i][j] for (i,j) in line]
        if sum(values) == -2 and 0 in values:
            for (i,j) in line:
                if board[i][j] == 0:
                    return (i,j)
    
    # Take center if available
    if board[1][1] == 0:
        return (1,1)
    
    # Take corners
    corners = [(0,0), (0,2), (2,0), (2,2)]
    for (i,j) in corners:
        if board[i][j] == 0:
            return (i,j)
    
    # Take edges
    edges = [(0,1), (1,0), (1,2), (2,1)]
    for (i,j) in edges:
        if board[i][j] == 0:
            return (i,j)
    
    # Fallback (shouldn't be reached in valid game states)
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                return (i,j)
    return (0,0)
