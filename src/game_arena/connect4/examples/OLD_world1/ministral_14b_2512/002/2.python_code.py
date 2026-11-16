
import numpy as np
import random
from collections import defaultdict

def policy(board: list[list[int]]) -> int:
    # Convert to numpy array for easier manipulation
    board = np.array(board, dtype=int)
    rows, cols = board.shape

    # Find all valid columns (not full)
    valid_cols = [col for col in range(cols) if board[rows-1][col] == 0]

    # Check for immediate winning moves
    for col in valid_cols:
        new_board = make_move(board, col, 1)
        if check_win(new_board, 1):
            return col

    # Check for opponent's immediate winning moves and block them
    for col in valid_cols:
        new_board = make_move(board, col, -1)
        if check_win(new_board, -1):
            return col

    # Evaluate all valid moves using a heuristic
    scores = []
    for col in valid_cols:
        new_board = make_move(board, col, 1)
        score = evaluate_position(new_board, 1)
        scores.append(score)

    # Find the move with the highest score
    best_score = max(scores)
    best_moves = [i for i, score in enumerate(scores) if score == best_score]

    # If there are multiple best moves, choose randomly among them
    return valid_cols[random.choice(best_moves)]

def make_move(board: np.ndarray, col: int, player: int) -> np.ndarray:
    """Make a move on the board and return the new board state."""
    new_board = board.copy()
    for row in range(new_board.shape[0]-1, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won on the board."""
    rows, cols = board.shape

    # Check horizontal locations
    for row in range(rows):
        for col in range(cols - 3):
            if board[row][col] == player and board[row][col+1] == player and \
               board[row][col+2] == player and board[row][col+3] == player:
                return True

    # Check vertical locations
    for row in range(rows - 3):
        for col in range(cols):
            if board[row][col] == player and board[row+1][col] == player and \
               board[row+2][col] == player and board[row+3][col] == player:
                return True

    # Check positively sloped diagonals
    for row in range(rows - 3):
        for col in range(cols - 3):
            if board[row][col] == player and board[row+1][col+1] == player and \
               board[row+2][col+2] == player and board[row+3][col+3] == player:
                return True

    # Check negatively sloped diagonals
    for row in range(3, rows):
        for col in range(cols - 3):
            if board[row][col] == player and board[row-1][col+1] == player and \
               board[row-2][col+2] == player and board[row-3][col+3] == player:
                return True

    return False

def evaluate_position(board: np.ndarray, player: int) -> int:
    """Evaluate the board position from the player's perspective."""
    score = 0
    rows, cols = board.shape

    # Check horizontal
    for row in range(rows):
        for col in range(cols - 3):
            window = board[row][col:col+4]
            score += evaluate_window(window, player)

    # Check vertical
    for row in range(rows - 3):
        for col in range(cols):
            window = board[row:row+4, col]
            score += evaluate_window(window, player)

    # Check positively sloped diagonals
    for row in range(rows - 3):
        for col in range(cols - 3):
            window = [board[row+i][col+i] for i in range(4)]
            score += evaluate_window(window, player)

    # Check negatively sloped diagonals
    for row in range(3, rows):
        for col in range(cols - 3):
            window = [board[row-i][col+i] for i in range(4)]
            score += evaluate_window(window, player)

    return score

def evaluate_window(window: list, player: int) -> int:
    """Evaluate a window of 4 cells."""
    score = 0
    opponent = -player

    if window.count(player) == 4:
        score += 100
    elif window.count(player) == 3 and window.count(0) == 1:
        score += 5
    elif window.count(player) == 2 and window.count(0) == 2:
        score += 2

    if window.count(opponent) == 3 and window.count(0) == 1:
        score -= 4

    return score
