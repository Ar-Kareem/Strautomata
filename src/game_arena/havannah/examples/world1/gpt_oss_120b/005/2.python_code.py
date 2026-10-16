
import random
from collections import deque
from typing import List, Tuple

# ----------------------------------------------------------------------
# Helper functions for the hex‑grid neighbourhood
# ----------------------------------------------------------------------
NEIGHBOURS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]

def neighbours(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    r, c = pos
    return [(r + dr, c + dc) for dr, dc in NEIGHBOURS]

def inside_board(pos: Tuple[int, int]) -> bool:
    r, c = pos
    return 0 <= r < 15 and 0 <= c < 15

# ----------------------------------------------------------------------
# Connected components for a set of stones
# ----------------------------------------------------------------------
def components(stones: set) -> List[set]:
    """Return a list of components, each component is a set of positions."""
    seen = set()
    comps = []
    for s in stones:
        if s in seen:
            continue
        comp = set()
        q = deque([s])
        seen.add(s)
        while q:
            cur = q.popleft()
            comp.add(cur)
            for nb in neighbours(cur):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
        comps.append(comp)
    return comps

def component_info(comp: set):
    """Return (corner_set, edge_set) for a component."""
    corners = {(0, 0), (0, 14), (14, 0), (14, 14)}
    corner_hits = set()
    edge_hits = set()           # values: 'top', 'bottom', 'left', 'right'
    for (r, c) in comp:
        if (r, c) in corners:
            corner_hits.add((r, c))
        else:
            if r == 0:
                edge_hits.add('top')
            if r == 14:
                edge_hits.add('bottom')
            if c == 0:
                edge_hits.add('left')
            if c == 14:
                edge_hits.add('right')
    return corner_hits, edge_hits

# ----------------------------------------------------------------------
# Main policy function
# ----------------------------------------------------------------------
def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           valid_mask) -> Tuple[int, int]:
    """
    Return a legal move (row, col) for player 0.
    `me`      – list of my stones,
    `opp`     – list of opponent stones,
    `valid_mask` – 2D bool array, True == playable cell.
    """

    # Convert to sets for fast lookup
    my_set = set(me)
    opp_set = set(opp)
    occupied = my_set | opp_set

    # Pre‑compute my components and their meta‑information
    my_comps = components(my_set)
    comp_corner = {}
    comp_edge   = {}
    for idx, comp in enumerate(my_comps):
        corners, edges = component_info(comp)
        comp_corner[idx] = corners
        comp_edge[idx]   = edges

    # Helper to find which component(s) a cell would join
    def joining_components(cell):
        joins = []
        for idx, comp in enumerate(my_comps):
            if any(nb in comp for nb in neighbours(cell)):
                joins.append(idx)
        return joins

    # Scoring loop
    best_score = -1
    best_moves = []

    corners = {(0, 0), (0, 14), (14, 0), (14, 14)}

    for r in range(15):
        for c in range(15):
            if not valid_mask[r][c]:
                continue
            if (r, c) in occupied:
                continue

            cell = (r, c)

            # ---- adjacency to my stones
            adj_my = sum(1 for nb in neighbours(cell) if nb in my_set)

            # ---- adjacency to opponent stones (tiny block incentive)
            adj_opp = sum(1 for nb in neighbours(cell) if nb in opp_set)

            # ---- corner / edge bonuses
            corner_bonus = 5 if cell in corners else 0
            edge_bonus = 0
            if (r == 0 or r == 14 or c == 0 or c == 14) and cell not in corners:
                edge_bonus = 3

            # ---- merging different components ?
            joins = joining_components(cell)
            merge_bonus = 2 if len(joins) >= 2 else 0

            # ---- simulate move to see if we would win immediately
            # temporarily add the stone to the proper component(s)
            # Build a new set and recompute the component that contains the cell
            simulated = my_set | {cell}
            new_comps = components(simulated)
            win_bridge = 0
            win_fork   = 0
            for comp in new_comps:
                corners_here, edges_here = component_info(comp)
                if len(corners_here) >= 2:          # bridge condition
                    win_bridge = 100
                if len(edges_here) >= 3:            # fork condition
                    win_fork = 80

            score = (adj_my * 4) + (adj_opp * 1) + corner_bonus + edge_bonus + \
                    merge_bonus + win_bridge + win_fork

            if score > best_score:
                best_score = score
                best_moves = [cell]
            elif score == best_score:
                best_moves.append(cell)

    # If somehow we found no move (should not happen), pick the first legal one
    if not best_moves:
        for r in range(15):
            for c in range(15):
                if valid_mask[r][c] and (r, c) not in occupied:
                    return (r, c)

    # Choose randomly among equally good moves
    return random.choice(best_moves)
