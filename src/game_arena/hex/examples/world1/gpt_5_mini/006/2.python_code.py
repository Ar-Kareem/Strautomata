
#!/usr/bin/env python3
# Hex 11x11 policy using shortest-path heuristics
# Implements: policy(me: list[tuple[int,int]], opp: list[tuple[int,int]], color: str) -> tuple[int,int]

import heapq
from typing import List, Tuple, Dict, Optional, Set

SIZE = 11
INF = 10**6

# Neighbor offsets for hex grid as described:
# neighbors = [(i, j-1),(i, j+1),(i-1,j),(i-1,j+1),(i+1,j),(i+1,j-1)]
_NEIGHBORS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1))


def in_bounds(i: int, j: int) -> bool:
    return 0 <= i < SIZE and 0 <= j < SIZE


def idx(i: int, j: int) -> int:
    return i * SIZE + j


def coord(k: int) -> Tuple[int, int]:
    return (k // SIZE, k % SIZE)


def neighbors(i: int, j: int):
    for di, dj in _NEIGHBORS:
        ni, nj = i + di, j + dj
        if in_bounds(ni, nj):
            yield ni, nj


def dijkstra_side_cost(
    me_set: Set[Tuple[int, int]],
    opp_set: Set[Tuple[int, int]],
    my_color: str
) -> Tuple[Dict[int, int], Dict[int, Optional[int]], int, List[int]]:
    """
    Run Dijkstra node-cost search for the player with color my_color.
    Node cost: 0 for my stones, 1 for empties, INF for opponent stones.
    Returns (dist, pred, best_sink_dist, list_of_best_sink_nodes)
    """
    # Determine source and sink side nodes
    sources = []
    sinks = []
    if my_color == 'b':
        # black connects top(row=0) to bottom(row=SIZE-1)
        for j in range(SIZE):
            sources.append((0, j))
            sinks.append((SIZE - 1, j))
    else:
        # white connects left(col=0) to right(col=SIZE-1)
        for i in range(SIZE):
            sources.append((i, 0))
            sinks.append((i, SIZE - 1))

    # node cost function
    def node_cost(i, j):
        if (i, j) in me_set:
            return 0
        if (i, j) in opp_set:
            return INF
        return 1

    dist: Dict[int, int] = {}
    pred: Dict[int, Optional[int]] = {}
    pq: List[Tuple[int, int]] = []

    # initialize with source side nodes
    for (i, j) in sources:
        k = idx(i, j)
        c = node_cost(i, j)
        dist[k] = c
        pred[k] = None
        heapq.heappush(pq, (c, k))

    # Dijkstra
    while pq:
        d, k = heapq.heappop(pq)
        if d != dist.get(k, INF):
            continue
        i, j = coord(k)
        for ni, nj in neighbors(i, j):
            nk = idx(ni, nj)
            nd = d + node_cost(ni, nj)
            if nd < dist.get(nk, INF):
                dist[nk] = nd
                pred[nk] = k
                heapq.heappush(pq, (nd, nk))

    # find best sink nodes with minimum distance
    best_dist = INF
    best_sinks = []
    for (i, j) in sinks:
        k = idx(i, j)
        dk = dist.get(k, INF)
        if dk < best_dist:
            best_dist = dk
            best_sinks = [k]
        elif dk == best_dist:
            best_sinks.append(k)

    return dist, pred, best_dist, best_sinks


def reconstruct_path(pred: Dict[int, Optional[int]], end_k: int) -> List[int]:
    path = []
    cur = end_k
    while cur is not None:
        path.append(cur)
        cur = pred.get(cur, None)
    path.reverse()
    return path


def first_empty_on_path(path: List[int], me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]) -> Optional[Tuple[int, int]]:
    for k in path:
        i, j = coord(k)
        if (i, j) not in me_set and (i, j) not in opp_set:
            return (i, j)
    return None


def center_move(me_set: Set[Tuple[int, int]], opp_set: Set[Tuple[int, int]]) -> Tuple[int, int]:
    center = (SIZE // 2, SIZE // 2)
    if center not in me_set and center not in opp_set:
        return center
    # fallback: pick nearest to center empty
    ci, cj = center
    best = None
    bestd = None
    for i in range(SIZE):
        for j in range(SIZE):
            if (i, j) in me_set or (i, j) in opp_set:
                continue
            d = abs(i - ci) + abs(j - cj)
            if best is None or d < bestd:
                best = (i, j)
                bestd = d
    if best is None:
        # board full? shouldn't happen, but return something valid
        for i in range(SIZE):
            for j in range(SIZE):
                if (i, j) not in me_set and (i, j) not in opp_set:
                    return (i, j)
    return best


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """
    Decide next move.
    me: list of my stones (row,col)
    opp: list of opponent stones
    color: 'b' or 'w' (my color)
    """
    me_set = set(me)
    opp_set = set(opp)

    # If board empty or first move, play center
    if not me and not opp:
        return center_move(me_set, opp_set)

    # 1) Compute my shortest path
    my_dist, my_pred, my_best_dist, my_best_sinks = dijkstra_side_cost(me_set, opp_set, color)

    # 2) Compute opponent shortest path (switch colors)
    # For opponent, we invert sets and color
    opp_color = 'b' if color == 'w' else 'w'
    opp_dist, opp_pred, opp_best_dist, opp_best_sinks = dijkstra_side_cost(opp_set, me_set, opp_color)

    # If I can win immediately (need exactly one empty)
    # my_best_dist is sum of node costs along min path; since my stones cost 0 and empties cost 1,
    # my_best_dist == 1 means a single empty is needed to connect.
    if my_best_dist <= 1:
        # reconstruct one of my shortest paths and place on its empty
        # choose the sink node with minimal dist and reconstruct
        chosen_path = None
        for sink_k in my_best_sinks:
            path = reconstruct_path(my_pred, sink_k)
            e = first_empty_on_path(path, me_set, opp_set)
            if e is not None:
                return e
            # if no empty (fully connected), ignore
        # fallback: pick any empty (should not reach here)
    # If opponent can win immediately, block their empty
    if opp_best_dist <= 1:
        for sink_k in opp_best_sinks:
            path = reconstruct_path(opp_pred, sink_k)
            e = first_empty_on_path(path, opp_set, me_set)  # in opp context, opp_set are their stones
            if e is not None and e not in me_set and e not in opp_set:
                return e
        # if not found, continue

    # Otherwise play an empty cell on my shortest path.
    # Reconstruct one of my shortest paths and pick first empty near my side.
    if my_best_dist < INF:
        # Try sinks in deterministic order
        my_best_sinks.sort()
        for sink_k in my_best_sinks:
            path = reconstruct_path(my_pred, sink_k)
            e = first_empty_on_path(path, me_set, opp_set)
            if e is not None:
                return e

    # If for some reason no path or no empty on my path (shouldn't happen), block opponent's path
    if opp_best_dist < INF:
        opp_best_sinks.sort()
        for sink_k in opp_best_sinks:
            path = reconstruct_path(opp_pred, sink_k)
            e = first_empty_on_path(path, opp_set, me_set)
            if e is not None and e not in me_set and e not in opp_set:
                return e

    # Fallback: play center-closest empty
    return center_move(me_set, opp_set)


# If run as a script, expose a simple test
if __name__ == "__main__":
    # quick smoke test: empty board for black
    print(policy([], [], 'b'))  # should print center (5,5)
