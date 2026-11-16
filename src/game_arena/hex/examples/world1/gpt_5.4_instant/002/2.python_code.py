
from __future__ import annotations

from heapq import heappush, heappop

N = 11

# Hex neighbors for coordinate system described in prompt:
# touching cells are all 8 grid neighbors except (r-1,c-1) and (r+1,c+1)
DIRS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def legal_moves(me_set, opp_set):
    occ = me_set | opp_set
    for r in range(N):
        for c in range(N):
            if (r, c) not in occ:
                yield (r, c)


def edge_dist(cell, color):
    r, c = cell
    if color == 'b':
        return min(r, N - 1 - r)
    return min(c, N - 1 - c)


def center_dist(cell):
    r, c = cell
    cr = cc = (N - 1) / 2.0
    return abs(r - cr) + abs(c - cc)


def has_connection(me_set, color: str) -> bool:
    """Check if me_set already connects the player's two sides."""
    stack = []
    seen = set()

    if color == 'b':
        for c in range(N):
            if (0, c) in me_set:
                stack.append((0, c))
                seen.add((0, c))
        target_row = N - 1
        while stack:
            r, c = stack.pop()
            if r == target_row:
                return True
            for nb in neighbors(r, c):
                if nb in me_set and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    else:
        for r in range(N):
            if (r, 0) in me_set:
                stack.append((r, 0))
                seen.add((r, 0))
        target_col = N - 1
        while stack:
            r, c = stack.pop()
            if c == target_col:
                return True
            for nb in neighbors(r, c):
                if nb in me_set and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return False


def dijkstra_connection_cost(me_set, opp_set, color: str) -> float:
    """
    Estimate connection cost for color:
    own stones cost 0, empty cells cost 1, opponent stones blocked.
    Returns minimal cost to connect the two goal sides.
    """
    INF = 10**9
    dist = {}
    pq = []

    occupied_opp = opp_set
    occupied_me = me_set

    def cell_cost(cell):
        if cell in occupied_opp:
            return None
        if cell in occupied_me:
            return 0
        return 1

    if color == 'b':
        for c in range(N):
            cell = (0, c)
            cc = cell_cost(cell)
            if cc is not None:
                dist[cell] = cc
                heappush(pq, (cc, cell))
        while pq:
            d, cell = heappop(pq)
            if d != dist.get(cell, INF):
                continue
            r, _ = cell
            if r == N - 1:
                return d
            for nb in neighbors(*cell):
                cc = cell_cost(nb)
                if cc is None:
                    continue
                nd = d + cc
                if nd < dist.get(nb, INF):
                    dist[nb] = nd
                    heappush(pq, (nd, nb))
    else:
        for r in range(N):
            cell = (r, 0)
            cc = cell_cost(cell)
            if cc is not None:
                dist[cell] = cc
                heappush(pq, (cc, cell))
        while pq:
            d, cell = heappop(pq)
            if d != dist.get(cell, INF):
                continue
            _, c = cell
            if c == N - 1:
                return d
            for nb in neighbors(*cell):
                cc = cell_cost(nb)
                if cc is None:
                    continue
                nd = d + cc
                if nd < dist.get(nb, INF):
                    dist[nb] = nd
                    heappush(pq, (nd, nb))
    return INF


def component_sizes(me_set):
    comp_id = {}
    sizes = []
    cid = 0
    for cell in me_set:
        if cell in comp_id:
            continue
        stack = [cell]
        comp_id[cell] = cid
        size = 0
        while stack:
            cur = stack.pop()
            size += 1
            for nb in neighbors(*cur):
                if nb in me_set and nb not in comp_id:
                    comp_id[nb] = cid
                    stack.append(nb)
        sizes.append(size)
        cid += 1
    return comp_id, sizes


def bridge_score(move, me_set):
    """
    Reward moves that connect multiple friendly neighbors/components
    and create robust local structure.
    """
    nbs = list(neighbors(*move))
    friendly = [x for x in nbs if x in me_set]
    score = 0.0

    # Direct friendly adjacencies
    score += 2.2 * len(friendly)

    # Distinct connected components touched
    if friendly:
        comp_id, _ = component_sizes(me_set)
        touched = {comp_id[x] for x in friendly}
        if len(touched) >= 2:
            score += 4.5 * (len(touched) - 1)

    # Virtual-connection-ish local support:
    # reward nearby two-step friendly structures around the move
    seen2 = set()
    for nb in nbs:
        for nn in neighbors(*nb):
            if nn != move and nn in me_set:
                seen2.add(nn)
    score += 0.25 * len(seen2)

    return score


def side_progress_score(move, color):
    r, c = move
    # reward progress toward both of our target sides and central lane
    if color == 'b':
        toward_sides = 5 - abs(r - 5)
        lane = 5 - abs(c - 5)
    else:
        toward_sides = 5 - abs(c - 5)
        lane = 5 - abs(r - 5)
    return 0.9 * toward_sides + 0.5 * lane


def disruption_score(move, opp_set):
    """
    Reward adjacency to opponent stones, especially if touching multiple.
    """
    cnt = 0
    for nb in neighbors(*move):
        if nb in opp_set:
            cnt += 1
    return 1.1 * cnt


def opening_book(me_set, opp_set, color):
    occupied = me_set | opp_set
    total = len(occupied)
    if total == 0:
        return (5, 5)

    # Strong early central / near-central choices
    prefs = [
        (5, 5), (5, 4), (4, 5), (6, 5), (5, 6),
        (4, 6), (6, 4), (4, 4), (6, 6),
        (5, 3), (3, 5), (7, 5), (5, 7),
    ]

    # Slight orientation preference
    if color == 'b':
        prefs = [(5, 5), (4, 5), (6, 5), (5, 4), (5, 6), (3, 5), (7, 5), (4, 6), (6, 4)]
    else:
        prefs = [(5, 5), (5, 4), (5, 6), (4, 5), (6, 5), (5, 3), (5, 7), (4, 6), (6, 4)]

    for mv in prefs:
        if mv not in occupied:
            return mv
    return None


def evaluate_move(move, me_set, opp_set, color):
    my_after = set(me_set)
    my_after.add(move)

    # Immediate win already handled outside, but keep huge bonus if so
    if has_connection(my_after, color):
        return 1e9

    opp_color = 'w' if color == 'b' else 'b'

    my_cost_before = dijkstra_connection_cost(me_set, opp_set, color)
    my_cost_after = dijkstra_connection_cost(my_after, opp_set, color)

    opp_cost_before = dijkstra_connection_cost(opp_set, me_set, opp_color)
    opp_cost_after = dijkstra_connection_cost(opp_set, my_after, opp_color)

    improve_self = my_cost_before - my_cost_after
    hinder_opp = opp_cost_after - opp_cost_before

    score = 0.0
    score += 9.0 * improve_self
    score += 6.5 * hinder_opp
    score += bridge_score(move, me_set)
    score += side_progress_score(move, color)
    score += disruption_score(move, opp_set)

    # Prefer centrality mildly
    score -= 0.18 * center_dist(move)

    # Prefer moves not too close to only one edge
    score -= 0.05 * edge_dist(move, color)

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occ = me_set | opp_set

    # Fallback legal move in all cases
    fallback = None
    for mv in legal_moves(me_set, opp_set):
        fallback = mv
        break
    if fallback is None:
        return (0, 0)  # Should never happen in legal Hex states

    # Opening move preferences
    ob = opening_book(me_set, opp_set, color)
    if ob is not None and ob not in occ:
        return ob

    empties = list(legal_moves(me_set, opp_set))

    # 1. Immediate winning move
    for mv in empties:
        s = set(me_set)
        s.add(mv)
        if has_connection(s, color):
            return mv

    # 2. Block opponent's immediate winning move(s)
    opp_color = 'w' if color == 'b' else 'b'
    opp_wins = []
    for mv in empties:
        s = set(opp_set)
        s.add(mv)
        if has_connection(s, opp_color):
            opp_wins.append(mv)
    if opp_wins:
        # If multiple, choose one that also helps us most
        best = None
        best_score = -10**18
        for mv in opp_wins:
            sc = evaluate_move(mv, me_set, opp_set, color)
            if sc > best_score:
                best_score = sc
                best = mv
        return best if best is not None else opp_wins[0]

    # 3. General evaluation
    best = fallback
    best_score = -10**18
    for mv in empties:
        sc = evaluate_move(mv, me_set, opp_set, color)
        if sc > best_score:
            best_score = sc
            best = mv

    # Always legal
    if best in occ or not (0 <= best[0] < N and 0 <= best[1] < N):
        return fallback
    return best
