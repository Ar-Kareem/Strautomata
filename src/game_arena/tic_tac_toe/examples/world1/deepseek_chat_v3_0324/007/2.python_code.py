
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert the board to numpy array for easier manipulation
    board = np.array(board)
    
    # Check all possible lines (rows, columns, diagonals) for potential winning move
    lines = [
        # Rows
        board[0, :], board[1, :], board[2, :],
        # Columns
        board[:, 0], board[:, 1], board[:, 2],
        # Diagonals
        np.diag(board), np.diag(np.fliplr(board))
    ]
    
    # 1. Check for immediate winning move
    for i, line in enumerate(lines):
        if sum(line == 1) == 2 and sum(line == 0) == 1:
            if i < 3:  # Row
                row = i
                col = np.where(line == 0)[0][0]
                return (row, col)
            elif i < 6:  # Column
                col = i - 3
                row = np.where(line == 0)[0][0]
                return (row, col)
            elif i == 6:  # Main diagonal
                idx = np.where(np.diag(board) == 0)[0][0]
                return (idx, idx)
            else:  # Anti-diagonal
                idx = np.where(np.diag(np.fliplr(board)) == 0)[0][0]
                return (idx, 2 - idx)
    
    # 2. Check for opponent's potential win and block
    for i, line in enumerate(lines):
        if sum(line == -1) == 2 and sum(line == 0) == 1:
            if i < 3:  # Row
                row = i
                col = np.where(line == 0)[0][0]
                return (row, col)
            elif i < 6:  # Column
                col = i - 3
                row = np.where(line == 0)[0][0]
                return (row, col)
            elif i == 6:  # Main diagonal
                idx = np.where(np.diag(board) == 0)[0][0]
                return (idx, idx)
            else:  # Anti-diagonal
                idx = np.where(np.diag(np.fliplr(board)) == 0)[0][0]
                return (idx, 2 - idx)
    
    # 3. Take center if available
    if board[1, 1] == 0:
        return (1, 1)
    
    # 4. Take a corner if available
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for corner in corners:
        if board[corner] == 0:
            return corner
    
    # 5. Take any available side
    sides = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for side in sides:
        if board[side] == 0:
            return side
    
    # Fallback (shouldn't reach here if board isn't full)
    return (0, 0)
