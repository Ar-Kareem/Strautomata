
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Returns the next move for 3x3x3 3D Tic Tac Toe.
    Uses a heuristic-based approach with move ordering and threat detection.
    """
    board = np.array(board)
    n = 3
    
    # Find all empty cells
    empty_cells = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i, j, k] == 0:
                    empty_cells.append((i, j, k))
    
    if not empty_cells:
        return (0, 0, 0)  # Should not happen in valid game
    
    # Check for winning move (play as agent)
    for cell in empty_cells:
        board_copy = board.copy()
        board_copy[cell] = 1
        if check_win(board_copy, 1):
            return cell
    
    # Check for blocking opponent's winning move
    for cell in empty_cells:
        board_copy = board.copy()
        board_copy[cell] = -1
        if check_win(board_copy, -1):
            return cell
    
    # Prefer center positions
    center_priority = []
    for cell in empty_cells:
        # Distance to center (1,1,1) - closer is better
        dist = sum(abs(cell[i] - 1) for i in range(3))
        center_priority.append((dist, cell))
    
    # Sort by distance to center (closer first)
    center_priority.sort()
    
    # Among center-preferred moves, check for creating forks (multiple threats)
    for _, cell in center_priority:
        board_copy = board.copy()
        board_copy[cell] = 1
        if count_winning_opportunities(board_copy, 1) >= 2:
            return cell
    
    # Return the cell closest to center
    return center_priority[0][1]

def check_win(board: np.ndarray, player: int) -> bool:
    """Check if the given player has won."""
    n = 3
    
    # Check all lines: rows, columns, pillars, and diagonals
    for i in range(n):
        for j in range(n):
            # Check rows (fixed y,z vary x)
            if all(board[x, j, i] == player for x in range(n)):
                return True
            # Check columns (fixed x,z vary y)
            if all(board[i, y, j] == player for y in range(n)):
                return True
            # Check pillars (fixed x,y vary z)
            if all(board[i, j, z] == player for z in range(n)):
                return True
    
    # Check face diagonals on each face
    for k in range(n):  # For each layer in z
        if all(board[i, i, k] == player for i in range(n)):
            return True
        if all(board[i, n-1-i, k] == player for i in range(n)):
            return True
    
    for k in range(n):  # For each layer in y
        if all(board[i, k, i] == player for i in range(n)):
            return True
        if all(board[i, k, n-1-i] == player for i in range(n)):
            return True
    
    for k in range(n):  # For each layer in x
        if all(board[k, i, i] == player for i in range(n)):
            return True
        if all(board[k, i, n-1-i] == player for i in range(n)):
            return True
    
    # Check 3D diagonals
    if all(board[i, i, i] == player for i in range(n)):
        return True
    if all(board[i, i, n-1-i] == player for i in range(n)):
        return True
    if all(board[i, n-1-i, i] == player for i in range(n)):
        return True
    if all(board[i, n-1-i, n-1-i] == player for i in range(n)):
        return True
    
    return False

def count_winning_opportunities(board: np.ndarray, player: int) -> int:
    """Count how many winning moves are available for player."""
    count = 0
    n = 3
    
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board[i, j, k] == 0:
                    board_copy = board.copy()
                    board_copy[i, j, k] = player
                    if check_win(board_copy, player):
                        count += 1
    
    return count
