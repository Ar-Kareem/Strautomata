
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    """
    Policy function for Connect 4: returns the best column index to play.
    """
    def is_valid_move(board, col):
        return board[0][col] == 0

    def get_valid_moves(board):
        return [col for col in range(7) if is_valid_move(board, col)]

    def drop_disc(board, col, player):
        new_board = [row[:] for row in board]  # Deep copy
        for row in range(5, -1, -1):  # Start from bottom
            if new_board[row][col] == 0:
                new_board[row][col] = player
                break
        return new_board

    def check_winner(board, player):
        # Check horizontal
        for row in range(6):
            for col in range(4):
                if all(board[row][col + i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(3):
            for col in range(7):
                if all(board[row + i][col] == player for i in range(4)):
                    return True
        
        # Check diagonal (positive slope)
        for row in range(3):
            for col in range(4):
                if all(board[row + i][col + i] == player for i in range(4)):
                    return True
        
        # Check diagonal (negative slope)
        for row in range(3, 6):
            for col in range(4):
                if all(board[row - i][col + i] == player for i in range(4)):
                    return True
        
        return False

    def evaluate_board(board):
        # Simple heuristic evaluation
        score = 0
        
        # Center column preference (index 3)
        center_count = sum(1 for row in range(6) if board[row][3] == 1)
        score += center_count * 3
        
        # Horizontal lines
        for row in range(6):
            for col in range(4):
                window = [board[row][col + i] for i in range(4)]
                score += evaluate_window(window)
        
        # Vertical lines
        for row in range(3):
            for col in range(7):
                window = [board[row + i][col] for i in range(4)]
                score += evaluate_window(window)
        
        # Diagonal (positive slope)
        for row in range(3):
            for col in range(4):
                window = [board[row + i][col + i] for i in range(4)]
                score += evaluate_window(window)
        
        # Diagonal (negative slope)
        for row in range(3, 6):
            for col in range(4):
                window = [board[row - i][col + i] for i in range(4)]
                score += evaluate_window(window)
        
        return score

    def evaluate_window(window):
        score = 0
        player_count = window.count(1)
        opponent_count = window.count(-1)
        empty_count = window.count(0)
        
        if player_count == 4:
            score += 100
        elif player_count == 3 and empty_count == 1:
            score += 10
        elif player_count == 2 and empty_count == 2:
            score += 2
        
        if opponent_count == 3 and empty_count == 1:
            score -= 80  # Block opponent from winning
            
        return score

    def minimax(board, depth, alpha, beta, maximizing_player):
        valid_moves = get_valid_moves(board)
        
        # Terminal conditions
        if check_winner(board, 1):
            return 1000000000
        elif check_winner(board, -1):
            return -1000000000
        elif depth == 0 or not valid_moves:
            return evaluate_board(board)
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in valid_moves:
                new_board = drop_disc(board, col, 1)
                eval_score = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                new_board = drop_disc(board, col, -1)
                eval_score = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval

    # Root call with limited depth for performance
    valid_moves = get_valid_moves(board)
    
    if not valid_moves:
        return 0
    
    # Try depth 5 first for good performance
    best_score = float('-inf')
    best_col = valid_moves[0]
    
    for col in valid_moves:
        new_board = drop_disc(board, col, 1)
        score = minimax(new_board, 5, float('-inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
