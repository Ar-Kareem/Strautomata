
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns the next move for a 4x4 Tic Tac Toe game.
    """
    def check_winner(board_state):
        """Returns 1 if player1 wins, -1 if player2 wins, 0 if no winner"""
        # Check rows
        for row in board_state:
            if all(x == 1 for x in row):
                return 1
            if all(x == -1 for x in row):
                return -1
        
        # Check columns
        for col in range(4):
            if all(board_state[row][col] == 1 for row in range(4)):
                return 1
            if all(board_state[row][col] == -1 for row in range(4)):
                return -1
        
        # Check diagonals
        if all(board_state[i][i] == 1 for i in range(4)):
            return 1
        if all(board_state[i][i] == -1 for i in range(4)):
            return -1
        
        if all(board_state[i][3-i] == 1 for i in range(4)):
            return 1
        if all(board_state[i][3-i] == -1 for i in range(4)):
            return -1
            
        return 0
    
    def evaluate_position(board_state):
        """Evaluate the board state for the current player (1)"""
        score = 0
        
        # Check rows
        for row in range(4):
            row_count = [board_state[row][col] for col in range(4)]
            ones = row_count.count(1)
            minus_ones = row_count.count(-1)
            if ones == 3 and minus_ones == 0:
                score += 100
            elif ones == 2 and minus_ones == 0:
                score += 10
            elif ones == 1 and minus_ones == 0:
                score += 1
        
        # Check columns
        for col in range(4):
            col_count = [board_state[row][col] for row in range(4)]
            ones = col_count.count(1)
            minus_ones = col_count.count(-1)
            if ones == 3 and minus_ones == 0:
                score += 100
            elif ones == 2 and minus_ones == 0:
                score += 10
            elif ones == 1 and minus_ones == 0:
                score += 1
        
        # Check diagonals
        diag1 = [board_state[i][i] for i in range(4)]
        ones = diag1.count(1)
        minus_ones = diag1.count(-1)
        if ones == 3 and minus_ones == 0:
            score += 100
        elif ones == 2 and minus_ones == 0:
            score += 10
        elif ones == 1 and minus_ones == 0:
            score += 1
            
        diag2 = [board_state[i][3-i] for i in range(4)]
        ones = diag2.count(1)
        minus_ones = diag2.count(-1)
        if ones == 3 and minus_ones == 0:
            score += 100
        elif ones == 2 and minus_ones == 0:
            score += 10
        elif ones == 1 and minus_ones == 0:
            score += 1
            
        return score
    
    def minimax(board_state, depth, is_maximizing, alpha, beta):
        winner = check_winner(board_state)
        if winner == 1:
            return 1000 - depth
        elif winner == -1:
            return -1000 + depth
        elif depth == 0 or all(board_state[row][col] != 0 for row in range(4) for col in range(4)):
            return evaluate_position(board_state)
        
        if is_maximizing:
            max_eval = float('-inf')
            for row in range(4):
                for col in range(4):
                    if board_state[row][col] == 0:
                        board_state[row][col] = 1
                        eval_score = minimax(board_state, depth - 1, False, alpha, beta)
                        board_state[row][col] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for row in range(4):
                for col in range(4):
                    if board_state[row][col] == 0:
                        board_state[row][col] = -1
                        eval_score = minimax(board_state, depth - 1, True, alpha, beta)
                        board_state[row][col] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Simple heuristic approach for optimization
    # First check if I can win immediately
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                board[row][col] = 1
                if check_winner(board) == 1:
                    board[row][col] = 0
                    return (row, col)
                board[row][col] = 0
    
    # Then check if opponent can win and block
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                board[row][col] = -1
                if check_winner(board) == -1:
                    board[row][col] = 0
                    return (row, col)
                board[row][col] = 0
    
    # Try to capture center positions if available
    center_positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for row, col in center_positions:
        if board[row][col] == 0:
            return (row, col)
    
    # If nothing else, make the best available move with minimax
    best_score = float('-inf')
    best_move = (0, 0)
    
    # For a faster response, reduce depth to 2
    for row in range(4):
        for col in range(4):
            if board[row][col] == 0:
                board[row][col] = 1
                score = minimax(board, 2, False, float('-inf'), float('inf'))
                board[row][col] = 0
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
    
    return best_move
