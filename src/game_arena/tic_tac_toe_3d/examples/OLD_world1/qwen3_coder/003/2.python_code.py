
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Get all empty positions
    empty_positions = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board_array[i, j, k] == 0]
    
    # If no empty positions, return None (should not happen in a valid game)
    if not empty_positions:
        return (0, 0, 0)
    
    # Check for winning move
    for pos in empty_positions:
        board_array[pos] = 1
        if check_winner(board_array, 1):
            board_array[pos] = 0  # Reset
            return pos
        board_array[pos] = 0  # Reset
    
    # Check for blocking opponent's winning move
    for pos in empty_positions:
        board_array[pos] = -1
        if check_winner(board_array, -1):
            board_array[pos] = 0  # Reset
            return pos
        board_array[pos] = 0  # Reset
    
    # Try to take center if available
    center = (1, 1, 1)
    if center in empty_positions:
        return center
    
    # Try to take a corner
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    available_corners = [corner for corner in corners if corner in empty_positions]
    if available_corners:
        return available_corners[0]
    
    # Otherwise, take the first available position
    return empty_positions[0]

def check_winner(board: np.ndarray, player: int) -> bool:
    # Check rows, columns, and pillars (lines along x, y, z axes)
    for i in range(3):
        for j in range(3):
            # Rows (along x-axis)
            if np.all(board[i, j, :] == player):
                return True
            # Columns (along y-axis)
            if np.all(board[i, :, j] == player):
                return True
            # Pillars (along z-axis)
            if np.all(board[:, i, j] == player):
                return True
    
    # Check diagonals on each face
    for i in range(3):
        # Diagonals on xy-plane faces
        if np.all(np.diag(board[i, :, :]) == player) or np.all(np.diag(np.fliplr(board[i, :, :])) == player):
            return True
        # Diagonals on xz-plane faces
        if np.all(np.diag(board[:, i, :]) == player) or np.all(np.diag(np.fliplr(board[:, i, :])) == player):
            return True
        # Diagonals on yz-plane faces
        if np.all(np.diag(board[:, :, i]) == player) or np.all(np.diag(np.fliplr(board[:, :, i])) == player):
            return True
    
    # Check space diagonals
    if (np.all([board[i, i, i] == player for i in range(3)]) or
        np.all([board[i, i, 2-i] == player for i in range(3)]) or
        np.all([board[i, 2-i, i] == player for i in range(3)]) or
        np.all([board[2-i, i, i] == player for i in range(3)])):
        return True
    
    # Check diagonal planes
    if (np.all([board[i, 2-i, 2-i] == player for i in range(3)]) or
        np.all([board[2-i, i, 2-i] == player for i in range(3)]) or
        np.all([board[2-i, 2-i, i] == player for i in range(3)]) or
        np.all([board[2-i, 2-i, 2-i] == player for i in range(3)])):
        return True
    
    return False
