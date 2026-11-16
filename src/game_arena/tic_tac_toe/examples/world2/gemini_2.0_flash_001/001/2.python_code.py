
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the next move for a 4x4 Tic Tac Toe game.
    """

    board_np = np.array(board)

    # Check for a winning move for the AI (1)
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                board_np[i, j] = 1
                if check_win(board_np, 1):
                    return (i, j)
                board_np[i, j] = 0  # Reset

    # Check for a blocking move for the opponent (-1)
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                board_np[i, j] = -1
                if check_win(board_np, -1):
                    return (i, j)
                board_np[i, j] = 0  # Reset

    # If no winning or blocking move, find the first available space
    for i in range(4):
        for j in range(4):
            if board_np[i, j] == 0:
                return (i, j)

    # If the board is full (shouldn't happen), return (0, 0) as default
    return (0, 0)


def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    # Check rows
    for row in board:
        if all(cell == player for cell in row):
            return True

    # Check columns
    for col in range(4):
        if all(board[row][col] == player for row in range(4)):
            return True

    # Check diagonals
    if all(board[i][i] == player for i in range(4)):
        return True
    if all(board[i][3 - i] == player for i in range(4)):
        return True

    return False
