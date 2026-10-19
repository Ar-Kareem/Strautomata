
import numpy as np
import random

def check_winner(board: np.ndarray, player: int) -> bool:
    # Check rows, columns and diagonals for a win
    for i in range(4):
        if np.all(board[i, :] == player) or np.all(board[:, i] == player):
            return True
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    return False

def policy(board: list[list[int]]) -> tuple[int, int]:
    np_board = np.array(board)
    
    # Check for winning move for myself
    for row in range(4):
        for col in range(4):
            if np_board[row, col] == 0:
                np_board[row, col] = 1  # Try my move
                if check_winner(np_board, 1):
                    return (row, col)
                np_board[row, col] = 0  # Undo my move

    # Check for winning move for the opponent
    for row in range(4):
        for col in range(4):
            if np_board[row, col] == 0:
                np_board[row, col] = -1  # Try opponent's move
                if check_winner(np_board, -1):
                    return (row, col)
                np_board[row, col] = 0  # Undo opponent's move

    # If no immediate wins, choose a random empty spot
    empty_positions = np.argwhere(np_board == 0)
    if empty_positions.size > 0:
        move = random.choice(empty_positions)
        return (move[0], move[1])

    # This return should be unreachable if the board is not full
    return (-1, -1)
