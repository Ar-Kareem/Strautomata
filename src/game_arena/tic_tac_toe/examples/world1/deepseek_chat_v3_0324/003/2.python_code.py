
def policy(board: list[list[int]]) -> tuple[int, int]:
    # First check if we can win in the next move
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Test if placing here would win
                board[i][j] = 1
                if is_win(board, 1):
                    board[i][j] = 0  # undo test move
                    return (i, j)
                board[i][j] = 0  # undo test move

    # Check if opponent can win next move and block them
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = -1
                if is_win(board, -1):
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0

    # Try to take the center if available
    if board[1][1] == 0:
        return (1, 1)

    # Try to take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if board[i][j] == 0:
            return (i, j)

    # Take any remaining edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for i, j in edges:
        if board[i][j] == 0:
            return (i, j)

    # Should never get here in valid game
    return (0, 0)

def is_win(board, player):
    # Check rows
    for row in range(3):
        if all(board[row][col] == player for col in range(3)):
            return True
    # Check columns
    for col in range(3):
        if all(board[row][col] == player for row in range(3)):
            return True
    # Check diagonals
    if board[0][0] == player and board[1][1] == player and board[2][2] == player:
        return True
    if board[0][2] == player and board[1][1] == player and board[2][0] == player:
        return True
    return False
