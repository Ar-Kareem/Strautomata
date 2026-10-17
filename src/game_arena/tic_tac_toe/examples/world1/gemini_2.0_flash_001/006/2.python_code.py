
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Chooses the next move for a 3x3 Tic Tac Toe game.

    Args:
        board: A 3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of two integers (0-2, 0-2) indicating the row and column you choose.
    """

    def check_win(board, player):
        """Checks if the given player has won the board."""
        for i in range(3):
            if all(board[i][j] == player for j in range(3)):
                return True
            if all(board[j][i] == player for j in range(3)):
                return True
        if all(board[i][i] == player for i in range(3)):
            return True
        if all(board[i][2 - i] == player for i in range(3)):
            return True
        return False

    # 1. Check for winning moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_win(board, 1):
                    return (row, col)
                board[row][col] = 0  # Undo the move

    # 2. Block opponent's winning moves
    for row in range(3):
        for col in range(3):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_win(board, -1):
                    return (row, col)
                board[row][col] = 0  # Undo the move

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

    # If no move is possible (board is full), return (0, 0) as a default
    return (0, 0)
