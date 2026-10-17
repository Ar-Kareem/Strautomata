
import numpy as np
from typing import Optional

def policy(board: list[list[int]]) -> int:
    """
    Returns the best column to play in Connect 4 using minimax with alpha-beta pruning.
    """
    board = np.array(board, dtype=int)
    
    # Column order for searching (center first, then moving outward)
    col_order = [3, 2, 4, 1, 5, 0, 6]
    
    # 1. Check for immediate winning move
    for col in col_order:
        if board[0, col] == 0:
            row = _get_drop_row(board, col)
            board[row, col] = 1
            if _check_winner(board) == 1:
                return col
            board[row, col] = 0
    
    # 2. Check for opponent winning move that must be blocked
    for col in col_order:
        if board[0, col] == 0:
            row = _get_drop_row(board, col)
            board[row, col] = -1
            if _check_winner(board) == -1:
                return col
            board[row, col] = 0
    
    # 3. Use minimax for deeper analysis
    best_score = float('-inf')
    best_col = 3  # Default to center
    
    for col in col_order:
        if board[0, col] == 0:
            row = _get_drop_row(board, col)
            board[row, col] = 1
            score = _minimax(board, 5, False, float('-inf'), float('inf'))
            board[row, col] = 0
            
            if score > best_score:
                best_score = score
                best_col = col
    
    return best_col

def _get_drop_row(board: np.ndarray, col: int) -> int:
    """Find the lowest empty row in the given column."""
    for row in range(5, -1, -1):
        if board[row, col] == 0:
            return row
    return -1

def _check_winner(board: np.ndarray) -> Optional[int]:
    """Check if there's a winner. Returns 1, -1, or None."""
    # Horizontal
    for row in range(6):
        for col in range(4):
            if board[row, col] != 0:
                val = board[row, col]
                if all(board[row, col+i] == val for i in range(4)):
                    return val
    
    # Vertical
    for row in range(3):
        for col in range(7):
            if board[row, col] != 0:
                val = board[row, col]
                if all(board[row+i, col] == val for i in range(4)):
                    return val
    
    # Diagonal (down-right)
    for row in range(3):
        for col in range(4):
            if board[row, col] != 0:
                val = board[row, col]
                if all(board[row+i, col+i] == val for i in range(4)):
                    return val
    
    # Diagonal (down-left)
    for row in range(3):
        for col in range(3, 7):
            if board[row, col] != 0:
                val = board[row, col]
                if all(board[row+i, col-i] == val for i in range(4)):
                    return val
    
    return None

def _evaluate(board: np.ndarray) -> float:
    """Evaluate the board position from player 1's perspective."""
    winner = _check_winner(board)
    if winner == 1:
        return 100000
    elif winner == -1:
        return -100000
    
    score = 0
    
    # Count pieces in center column (strategically important)
    center_col = board[:, 3]
    score += np.sum(center_col == 1) * 3
    score -= np.sum(center_col == -1) * 3
    
    # Evaluate all windows of 4 cells
    windows = []
    
    # Horizontal windows
    for row in range(6):
        for col in range(4):
            windows.append(board[row, col:col+4])
    
    # Vertical windows
    for row in range(3):
        for col in range(7):
            windows.append(board[row:row+4, col])
    
    # Diagonal (down-right) windows
    for row in range(3):
        for col in range(4):
            windows.append(np.array([board[row+i, col+i] for i in range(4)]))
    
    # Diagonal (down-left) windows
    for row in range(3):
        for col in range(3, 7):
            windows.append(np.array([board[row+i, col-i] for i in range(4)]))
    
    for window in windows:
        score += _evaluate_window(window)
    
    return score

def _evaluate_window(window: np.ndarray) -> float:
    """Evaluate a window of 4 cells."""
    my_count = np.sum(window == 1)
    empty_count = np.sum(window == 0)
    opp_count = np.sum(window == -1)
    
    if my_count == 4:
        return 100
    elif my_count == 3 and empty_count == 1:
        return 10
    elif my_count == 2 and empty_count == 2:
        return 3
    elif opp_count == 3 and empty_count == 1:
        return -80  # High priority to block
    elif opp_count == 2 and empty_count == 2:
        return -2
    
    return 0

def _minimax(board: np.ndarray, depth: int, maximizing: bool, 
             alpha: float, beta: float) -> float:
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return _evaluate(board)
    
    winner = _check_winner(board)
    if winner is not None:
        return winner * 100000
    
    valid_cols = [c for c in range(7) if board[0, c] == 0]
    
    if not valid_cols:
        return 0  # Draw
    
    if maximizing:
        max_eval = float('-inf')
        for col in valid_cols:
            row = _get_drop_row(board, col)
            board[row, col] = 1
            eval_score = _minimax(board, depth - 1, False, alpha, beta)
            board[row, col] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for col in valid_cols:
            row = _get_drop_row(board, col)
            board[row, col] = -1
            eval_score = _minimax(board, depth - 1, True, alpha, beta)
            board[row, col] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
