
def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 3x3 Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of two integers (0-2, 0-2) indicating the row and column you choose.
    """

    def check_win(board, player):
        """Checks if the given player has won the game."""
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] == player:
                return True
            if board[0][i] == board[1][i] == board[2][i] == player:
                return True
        if board[0][0] == board[1][1] == board[2][2] == player:
            return True
        if board[0][2] == board[1][1] == board[2][0] == player:
            return True
        return False

    # 1. Check for winning moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    return (row, col)
                board[row][col] = 0  # Reset the board

    # 2. Check for blocking moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    return (row, col)
                board[row][col] = 0  # Reset the board

    # 3. Take the center if available
    if board[1][1] == 0:
        return (1, 1)

    # 4. Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for row, col in corners:
        if board[row][col] == 0:
            return (row, col)

    # 5. Take any available cell
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                return (row, col)

    # If the board is full (which shouldn't happen), return (0, 0) as a default
    return (0, 0)
