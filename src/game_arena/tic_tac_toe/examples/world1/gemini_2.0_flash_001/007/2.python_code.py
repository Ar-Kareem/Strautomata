
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a 3x3 Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of two integers (0-2, 0-2) indicating the row and column you choose.
    """

    # 1. Win if possible
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1  # Temporarily make the move
                if check_win(board, 1):
                    return (row, col)
                board[row][col] = 0  # Undo the move

    # 2. Block if necessary
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1  # Temporarily make the move for the opponent
                if check_win(board, -1):
                    return (row, col)
                board[row][col] = 0  # Undo the move

    # 3. Take the center
    if board[1][1] == 0:
        return (1, 1)

    # 4. Take a corner
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for row, col in corners:
        if board[row][col] == 0:
            return (row, col)

    # 5. Take any available space
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                return (row, col)

    # If no moves are available (shouldn't happen in a valid game), return (0, 0)
    return (0, 0)


def check_win(board: list[list[int]], player: int) -> bool:
    """Checks if the given player has won the Tic Tac Toe game."""
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
