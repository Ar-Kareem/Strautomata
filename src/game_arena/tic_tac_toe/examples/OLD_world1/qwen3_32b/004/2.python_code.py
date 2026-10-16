
def policy(board: list[list[int]]) -> tuple[int, int]:
    def is_win(player):
        # Check rows
        for row in board:
            if all(cell == player for cell in row):
                return True
        # Check columns
        for col in range(3):
            if all(board[row][col] == player for row in range(3)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2 - i] == player for i in range(3)):
            return True
        return False

    # Check for winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                if is_win(1):
                    board[i][j] = 0
                    return (i, j)
                else:
                    board[i][j] = 0
    # Check for opponent's winning move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if is_win(-1):
                    board[i][j] = 0
                    return (i, j)
                else:
                    board[i][j] = 0
    # Choose center if available
    if board[1][1] == 0:
        return (1, 1)
    # Check corners
    for (x, y) in [(0, 0), (0, 2), (2, 0), (2, 2)]:
        if board[x][y] == 0:
            return (x, y)
    # Check edges
    for (x, y) in [(0, 1), (1, 0), (1, 2), (2, 1)]:
        if board[x][y] == 0:
            return (x, y)
