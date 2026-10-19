
import random
import numpy as np
from collections import defaultdict

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    n = board.shape[0]

    # Find all unknown cells (0)
    unknown_cells = np.argwhere(board == 0)

    # If no unknown cells left, return any cell (shouldn't happen in valid game)
    if len(unknown_cells) == 0:
        return (0, 0)

    # Get all hit cells (1)
    hit_cells = np.argwhere(board == 1)

    # If we have no hits yet, just pick a random unknown cell
    if len(hit_cells) == 0:
        return tuple(unknown_cells[random.randint(0, len(unknown_cells)-1)])

    # Create a list of potential targets near hits
    potential_targets = []

    # For each hit, consider its neighbors and nearby cells
    for hit in hit_cells:
        row, col = hit
        # Check all 8 surrounding cells
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue  # skip the hit cell itself
                r, c = row + dr, col + dc
                if 0 <= r < n and 0 <= c < n and board[r, c] == 0:
                    potential_targets.append((r, c))

    # If we have potential targets near hits, prioritize them
    if potential_targets:
        # Sort by distance to nearest hit (closest first)
        potential_targets.sort(key=lambda x: min(
            np.linalg.norm(np.array(x) - hit, axis=1)
            for hit in hit_cells
        ))
        return potential_targets[0]

    # If no potential targets near hits (unlikely), fall back to random
    return tuple(unknown_cells[random.randint(0, len(unknown_cells)-1)])
