
from __future__ import annotations

from heapq import heappush, heappop
from collections import deque

N = 11
INF = 10**9

# Hex neighbors for the coordinate system described in the prompt.
DIRS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _neighbors(cell: tuple[int, int]):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc):
            yield (nr, nc)


def _empties(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]):
    occ = me_set | opp_set
    for r in range(N):
        for c in range(N):
            if (r, c) not in occ:
                yield (r, c)


def _has_connection(stones: set[tuple[int, int]], color: str) -> bool:
    """Check if stones already connect the target sides."""
    dq = deque()
    seen = set()

    if color == 'b':
        for c in range(N):
            cell = (0, c)
            if cell in stones:
                dq.append(cell)
                seen.add(cell)
        target_row = N - 1
        while dq:
            cell = dq.popleft()
            if cell[0] == target_row:
                return True
            for nb in _neighbors(cell):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
    else:
        for r in range(N):
            cell = (r, 0)
            if cell in stones:
                dq.append(cell)
                seen.add(cell)
        target_col = N - 1
        while dq:
            cell = dq.popleft()
            if cell[1] == target_col:
                return True
            for nb in _neighbors(cell):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
    return False


def _shortest_connection_cost(my_set: set[tuple[int, int]],
                              opp_set: set[tuple[int, int]],
                              color: str) -> int:
    """
    Dijkstra-style shortest path cost:
    - own stones cost 0
    - empty cells cost 1
    - opponent stones are blocked
    Returns minimum number of extra stones needed to complete a connection.
    """
    dist = {}
    pq = []

    def cell_cost(cell):
        if cell in opp_set:
            return INF
        if cell in my_set:
            return 0
        return 1

    if color == 'b':
        for c in range(N):
            cell = (0, c)
            w = cell_cost(cell)
            if w >= INF:
                continue
            dist[cell] = w
            heappush(pq, (w, cell))
        target = lambda cell: cell[0] == N - 1
    else:
        for r in range(N):
            cell = (r, 0)
            w = cell_cost(cell)
            if w >= INF:
                continue
            dist[cell] = w
            heappush(pq, (w, cell))
        target = lambda cell: cell[1] == N - 1

    best = INF
    while pq:
        d, cell = heappop(pq)
        if d != dist.get(cell, INF):
            continue
        if d >= best:
            continue
        if target(cell):
            best = d
            continue
        for nb in _neighbors(cell):
            w = cell_cost(nb)
            if w >= INF:
                continue
            nd = d + w
            if nd < dist.get(nb, INF):
                dist[nb] = nd
                heappush(pq, (nd, nb))

    return best


def _component_labels(stones: set[tuple[int, int]]) -> dict[tuple[int, int], int]:
    labels = {}
    comp_id = 0
    for s in stones:
        if s in labels:
            continue
        comp_id += 1
        dq = [s]
        labels[s] = comp_id
        while dq:
            cur = dq.pop()
            for nb in _neighbors(cur):
                if nb in stones and nb not in labels:
                    labels[nb] = comp_id
                    dq.append(nb)
    return labels


def _edge_bonus(move: tuple[int, int], color: str) -> float:
    r, c = move
    if color == 'b':
        return 0.6 if r == 0 or r == N - 1 else 0.0
    else:
        return 0.6 if c == 0 or c == N - 1 else 0.0


def _center_bonus(move: tuple[int, int]) -> float:
    r, c = move
    # Mild preference for central moves early/midgame.
    d = abs(r - 5) + abs(c - 5)
    return -0.08 * d


def _opening_move(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str):
    occ = me_set | opp_set
    if not occ:
        return (5, 5)

    # If center is free, it is usually strong.
    if (5, 5) not in occ:
        return (5, 5)

    # White's first move after black often benefits from a center-adjacent response.
    if color == 'w' and len(me_set) == 0:
        candidates = [(5, 4), (4, 5), (6, 5), (5, 6), (4, 6), (6, 4)]
        for mv in candidates:
            if mv not in occ:
                return mv
    return None


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occ = me_set | opp_set
    legal_moves = [cell for cell in _empties(me_set, opp_set)]

    # Absolute safety: always return something legal if possible.
    if not legal_moves:
        return (0, 0)

    opp_color = 'w' if color == 'b' else 'b'

    # Opening heuristic.
    op = _opening_move(me_set, opp_set, color)
    if op is not None and op not in occ:
        return op

    # 1) Immediate winning move.
    for mv in legal_moves:
        if _has_connection(me_set | {mv}, color):
            return mv

    # 2) Immediate block if opponent has a winning move next turn.
    opp_wins = []
    for mv in legal_moves:
        if _has_connection(opp_set | {mv}, opp_color):
            opp_wins.append(mv)

    if opp_wins:
        # If there are threats, choose a blocking move that is also best by heuristic.
        my_labels = _component_labels(me_set)
        opp_labels = _component_labels(opp_set)
        best_mv = opp_wins[0]
        best_score = -10**18
        for mv in opp_wins:
            nbrs = list(_neighbors(mv))
            own_n = sum(1 for x in nbrs if x in me_set)
            opp_n = sum(1 for x in nbrs if x in opp_set)
            own_groups = {my_labels[x] for x in nbrs if x in me_set}
            opp_groups = {opp_labels[x] for x in nbrs if x in opp_set}
            my_cost = _shortest_connection_cost(me_set | {mv}, opp_set, color)
            opp_cost = _shortest_connection_cost(opp_set, me_set | {mv}, opp_color)
            score = 7.0 * opp_cost - 8.0 * my_cost
            score += 1.2 * own_n + 0.8 * opp_n
            score += 1.6 * max(0, len(own_groups) - 1)
            score += 1.2 * max(0, len(opp_groups) - 1)
            score += _edge_bonus(mv, color) + _center_bonus(mv)
            if score > best_score:
                best_score = score
                best_mv = mv
        return best_mv

    # 3) General heuristic evaluation.
    my_labels = _component_labels(me_set)
    opp_labels = _component_labels(opp_set)

    best_move = legal_moves[0]
    best_score = -10**18

    # Precompute current path costs for scale/intuition.
    # Not strictly necessary, but helps shape the score.
    cur_my_cost = _shortest_connection_cost(me_set, opp_set, color)
    cur_opp_cost = _shortest_connection_cost(opp_set, me_set, opp_color)

    for mv in legal_moves:
        nbrs = list(_neighbors(mv))
        own_n = sum(1 for x in nbrs if x in me_set)
        opp_n = sum(1 for x in nbrs if x in opp_set)

        own_groups = {my_labels[x] for x in nbrs if x in me_set}
        opp_groups = {opp_labels[x] for x in nbrs if x in opp_set}

        my_after = me_set | {mv}
        my_cost = _shortest_connection_cost(my_after, opp_set, color)
        opp_cost = _shortest_connection_cost(opp_set, my_after, opp_color)

        # Main strategic score:
        # reduce our remaining distance, increase opponent's.
        score = 7.5 * opp_cost - 8.5 * my_cost

        # Improvement relative to current position.
        score += 1.5 * (cur_my_cost - my_cost)
        score += 1.2 * (opp_cost - cur_opp_cost)

        # Local support / disruption.
        score += 0.9 * own_n + 0.55 * opp_n

        # Connecting multiple friendly groups is very valuable.
        score += 1.8 * max(0, len(own_groups) - 1)

        # Intersecting multiple opponent groups can be useful too.
        score += 1.0 * max(0, len(opp_groups) - 1)

        # Slight preference for useful edges and center.
        score += _edge_bonus(mv, color)
        score += _center_bonus(mv)

        # Mild directional preference:
        r, c = mv
        if color == 'b':
            # Favor moves not too close to left/right extremes unless justified.
            score += -0.03 * abs(c - 5)
        else:
            # Favor moves not too close to top/bottom extremes unless justified.
            score += -0.03 * abs(r - 5)

        if score > best_score:
            best_score = score
            best_move = mv

    # Final safety: ensure legal.
    if best_move not in occ and _in_bounds(best_move[0], best_move[1]):
        return best_move

    # Guaranteed legal fallback.
    return legal_moves[0]
