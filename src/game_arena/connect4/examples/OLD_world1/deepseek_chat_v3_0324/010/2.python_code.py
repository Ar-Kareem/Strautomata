
import numpy as np

def policy(board: list[list[int]]) -> int:
    board_array = np.array(board)
    rows, cols = board_array.shape
    
    # Check for immediate win
    for col in range(cols):
        if board_array[0, col] != 0:  # Column is full
            continue
        # Find the first empty row in the column
        row = np.max(np.where(board_array[:, col] == 0))
        # Simulate placing the disc
        board_array[row, col] = 1
        if check_win(board_array, row, col):
            return col
        # Revert the move
        board_array[row, col] = 0
    
    # Check for opponent's immediate win and block
    for col in range(cols):
        if board_array[0, col] != 0:  # Column is full
            continue
        # Find the first empty row in the column
        row = np.max(np.where(board_array[:, col] == 0))
        # Simulate opponent's move
        board_array[row, col] = -1
        if check_win(board_array, row, col):
            # Revert the move and block
            board_array[row, col] = 0
            return col
        # Revert the move
        board_array[row, col] = 0
    
    # Try to create a fork (two potential winning moves)
    for col in range(cols):
        if board_array[0, col] != 0:
            continue
        row = np.max(np.where(board_array[:, col] == 0))
        board_array[row, col] = 1
        winning_moves = 0
        for c in range(cols):
            if board_array[0, c] != 0:
                continue
            r = np.max(np.where(board_array[:, c] == 0))
            board_array[r, c] = 1
            if check_win(board_array, r, c):
                winning_moves += 1
            board_array[r, c] = 0
        board_array[row, col] = 0
        if winning_moves >= 2:
            return col
    
    # Try to prevent opponent's fork
    opponent_forks = []
    for col in range(cols):
        if board_array[0, col] != 0:
            continue
        row = np.max(np.where(board_array[:, col] == 0))
        board_array[row, col] = -1
        opponent_winning_moves = 0
        for c in range(cols):
            if board_array[0, c] != 0:
                continue
            r = np.max(np.where(board_array[:, c] == 0))
            board_array[r, c] = -1
            if check_win(board_array, r, c):
                opponent_winning_moves += 1
            board_array[r, c] = 0
        board_array[row, col] = 0
        if opponent_winning_moves >= 2:
            opponent_forks.append(col)
    
    if opponent_forks:
        # Choose the column that allows the opponent the fewest forks
        best_col = opponent_forks[0]
        min_forks = float('inf')
        for col in opponent_forks:
            forks = 0
            row = np.max(np.where(board_array[:, col] == 0))
            board_array[row, col] = 1
            for c in range(cols):
                if board_array[0, c] != 0:
                    continue
                r = np.max(np.where(board_array[:, c] == 0))
                board_array[r, c] = -1
                if check_win(board_array, r, c):
                    forks += 1
                board_array[r, c] = 0
            board_array[row, col] = 0
            if forks < min_forks:
                min_forks = forks
                best_col = col
        return best_col
    
    # Choose the center column if available
    center_col = cols // 2
    if board_array[0, center_col] == 0:
        return center_col
    
    # Choose a random available column
    available_cols = [col for col in range(cols) if board_array[0, col] == 0]
    return np.random.choice(available_cols)

def check_win(board: np.ndarray, row: int, col: int) -> bool:
    player = board[row, col]
    directions = [
        [(0, 1), (0, -1)],  # Horizontal
        [(1, 0), (-1, 0)],   # Vertical
        [(1, 1), (-1, -1)],  # Diagonal /
        [(1, -1), (-1, 1)]   # Diagonal \
    ]
    
    for dir_pair in directions:
        count = 1
        for dr, dc in dir_pair:
            r, c = row + dr, col + dc
            while 0 <= r < board.shape[0] and 0 <= c < board.shape[1] and board[r, c] == player:
                count += 1
                r += dr
                c += dc
        if count >= 4:
            return True
    return False
