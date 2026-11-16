
import random
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    n = board.shape[0]

    # Find all unknown cells (0)
    unknown_cells = np.argwhere(board == 0)

    if len(unknown_cells) == 0:
        # All cells are known, return any miss (shouldn't happen in normal play)
        return (0, 0)

    # Get all hit cells (1)
    hit_cells = np.argwhere(board == 1)

    # If we have no hits yet, just pick a random unknown cell
    if len(hit_cells) == 0:
        return tuple(unknown_cells[random.randint(0, len(unknown_cells)-1)])

    # If we have hits, try to find adjacent cells to hits
    # We'll prioritize cells adjacent to hits to try to find ship lengths
    adjacent_cells = set()

    for cell in hit_cells:
        row, col = cell
        # Check all 8 surrounding cells
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue  # skip the cell itself
                nr, nc = row + dr, col + dc
                if 0 <= nr < n and 0 <= nc < n:
                    if board[nr, nc] == 0:  # only consider unknown cells
                        adjacent_cells.add((nr, nc))

    # Convert to list and filter out cells we've already considered
    adjacent_cells = list(adjacent_cells)
    random.shuffle(adjacent_cells)  # randomize to avoid predictable patterns

    # If we have adjacent cells, pick one randomly
    if adjacent_cells:
        return adjacent_cells[0]

    # Otherwise, pick a random unknown cell
    return tuple(unknown_cells[random.randint(0, len(unknown_cells)-1)])
