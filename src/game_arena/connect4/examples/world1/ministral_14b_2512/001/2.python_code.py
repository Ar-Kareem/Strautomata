
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    """
    Implements a targeting policy for a Connect 4 game.
    The goal is to place a disc in a column that will help win the game by forming four consecutive discs.

    Args:
        board: A 6x7 grid representing the Connect 4 board.
              0: empty cell, 1: current player's disc, -1: opponent's disc.

    Returns:
        int: The column index (0-6) where to drop the current player's disc.
    """
    # Convert the board to a numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Check for immediate win
    immediate_win_col = check_immediate_win(board_np)
    if immediate_win_col is not None:
        return immediate_win_col

    # Check for opponent's win and block it
    block_col = check_opponent_win(board_np)
    if block_col is not None:
        return block_col

    # If no immediate win or block, use heuristic to choose the best column
    best_col = choose_best_column_heuristic(board_np)

    return best_col

def check_immediate_win(board: np.ndarray) -> int:
    """
    Checks if placing a disc in any column results in an immediate win.

    Args:
        board: The current board state as a numpy array.

    Returns:
        int: The column index where placing a disc results in an immediate win, or None if no such column exists.
    """
    for col in range(7):
        if is_column_full(board, col):
            continue
        next_row = get_next_row(board, col)
        # Simulate placing a disc in the column
        new_board = board.copy()
        new_board[next_row, col] = 1
        if is_win_condition(new_board, next_row, col):
            return col
    return None

def check_opponent_win(board: np.ndarray) -> int:
    """
    Checks if the opponent can win in their next move and returns the column to block.

    Args:
        board: The current board state as a numpy array.

    Returns:
        int: The column index where placing a disc would block the opponent's win, or None if no such column exists.
    """
    for col in range(7):
        if is_column_full(board, col):
            continue
        next_row = get_next_row(board, col)
        # Simulate placing the opponent's disc in the column
        new_board = board.copy()
        new_board[next_row, col] = -1
        if is_win_condition(new_board, next_row, col, player=-1):
            return col
    return None

def choose_best_column_heuristic(board: np.ndarray) -> int:
    """
    Chooses the best column based on heuristic evaluation.

    Args:
        board: The current board state as a numpy array.

    Returns:
        int: The best column index to drop a disc based on heuristic.
    """
    # Initialize scores for each column
    scores = np.zeros(7)

    # Evaluate each column
    for col in range(7):
        if is_column_full(board, col):
            continue
        next_row = get_next_row(board, col)
        # Simulate placing a disc in the column
        new_board = board.copy()
        new_board[next_row, col] = 1

        # Score based on potential lines
        scores[col] += evaluate_potential_lines(new_board, next_row, col)

        # Prefer center columns
        center_bonus = 3 - abs(col - 3)
        scores[col] += center_bonus

    # Choose the column with the highest score
    best_cols = np.where(scores == np.max(scores))[0]
    # Prefer center columns if there's a tie
    best_cols = sorted(best_cols, key=lambda x: abs(x - 3))
    return best_cols[0]

def evaluate_potential_lines(board: np.ndarray, row: int, col: int) -> int:
    """
    Evaluates the potential lines (horizontal, vertical, diagonal) that can be formed by placing a disc at (row, col).

    Args:
        board: The board state after placing the disc.
        row: The row where the disc was placed.
        col: The column where the disc was placed.

    Returns:
        int: The score based on potential lines.
    """
    score = 0
    directions = [
        (0, 1),  # horizontal
        (1, 0),  # vertical
        (1, 1),  # diagonal down-right
        (1, -1)  # diagonal down-left
    ]

    for dr, dc in directions:
        # Check in the positive direction
        count = 1  # the disc itself
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == 1:
            count += 1
            r += dr
            c += dc

        # Check in the negative direction
        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == 1:
            count += 1
            r -= dr
            c -= dc

        # Score based on the count of consecutive discs
        if count >= 3:
            score += 10 ** (count - 3)  # exponential score for longer lines

    return score

def is_win_condition(board: np.ndarray, row: int, col: int, player: int = 1) -> bool:
    """
    Checks if placing a disc at (row, col) for the given player results in a win.

    Args:
        board: The board state after placing the disc.
        row: The row where the disc was placed.
        col: The column where the disc was placed.
        player: The player whose disc was placed (1 or -1).

    Returns:
        bool: True if the placement results in a win, False otherwise.
    """
    directions = [
        (0, 1),  # horizontal
        (1, 0),  # vertical
        (1, 1),  # diagonal down-right
        (1, -1)  # diagonal down-left
    ]

    for dr, dc in directions:
        count = 1
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
            count += 1
            r += dr
            c += dc

        r, c = row - dr, col - dc
        while 0 <= r < 6 and 0 <= c < 7 and board[r, c] == player:
            count += 1
            r -= dr
            c -= dc

        if count >= 4:
            return True

    return False

def get_next_row(board: np.ndarray, col: int) -> int:
    """
    Gets the next available row in the specified column.

    Args:
        board: The current board state as a numpy array.
        col: The column index.

    Returns:
        int: The row index where the next disc would be placed.
    """
    for row in range(5, -1, -1):
        if board[row, col] == 0:
            return row
    return -1  # column is full

def is_column_full(board: np.ndarray, col: int) -> bool:
    """
    Checks if the specified column is full.

    Args:
        board: The current board state as a numpy array.
        col: The column index.

    Returns:
        bool: True if the column is full, False otherwise.
    """
    return board[0, col] != 0
