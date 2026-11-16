
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    rows, cols = board_np.shape

    # Check if we are in the initial random phase (first 20 moves)
    if np.sum(board_np == 0) > 80:  # More than 80 unknown cells (10x10 - 20 = 80)
        # Random move: pick a cell with 0
        available_cells = np.argwhere(board_np == 0)
        chosen_cell = np.random.choice(available_cells.shape[0])
        return tuple(available_cells[chosen_cell])
    else:
        # Find all hits (1) and misses (-1)
        hits = np.argwhere(board_np == 1)
        misses = np.argwhere(board_np == -1)

        # If no hits, pick the cell with highest probability (random if all equal)
        if hits.size == 0:
            return targeted_probability_attack(board_np)

        # Check if any ship is partially sunk (adjacent cells with hits)
        adjacent_unknowns = []
        for (r, c) in hits:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board_np[nr, nc] == 0:
                    adjacent_unknowns.append((nr, nc))

        # If adjacent unknowns exist, pick one randomly (prioritize sinking)
        if adjacent_unknowns:
            return np.random.choice(adjacent_unknowns)

        # Otherwise, pick the cell with highest probability
        return targeted_probability_attack(board_np)

def targeted_probability_attack(board: np.ndarray) -> tuple[int, int]:
    rows, cols = board.shape
    probability_map = np.zeros((rows, cols))

    # For each hit, increase probability of adjacent cells
    hits = np.argwhere(board == 1)
    for (r, c) in hits:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                probability_map[nr, nc] += 1

    # For each miss, decrease probability of adjacent cells
    misses = np.argwhere(board == -1)
    for (r, c) in misses:
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                probability_map[nr, nc] -= 1

    # Normalize probabilities (avoid negative values)
    probability_map = np.clip(probability_map, 0, None)

    # Get all unknown cells (0) and their probabilities
    unknown_cells = np.argwhere(board == 0)
    if unknown_cells.size == 0:
        # Edge case: no unknown cells left (should not happen in normal game)
        return (0, 0)  # Invalid, but forced by constraints

    # Assign probabilities to unknown cells (weighted by distance from hits/misses)
    for (r, c) in unknown_cells:
        # Distance from nearest hit (inverse decay)
        if hits.size > 0:
            dist_to_hits = np.min(np.linalg.norm(hits - [r, c], axis=1))
            probability_map[r, c] += 1 / (1 + dist_to_hits)

        # Distance from nearest miss (penalize)
        if misses.size > 0:
            dist_to_misses = np.min(np.linalg.norm(misses - [r, c], axis=1))
            probability_map[r, c] -= 1 / (1 + dist_to_misses)

    # Normalize probabilities to sum to 1 (for random selection)
    total_prob = np.sum(probability_map[board == 0])
    if total_prob > 0:
        probability_map[board == 0] /= total_prob

    # Pick the cell with highest probability
    best_cell = np.argwhere(probability_map == np.max(probability_map))
    return tuple(best_cell[np.random.choice(best_cell.shape[0])])
