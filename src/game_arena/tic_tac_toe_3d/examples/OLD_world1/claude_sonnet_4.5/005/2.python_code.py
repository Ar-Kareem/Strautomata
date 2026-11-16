
import numpy as np
from typing import Optional

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    3D Tic Tac Toe policy for a 3x3x3 board.
    Returns the best move as (z, y, x) coordinates.
    """
    board_array = np.array(board)
    n = len(board)
    
    # First check if we can win in one move
    move = find_winning_move(board_array, 1)
    if move is not None:
        return move
    
    # Then block opponent's winning move
    move = find_winning_move(board_array, -1)
    if move is not None:
        return move
    
    # Take center if available
    center = n // 2
    if board_array[center, center, center] == 0:
        return (center, center, center)
    
    # Take corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for corner in corners:
        if board_array[corner] == 0:
            return corner
    
    # Take any available move
    empty_cells = np.argwhere(board_array == 0)
    if len(empty_cells) > 0:
        return tuple(empty_cells[0])
    
    return (0, 0, 0)  # Fallback (should never happen in valid game)


def find_winning_move(board: np.ndarray, player: int) -> Optional[tuple[int, int, int]]:
    """
    Find a move that would result in a win for the given player.
    Returns the coordinates of the winning move, or None if no such move exists.
    """
    n = board.shape[0]
    
    # Check all possible lines in 3D tic-tac-toe
    lines = get_all_lines(n)
    
    for line in lines:
        cells = [board[pos] for pos in line]
        if cells.count(player) == n - 1 and cells.count(0) == 1:
            # Found a line with n-1 of our pieces and 1 empty
            for pos in line:
                if board[pos] == 0:
                    return pos
    
    return None


def get_all_lines(n: int) -> list[list[tuple[int, int, int]]]:
    """
    Generate all winning lines in an nxnxn 3D tic-tac-toe board.
    """
    lines = []
    
    # Lines parallel to axes (rows, columns, pillars)
    for i in range(n):
        for j in range(n):
            # Lines parallel to x-axis
            lines.append([(i, j, k) for k in range(n)])
            # Lines parallel to y-axis
            lines.append([(i, k, j) for k in range(n)])
            # Lines parallel to z-axis
            lines.append([(k, i, j) for k in range(n)])
    
    # Diagonal lines within planes
    for i in range(n):
        # xy-plane diagonals at each z
        lines.append([(i, j, j) for j in range(n)])
        lines.append([(i, j, n-1-j) for j in range(n)])
        # xz-plane diagonals at each y
        lines.append([(j, i, j) for j in range(n)])
        lines.append([(j, i, n-1-j) for j in range(n)])
        # yz-plane diagonals at each x
        lines.append([(j, j, i) for j in range(n)])
        lines.append([(j, n-1-j, i) for j in range(n)])
    
    # 3D space diagonals (4 total)
    lines.append([(i, i, i) for i in range(n)])
    lines.append([(i, i, n-1-i) for i in range(n)])
    lines.append([(i, n-1-i, i) for i in range(n)])
    lines.append([(n-1-i, i, i) for i in range(n)])
    
    return lines
