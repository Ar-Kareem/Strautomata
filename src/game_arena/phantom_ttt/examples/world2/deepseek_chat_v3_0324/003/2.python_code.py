
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    n = 3
    
    # List of all possible lines (rows, columns, diagonals)
    lines = [
        [(0, 0), (0, 1), (0, 2)],  # Row 0
        [(1, 0), (1, 1), (1, 2)],  # Row 1
        [(2, 0), (2, 1), (2, 2)],  # Row 2
        [(0, 0), (1, 0), (2, 0)],  # Column 0
        [(0, 1), (1, 1), (2, 1)],  # Column 1
        [(0, 2), (1, 2), (2, 2)],  # Column 2
        [(0, 0), (1, 1), (2, 2)],  # Main diagonal
        [(0, 2), (1, 1), (2, 0)]   # Anti-diagonal
    ]
    
    # Step 1: Check for immediate winning move (two 1s and one 0)
    for line in lines:
        values = [board[pos[0], pos[1]] for pos in line]
        if sum(values) == 2 and 0 in values:
            for pos in line:
                if board[pos[0], pos[1]] == 0:
                    return pos  # Return the winning move
    
    # Step 2: Block potential opponent winning moves (assume opponent is playing optimally)
    # For each unconfirmed cell, check if it could belong to a line with two 0s and one 1
    for line in lines:
        values = [board[pos[0], pos[1]] for pos in line]
        if sum(values) == 1 and values.count(0) == 2:
            for pos in line:
                if board[pos[0], pos[1]] == 0:
                    # Block by marking one of the 0s
                    return pos
    
    # Step 3: Prefer center if available
    if board[1, 1] == 0:
        return (1, 1)
    
    # Step 4: Prefer corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for pos in corners:
        if board[pos[0], pos[1]] == 0:
            return pos
    
    # Step 5: Choose any remaining edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for pos in edges:
        if board[pos[0], pos[1]] == 0:
            return pos
    
    # Fallback: Choose any legal move (shouldn't reach here if board isn't full)
    for i in range(n):
        for j in range(n):
            if board[i, j] == 0:
                return (i, j)
    
    # If no legal move found (shouldn't happen in a valid game)
    raise Exception("No legal move available")
