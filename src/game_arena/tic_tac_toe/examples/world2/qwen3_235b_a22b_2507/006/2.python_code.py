
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    board_array = np.array(board)
    
    def is_winner(b: np.ndarray, player: int) -> bool:
        # Check rows
        for i in range(4):
            if np.all(b[i, :] == player):
                return True
        # Check columns
        for j in range(4):
            if np.all(b[:, j] == player):
                return True
        # Check diagonals
        if np.all(np.diag(b) == player) or np.all(np.diag(np.fliplr(b)) == player):
            return True
        return False
    
    def is_terminal(b: np.ndarray) -> tuple:
        # Returns (is_terminal, score)
        if is_winner(b, 1):  # I win
            return True, 1
        if is_winner(b, -1):  # Opponent wins
            return True, -1
        if not np.any(b == 0):  # Draw
            return True, 0
        return False, 0
    
    def get_valid_moves(b: np.ndarray) -> List[Tuple[int, int]]:
        return [(i, j) for i in range(4) for j in range(4) if b[i, j] == 0]
    
    def minimax(b: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        is_term, score = is_terminal(b)
        if is_term or depth == 0:
            return score
        
        if maximizing:
            max_eval = float('-inf')
            for i in range(4):
                for j in range(4):
                    if b[i, j] == 0:
                        b[i, j] = 1
                        eval_score = minimax(b, depth - 1, alpha, beta, False)
                        b[i, j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(4):
                for j in range(4):
                    if b[i, j] == 0:
                        b[i, j] = -1
                        eval_score = minimax(b, depth - 1, alpha, beta, True)
                        b[i, j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
                if beta <= alpha:
                    break
            return min_eval
    
    # Get all valid moves
    valid_moves = get_valid_moves(board_array)
    
    # If it's the first move, take center position or (0,0) as default
    if len(valid_moves) == 16:
        return (1, 1)  # Good opening move
    
    # Find the best move using minimax
    best_score = float('-inf')
    best_move = valid_moves[0]
    
    for move in valid_moves:
        i, j = move
        board_array[i, j] = 1
        score = minimax(board_array, 8, float('-inf'), float('inf'), False)
        board_array[i, j] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
