
import numpy as np
from random import choice

def policy(board: list[list[int]]) -> tuple[int, int]:
    np_board = np.array(board, dtype=int)
    empty_spots = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]

    # Check for immediate win
    for i, j in empty_spots:
        temp_board = np_board.copy()
        temp_board[i, j] = 1
        # Check row
        if np.all(temp_board[i, :] == 1):
            return (i, j)
        # Check column
        if np.all(temp_board[:, j] == 1):
            return (i, j)
        # Check diagonal (top-left to bottom-right)
        diag = np.array([temp_board[k, k] for k in range(4)])
        if np.all(diag == 1):
            return (i, j)
        # Check anti-diagonal (top-right to bottom-left)
        anti_diag = np.array([temp_board[k, 3-k] for k in range(4)])
        if np.all(anti_diag == 1):
            return (i, j)

    # Check for opponent's immediate win
    for i, j in empty_spots:
        temp_board = np_board.copy()
        temp_board[i, j] = -1
        # Check row
        if np.all(temp_board[i, :] == -1):
            return (i, j)
        # Check column
        if np.all(temp_board[:, j] == -1):
            return (i, j)
        # Check diagonal
        diag = np.array([temp_board[k, k] for k in range(4)])
        if np.all(diag == -1):
            return (i, j)
        # Check anti-diagonal
        anti_diag = np.array([temp_board[k, 3-k] for k in range(4)])
        if np.all(anti_diag == -1):
            return (i, j)

    # Check for potential 3-in-a-rows for me
    for i, j in empty_spots:
        temp_board = np_board.copy()
        temp_board[i, j] = 1
        # Check row
        row = temp_board[i, :]
        if np.sum(row == 1) == 3 and np.sum(row == 0) == 1:
            return (i, j)
        # Check column
        col = temp_board[:, j]
        if np.sum(col == 1) == 3 and np.sum(col == 0) == 1:
            return (i, j)
        # Check diagonal
        diag = np.array([temp_board[k, k] for k in range(4)])
        if np.sum(diag == 1) == 3 and np.sum(diag == 0) == 1:
            return (i, j)
        # Check anti-diagonal
        anti_diag = np.array([temp_board[k, 3-k] for k in range(4)])
        if np.sum(anti_diag == 1) == 3 and np.sum(anti_diag == 0) == 1:
            return (i, j)

    # Check for opponent's potential 3-in-a-rows and block
    for i, j in empty_spots:
        temp_board = np_board.copy()
        temp_board[i, j] = -1
        # Check row
        row = temp_board[i, :]
        if np.sum(row == -1) == 3 and np.sum(row == 0) == 1:
            return (i, j)
        # Check column
        col = temp_board[:, j]
        if np.sum(col == -1) == 3 and np.sum(col == 0) == 1:
            return (i, j)
        # Check diagonal
        diag = np.array([temp_board[k, k] for k in range(4)])
        if np.sum(diag == -1) == 3 and np.sum(diag == 0) == 1:
            return (i, j)
        # Check anti-diagonal
        anti_diag = np.array([temp_board[k, 3-k] for k in range(4)])
        if np.sum(anti_diag == -1) == 3 and np.sum(anti_diag == 0) == 1:
            return (i, j)

    # If no winning or blocking moves, pick a random empty spot
    return choice(empty_spots)
