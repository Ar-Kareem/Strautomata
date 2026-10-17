
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Minimax policy for Tic Tac Toe with alpha-beta pruning.
    Board: 3x3 list of lists, where:
        0 = empty
        1 = player (us)
        -1 = opponent
    Returns (row, col) move.
    """
    board = np.array(board)
    
    def is_winner(board, player):
        # Check rows, columns, and diagonals
        for i in range(3):
            if all(board[i, :] == player) or all(board[:, i] == player):
                return True
        if all(np.diag(board) == player) or all(np.diag(np.fliplr(board)) == player):
            return True
        return False
    
    def is_terminal(board):
        if is_winner(board, 1) or is_winner(board, -1):
            return True
        if not (board == 0).any():  # No empty cells
            return True
        return False
    
    def evaluate(board):
        if is_winner(board, 1):
            return 1
        if is_winner(board, -1):
            return -1
        return 0
    
    def minimax(board, depth, alpha, beta, maximizing_player):
        if is_terminal(board):
            return evaluate(board)
        
        if maximizing_player:
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
    
    best_move = None
    best_value = float('-inf')
    
    # Try each available move
    for i in range(3):
        for j in range(3):
            if board[i, j] == 0:
                board[i, j] = 1  # Place our mark
                move_value = minimax(board, 0, float('-inf'), float('inf'), False)
                board[i, j] = 0  # Undo move
                
                if move_value > best_value:
                    best_value = move_value
                    best_move = (i, j)
    
    # If no best move found (shouldn't happen in valid game), pick first available
    if best_move is None:
        for i in range(3):
            for j in range(3):
                if board[i, j] == 0:
                    return (i, j)
    
    return best_move
