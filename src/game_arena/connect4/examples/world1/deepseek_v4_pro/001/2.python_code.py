
import numpy as np
from typing import List, Tuple
import math
import time

ROWS = 6
COLS = 7
EMPTY = 0
PLAYER = 1
OPPONENT = -1

# Weights for positional evaluation
POSITION_WEIGHTS = np.array([
    [3, 4, 5, 7, 5, 4, 3],
    [4, 6, 8, 10, 8, 6, 4],
    [5, 8, 11, 13, 11, 8, 5],
    [5, 8, 11, 13, 11, 8, 5],
    [4, 6, 8, 10, 8, 6, 4],
    [3, 4, 5, 7, 5, 4, 3]
])

def is_valid_move(board: np.ndarray, col: int) -> bool:
    return board[0][col] == EMPTY

def get_valid_moves(board: np.ndarray) -> List[int]:
    return [col for col in range(COLS) if is_valid_move(board, col)]

def make_move(board: np.ndarray, col: int, player: int) -> np.ndarray:
    new_board = board.copy()
    for row in range(ROWS-1, -1, -1):
        if new_board[row][col] == EMPTY:
            new_board[row][col] = player
            break
    return new_board

def check_win(board: np.ndarray, player: int) -> bool:
    # Check horizontal
    for row in range(ROWS):
        for col in range(COLS-3):
            if all(board[row][col+i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(ROWS-3):
        for col in range(COLS):
            if all(board[row+i][col] == player for i in range(4)):
                return True
    
    # Check diagonal (positive slope)
    for row in range(ROWS-3):
        for col in range(COLS-3):
            if all(board[row+i][col+i] == player for i in range(4)):
                return True
    
    # Check diagonal (negative slope)
    for row in range(3, ROWS):
        for col in range(COLS-3):
            if all(board[row-i][col+i] == player for i in range(4)):
                return True
    
    return False

def evaluate_window(window: List[int], player: int) -> int:
    score = 0
    opponent = OPPONENT if player == PLAYER else PLAYER
    
    if window.count(player) == 4:
        score += 100
    elif window.count(player) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(player) == 2 and window.count(EMPTY) == 2:
        score += 2
    
    if window.count(opponent) == 3 and window.count(EMPTY) == 1:
        score -= 4
    
    return score

def evaluate_board(board: np.ndarray, player: int) -> float:
    score = 0
    
    # Check for terminal state
    if check_win(board, PLAYER):
        return 1000000
    if check_win(board, OPPONENT):
        return -1000000
    
    # Add positional weights
    player_positions = np.where(board == PLAYER)
    opponent_positions = np.where(board == OPPONENT)
    
    score += np.sum(POSITION_WEIGHTS[player_positions])
    score -= np.sum(POSITION_WEIGHTS[opponent_positions])
    
    return float(score)

def score_position(board: np.ndarray, player: int) -> int:
    score = 0
    
    # Score center column
    center_array = [board[row][COLS//2] for row in range(ROWS)]
    center_count = center_array.count(player)
    score += center_count * 3
    
    # Score Horizontal
    for row in range(ROWS):
        row_array = [board[row][col] for col in range(COLS)]
        for col in range(COLS-3):
            window = row_array[col:col+4]
            score += evaluate_window(window, player)
    
    # Score Vertical
    for col in range(COLS):
        col_array = [board[row][col] for row in range(ROWS)]
        for row in range(ROWS-3):
            window = col_array[row:row+4]
            score += evaluate_window(window, player)
    
    # Score positive diagonal
    for row in range(ROWS-3):
        for col in range(COLS-3):
            window = [board[row+i][col+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Score negative diagonal
    for row in range(ROWS-3):
        for col in range(COLS-3):
            window = [board[row+3-i][col+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score

def get_next_open_row(board: np.ndarray, col: int) -> int:
    for row in range(ROWS-1, -1, -1):
        if board[row][col] == EMPTY:
            return row
    return -1

def is_terminal_node(board: np.ndarray) -> bool:
    return check_win(board, PLAYER) or check_win(board, OPPONENT) or len(get_valid_moves(board)) == 0

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing_player: bool) -> Tuple[float, int]:
    valid_moves = get_valid_moves(board)
    is_terminal = is_terminal_node(board)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if check_win(board, PLAYER):
                return (100000000000000, None)
            elif check_win(board, OPPONENT):
                return (-100000000000000, None)
            else:
                return (0, None)
        else:
            return (score_position(board, PLAYER), None)
    
    if maximizing_player:
        value = -math.inf
        best_column = valid_moves[0]
        
        for col in valid_moves:
            new_board = make_move(board, col, PLAYER)
            new_score = minimax(new_board, depth-1, alpha, beta, False)[0]
            
            if new_score > value:
                value = new_score
                best_column = col
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        
        return (value, best_column)
    else:
        value = math.inf
        best_column = valid_moves[0]
        
        for col in valid_moves:
            new_board = make_move(board, col, OPPONENT)
            new_score = minimax(new_board, depth-1, alpha, beta, True)[0]
            
            if new_score < value:
                value = new_score
                best_column = col
            
            beta = min(beta, value)
            if alpha >= beta:
                break
        
        return (value, best_column)

def policy(board: List[List[int]]) -> int:
    board_np = np.array(board, dtype=int)
    valid_moves = get_valid_moves(board_np)
    
    if not valid_moves:
        return 0  # fallback
    
    # Quick check for immediate win
    for col in valid_moves:
        test_board = make_move(board_np, col, PLAYER)
        if check_win(test_board, PLAYER):
            return col
    
    # Quick check to block opponent win
    for col in valid_moves:
        test_board = make_move(board_np, col, OPPONENT)
        if check_win(test_board, OPPONENT):
            return col
    
    # Use minimax with alpha-beta pruning
    start_time = time.time()
    depth = 6  # Can adjust based on performance
    
    _, best_col = minimax(board_np, depth, -math.inf, math.inf, True)
    
    # Ensure we have a valid move
    if best_col is None or not is_valid_move(board_np, best_col):
        best_col = valid_moves[0]
    
    return best_col
