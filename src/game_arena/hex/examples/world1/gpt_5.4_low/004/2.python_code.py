
from __future__ import annotations

from heapq import heappush, heappop
from collections import deque

N = 11
INF = 10**9

# Hex neighbors for coordinates described in the prompt:
# all 8 surrounding cells except (r-1,c-1) and (r+1,c+1)
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def side_start_cells(color: str):
    if color == 'b':
        return [(0, c) for c in range(N)]
    else:
        return [(r, 0) for r in range(N)]


def is_goal_cell(r: int, c: int, color: str) -> bool:
    if color == 'b':
        return r == N - 1
    else:
        return c == N - 1


def connected_win(stones: set[tuple[int, int]], color: str) -> bool:
    dq = deque()
    seen = set()

    if color == 'b':
        for c in range(N):
            cell = (0, c)
            if cell in stones:
                dq.append(cell)
                seen.add(cell)
        while dq:
            r, c = dq.popleft()
            if r == N - 1:
                return True
            for nr, nc in neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    dq.append((nr, nc))
    else:
        for r in range(N):
            cell = (r, 0)
            if cell in stones:
                dq.append(cell)
                seen.add(cell)
        while dq:
            r, c = dq.popleft()
            if c == N - 1:
                return True
            for nr, nc in neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    dq.append((nr, nc))
    return False


def shortest_path_cost(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str) -> int:
    dist = [[INF] * N for _ in range(N)]
    pq = []

    for r, c in side_start_cells(color):
        if (r, c) in opp_set:
            continue
        start_cost = 0 if (r, c) in me_set else 1
        if start_cost < dist[r][c]:
            dist[r][c] = start_cost
            heappush(pq, (start_cost, r, c))

    best = INF
    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        if is_goal_cell(r, c, color):
            best = d
            break
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                continue
            w = 0 if (nr, nc) in me_set else 1
            nd = d + w
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))
    return best


def shortest_path_maps(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str):
    # Forward distances from starting side
    dist_start = [[INF] * N for _ in range(N)]
    pq = []

    for r, c in side_start_cells(color):
        if (r, c) in opp_set:
            continue
        start_cost = 0 if (r, c) in me_set else 1
        if start_cost < dist_start[r][c]:
            dist_start[r][c] = start_cost
            heappush(pq, (start_cost, r, c))

    while pq:
        d, r, c = heappop(pq)
        if d != dist_start[r][c]:
            continue
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                continue
            w = 0 if (nr, nc) in me_set else 1
            nd = d + w
            if nd < dist_start[nr][nc]:
                dist_start[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    # Reverse distances from goal side
    dist_goal = [[INF] * N for _ in range(N)]
    pq = []

    if color == 'b':
        goals = [(N - 1, c) for c in range(N)]
    else:
        goals = [(r, N - 1) for r in range(N)]

    for r, c in goals:
        if (r, c) in opp_set:
            continue
        start_cost = 0 if (r, c) in me_set else 1
        if start_cost < dist_goal[r][c]:
            dist_goal[r][c] = start_cost
            heappush(pq, (start_cost, r, c))

    while pq:
        d, r, c = heappop(pq)
        if d != dist_goal[r][c]:
            continue
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set:
                continue
            w = 0 if (nr, nc) in me_set else 1
            nd = d + w
            if nd < dist_goal[nr][nc]:
                dist_goal[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    best = INF
    for r in range(N):
        for c in range(N):
            if dist_start[r][c] < INF and dist_goal[r][c] < INF:
                cost_here = 0 if (r, c) in me_set else 1
                total = dist_start[r][c] + dist_goal[r][c] - cost_here
                if total < best:
                    best = total

    return dist_start, dist_goal, best


def centrality_score(r: int, c: int) -> float:
    # Prefer the center region
    return -0.12 * ((r - 5) ** 2 + (c - 5) ** 2)


def edge_progress_score(r: int, c: int, color: str) -> float:
    # Slight preference for positions that are well-placed along the needed axis,
    # but still keep central bias.
    if color == 'b':
        return -0.03 * abs(c - 5)
    else:
        return -0.03 * abs(r - 5)


def local_shape_score(move: tuple[int, int], me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]], color: str) -> float:
    r, c = move
    score = 0.0

    own_adj = 0
    opp_adj = 0
    for nr, nc in neighbors(r, c):
        if (nr, nc) in me_set:
            own_adj += 1
        elif (nr, nc) in opp_set:
            opp_adj += 1

    score += 0.55 * own_adj
    score += 0.18 * opp_adj

    # Reward extending in useful directions
    if color == 'b':
        axial = [(-1, 0), (1, 0), (-1, 1), (1, -1)]
    else:
        axial = [(0, -1), (0, 1), (-1, 1), (1, -1)]

    aligned = 0
    for dr, dc in axial:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc) and (nr, nc) in me_set:
            aligned += 1
    score += 0.22 * aligned

    score += centrality_score(r, c)
    score += edge_progress_score(r, c, color)
    return score


def first_legal(me_set: set[tuple[int, int]], opp_set: set[tuple[int, int]]) -> tuple[int, int]:
    occupied = me_set | opp_set
    for r in range(N):
        for c in range(N):
            if (r, c) not in occupied:
                return (r, c)
    return (0, 0)  # Should never happen on a legal non-full board


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    legal_moves = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
    if not legal_moves:
        return (0, 0)

    opp_color = 'w' if color == 'b' else 'b'

    # Opening preference
    if not me_set and not opp_set:
        return (5, 5)
    if len(occupied) == 1:
        if (5, 5) not in occupied:
            return (5, 5)
        for mv in [(5, 4), (4, 5), (5, 6), (6, 5), (4, 6), (6, 4)]:
            if mv not in occupied:
                return mv

    # 1) Immediate winning move
    winning_moves = []
    for mv in legal_moves:
        if connected_win(me_set | {mv}, color):
            winning_moves.append(mv)
    if winning_moves:
        # Choose the most central/aligned if multiple
        best_mv = max(winning_moves, key=lambda m: local_shape_score(m, me_set, opp_set, color))
        return best_mv

    # 2) Immediate block of opponent winning move
    opp_winning_moves = []
    for mv in legal_moves:
        if connected_win(opp_set | {mv}, opp_color):
            opp_winning_moves.append(mv)
    if opp_winning_moves:
        best_mv = max(
            opp_winning_moves,
            key=lambda m: local_shape_score(m, me_set, opp_set, color)
        )
        return best_mv

    # Baseline path values
    my_base = shortest_path_cost(me_set, opp_set, color)
    opp_base = shortest_path_cost(opp_set, me_set, opp_color)

    # Maps for shortest-route bonuses
    my_ds, my_dg, my_best = shortest_path_maps(me_set, opp_set, color)
    op_ds, op_dg, op_best = shortest_path_maps(opp_set, me_set, opp_color)

    best_score = -10**18
    best_move = legal_moves[0]

    for mv in legal_moves:
        r, c = mv

        my_after_set = me_set | {mv}
        my_after = shortest_path_cost(my_after_set, opp_set, color)
        opp_after = shortest_path_cost(opp_set, my_after_set, opp_color)

        score = 0.0

        # Main strategic terms
        score += 8.0 * (my_base - my_after)
        score += 6.5 * (opp_after - opp_base)

        # Prefer moves that put us on current shortest routes
        if my_ds[r][c] < INF and my_dg[r][c] < INF:
            through = my_ds[r][c] + my_dg[r][c] - 1
            if through == my_best:
                score += 2.2
            else:
                score += max(0.0, 1.0 - 0.25 * (through - my_best))

        # Prefer moves that disrupt opponent shortest routes
        if op_ds[r][c] < INF and op_dg[r][c] < INF:
            through_opp = op_ds[r][c] + op_dg[r][c] - 1
            if through_opp == op_best:
                score += 2.0
            else:
                score += max(0.0, 0.8 - 0.2 * (through_opp - op_best))

        # Local shape / centrality
        score += local_shape_score(mv, me_set, opp_set, color)

        # Small edge bonuses for touching own target borders
        if color == 'b':
            if r == 0 or r == N - 1:
                score += 0.35
        else:
            if c == 0 or c == N - 1:
                score += 0.35

        # Tiebreak toward lexicographically earlier only very slightly negative
        score += -1e-6 * (r * N + c)

        if score > best_score:
            best_score = score
            best_move = mv

    # Safety: always return legal move
    if best_move in occupied or not in_bounds(best_move[0], best_move[1]):
        return first_legal(me_set, opp_set)
    return best_move
