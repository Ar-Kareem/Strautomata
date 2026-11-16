
def policy(board: list[list[int]]) -> tuple[int, int]:
    empty = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # Check for winning move
    for i, j in empty:
        # Check row
        if sum(1 for x in range(3) if board[i][x] == 1) == 2:
            return (i, j)
        # Check column
        if sum(1 for x in range(3) if board[x][j] == 1) == 2:
            return (i, j)
        # Check diagonal (main)
        if i == j and sum(1 for x in range(3) if board[x][x] == 1) == 2:
            return (i, j)
        # Check anti-diagonal
        if i + j == 2 and sum(1 for x in range(3) if board[x][2 - x] == 1) == 2:
            return (i, j)
    
    # Check for blocking opponent's win
    for i, j in empty:
        if sum(1 for x in range(3) if board[i][x] == -1) == 2:
            return (i, j)
        if sum(1 for x in range(3) if board[x][j] == -1) == 2:
            return (i, j)
        if i == j and sum(1 for x in range(3) if board[x][x] == -1) == 2:
            return (i, j)
        if i + j == 2 and sum(1 for x in range(3) if board[x][2 - x] == -1) == 2:
            return (i, j)
    
    # Default strategy (center > corners > edges)
    priority = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (2, 1), (1, 2)]
    for move in priority:
        if board[move[0]][move[1]] == 0:
            return move
    
    return empty[0]
