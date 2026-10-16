
import numpy as np
from typing import Optional, List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    return find_best_move(board)

def evaluate(board: np.ndarray) -> int:
    """Evaluate the board state for the AI (player 1)."""
    for player in [1, -1]:
        # Check rows and columns
        for i in range(4):
            if all(board[i, j] == player for j in range(4)):  # row
                return 10 if player == 1 else -10
            if all(board[j, i] == player for i in range(4)):  # column
                return 10 if player == 1 else -10
        
        # Check diagonals
        if all(board[i, i] == player for i in range(4)):  # main diagonal
            return 10 if player == 1 else -10
        if all(board[i, 3 - i] == player for i in range(4)):  # anti-diagonal
            return 10 if player == 1 else -10
    
    return 0  # No winner yet

def is_moves_left(board: np.ndarray) -> bool:
    """Check if there are moves remaining on the board."""
    return 0 in board

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: int, beta: int) -> int:
    """Minimax algorithm with alpha-beta pruning."""
    score = evaluate(board)
    
    if score == 10:  # AI wins
        return score - depth
    if score == -10:  # Opponent wins
        return score + depth
    if not is_moves_left(board):  # Draw
        return 0
    
    if is_maximizing:
        best = -float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = 1  # AI move
                    val = minimax(board, depth + 1, False, alpha, beta)
                    board[i, j] = 0  # Undo move
                    best = max(best, val)
                    alpha = max(alpha, best)
                    if beta <= alpha:
                        break
        return best
    else:
        best = float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = -1  # Opponent move
                    val = minimax(board, depth + 1, True, alpha, beta)
                    board[i, j] = 0  # Undo move
                    best = min(best, val)
                    beta = min(beta, best)
                    if beta <= alpha:
                        break
        return best

def find_best_move(board: List[List[int]]) -> Tuple[int, int]:
    """Find the best move for the AI using minimax."""
    np_board = np.array(board)
    best_val = -float('inf')
    best_move = (-1, -1)
    
    for i in range(4):
        for j in range(4):
            if np_board[i, j] == 0:
                np_board[i, j] = 1  # Try the move
                move_val = minimax(np_board, 0, False, -float('inf'), float('inf'))
                np_board[i, j] = 0  # Undo the move
                
                if move_val > best_val:
                    best_move = (i, j)
                    best_val = move_val
                elif move_val == best_val:
                    # For equal moves, prefer center positions
                    center_score = (3 - abs(i - 1.5) - abs(j - 1.5))
                    current_center_score = (3 - abs(best_move[0] - 1.5) - abs(best_move[1] - 1.5))
                    if center_score > current_center_score:
                        best_move = (i, j)
                        best_val = move_val
    
    if best_move == (-1, -1):  # Shouldn't happen if board isn't full
        # Find first available move if no best move found (fallback)
        for i in range(4):
            for j in range(4):
                if np_board[i, j] == 0:
                    return (i, j)
    
    return best_move
