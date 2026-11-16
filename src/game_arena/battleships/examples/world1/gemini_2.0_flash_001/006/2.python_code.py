
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A Battleship policy that combines hunting and targeting strategies.
    """
    board_np = np.array(board)
    # 1. Prioritize targeting adjacent to known hits
    hit_cells = np.argwhere(board_np == 1)
    if len(hit_cells) > 0:
        for row, col in hit_cells:
            adjacent_moves = [(row - 1, col), (row + 1, col), (row, col - 1), (row, col + 1)]
            for r, c in adjacent_moves:
                if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
                    return (r, c)

    # 2. Hunting Phase (Checkerboard pattern)
    for r in range(10):
        for c in range(10):
            if (r + c) % 2 == 0 and board[r][c] == 0:
                return (r, c)

    # 3. Last Resort: Find Any Remaining Unknown Cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)

    # If no valid move is found (which should never happen if the board is valid), return (0, 0) as a default.
    return (0, 0)
