
import random
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for easier manipulation
    board_arr = np.array(board)
    
    # Get list of empty cells (where board is 0)
    empty_cells = list(zip(*np.where(board_arr == 0)))
    
    # 1. Check for immediate winning moves
    for row, col in empty_cells:
        # Check if placing here would complete a line
        temp_board = board_arr.copy()
        temp_board[row, col] = 1
        
        # Check all possible lines
        if (temp_board[row, :] == 1).all():  # Check row
            return (row, col)
        if (temp_board[:, col] == 1).all():  # Check column
            return (row, col)
        if row == col and (np.diag(temp_board) == 1).all():  # Check main diagonal
            return (row, col)
        if row + col == 2 and (np.diag(np.fliplr(temp_board)) == 1).all():  # Check anti-diagonal
            return (row, col)
    
    # 2. Block potential opponent wins (where two cells in a line are empty and one is mine)
    opponent_threats = []
    for row, col in empty_cells:
        temp_board = board_arr.copy()
        temp_board[row, col] = 1  # Simulate opponent move
        
        # Check if this would create a line with two opponent marks (represented by 0s in our board)
        # Since we can't see opponent marks, we look for lines where we have few marks
        row_vals = temp_board[row, :]
        col_vals = temp_board[:, col]
        
        # Check rows and columns for potential threats
        if (row_vals == 0).sum() >= 2 and (row_vals == 1).sum() == 0:
            opponent_threats.append((row, col))
        if (col_vals == 0).sum() >= 2 and (col_vals == 1).sum() == 0:
            opponent_threats.append((row, col))
        
        # Check diagonals
        if row == col:
            diag = np.diag(temp_board)
            if (diag == 0).sum() >= 2 and (diag == 1).sum() == 0:
                opponent_threats.append((row, col))
        if row + col == 2:
            anti_diag = np.diag(np.fliplr(temp_board))
            if (anti_diag == 0).sum() >= 2 and (anti_diag == 1).sum() == 0:
                opponent_threats.append((row, col))
    
    # If we found opponent threats, block one of them
    if opponent_threats:
        return random.choice(opponent_threats)
    
    # 3. Take center if available
    if board_arr[1, 1] == 0:
        return (1, 1)
    
    # 4. Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    available_corners = [c for c in corners if board_arr[c[0], c[1]] == 0]
    if available_corners:
        return random.choice(available_corners)
    
    # 5. Take any available edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    available_edges = [e for e in edges if board_arr[e[0], e[1]] == 0]
    if available_edges:
        return random.choice(available_edges)
    
    # 6. Fallback - should theoretically never reach here if board isn't full
    return empty_cells[0] if empty_cells else (0, 0)
