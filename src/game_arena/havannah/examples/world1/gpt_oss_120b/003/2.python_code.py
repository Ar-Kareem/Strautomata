
import numpy as np
from collections import deque
from typing import List, Tuple, Set

# neighbour offsets for the rectangular representation of a hex board
_NEIGHBOURS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < 15 and 0 <= c < 15

def _neighbours(r: int, c: int, valid_mask) -> List[Tuple[int, int]]:
    """Return list of neighbour coordinates that are inside the board and valid."""
    res = []
    for dr, dc in _NEIGHBOURS:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc) and valid_mask[nr][nc]:
            res.append((nr, nc))
    return res

def _degree(r: int, c: int, valid_mask) -> int:
    """Number of hex neighbours for a cell (used to detect corners / edges)."""
    return len(_neighbours(r, c, valid_mask))

def _components(me: Set[Tuple[int, int]], valid_mask) -> dict:
    """
    Return a mapping from cell -> component_id for all our stones.
    Component ids are integers starting from 0.
    """
    visited = set()
    comp_id = {}
    cur_id = 0

    for stone in me:
        if stone in visited:
            continue
        # BFS for this component
        q = deque([stone])
        visited.add(stone)
        comp_id[stone] = cur_id
        while q:
            r, c = q.popleft()
            for nr, nc in _neighbours(r, c, valid_mask):
                if (nr, nc) in me and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    comp_id[(nr, nc)] = cur_id
                    q.append((nr, nc))
        cur_id += 1
    return comp_id

def _empty_cells(me: Set[Tuple[int, int]],
                 opp: Set[Tuple[int, int]],
                 valid_mask) -> List[Tuple[int, int]]:
    empties = []
    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue
            if (r, c) in me or (r, c) in opp:
                continue
            empties.append((r, c))
    return empties

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           valid_mask) -> Tuple[int, int]:
    """
    Return a legal move (row, col) for the current player.
    The move is chosen using a connectivity‑centric heuristic.
    """
    # Convert to sets for O(1) membership tests
    me_set = set(me)
    opp_set = set(opp)

    # all playable empty cells
    empties = _empty_cells(me_set, opp_set, valid_mask)
    if not empties:                     # should never happen, but be safe
        raise RuntimeError("No legal moves available")

    # component information of our current stones
    comp_map = _components(me_set, valid_mask)

    # Pre‑compute corner cells (degree == 3) – they are the six board corners
    corner_cells = {(r, c) for r, c in empties if _degree(r, c, valid_mask) == 3}
    edge_cells   = {(r, c) for r, c in empties if _degree(r, c, valid_mask) == 4}

    best_score = -10**9
    best_moves = []

    for r, c in empties:
        nbrs = _neighbours(r, c, valid_mask)

        # count own neighbours
        nbr_me = sum(1 for (nr, nc) in nbrs if (nr, nc) in me_set)

        # determine which of our components are adjacent
        adj_comps = {comp_map[(nr, nc)] for (nr, nc) in nbrs
                     if (nr, nc) in me_set}

        merge_bonus = 5 if len(adj_comps) >= 2 else 0

        corner_bonus = 0
        if (r, c) in corner_cells:
            corner_bonus = 10
        elif (r, c) in edge_cells:
            corner_bonus = 2

        score = nbr_me + merge_bonus + corner_bonus

        # keep the best
        if score > best_score:
            best_score = score
            best_moves = [(r, c)]
        elif score == best_score:
            best_moves.append((r, c))

    # tie‑breaker: choose the move nearest to the centre (7,7)
    centre = (7, 7)
    def dist_to_center(cell):
        return abs(cell[0] - centre[0]) + abs(cell[1] - centre[1])

    best_move = min(best_moves, key=dist_to_center)
    return best_move
