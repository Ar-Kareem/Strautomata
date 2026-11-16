
import copy
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Tic Tac Toe policy function that returns the best move for player 1.
    Uses minimax algorithm with alpha-beta pruning for optimal play.
    """
    
    def check_winner(board: List[List[int]]) -> int:
        """Check if there's a winner. Returns 1 (player 1), -1 (player -1), or 0 (draw/none)."""
        # Check rows and columns
        for i in range(3):
            if all(board[i][j] == 1 for j in range(3)):
                return 1
            if all(board[i][j] == -1 for j in range(3)):
                return -1
            if all(board[j][i] == 1 for j in range(3)):
                return 1
            if all(board[j][i] == -1 for j in range(3)):
                return -1
        
        # Check diagonals
        if all(board[i][i] == 1 for i in range(3)):
            return 1
        if all(board[i][i] == -1 for i in range(3)):
            return -1
        if all(board[i][2-i] == 1 for i in range(3)):
            return 1
        if all(board[i][2-i] == -1 for i in range(3)):
            return -1
        
        return 0
    
    def get_empty_positions(board: List[List[int]]) -> List[Tuple[int, int]]:
        """Get list of empty positions on the board."""
        empty = []
        for i in range(3):
            for j in range(3):
                if board[i][j] == 0:
                    empty.append((i, j))
        return empty
    
    def minimax(board: List[List[int]], depth: int, is_maximizing: bool, 
                 alpha: int, beta: int) -> int:
        """Minimax algorithm with alpha-beta pruning."""
        winner = check_winner(board)
        
        if winner == 1:  # Player wins
            return 10 - depth
        elif winner == -1:  # Opponent wins
            return depth - 10
        elif not get_empty_positions(board):  # Draw
            return 0
        
        empty_positions = get_empty_positions(board)
        
        if is_maximizing:  # Player's turn (1)
            max_eval = -1000
            for i, j in empty_positions:
                board[i][j] = 1
                eval_score = minimax(board, depth + 1, False, alpha, beta)
                board[i][j] = 0
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:  # Opponent's turn (-1)
            min_eval = 1000
            for i, j in empty_positions:
                board[i][j] = -1
                eval_score = minimax(board, depth + 1, True, alpha, beta)
                board[i][j] = 0
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval
    
    # Check for immediate winning moves first
    empty_positions = get_empty_positions(board)
    for i, j in empty_positions:
        board[i][j] = 1
        if check_winner(board) == 1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Check for immediate blocks
    for i, j in empty_positions:
        board[i][j] = -1
        if check_winner(board) == -1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Use minimax for strategic play
    best_score = -1000
    best_moves = []
    
    for i, j in empty_positions:
        board[i][j] = 1
        score = minimax(board, 0, False, -1000, 1000)
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_moves = [(i, j)]
        elif score == best_score:
            best_moves.append((i, j))
    
    # Add some randomness to avoid being predictable
    # but prioritize strategic positions
    if len(best_moves) > 1:
        # Prefer center, then corners, then edges
        center_preferred = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
        for pos in center_preferred:
            if pos in best_moves:
                return pos
    
    return random.choice(best_moves) if best_moves else (0, 0)
