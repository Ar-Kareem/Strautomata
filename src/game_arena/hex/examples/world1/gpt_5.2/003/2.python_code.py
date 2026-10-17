
from __future__ import annotations

import heapq
from typing import List, Tuple, Set, Dict, Optional

N = 11
INF = 10**9

Coord = Tuple[int, int]


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _neighbors(r: int, c: int) -> List[Coord]:
    # Hex neighbors in the problem's coordinate system:
    # all 8 grid neighbors except (r-1,c-1) and (r+1,c+1)
    cand = [
        (r, c - 1), (r, c + 1),
        (r - 1, c), (r - 1, c + 1),
        (r + 1, c), (r + 1, c - 1),
    ]
    return [(rr, cc) for rr, cc in cand if _in_bounds(rr, cc)]


def _edge_cells(color: str, which: str) -> List[Coord]:
    # which: "start" or "end"
    if color == "b":
        if which == "start":  # top
            return [(0, c) for c in range(N)]
        else:  # bottom
            return [(N - 1, c) for c in range(N)]
    else:  # 'w'
        if which == "start":  # left
            return [(r, 0) for r in range(N)]
        else:  # right
            return [(r, N - 1) for r in range(N)]


def _cell_cost(cell: Coord, player: Set[Coord], other: Set[Coord]) -> int:
    if cell in player:
        return 0
    if cell in other:
        return INF
    return 1


def _dijkstra(
    player_color: str,
    player: Set[Coord],
    other: Set[Coord],
    start_side: str = "start",
) -> Tuple[int, Dict[Coord, int]]:
    """
    Returns (best_cost_to_connect, dist_map_from_start_edge).
    Costs: 0 for player's stones, 1 for empty, INF for opponent.
    start_side: "start" uses the player's normal start edge, "end" uses the opposite edge.
    """
    if start_side == "start":
        starts = _edge_cells(player_color, "start")
        ends = set(_edge_cells(player_color, "end"))
    else:
        starts = _edge_cells(player_color, "end")
        ends = set(_edge_cells(player_color, "start"))

    dist: Dict[Coord, int] = {}
    h: List[Tuple[int, Coord]] = []

    for s in starts:
        cs = _cell_cost(s, player, other)
        if cs >= INF:
            continue
        dist[s] = cs
        heapq.heappush(h, (cs, s))

    best_end = INF
    while h:
        d, u = heapq.heappop(h)
        if d != dist.get(u, INF):
            continue
        if d >= best_end:
            continue
        if u in ends:
            best_end = d
            continue
        ur, uc = u
        for v in _neighbors(ur, uc):
            cv = _cell_cost(v, player, other)
            if cv >= INF:
                continue
            nd = d + cv
            if nd < dist.get(v, INF):
                dist[v] = nd
                heapq.heappush(h, (nd, v))

    return best_end, dist


def _through_values(
    player_color: str,
    player: Set[Coord],
    other: Set[Coord],
) -> Tuple[int, Dict[Coord, int]]:
    """
    Computes a rough 'through' value for each cell:
      through[cell] = dist_from_start[cell] + dist_from_end[cell] - cost(cell)
    which approximates how close the cell is to being on a shortest connecting route.
    Returns (best_connection_cost, through_map).
    """
    best_s, ds = _dijkstra(player_color, player, other, start_side="start")
    _, de = _dijkstra(player_color, player, other, start_side="end")

    through: Dict[Coord, int] = {}
    for r in range(N):
        for c in range(N):
            cell = (r, c)
            if cell not in ds or cell not in de:
                continue
            cc = _cell_cost(cell, player, other)
            if cc >= INF:
                continue
            through[cell] = ds[cell] + de[cell] - cc
    return best_s, through


def _bridge_bonus(move: Coord, player: Set[Coord], other: Set[Coord]) -> int:
    """
    Small tactical heuristic: bonuses for creating/maintaining bridges,
    and for occupying a bridge point that the opponent could use.
    Bridge patterns implemented (offset coords):
      endpoints (r,c) & (r+1,c+1): bridge cells (r,c+1) and (r+1,c)
      endpoints (r,c) & (r+1,c-1): bridge cells (r,c-1) and (r+1,c)
    """
    mr, mc = move
    bonus = 0

    # helper to check endpoints/bridge-cells pattern
    def consider(e1: Coord, e2: Coord, b1: Coord, b2: Coord) -> None:
        nonlocal bonus
        if not (_in_bounds(*e1) and _in_bounds(*e2) and _in_bounds(*b1) and _in_bounds(*b2)):
            return
        # If we own both endpoints, playing a bridge cell helps stabilize connection.
        if e1 in player and e2 in player:
            if move == b1 or move == b2:
                bonus += 6
        # If opponent owns both endpoints, taking a bridge cell can disrupt.
        if e1 in other and e2 in other:
            if move == b1 or move == b2:
                bonus += 5

    # Patterns where move could be one of the bridge cells; check endpoints around it.
    # We'll enumerate possible endpoint pairs that generate bridges containing 'move'.
    # Case A: endpoints (r,c) & (r+1,c+1) => bridge cells (r,c+1) and (r+1,c)
    # If move == (r,c+1) then endpoints are (r,c) and (r+1,c+1)
    consider((mr, mc - 1), (mr + 1, mc), (mr, mc), (mr + 1, mc - 1))  # derived from move as b1
    # If move == (r+1,c) then endpoints are (r,c) and (r+1,c+1)
    consider((mr - 1, mc), (mr, mc + 1), (mr - 1, mc + 1), (mr, mc))  # derived from move as b2

    # Case B: endpoints (r,c) & (r+1,c-1) => bridge cells (r,c-1) and (r+1,c)
    # If move == (r,c-1) then endpoints are (r,c) and (r+1,c-1)
    consider((mr, mc + 1), (mr + 1, mc), (mr, mc), (mr + 1, mc + 1))
    # If move == (r+1,c) then endpoints are (r,c) and (r+1,c-1)
    consider((mr - 1, mc), (mr, mc - 1), (mr - 1, mc - 1), (mr, mc))

    return bonus


def _adjacency_bonus(move: Coord, me: Set[Coord], opp: Set[Coord]) -> int:
    r, c = move
    nb = _neighbors(r, c)
    my_adj = sum((x in me) for x in nb)
    opp_adj = sum((x in opp) for x in nb)
    # Prefer some contact, but not pure clumping; keep it mild.
    return 2 * my_adj + 1 * opp_adj


def _center_penalty(move: Coord) -> float:
    r, c = move
    return 0.15 * (abs(r - (N // 2)) + abs(c - (N // 2)))


def policy(me: List[Coord], opp: List[Coord], color: str) -> Coord:
    me_set: Set[Coord] = set(me)
    opp_set: Set[Coord] = set(opp)

    # All empty cells
    empties: List[Coord] = [(r, c) for r in range(N) for c in range(N)
                            if (r, c) not in me_set and (r, c) not in opp_set]

    # Always return a legal move
    if not empties:
        return (0, 0)  # should never happen in normal play

    # Opening: center is robust
    if not me_set and not opp_set:
        center = (N // 2, N // 2)
        if center in empties:
            return center
        return empties[0]

    # Compute current path landscapes for candidate focusing
    my_best_before, my_through = _through_values(color, me_set, opp_set)
    opp_color = "w" if color == "b" else "b"
    opp_best_before, opp_through = _through_values(opp_color, opp_set, me_set)

    # Candidate generation: near shortest paths + neighbors of stones
    candidates: Set[Coord] = set()

    # Near our shortest path
    for cell, tv in my_through.items():
        if cell in me_set or cell in opp_set:
            continue
        if tv <= my_best_before + 2:
            candidates.add(cell)

    # Near opponent shortest path (to block)
    for cell, tv in opp_through.items():
        if cell in me_set or cell in opp_set:
            continue
        if tv <= opp_best_before + 2:
            candidates.add(cell)

    # Local vicinity of existing stones
    for (r, c) in list(me_set) + list(opp_set):
        for nb in _neighbors(r, c):
            if nb in me_set or nb in opp_set:
                continue
            candidates.add(nb)

    # Ensure at least some candidates
    if not candidates:
        candidates = set(empties)

    # Evaluate candidates by simulating the move
    best_move: Optional[Coord] = None
    best_score: float = -1e18

    for mv in candidates:
        if mv in me_set or mv in opp_set:
            continue
        r, c = mv
        if not _in_bounds(r, c):
            continue

        me2 = set(me_set)
        me2.add(mv)

        # Recompute shortest-path costs after the move
        my_best_after, _ = _dijkstra(color, me2, opp_set, start_side="start")
        opp_best_after, _ = _dijkstra(opp_color, opp_set, me2, start_side="start")

        # Immediate win preference
        if my_best_after == 0:
            return mv

        improve_me = my_best_before - my_best_after
        worsen_opp = opp_best_after - opp_best_before

        score = 0.0
        score += 100.0 * (opp_best_after - my_best_after)     # main objective
        score += 25.0 * worsen_opp                            # blocking value
        score += 18.0 * improve_me                            # self improvement
        score += 5.0 * _bridge_bonus(mv, me_set, opp_set)
        score += 1.2 * _adjacency_bonus(mv, me_set, opp_set)
        score -= _center_penalty(mv)

        # Tiny deterministic tie-break
        score -= 1e-4 * (r * N + c)

        if score > best_score:
            best_score = score
            best_move = mv

    # Fallback: first legal empty
    if best_move is None or best_move in me_set or best_move in opp_set:
        # Prefer center-ish as final fallback
        empties_sorted = sorted(empties, key=lambda x: (abs(x[0] - N // 2) + abs(x[1] - N // 2), x[0], x[1]))
        return empties_sorted[0]

    return best_move
