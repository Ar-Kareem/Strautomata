
import numpy as np
from typing import Optional

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    3D Tic Tac Toe policy for a 3x3x3 board.
    Returns the best move as (z, y, x) coordinates.
    """
    n = 3
    board_array = np.array(board)
    
    # First, check if we can win in one move
    win_move = find_winning_move(board_array, 1)
    if win_move is not None:
        return win_move
    
    # Second, block opponent's winning move
    block_move = find_winning_move(board_array, -1)
    if block_move is not None:
        return block_move
    
    # Third, try to take center if available
    if board_array[1, 1, 1] == 0:
        return (1, 1, 1)
    
    # Fourth, try corners
    corners = [
        (0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2),
        (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)
    ]
    for corner in corners:
        if board_array[corner] == 0:
            return corner
    
    # Fifth, take any available move
    for z in range(n):
        for y in range(n):
            for x in range(n):
                if board_array[z, y, x] == 0:
                    return (z, y, x)
    
    return (0, 0, 0)  # Fallback (should never reach here in valid game)


def find_winning_move(board: np.ndarray, player: int) -> Optional[tuple[int, int, int]]:
    """
    Find a move that would create three in a row for the given player.
    Returns the coordinates of the winning move, or None if no such move exists.
    """
    n = 3
    
    # Check all possible lines in 3D tic-tac-toe
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
    Generate all possible winning lines in a 3x3x3 board.
    """
    lines = []
    
    # Lines parallel to axes (27 lines total: 9 per axis)
    for z in range(n):
        for y in range(n):
            lines.append([(z, y, x) for x in range(n)])  # Along x-axis
        for x in range(n):
            lines.append([(z, y, x) for y in range(n)])  # Along y-axis
    
    for y in range(n):
        for x in range(n):
            lines.append([(z, y, x) for z in range(n)])  # Along z-axis
    
    # Diagonals in planes parallel to xy (6 lines)
    for z in range(n):
        lines.append([(z, i, i) for i in range(n)])  # Main diagonal
        lines.append([(z, i, n-1-i) for i in range(n)])  # Anti-diagonal
    
    # Diagonals in planes parallel to xz (6 lines)
    for y in range(n):
        lines.append([(i, y, i) for i in range(n)])  # Main diagonal
        lines.append([(i, y, n-1-i) for i in range(n)])  # Anti-diagonal
    
    # Diagonals in planes parallel to yz (6 lines)
    for x in range(n):
        lines.append([(i, i, x) for i in range(n)])  # Main diagonal
        lines.append([(i, n-1-i, x) for i in range(n)])  # Anti-diagonal
    
    # Space diagonals (4 lines - corner to opposite corner)
    lines.append([(i, i, i) for i in range(n)])  # Main space diagonal
    lines.append([(i, i, n-1-i) for i in range(n)])
    lines.append([(i, n-1-i, i) for i in range(n)])
    lines.append([(i, n-1-i, n-1-i) for i in range(n)])
    
    return lines
