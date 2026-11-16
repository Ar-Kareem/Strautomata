
def policy(board: list[list[int]]) -> tuple[int, int]:
    def check_winner(player):
        # Check rows and columns
        for i in range(4):
            if all(board[i][j] == player for j in range(4)) or all(board[j][i] == player for j in range(4)):
                return True
        # Check diagonals
        if all(board[i][i] == player for i in range(4)) or all(board[i][3 - i] == player for i in range(4)):
            return True
        return False

    # Check for winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1  # Try making a move
                if check_winner(1):
                    return (i, j)
                board[i][j] = 0  # Undo move

    # Block opponent's winning move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1  # Try blocking
                if check_winner(-1):
                    board[i][j] = 0  # Undo move
                    return (i, j)
                board[i][j] = 0  # Undo move

    # Priority moves: center and corners
    preferred_moves = [(1, 1), (0, 0), (0, 3), (3, 0), (3, 3)]
    for move in preferred_moves:
        if board[move[0]][move[1]] == 0:
            return move

    # If no preferred moves, just pick any available spot
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return (i, j)

    # Fallback, should never reach here if function is used correctly
    return (-1, -1)
