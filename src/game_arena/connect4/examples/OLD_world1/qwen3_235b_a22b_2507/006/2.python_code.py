
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning and heuristic evaluation.
    Prioritizes winning moves, blocks opponent wins, and evaluates board positions.
    """
    np_board = np.array(board)
    rows, cols = np_board.shape
    
    def is_valid_move(col):
        return np_board[0, col] == 0
    
    def make_move(board, col, player):
        new_board = board.copy()
        for row in range(rows - 1, -1, -1):
            if new_board[row, col] == 0:
                new_board[row, col] = player
                break
        return new_board
    
    def check_winner(board, player):
        # Check horizontal
        for row in range(rows):
            for col in range(cols - 3):
                if all(board[row, col + i] == player for i in range(4)):
                    return True
        
        # Check vertical
        for row in range(rows - 3):
            for col in range(cols):
                if all(board[row + i, col] == player for i in range(4)):
                    return True
        
        # Check diagonal (positive slope)
        for row in range(rows - 3):
            for col in range(cols - 3):
                if all(board[row + i, col + i] == player for i in range(4)):
                    return True
        
        # Check diagonal (negative slope)
        for row in range(3, rows):
            for col in range(cols - 3):
                if all(board[row - i, col + i] == player for i in range(4)):
                    return True
        
        return False
    
    def evaluate_window(window, player):
        """Evaluate a window of 4 cells for the given player"""
        score = 0
        opp_player = -player
        
        player_count = np.sum(window == player)
        opp_count = np.sum(window == opp_player)
        empty_count = np.sum(window == 0)
        
        if player_count == 4:
            score += 1000
        elif player_count == 3 and empty_count == 1:
            score += 100
        elif player_count == 2 and empty_count == 2:
            score += 10
        
        if opp_count == 3 and empty_count == 1:
            score -= 90
        
        return score
    
    def score_position(board, player):
        """Score the entire board position"""
        score = 0
        
        # Center column preference
        center_col = board[:, cols // 2]
        center_count = np.sum(center_col == player)
        score += center_count * 6
        
        # Score horizontal
        for row in range(rows):
            for col in range(cols - 3):
                window = board[row, col:col + 4]
                score += evaluate_window(window, player)
        
        # Score vertical
        for row in range(rows - 3):
            for col in range(cols):
                window = board[row:row + 4, col]
                score += evaluate_window(window, player)
        
        # Score diagonal (positive slope)
        for row in range(rows - 3):
            for col in range(cols - 3):
                window = np.array([board[row + i, col + i] for i in range(4)])
                score += evaluate_window(window, player)
        
        # Score diagonal (negative slope)
        for row in range(3, rows):
            for col in range(cols - 3):
                window = np.array([board[row - i, col + i] for i in range(4)])
                score += evaluate_window(window, player)
        
        return score
    
    def get_valid_moves(board):
        """Get all valid column moves"""
        return [col for col in range(cols) if is_valid_move(col)]
    
    def minimax(board, depth, alpha, beta, maximizing_player, player):
        """Minimax with alpha-beta pruning"""
        valid_moves = get_valid_moves(board)
        
        # Terminal conditions
        if depth == 0 or len(valid_moves) == 0:
            return score_position(board, player)
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in valid_moves:
                child_board = make_move(board, col, player)
                if check_winner(child_board, player):
                    return 10000 - depth  # Prefer faster wins
                
                eval_score = minimax(child_board, depth - 1, alpha, beta, False, player)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return max_eval
        else:
            min_eval = float('inf')
            opp_player = -player
            for col in valid_moves:
                child_board = make_move(board, col, opp_player)
                if check_winner(child_board, opp_player):
                    return -10000 + depth  # Penalize positions where opponent wins
                
                eval_score = minimax(child_board, depth - 1, alpha, beta, True, player)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                
                if beta <= alpha:
                    break  # Alpha-beta pruning
            
            return min_eval
    
    # First, check if we can win immediately
    valid_moves = get_valid_moves(np_board)
    for col in valid_moves:
        child_board = make_move(np_board, col, 1)
        if check_winner(child_board, 1):
            return col
    
    # Then, check if we need to block opponent's winning move
    for col in valid_moves:
        child_board = make_move(np_board, col, -1)
        if check_winner(child_board, -1):
            return col
    
    # Use minimax to determine best move
    best_score = float('-inf')
    best_col = valid_moves[0]  # default to first valid move
    
    # Adjust depth based on game stage
    # Count number of pieces on board to determine game stage
    pieces_count = np.sum(np_board != 0)
    depth = 6 if pieces_count < 20 else 5  # Deeper search in early/mid game
    
    for col in valid_moves:
        child_board = make_move(np_board, col, 1)
        score = minimax(child_board, depth - 1, float('-inf'), float('inf'), False, 1)
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
