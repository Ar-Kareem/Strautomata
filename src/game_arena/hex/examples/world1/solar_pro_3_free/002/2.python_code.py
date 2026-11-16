
from collections import deque
from typing import List, Tuple, Set

# Board size for the provided arena
N = 11
INF = 10**9

# Hexagonal neighbor offsets (exclude (i-1, j-1) and (i+1, j+1))
NEIGH = [(-1, 0), (0, -1), (0, 1), (1, 0), (1, -1), (-1, 1)]

def _multi_source_bfs(
    starts: List[Tuple[int, int]],
    allowed: Set[Tuple[int, int]],
) -> dict[Tuple[int, int], int]:
    """Breadth‑first search from all start cells simultaneously.
    Returns a dict: cell → shortest distance from any start cell."""
    dist = {}
    q = deque()
    for s in starts:
        if s in allowed:
            dist[s] = 0
            q.append(s)
    while q:
        r, c = q.popleft()
        cur = dist[(r, c)]
        for dr, dc in NEIGH:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                nxt = (nr, nc)
                if nxt in allowed and nxt not in dist:
                    dist[nxt] = cur + 1
                    q.append(nxt)
    return dist

def policy(
    me: List[Tuple[int, int]],
    opp: List[Tuple[int, int]],
    color: str,
) -> Tuple[int, int]:
    # All possible cells on the 11×11 board
    board: Set[Tuple[int, int]] = {(i, j) for i in range(N) for j in range(N)}
    # Cells that are still empty
    empties: Set[Tuple[int, int]] = board - set(me) - set(opp)
    if not empties:      # Defensive fallback (should never happen at legal turn)
        return (0, 0)

    # Which cells we can walk on from the perspective of each player
    # Black (me) can only step on empty cells or its own stones
    allowed_black = board - set(opp)
    # White (opp) can only step on empty cells or its own stones
    allowed_white = board - set(me)

    # Borders for each side
    top_start = [(0, j) for j in range(N) if (0, j) in allowed_black]
    bottom_start = [(N - 1, j) for j in range(N) if (N - 1, j) in allowed_black]
    left_start = [(i, 0) for i in range(N) if (i, 0) in allowed_white]
    right_start = [(i, N - 1) for i in range(N) if (i, N - 1) in allowed_white]

    # Distances for each side
    dist_top = _multi_source_bfs(top_start, allowed_black)
    dist_bottom = _multi_source_bfs(bottom_start, allowed_black)
    dist_left = _multi_source_bfs(left_start, allowed_white)
    dist_right = _multi_source_bfs(right_start, allowed_white)

    best_cell = None
    best_sum = INF

    if color == 'b':            # Black tries to connect top ↔ bottom
        for cell in empties:
            d = dist_top.get(cell, INF) + dist_bottom.get(cell, INF)
            if d < best_sum:
                best_sum = d
                best_cell = cell
    else:                       # White tries to connect left ↔ right
        for cell in empties:
            d = dist_left.get(cell, INF) + dist_right.get(cell, INF)
            if d < best_sum:
                best_sum = d
                best_cell = cell

    # Defensive fallback: if every sum is INF (opponent blocked all paths)
    if best_cell is None:
        best_cell = next(iter(empties))

    return best_cell  # tuple (row, col) – always a legal empty cell
