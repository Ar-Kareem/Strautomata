
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Get empty cells
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i, j, k] == 0:
                    empty_cells.append((i, j, k))
    
    # Check if I can win in next move
    for i, j, k in empty_cells:
        board[i, j, k] = 1
        if check_winner(board) == 1:
            return (i, j, k)
        board[i, j, k] = 0
    
    # Check if opponent can win and block
    for i, j, k in empty_cells:
        board[i, j, k] = -1
        if check_winner(board) == -1:
            return (i, j, k)
        board[i, j, k] = 0
    
    # Prioritize center
    if (1, 1, 1) in empty_cells:
        return (1, 1, 1)
    
    # Prioritize face centers (not corners)
    face_centers = [(1,1,0), (1,1,2), (1,0,1), (1,2,1), (0,1,1), (2,1,1)]
    for move in face_centers:
        if move in empty_cells:
            return move
    
    # Prioritize corners
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2), 
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for move in corners:
        if move in empty_cells:
            return move
    
    # Otherwise take any empty cell
    return empty_cells[0]

def check_winner(board):
    # Check all possible winning lines in 3D
    for i in range(3):
        for j in range(3):
            # Check lines along the k-axis
            if abs(board[i, j, 0] + board[i, j, 1] + board[i, j, 2]) == 3:
                return board[i, j, 0]
            # Check lines along the j-axis
            if abs(board[i, 0, j] + board[i, 1, j] + board[i, 2, j]) == 3:
                return board[i, 0, j]
            # Check lines along the i-axis
            if abs(board[0, i, j] + board[1, i, j] + board[2, i, j]) == 3:
                return board[0, i, j]
    
    # Check diagonals in each slice
    for i in range(3):
        # j-k diagonals
        if abs(board[i, 0, 0] + board[i, 1, 1] + board[i, 2, 2]) == 3:
            return board[i, 0, 0]
        if abs(board[i, 0, 2] + board[i, 1, 1] + board[i, 2, 0]) == 3:
            return board[i, 0, 2]
        # i-k diagonals
        if abs(board[0, i, 0] + board[1, i, 1] + board[2, i, 2]) == 3:
            return board[0, i, 0]
        if abs(board[0, i, 2] + board[1, i, 1] + board[2, i, 0]) == 3:
            return board[0, i, 2]
        # i-j diagonals
        if abs(board[0, 0, i] + board[1, 1, i] + board[2, 2, i]) == 3:
            return board[0, 0, i]
        if abs(board[0, 2, i] + board[1, 1, i] + board[2, 0, i]) == 3:
            return board[0, 2, i]
    
    # Check main 3D diagonals
    if abs(board[0, 0, 0] + board[1, 1, 1] + board[2, 2, 2]) == 3:
        return board[0, 0, 0]
    if abs(board[0, 0, 2] + board[1, 1, 1] + board[2, 2, 0]) == 3:
        return board[0, 0, 2]
    if abs(board[0, 2, 0] + board[1, 1, 1] + board[2, 0, 2]) == 3:
        return board[0, 2, 0]
    if abs(board[0, 2, 2] + board[1, 1, 1] + board[2, 0, 0]) == 3:
        return board[0, 2, 2]
    
    return 0
