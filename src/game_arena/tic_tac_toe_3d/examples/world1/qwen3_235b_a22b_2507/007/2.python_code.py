
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    board = np.array(board)
    
    # All possible moves
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i, j, k] == 0]
    
    # Check for winning move for me (player 1)
    for cell in empty_cells:
        board[cell] = 1
        if check_win(board, 1):
            board[cell] = 0  # undo
            return cell
        board[cell] = 0  # undo
    
    # Check for opponent's winning move and block
    for cell in empty_cells:
        board[cell] = -1
        if check_win(board, -1):
            board[cell] = 0  # undo
            return cell
        board[cell] = 0  # undo
    
    # Prefer center
    if (1,1,1) in empty_cells:
        return (1,1,1)
    
    # Prefer face centers (6 of them)
    face_centers = [(1,1,0), (1,1,2), (1,0,1), (1,2,1), (0,1,1), (2,1,1)]
    for cell in face_centers:
        if cell in empty_cells:
            return cell
    
    # Prefer corners (8 of them)
    corners = [(i,j,k) for i in (0,2) for j in (0,2) for k in (0,2)]
    for cell in corners:
        if cell in empty_cells:
            return cell
    
    # Otherwise, return any empty cell (should not reach here in 3x3x3 unless board is full, but guaranteed to have move)
    return empty_cells[0]

def check_win(board, player):
    # Check all lines in 3D: along x, y, z, and diagonals
    # Axis-aligned lines
    for i in range(3):
        for j in range(3):
            # Along x (fixed y,z)
            if np.all(board[:, j, i] == player):
                return True
            # Along y (fixed x,z)
            if np.all(board[i, :, j] == player):
                return True
            # Along z (fixed x,y)
            if np.all(board[i, j, :] == player):
                return True

    # Diagonals on each face in xy, xz, yz planes
    # We'll check all possible 3-in-a-row diagonals manually
    # All 4 space diagonals through the cube
    if board[0,0,0] == board[1,1,1] == board[2,2,2] == player:
        return True
    if board[0,0,2] == board[1,1,1] == board[2,2,0] == player:
        return True
    if board[0,2,0] == board[1,1,1] == board[2,0,2] == player:
        return True
    if board[0,2,2] == board[1,1,1] == board[2,0,0] == player:
        return True

    # Face diagonals: 6 faces, 2 diagonals each
    for z in range(3):  # xy-faces
        if board[0,0,z] == board[1,1,z] == board[2,2,z] == player:
            return True
        if board[0,2,z] == board[1,1,z] == board[2,0,z] == player:
            return True
    for y in range(3):  # xz-faces
        if board[0,y,0] == board[1,y,1] == board[2,y,2] == player:
            return True
        if board[0,y,2] == board[1,y,1] == board[2,y,0] == player:
            return True
    for x in range(3):  # yz-faces
        if board[x,0,0] == board[x,1,1] == board[x,2,2] == player:
            return True
        if board[x,0,2] == board[x,1,1] == board[x,2,0] == player:
            return True

    return False
