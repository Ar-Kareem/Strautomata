
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Check for winning moves first
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:  # Empty cell
                    # Try placing our piece here
                    board_np[i, j, k] = 1
                    if check_win(board_np, 1):
                        return (i, j, k)
                    # Reset the cell
                    board_np[i, j, k] = 0
    
    # Check for blocking opponent's winning move
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:  # Empty cell
                    # Try placing opponent's piece here
                    board_np[i, j, k] = -1
                    if check_win(board_np, -1):
                        return (i, j, k)
                    # Reset the cell
                    board_np[i, j, k] = 0
    
    # If no immediate win or block, use a strategic approach
    # Prefer center, then corners, then edges
    priority_positions = [
        (1, 1, 1),  # Center
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),  # Corners
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2),
        (0, 0, 1), (0, 1, 0), (0, 1, 2), (0, 2, 1),  # Edges
        (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2),
        (2, 0, 1), (2, 1, 0), (2, 1, 2), (2, 2, 1),
        (1, 1, 0), (1, 1, 2)
    ]
    
    for pos in priority_positions:
        if board_np[pos] == 0:
            return pos
    
    # Fallback: first empty cell found
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:
                    return (i, j, k)
    
    # This should never happen in a valid game
    raise Exception("No valid moves available")

def check_win(board: np.ndarray, player: int) -> bool:
    # Check all possible winning lines in 3D tic-tac-toe
    # Rows in each layer
    for layer in range(3):
        for row in range(3):
            if np.all(board[layer, row, :] == player):
                return True
        for col in range(3):
            if np.all(board[layer, :, col] == player):
                return True
        # Diagonals in each layer
        if np.all(board[layer, :, :].diagonal() == player):
            return True
        if np.all(np.fliplr(board[layer, :, :]).diagonal() == player):
            return True
    
    # Columns through layers
    for row in range(3):
        for col in range(3):
            if np.all(board[:, row, col] == player):
                return True
    
    # Diagonals through layers
    # Vertical diagonals
    if np.all(np.array([board[i, i, i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, i, 2-i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, 2-i, i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, 2-i, 2-i] for i in range(3)]) == player):
        return True
    
    # Face diagonals
    if np.all(np.array([board[i, i, 0] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, 2-i, 0] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, i, 2] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[i, 2-i, 2] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[0, i, i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[0, i, 2-i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[2, i, i] for i in range(3)]) == player):
        return True
    if np.all(np.array([board[2, i, 2-i] for i in range(3)]) == player):
        return True
    
    return False
