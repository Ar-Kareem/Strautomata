
import numpy as np
from typing import List, Tuple
import collections

# Global variables for the board dimensions
ROWS = 6
COLS = 7

def check_winner(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won on the board."""
    # Check horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r, c+i] == player for i in range(4)):
                return True
    
    # Check vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            if all(board[r+i, c] == player for i in range(4)):
                return True
    
    # Check diagonal (positive slope)
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r+i, c+i] == player for i in range(4)):
                return True
    
    # Check diagonal (negative slope)
    for r in range(3, ROWS):
        for c in range(COLS - 3):
            if all(board[r-i, c+i] == player for i in range(4)):
                return True
    
    return False

def get_valid_moves(board: np.ndarray) -> List[int]:
    """Get list of columns that are not full."""
    return [c for c in range(COLS) if board[0, c] == 0]

def drop_piece(board: np.ndarray, col: int, player: int) -> Tuple[np.ndarray, int]:
    """Drop a piece in the specified column and return new board and row."""
    new_board = board.copy()
    for r in range(ROWS - 1, -1, -1):
        if new_board[r, col] == 0:
            new_board[r, col] = player
            return new_board, r
    return new_board, -1  # Should not happen if column is valid

def evaluate_window(window: np.ndarray, player: int) -> int:
    """Evaluate a window of 4 pieces for scoring."""
    score = 0
    opponent = -player
    
    player_count = np.count_nonzero(window == player)
    opponent_count = np.count_nonzero(window == opponent)
    empty_count = np.count_nonzero(window == 0)
    
    if player_count == 4:
        score += 1000
    elif player_count == 3 and empty_count == 1:
        score += 100
    elif player_count == 2 and empty_count == 2:
        score += 10
    elif player_count == 1 and empty_count == 3:
        score += 1
        
    if opponent_count == 3 and empty_count == 1:
        score -= 100
    elif opponent_count == 2 and empty_count == 2:
        score -= 10
        
    return score

def evaluate_board(board: np.ndarray, player: int) -> int:
    """Evaluate the entire board position."""
    score = 0
    
    # Score center column preference
    center_array = board[:, COLS//2]
    center_count = np.count_nonzero(center_array == player)
    score += center_count * 3
    
    # Score horizontal windows
    for r in range(ROWS):
        row_array = board[r, :]
        for c in range(COLS - 3):
            window = row_array[c:c+4]
            score += evaluate_window(window, player)
    
    # Score vertical windows
    for c in range(COLS):
        col_array = board[:, c]
        for r in range(ROWS - 3):
            window = col_array[r:r+4]
            score += evaluate_window(window, player)
    
    # Score positive diagonal windows
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+i, c+i] for i in range(4)]
            score += evaluate_window(np.array(window), player)
    
    # Score negative diagonal windows
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            window = [board[r+3-i, c+i] for i in range(4)]
            score += evaluate_window(np.array(window), player)
    
    return score

def minimax(board: np.ndarray, depth: int, alpha: int, beta: int, maximizing: bool, player: int) -> Tuple[int, int]:
    """Minimax algorithm with alpha-beta pruning."""
    valid_moves = get_valid_moves(board)
    
    # Terminal conditions
    if depth == 0 or len(valid_moves) == 0 or check_winner(board, player) or check_winner(board, -player):
        if check_winner(board, player):
            return (1000000, -1)
        elif check_winner(board, -player):
            return (-1000000, -1)
        elif len(valid_moves) == 0:  # Tie
            return (0, -1)
        else:
            return (evaluate_board(board, player), -1)
    
    if maximizing:
        value = -np.inf
        column = valid_moves[0]
        for col in valid_moves:
            new_board, _ = drop_piece(board, col, player)
            new_score, _ = minimax(new_board, depth-1, alpha, beta, False, player)
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, column
    else:
        value = np.inf
        column = valid_moves[0]
        for col in valid_moves:
            new_board, _ = drop_piece(board, col, -player)
            new_score, _ = minimax(new_board, depth-1, alpha, beta, True, player)
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value, column

def policy(board: List[List[int]]) -> int:
    """Main policy function for Connect 4."""
    # Convert to numpy array for efficiency
    np_board = np.array(board)
    
    # Check for immediate winning move
    for col in get_valid_moves(np_board):
        new_board, _ = drop_piece(np_board, col, 1)
        if check_winner(new_board, 1):
            return col
    
    # Check for blocking opponent's winning move
    for col in get_valid_moves(np_board):
        new_board, _ = drop_piece(np_board, col, -1)
        if check_winner(new_board, -1):
            return col
    
    # Use minimax with depth 4 for general play
    try:
        _, column = minimax(np_board, 4, -np.inf, np.inf, True, 1)
        if column != -1 and column in get_valid_moves(np_board):
            return column
    except:
        pass
    
    # Fallback to first valid move
    valid_moves = get_valid_moves(np_board)
    if valid_moves:
        # Prefer center columns
        center_prefs = [3, 2, 4, 1, 5, 0, 6]
        for col in center_prefs:
            if col in valid_moves:
                return col
        return valid_moves[0]
    
    # Should never happen in a valid game
    return 0
