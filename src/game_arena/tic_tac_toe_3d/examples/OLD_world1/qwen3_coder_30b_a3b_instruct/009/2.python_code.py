
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determine the next move for 3D Tic Tac Toe using a simple heuristic.
    The algorithm prioritizes:
    1. Winning moves
    2. Blocking opponent wins
    3. Taking the center if available
    4. Taking a corner
    5. Taking any available move
    """
    n = 3
    # Flatten the board for easier processing
    flat_board = np.array(board)
    
    # Check for winning moves or blocking moves
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:  # Empty cell
                    # Temporarily place our mark
                    board[i][j][k] = 1
                    if check_win(board, 1):
                        board[i][j][k] = 0  # Restore
                        return (i, j, k)
                    board[i][j][k] = 0  # Restore
    
    # Check for blocking opponent wins
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:  # Empty cell
                    # Temporarily place opponent's mark
                    board[i][j][k] = -1
                    if check_win(board, -1):
                        board[i][j][k] = 0  # Restore
                        return (i, j, k)
                    board[i][j][k] = 0  # Restore
    
    # Try to take the center
    center = n // 2
    if n % 2 == 1 and board[center][center][center] == 0:
        return (center, center, center)
    
    # Take a corner
    corners = [
        (0, 0, 0), (0, 0, n-1), (0, n-1, 0), (0, n-1, n-1),
        (n-1, 0, 0), (n-1, 0, n-1), (n-1, n-1, 0), (n-1, n-1, n-1)
    ]
    for i, j, k in corners:
        if board[i][j][k] == 0:
            return (i, j, k)
    
    # Take any available move
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i][j][k] == 0:
                    return (i, j, k)

def check_win(board: List[List[List[int]]], player: int) -> bool:
    """
    Check if the specified player has won on the board.
    """
    n = 3
    
    # Check rows, columns, and layers for all 3 dimensions
    # Horizontal lines
    for i in range(n):
        for j in range(n):
            if all(board[i][j][k] == player for k in range(n)):
                return True
    
    # Vertical lines
    for i in range(n):
        for k in range(n):
            if all(board[i][j][k] == player for j in range(n)):
                return True
    
    # Depth lines
    for j in range(n):
        for k in range(n):
            if all(board[i][j][k] == player for i in range(n)):
                return True
    
    # Diagonal lines within each 2D slice (for each layer)
    for i in range(n):
        if all(board[i][j][j] == player for j in range(n)) or \
           all(board[i][j][n-1-j] == player for j in range(n)):
            return True
    
    # Diagonal lines across the board
    # Main diagonals
    if all(board[i][i][i] == player for i in range(n)) or \
       all(board[i][i][n-1-i] == player for i in range(n)) or \
       all(board[i][n-1-i][i] == player for i in range(n)) or \
       all(board[i][n-1-i][n-1-i] == player for i in range(n)):
        return True
    
    # Other diagonals
    if all(board[0][j][j] == player for j in range(n)) and \
       all(board[1][j][j] == player for j in range(n)) and \
       all(board[2][j][j] == player for j in range(n)):
        return True
        
    if all(board[0][j][n-1-j] == player for j in range(n)) and \
       all(board[1][j][n-1-j] == player for j in range(n)) and \
       all(board[2][j][n-1-j] == player for j in range(n)):
        return True
        
    if all(board[n-1][j][j] == player for j in range(n)) and \
       all(board[n-2][j][j] == player for j in range(n)) and \
       all(board[n-3][j][j] == player for j in range(n)):
        return True
        
    if all(board[n-1][j][n-1-j] == player for j in range(n)) and \
       all(board[n-2][j][n-1-j] == player for j in range(n)) and \
       all(board[n-3][j][n-1-j] == player for j in range(n)):
        return True

    # Main diagonal through cube - all directions
    # These are the 4 main space diagonals
    if all(board[i][i][i] == player for i in range(n)) or \
       all(board[n-1-i][i][i] == player for i in range(n)) or \
       all(board[i][n-1-i][i] == player for i in range(n)) or \
       all(board[i][i][n-1-i] == player for i in range(n)):
        return True
    
    return False
