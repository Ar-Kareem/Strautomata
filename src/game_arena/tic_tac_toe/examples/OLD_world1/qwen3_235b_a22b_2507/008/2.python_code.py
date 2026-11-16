
import numpy as np
from typing import Tuple, List

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns the next move for Tic Tac Toe using minimax algorithm with alpha-beta pruning.
    1 is the player (us), -1 is the opponent.
    """
    board_array = np.array(board)
    
    def check_winner(b):
        # Check rows, columns, and diagonals
        for i in range(3):
            if abs(sum(b[i])) == 3:
                return b[i][0]
            if abs(sum(b[:, i])) == 3:
                return b[0][i]
        
        if abs(sum([b[i][i] for i in range(3)])) == 3:
            return b[0][0]
        if abs(sum([b[i][2-i] for i in range(3)])) == 3:
            return b[0][2]
        
        return 0
    
    def is_terminal(b):
        return check_winner(b) != 0 or not (b == 0).any()
    
    def evaluate(b):
        winner = check_winner(b)
        if winner == 1:
            return 10  # We win
        elif winner == -1:
            return -10  # Opponent wins
        else:
            return 0  # Draw or ongoing
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        if is_terminal(b) or depth == 0:
            return evaluate(b)
        
        if is_maximizing:
            max_eval = -float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = 1  # Our move
                        eval_score = minimax(b, depth - 1, alpha, beta, False)
                        b[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    if b[i][j] == 0:
                        b[i][j] = -1  # Opponent's move
                        eval_score = minimax(b, depth - 1, alpha, beta, True)
                        b[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    # Find all valid moves
    valid_moves = [(i, j) for i in range(3) for j in range(3) if board_array[i][j] == 0]
    
    if not valid_moves:
        return (0, 0)  # Should not happen in valid game
    
    # If it's the first move, take center or corner
    if len(valid_moves) == 9:
        return (1, 1)  # Take center
    
    # If it's second move and center is free, take it; otherwise corner
    if len(valid_moves) == 8:
        if board_array[1][1] == 0:
            return (1, 1)
        else:
            corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
            return next(move for move in corners if move in valid_moves)
    
    # Use minimax to find the best move
    best_score = -float('inf')
    best_move = valid_moves[0]
    
    for move in valid_moves:
        i, j = move
        board_array[i][j] = 1  # Try our move
        score = minimax(board_array, 9, -float('inf'), float('inf'), False)
        board_array[i][j] = 0  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
