
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Check if we can win in the next move
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:  # Empty cell
                # Try this move
                board_array[i, j] = 1
                if check_win(board_array, 1):
                    return (i, j)
                # Undo the move
                board_array[i, j] = 0
    
    # Check if opponent can win in the next move (block them)
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:  # Empty cell
                # Try this move for opponent
                board_array[i, j] = -1
                if check_win(board_array, -1):
                    board_array[i, j] = 0
                    return (i, j)
                # Undo the move
                board_array[i, j] = 0
    
    # If center is free, take it (optimal opening strategy)
    if board_array[1, 1] == 0:
        return (1, 1)
    
    # If opponent took center and we're going second, take a corner
    if board_array[1, 1] == -1 and sum(sum(abs(board_array[i, j]) for j in range(3)) for i in range(3)) == 1:
        # Take a corner
        for corner in [(0, 0), (0, 2), (2, 0), (2, 2)]:
            if board_array[corner] == 0:
                return corner
    
    # Otherwise use minimax to find the best move
    best_score = float('-inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                score = minimax(board_array, 0, False, float('-inf'), float('inf'))
                board_array[i, j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    # In case all cells are filled (shouldn't happen in normal play)
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board_array[i, j] == 0:
                    return (i, j)
    
    return best_move

def check_win(board: np.ndarray, player: int) -> bool:
    # Check rows, columns, and diagonals
    for i in range(3):
        if all(board[i, j] == player for j in range(3)):
            return True
        if all(board[j, i] == player for j in range(3)):
            return True
    if all(board[i, i] == player for i in range(3)):
        return True
    if all(board[i, 2-i] == player for i in range(3)):
        return True
    return False

def is_game_over(board: np.ndarray) -> Tuple[bool, int]:
    # Check if someone won
    if check_win(board, 1):
        return (True, 1)
    if check_win(board, -1):
        return (True, -1)
    
    # Check for draw (all cells filled)
    if all(board[i, j] != 0 for i in range(3) for j in range(3)):
        return (True, 0)
    
    return (False, 0)

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> int:
    game_over, winner = is_game_over(board)
    
    if game_over:
        if winner == 1:
            return 10 - depth  # Win, prefer faster wins
        elif winner == -1:
            return depth - 10  # Loss, prefer longer games
        else:
            return 0  # Draw
    
    if is_maximizing:
        max_eval = float('-inf')
        for i in range(3):
            for j in range(3):
                if board[i, j] == 0:
                    board[i, j] = 1
                    eval_score = minimax(board, depth + 1, False, alpha, beta)
                    board[i, j] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Beta cutoff
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
                        break  # Alpha cutoff
            if beta <= alpha:
                break
        return min_eval
