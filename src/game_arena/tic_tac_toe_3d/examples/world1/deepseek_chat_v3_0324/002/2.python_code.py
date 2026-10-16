
import numpy as np
import random

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Check all possible lines for a winning move
    def check_lines(value):
        # Check rows in each layer
        for z in range(3):
            for y in range(3):
                line = board[z, y, :]
                if sum(line == value) == 2 and sum(line == 0) == 1:
                    return (z, y, np.where(line == 0)[0][0])
        
        # Check columns in each layer
        for z in range(3):
            for x in range(3):
                line = board[z, :, x]
                if sum(line == value) == 2 and sum(line == 0) == 1:
                    return (z, np.where(line == 0)[0][0], x)
        
        # Check depth lines (vertical)
        for y in range(3):
            for x in range(3):
                line = board[:, y, x]
                if sum(line == value) == 2 and sum(line == 0) == 1:
                    return (np.where(line == 0)[0][0], y, x)
        
        # Check 2D diagonals in each layer
        for z in range(3):
            diag1 = [board[z, i, i] for i in range(3)]
            if sum(diag1 == value) == 2 and sum(diag1 == 0) == 1:
                pos = np.where(diag1 == 0)[0][0]
                return (z, pos, pos)
            diag2 = [board[z, i, 2-i] for i in range(3)]
            if sum(diag2 == value) == 2 and sum(diag2 == 0) == 1:
                pos = np.where(diag2 == 0)[0][0]
                return (z, pos, 2-pos)
        
        # Check space diagonals
        space_diag1 = [board[i, i, i] for i in range(3)]
        if sum(space_diag1 == value) == 2 and sum(space_diag1 == 0) == 1:
            pos = np.where(space_diag1 == 0)[0][0]
            return (pos, pos, pos)
        space_diag2 = [board[i, i, 2-i] for i in range(3)]
        if sum(space_diag2 == value) == 2 and sum(space_diag2 == 0) == 1:
            pos = np.where(space_diag2 == 0)[0][0]
            return (pos, pos, 2-pos)
        space_diag3 = [board[i, 2-i, i] for i in range(3)]
        if sum(space_diag3 == value) == 2 and sum(space_diag3 == 0) == 1:
            pos = np.where(space_diag3 == 0)[0][0]
            return (pos, 2-pos, pos)
        space_diag4 = [board[i, 2-i, 2-i] for i in range(3)]
        if sum(space_diag4 == value) == 2 and sum(space_diag4 == 0) == 1:
            pos = np.where(space_diag4 == 0)[0][0]
            return (pos, 2-pos, 2-pos)
        
        return None
    
    # Check for winning move (value = 1)
    win_move = check_lines(1)
    if win_move is not None:
        return win_move
    
    # Check for blocking move (value = -1)
    block_move = check_lines(-1)
    if block_move is not None:
        return block_move
    
    # Take center if available
    if board[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # If no strategic moves, choose random empty cell
    empty_cells = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z, y, x] == 0:
                    empty_cells.append((z, y, x))
    return random.choice(empty_cells)
