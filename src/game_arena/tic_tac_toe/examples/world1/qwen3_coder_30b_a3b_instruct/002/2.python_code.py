
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determine the best move for the current Tic Tac Toe board state.
    Uses minimax algorithm with alpha-beta pruning for optimal play.
    """
    
    def is_terminal(state):
        """Check if the game has ended and return the winner."""
        # Check rows
        for row in state:
            if abs(sum(row)) == 3:
                return sum(row) // 3
        
        # Check columns
        for col in range(3):
            col_sum = sum(state[row][col] for row in range(3))
            if abs(col_sum) == 3:
                return col_sum // 3
        
        # Check diagonals
        diag1 = sum(state[i][i] for i in range(3))
        diag2 = sum(state[i][2-i] for i in range(3))
        if abs(diag1) == 3:
            return diag1 // 3
        if abs(diag2) == 3:
            return diag2 // 3
            
        # Check for draw (no empty cells)
        if all(state[i][j] != 0 for i in range(3) for j in range(3)):
            return 0
            
        return None  # Game not over
    
    def get_available_moves(state):
        """Get all available moves (empty cells)."""
        moves = []
        for i in range(3):
            for j in range(3):
                if state[i][j] == 0:
                    moves.append((i, j))
        return moves
    
    def minimax(state, depth, is_maximizing, alpha, beta):
        """Minimax algorithm with alpha-beta pruning."""
        result = is_terminal(state)
        
        # Terminal states
        if result is not None:
            return result
            
        if is_maximizing:
            max_eval = -2
            for move in get_available_moves(state):
                row, col = move
                state[row][col] = 1  # My move
                eval_score = minimax(state, depth + 1, False, alpha, beta)
                state[row][col] = 0  # Undo move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = 2
            for move in get_available_moves(state):
                row, col = move
                state[row][col] = -1  # Opponent's move
                eval_score = minimax(state, depth + 1, True, alpha, beta)
                state[row][col] = 0  # Undo move
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move by trying all possible moves
    best_score = -2
    best_move = None
    
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                # Try this move
                board[i][j] = 1  # My move
                score = minimax(board, 0, False, -2, 2)
                board[i][j] = 0  # Undo move
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
    
    return best_move
