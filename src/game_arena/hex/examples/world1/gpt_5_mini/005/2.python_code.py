
#!/usr/bin/env python3
"""
Hex 11x11 policy.

Implements:
def policy(me: list[tuple[int,int]], opp: list[tuple[int,int]], color: str) -> tuple[int,int]

Strategy:
- Compute shortest "fill" cost for connecting our target sides using a Dijkstra-style search:
    cost to traverse a node = 0 if occupied by us, 1 if empty, blocked if occupied by opponent.
  This yields the minimum number of empty cells we must fill to complete a connection.
- For each empty cell, simulate placing our stone and recompute:
    - our new shortest cost (we prefer large reductions),
    - opponent's new shortest cost (we prefer moves that increase opponent cost).
- Score = 10*(our_cost_reduction) + 1*(opp_cost_increase) + small_center_bonus.
- If any move yields our cost == 0 (immediate connection), play it.
- Return a legal empty cell (always).
"""

from heapq import heappush, heappop
from typing import List, Tuple, Set

N = 11
INF = 10**9

# Precompute neighbors according to the hex adjacency described:
# neighbors = all 8 neighbors except (i-1, j-1) and (i+1, j+1)
_NEIGHBORS = {}
for i in range(N):
    for j in range(N):
        neigh = []
        for di, dj in [(0, -1), (0, 1), (-1, 0), (1, 0), (-1, 1), (1, -1)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < N and 0 <= nj < N:
                neigh.append((ni, nj))
        _NEIGHBORS[(i, j)] = neigh


def side_cells(color: str, side: str) -> List[Tuple[int, int]]:
    """
    Return list of coordinates for a given side:
    For 'b' (black) sides are 'top' (row 0) and 'bottom' (row N-1).
    For 'w' (white) sides are 'left' (col 0) and 'right' (col N-1).
    """
    if color == 'b':
        if side == 'start':
            return [(0, j) for j in range(N)]
        else:
            return [(N-1, j) for j in range(N)]
    else:
        if side == 'start':
            return [(i, 0) for i in range(N)]
        else:
            return [(i, N-1) for i in range(N)]


def shortest_fill_cost(player_set: Set[Tuple[int, int]],
                       other_set: Set[Tuple[int, int]],
                       color: str) -> int:
    """
    Dijkstra-like search for minimum number of empty cells that must be filled
    to connect this player's two sides.
    - player_set: coordinates occupied by this player
    - other_set: coordinates occupied by opponent (treated as blocked)
    - color: 'b' or 'w' for which sides to connect
    Returns INF if no path exists (completely blocked).
    """
    # Starting cells (side A) and target cells (side B)
    starts = side_cells(color, 'start')
    targets = set(side_cells(color, 'end'))

    # If any start cell is blocked by opponent, skip it.
    dist = { (i,j): INF for i in range(N) for j in range(N) }
    heap = []

    for (i, j) in starts:
        if (i, j) in other_set:
            continue
        # cost to "enter" this start cell
        c = 0 if (i, j) in player_set else 1
        if c < dist[(i, j)]:
            dist[(i, j)] = c
            heappush(heap, (c, (i, j)))

    # If no valid starts, no path
    if not heap:
        return INF

    visited = set()
    while heap:
        d, node = heappop(heap)
        if d != dist[node]:
            continue
        if node in targets:
            return d
        visited.add(node)
        for nb in _NEIGHBORS[node]:
            if nb in other_set:
                continue
            # cost to move into neighbor
            add = 0 if nb in player_set else 1
            nd = d + add
            if nd < dist[nb]:
                dist[nb] = nd
                heappush(heap, (nd, nb))
    return INF


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """
    Choose a legal move for Hex 11x11.
    Returns (row, col).
    """
    me_set = set(me)
    opp_set = set(opp)

    # Sanity: list empty cells
    empties = [(i, j) for i in range(N) for j in range(N) if (i, j) not in me_set and (i, j) not in opp_set]
    if not empties:
        # No empty cell -- shouldn't happen, but pick a default in bounds
        return (0, 0)

    # Opponent color
    opp_color = 'b' if color == 'w' else 'w'

    # Baseline distances
    baseline_my = shortest_fill_cost(me_set, opp_set, color)
    baseline_opp = shortest_fill_cost(opp_set, me_set, opp_color)

    best_move = None
    best_score = -10**9
    # center for tie-break
    center = (N - 1) / 2.0

    for pos in empties:
        # simulate placing at pos
        me2 = me_set.union({pos})

        # Our new cost
        my_new = shortest_fill_cost(me2, opp_set, color)
        if my_new == 0:
            # immediate win
            return pos

        # Opponent's cost when we occupy pos (we may block them)
        opp_new = shortest_fill_cost(opp_set, me2, opp_color)

        # score: prioritize reducing our cost, then hurting opponent, then centrality
        my_reduction = baseline_my - my_new
        opp_increase = opp_new - baseline_opp

        # small centrality bonus to prefer center moves on ties
        r, c = pos
        dist_center_sq = (r - center) ** 2 + (c - center) ** 2
        center_bonus = -0.01 * dist_center_sq

        score = 10.0 * my_reduction + 1.0 * opp_increase + center_bonus

        # tie-break by lower (row,col) deterministic if scores equal-ish
        if score > best_score + 1e-9:
            best_score = score
            best_move = pos

    # Fallback: if something went wrong, pick a central empty
    if best_move is None:
        # pick the empty with minimal distance to center
        best_move = min(empties, key=lambda rc: (rc[0]-center)**2 + (rc[1]-center)**2)

    return best_move


# If the module is run directly, provide a trivial demo (not used in arena).
if __name__ == "__main__":
    # simple test: empty board, black to move -> play near center
    print(policy([], [], 'b'))
