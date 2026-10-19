
import numpy as np
from typing import Tuple, List, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Minimax-based policy for 4x4 Tic Tac Toe with alpha-beta pruning.
    Prioritizes winning moves, blocks opponent wins, and uses board evaluation.
    """
    board_array = np.array(board)
    
    # Check for immediate winning move
    win_move = find_winning_move(board_array, 1)
    if win_move:
        return win_move
    
    # Check to block opponent's winning move
    block_move = find_winning_move(board_array, -1)
    if block_move:
        return block_move
    
    # Use minimax with depth limit for best move
    best_move = minimax_move(board_array, depth=6)
    if best_move:
        return best_move
    
    # Fallback: return first available move
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                return (i, j)
    
    return (0, 0)  # Should never reach here in valid game

def find_winning_move(board: np.ndarray, player: int) -> Optional[Tuple[int, int]]:
    """Find a move that wins immediately for the given player."""
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                board[i, j] = player
                if check_winner(board) == player:
                    board[i, j] = 0
                    return (i, j)
                board[i, j] = 0
    return None

def check_winner(board: np.ndarray) -> int:
    """Check if there's a winner. Return 1, -1, or 0 (no winner yet)."""
    # Check rows and columns
    for i in range(4):
        row_sum = np.sum(board[i, :])
        if abs(row_sum) == 4:
            return 1 if row_sum == 4 else -1
        
        col_sum = np.sum(board[:, i])
        if abs(col_sum) == 4:
            return 1 if col_sum == 4 else -1
    
    # Check diagonals
    diag1_sum = np.sum(board.diagonal())
    if abs(diag1_sum) == 4:
        return 1 if diag1_sum == 4 else -1
    
    diag2_sum = np.sum(np.fliplr(board).diagonal())
    if abs(diag2_sum) == 4:
        return 1 if diag2_sum == 4 else -1
    
    return 0

def is_terminal(board: np.ndarray) -> bool:
    """Check if the game is over."""
    if check_winner(board) != 0:
        return True
    
    # Check for draw (no empty spaces)
    return np.all(board != 0)

def evaluate_board(board: np.ndarray) -> float:
    """Heuristic evaluation of board position."""
    if check_winner(board) == 1:
        return 1000
    elif check_winner(board) == -1:
        return -1000
    elif np.all(board != 0):  # Draw
        return 0
    
    score = 0
    
    # Evaluate rows
    for i in range(4):
        row = board[i, :]
        score += evaluate_line(row)
    
    # Evaluate columns
    for j in range(4):
        col = board[:, j]
        score += evaluate_line(col)
    
    # Evaluate diagonals
    score += evaluate_line(board.diagonal())
    score += evaluate_line(np.fliplr(board).diagonal())
    
    return score

def evaluate_line(line: np.ndarray) -> int:
    """Evaluate a single row, column, or diagonal."""
    player_count = np.sum(line == 1)
    opponent_count = np.sum(line == -1)
    empty_count = np.sum(line == 0)
    
    # If both players have marks in this line, it's blocked
    if player_count > 0 and opponent_count > 0:
        return 0
    
    # Score based on number of marks and empties
    if player_count > 0:
        if player_count == 3:
            return 100  # Close to winning
        elif player_count == 2:
            return 10
        elif player_count == 1:
            return 1
    
    if opponent_count > 0:
        if opponent_count == 3:
            return -100  # Close to losing
        elif opponent_count == 2:
            return -10
        elif opponent_count == 1:
            return -1
    
    return 0

def minimax_move(board: np.ndarray, depth: int) -> Optional[Tuple[int, int]]:
    """Find the best move using minimax with alpha-beta pruning."""
    best_score = float('-inf')
    best_move = None
    alpha = float('-inf')
    beta = float('inf')
    
    for i in range(4):
        for j in range(4):
            if board[i, j] == 0:
                board[i, j] = 1  # Try our move
                score = minimax(board, depth-1, alpha, beta, False)
                board[i, j] = 0  # Undo move
                
                if score > best_score:
                    best_score = score
                    best_move = (i, j)
                
                alpha = max(alpha, best_score)
                if beta <= alpha:
                    break
    
    return best_move

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, is_maximizing: bool) -> float:
    """Minimax algorithm with alpha-beta pruning."""
    if depth == 0 or is_terminal(board):
        return evaluate_board(board)
    
    if is_maximizing:
        max_eval = float('-inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = 1
                    eval_score = minimax(board, depth-1, alpha, beta, False)
                    board[i, j] = 0
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break
        return max_eval
    else:
        min_eval = float('inf')
        for i in range(4):
            for j in range(4):
                if board[i, j] == 0:
                    board[i, j] = -1
                    eval_score = minimax(board, depth-1, alpha, beta, True)
                    board[i, j] = 0
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break
        return min_eval
