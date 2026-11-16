
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Get all empty positions
    empty_positions = np.where(board_array == 0)
    empty_coords = list(zip(empty_positions[0], empty_positions[1], empty_positions[2]))
    
    # If board is empty, take the center
    if len(empty_coords) == 27:
        return (1, 1, 1)
    
    # Check for winning moves
    for coord in empty_coords:
        if is_winning_move(board_array, coord, 1):
            return coord
    
    # Check for blocking opponent's winning moves
    for coord in empty_coords:
        if is_winning_move(board_array, coord, -1):
            return coord
    
    # Try to create threats (two in a row with empty third)
    for coord in empty_coords:
        if creates_threat(board_array, coord, 1):
            return coord
    
    # Block opponent's threats
    for coord in empty_coords:
        if creates_threat(board_array, coord, -1):
            return coord
    
    # Prefer center and corners for strategic positioning
    priority_positions = [(1,1,1), (0,0,0), (0,0,2), (0,2,0), (0,2,2),
                         (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    
    for pos in priority_positions:
        if pos in empty_coords:
            return pos
    
    # If no strategic move found, pick first available
    return empty_coords[0]

def is_winning_move(board: np.ndarray, coord: Tuple[int, int, int], player: int) -> bool:
    """Check if placing a piece at coord would win the game for player"""
    test_board = board.copy()
    test_board[coord] = player
    
    # Check all possible lines through this position
    x, y, z = coord
    
    # Rows along x-axis
    if np.all(test_board[x, y, :] == player):
        return True
    
    # Rows along y-axis
    if np.all(test_board[x, :, z] == player):
        return True
    
    # Rows along z-axis
    if np.all(test_board[:, y, z] == player):
        return True
    
    # Diagonals on xy-plane (z fixed)
    if y == z and np.all([test_board[i, i, z] == player for i in range(3)]):
        return True
    
    if y + z == 2 and np.all([test_board[i, 2-i, z] == player for i in range(3)]):
        return True
    
    # Diagonals on xz-plane (y fixed)
    if x == z and np.all([test_board[i, y, i] == player for i in range(3)]):
        return True
    
    if x + z == 2 and np.all([test_board[2-i, y, i] == player for i in range(3)]):
        return True
    
    # Diagonals on yz-plane (x fixed)
    if x == y and np.all([test_board[x, i, i] == player for i in range(3)]):
        return True
    
    if x + y == 2 and np.all([test_board[x, 2-i, i] == player for i in range(3)]):
        return True
    
    # Space diagonals
    if x == y == z and np.all([test_board[i, i, i] == player for i in range(3)]):
        return True
    
    if x == y and x + z == 2 and np.all([test_board[i, i, 2-i] == player for i in range(3)]):
        return True
    
    if x == z and x + y == 2 and np.all([test_board[i, 2-i, i] == player for i in range(3)]):
        return True
    
    if y == z and x + y == 2 and np.all([test_board[2-i, i, i] == player for i in range(3)]):
        return True
    
    return False

def creates_threat(board: np.ndarray, coord: Tuple[int, int, int], player: int) -> bool:
    """Check if placing a piece at coord creates a threat (two in a row)"""
    test_board = board.copy()
    test_board[coord] = player
    
    x, y, z = coord
    
    # Check rows along x-axis
    row_x = test_board[x, y, :]
    if np.sum(row_x == player) == 2 and np.sum(row_x == 0) == 1:
        return True
    
    # Check rows along y-axis
    row_y = test_board[x, :, z]
    if np.sum(row_y == player) == 2 and np.sum(row_y == 0) == 1:
        return True
    
    # Check rows along z-axis
    row_z = test_board[:, y, z]
    if np.sum(row_z == player) == 2 and np.sum(row_z == 0) == 1:
        return True
    
    # Check main diagonals on planes (simplified approach)
    # xy-plane diagonal
    if y == z:
        diag1 = [test_board[i, i, z] for i in range(3)]
        diag1_arr = np.array(diag1)
        if np.sum(diag1_arr == player) == 2 and np.sum(diag1_arr == 0) == 1:
            return True
    
    if y + z == 2:
        diag2 = [test_board[i, 2-i, z] for i in range(3)]
        diag2_arr = np.array(diag2)
        if np.sum(diag2_arr == player) == 2 and np.sum(diag2_arr == 0) == 1:
            return True
    
    # xz-plane diagonal
    if x == z:
        diag3 = [test_board[i, y, i] for i in range(3)]
        diag3_arr = np.array(diag3)
        if np.sum(diag3_arr == player) == 2 and np.sum(diag3_arr == 0) == 1:
            return True
    
    if x + z == 2:
        diag4 = [test_board[2-i, y, i] for i in range(3)]
        diag4_arr = np.array(diag4)
        if np.sum(diag4_arr == player) == 2 and np.sum(diag4_arr == 0) == 1:
            return True
    
    # yz-plane diagonal
    if x == y:
        diag5 = [test_board[x, i, i] for i in range(3)]
        diag5_arr = np.array(diag5)
        if np.sum(diag5_arr == player) == 2 and np.sum(diag5_arr == 0) == 1:
            return True
    
    if x + y == 2:
        diag6 = [test_board[x, 2-i, i] for i in range(3)]
        diag6_arr = np.array(diag6)
        if np.sum(diag6_arr == player) == 2 and np.sum(diag6_arr == 0) == 1:
            return True
    
    return False
