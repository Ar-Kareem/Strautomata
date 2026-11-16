
import numpy as np
from typing import Optional, Tuple

def policy(board: list[list[int]]) -> tuple[int, int]:
    """Determine the best move for the AI player in 4x4 Tic Tac Toe."""
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # First check if we can win in the next move
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = 1
                if check_winner(board_array) == 1:
                    return (i, j)
                board_array[i, j] = 0
    
    # Then check if opponent can win in the next move and block them
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                board_array[i, j] = -1
                if check_winner(board_array) == -1:
                    return (i, j)
                board_array[i, j] = 0
    
    # If center is empty, take it
    if board_array[1, 1] == 0 or board_array[1, 2] == 0 or board_array[2, 1] == 0 or board_array[2, 2] == 0:
        for i, j in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            if board_array[i, j] == 0:
                return (i, j)
    
    # Try to take a corner if available
    corners = [(0, 0), (0, 3), (3, 0), (3, 3)]
    for i, j in corners:
        if board_array[i, j] == 0:
            return (i, j)
    
    # Try to take an edge if available
    edges = [(0, 1), (0, 2), (1, 0), (1, 3), 
             (2, 0), (2, 3), (3, 1), (3, 2)]
    for i, j in edges:
        if board_array[i, j] == 0:
            return (i, j)
    
    # If all else fails, take any available spot
    for i in range(4):
        for j in range(4):
            if board_array[i, j] == 0:
                return (i, j)
    
    # Should never reach here if the game isn't already over
    return (0, 0)

def check_winner(board: np.ndarray) -> Optional[int]:
    """Check if there's a winner on the current board.
    Returns 1 if player 1 wins, -1 if player -1 wins, 0 for draw, None if game continues."""
    # Check rows
    for row in board:
        if all(cell == 1 for cell in row):
            return 1
        if all(cell == -1 for cell in row):
            return -1
    
    # Check columns
    for col in board.T:
        if all(cell == 1 for cell in col):
            return 1
        if all(cell == -1 for cell in col):
            return -1
    
    # Check diagonals
    if all(board[i, i] == 1 for i in range(4)):
        return 1
    if all(board[i, 3 - i] == 1 for i in range(4)):
        return 1
    if all(board[i, i] == -1 for i in range(4)):
        return -1
    if all(board[i, 3 - i] == -1 for i in range(4)):
        return -1
    
    # Check if board is full (draw)
    if 0 not in board:
        return 0
    
    # Game continues
    return None
