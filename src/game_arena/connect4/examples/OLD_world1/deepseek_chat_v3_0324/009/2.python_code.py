
import numpy as np

def policy(board: list[list[int]]) -> int:
    board_array = np.array(board)
    rows, cols = board_array.shape
    
    # Check for immediate winning move
    for col in range(cols):
        if can_win(board_array, col, 1):
            return col
    
    # Check if opponent can win next move and block
    for col in range(cols):
        if can_win(board_array, col, -1):
            return col
    
    # Try to create a fork (multiple winning opportunities)
    fork_col = find_fork(board_array, 1)
    if fork_col is not None:
        return fork_col
    
    # Try to prevent opponent's fork
    opp_fork_col = find_fork(board_array, -1)
    if opp_fork_col is not None:
        return opp_fork_col
    
    # Prefer center columns for better opportunities
    center_cols = [3, 2, 4, 1, 5, 0, 6]
    for col in center_cols:
        if col < cols and is_valid_move(board_array, col):
            return col
    
    # Fallback: first available column
    for col in range(cols):
        if is_valid_move(board_array, col):
            return col
    
    return 0  # should never reach here if board isn't full

def is_valid_move(board: np.ndarray, col: int) -> bool:
    return board[0, col] == 0

def can_win(board: np.ndarray, col: int, player: int) -> bool:
    if not is_valid_move(board, col):
        return False
    
    # Simulate the move
    temp_board = board.copy()
    row = get_next_empty_row(temp_board, col)
    temp_board[row, col] = player
    
    # Check if this move wins
    return check_win(temp_board, player)

def get_next_empty_row(board: np.ndarray, col: int) -> int:
    for row in range(board.shape[0]-1, -1, -1):
        if board[row, col] == 0:
            return row
    return -1

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

def find_fork(board: np.ndarray, player: int) -> int:
    rows, cols = board.shape
    potential_forks = []
    
    for col in range(cols):
        if not is_valid_move(board, col):
            continue
        
        temp_board = board.copy()
        row = get_next_empty_row(temp_board, col)
        temp_board[row, col] = player
        
        # Count number of winning opportunities created
        win_count = 0
        for c in range(cols):
            if is_valid_move(temp_board, c):
                temp_board2 = temp_board.copy()
                r = get_next_empty_row(temp_board2, c)
                temp_board2[r, c] = player
                if check_win(temp_board2, player):
                    win_count += 1
        
        if win_count >= 2:
            potential_forks.append(col)
    
    if potential_forks:
        return potential_forks[0]
    return None
