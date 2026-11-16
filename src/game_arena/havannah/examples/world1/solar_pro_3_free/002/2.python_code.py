
import random
from typing import List, Tuple

# Hexagonal neighbourhood offsets.
# Odd‑row (row % 2 == 1) and even‑row (row % 2 == 0) have slightly different neighbour patterns.
DIRS: List[Tuple[int, int]] = [
    # even rows
    (-1, -1), (-1, 0), (0, -1), (0, 1), (1, -1), (1, 0),
    # odd rows
    (-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, 1),
]

def is_edge(cell: Tuple[int, int]) -> bool:
    """Return True if a cell touches the outer border of the 15×15 board."""
    r, c = cell
    return r == 0 or r == 14 or c == 0 or c == 14

def heuristic_score(cell: Tuple[int, int],
                    me: List[Tuple[int, int]],
                    opp: List[Tuple[int, int]],
                    valid_mask: List[List[bool]]) -> int:
    """
    Compute a simple score for a candidate empty cell:
    * +my_adj : how many of the player’s stones would be adjacent after placing here.
    * -opp_adj: how many opponent stones would be adjacent.
    * +3*is_edge: extra incentive for being on the edge itself.
    * +2*edge_adj: extra incentive for touching edge cells as neighbours.
    """
    r, c = cell
    # quick validity test (if invalid just give a low score)
    if not valid_mask[r][c]:
        return -10

    # Convert to set for O(1) membership tests.
    my_set = set(me)
    opp_set = set(opp)

    my_adj = 0
    opp_adj = 0
    edge_adj = 0
    is_edge_self = is_edge(cell)

    # iterate through the six possible neighbours respecting the hex shape.
    for dr, dc in DIRS:
        nr = r + dr
        nc = c + dc
        # neighbour might be outside the board → ignore (edge detection later)
        if not (0 <= nr < 15 and 0 <= nc < 15):
            continue
        # own adjacency
        if (nr, nc) in my_set:
            my_adj += 1
        # opponent adjacency
        if (nr, nc) in opp_set:
            opp_adj += 1
        # edge adjacency of neighbour (if neighbour touches board edge)
        if is_edge((nr, nc)):
            edge_adj += 1

    # final score
    score = my_adj - opp_adj + 3 * is_edge_self + 2 * edge_adj
    return score

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           valid_mask: List[List[bool]]) -> Tuple[int, int]:
    """
    Return the next move for the player (player‑0). The move must be a legal
    empty cell marked True in `valid_mask`. The function runs in < 1 s.
    """
    # Convert the opponent list for quick lookup.
    opp_set = set(opp)
    # Gather all candidate cells.
    candidates = [(r, c) for r in range(15)
                     for c in range(15)
                     if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp_set]

    # Edge‑early‑exit: if there are no legal moves we fall back to the first True cell
    # (this should never happen in a legal Havannah position).
    if not candidates:
        # Find any True cell (ignoring ownership – shouldn't be needed)
        for r in range(15):
            for c in range(15):
                if valid_mask[r][c]:
                    return r, c

    # Score candidates.
    scored = [(cell, heuristic_score(cell, me, opp_set, valid_mask)) for cell in candidates]

    # Pick the best score.
    best_score = max(s for _, s in scored)
    best_candidates = [cell for cell, s in scored if s == best_score]

    # Randomised tie‑break – always a legal move.
    chosen = random.choice(best_candidates)
    return chosen[0], chosen[1]
