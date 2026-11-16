
import random

def has_win(board, player):
    # Check rows
    for i in range(4):
        if all(board[i][j] == player for j in range(4)):
            return True
    # Check columns
    for j in range(4):
        if all(board[i][j] == player for i in range(4)):
            return True
    # Check main diagonal
    if all(board[i][i] == player for i in range(4)):
        return True
    # Check anti-diagonal
    if all(board[i][3 - i] == player for i in range(4)):
        return True
    return False

def policy(board):
    # Create a copy of the board for simulation
    board_copy = [row[:] for row in board]
    # Get available moves
    avail = [(i, j) for i in range(4) for j in range(4) if board[i][j] == 0]
    if not avail:
        return None  # Should not happen, but safety
    
    # Check for a winning move
    for move in avail:
        board_copy[move[0]][move[1]] = 1
        if has_win(board_copy, 1):
            return move
        board_copy[move[0]][move[1]] = 0
    
    # Check for a blocking move
    for move in avail:
        board_copy[move[0]][move[1]] = -1
        if has_win(board_copy, -1):
            return move
        board_copy[move[0]][move[1]] = 0
    
    # Prefer center-like positions
    centers = [m for m in avail if m in [(1, 1), (1, 2), (2, 1), (2, 2)]]
    if centers:
        return random.choice(centers)
    
    # Otherwise, random move
    return random.choice(avail)
