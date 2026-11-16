
import numpy as np
from typing import Tuple, List, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Determines the best move for 4x4 Tic Tac Toe using minimax with alpha-beta pruning.
    The player is 1, opponent is -1, empty is 0.
    """
    board_array = np.array(board)
    
    def check_winner(board: np.ndarray) -> int:
        """Check if there's a winner. Returns 1, -1, 0 for player, opponent, no winner, or 2 for draw."""
        # Check rows, columns, and diagonals for 4 in a row
        for player in [1, -1]:
            # Check rows
            for i in range(4):
                if np.all(board[i, :] == player):
                    return player
            # Check columns
            for j in range(4):
                if np.all(board[:, j] == player):
                    return player
            # Check main diagonal
            if np.all(np.diagonal(board) == player):
                return player
            # Check anti-diagonal
            if np.all(np.diagonal(np.fliplr(board)) == player):
                return player
        return 0
    
    def is_board_full(board: np.ndarray) -> bool:
        """Check if the board is full."""
        return not np.any(board == 0)
    
    def get_valid_moves(board: np.ndarray) -> List[Tuple[int, int]]:
        """Get all valid moves (empty cells)."""
        return [(i, j) for i in range(4) for j in range(4) if board[i, j] == 0]
    
    def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> float:
        """Minimax algorithm with alpha-beta pruning."""
        winner = check_winner(board)
        if winner == 1:  # AI wins
            return 100 - depth
        elif winner == -1:  # Opponent wins
            return depth - 100
        elif is_board_full(board):  # Draw
            return 0
        
        valid_moves = get_valid_moves(board)
        
        if maximizing:
            max_eval = float('-inf')
            for move in valid_moves:
                board[move] = 1
                eval_score = minimax(board, depth + 1, alpha, beta, False)
                board[move] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in valid_moves:
                board[move] = -1
                eval_score = minimax(board, depth + 1, alpha, beta, True)
                board[move] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # First, check if we can win immediately
    valid_moves = get_valid_moves(board_array)
    for move in valid_moves:
        board_array[move] = 1
        if check_winner(board_array) == 1:
            board_array[move] = 0
            return move
        board_array[move] = 0
    
    # Check if opponent can win next move - block them
    for move in valid_moves:
        board_array[move] = -1
        if check_winner(board_array) == -1:
            board_array[move] = 0
            return move
        board_array[move] = 0
    
    # Use minimax to find the best move
    best_score = float('-inf')
    best_move = valid_moves[0]  # Default to first valid move
    
    for move in valid_moves:
        board_array[move] = 1
        score = minimax(board_array, 0, float('-inf'), float('inf'), False)
        board_array[move] = 0
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
