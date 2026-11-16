
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determines the next move for 3x3x3 3D Tic Tac Toe using a minimax algorithm with alpha-beta pruning.
    """
    board_array = np.array(board)
    n = 3
    
    # Check if board is already numpy array, if not convert it
    if not isinstance(board_array, np.ndarray):
        board_array = np.array(board_array)
    
    def is_winner(b, player):
        """Check if the given player has won"""
        for i in range(n):
            for j in range(n):
                # Check lines along z-axis
                if np.all(b[i, j, :] == player):
                    return True
                # Check lines along y-axis
                if np.all(b[i, :, j] == player):
                    return True
                # Check lines along x-axis
                if np.all(b[:, i, j] == player):
                    return True
        
        # Check diagonals on each xy, xz, yz plane
        for k in range(n):
            # xy planes
            if np.all(np.diagonal(b[:, :, k]) == player) or np.all(np.diagonal(np.fliplr(b[:, :, k])) == player):
                return True
            # xz planes
            if np.all(np.diagonal(b[:, k, :]) == player) or np.all(np.diagonal(np.fliplr(b[:, k, :])) == player):
                return True
            # yz planes
            if np.all(np.diagonal(b[k, :, :]) == player) or np.all(np.diagonal(np.fliplr(b[k, :, :])) == player):
                return True
        
        # Check 3D diagonals
        if (b[0,0,0] == player and b[1,1,1] == player and b[2,2,2] == player) or \
           (b[0,0,2] == player and b[1,1,1] == player and b[2,2,0] == player) or \
           (b[0,2,0] == player and b[1,1,1] == player and b[2,0,2] == player) or \
           (b[0,2,2] == player and b[1,1,1] == player and b[2,0,0] == player):
            return True
            
        return False
    
    def get_empty_cells(b):
        """Get list of empty cells"""
        empty_cells = []
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    if b[i, j, k] == 0:
                        empty_cells.append((i, j, k))
        return empty_cells
    
    def evaluate(b):
        """Evaluate the board position"""
        if is_winner(b, 1):  # Current player wins
            return 10
        elif is_winner(b, -1):  # Opponent wins
            return -10
        else:
            return 0
    
    def minimax(b, depth, alpha, beta, is_maximizing):
        """Minimax algorithm with alpha-beta pruning"""
        score = evaluate(b)
        
        # If maximizer or minimizer has won
        if score == 10 or score == -10:
            return score
        
        # If no more moves and no winner
        empty_cells = get_empty_cells(b)
        if len(empty_cells) == 0:
            return 0
        
        if is_maximizing:
            max_eval = float('-inf')
            for cell in empty_cells:
                i, j, k = cell
                b[i, j, k] = 1  # Current player's move
                eval_score = minimax(b, depth + 1, alpha, beta, False)
                b[i, j, k] = 0  # Undo move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for cell in empty_cells:
                i, j, k = cell
                b[i, j, k] = -1  # Opponent's move
                eval_score = minimax(b, depth + 1, alpha, beta, True)
                b[i, j, k] = 0  # Undo move
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Find the best move
    empty_cells = get_empty_cells(board_array)
    
    if len(empty_cells) == 27:  # First move
        return (1, 1, 1)  # Take center
    
    best_value = float('-inf')
    best_move = empty_cells[0]  # Default to first empty cell
    
    for cell in empty_cells:
        i, j, k = cell
        board_array[i, j, k] = 1  # Try our move
        move_value = minimax(board_array, 0, float('-inf'), float('inf'), False)
        board_array[i, j, k] = 0  # Undo move
        
        if move_value > best_value:
            best_value = move_value
            best_move = cell
    
    return best_move
