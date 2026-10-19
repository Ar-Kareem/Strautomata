
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Check for winning moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:
                    # Try placing our piece here
                    board_np[i, j, k] = 1
                    if check_win(board_np, 1):
                        return (i, j, k)
                    # Reset the board
                    board_np[i, j, k] = 0
    
    # Check for blocking opponent's winning moves
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:
                    # Try placing opponent's piece here
                    board_np[i, j, k] = -1
                    if check_win(board_np, -1):
                        return (i, j, k)
                    # Reset the board
                    board_np[i, j, k] = 0
    
    # If no immediate win/block, try to take center if available
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Otherwise, choose a corner
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    for corner in corners:
        if board_np[corner] == 0:
            return corner
    
    # If no corners available, choose any empty spot
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:
                    return (i, j, k)
    
    # This should never happen in a valid game
    raise Exception("No valid moves available")

def check_win(board: np.ndarray, player: int) -> bool:
    # Check all possible lines in 3D tic-tac-toe
    # There are 49 such lines:
    # 9 rows per layer × 3 layers = 27
    # 9 columns per layer × 3 layers = 27
    # But we need to be more precise...
    
    # Check rows (along x-axis)
    for y in range(3):
        for z in range(3):
            if np.all(board[:, y, z] == player):
                return True
    
    # Check columns (along y-axis)
    for x in range(3):
        for z in range(3):
            if np.all(board[x, :, z] == player):
                return True
    
    # Check pillars (along z-axis)
    for x in range(3):
        for y in range(3):
            if np.all(board[x, y, :] == player):
                return True
    
    # Check diagonals in xy-planes
    for z in range(3):
        if np.all(np.diag(board[:, :, z]) == player):
            return True
        if np.all(np.diag(np.fliplr(board[:, :, z])) == player):
            return True
    
    # Check diagonals in xz-planes
    for y in range(3):
        if np.all(np.diag(board[:, y, :]) == player):
            return True
        if np.all(np.diag(np.fliplr(board[:, y, :])) == player):
            return True
    
    # Check diagonals in yz-planes
    for x in range(3):
        if np.all(np.diag(board[x, :, :]) == player):
            return True
        if np.all(np.diag(np.fliplr(board[x, :, :])) == player):
            return True
    
    # Check 3D space diagonals
    if np.all([board[i, i, i] == player for i in range(3)]):
        return True
    if np.all([board[i, i, 2-i] == player for i in range(3)]):
        return True
    if np.all([board[i, 2-i, i] == player for i in range(3)]):
        return True
    if np.all([board[2-i, i, i] == player for i in range(3)]):
        return True
    
    return False
