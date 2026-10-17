
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # First check if we can win in the next move
    for col in range(7):
        if is_valid_col(board, col):
            temp_board = simulate_move(board, col, 1)
            if check_win(temp_board, 1):
                return col
    
    # Then check if opponent can win next move and block them
    for col in range(7):
        if is_valid_col(board, col):
            temp_board = simulate_move(board, col, -1)
            if check_win(temp_board, -1):
                return col
    
    # Preference for center columns as they offer more winning opportunities
    preferred_cols = [3, 2, 4, 1, 5, 0, 6]
    
    # Try to create multiple opportunities to win or prevent opponent
    for col in preferred_cols:
        if is_valid_col(board, col):
            # If this move creates a potential line of three
            temp_board = simulate_move(board, col, 1)
            if count_potential_wins(temp_board, 1) >= 2:
                return col
    
    # Just pick the first valid preferred column
    for col in preferred_cols:
        if is_valid_col(board, col):
            return col
    
    # Fallback - should never reach here if board isn't full
    return np.random.choice(np.where(board[0] == 0)[0])

def is_valid_col(board, col):
    """Check if column has empty space"""
    return board[5][col] == 0

def simulate_move(board, col, player):
    """Simulate a move and return new board state"""
    temp_board = np.copy(board)
    for row in range(6):
        if temp_board[row][col] == 0:
            temp_board[row][col] = player
            break
    return temp_board

def check_win(board, player):
    """Check if the specified player has won"""
    # Check horizontal locations
    for r in range(6):
        for c in range(4):
            if all(board[r][c+i] == player for i in range(4)):
                return True
    
    # Check vertical locations
    for c in range(7):
        for r in range(3):
            if all(board[r+i][c] == player for i in range(4)):
                return True
    
    # Check diagonals
    for r in range(3):
        for c in range(4):
            if all(board[r+i][c+i] == player for i in range(4)):
                return True
            if all(board[r+i][c+3-i] == player for i in range(4)):
                return True
    return False

def count_potential_wins(board, player, length=3):
    """Count how many potential winning lines of specified length exist"""
    count = 0
    
    # Check horizontal
    for r in range(6):
        for c in range(8 - length):
            line = board[r][c:c+length]
            if sum(line == player) == length and sum(line == 0) == (4 - length):
                count += 1
    
    # Check vertical
    for c in range(7):
        for r in range(7 - length):
            line = board[r:r+length, c]
            if sum(line == player) == length and sum(line == 0) == (4 - length):
                count += 1
    
    # Check diagonals
    for r in range(7 - length):
        for c in range(8 - length):
            line1 = [board[r+i][c+i] for i in range(length)]
            line2 = [board[r+i][c+length-1-i] for i in range(length)]
            if sum(np.array(line1) == player) == length and sum(np.array(line1) == 0) == (4 - length):
                count += 1
            if sum(np.array(line2) == player) == length and sum(np.array(line2) == 0) == (4 - length):
                count += 1
    return count
