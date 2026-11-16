
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> int:
    # Convert to numpy array for easier manipulation
    np_board = np.array(board)
    
    # Check for immediate winning move
    for col in range(7):
        if is_valid_move(np_board, col):
            row = get_next_row(np_board, col)
            np_board[row][col] = 1
            if check_win(np_board, 1):
                return col
            np_board[row][col] = 0  # Undo move
    
    # Check for opponent winning move to block
    for col in range(7):
        if is_valid_move(np_board, col):
            row = get_next_row(np_board, col)
            np_board[row][col] = -1
            if check_win(np_board, -1):
                return col
            np_board[row][col] = 0  # Undo move
    
    # Use minimax for best move with depth 4 (adjustable based on performance)
    best_move = minimax(np_board, 4, -np.inf, np.inf, True)[1]
    return best_move if best_move is not None else get_first_valid_column(np_board)

def is_valid_move(board: np.ndarray, col: int) -> bool:
    return board[0][col] == 0

def get_first_valid_column(board: np.ndarray) -> int:
    for col in range(7):
        if is_valid_move(board, col):
            return col
    return 0  # Fallback

def get_next_row(board: np.ndarray, col: int) -> int:
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1

def check_win(board: np.ndarray, player: int) -> bool:
    # Check horizontal
    for row in range(6):
        for col in range(4):
            if all(board[row][col+i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(3):
        for col in range(7):
            if all(board[row+i][col] == player for i in range(4)):
                return True
    
    # Check diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            if all(board[row+i][col+i] == player for i in range(4)):
                return True
    
    # Check diagonal (negative slope)
    for row in range(3, 6):
        for col in range(4):
            if all(board[row-i][col+i] == player for i in range(4)):
                return True
    
    return False

def evaluate_window(window: List[int]) -> int:
    score = 0
    player_count = window.count(1)
    opponent_count = window.count(-1)
    empty_count = window.count(0)
    
    if player_count == 4:
        score += 1000
    elif player_count == 3 and empty_count == 1:
        score += 100
    elif player_count == 2 and empty_count == 2:
        score += 10
    elif player_count == 1 and empty_count == 3:
        score += 1
        
    if opponent_count == 4:
        score -= 1000
    elif opponent_count == 3 and empty_count == 1:
        score -= 100
    elif opponent_count == 2 and empty_count == 2:
        score -= 10
    elif opponent_count == 1 and empty_count == 3:
        score -= 1
        
    return score

def evaluate_board(board: np.ndarray) -> int:
    score = 0
    
    # Score center column preference
    center_array = [int(i) for i in list(board[:, 3])]
    center_count = center_array.count(1)
    score += center_count * 3
    
    # Score horizontal
    for row in range(6):
        for col in range(4):
            window = [board[row][col+i] for i in range(4)]
            score += evaluate_window(window)
    
    # Score vertical
    for row in range(3):
        for col in range(7):
            window = [board[row+i][col] for i in range(4)]
            score += evaluate_window(window)
    
    # Score diagonal (positive slope)
    for row in range(3):
        for col in range(4):
            window = [board[row+i][col+i] for i in range(4)]
            score += evaluate_window(window)
    
    # Score diagonal (negative slope)
    for row in range(3, 6):
        for col in range(4):
            window = [board[row-i][col+i] for i in range(4)]
            score += evaluate_window(window)
    
    return score

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[int, int]:
    valid_locations = [col for col in range(7) if is_valid_move(board, col)]
    is_terminal = len(valid_locations) == 0 or check_win(board, 1) or check_win(board, -1) or depth == 0
    
    if is_terminal:
        if check_win(board, 1):
            return (10000000000000, None)
        elif check_win(board, -1):
            return (-10000000000000, None)
        elif len(valid_locations) == 0:  # Game tie
            return (0, None)
        else:  # Depth is zero
            return (evaluate_board(board), None)
    else:
        if maximizing:
            value = -np.inf
            column = valid_locations[0]
            for col in valid_locations:
                row = get_next_row(board, col)
                board_copy = board.copy()
                board_copy[row][col] = 1
                new_score = minimax(board_copy, depth-1, alpha, beta, False)[0]
                if new_score > value:
                    value = new_score
                    column = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return (value, column)
        else:  # Minimizing player
            value = np.inf
            column = valid_locations[0]
            for col in valid_locations:
                row = get_next_row(board, col)
                board_copy = board.copy()
                board_copy[row][col] = -1
                new_score = minimax(board_copy, depth-1, alpha, beta, True)[0]
                if new_score < value:
                    value = new_score
                    column = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return (value, column)
