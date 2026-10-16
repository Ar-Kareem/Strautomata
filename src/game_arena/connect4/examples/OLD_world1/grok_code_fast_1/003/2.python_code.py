
import random

def drop_disc(board, col, player):
    # Create a deep copy of the board
    new_board = [row[:] for row in board]
    # Find the lowest empty row in the column
    for r in range(5, -1, -1):
        if new_board[r][col] == 0:
            new_board[r][col] = player
            return new_board
    return None  # Column is full, though we ensure it's not in valid moves

def check_win(board, player):
    # Check horizontal wins
    for r in range(6):
        for c in range(4):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # Check vertical wins
    for c in range(7):
        for r in range(3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # Check diagonal wins (/)
    for r in range(3):
        for c in range(4):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # Check diagonal wins (\)
    for r in range(3):
        for c in range(3, 7):
            if all(board[r + i][c - i] == player for i in range(4)):
                return True
    return False

def policy(board):
    # Find valid moves: columns with at least one empty cell (top row empty)
    valid = [i for i in range(7) if board[0][i] == 0]
    
    # Check if we can win immediately
    for c in valid:
        nb = drop_disc(board, c, 1)
        if check_win(nb, 1):
            return c
    
    # Check if we need to block opponent's winning move
    for c in valid:
        nb = drop_disc(board, c, -1)
        if check_win(nb, -1):
            return c
    
    # Otherwise, prefer the center column (3), or if not available, choose randomly
    if 3 in valid:
        return 3
    else:
        return random.choice(valid)
