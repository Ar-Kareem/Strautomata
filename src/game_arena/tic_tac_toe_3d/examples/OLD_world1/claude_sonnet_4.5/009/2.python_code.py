
import numpy as np
from typing import Optional

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    Policy for 3x3x3 3D Tic Tac Toe.
    Returns the next move as (z, y, x) coordinates.
    """
    n = 3
    b = np.array(board)
    
    # Try to win immediately
    move = find_winning_move(b, 1)
    if move is not None:
        return move
    
    # Block opponent from winning
    move = find_winning_move(b, -1)
    if move is not None:
        return move
    
    # Take center if available
    if b[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Take corners (prioritize)
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for corner in corners:
        if b[corner] == 0:
            return corner
    
    # Take any available move
    empty_cells = np.argwhere(b == 0)
    if len(empty_cells) > 0:
        return tuple(empty_cells[0])
    
    return (0, 0, 0)  # Fallback (should not reach)


def find_winning_move(board: np.ndarray, player: int) -> Optional[tuple[int, int, int]]:
    """
    Find a move that wins for the given player.
    Returns (z, y, x) or None if no winning move exists.
    """
    n = 3
    
    # Generate all possible lines in 3D tic-tac-toe
    lines = get_all_lines(n)
    
    for line in lines:
        cells = [board[pos] for pos in line]
        
        # Check if this line has 2 of player's marks and 1 empty
        if cells.count(player) == 2 and cells.count(0) == 1:
            # Find the empty position
            for pos in line:
                if board[pos] == 0:
                    return pos
    
    return None


def get_all_lines(n: int) -> list[list[tuple[int, int, int]]]:
    """
    Generate all winning lines in a 3x3x3 board.
    """
    lines = []
    
    # Lines parallel to axes
    for z in range(n):
        for y in range(n):
            # X-axis lines
            lines.append([(z, y, x) for x in range(n)])
        for x in range(n):
            # Y-axis lines
            lines.append([(z, y, x) for y in range(n)])
    
    for y in range(n):
        for x in range(n):
            # Z-axis lines
            lines.append([(z, y, x) for z in range(n)])
    
    # Diagonals in XY planes
    for z in range(n):
        lines.append([(z, i, i) for i in range(n)])
        lines.append([(z, i, n-1-i) for i in range(n)])
    
    # Diagonals in XZ planes
    for y in range(n):
        lines.append([(i, y, i) for i in range(n)])
        lines.append([(i, y, n-1-i) for i in range(n)])
    
    # Diagonals in YZ planes
    for x in range(n):
        lines.append([(i, i, x) for i in range(n)])
        lines.append([(i, n-1-i, x) for i in range(n)])
    
    # 4 space diagonals (corner to corner)
    lines.append([(i, i, i) for i in range(n)])
    lines.append([(i, i, n-1-i) for i in range(n)])
    lines.append([(i, n-1-i, i) for i in range(n)])
    lines.append([(i, n-1-i, n-1-i) for i in range(n)])
    
    return lines
