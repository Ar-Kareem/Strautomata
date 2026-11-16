
import numpy as np

def check_win(board: list[list[list[int]]], player: int) -> bool:
    """Checks if the given player has won the board."""
    # Check rows, columns, and depths
    for i in range(3):
        for j in range(3):
            if all(board[i][j][k] == player for k in range(3)):
                return True
            if all(board[i][k][j] == player for k in range(3)):
                return True
            if all(board[k][i][j] == player for k in range(3)):
                return True

    # Check diagonals
    for i in range(3):
        if all(board[i][k][k] == player for k in range(3)):
            return True
        if all(board[i][k][2 - k] == player for k in range(3)):
            return True
        if all(board[k][i][k] == player for k in range(3)):
            return True
        if all(board[k][i][2 - k] == player for k in range(3)):
            return True
        if all(board[k][k][i] == player for k in range(3)):
            return True
        if all(board[k][2 - k][i] == player for k in range(3)):
            return True

    # Check space diagonals
    if all(board[k][k][k] == player for k in range(3)):
        return True
    if all(board[k][k][2 - k] == player for k in range(3)):
        return True
    if all(board[k][2 - k][k] == player for k in range(3)):
        return True
    if all(board[k][2-k][2-k] == player for k in range(3)):
      return True
    return False

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for the 3x3x3 Tic Tac Toe game.
    """

    # 1. Check for Winning Moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = 1
                    if check_win(board, 1):
                        return (i, j, k)
                    board[i][j][k] = 0  # Reset the board

    # 2. Check for Blocking Moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    board[i][j][k] = -1
                    if check_win(board, -1):
                        return (i, j, k)
                    board[i][j][k] = 0  # Reset the board

    # 3. Center Move
    if board[1][1][1] == 0:
        return (1, 1, 1)

    # 4. Random Move (First available cell)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    return (i, j, k)

    return (0, 0, 0)  # Should not happen in a valid game state
