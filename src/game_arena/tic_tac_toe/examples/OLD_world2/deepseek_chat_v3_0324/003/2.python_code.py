
import numpy as np
from typing import Optional

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Check if we can win immediately
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                if check_win(board_array, 1):
                    return (i, j)
                board_array[i, j] = 0
    
    # Check if we need to block opponent
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = -1
                if check_win(board_array, -1):
                    board_array[i, j] = 0
                    return (i, j)
                board_array[i, j] = 0
    
    # Use minimax with alpha-beta pruning for other moves
    best_score = -float('inf')
    best_move = None
    
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                score = minimax(board_array, False, -float('inf'), float('inf'), depth=3)
                board_array[i, j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move if best_move else get_first_empty(board)

def minimax(board: np.ndarray, is_maximizing: bool, alpha: float, beta: float, depth: int) -> float:
    winner = check_winner(board)
    if winner == 1:
        return 10
    elif winner == -1:
        return -10
    elif np.all(board != 0) or depth == 0:  # Draw or depth limit reached
        return 0
    
    if is_maximizing:
        max_eval = -float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = 1
                    eval_val = minimax(board, False, alpha, beta, depth-1)
                    board[i, j] = 0
                    max_eval = max(max_eval, eval_val)
                    alpha = max(alpha, eval_val)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = -1
                    eval_val = minimax(board, True, alpha, beta, depth-1)
                    board[i, j] = 0
                    min_eval = min(min_eval, eval_val)
                    beta = min(beta, eval_val)
                    if beta <= alpha:
                        break
        return min_eval

def check_win(board: np.ndarray, player: int) -> bool:
    # Check rows, columns and diagonals for 4 in a row
    for i in range(4):
        if np.all(board[i, :] == player) or np.all(board[:, i] == player):
            return True
    if np.all(np.diag(board) == player) or np.all(np.diag(np.fliplr(board)) == player):
        return True
    
    # Check all possible 3-in-a-row lines (8 possible directions per cell)
    for i in range(4):
        for j in range(4):
            # Check horizontal
            if j <= 1 and np.all(board[i, j:j+3] == player):
                return True
            # Check vertical
            if i <= 1 and np.all(board[i:i+3, j] == player):
                return True
            # Check diagonals
            if i <= 1 and j <= 1 and board[i, j] == player and board[i+1, j+1] == player and board[i+2, j+2] == player:
                return True
            if i <= 1 and j >= 2 and board[i, j] == player and board[i+1, j-1] == player and board[i+2, j-2] == player:
                return True
    return False

def check_winner(board: np.ndarray) -> Optional[int]:
    if check_win(board, 1):
        return 1
    if check_win(board, -1):
        return -1
    if np.all(board != 0):
        return 0  # Draw
    return None  # Game not finished

def get_first_empty(board: np.ndarray) -> tuple[int, int]:
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                return (i, j)
    return (0, 0)  # Shouldn't reach here for valid game states
