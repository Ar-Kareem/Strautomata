
import numpy as np
from typing import List, Tuple, Dict, Set

# Hex adjacency offsets (pointy‑top orientation matching the example)
_HEX_NEIGHBORS: List[Tuple[int, int]] = [
    (-1, 0),   # up
    (1, 0),    # down
    (-1, -1),  # left‑down
    (0, -1),   # left‑up
    (-1, 1),   # right‑down
    (0, 1),    # right‑up
]

def _build_neighbors(N: int) -> Dict[Tuple[int, int], List[Tuple[int, int]]]:
    """Return a dict mapping each cell (r,c) to its 6‑hex neighbours inside the board."""
    neighbors: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}
    for r in range(N):
        for c in range(N):
            nbrs = []
            for dr, dc in _HEX_NEIGHBORS:
                nr = r + dr
                nc = c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    nbrs.append((nr, nc))
            neighbors[(r, c)] = nbrs
    return neighbors

# The six corner cells of a 15×15 hexagonal board
_CORNERS: List[Tuple[int, int]] = [
    (0, 0),      # top‑left
    (0, 14),     # top‑right
    (14, 0),     # bottom‑left
    (14, 14),    # bottom‑right
    (7, 0),      # left middle
    (7, 14),     # right middle
]

def _edge_cells(N: int, corners_set: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
    """All perimeter cells except the six corner cells."""
    edges = set()
    for r in range(N):
        for c in range(N):
            if (r == 0 or r == N - 1 or c == 0 or c == N - 1) and (r, c) not in corners_set:
                edges.add((r, c))
    return edges

def policy(me: List[Tuple[int, int]],
          opp: List[Tuple[int, int]],
          valid_mask) -> Tuple[int, int]:
    """
    Choose a legal move for Havannah on a 15×15 hex board.
    Parameters
    ----------
    me : list of (row, col) tuples
        Positions of player‑0 stones.
    opp : list of (row, col) tuples
        Positions of player‑1 stones.
    valid_mask : np.ndarray or list of lists
        Boolean 15×15 array; True on playable cells.
    Returns
    -------
    (row, col) : tuple of ints
        The chosen move coordinates.
    """
    # Convert mask to a numpy array for convenient indexing
    board_mask = np.asarray(valid_mask, dtype=bool)
    N = board_mask.shape[0]          # should be 15
    assert N == 15, "Policy expects a 15×15 board"

    # Quick lookup of occupancy
    me_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)

    # Pre‑compute neighbour relationships for all cells
    neighbors = _build_neighbors(N)

    # ------------------------------------------------------------------
    # Build connected components for each player
    # ------------------------------------------------------------------
    # me components
    me_comp_id: Dict[Tuple[int, int], int] = {}
    me_components: Dict[int, List[Tuple[int, int]]] = {}

    comp_counter = 0
    for stone in me:
        if stone not in me_comp_id:
            comp_counter += 1
            comp_id = comp_counter
            me_comp_id[stone] = comp_id
            comp_nodes = [stone]
            stack = [stone]
            while stack:
                cur = stack.pop()
                for nb in neighbors[cur]:
                    if nb in me_set and nb not in me_comp_id:
                        me_comp_id[nb] = comp_id
                        comp_nodes.append(nb)
                        stack.append(nb)
            me_components[comp_id] = comp_nodes

    # opp components
    opp_comp_id: Dict[Tuple[int, int], int] = {}
    opp_components: Dict[int, List[Tuple[int, int]]] = {}

    comp_counter = 0
    for stone in opp:
        if stone not in opp_comp_id:
            comp_counter += 1
            comp_id = comp_counter
            opp_comp_id[stone] = comp_id
            comp_nodes = [stone]
            stack = [stone]
            while stack:
                cur = stack.pop()
                for nb in neighbors[cur]:
                    if nb in opp_set and nb not in opp_comp_id:
                        opp_comp_id[nb] = comp_id
                        comp_nodes.append(nb)
                        stack.append(nb)
            opp_components[comp_id] = comp_nodes

    # ------------------------------------------------------------------
    # For each component, record which corners / edges it already touches
    # ------------------------------------------------------------------
    # corners
    me_corner_comp: Dict[int, Set[Tuple[int, int]]] = {c: set() for c in me_components}
    opp_corner_comp: Dict[int, Set[Tuple[int, int]]] = {c: set() for c in opp_components}

    # edges
    me_edge_comp: Dict[int, Set[Tuple[int, int]]] = {c: set() for c in me_components}
    opp_edge_comp: Dict[int, Set[Tuple[int, int]]] = {c: set() for c in opp_components}

    # helper to check adjacency to corners / edges
    for corner in _CORNERS:
        # check if any neighbour of this corner belongs to player X
        for nb in neighbors[corner]:
            if nb in me_set:
                cid = me_comp_id[nb]
                me_corner_comp[cid].add(corner)
                break
        for nb in neighbors[corner]:
            if nb in opp_set:
                cid = opp_comp_id[nb]
                opp_corner_comp[cid].add(corner)
                break

    edges = _edge_cells(N, set(_CORNERS))
    for edge in edges:
        for nb in neighbors[edge]:
            if nb in me_set:
                cid = me_comp_id[nb]
                me_edge_comp[cid].add(edge)
                break
        for nb in neighbors[edge]:
            if nb in opp_set:
                cid = opp_comp_id[nb]
                opp_edge_comp[cid].add(edge)
                break

    # ------------------------------------------------------------------
    # Evaluate each playable empty cell
    # ------------------------------------------------------------------
    # Collect all playable coordinates
    playable: List[Tuple[int, int]] = [
        (r, c) for r in range(N) for c in range(N)
        if board_mask[r, c] and (r, c) not in me_set and (r, c) not in opp_set
    ]

    if not playable:
        # Defensive fallback (should never happen)
        # Choose the centre of the board, falling back to any legal cell
        return tuple(valid_mask.argmax())

    best_move = None
    best_score = -float('inf')
    best_manhattan = float('inf')

    for rc in playable:
        r, c = rc

        # Direct corner/edge adjacency of this empty cell
        my_adjacent_corners: Set[Tuple[int, int]] = set()
        my_adjacent_edges: Set[Tuple[int, int]] = set()
        opp_adjacent_corners: Set[Tuple[int, int]] = set()
        opp_adjacent_edges: Set[Tuple[int, int]] = set()

        for adj in neighbors[(r, c)]:
            # My stones
            if adj in me_set:
                my_cid = me_comp_id[adj]
                my_adjacent_corners |= me_corner_comp.get(my_cid, set())
                my_adjacent_edges |= me_edge_comp.get(my_cid, set())
            # Opponent stones
            if adj in opp_set:
                opp_cid = opp_comp_id[adj]
                opp_adjacent_corners |= opp_corner_comp.get(opp_cid, set())
                opp_adjacent_edges |= opp_edge_comp.get(opp_cid, set())

        # Direct adjacency to corners / edges
        for corner in _CORNERS:
            if corner in neighbors[(r, c)]:
                my_adjacent_corners.add(corner)
        for edge in edges:
            if edge in neighbors[(r, c)]:
                my_adjacent_edges.add(edge)
        # similarly for opponent adjacency
        for corner in _CORNERS:
            if corner in neighbors[(r, c)]:
                opp_adjacent_corners.add(corner)
        for edge in edges:
            if edge in neighbors[(r, c)]:
                opp_adjacent_edges.add(edge)

        # Heuristic benefit
        # weight corners double because a bridge (2 corners) is more valuable than a fork (3 edges)
        score = (
            2 * len(my_adjacent_corners) + len(my_adjacent_edges) -
            2 * len(opp_adjacent_corners) - len(opp_adjacent_edges)
        )
        # Bonus for joining ≥2 distinct components of my own stones
        my_cids = {me_comp_id[nb] for nb in neighbors[(r, c)] if nb in me_set}
        extra = max(len(my_cids) - 1, 0) * 5   # encourages merging components
        score += extra

        # Break ties: choose the cell closest to the centre (min max‑distance)
        # and then by smallest row then column
        manhattan = abs(r - N // 2) + abs(c - N // 2)

        if score > best_score or (score == best_score and manhattan < best_manhattan):
            best_score = score
            best_move = (r, c)
            best_manhattan = manhattan

    return best_move
