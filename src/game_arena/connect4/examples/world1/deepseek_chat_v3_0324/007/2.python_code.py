
import numpy as np

def policy(board: list[list[int]]) -> int:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    rows, cols = 6, 7
    
    def is_winning_move(col, player):
        """Check if placing a disc in the given column would result in a win for the player"""
        # Find the first empty row in the column
        row = np.max(np.where(board_array[:, col] == 0)[0]) if np.any(board_array[:, col] == 0) else -1
        if row == -1:
            return False  # Column is full
        
        # Temporarily place the disc
        board_array[row, col] = player
        
        directions = [
            (0, 1),  # horizontal
            (1, 0),  # vertical
            (1, 1),  # diagonal down-right
            (1, -1)   # diagonal down-left
        ]
        
        for dr, dc in directions:
            count = 1
            # Check in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < rows and 0 <= c < cols and board_array[r, c] == player:
                count += 1
                r += dr
                c += dc
            # Check in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < rows and 0 <= c < cols and board_array[r, c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                # Undo the temporary placement
                board_array[row, col] = 0
                return True
        
        # Undo the temporary placement
        board_array[row, col] = 0
        return False
    
    # 1. Check for immediate win
    for col in range(cols):
        if np.any(board_array[:, col] == 0):  # Column not full
            if is_winning_move(col, 1):
                return col
    
    # 2. Check if opponent can win next move, then block
    for col in range(cols):
        if np.any(board_array[:, col] == 0):  # Column not full
            if is_winning_move(col, -1):
                return col
    
    # 3. Try to create opportunities (3 in a row with open ends)
    for col in [3, 2, 4, 1, 5, 0, 6]:  # Center columns first
        if np.any(board_array[:, col] == 0):  # Column not full
            return col
    
    # Fallback: first available column (shouldn't reach here in normal games)
    for col in range(cols):
        if np.any(board_array[:, col] == 0):
            return col
    
    return 3  # Should never reach here
