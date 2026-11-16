
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns the optimal move for the current player (1) in 4x4 Tic Tac Toe.
    Uses minimax algorithm with alpha-beta pruning.
    """
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)

    # Find all empty cells
    empty_cells = np.argwhere(board_array == 0)

    # If board is empty, take center (optimal first move)
    if len(empty_cells) == 16:
        return (1, 1)

    # Check for immediate winning move
    for move in empty_cells:
        row, col = move
        board_array[row, col] = 1
        if check_win(board_array, 1):
            return (row, col)
        board_array[row, col] = 0  # undo move

    # Check for opponent's immediate winning move to block
    for move in empty_cells:
        row, col = move
        board_array[row, col] = -1
        if check_win(board_array, -1):
            return (row, col)
        board_array[row, col] = 0  # undo move

    # Use minimax to find best move
    best_score = -float('inf')
    best_move = None

    for move in empty_cells:
        row, col = move
        board_array[row, col] = 1
        score = minimax(board_array, 0, False, -float('inf'), float('inf'))
        board_array[row, col] = 0  # undo move

        if score > best_score:
            best_score = score
            best_move = (row, col)

    return best_move

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has won."""
    # Check rows
    for row in range(4):
        if np.all(board[row, :] == player):
            return True

    # Check columns
    for col in range(4):
        if np.all(board[:, col] == player):
            return True

    # Check diagonals
    if np.all(np.diag(board) == player):
        return True
    if np.all(np.diag(np.fliplr(board)) == player):
        return True

    return False

def evaluate(board: np.ndarray) -> int:
    """Evaluate the board state for the current player (1)."""
    # Check if current player has won
    if check_win(board, 1):
        return 100

    # Check if opponent has won
    if check_win(board, -1):
        return -100

    # Evaluate based on potential lines
    score = 0

    # Evaluate rows
    for row in range(4):
        line = board[row, :]
        score += evaluate_line(line)

    # Evaluate columns
    for col in range(4):
        line = board[:, col]
        score += evaluate_line(line)

    # Evaluate diagonals
    score += evaluate_line(np.diag(board))
    score += evaluate_line(np.diag(np.fliplr(board)))

    return score

def evaluate_line(line: np.ndarray) -> int:
    """Evaluate a single line (row, column, or diagonal)."""
    count_1 = np.count_nonzero(line == 1)
    count_neg1 = np.count_nonzero(line == -1)
    count_0 = np.count_nonzero(line == 0)

    # If line is empty
    if count_1 == 0 and count_neg1 == 0:
        return 0

    # If line has both players, it's blocked
    if count_1 > 0 and count_neg1 > 0:
        return 0

    # Evaluate based on current player's potential
    if count_neg1 == 0:  # Only current player's pieces
        if count_1 == 3 and count_0 == 1:
            return 50
        elif count_1 == 2 and count_0 == 2:
            return 10
        elif count_1 == 1 and count_0 == 3:
            return 1
    else:  # Only opponent's pieces
        if count_neg1 == 3 and count_0 == 1:
            return -40
        elif count_neg1 == 2 and count_0 == 2:
            return -5
        elif count_neg1 == 1 and count_0 == 3:
            return -1

    return 0

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
    """Minimax algorithm with alpha-beta pruning."""
    # Check terminal states
    if check_win(board, 1):
        return 100 - depth
    if check_win(board, -1):
        return -100 + depth
    if np.all(board != 0):  # Draw
        return 0

    if is_maximizing:
        best_score = -float('inf')
        for move in np.argwhere(board == 0):
            row, col = move
            board[row, col] = 1
            score = minimax(board, depth + 1, False, alpha, beta)
            board[row, col] = 0  # undo move
            best_score = max(score, best_score)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return best_score
    else:
        best_score = float('inf')
        for move in np.argwhere(board == 0):
            row, col = move
            board[row, col] = -1
            score = minimax(board, depth + 1, True, alpha, beta)
            board[row, col] = 0  # undo move
            best_score = min(score, best_score)
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return best_score
