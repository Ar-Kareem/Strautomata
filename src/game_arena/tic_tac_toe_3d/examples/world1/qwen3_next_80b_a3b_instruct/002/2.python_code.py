
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    b = np.array(board)
    
    # Get all empty positions
    empty_positions = np.where(b == 0)
    empty_cells = list(zip(empty_positions[0], empty_positions[1], empty_positions[2]))
    
    # If no empty cells, return arbitrary (shouldn't happen in practice)
    if len(empty_cells) == 0:
        return (0, 0, 0)
    
    # Check for immediate win
    for move in empty_cells:
        x, y, z = move
        b[x, y, z] = 1  # Try placing my mark
        if check_win(b, 1):
            b[x, y, z] = 0  # Revert
            return move
        b[x, y, z] = 0  # Revert
    
    # Check for opponent's immediate win and block it
    for move in empty_cells:
        x, y, z = move
        b[x, y, z] = -1  # Try placing opponent's mark
        if check_win(b, -1):
            b[x, y, z] = 0  # Revert
            return move
        b[x, y, z] = 0  # Revert
    
    # Heuristic: prefer center (1,1,1), then corners, then edges
    center = (1, 1, 1)
    corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2), 
               (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
    edges = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if (i, j, k) not in corners and (i, j, k) != center:
                    edges.append((i, j, k))
    
    # Prioritize moves: center, then corners, then edges
    for pos in [center] + corners + edges:
        if pos in empty_cells:
            return pos
    
    # Fallback: return first empty cell (shouldn't reach here due to above logic)
    return empty_cells[0]

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won on the 3x3x3 board."""
    # Check all possible lines: rows, columns, depths, and diagonals
    
    # Rows (x fixed, y and z vary) - 3x3 = 9 lines per x
    for x in range(3):
        for y in range(3):
            if all(board[x, y, z] == player for z in range(3)):
                return True
        for z in range(3):
            if all(board[x, y, z] == player for y in range(3)):
                return True
        for y in range(3):
            if all(board[x, y, z] == player for z in range(3)):
                return True
    
    # For each fixed z (depth), check y rows and x columns
    for z in range(3):
        for y in range(3):
            if all(board[x, y, z] == player for x in range(3)):
                return True
        for x in range(3):
            if all(board[x, y, z] == player for y in range(3)):
                return True
    
    # Depth-wise columns (z varying, x,y fixed)
    for x in range(3):
        for y in range(3):
            if all(board[x, y, z] == player for z in range(3)):
                return True
    
    # Diagonals in each 3x3 slice (xy planes)
    for z in range(3):
        # Main diagonal in xy-plane
        if all(board[i, i, z] == player for i in range(3)):
            return True
        # Anti-diagonal in xy-plane
        if all(board[i, 2-i, z] == player for i in range(3)):
            return True
    
    # Diagonals in xz planes
    for y in range(3):
        # Main diagonal in xz-plane
        if all(board[i, y, i] == player for i in range(3)):
            return True
        # Anti-diagonal in xz-plane
        if all(board[i, y, 2-i] == player for i in range(3)):
            return True
    
    # Diagonals in yz planes
    for x in range(3):
        # Main diagonal in yz-plane
        if all(board[x, i, i] == player for i in range(3)):
            return True
        # Anti-diagonal in yz-plane
        if all(board[x, i, 2-i] == player for i in range(3)):
            return True
    
    # 4 Body diagonals through the center
    # Main space diagonal
    if all(board[i, i, i] == player for i in range(3)):
        return True
    # Other space diagonals
    if all(board[i, i, 2-i] == player for i in range(3)):
        return True
    if all(board[i, 2-i, i] == player for i in range(3)):
        return True
    if all(board[i, 2-i, 2-i] == player for i in range(3)):
        return True
    
    return False
