
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next legal move (row, col) on a 10×10 Battleship board.
    The board contains:
        0 = unknown cell
       -1 = miss
        1 = hit
    The move must be an unknown cell.
    """
    # Convert to a NumPy array for fast slicing and masking
    b = np.array(board, dtype=int)

    # Count of legal placements covering each cell
    counts = np.zeros((10, 10), dtype=int)

    ship_lengths = [5, 4, 3, 3, 2]          # lengths of the opponent's fleet

    # Helper to increment counts for a valid placement
    def add_counts_orientation(orient, length, cells):
        """increment counts for a valid placement covering `cells` (list of (r,c))."""
        for r, c in cells:
            if b[r, c] == 0:                # only unknown cells get a score
                counts[r, c] += 1

    # Horizontal placements
    for L in ship_lengths:
        max_start = 10 - L
        for row in range(10):
            for start_col in range(max_start):
                segment = b[row, start_col:start_col + L]
                if np.any(segment == -1):
                    continue                # placement touches a miss → illegal
                # Cells in this placement that are still unknown
                unknown_cells = [(row, col) for col in range(start_col, start_col + L)
                                 if b[row, col] == 0]
                add_counts_orientation('H', L, unknown_cells)

    # Vertical placements
    for L in ship_lengths:
        max_start = 10 - L
        for col in range(10):
            for start_row in range(max_start):
                segment = b[start_row:start_row + L, col]
                if np.any(segment == -1):
                    continue                # placement touches a miss → illegal
                unknown_cells = [(row, col) for row in range(start_row, start_row + L)
                                 if b[row, col] == 0]
                add_counts_orientation('V', L, unknown_cells)

    # Find all unknown cells that have at least one possible placement
    possible = (b == 0) & (counts > 0)
    if not possible.any():
        # Very unlikely – fallback to a random unknown cell
        unknown_rows = [r for r in range(10) if unknown_cells.any()]
        unknown_cols = [c for c in range(10) if any(b[r, c] == 0 for r in range(10))]
        row = random.choice([r for r in unknown_rows if any(b[r, c] == 0 for c in unknown_cols)])
        col = random.choice([c for c in unknown_cols if b[row, c] == 0])
        return row, col

    # Extract candidate positions
    candidates = np.argwhere(possible)               # shape (n, 2)
    scores = counts[candidates]                     # scores for those cells
    max_score = scores.max()
    best_candidates = candidates[scores == max_score]

    # Randomly break ties
    chosen = random.choice(best_candidates)
    return int(chosen[0]), int(chosen[1])
