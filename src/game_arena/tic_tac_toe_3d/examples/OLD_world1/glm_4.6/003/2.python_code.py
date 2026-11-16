
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Determine the next move for a 3x3x3 3D Tic Tac Toe game.

    Args:
        board: A 3x3x3 list of lists containing 0 (empty), 1 (you), and -1 (opponent).

    Returns:
        A tuple of three integers (x, y, z) indicating the next move.
    """
    n = 3
    board_np = np.array(board)
    
    # Check if the board is empty (first move)
    if np.all(board_np == 0):
        return (1, 1, 1)  # Center is a strong first move
    
    # Priority 1: Win if possible
    move = find_winning_move(board_np, 1)
    if move is not None:
        return move
    
    # Priority 2: Block opponent's win
    move = find_winning_move(board_np, -1)
    if move is not None:
        return move
    
    # Priority 3: Take center if available
    if board_np[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Priority 4: Take a corner
    corners = [(0,0,0), (0,0,2), (0,2,0), (0,2,2),
               (2,0,0), (2,0,2), (2,2,0), (2,2,2)]
    for corner in corners:
        if board_np[corner] == 0:
            return corner
    
    # Priority 5: Take an edge
    edges = [(0,1,0), (0,1,2), (0,0,1), (0,2,1),
             (1,0,0), (1,0,2), (1,2,0), (1,2,2),
             (2,1,0), (2,1,2), (2,0,1), (2,2,1)]
    for edge in edges:
        if board_np[edge] == 0:
            return edge
    
    # If no strategic move found, take first available
    empty_cells = np.argwhere(board_np == 0)
    if len(empty_cells) > 0:
        return tuple(empty_cells[0])
    
    # Shouldn't happen if game is not over
    return (0, 0, 0)

def find_winning_move(board: np.ndarray, player: int) -> Tuple[int, int, int]:
    """
    Find a move that would make the player win immediately.
    
    Args:
        board: 3x3x3 numpy array
        player: 1 (you) or -1 (opponent)
    
    Returns:
        Tuple of coordinates if winning move exists, None otherwise
    """
    n = 3
    target = player * 2  # Two of our marks and one empty
    
    # Check all possible lines (rows, columns, pillars, diagonals)
    lines = []
    
    # Rows in each layer
    for z in range(n):
        for y in range(n):
            line = [(x, y, z) for x in range(n)]
            lines.append(line)
    
    # Columns in each layer
    for z in range(n):
        for x in range(n):
            line = [(x, y, z) for y in range(n)]
            lines.append(line)
    
    # Pillars (vertical lines)
    for x in range(n):
        for y in range(n):
            line = [(x, y, z) for z in range(n)]
            lines.append(line)
    
    # Face diagonals
    for z in range(n):
        # Top-left to bottom-right
        line = [(i, i, z) for i in range(n)]
        lines.append(line)
        # Top-right to bottom-left
        line = [(i, n-1-i, z) for i in range(n)]
        lines.append(line)
    
    for x in range(n):
        # Top-left to bottom-right (y-z plane)
        line = [(x, i, i) for i in range(n)]
        lines.append(line)
        # Top-right to bottom-left (y-z plane)
        line = [(x, i, n-1-i) for i in range(n)]
        lines.append(line)
    
    for y in range(n):
        # Top-left to bottom-right (x-z plane)
        line = [(i, y, i) for i in range(n)]
        lines.append(line)
        # Top-right to bottom-left (x-z plane)
        line = [(i, y, n-1-i) for i in range(n)]
        lines.append(line)
    
    # Main space diagonals
    line = [(i, i, i) for i in range(n)]
    lines.append(line)
    line = [(i, i, n-1-i) for i in range(n)]
    lines.append(line)
    line = [(i, n-1-i, i) for i in range(n)]
    lines.append(line)
    line = [(i, n-1-i, n-1-i) for i in range(n)]
    lines.append(line)
    
    # Check each line for a winning opportunity
    for line in lines:
        cells = [board[pos] for pos in line]
        if sum(cells) == target and 0 in cells:
            empty_idx = cells.index(0)
            return line[empty_idx]
    
    return None
