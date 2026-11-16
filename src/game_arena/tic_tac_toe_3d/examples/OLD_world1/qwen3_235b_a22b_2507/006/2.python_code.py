
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Basic 3D Tic Tac Toe policy that uses a minimax-inspired strategy with heuristics.
    Prioritizes winning moves, then blocking opponent wins, then center positions.
    """
    board_array = np.array(board)
    n = 3
    
    # Find all empty cells
    empty_cells = []
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if board_array[i, j, k] == 0:
                    empty_cells.append((i, j, k))
    
    if not empty_cells:
        return (0, 0, 0)  # Should not happen in valid game
    
    # Check for winning move
    for cell in empty_cells:
        if would_win(cell, board_array, 1):
            return cell
    
    # Check for blocking opponent's winning move
    for cell in empty_cells:
        if would_win(cell, board_array, -1):
            return cell
    
    # Prefer center positions
    center_priority = []
    for cell in empty_cells:
        # Distance to center (1,1,1) - closer is better
        dist = sum(abs(cell[i] - 1) for i in range(3))
        center_priority.append((dist, cell))
    
    # Sort by distance to center (lower is better)
    center_priority.sort()
    
    # Return the centermost available position
    return center_priority[0][1]

def would_win(cell: Tuple[int, int, int], board: np.ndarray, player: int) -> bool:
    """Check if placing player's mark at cell would result in a win."""
    i, j, k = cell
    board_copy = board.copy()
    board_copy[i, j, k] = player
    
    n = 3
    # Check all possible lines through (i,j,k)
    for di in range(-1, 2):
        for dj in range(-1, 2):
            for dk in range(-1, 2):
                if di == 0 and dj == 0 and dk == 0:
                    continue
                
                # Count consecutive marks in this direction and its opposite
                count = 1  # Start with the placed mark
                # Forward direction
                ni, nj, nk = i + di, j + dj, k + dk
                while 0 <= ni < n and 0 <= nj < n and 0 <= nk < n:
                    if board_copy[ni, nj, nk] == player:
                        count += 1
                    else:
                        break
                    ni, nj, nk = ni + di, nj + dj, nk + dk
                
                # Backward direction
                ni, nj, nk = i - di, j - dj, k - dk
                while 0 <= ni < n and 0 <= nj < n and 0 <= nk < n:
                    if board_copy[ni, nj, nk] == player:
                        count += 1
                    else:
                        break
                    ni, nj, nk = ni - di, nj - dj, nk - dk
                
                if count >= n:
                    return True
    
    return False
