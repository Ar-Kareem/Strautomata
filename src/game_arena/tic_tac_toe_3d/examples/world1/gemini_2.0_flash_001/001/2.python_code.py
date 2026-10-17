
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Chooses the next move for a 3x3x3 Tic Tac Toe game.
    """

    board_np = np.array(board)
    # Check for winning moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i][j][k] == 0:
                    board_np[i][j][k] = 1
                    if check_win(board_np, 1):
                        return (i, j, k)
                    board_np[i][j][k] = 0

    # Check for blocking moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i][j][k] == 0:
                    board_np[i][j][k] = -1
                    if check_win(board_np, -1):
                        return (i, j, k)
                    board_np[i][j][k] = 0

    # Take the center if available
    if board_np[1][1][1] == 0:
        return (1, 1, 1)

    # Take a corner if available
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board_np[corner[0]][corner[1]][corner[2]] == 0:
            return corner

    # Take any available cell
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i][j][k] == 0:
                    return (i, j, k)

    return (0, 0, 0)  # Should never happen in a valid game

def check_win(board: np.ndarray, player: int) -> bool:
    """
    Checks if the given player has won the game.
    """
    for i in range(3):
        # Check rows in each layer
        for j in range(3):
            if np.all(board[i][j] == player):
                return True
            if np.all(board[j][i] == player):
                return True
        if np.all(board[i, :, i] == player):
            return True
        if np.all(board[i, :, 2 - i] == player):
            return True
        if np.all(board[:, i, i] == player):
            return True
        if np.all(board[:, i, 2-i] == player):
            return True
        if np.all(board[i, i, :] == player):
            return True
        if np.all(board[i, 2-i, :] == player):
            return True
    # Check diagonals
    winning_conditions = [
        np.array([board[i, i, i] for i in range(3)]),
        np.array([board[i, i, 2-i] for i in range(3)]),
        np.array([board[i, 2-i, i] for i in range(3)]),
        np.array([board[i, 2-i, 2-i] for i in range(3)])
    ]
    for condition in winning_conditions:
        if np.all(condition == player):
            return True

    return False
