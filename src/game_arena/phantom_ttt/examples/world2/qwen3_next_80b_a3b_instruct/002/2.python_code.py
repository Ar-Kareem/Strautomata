
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # We can only place on 0s (unknown), not on 1s (already ours)
    possible_moves = [(i, j) for i in range(3) for j in range(3) if board[i][j] == 0]
    
    # If no possible moves (shouldn't happen in a valid game), return any legal move — but per spec, we must return legal, so fallback
    if not possible_moves:
        # This should never occur, but safety fallback
        return (0, 0)
    
    # Check for immediate wins: two 1s and one 0 in a line → play the 0
    for i in range(3):
        # Check rows
        if np.sum(board[i, :] == 1) == 2 and np.sum(board[i, :] == 0) == 1:
            j = np.where(board[i, :] == 0)[0][0]
            return (i, j)
        # Check columns
        if np.sum(board[:, i] == 1) == 2 and np.sum(board[:, i] == 0) == 1:
            j = np.where(board[:, i] == 0)[0][0]
            return (j, i)
    
    # Check diagonals
    diag1 = [board[0,0], board[1,1], board[2,2]]
    diag2 = [board[0,2], board[1,1], board[2,0]]
    if np.sum(diag1) == 2 and diag1.count(0) == 1:
        idx = diag1.index(0)
        return (idx, idx)
    if np.sum(diag2) == 2 and diag2.count(0) == 1:
        idx = diag2.index(0)
        if idx == 0:
            return (0, 2)
        elif idx == 1:
            return (1, 1)
        else:
            return (2, 0)
    
    # Check for blocking: opponent might have two in a row (two 0s) and we have one → block
    # We assume that if a line has two 0s and one 1, then the opponent is likely to win, so we block one of the 0s
    for i in range(3):
        if np.sum(board[i, :] == 0) == 2 and np.sum(board[i, :] == 1) == 1:
            j = np.where(board[i, :] == 0)[0][0]
            return (i, j)
        if np.sum(board[:, i] == 0) == 2 and np.sum(board[:, i] == 1) == 1:
            j = np.where(board[:, i] == 0)[0][0]
            return (j, i)
    
    if np.sum(diag1) == 1 and diag1.count(0) == 2:
        # Block diagonal 1
        idx = diag1.index(0)
        return (idx, idx)
    if np.sum(diag2) == 1 and diag2.count(0) == 2:
        # Block diagonal 2
        idx = diag2.index(0)
        if idx == 0:
            return (0, 2)
        elif idx == 1:
            return (1, 1)
        else:
            return (2, 0)
    
    # If no immediate win or block, use optimal opening strategy
    # Prioritize center, then corners, then edges
    optimal_order = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2), (0, 1), (1, 0), (1, 2), (2, 1)]
    
    for move in optimal_order:
        if move in possible_moves:
            return move
    
    # Fallback: return any possible move (should not reach here due to optimal_order covering all)
    return possible_moves[0]
