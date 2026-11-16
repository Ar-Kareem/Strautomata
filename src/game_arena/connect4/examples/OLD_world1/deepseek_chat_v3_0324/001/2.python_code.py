
import numpy as np
import random

def policy(board: list[list[int]]) -> int:
    board_array = np.array(board)
    rows, cols = board_array.shape
    
    # Check for immediate winning move
    for col in range(cols):
        if is_valid_move(board_array, col):
            temp_board = simulate_move(board_array, col, 1)
            if check_win(temp_board, 1):
                return col
    
    # Check for opponent's immediate winning move and block
    for col in range(cols):
        if is_valid_move(board_array, col):
            temp_board = simulate_move(board_array, col, -1)
            if check_win(temp_board, -1):
                return col
    
    # Prioritize center column (better strategic position)
    center_col = cols // 2
    if is_valid_move(board_array, center_col):
        return center_col
    
    # Try to create potential winning opportunities (two in a row with space)
    for col in range(cols):
        if is_valid_move(board_array, col):
            temp_board = simulate_move(board_array, col, 1)
            if count_potential_wins(temp_board, 1) > 0:
                return col
    
    # Fallback: choose random valid move
    valid_columns = [col for col in range(cols) if is_valid_move(board_array, col)]
    return random.choice(valid_columns)

def is_valid_move(board: np.ndarray, col: int) -> bool:
    return 0 in board[:, col]

def simulate_move(board: np.ndarray, col: int, player: int) -> np.ndarray:
    temp_board = board.copy()
    for row in range(board.shape[0]-1, -1, -1):
        if temp_board[row, col] == 0:
            temp_board[row, col] = player
            break
    return temp_board

def check_win(board: np.ndarray, player: int) -> bool:
    rows, cols = board.shape
    
    # Check horizontal
    for row in range(rows):
        for col in range(cols - 3):
            if all(board[row, col+i] == player for i in range(4)):
                return True
    
    # Check vertical
    for row in range(rows - 3):
        for col in range(cols):
            if all(board[row+i, col] == player for i in range(4)):
                return True
    
    # Check diagonal (top-left to bottom-right)
    for row in range(rows - 3):
        for col in range(cols - 3):
            if all(board[row+i, col+i] == player for i in range(4)):
                return True
    
    # Check diagonal (bottom-left to top-right)
    for row in range(3, rows):
        for col in range(cols - 3):
            if all(board[row-i, col+i] == player for i in range(4)):
                return True
    
    return False

def count_potential_wins(board: np.ndarray, player: int) -> int:
    count = 0
    rows, cols = board.shape
    
    # Check for open threes that can become fours
    for row in range(rows):
        for col in range(cols):
            if board[row, col] == 0:
                temp_board = board.copy()
                temp_board[row, col] = player
                if check_win(temp_board, player):
                    count += 1
    return count
