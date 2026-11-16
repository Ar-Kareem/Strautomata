
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)
    
    # Get empty positions
    empty_positions = np.argwhere(board_np == 0)
    
    # If no moves left, return something (though game should be over)
    if len(empty_positions) == 0:
        return (0, 0)
    
    # If only one move left, take it
    if len(empty_positions) == 1:
        return tuple(empty_positions[0])
    
    # Find best move using minimax with alpha-beta pruning
    best_move = None
    best_value = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Try each empty position
    for pos in empty_positions:
        row, col = pos[0], pos[1]
        # Make move
        board_np[row, col] = 1
        
        # Evaluate this move with minimax (opponent's turn now)
        value = minimax(board_np, 0, False, alpha, beta)
        
        # Undo move
        board_np[row, col] = 0
        
        # Update best move
        if value > best_value:
            best_value = value
            best_move = (row, col)
            alpha = max(alpha, best_value)
    
    return best_move

def minimax(board: np.ndarray, depth: int, is_maximizing: bool, alpha: float, beta: float) -> float:
    # Check for terminal states
    player_win = check_win(board, 1)
    opponent_win = check_win(board, -1)
    
    if player_win:
        return 1000 - depth  # Prefer faster wins
    if opponent_win:
        return -1000 + depth  # Prefer slower losses
    
    # Check if board is full (draw)
    if np.count_nonzero(board == 0) == 0:
        return 0
    
    # Get empty positions
    empty_positions = np.argwhere(board == 0)
    
    if is_maximizing:  # Player 1's turn
        max_eval = -float('inf')
        for pos in empty_positions:
            row, col = pos[0], pos[1]
            board[row, col] = 1
            eval_score = minimax(board, depth + 1, False, alpha, beta)
            board[row, col] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return max_eval
    else:  # Player -1's turn
        min_eval = float('inf')
        for pos in empty_positions:
            row, col = pos[0], pos[1]
            board[row, col] = -1
            eval_score = minimax(board, depth + 1, True, alpha, beta)
            board[row, col] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break  # Alpha-beta pruning
        return min_eval

def check_win(board: np.ndarray, player: int) -> bool:
    """
    Check if the specified player has won (4 in a row)
    """
    n = 4
    # Check rows
    for i in range(n):
        for j in range(n - 3):
            if all(board[i, j+k] == player for k in range(4)):
                return True
    
    # Check columns
    for j in range(n):
        for i in range(n - 3):
            if all(board[i+k, j] == player for k in range(4)):
                return True
    
    # Check main diagonals (top-left to bottom-right)
    for i in range(n - 3):
        for j in range(n - 3):
            if all(board[i+k, j+k] == player for k in range(4)):
                return True
    
    # Check anti-diagonals (top-right to bottom-left)
    for i in range(n - 3):
        for j in range(3, n):
            if all(board[i+k, j-k] == player for k in range(4)):
                return True
    
    return False
