
import numpy as np

def is_winning_move(board, row, col, player):
    # Check horizontal, vertical, and diagonal connections
    for direction in [(1, 0), (0, 1), (1, 1), (1, -1)]:
        connect_count = 1
        
        # Check in the positive direction
        for d in range(1, 4):
            r = row + d * direction[0]
            c = col + d * direction[1]
            if 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                connect_count += 1
            else:
                break
        
        # Check in the negative direction
        for d in range(1, 4):
            r = row - d * direction[0]
            c = col - d * direction[1]
            if 0 <= r < 6 and 0 <= c < 7 and board[r][c] == player:
                connect_count += 1
            else:
                break
        
        if connect_count >= 4:
            return True
    
    return False

def get_next_row(board, col):
    for row in range(5, -1, -1):
        if board[row][col] == 0:
            return row
    return -1

def policy(board: list[list[int]]) -> int:
    for col in range(7):
        if board[0][col] == 0:  # If the column is not full
            row = get_next_row(board, col)
            if is_winning_move(board, row, col, 1):
                return col  # I can win
            
            if is_winning_move(board, row, col, -1):
                return col  # Block opponent's winning move
    
    # If no winning move, try to play in the center column if possible
    if board[0][3] == 0:
        return 3  # Play in the center
    
    # Otherwise, choose the first available column
    for col in range(7):
        if board[0][col] == 0:
            return col  # Return first available column

    return -1  # This should never happen since at least one column will be available
