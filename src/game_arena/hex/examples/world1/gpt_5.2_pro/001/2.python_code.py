
from __future__ import annotations

import heapq
from typing import List, Tuple, Set, Dict, Iterable

N = 11
INF = 10**9

# Hex neighbors for the given coordinate system:
# "all 8 neighbors except (i-1, j-1) and (i+1, j+1)"
# => 6 neighbors:
NEI_OFFS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _idx(r: int, c: int) -> int:
    return r * N + c


def _rc(i: int) -> Tuple[int, int]:
    return divmod(i, N)


# Precompute neighbors for speed
_NEIGHBORS: List[List[int]] = []
for r in range(N):
    for c in range(N):
        ns = []
        for dr, dc in NEI_OFFS:
            rr, cc = r + dr, c + dc
            if _in_bounds(rr, cc):
                ns.append(_idx(rr, cc))
        _NEIGHBORS.append(ns)


def _borders(color: str) -> Tuple[List[int], Set[int]]:
    """
    Returns (sources, goals) indices for the player of given color.
    black 'b' connects top (row=0) to bottom (row=10)
    white 'w' connects left (col=0) to right (col=10)
    """
    if color == "b":
        sources = [_idx(0, c) for c in range(N)]
        goals = {_idx(N - 1, c) for c in range(N)}
    else:
        sources = [_idx(r, 0) for r in range(N)]
        goals = {_idx(r, N - 1) for r in range(N)}
    return sources, goals


def _cell_cost(i: int, own: Set[int], opp: Set[int]) -> int:
    if i in opp:
        return INF
    if i in own:
        return 0
    return 1


def _dijkstra_best_cost(color: str, own: Set[int], opp: Set[int]) -> int:
    sources, goals = _borders(color)
    dist = [INF] * (N * N)
    h = []

    # multi-source init
    for s in sources:
        w = _cell_cost(s, own, opp)
        if w >= INF:
            continue
        if w < dist[s]:
            dist[s] = w
            heapq.heappush(h, (w, s))

    while h:
        d, u = heapq.heappop(h)
        if d != dist[u]:
            continue
        if u in goals:
            return d
        for v in _NEIGHBORS[u]:
            wv = _cell_cost(v, own, opp)
            if wv >= INF:
                continue
            nd = d + wv
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(h, (nd, v))

    return INF


def _dijkstra_all_from_sources(sources: Iterable[int], own: Set[int], opp: Set[int]) -> List[int]:
    dist = [INF] * (N * N)
    h = []
    for s in sources:
        w = _cell_cost(s, own, opp)
        if w >= INF:
            continue
        if w < dist[s]:
            dist[s] = w
            heapq.heappush(h, (w, s))

    while h:
        d, u = heapq.heappop(h)
        if d != dist[u]:
            continue
        for v in _NEIGHBORS[u]:
            wv = _cell_cost(v, own, opp)
            if wv >= INF:
                continue
            nd = d + wv
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(h, (nd, v))
    return dist


def _compute_path_fields(color: str, own: Set[int], opp: Set[int]) -> Tuple[int, List[int], List[int]]:
    """
    Returns:
      best_cost, dist_from_sources, dist_from_goals
    dist arrays include the cost of the node itself when entered (as defined by _cell_cost).
    """
    sources, goals = _borders(color)
    best = _dijkstra_best_cost(color, own, opp)
    dist_fwd = _dijkstra_all_from_sources(sources, own, opp)
    dist_rev = _dijkstra_all_from_sources(goals, own, opp)  # undirected graph so same neighbor relation
    return best, dist_fwd, dist_rev


def _bridge_scores(own: Set[int], opp: Set[int]) -> Dict[int, int]:
    """
    Bridge pattern for this coordinate system:
    Cells (r,c) and (r+1,c+1) are NOT adjacent and form a virtual connection.
    The two bridge points are (r, c+1) and (r+1, c).
    Symmetrically for (r,c) and (r-1,c-1), bridge points (r-1,c) and (r,c-1).

    Return a dict: empty_cell_idx -> bonus score.
    """
    bonus: Dict[int, int] = {}

    def add(idx_cell: int, val: int) -> None:
        if idx_cell < 0:
            return
        bonus[idx_cell] = bonus.get(idx_cell, 0) + val

    for a in own:
        r, c = _rc(a)

        # Pair with (r+1, c+1)
        rb, cb = r + 1, c + 1
        if _in_bounds(rb, cb) and _idx(rb, cb) in own:
            p1 = (r, c + 1)
            p2 = (r + 1, c)
            if _in_bounds(*p1) and _in_bounds(*p2):
                i1, i2 = _idx(*p1), _idx(*p2)
                # If one bridge point is taken by opponent, the other becomes urgent.
                if i1 in opp and i2 not in own and i2 not in opp:
                    add(i2, 80)
                if i2 in opp and i1 not in own and i1 not in opp:
                    add(i1, 80)
                # Otherwise both bridge points are generally good.
                if i1 not in own and i1 not in opp:
                    add(i1, 18)
                if i2 not in own and i2 not in opp:
                    add(i2, 18)

        # Pair with (r-1, c-1)
        rb, cb = r - 1, c - 1
        if _in_bounds(rb, cb) and _idx(rb, cb) in own:
            p1 = (r - 1, c)
            p2 = (r, c - 1)
            if _in_bounds(*p1) and _in_bounds(*p2):
                i1, i2 = _idx(*p1), _idx(*p2)
                if i1 in opp and i2 not in own and i2 not in opp:
                    add(i2, 80)
                if i2 in opp and i1 not in own and i1 not in opp:
                    add(i1, 80)
                if i1 not in own and i1 not in opp:
                    add(i1, 18)
                if i2 not in own and i2 not in opp:
                    add(i2, 18)

    return bonus


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    my_set: Set[int] = {_idx(r, c) for r, c in me}
    opp_set: Set[int] = {_idx(r, c) for r, c in opp}

    # Build empties
    empties: List[int] = []
    for r in range(N):
        for c in range(N):
            i = _idx(r, c)
            if i not in my_set and i not in opp_set:
                empties.append(i)

    # Always return a legal move
    if not empties:
        return (0, 0)

    # Opening preference: center-ish if empty
    center = _idx(N // 2, N // 2)
    if len(my_set) == 0 and len(opp_set) == 0 and center in empties:
        return (N // 2, N // 2)

    their_color = "w" if color == "b" else "b"

    # 1) Immediate winning move
    for e in empties:
        new_my = set(my_set)
        new_my.add(e)
        if _dijkstra_best_cost(color, new_my, opp_set) == 0:
            return _rc(e)

    # 2) Must-block opponent immediate win
    opp_winning_moves = []
    for e in empties:
        new_opp = set(opp_set)
        new_opp.add(e)
        if _dijkstra_best_cost(their_color, new_opp, my_set) == 0:
            opp_winning_moves.append(e)

    if opp_winning_moves:
        # Choose the block that best improves our own situation
        best_block = opp_winning_moves[0]
        best_val = INF
        for e in opp_winning_moves:
            new_my = set(my_set)
            new_my.add(e)
            my_cost = _dijkstra_best_cost(color, new_my, opp_set)
            if my_cost < best_val:
                best_val = my_cost
                best_block = e
        return _rc(best_block)

    # 3) Strategic scoring
    my_best, my_fwd, my_rev = _compute_path_fields(color, my_set, opp_set)
    opp_best, opp_fwd, opp_rev = _compute_path_fields(their_color, opp_set, my_set)

    my_bridge = _bridge_scores(my_set, opp_set)
    opp_bridge = _bridge_scores(opp_set, my_set)

    # Heuristic shortlist
    scored: List[Tuple[int, int]] = []
    for e in empties:
        r, c = _rc(e)
        # Center pull (mild)
        center_pull = 10 - (abs(r - (N // 2)) + abs(c - (N // 2)))

        # Whether this empty lies on an optimal path currently
        # For empties, cost(cell) = 1, so:
        # path_via = fwd[e] + rev[e] - 1
        my_on_best = 1 if (my_fwd[e] < INF and my_rev[e] < INF and (my_fwd[e] + my_rev[e] - 1) == my_best) else 0
        opp_on_best = 1 if (opp_fwd[e] < INF and opp_rev[e] < INF and (opp_fwd[e] + opp_rev[e] - 1) == opp_best) else 0

        b_my = my_bridge.get(e, 0)
        b_opp = opp_bridge.get(e, 0)  # playing here also disrupts their bridge

        h = (
            20 * my_on_best +
            16 * opp_on_best +
            b_my +
            (b_opp // 2) +  # disrupting bridges is good, but less than building ours
            center_pull
        )
        scored.append((h, e))

    scored.sort(reverse=True)

    # Evaluate exact Dijkstra on top K candidates
    K = 14
    candidates = [e for _, e in scored[:K]]
    if not candidates:
        candidates = [scored[0][1]]

    best_move = candidates[0]
    best_score = -10**18

    for e in candidates:
        new_my = set(my_set)
        new_my.add(e)

        my_cost_after = _dijkstra_best_cost(color, new_my, opp_set)
        # Opponent cost with same board (they haven't moved), but our stone blocks them
        opp_cost_after = _dijkstra_best_cost(their_color, opp_set, new_my)

        r, c = _rc(e)
        center_pull = 10 - (abs(r - (N // 2)) + abs(c - (N // 2)))
        b_my = my_bridge.get(e, 0)
        b_opp = opp_bridge.get(e, 0)

        # Main objective: maximize opponent difficulty while minimizing ours
        # Large weight on the differential, then small positional tweaks.
        score = (opp_cost_after - my_cost_after) * 1000 + center_pull * 3 + b_my * 4 + (b_opp * 2)

        if score > best_score:
            best_score = score
            best_move = e

    # Safety: ensure legal
    if best_move in my_set or best_move in opp_set:
        best_move = empties[0]
    return _rc(best_move)
