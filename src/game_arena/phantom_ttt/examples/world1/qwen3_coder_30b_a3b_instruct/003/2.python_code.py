
import random
import numpy as np

def policy(board: list[list[int]], legal_moves: list[int]) -> int:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Convert legal moves from 0-8 to (row, col) coordinates
    legal_positions = []
    for move in legal_moves:
        row = move // 3
        col = move % 3
        legal_positions.append((row, col))
    
    # Filter out positions already confirmed as ours 
    available_positions = []
    for row, col in legal_positions:
        if board[row][col] != 1:  # Not confirmed ours
            available_positions.append((row, col))
    
    if not available_positions:
        # Fallback to any legal move if all are confirmed ours (shouldn't happen)
        row, col = legal_positions[0]
        return row * 3 + col
    
    # Check for winning moves (3 in a row with 2 ours and 1 empty)
    for row, col in available_positions:
        # Check row
        if all(board[row][i] == 1 for i in range(3) if i != col):
            # Row has two ours and one empty, good spot
            if board[row][col] == 0:
                return row * 3 + col
        # Check column
        if all(board[i][col] == 1 for i in range(3) if i != row):
            # Col has two ours and one empty, good spot  
            if board[row][col] == 0:
                return row * 3 + col
        # Check diagonals
        if row == col:
            if all(board[i][i] == 1 for i in range(3) if i != row):
                if board[row][col] == 0:
                    return row * 3 + col
        if row + col == 2:
            if all(board[i][2-i] == 1 for i in range(3) if i != row):
                if board[row][col] == 0:
                    return row * 3 + col
    
    # Check for blocking moves (opponent two in a row)
    for row, col in available_positions:
        # Check row for potential opponent win
        row_val = [board[row][c] for c in range(3)]
        if row_val.count(0) == 1 and row_val.count(1) == 2:  # Already confirmed ours
            if board[row][col] == 0:
                return row * 3 + col
        # Check column for potential opponent win
        col_val = [board[r][col] for r in range(3)]
        if col_val.count(0) == 1 and col_val.count(1) == 2:  # Already confirmed ours
            if board[row][col] == 0:
                return row * 3 + col
        # Check diagonals
        if row == col:
            diag1 = [board[i][i] for i in range(3)]
            if diag1.count(0) == 1 and diag1.count(1) == 2:
                if board[row][col] == 0:
                    return row * 3 + col
        if row + col == 2:
            diag2 = [board[i][2-i] for i in range(3)]
            if diag2.count(0) == 1 and diag2.count(1) == 2:
                if board[row][col] == 0:
                    return row * 3 + col
    
    # Prefer corners if available
    corner_positions = [(0,0), (0,2), (2,0), (2,2)]
    available_corners = [pos for pos in corner_positions if pos in available_positions]
    
    if available_corners:
        # Prefer center if available
        center_pos = (1,1)
        if center_pos in available_positions:
            return center_pos[0] * 3 + center_pos[1]
        # Otherwise prefer corner
        return available_corners[0][0] * 3 + available_corners[0][1]
    
    # Prefer center if available
    center_pos = (1,1)
    if center_pos in available_positions:
        return center_pos[0] * 3 + center_pos[1]
    
    # If no high priority moves, choose one that reduces uncertainty
    # Prioritize positions that are not confirmed ours and in more potential winning lines
    # Simple heuristic: choose a safe move
    return available_positions[0][0] * 3 + available_positions[0][1]
