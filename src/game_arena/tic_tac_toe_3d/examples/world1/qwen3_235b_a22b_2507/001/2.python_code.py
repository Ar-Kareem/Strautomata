
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    def is_winner(b: np.ndarray, player: int) -> bool:
        # Check all possible winning lines in 3D
        # There are 49 possible winning lines in 3x3x3
        # Check rows, columns, depths, and diagonals
        
        # Check each 2D plane in each dimension
        for i in range(3):
            # xy planes (fixed z)
            if np.all(b[i, :, :] == player).any() or np.all(b[:, i, :] == player).any() or np.all(b[:, :, i] == player).any():
                return True
            if np.all(b[i, :, i] == player) or np.all(b[i, i, :] == player) or np.all(b[:, i, i] == player):
                return True
        
        # Check main diagonals through the cube
        if (np.all(np.diagonal(b)) == player or 
            np.all(np.diagonal(b[:, :, ::-1])) == player or
            np.all(np.diagonal(b[:, ::-1, :])) == player or
            np.all(np.diagonal(b[::-1, :, :])) == player):
            return True
            
        # Check the four space diagonals
        if (b[0,0,0] == b[1,1,1] == b[2,2,2] == player or
            b[0,0,2] == b[1,1,1] == b[2,2,0] == player or
            b[0,2,0] == b[1,1,1] == b[2,0,2] == player or
            b[0,2,2] == b[1,1,1] == b[2,0,0] == player):
            return True
            
        return False
    
    def get_empty_cells(b: np.ndarray) -> List[Tuple[int, int, int]]:
        empty = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if b[i, j, k] == 0:
                        empty.append((i, j, k))
        return empty
    
    def evaluate(b: np.ndarray) -> int:
        if is_winner(b, 1):  # AI wins
            return 1000
        if is_winner(b, -1):  # Opponent wins
            return -1000
        return 0  # No winner yet
    
    def minimax(b: np.ndarray, depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
        score = evaluate(b)
        
        # If AI has won
        if score == 1000:
            return score - depth  # Prefer faster wins
        
        # If opponent has won
        if score == -1000:
            return score + depth  # Prefer slower losses
        
        # If no more moves or depth limit
        empty_cells = get_empty_cells(b)
        if len(empty_cells) == 0:
            return 0
        
        if depth == 0:
            return 0
            
        if is_maximizing:
            max_eval = float('-inf')
            for (i, j, k) in empty_cells:
                b[i, j, k] = 1  # AI's move
                eval_score = minimax(b, depth - 1, alpha, beta, False)
                b[i, j, k] = 0  # Undo move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for (i, j, k) in empty_cells:
                b[i, j, k] = -1  # Opponent's move
                eval_score = minimax(b, depth - 1, alpha, beta, True)
                b[i, j, k] = 0  # Undo move
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Get all empty cells
    empty_cells = get_empty_cells(board_array)
    
    if len(empty_cells) == 27:
        # First move - take center for strategic advantage
        if (1, 1, 1) in empty_cells:
            return (1, 1, 1)
    
    # Check for immediate win
    for (i, j, k) in empty_cells:
        board_array[i, j, k] = 1
        if is_winner(board_array, 1):
            board_array[i, j, k] = 0
            return (i, j, k)
        board_array[i, j, k] = 0
    
    # Check for opponent's immediate win and block
    for (i, j, k) in empty_cells:
        board_array[i, j, k] = -1
        if is_winner(board_array, -1):
            board_array[i, j, k] = 0
            return (i, j, k)
        board_array[i, j, k] = 0
    
    # Use minimax to determine best move
    best_score = float('-inf')
    best_move = empty_cells[0]  # fallback to first empty cell
    
    # Adjust depth based on remaining moves
    remaining_moves = len(empty_cells)
    depth = min(6, remaining_moves)  # Don't go too deep when many moves left
    
    for (i, j, k) in empty_cells:
        board_array[i, j, k] = 1
        move_score = minimax(board_array, depth, float('-inf'), float('inf'), False)
        board_array[i, j, k] = 0
        
        if move_score > best_score:
            best_score = move_score
            best_move = (i, j, k)
    
    return best_move
