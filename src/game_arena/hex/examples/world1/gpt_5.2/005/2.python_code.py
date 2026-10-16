
from __future__ import annotations

import heapq
from typing import List, Tuple, Set, Optional

N = 11
INF = 10**9

# Hex neighbors per prompt: all 8 grid neighbors except (i-1,j-1) and (i+1,j+1)
# Equivalent 6 deltas:
DELTAS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

# Precompute neighbors for speed
_NEIGHBORS: List[List[List[Tuple[int, int]]]] = [[[] for _ in range(N)] for __ in range(N)]
for r in range(N):
    for c in range(N):
        nb = []
        for dr, dc in DELTAS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                nb.append((rr, cc))
        _NEIGHBORS[r][c] = nb


def _other_color(color: str) -> str:
    return "w" if color == "b" else "b"


def _start_goal_cells(color: str) -> Tuple[List[Tuple[int, int]], Set[Tuple[int, int]]]:
    """Return (start_side_cells, goal_side_set) for the given color."""
    if color == "b":
        start = [(0, c) for c in range(N)]
        goal = {(N - 1, c) for c in range(N)}
    else:
        start = [(r, 0) for r in range(N)]
        goal = {(r, N - 1) for r in range(N)}
    return start, goal


def _shortest_path_cost(own: Set[Tuple[int, int]], opp: Set[Tuple[int, int]], color: str) -> int:
    """
    Dijkstra shortest-path cost from one side to the opposite.
    Cell entry costs: own=0, empty=1, opp=INF(blocked).
    """
    start_cells, goal_cells = _start_goal_cells(color)

    def cell_cost(rc: Tuple[int, int]) -> int:
        if rc in opp:
            return INF
        if rc in own:
            return 0
        return 1

    dist = [[INF] * N for _ in range(N)]
    pq: List[Tuple[int, int, int]] = []

    for rc in start_cells:
        w = cell_cost(rc)
        if w >= INF:
            continue
        r, c = rc
        if w < dist[r][c]:
            dist[r][c] = w
            heapq.heappush(pq, (w, r, c))

    best_goal = INF
    while pq:
        d, r, c = heapq.heappop(pq)
        if d != dist[r][c]:
            continue
        if (r, c) in goal_cells:
            best_goal = d
            break
        for rr, cc in _NEIGHBORS[r][c]:
            w = cell_cost((rr, cc))
            if w >= INF:
                continue
            nd = d + w
            if nd < dist[rr][cc]:
                dist[rr][cc] = nd
                heapq.heappush(pq, (nd, rr, cc))

    return best_goal


def _local_bonus(move: Tuple[int, int], my_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]], color: str) -> float:
    """Small heuristic tie-breakers: connectivity, centrality, and directional preference."""
    r, c = move
    adj_my = 0
    adj_opp = 0
    for rr, cc in _NEIGHBORS[r][c]:
        if (rr, cc) in my_set:
            adj_my += 1
        elif (rr, cc) in opp_set:
            adj_opp += 1

    # Prefer adjacency to our stones, avoid adjacency to opponent stones (slightly).
    bonus = 22.0 * adj_my - 16.0 * adj_opp

    # Prefer central cells a bit (helps most openings/middlegame).
    center = (N - 1) / 2.0
    bonus -= 2.2 * (abs(r - center) + abs(c - center))

    # Mild directional shaping: black wants vertical connection, white wants horizontal.
    if color == "b":
        bonus -= 0.4 * abs(c - center)
    else:
        bonus -= 0.4 * abs(r - center)

    return bonus


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    my_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)

    occupied = my_set | opp_set
    empties: List[Tuple[int, int]] = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
    if not empties:
        # Should never happen in normal Hex, but must return something.
        return (0, 0)

    # Opening: if board empty, play center.
    center_move = (N // 2, N // 2)
    if not me and not opp and center_move in empties:
        return center_move

    my0 = _shortest_path_cost(my_set, opp_set, color)
    opp_color = _other_color(color)
    opp0 = _shortest_path_cost(opp_set, my_set, opp_color)

    # If already connected (shouldn't happen), just play any legal move.
    if my0 == 0:
        return empties[0]

    # If opponent has a 1-move win threat, prioritize blocking.
    urgent_defense = (opp0 <= 1)

    best_move: Optional[Tuple[int, int]] = None
    best_score: float = -1e18

    for mv in empties:
        my2 = set(my_set)
        my2.add(mv)

        my_after = _shortest_path_cost(my2, opp_set, color)
        opp_after = _shortest_path_cost(opp_set, my2, opp_color)

        # Immediate win.
        if my_after == 0:
            return mv

        # Core scoring:
        # - Strongly minimize our distance; strongly maximize opponent distance.
        # - Also consider improvements relative to current baseline.
        score = 0.0
        score += -1000.0 * my_after
        score += 700.0 * opp_after
        score += 320.0 * (my0 - my_after)
        score += 260.0 * (opp_after - opp0)

        # Local tie-break heuristics.
        score += _local_bonus(mv, my_set, opp_set, color)

        if urgent_defense:
            # When in danger, bias even more to increasing opponent's cost.
            score += 900.0 * (opp_after - opp0)

        if score > best_score:
            best_score = score
            best_move = mv

    # Safety fallback: ensure legal.
    if best_move is None or best_move in occupied:
        return empties[0]
    return best_move
