
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier manipulation
    b = np.array(board)
    
    # Check if we can win in one move
    for i in range(3):
        for j in range(3):
            if b[i, j] == 0:  # Empty cell
                # Try placing our mark
                b[i, j] = 1
                # Check if this leads to a win
                if check_winner(b) == 1:
                    b[i, j] = 0  # Reset
                    return (i, j)
                b[i, j] = 0  # Reset
    
    # Check if opponent can win in one move and block them
    for i in range(3):
        for j in range(3):
            if b[i, j] == 0:  # Empty cell
                # Try placing opponent's mark
                b[i, j] = -1
                # Check if this leads to opponent winning
                if check_winner(b) == -1:
                    b[i, j] = 0  # Reset
                    return (i, j)
                b[i, j] = 0  # Reset
    
    # Prefer center if it's empty
    if b[1, 1] == 0:
        return (1, 1)
    
    # Prefer corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for i, j in corners:
        if b[i, j] == 0:
            return (i, j)
    
    # If no strategic move, pick any empty spot
    for i in range(3):
        for j in range(3):
            if b[i, j] == 0:
                return (i, j)
    
    # This shouldn't happen in a valid game state
    return (0, 0)

def check_winner(board: np.ndarray) -> int:
    """Returns 1 if X wins, -1 if O wins, 0 if no winner"""
    # Check rows
    for i in range(3):
        if board[i, 0] == board[i, 1] == board[i, 2] != 0:
            return board[i, 0]
    
    # Check columns
    for j in range(3):
        if board[0, j] == board[1, j] == board[2, j] != 0:
            return board[0, j]
    
    # Check diagonals
    if board[0, 0] == board[1, 1] == board[2, 2] != 0:
        return board[0, 0]
    
    if board[0, 2] == board[1, 1] == board[2, 0] != 0:
        return board[0, 2]
    
    # No winner
    return 0
