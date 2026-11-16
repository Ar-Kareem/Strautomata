
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Minimax algorithm with alpha-beta pruning for 4x4 Tic Tac Toe.
    The goal is to get 4 in a row (horizontally, vertically, or diagonally).
    """
    board_array = np.array(board)
    
    def is_winner(board, player):
        """Check if player has won"""
        # Check rows
        for i in range(4):
            for j in range(1):
                if all(board[i, j+k] == player for k in range(4)):
                    return True
        
        # Check columns
        for j in range(4):
            for i in range(1):
                if all(board[i+k, j] == player for k in range(4)):
                    return True
        
        # Check diagonals
        if all(board[i, i] == player for i in range(4)):
            return True
        if all(board[i, 3-i] == player for i in range(4)):
            return True
        
        # Check other diagonals of length 4
        if all(board[i, j+i] == player for i in range(4) for j in range(1) if j+i < 4):
            # This is complex, let's check specific diagonals
            if all(board[i, i] == player for i in range(4)): return True
            if all(board[i, i+1] == player for i in range(3)): return True  # Not possible for length 4
        
        # Actually, in 4x4 we need to check all possible 4-length diagonals
        # Main diagonals
        if all(board[i, i] == player for i in range(4)): return True
        if all(board[i, 3-i] == player for i in range(4)): return True
        
        return False
    
    def evaluate(board):
        """Evaluate the board position"""
        if is_winner(board, 1):  # AI wins
            return 1000
        if is_winner(board, -1):  # Opponent wins
            return -1000
        
        # Count potential lines for each player
        score = 0
        
        # Check all possible 4-in-a-row positions
        lines = []
        
        # Rows
        for i in range(4):
            lines.append(board[i, :])
        
        # Columns
        for j in range(4):
            lines.append(board[:, j])
        
        # Diagonals
        lines.append(np.diag(board))
        lines.append(np.diag(np.fliplr(board)))
        
        for line in lines:
            player_count = np.sum(line == 1)
            opponent_count = np.sum(line == -1)
            empty_count = np.sum(line == 0)
            
            if opponent_count == 0:  # Only AI and empty cells
                if player_count == 3:  # One move from winning
                    score += 100
                else:
                    score += player_count
            elif player_count == 0:  # Only opponent and empty cells
                if opponent_count == 3:  # Opponent one move from winning - block!
                    score -= 500
                else:
                    score -= opponent_count * 2
        
        return score
    
    def get_valid_moves(board):
        """Get all empty positions"""
        return [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        """Minimax algorithm with alpha-beta pruning"""
        if depth == 0 or is_winner(board, 1) or is_winner(board, -1) or len(get_valid_moves(board)) == 0:
            return evaluate(board)
        
        if is_maximizing:
            max_eval = float('-inf')
            for move in get_valid_moves(board):
                board[move[0], move[1]] = 1
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[move[0], move[1]] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for move in get_valid_moves(board):
                board[move[0], move[1]] = -1
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[move[0], move[1]] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval
    
    # Find the best move
    valid_moves = get_valid_moves(board_array)
    if not valid_moves:
        return (0, 0)  # Should not happen in normal gameplay
    
    # If it's the first move, take the center
    if len(valid_moves) == 16:
        return (1, 1)
    
    best_move = valid_moves[0]
    best_value = float('-inf')
    
    # Depth depends on number of empty cells to stay within time limits
    depth = 4 if len(valid_moves) > 8 else 6
    
    for move in valid_moves:
        board_array[move[0], move[1]] = 1
        move_value = minimax(board_array, depth, float('-inf'), float('inf'), False)
        board_array[move[0], move[1]] = 0
        
        if move_value > best_value:
            best_value = move_value
            best_move = move
    
    return best_move
