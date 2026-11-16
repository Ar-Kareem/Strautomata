
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier manipulation
    b = np.array(board)
    
    # Check if I can win in one move
    for i in range(3):
        for j in range(3):
            if b[i, j] == 0:  # Empty spot
                # Try placing my mark there
                b[i, j] = 1
                if check_winner(b) == 1:
                    b[i, j] = 0  # Reset
                    return (i, j)
                b[i, j] = 0  # Reset
    
    # Check if opponent can win in one move and block
    for i in range(3):
        for j in range(3):
            if b[i, j] == 0:  # Empty spot
                # Try placing opponent's mark there
                b[i, j] = -1
                if check_winner(b) == -1:
                    b[i, j] = 0  # Reset
                    return (i, j)
                b[i, j] = 0  # Reset
    
    # If no immediate win/block, choose based on priority
    # Priority: center, then corners, then edges
    
    # Center
    if b[1, 1] == 0:
        return (1, 1)
    
    # Corners in order
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if b[r, c] == 0:
            return (r, c)
    
    # Edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in edges:
        if b[r, c] == 0:
            return (r, c)
    
    # Fallback (shouldn't really reach here in normal gameplay)
    for i in range(3):
        for j in range(3):
            if b[i, j] == 0:
                return (i, j)

def check_winner(board: np.ndarray) -> int:
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
