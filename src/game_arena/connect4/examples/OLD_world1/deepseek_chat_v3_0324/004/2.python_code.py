
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    rows, cols = board_array.shape
    
    # Check for immediate winning move
    for col in range(cols):
        if can_win(board_array, col, 1):
            return col
    
    # Check if opponent can win next move and block them
    for col in range(cols):
        if can_win(board_array, col, -1):
            return col
    
    # Try to create a potential winning opportunity (two in a row with space)
    for col in range(cols):
        if is_potential_win(board_array, col, 1):
            return col
    
    # Try to prevent opponent from creating potential winning opportunities
    for col in range(cols):
        if is_potential_win(board_array, col, -1):
            return col
    
    # Prefer center columns for better strategic position
    center_cols = [3, 2, 4, 1, 5, 0, 6]
    for col in center_cols:
        if col < cols and is_valid_move(board_array, col):
            return col
    
    # Fallback: first available column (shouldn't reach here if board isn't full)
    for col in range(cols):
        if is_valid_move(board_array, col):
            return col
    
    return 0  # default (shouldn't reach here if board isn't full)

def is_valid_move(board: np.ndarray, col: int) -> bool:
    """Check if a column is valid for a move (has empty space)."""
    return 0 in board[:, col]

def can_win(board: np.ndarray, col: int, player: int) -> bool:
    """Check if dropping a disc in this column would result in a win."""
    if not is_valid_move(board, col):
        return False
    
    # Make a copy of the board to simulate the move
    temp_board = board.copy()
    row = get_next_open_row(temp_board, col)
    temp_board[row, col] = player
    
    # Check if this move wins
    return check_winner(temp_board, player)

def get_next_open_row(board: np.ndarray, col: int) -> int:
    """Get the next open row in a column."""
    column = board[:, col]
    for row in range(len(column)-1, -1, -1):
        if column[row] == 0:
            return row
    return -1

def check_winner(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has won."""
    rows, cols = board.shape
    
    # Check horizontal
    for r in range(rows):
        for c in range(cols - 3):
            if all(board[r, c+i] == player for i in range(4)):
                return True
    
    # Check vertical
    for r in range(rows - 3):
        for c in range(cols):
            if all(board[r+i, c] == player for i in range(4)):
                return True
    
    # Check diagonal (positive slope)
    for r in range(rows - 3):
        for c in range(cols - 3):
            if all(board[r+i, c+i] == player for i in range(4)):
                return True
    
    # Check diagonal (negative slope)
    for r in range(3, rows):
        for c in range(cols - 3):
            if all(board[r-i, c+i] == player for i in range(4)):
                return True
    
    return False

def is_potential_win(board: np.ndarray, col: int, player: int) -> bool:
    """Check if this move creates a potential winning opportunity (three in a row with space)."""
    if not is_valid_move(board, col):
        return False
    
    temp_board = board.copy()
    row = get_next_open_row(temp_board, col)
    temp_board[row, col] = player
    
    # Count the number of potential winning lines this move creates
    potential_lines = 0
    
    # Check horizontal
    for c in range(max(0, col-3), min(cols-3, col+1)):
        window = temp_board[row, c:c+4]
        if sum(window == player) >= 3 and 0 in window:
            potential_lines += 1
    
    # Check vertical
    if row <= rows - 4:
        window = temp_board[row:row+4, col]
        if sum(window == player) >= 3 and 0 in window:
            potential_lines += 1
    
    # Check diagonal (positive slope)
    for offset in range(-3, 1):
        r, c = row - offset, col - offset
        if 0 <= r <= rows-4 and 0 <= c <= cols-4:
            window = [temp_board[r+i, c+i] for i in range(4)]
            if sum(w == player for w in window) >= 3 and 0 in window:
                potential_lines += 1
    
    # Check diagonal (negative slope)
    for offset in range(-3, 1):
        r, c = row + offset, col - offset
        if 3 <= r < rows and 0 <= c <= cols-4:
            window = [temp_board[r-i, c+i] for i in range(4)]
            if sum(w == player for w in window) >= 3 and 0 in window:
                potential_lines += 1
    
    return potential_lines > 0
