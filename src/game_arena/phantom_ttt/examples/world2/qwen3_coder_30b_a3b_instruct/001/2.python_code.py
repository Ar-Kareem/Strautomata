
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy for easier manipulation
    board = np.array(board)
    
    # Get all unconfirmed cells (0) that are not already mine (1)
    unconfirmed = []
    for i in range(3):
        for j in range(3):
            if board[i][j] == 0:
                unconfirmed.append((i, j))
    
    if not unconfirmed:
        # If no unconfirmed cells, return any empty cell
        for i in range(3):
            for j in range(3):
                if board[i][j] != 1:
                    return (i, j)
    
    # First priority: Find a move that wins for us
    for i in range(3):
        # Check rows
        if board[i][0] == 1 and board[i][1] == 1 and board[i][2] == 0:
            return (i, 2)
        if board[i][0] == 1 and board[i][2] == 1 and board[i][1] == 0:
            return (i, 1)
        if board[i][1] == 1 and board[i][2] == 1 and board[i][0] == 0:
            return (i, 0)
        
        # Check columns
        if board[0][i] == 1 and board[1][i] == 1 and board[2][i] == 0:
            return (2, i)
        if board[0][i] == 1 and board[2][i] == 1 and board[1][i] == 0:
            return (1, i)
        if board[1][i] == 1 and board[2][i] == 1 and board[0][i] == 0:
            return (0, i)
    
    # Check diagonals
    if board[0][0] == 1 and board[1][1] == 1 and board[2][2] == 0:
        return (2, 2)
    if board[0][0] == 1 and board[2][2] == 1 and board[1][1] == 0:
        return (1, 1)
    if board[1][1] == 1 and board[2][2] == 1 and board[0][0] == 0:
        return (0, 0)
    if board[0][2] == 1 and board[1][1] == 1 and board[2][0] == 0:
        return (2, 0)
    if board[0][2] == 1 and board[2][0] == 1 and board[1][1] == 0:
        return (1, 1)
    if board[1][1] == 1 and board[2][0] == 1 and board[0][2] == 0:
        return (0, 2)
    
    # Second priority: Block opponent from winning
    for i in range(3):
        # Check rows
        if board[i][0] == 0 and board[i][1] == 0 and board[i][2] == 1:
            return (i, 2)  # We'd block a win, return the unconfirmed square
        if board[i][0] == 0 and board[i][2] == 0 and board[i][1] == 1:
            return (i, 1)
        if board[i][1] == 0 and board[i][2] == 0 and board[i][0] == 1:
            return (i, 0)
        
        # Check columns
        if board[0][i] == 0 and board[1][i] == 0 and board[2][i] == 1:
            return (2, i)
        if board[0][i] == 0 and board[2][i] == 0 and board[1][i] == 1:
            return (1, i)
        if board[1][i] == 0 and board[2][i] == 0 and board[0][i] == 1:
            return (0, i)
    
    # Check diagonals
    if board[0][0] == 0 and board[1][1] == 0 and board[2][2] == 1:
        return (2, 2)
    if board[0][0] == 0 and board[2][2] == 0 and board[1][1] == 1:
        return (1, 1)
    if board[1][1] == 0 and board[2][2] == 0 and board[0][0] == 1:
        return (0, 0)
    if board[0][2] == 0 and board[1][1] == 0 and board[2][0] == 1:
        return (2, 0)
    if board[0][2] == 0 and board[2][0] == 0 and board[1][1] == 1:
        return (1, 1)
    if board[1][1] == 0 and board[2][0] == 0 and board[0][2] == 1:
        return (0, 2)
    
    # Third priority: Prefer center, then corners, then edges
    preferred_moves = [(1, 1), (0, 0), (0, 2), (2, 0), (2, 2)]
    for move in preferred_moves:
        if move in unconfirmed:
            return move
    
    # If no preferred moves available, return any unconfirmed cell
    return unconfirmed[0]
