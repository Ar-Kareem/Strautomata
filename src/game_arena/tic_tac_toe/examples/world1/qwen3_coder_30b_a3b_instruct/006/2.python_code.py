
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    def minimax(board_state, depth, is_maximizing, alpha, beta):
        # Check for terminal states
        winner = check_winner(board_state)
        if winner == 1:  # AI wins
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return depth - 10
        elif is_board_full(board_state):  # Draw
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    if board_state[i][j] == 0:  # Empty cell
                        board_state[i][j] = 1  # AI plays
                        eval_score = minimax(board_state, depth + 1, False, alpha, beta)
                        board_state[i][j] = 0  # Undo move
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if board_state[i][j] == 0:  # Empty cell
                        board_state[i][j] = -1  # Opponent plays
                        eval_score = minimax(board_state, depth + 1, True, alpha, beta)
                        board_state[i][j] = 0  # Undo move
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return min_eval
    
    def check_winner(b):
        # Check rows, columns, and diagonals
        for i in range(3):
            if b[i][0] == b[i][1] == b[i][2] != 0:
                return b[i][0]
            if b[0][i] == b[1][i] == b[2][i] != 0:
                return b[0][i]
        
        if b[0][0] == b[1][1] == b[2][2] != 0:
            return b[0][0]
        if b[0][2] == b[1][1] == b[2][0] != 0:
            return b[0][2]
        return 0  # No winner
    
    def is_board_full(b):
        for i in range(3):
            for j in range(3):
                if b[i][j] == 0:
                    return False
        return True
    
    # Try to find a winning move or block opponent
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Check if this move wins for us
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
                
                # Check if this move blocks opponent win
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
                
    # If no immediate win/block, use minimax
    best_score = float('-inf')
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                board[i][j] = 1
                score = minimax(board, 0, False, float('-inf'), float('inf'))
                board[i][j] = 0
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move if best_move else (0, 0)
