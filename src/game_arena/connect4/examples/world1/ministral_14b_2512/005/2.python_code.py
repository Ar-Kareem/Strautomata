
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning and heuristic evaluation.
    """
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)

    # Find all legal moves (columns with at least one empty cell)
    legal_moves = [col for col in range(7) if board_np[0][col] == 0]

    if not legal_moves:
        raise ValueError("No legal moves available (board is full)")

    # Start minimax search with alpha-beta pruning
    best_score = -float('inf')
    best_move = legal_moves[0]

    # Use a fixed depth for simplicity (adjust based on performance)
    depth = 5  # Can be increased if time allows

    for col in legal_moves:
        # Simulate the move
        new_board = np.copy(board_np)
        row = get_next_open_row(new_board, col)
        new_board[row][col] = 1

        # Evaluate the move
        score = minimax(new_board, depth - 1, -float('inf'), float('inf'), False)

        # Update best move
        if score > best_score:
            best_score = score
            best_move = col

    return best_move

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
    """
    Minimax with alpha-beta pruning for Connect 4.
    """
    # Check if the game is over
    winner = check_winner(board)
    if winner == 1:
        return float('inf')  # Current player wins
    elif winner == -1:
        return -float('inf')  # Opponent wins
    elif depth == 0 or is_board_full(board):
        return evaluate_board(board)

    if is_maximizing:
        max_eval = -float('inf')
        for col in range(7):
            if board[0][col] == 0:  # Legal move
                new_board = np.copy(board)
                row = get_next_open_row(new_board, col)
                new_board[row][col] = 1
                eval = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
        return max_eval
    else:
        min_eval = float('inf')
        for col in range(7):
            if board[0][col] == 0:  # Legal move
                new_board = np.copy(board)
                row = get_next_open_row(new_board, col)
                new_board[row][col] = -1
                eval = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
        return min_eval

def evaluate_board(board: np.ndarray) -> int:
    """
    Heuristic evaluation of the board.
    """
    score = 0

    # Check for center control (columns 2, 3, 4 are more valuable)
    center_column = board[:, 3]
    center_count = np.sum(center_column == 1) - np.sum(center_column == -1)
    score += center_count * 3

    # Check for potential lines (horizontal, vertical, diagonal)
    score += evaluate_window(board, [1, 1, 1, 1], 100000)  # Winning move
    score += evaluate_window(board, [1, 1, 1, -1], 1000)   # Block opponent's win
    score += evaluate_window(board, [-1, -1, -1, 1], 1000)  # Block opponent's win
    score += evaluate_window(board, [1, 1, -1, -1], 10)    # Opponent's potential threat
    score += evaluate_window(board, [-1, 1, 1, -1], 10)    # Opponent's potential threat

    # Evaluate lines of 3 and 2 for the current player
    score += evaluate_window(board, [1, 1, 1, 0], 100)     # Three in a row
    score += evaluate_window(board, [1, 1, 0, 1], 100)     # Three in a row
    score += evaluate_window(board, [1, 0, 1, 1], 100)     # Three in a row
    score += evaluate_window(board, [0, 1, 1, 1], 100)     # Three in a row
    score += evaluate_window(board, [1, 1, 0, 0], 10)      # Two in a row
    score += evaluate_window(board, [0, 1, 1, 0], 10)      # Two in a row
    score += evaluate_window(board, [0, 0, 1, 1], 10)      # Two in a row

    # Penalize opponent's lines of 3 and 2
    score -= evaluate_window(board, [-1, -1, -1, 0], 100)  # Opponent's three in a row
    score -= evaluate_window(board, [-1, -1, 0, -1], 100)  # Opponent's three in a row
    score -= evaluate_window(board, [-1, 0, -1, -1], 100)  # Opponent's three in a row
    score -= evaluate_window(board, [0, -1, -1, -1], 100)  # Opponent's three in a row
    score -= evaluate_window(board, [-1, -1, 0, 0], 10)    # Opponent's two in a row
    score -= evaluate_window(board, [0, -1, -1, 0], 10)    # Opponent's two in a row
    score -= evaluate_window(board, [0, 0, -1, -1], 10)    # Opponent's two in a row

    return score

def evaluate_window(window: np.ndarray, pattern: List[int], multiplier: int) -> int:
    """
    Evaluate a window (4 consecutive cells) for a given pattern.
    """
    score = 0
    for i in range(len(window) - 3):
        window_slice = window[i:i+4]
        if np.array_equal(window_slice, pattern):
            score += multiplier
    return score

def check_winner(board: np.ndarray) -> int:
    """
    Check if there is a winner (1 for current player, -1 for opponent, 0 for no winner).
    """
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if board[row][col] != 0 and board[row][col] == board[row][col+1] == board[row][col+2] == board[row][col+3]:
                return board[row][col]

    # Check vertical
    for row in range(3):
        for col in range(7):
            if board[row][col] != 0 and board[row][col] == board[row+1][col] == board[row+2][col] == board[row+3][col]:
                return board[row][col]

    # Check positive diagonal
    for row in range(3):
        for col in range(4):
            if board[row][col] != 0 and board[row][col] == board[row+1][col+1] == board[row+2][col+2] == board[row+3][col+3]:
                return board[row][col]

    # Check negative diagonal
    for row in range(3):
        for col in range(3, 7):
            if board[row][col] != 0 and board[row][col] == board[row+1][col-1] == board[row+2][col-2] == board[row+3][col-3]:
                return board[row][col]

    return 0

def is_board_full(board: np.ndarray) -> bool:
    """
    Check if the board is full (no empty cells).
    """
    return np.all(board != 0)

def get_next_open_row(board: np.ndarray, col: int) -> int:
    """
    Find the next open row in a column.
    """
    for row in range(6):
        if board[row][col] == 0:
            return row
    return -1  # Column is full
