
#!/usr/bin/env python3
"""
Battleship targeting policy.

Implements a simple probability‑heat‑map shooter:
  * Enumerates every ship placement consistent with known misses.
  * Counts how many placements cover each cell.
  * Fires at the unknown cell with the highest count (ties broken randomly).

The function `policy(board)` conforms to the required signature.
"""

from __future__ import annotations

import random
from typing import List, Tuple

import numpy as np

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------
SHIP_LENGTHS: List[int] = [5, 4, 3, 3, 2]  # Standard fleet
GRID_SIZE: int = 10  # 10x10 board


def _enumerate_valid_placements(
    knowledge: np.ndarray, length: int
) -> List[np.ndarray]:
    """
    Return a list of placement masks (10x10 bool arrays) for a ship of the given
    length that do not intersect any known miss (-1) on the board.
    """
    placements: List[np.ndarray] = []

    # Horizontal placements
    for r in range(GRID_SIZE):
        for c in range(GRID_SIZE - length + 1):
            # slice covering the ship
            segment = knowledge[r, c : c + length]
            # Placement is invalid if any cell is a miss
            if np.any(segment == -1):
                continue
            mask = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
            mask[r, c : c + length] = True
            placements.append(mask)

    # Vertical placements
    for c in range(GRID_SIZE):
        for r in range(GRID_SIZE - length + 1):
            segment = knowledge[r : r + length, c]
            if np.any(segment == -1):
                continue
            mask = np.zeros((GRID_SIZE, GRID_SIZE), dtype=bool)
            mask[r : r + length, c] = True
            placements.append(mask)

    return placements


def _build_heatmap(knowledge: np.ndarray) -> np.ndarray:
    """
    Construct a heat map where each cell contains the number of possible
    ship placements (over all remaining ships) that cover that cell.
    """
    heat = np.zeros((GRID_SIZE, GRID_SIZE), dtype=int)

    for length in SHIP_LENGTHS:
        for placement in _enumerate_valid_placements(knowledge, length):
            # Increment heat for every cell belonging to this placement
            heat[placement] += 1

    return heat


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Choose the next target cell.

    Parameters
    ----------
    board : list[list[int]]
        Current knowledge of opponent board:
            0  -> unknown (not yet fired)
           -1  -> miss
            1  -> hit

    Returns
    -------
    (row, col) : tuple[int, int]
        Coordinates of the chosen shot. Must satisfy board[row][col] == 0.
    """
    # Convert to a NumPy array for fast processing
    knowledge = np.array(board, dtype=int)

    # Build the probability heat map
    heat = _build_heatmap(knowledge)

    # Mask of cells we are allowed to fire at (still unknown)
    unknown_mask = knowledge == 0

    # If nothing is unknown (should not happen), raise an error
    if not np.any(unknown_mask):
        raise RuntimeError("No unknown cells left to fire at.")

    # Zero out heat values for non‑unknown cells to avoid picking them
    heat_filtered = np.where(unknown_mask, heat, -1)

    max_heat = heat_filtered.max()
    # Gather all coordinates that share the maximal heat value
    candidate_positions = np.argwhere(heat_filtered == max_heat)

    # Randomly pick one of the best candidates to avoid deterministic play
    chosen_idx = random.choice(range(len(candidate_positions)))
    row, col = map(int, candidate_positions[chosen_idx])

    return row, col


# ------------------------------------------------------------
# Optional: simple self‑test when run as a script
# ------------------------------------------------------------
if __name__ == "__main__":
    # Create an empty board (all unknown)
    empty_board = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    # Make a few dummy shots to see the policy respond
    test_board = [row[:] for row in empty_board]
    test_board[4][4] = -1  # miss
    test_board[7][2] = 1   # hit

    print("Chosen target:", policy(test_board))
