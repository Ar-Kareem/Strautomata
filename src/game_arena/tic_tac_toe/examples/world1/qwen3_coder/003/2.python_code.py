
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier handling
    board_array = np.array(board)
    
    # Check for immediate winning moves
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                # Try placing my mark here
                board_array[i, j] = 1
                if check_winner(board_array) == 1:
                    return (i, j)
                # Undo the move
                board_array[i, j] = 0
    
    # Check for opponent winning moves to block
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                # Try placing opponent's mark here
                board_array[i, j] = -1
                if check_winner(board_array) == -1:
                    return (i, j)
                # Undo the move
                board_array[i, j] = 0
    
    # Use minimax for optimal play
    best_score = -float('inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                score = minimax(board_array, 0, False, -float('inf'), float('inf'))
                board_array[i, j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    # Fallback to first available move if needed
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board_array[i, j] == 0:
                    return (i, j)
    
    return best_move

def check_winner(board: np.ndarray) -> int:
    # Check rows
    for i in range(3):
        if abs(board[i, 0] + board[i, 1] + board[i, 2]) == 3:
            return board[i, 0]
    
    # Check columns
    for j in range(3):
        if abs(board[0, j] + board[1, j] + board[2, j]) == 3:
            return board[0, j]
    
    # Check diagonals
    if abs(board[0, 0] + board[1, 1] + board[2, 2]) == 3:
        return board[1, 1]
    
    if abs(board[0, 2] + board[1, 1] + board[2, 0]) == 3:
        return board[1, 1]
    
    return 0

def is_board_full(board: np.ndarray) -> bool:
    return not np.any(board == 0)

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
    winner = check_winner(board)
    
    # Terminal states
    if winner == 1:  # I win
        return 10 - depth
    elif winner == -1:  # Opponent wins
        return depth - 10
    elif is_board_full(board):  # Draw
        return 0
    
    if is_maximizing:
        max_eval = -float('inf')
        for i in range(3):
            for j in range(3):
                if board[i, j] == 0:
                    board[i, j] = 1
                    eval_score = minimax(board, depth + 1, False, alpha, beta)
                    board[i, j] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(3):
            for j in range(3):
                if board[i, j] == 0:
                    board[i, j] = -1
                    eval_score = minimax(board, depth + 1, True, alpha, beta)
                    board[i, j] = 0
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
            if beta <= alpha:
                break
        return min_eval
