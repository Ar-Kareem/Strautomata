
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    empty_cells = list(zip(*np.where(board == 0)))
    
    # Check for immediate winning move (3 in a row with empty spot)
    for i, j in empty_cells:
        temp_board = board.copy()
        temp_board[i, j] = 1
        if check_win(temp_board, 1):
            return (i, j)
    
    # Check for opponent's immediate threat (3 in a row)
    for i, j in empty_cells:
        temp_board = board.copy()
        temp_board[i, j] = -1
        if check_win(temp_board, -1):
            return (i, j)
    
    # Prioritize center squares
    center_squares = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for i, j in center_squares:
        if board[i, j] == 0:
            return (i, j)
    
    # Then prioritize corners
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corners)  # Randomize corner selection
    for i, j in corners:
        if board[i, j] == 0:
            return (i, j)
    
    # If all else fails, return a random empty cell
    return random.choice(empty_cells)

def check_win(board: np.ndarray, player: int) -> bool:
    # Check rows
    for row in range(4):
        for col in range(2):  # Check all possible 4-in-a-row starting positions
            if all(board[row, col:col+4] == player):
                return True
    
    # Check columns
    for col in range(4):
        for row in range(2):
            if all(board[row:row+4, col] == player):
                return True
    
    # Check diagonals
    for row in range(2):
        for col in range(2):
            if all([board[row+i, col+i] == player for i in range(4)]):
                return True
            if all([board[row+i, 3-col-i] == player for i in range(4)]):
                return True
    
    return False
