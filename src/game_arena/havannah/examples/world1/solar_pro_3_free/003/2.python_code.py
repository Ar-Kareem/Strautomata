
import numpy as np
from typing import List, Tuple

# Board constants
N = 15

# Hexagonal neighbour offsets depending on row parity (odd‑r layout)
NEIGHBOR_OFFSETS = {
    0: [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0)],
    1: [(0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)],
}


def get_neighbors(row: int, col: int) -> List[Tuple[int, int]]:
    """Return the six possible hex neighbours of (row, col)."""
    return [
        (row + dr, col + dc)
        for dr, dc in NEIGHBOR_OFFSETS[row % 2]
        if 0 <= row + dr < N and 0 <= col + dc < N
    ]


def neighbor_degree(row: int, col: int, valid_mask: np.ndarray) -> int:
    """Number of playable neighbours (inside `valid_mask`) for a cell."""
    count = 0
    for dr, dc in NEIGHBOR_OFFSETS[row % 2]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < N and 0 <= nc < N and valid_mask[nr, nc]:
            count += 1
    return count


def compute_score(
    r: int,
    c: int,
    me: set,
    opp: set,
    valid_mask: np.ndarray,
) -> int:
    """
    Heuristic score for a candidate move (r,c).

    Returns a positive integer that captures:
      * number of own neighbours (+1 each)
      * number of opponent neighbours (‑1 each)
      * bonus for edge placement (degree ≤ 3)
      * bonus for corner (degree ≤ 2) –‑ mainly for threat handling
      * huge bonus for an immediate ring (six own neighbours)
    """
    # raw connectivity
    score = 0
    for nb in get_neighbors(r, c):
        if nb in me:
            score += 1   # own stone next to us
        elif nb in opp:
            score -= 1  # opponent stone next to us

    # corner/edge bonuses based on degree of the empty cell
    deg = neighbor_degree(r, c, valid_mask)
    if deg <= 2:            # true corner
        score += 100
    elif deg <= 3:          # edge cell
        score += 30

    # ring bonus (surround an empty cell)
    if len(get_neighbors(r, c)) == 6 and all(nb in me for nb in get_neighbors(r, c)):
        score += 1000

    return score


def policy(me: List[Tuple[int, int]],
          opp: List[Tuple[int, int]],
          valid_mask: np.ndarray) -> Tuple[int, int]:
    """
    Return the next move for Havannah as a tuple (row, col).
    Implements a greedy heuristic that blocks opponent corners,
    rewards own connectivity and immediate win chances.
    """
    # Convert to sets for O(1) membership tests
    me_set = set(me)
    opp_set = set(opp)

    # Determine all legal empty cells (playable and unoccupied)
    empty_cells = []
    for row in range(N):
        for col in range(N):
            if valid_mask[row, col] and (row, col) not in me_set and (row, col) not in opp_set:
                empty_cells.append((row, col))

    # Find true corners (cells with ≤ 2 playable neighbours)
    corners = {cell for cell in empty_cells if neighbor_degree(*cell, valid_mask) <= 2}

    # Threat corners: empty corners that have an opponent neighbour
    threat_corners = [
        cell for cell in corners
        if any(nb in opp_set for nb in get_neighbors(*cell))
    ]

    # --------------------------------------------------------------------
    # 1️⃣  Block any opponent‑adjacent corner (threat) immediately
    # --------------------------------------------------------------------
    if threat_corners:
        # Compute scores for those threat corners
        scored_threats = [
            (compute_score(*cell, me_set, opp_set, valid_mask), row, col)
            for (row, col) in threat_corners
        ]
        # Highest score (first) is the best block
        scored_threats.sort(key=lambda x: (-x[0], x[1], x[2]))
        return scored_threats[0][1], scored_threats[0][2]

    # --------------------------------------------------------------------
    # 2️⃣  Choose the best non‑threat move among all legal cells
    # --------------------------------------------------------------------
    # Score each empty cell
    scored_moves = [
        (compute_score(*cell, me_set, opp_set, valid_mask), row, col)
        for (row, col) in empty_cells
    ]
    # Prefer moves that increase our connectivity and build a ring
    scored_moves.sort(key=lambda x: (-x[0], x[1], x[2]))
    return scored_moves[0][1], scored_moves[0][2]
