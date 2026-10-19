
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    n = len(board)
    
    # Check for winning moves (for us)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:  # Empty cell
                    # Temporarily place our mark
                    board[i][j][k] = 1
                    if check_win(board, 1):
                        # Undo the move and return this position
                        board[i][j][k] = 0
                        return (i, j, k)
                    # Undo the move
                    board[i][j][k] = 0
    
    # Check for blocking moves (opponent winning)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:  # Empty cell
                    # Temporarily place opponent's mark
                    board[i][j][k] = -1
                    if check_win(board, -1):
                        # Undo the move and return this position to block
                        board[i][j][k] = 0
                        return (i, j, k)
                    # Undo the move
                    board[i][j][k] = 0
    
    # Try to take the center if it's empty
    center = n // 2
    if n % 2 == 1:  # Odd dimensions
        if board[center][center][center] == 0:
            return (center, center, center)
    
    # Try corners
    corners = []
    for i in [0, n-1]:
        for j in [0, n-1]:
            for k in [0, n-1]:
                if board[i][j][k] == 0:
                    corners.append((i, j, k))
    
    if corners:
        # Prioritize corners that are not on the same face
        # But for simplicity, pick one at random among available corners
        return corners[0]
    
    # If no special moves, find any empty cell
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    return (i, j, k)
    
    # This should not happen in a valid game state
    raise Exception("No valid move found")

def check_win(board, player):
    """Check if the specified player has won"""
    n = len(board)
    
    # Check rows, columns, and layers for each face
    for i in range(n):
        for j in range(n):
            # Check horizontal lines in each layer
            if all(board[i][j][k] == player for k in range(n)):
                return True
            # Check vertical lines in each layer
            if all(board[i][k][j] == player for k in range(n)):
                return True
            # Check depth lines in each layer
            if all(board[k][j][i] == player for k in range(n)):
                return True
    
    # Check all the main diagonals across all layers
    # Check main diagonal planes
    for i in range(n):
        # Diagonals in the same layer (top face for example)
        if all(board[i][j][j] == player for j in range(n)):
            return True
        # Diagonals in the same layer (bottom face for example)
        if all(board[i][j][n-1-j] == player for j in range(n)):
            return True
        
        # Diagonals from first to last layer
        if all(board[j][j][i] == player for j in range(n)):
            return True
        # Diagonals from first to last layer (reverse)
        if all(board[j][n-1-j][i] == player for j in range(n)):
            return True
    
    # Check the main space diagonals
    # Forward diagonal from top-left-front to bottom-right-back
    if all(board[i][i][i] == player for i in range(n)):
        return True
    # Backward diagonal from top-right-front to bottom-left-back
    if all(board[i][i][n-1-i] == player for i in range(n)):
        return True
    # Forward diagonal from top-left-back to bottom-right-front
    if all(board[i][n-1-i][i] == player for i in range(n)):
        return True
    # Backward diagonal from top-right-back to bottom-left-front
    if all(board[i][n-1-i][n-1-i] == player for i in range(n)):
        return True
        
    return False
