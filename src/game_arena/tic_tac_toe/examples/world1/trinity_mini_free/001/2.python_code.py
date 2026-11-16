
def policy(board):
    def check_win(player):
        # Check rows
        for i in range(3):
            if all(board[i][j] == player for j in range(3)):
                return True
        # Check columns
        for j in range(3):
            if all(board[i][j] == player for i in range(3)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2-i] == player for i in range(3)):
            return True
        return False

    # Check for winning moves
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_win(1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Check for blocking moves
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_win(-1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Priority-based move selection
    priority = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]
    for (i, j) in priority:
        if board[i][j] == 0:
            return (i, j)
