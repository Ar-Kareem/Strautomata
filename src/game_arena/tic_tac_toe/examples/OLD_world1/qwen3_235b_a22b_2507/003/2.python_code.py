
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the optimal move for Tic Tac Toe using minimax algorithm with alpha-beta pruning.
    """
    board_array = np.array(board)
    
    def check_winner(board):
        # Check rows, columns, and diagonals
        for i in range(3):
            if abs(np.sum(board[i, :])) == 3:
                return np.sign(np.sum(board[i, :]))
            if abs(np.sum(board[:, i])) == 3:
                return np.sign(np.sum(board[:, i]))
        
        if abs(np.sum(np.diag(board))) == 3:
            return np.sign(np.sum(np.diag(board)))
        if abs(np.sum(np.diag(np.fliplr(board)))) == 3:
            return np.sign(np.sum(np.diag(np.fliplr(board))))
        
        return 0  # No winner
    
    def is_terminal(board):
        winner = check_winner(board)
        if winner != 0:
            return True, winner
        
        # Check for draw (no empty cells)
        if np.all(board != 0):
            return True, 0
        
        return False, 0
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        is_terminal_state, result = is_terminal(board)
        
        if is_terminal_state:
            if result == 1:  # AI wins
                return 10 - depth
            elif result == -1:  # Opponent wins
                return depth - 10
            else:  # Draw
                return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board[i, j] == 0:
                        board[i, j] = 1
                        eval_score = minimax(board, depth + 1, alpha, beta, False)
                        board[i, j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board[i, j] == 0:
                        board[i, j] = -1
                        eval_score = minimax(board, depth + 1, alpha, beta, True)
                        board[i, j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Find the best move
    best_score = float('-inf')
    best_move = (0, 0)
    
    for i in range(3):
        for j in range(3):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                score = minimax(board_array, 0, float('-inf'), float('inf'), False)
                board_array[i, j] = 0
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
