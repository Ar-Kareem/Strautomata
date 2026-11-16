
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Check for winning moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_array[i, j, k] == 0:
                    # Try placing our mark here
                    board_array[i, j, k] = 1
                    if check_win(board_array, 1):
                        return (i, j, k)
                    # Reset the board
                    board_array[i, j, k] = 0
    
    # Check for blocking opponent's winning moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_array[i, j, k] == 0:
                    # Try placing opponent's mark here
                    board_array[i, j, k] = -1
                    if check_win(board_array, -1):
                        return (i, j, k)
                    # Reset the board
                    board_array[i, j, k] = 0
    
    # If no immediate win or block, try to take center if available
    if board_array[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Otherwise, pick a corner if available
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board_array[corner] == 0:
            return corner
    
    # If no strategic move, pick the first available spot
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_array[i, j, k] == 0:
                    return (i, j, k)

def check_win(board: np.ndarray, player: int) -> bool:
    # Check all possible lines in 3D tic-tac-toe
    
    # Check rows along x-axis (fixed y, z)
    for y in range(3):
        for z in range(3):
            if np.all(board[:, y, z] == player):
                return True
    
    # Check rows along y-axis (fixed x, z)
    for x in range(3):
        for z in range(3):
            if np.all(board[x, :, z] == player):
                return True
    
    # Check rows along z-axis (fixed x, y)
    for x in range(3):
        for y in range(3):
            if np.all(board[x, y, :] == player):
                return True
    
    # Check diagonals on xy planes (fixed z)
    for z in range(3):
        if np.all(np.diag(board[:, :, z]) == player):
            return True
        if np.all(np.diag(np.fliplr(board[:, :, z])) == player):
            return True
    
    # Check diagonals on xz planes (fixed y)
    for y in range(3):
        diag1 = [board[i, y, i] for i in range(3)]
        diag2 = [board[i, y, 2-i] for i in range(3)]
        if np.all(np.array(diag1) == player):
            return True
        if np.all(np.array(diag2) == player):
            return True
    
    # Check diagonals on yz planes (fixed x)
    for x in range(3):
        diag1 = [board[x, i, i] for i in range(3)]
        diag2 = [board[x, i, 2-i] for i in range(3)]
        if np.all(np.array(diag1) == player):
            return True
        if np.all(np.array(diag2) == player):
            return True
    
    # Check space diagonals
    space_diag1 = [board[i, i, i] for i in range(3)]
    space_diag2 = [board[i, i, 2-i] for i in range(3)]
    space_diag3 = [board[i, 2-i, i] for i in range(3)]
    space_diag4 = [board[2-i, i, i] for i in range(3)]
    
    if np.all(np.array(space_diag1) == player):
        return True
    if np.all(np.array(space_diag2) == player):
        return True
    if np.all(np.array(space_diag3) == player):
        return True
    if np.all(np.array(space_diag4) == player):
        return True
    
    return False
