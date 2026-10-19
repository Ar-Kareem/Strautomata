
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Check if we can win in this move
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # Empty cell
                # Temporarily place our mark
                board_np[i][j] = 1
                if check_winner(board_np) == 1:
                    board_np[i][j] = 0  # Reset
                    return (i, j)
                board_np[i][j] = 0  # Reset
    
    # Check if opponent can win in next move and block them
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:  # Empty cell
                # Temporarily place opponent's mark
                board_np[i][j] = -1
                if check_winner(board_np) == -1:
                    board_np[i][j] = 0  # Reset
                    return (i, j)
                board_np[i][j] = 0  # Reset
    
    # Prefer center positions if available
    center_positions = [(1,1), (1,2), (2,1), (2,2)]
    for r, c in center_positions:
        if board[r][c] == 0:
            return (r, c)
    
    # Prefer corners
    corner_positions = [(0,0), (0,3), (3,0), (3,3)]
    for r, c in corner_positions:
        if board[r][c] == 0:
            return (r, c)
    
    # If no special moves, pick the first available position
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                return (i, j)

def check_winner(board: np.ndarray) -> int:
    # Check rows
    for row in board:
        if np.all(row == 1):
            return 1
        if np.all(row == -1):
            return -1
    
    # Check columns
    for col in board.T:
        if np.all(col == 1):
            return 1
        if np.all(col == -1):
            return -1
    
    # Check main diagonal
    if np.all(np.diag(board) == 1):
        return 1
    if np.all(np.diag(board) == -1):
        return -1
    
    # Check anti-diagonal
    if np.all(np.diag(np.fliplr(board)) == 1):
        return 1
    if np.all(np.diag(np.fliplr(board)) == -1):
        return -1
    
    # No winner
    return 0
