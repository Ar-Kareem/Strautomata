
import numpy as np
from typing import List, Tuple
import random

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert board to numpy array for easier manipulation
    board_array = np.array(board)
    
    # All possible lines in 3D Tic Tac Toe (49 total)
    lines = []
    
    # Add all rows in each layer
    for z in range(3):
        for y in range(3):
            lines.append(board_array[z, y, :])  # row
        for x in range(3):
            lines.append(board_array[z, :, x])  # column
    
    # Add all columns through layers
    for x in range(3):
        for y in range(3):
            lines.append(board_array[:, y, x])  # depth
    
    # Add 2D diagonals in each layer
    for z in range(3):
        lines.append(board_array[z, [0, 1, 2], [0, 1, 2]])  # top-left to bottom-right
        lines.append(board_array[z, [0, 1, 2], [2, 1, 0]])  # top-right to bottom-left
    
    # Add vertical diagonals through layers
    for x in range(3):
        lines.append(board_array[:, [0, 1, 2], x])  # front-top to back-bottom
        lines.append(board_array[:, [2, 1, 0], x])  # front-bottom to back-top
    
    # Add 3D space diagonals
    lines.append(board_array[[0, 1, 2], [0, 1, 2], [0, 1, 2]])  # top-front-left to bottom-back-right
    lines.append(board_array[[0, 1, 2], [0, 1, 2], [2, 1, 0]])  # top-front-right to bottom-back-left
    lines.append(board_array[[0, 1, 2], [2, 1, 0], [0, 1, 2]])  # top-back-left to bottom-front-right
    lines.append(board_array[[0, 1, 2], [2, 1, 0], [2, 1, 0]])  # top-back-right to bottom-front-left
    
    # Check for winning move (two 1s and one 0)
    for line in lines:
        if np.sum(line == 1) == 2 and np.sum(line == 0) == 1:
            empty_pos = np.where(line == 0)[0][0]
            # Find which coordinates correspond to this empty position
            # This is a bit complex since we need to trace back which line this was
            # Instead, let's scan the board for empty cells that complete a line
            pass
    
    # More efficient way to check for winning moves
    empty_cells = np.argwhere(board_array == 0)
    for (z, y, x) in empty_cells:
        # Temporarily place our mark
        board_array[z, y, x] = 1
        # Check if this creates a line of three
        if check_win(board_array, 1):
            return (z, y, x)
        # Undo the temporary placement
        board_array[z, y, x] = 0
    
    # Check for blocking move (two -1s and one 0)
    for (z, y, x) in empty_cells:
        # Temporarily place opponent's mark
        board_array[z, y, x] = -1
        # Check if this creates a line of three for opponent
        if check_win(board_array, -1):
            board_array[z, y, x] = 0  # undo
            return (z, y, x)
        # Undo the temporary placement
        board_array[z, y, x] = 0
    
    # Center is most valuable position
    if board_array[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Then corners
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    random.shuffle(corners)  # randomize corner selection
    for (z, y, x) in corners:
        if board_array[z, y, x] == 0:
            return (z, y, x)
    
    # Then edges
    edges = [(0, 0, 1), (0, 1, 0), (0, 1, 2), (0, 2, 1),
             (1, 0, 0), (1, 0, 2), (1, 2, 0), (1, 2, 2),
             (2, 0, 1), (2, 1, 0), (2, 1, 2), (2, 2, 1)]
    random.shuffle(edges)  # randomize edge selection
    for (z, y, x) in edges:
        if board_array[z, y, x] == 0:
            return (z, y, x)
    
    # If all else fails, pick first available cell
    for (z, y, x) in empty_cells:
        return (z, y, x)
    
    # Should never reach here if board isn't full
    return (0, 0, 0)

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the specified player has a winning line"""
    # Check all rows in each layer
    for z in range(3):
        for y in range(3):
            if np.all(board[z, y, :] == player):
                return True
        for x in range(3):
            if np.all(board[z, :, x] == player):
                return True
    
    # Check all columns through layers
    for x in range(3):
        for y in range(3):
            if np.all(board[:, y, x] == player):
                return True
    
    # Check 2D diagonals in each layer
    for z in range(3):
        if np.all(board[z, [0, 1, 2], [0, 1, 2]] == player):
            return True
        if np.all(board[z, [0, 1, 2], [2, 1, 0]] == player):
            return True
    
    # Check vertical diagonals through layers
    for x in range(3):
        if np.all(board[:, [0, 1, 2], x] == player):
            return True
        if np.all(board[:, [2, 1, 0], x] == player):
            return True
    
    # Check 3D space diagonals
    if np.all(board[[0, 1, 2], [0, 1, 2], [0, 1, 2]] == player):
        return True
    if np.all(board[[0, 1, 2], [0, 1, 2], [2, 1, 0]] == player):
        return True
    if np.all(board[[0, 1, 2], [2, 1, 0], [0, 1, 2]] == player):
        return True
    if np.all(board[[0, 1, 2], [2, 1, 0], [2, 1, 0]] == player):
        return True
    
    return False
