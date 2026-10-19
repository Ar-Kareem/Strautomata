
import numpy as np
from collections import deque
from typing import List, Tuple

# Global bookkeeping for the simplest ko handling.
# If a capture move repeats the opponent's last move, it is ignored.
_last_move: Tuple[int, int] = None
_ko_point: Tuple[int, int] = None

# Directions: orthogonal and diagonal neighbours for group detection.
_NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1)]            # orthogonal (liberties)
_ALL_NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1),
                  (1, 1), (1, -1), (-1, 1), (-1, -1)]    # full adjacency

def _dist_edge(r: int, c: int) -> int:
    """Manhattan distance to the nearest board edge (0‑18)."""
    return min(r, c, 18 - r, 18 - c)

def _adjacent(board: np.ndarray, row: int, col: int) -> Tuple[int, int]:
    """Return (my_adjacent, opponent_adjacent) counts for a given point."""
    my_adj, opp_adj = 0, 0
    for dr, dc in _ALL_NEIGHBORS:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            val = board[nr, nc]
            if val == 1:
                my_adj += 1
            elif val == -1:
                opp_adj += 1
    return my_adj, opp_adj

def _capture_candidates(board: np.ndarray, me_stones: List[Tuple[int, int]],
                       opponent_stones: List[Tuple[int, int]]) -> set:
    """
    Find empty points that would capture an opponent group with exactly
    one liberty (i.e. opponent groups that are at‑ari). These points are
    safe captures unless they are the ko point.
    """
    visited = set()
    components = []          # list of opponent groups
    comp_id_of = {}          # maps position → component index
    comp_grid = np.full((19, 19), -1, dtype=int)  # -1 unknown, >=0 id

    # BFS to label opponent groups
    for opp in opponent_stones:
        r, c = opp
        if comp_grid[r, c] != -1:
            continue
        comp_id = len(components)
        components.append([])
        comp_id_of[(r, c)] = comp_id
        q = deque([opp])
        comp_grid[r, c] = comp_id
        while q:
            cur = q.popleft()
            r, c = cur
            for dr, dc in _ALL_NEIGHBORS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19:
                    if board[nr, nc] == -1 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
                        comp_id_of[(nr, nc)] = comp_id
                        components[comp_id].append((nr, nc))
                        comp_grid[nr, nc] = comp_id

    # Compute orthogonal liberties for each opponent component
    liberties = {}
    orthogonal_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for comp in components:
        lib_set = set()
        for (r, c) in comp:
            for dr, dc in orthogonal_dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    lib_set.add((nr, nc))
        liberties[comp_id_of[(r, c)]] = lib_set

    # Capture candidates are liberty points of opponent groups with exactly one liberty
    caps = {p for lib in liberties.values() for p in lib if len(lib) == 1}
    return caps

def _my_group_liberties(board: np.ndarray, my_stones: List[Tuple[int, int]]) -> set:
    """Return a dict: component_id → set of orthogonal liberties."""
    visited = set()
    comp_id_of = {}
    comp_grid = np.full((19, 19), -1, dtype=int)
    comps = []
    for stone in my_stones:
        r, c = stone
        if comp_grid[r, c] != -1:
            continue
        comp_id = len(comps)
        comps.append([])
        comp_id_of[(r, c)] = comp_id
        comp_grid[r, c] = comp_id
        q = deque([stone])
        while q:
            cur = q.popleft()
            r, c = cur
            for dr, dc in _ALL_NEIGHBORS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19:
                    if board[nr, nc] == 1 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        q.append((nr, nc))
                        comp_id_of[(nr, nc)] = comp_id
                        comps[comp_id].append((nr, nc))
                        comp_grid[nr, nc] = comp_id
    # Compute liberties for each component
    libs = {}
    orthogonal_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    for comp in comps:
        lib_set = set()
        for (r, c) in comp:
            for dr, dc in orthogonal_dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                    lib_set.add((nr, nc))
        libs[comp_id_of[(r, c)]] = lib_set
    return libs

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Determine the next legal Go move.

    Parameters
    ----------
    me : List[Tuple[int, int]]
        Current coordinates of my stones (row, column) with 1‑based indexing.
    opponent : List[Tuple[int, int]]
        Current coordinates of opponent stones (row, column) with 1‑based indexing.

    Returns
    -------
    Tuple[int, int]
        The move as (row, column) in 1‑based indexing, or (0, 0) to pass.
    """
    global _last_move, _ko_point

    # 1. Build board representation (0‑based)
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r - 1, c - 1] = 1
    for r, c in opponent:
        board[r - 1, c - 1] = -1

    # No empty points -> pass
    empty = [(r, c) for r in range(19) for c in range(19) if board[r, c] == 0]
    if not empty:
        return (0, 0)

    # 2. Capture opportunities
    caps = _capture_candidates(board, me, opponent)
    valid_caps = [pt for pt in caps if pt != _ko_point]   # avoid immediate ko recurrence
    if valid_caps:
        # Simple score: central distance + liberties + my adjacency
        def move_score(p):
            r, c = p
            my_adj, opp_adj = _adjacent(board, r, c)
            libs = sum(board[r + dr, c + dc] == 0
                      for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]
                      if 0 <= r + dr < 19 and 0 <= c + dc < 19)
            return (_dist_edge(r, c) * 5) + (libs * 3) + (my_adj * 2) - (opp_adj * 2)

        best = max(valid_caps, key=move_score)
        _last_move = best
        return (best[0] + 1, best[1] + 1)

    # 3. Compute my groups and dangerous (self‑capture) liberties
    my_libs = _my_group_liberties(board, me)
    danger = {pt for lib in my_libs.values() for pt in lib if len(lib) == 1}
    # Remove danger points from consideration (unless they are a capture, already handled)
    safe_moves = {pt for pt in empty if pt not in danger}

    # 4. Influence scoring for all safe empty points
    scores = {}
    for r, c in safe_moves:
        my_adj, opp_adj = _adjacent(board, r, c)
        libs = sum(board[r + dr, c + dc] == 0
                  for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]
                  if 0 <= r + dr < 19 and 0 <= c + dc < 19)
        dist = _dist_edge(r, c)
        # Basic weighted formula – liberti es are safest, adjacency boosts influence
        scores[(r, c)] = (libs * 3) + (my_adj * 1) - (opp_adj * 1) + dist

    # 5. Filter out the move that would repeat the previous player's move (simple ko defence)
    if _last_move:
        scores.pop(_last_move, None)

    # 6. If the top score is exactly a ko point, skip it and take the next best
    if scores and _ko_point and (next(iter(scores), None) == _ko_point):
        # Find a move that is not the ko point (if any)
        best_move = max(
            (pt for pt, sc in scores.items() if pt != _ko_point), key=lambda k: scores[k],
            default=_ko_point
        )
        if best_move == _ko_point:
            # No legal non‑ko move – pass
            return (0, 0)
        else:
            _last_move = best_move
            return (best_move[0] + 1, best_move[1] + 1)

    # 7. Choose the best scoring move
    if scores:
        best_move = max(scores.items(), key=lambda kv: kv[1])[0]
    else:               # board empty but we already returned pass, should not reach here
        best_move = (0, 0)

    # Record the move globally for possible ko handling
    _last_move = best_move
    return (best_move[0] + 1, best_move[1] + 1)
