
from heapq import heappush, heappop
import math
import random

N = 11

# Hex neighbors per prompt:
# all 8 surrounding grid cells except (r-1,c-1) and (r+1,c+1)
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def _first_empty(occupied):
    # Prefer center fallback, then scan.
    order = [(5, 5)]
    for r in range(N):
        for c in range(N):
            if (r, c) != (5, 5):
                order.append((r, c))
    for mv in order:
        if mv not in occupied:
            return mv
    return (0, 0)  # Should never happen in a legal non-full game.


def _has_connection(stones, color):
    """Check if stones of color connect their required sides."""
    if not stones:
        return False
    stones = set(stones)
    stack = []
    seen = set()

    if color == 'b':
        for c in range(N):
            if (0, c) in stones:
                stack.append((0, c))
                seen.add((0, c))
        target = lambda x: x[0] == N - 1
    else:
        for r in range(N):
            if (r, 0) in stones:
                stack.append((r, 0))
                seen.add((r, 0))
        target = lambda x: x[1] == N - 1

    while stack:
        cell = stack.pop()
        if target(cell):
            return True
        for nb in _neighbors(*cell):
            if nb in stones and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def _shortest_distance(my_stones, opp_stones, color):
    """
    Minimum number of empty cells needed to complete a connection.
    Friendly stones cost 0, empty cells cost 1, opponent stones blocked.
    """
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)

    dist = [[10**9] * N for _ in range(N)]
    pq = []

    if color == 'b':
        # Connect top to bottom.
        for c in range(N):
            cell = (0, c)
            if cell in opp_stones:
                continue
            cost = 0 if cell in my_stones else 1
            dist[0][c] = cost
            heappush(pq, (cost, 0, c))
        is_target = lambda r, c: r == N - 1
    else:
        # Connect left to right.
        for r in range(N):
            cell = (r, 0)
            if cell in opp_stones:
                continue
            cost = 0 if cell in my_stones else 1
            dist[r][0] = cost
            heappush(pq, (cost, r, 0))
        is_target = lambda r, c: c == N - 1

    best = 10**9
    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        if is_target(r, c):
            best = d
            break
        for nr, nc in _neighbors(r, c):
            if (nr, nc) in opp_stones:
                continue
            nd = d + (0 if (nr, nc) in my_stones else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))
    return best


def _distance_map_from_start(my_stones, opp_stones, color, reverse=False):
    """
    Dijkstra distance from one side. Used to identify cells on/near shortest paths.
    reverse=False: top/left side. reverse=True: bottom/right side.
    """
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)
    dist = [[10**9] * N for _ in range(N)]
    pq = []

    if color == 'b':
        row = N - 1 if reverse else 0
        for c in range(N):
            cell = (row, c)
            if cell in opp_stones:
                continue
            cost = 0 if cell in my_stones else 1
            dist[row][c] = cost
            heappush(pq, (cost, row, c))
    else:
        col = N - 1 if reverse else 0
        for r in range(N):
            cell = (r, col)
            if cell in opp_stones:
                continue
            cost = 0 if cell in my_stones else 1
            dist[r][col] = cost
            heappush(pq, (cost, r, col))

    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        for nr, nc in _neighbors(r, c):
            if (nr, nc) in opp_stones:
                continue
            nd = d + (0 if (nr, nc) in my_stones else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))
    return dist


def _orientation_center_bonus(move, color):
    r, c = move
    # General center bonus, but avoid being too timid: Hex likes central templates.
    center = 5
    euclid = abs(r - center) + abs(c - center)
    bonus = 12.0 - 1.25 * euclid

    # Slight preference for the central "river" in own connection direction.
    if color == 'b':
        bonus += 2.0 - 0.35 * abs(c - center)
    else:
        bonus += 2.0 - 0.35 * abs(r - center)
    return bonus


def _local_shape_bonus(move, my_stones, opp_stones, color):
    r, c = move
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)
    bonus = 0.0

    friendly_neighbors = 0
    enemy_neighbors = 0
    empty_neighbors = 0
    for nb in _neighbors(r, c):
        if nb in my_stones:
            friendly_neighbors += 1
        elif nb in opp_stones:
            enemy_neighbors += 1
        else:
            empty_neighbors += 1

    # Connecting to existing stones matters, but over-clumping is not ideal.
    bonus += 7.0 * friendly_neighbors
    if friendly_neighbors >= 2:
        bonus += 5.0
    if friendly_neighbors >= 4:
        bonus -= 5.0

    # Blocking/touching opponent is often valuable in Hex.
    bonus += 3.5 * enemy_neighbors

    # Edge relevance.
    if color == 'b':
        if r == 0 or r == N - 1:
            bonus += 4.0
        # Do not overvalue left/right side for black.
        if c == 0 or c == N - 1:
            bonus -= 1.0
    else:
        if c == 0 or c == N - 1:
            bonus += 4.0
        if r == 0 or r == N - 1:
            bonus -= 1.0

    # Common loose bridge patterns. If playing this cell supports a two-point
    # diagonal/knight-like virtual connection, add a modest bonus.
    bridge_pairs = [
        ((-1, 0), (0, -1)),
        ((-1, 1), (0, 1)),
        ((1, -1), (0, -1)),
        ((1, 0), (0, 1)),
        ((-1, 0), (-1, 1)),
        ((1, -1), (1, 0)),
    ]
    for a, b in bridge_pairs:
        ar, ac = r + a[0], c + a[1]
        br, bc = r + b[0], c + b[1]
        if _inside(ar, ac) and _inside(br, bc):
            if (ar, ac) in my_stones and (br, bc) in my_stones:
                bonus += 5.0

    return bonus


def _opponent_color(color):
    return 'w' if color == 'b' else 'b'


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    try:
        me_set = set(me)
        opp_set = set(opp)
        occupied = me_set | opp_set
        legal = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
        if not legal:
            return (0, 0)

        # Opening: take center or near-center.
        if len(occupied) == 0:
            return (5, 5)
        if (5, 5) in legal and len(occupied) <= 2:
            return (5, 5)

        opp_color = _opponent_color(color)

        # Immediate win.
        for mv in legal:
            if _has_connection(me_set | {mv}, color):
                return mv

        # Immediate block if opponent has a winning move.
        opp_wins = []
        for mv in legal:
            if _has_connection(opp_set | {mv}, opp_color):
                opp_wins.append(mv)
        if opp_wins:
            # If multiple, pick the one that is also best for our path.
            best_block = opp_wins[0]
            best_d = 10**9
            for mv in opp_wins:
                d = _shortest_distance(me_set | {mv}, opp_set, color)
                if d < best_d:
                    best_d = d
                    best_block = mv
            return best_block

        base_my_dist = _shortest_distance(me_set, opp_set, color)
        base_opp_dist = _shortest_distance(opp_set, me_set, opp_color)

        my_start = _distance_map_from_start(me_set, opp_set, color, reverse=False)
        my_end = _distance_map_from_start(me_set, opp_set, color, reverse=True)
        op_start = _distance_map_from_start(opp_set, me_set, opp_color, reverse=False)
        op_end = _distance_map_from_start(opp_set, me_set, opp_color, reverse=True)

        best_score = -10**18
        best_moves = []

        for mv in legal:
            r, c = mv

            # Shortest path effects after playing move.
            nd_my = _shortest_distance(me_set | {mv}, opp_set, color)
            nd_opp = _shortest_distance(opp_set, me_set | {mv}, opp_color)

            score = 0.0

            # Primary: improve our connection and damage opponent connection.
            score += 95.0 * (base_my_dist - nd_my)
            score += 82.0 * (nd_opp - base_opp_dist)

            # Absolute path quality.
            score += 35.0 / max(1, nd_my)
            score += 22.0 * nd_opp / 10.0

            # Cells that lie on shortest corridors are very important.
            mv_cost_my = 1  # currently empty
            through_my = my_start[r][c] + my_end[r][c] - mv_cost_my
            through_op = op_start[r][c] + op_end[r][c] - 1

            if through_my < 10**8:
                score += 30.0 / max(1, through_my)
                if through_my <= base_my_dist:
                    score += 22.0
                elif through_my == base_my_dist + 1:
                    score += 10.0

            if through_op < 10**8:
                score += 26.0 / max(1, through_op)
                if through_op <= base_opp_dist:
                    score += 26.0
                elif through_op == base_opp_dist + 1:
                    score += 10.0

            score += _orientation_center_bonus(mv, color)
            score += _local_shape_bonus(mv, me_set, opp_set, color)

            # Urgency: if opponent is close, blocking gets more weight.
            if base_opp_dist <= 2:
                score += 60.0 * (nd_opp - base_opp_dist)
                if through_op <= base_opp_dist:
                    score += 45.0

            # Finish strongly when our connection is close.
            if nd_my <= 2:
                score += 35.0

            # Deterministic tiny tie-breaker favoring central cells.
            score -= 0.001 * (abs(r - 5) + abs(c - 5))

            if score > best_score + 1e-9:
                best_score = score
                best_moves = [mv]
            elif abs(score - best_score) <= 1e-9:
                best_moves.append(mv)

        if best_moves:
            # Deterministic choice among ties.
            best_moves.sort(key=lambda x: (abs(x[0] - 5) + abs(x[1] - 5), x[0], x[1]))
            return best_moves[0]

        return _first_empty(occupied)

    except Exception:
        # Absolute safety: never fail to return a legal move if possible.
        occupied = set(me) | set(opp)
        return _first_empty(occupied)
