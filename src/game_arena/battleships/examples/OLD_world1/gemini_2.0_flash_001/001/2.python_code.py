
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Implements a targeting policy for a Battleship-like game on a 10x10 grid.

    Args:
        board: A 10x10 list of lists representing the current knowledge of the opponent grid.
               0  → unknown cell (you have not fired here).
               -1 → miss (you fired here and hit water).
               1  → hit (you fired here and hit a ship cell).

    Returns:
        A tuple (row, col) with integers in the range 0-9, choosing a cell you have not previously fired at.
    """

    n = len(board)

    # Prioritize hitting adjacent cells to known hits
    for r in range(n):
        for c in range(n):
            if board[r][c] == 1:
                # Check adjacent cells
                adjacent_cells = [(r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)]
                possible_targets = []
                for row, col in adjacent_cells:
                    if 0 <= row < n and 0 <= col < n and board[row][col] == 0:
                        possible_targets.append((row, col))
                if possible_targets:
                    return random.choice(possible_targets)

    # If no adjacent hits, try a random unknown cell
    unknown_cells = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                unknown_cells.append((r, c))

    if unknown_cells:
        return random.choice(unknown_cells)
    else:
        # If no unknown cells, return a random cell (should not happen in a normal game)
        return (random.randint(0, n-1), random.randint(0, n-1))
