
def policy(board: list[list[int]]) -> int:
    import numpy as np
    
    # Helper to check if there's a win from a specific position
    def check_win(board, row, col, player):
        # Check all directions (horizontal, vertical, diagonal)
        directions = [
            (0, 1),   # right
            (1, 0),   # down
            (1, 1),   # down-right
            (1, -1)   # down-left
        ]
        
        for dr, dc in directions:
            count = 1  # count the current piece
            # Check in positive direction
            r, c = row + dr, col + dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r += dr
                c += dc
            # Check in negative direction
            r, c = row - dr, col - dc
            while 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                count += 1
                r -= dr
                c -= dc
            if count >= 4:
                return True
        return False
    
    # Helper to find the lowest empty row in a column
    def get_lowest_row(board, col):
        for row in range(5, -1, -1):  # start from bottom
            if board[row][col] == 0:
                return row
        return -1  # column is full
    
    # Try to win immediately 
    for col in range(7):
        row = get_lowest_row(board, col)
        if row != -1:  # column is not full
            # Simulate placing disc
            board[row][col] = 1
            if check_win(board, row, col, 1):
                # Undo the move and return column
                board[row][col] = 0
                return col
            # Undo the move
            board[row][col] = 0
    
    # Block opponent from winning
    for col in range(7):
        row = get_lowest_row(board, col)
        if row != -1:  # column is not full
            # Simulate opponent placing disc
            board[row][col] = -1
            if check_win(board, row, col, -1):
                # Undo the move and block this column
                board[row][col] = 0
                return col
            # Undo the move
            board[row][col] = 0
    
    # Prefer center columns for strategic advantage
    center_cols = [3, 2, 4, 1, 5, 0, 6]
    for col in center_cols:
        if get_lowest_row(board, col) != -1:
            return col
    
    # If we can't find a good move, just pick first available
    for col in range(7):
        if get_lowest_row(board, col) != -1:
            return col
    
    # This should never happen if board is valid
    return 0
