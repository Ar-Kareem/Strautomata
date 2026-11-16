
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier manipulation
    b = np.array(board)
    
    # Check if we can win in this move
    for i in range(4):
        for j in range(4):
            if b[i, j] == 0:  # Empty spot
                # Try placing our mark
                b[i, j] = 1
                if check_winner(b) == 1:
                    b[i, j] = 0  # Reset
                    return (i, j)
                b[i, j] = 0  # Reset
    
    # If opponent can win, block them
    for i in range(4):
        for j in range(4):
            if b[i, j] == 0:  # Empty spot
                # Try placing opponent's mark
                b[i, j] = -1
                if check_winner(b) == -1:
                    b[i, j] = 0  # Reset
                    return (i, j)
                b[i, j] = 0  # Reset
    
    # If no immediate win or block, use heuristic
    # Prioritize center positions, then corners, then edges
    
    # Define priority positions (center first, then corners, then others)
    priorities = [
        (1, 1), (1, 2), (2, 1), (2, 2),  # Center positions
        (0, 0), (0, 3), (3, 0), (3, 3),  # Corner positions
        (0, 1), (0, 2), (1, 0), (1, 3), (2, 0), (2, 3), (3, 1), (3, 2)  # Edge positions
    ]
    
    # Find first empty position with highest priority
    for row, col in priorities:
        if b[row, col] == 0:
            return (row, col)
    
    # Fallback - find any empty position
    for i in range(4):
        for j in range(4):
            if b[i, j] == 0:
                return (i, j)

def check_winner(board):
    """Check if there's a winner. Return 1 if player 1 wins, -1 if player -1 wins, 0 if no winner."""
    # Check rows
    for i in range(4):
        if abs(sum(board[i, :])) == 4:
            return board[i, 0]
    
    # Check columns
    for j in range(4):
        if abs(sum(board[:, j])) == 4:
            return board[0, j]
    
    # Check main diagonal
    if abs(sum(board[i, i] for i in range(4))) == 4:
        return board[0, 0]
    
    # Check anti-diagonal
    if abs(sum(board[i, 3-i] for i in range(4))) == 4:
        return board[0, 3]
    
    return 0  # No winner
