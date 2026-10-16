
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Helper function to check if a move would win
    def is_winning_move(col, player):
        # Find first empty row in the column
        if np.all(board[:, col] != 0):
            return False  # Column is full

        # Simulate the move
        row = np.where(board[:, col] == 0)[0][-1]  # Lowest empty row
        temp_board = board.copy()
        temp_board[row, col] = player
        
        # Check all four directions for a line of 4
        def check_line(r, c, dr, dc):
            count = 0
            for i in range(4):
                if (0 <= r + i*dr < 6 and 0 <= c + i*dc < 7 and 
                    temp_board[r + i*dr, c + i*dc] == player):
                    count += 1
                else:
                    break
            for i in range(1, 4):
                if (0 <= r - i*dr < 6 and 0 <= c - i*dc < 7 and 
                    temp_board[r - i*dr, c - i*dc] == player):
                    count += 1
                else:
                    break
            return count >= 4
        
        # Check horizontal
        if (c := col - 3) < 0: c = 0
        for c in range(max(0, col - 3), min(4, col + 1)):
            if all(temp_board[row, c + i] == player for i in range(4)):
                return True
        
        # Check vertical (only need to check downward)
        if row <= 2:
            if all(temp_board[row + i, col] == player for i in range(4)):
                return True
        
        # Check diagonals
        for dr, dc in [(1, 1), (1, -1)]:
            if check_line(row, col, dr, dc):
                return True
        return False
    
    # 1. Check for immediate winning moves
    for col in range(7):
        if np.any(board[:, col] == 0):  # Column not full
            if is_winning_move(col, 1):
                return col
    
    # 2. Block opponent's winning moves
    for col in range(7):
        if np.any(board[:, col] == 0):  # Column not full
            if is_winning_move(col, -1):
                return col
    
    # 3. Prefer center columns for better strategic position
    center_order = [3, 2, 4, 1, 5, 0, 6]
    for col in center_order:
        if np.any(board[:, col] == 0):
            return col
    
    # Fallback (shouldn't reach here if board isn't full)
    return 0
