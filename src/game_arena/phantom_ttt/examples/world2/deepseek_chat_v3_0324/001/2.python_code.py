
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Check for immediate winning move
    for i in range(3):
        # Check rows
        if sum(board[i, :] == 1) == 2 and 0 in board[i, :]:
            return (i, np.where(board[i, :] == 0)[0][0])
        # Check columns
        if sum(board[:, i] == 1) == 2 and 0 in board[:, i]:
            return (np.where(board[:, i] == 0)[0][0], i)
    
    # Check diagonals
    diag1 = [board[0,0], board[1,1], board[2,2]]
    if sum(x == 1 for x in diag1) == 2 and 0 in diag1:
        pos = diag1.index(0)
        return (pos, pos)
    diag2 = [board[0,2], board[1,1], board[2,0]]
    if sum(x == 1 for x in diag2) == 2 and 0 in diag2:
        pos = diag2.index(0)
        return (pos, 2 - pos)
    
    # Check if opponent might be about to win (blocking)
    # We assume opponent might have marks where we have 0s
    for i in range(3):
        # Check rows
        row = board[i, :]
        if sum(row == 0) == 1 and sum(row == 1) == 0:
            return (i, np.where(row == 0)[0][0])
        # Check columns
        col = board[:, i]
        if sum(col == 0) == 1 and sum(col == 1) == 0:
            return (np.where(col == 0)[0][0], i)
    
    # Check diagonals for blocking
    diag1 = [board[0,0], board[1,1], board[2,2]]
    if sum(x == 0 for x in diag1) == 1 and sum(x == 1 for x in diag1) == 0:
        pos = diag1.index(0)
        return (pos, pos)
    diag2 = [board[0,2], board[1,1], board[2,0]]
    if sum(x == 0 for x in diag2) == 1 and sum(x == 1 for x in diag2) == 0:
        pos = diag2.index(0)
        return (pos, 2 - pos)
    
    # Priority order: center, corners, edges
    priority_order = [(1,1), (0,0), (0,2), (2,0), (2,2), 
                     (0,1), (1,0), (1,2), (2,1)]
    
    for move in priority_order:
        if board[move] == 0:
            return move
    
    # Fallback - return first available 0 cell (should always exist)
    available = np.argwhere(board == 0)
    return tuple(available[0])
