
import numpy as np
from typing import Optional

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert the board to a numpy array for easier manipulation
    board_array = np.array(board)
    
    # If the board is empty, start with the center (best first move)
    if np.all(board_array == 0):
        return (1, 1)
    
    # Find the best move using minimax with alpha-beta pruning
    best_score = -float('inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                score = minimax(board_array, False, -float('inf'), float('inf'))
                board_array[i, j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move

def minimax(board: np.ndarray, is_maximizing: bool, alpha: float, beta: float) -> int:
    result = evaluate(board)
    if result is not None:
        return result
    
    if is_maximizing:
        best_score = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i, j] == 0:
                    board[i, j] = 1
                    score = minimax(board, False, alpha, beta)
                    board[i, j] = 0
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
        return best_score
    else:
        best_score = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i, j] == 0:
                    board[i, j] = -1
                    score = minimax(board, True, alpha, beta)
                    board[i, j] = 0
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
        return best_score

def evaluate(board: np.ndarray) -> Optional[int]:
    # Check rows
    for row in range(3):
        if np.all(board[row, :] == 1):
            return 1
        if np.all(board[row, :] == -1):
            return -1
    
    # Check columns
    for col in range(3):
        if np.all(board[:, col] == 1):
            return 1
        if np.all(board[:, col] == -1):
            return -1
    
    # Check diagonals
    if np.all(np.diag(board) == 1) or np.all(np.diag(np.fliplr(board)) == 1):
        return 1
    if np.all(np.diag(board) == -1) or np.all(np.diag(np.fliplr(board)) == -1):
        return -1
    
    # Check for draw
    if np.all(board != 0):
        return 0
    
    # Game not finished
    return None
