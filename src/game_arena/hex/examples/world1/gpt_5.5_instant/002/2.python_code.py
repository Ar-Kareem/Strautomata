
from heapq import heappush, heappop
import math
import random

N = 11

# Hex neighbors for the coordinate convention described:
# all 8 surrounding cells except (r-1,c-1) and (r+1,c+1)
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def _has_win(stones, color):
    stones = set(stones)
    if not stones:
        return False

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
        x = stack.pop()
        if target(x):
            return True
        for y in _neighbors(*x):
            if y in stones and y not in seen:
                seen.add(y)
                stack.append(y)
    return False


def _dist_map(my_stones, opp_stones, color):
    """
    Dijkstra distance from the starting edge to every cell.
    Cost convention:
      own stone: 0
      empty: 1
      opponent: blocked
    Includes edge entry cost.
    """
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)
    INF = 10 ** 9
    dist = [[INF] * N for _ in range(N)]
    pq = []

    if color == 'b':
        starts = [(0, c) for c in range(N)]
    else:
        starts = [(r, 0) for r in range(N)]

    for r, c in starts:
        if (r, c) in opp_stones:
            continue
        cost = 0 if (r, c) in my_stones else 1
        if cost < dist[r][c]:
            dist[r][c] = cost
            heappush(pq, (cost, r, c))

    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        for nr, nc in _neighbors(r, c):
            if (nr, nc) in opp_stones:
                continue
            step = 0 if (nr, nc) in my_stones else 1
            nd = d + step
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    return dist


def _connection_distance(my_stones, opp_stones, color):
    dist = _dist_map(my_stones, opp_stones, color)
    if color == 'b':
        return min(dist[N - 1][c] for c in range(N))
    else:
        return min(dist[r][N - 1] for r in range(N))


def _two_sided_dist(my_stones, opp_stones, color):
    """
    Returns dist-from-start and dist-from-end maps.
    Useful for identifying cells on low-cost connection corridors.
    """
    d1 = _dist_map(my_stones, opp_stones, color)

    # Reverse board color edge by mirroring coordinates.
    # Simpler: compute from opposite edge with custom start.
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)
    INF = 10 ** 9
    d2 = [[INF] * N for _ in range(N)]
    pq = []

    if color == 'b':
        starts = [(N - 1, c) for c in range(N)]
    else:
        starts = [(r, N - 1) for r in range(N)]

    for r, c in starts:
        if (r, c) in opp_stones:
            continue
        cost = 0 if (r, c) in my_stones else 1
        d2[r][c] = cost
        heappush(pq, (cost, r, c))

    while pq:
        d, r, c = heappop(pq)
        if d != d2[r][c]:
            continue
        for nr, nc in _neighbors(r, c):
            if (nr, nc) in opp_stones:
                continue
            step = 0 if (nr, nc) in my_stones else 1
            nd = d + step
            if nd < d2[nr][nc]:
                d2[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    return d1, d2


def _adj_count(cell, stones):
    stones = set(stones)
    return sum((n in stones) for n in _neighbors(*cell))


def _would_win(move, me, opp, color):
    return _has_win(set(me) | {move}, color)


def _opp_color(color):
    return 'w' if color == 'b' else 'b'


def _center_score(r, c):
    # Hex board strategic center, mild preference.
    return -((r - 5) ** 2 + (c - 5) ** 2) * 0.015


def _axis_score(r, c, color):
    # Prefer cells that are central across the perpendicular axis.
    if color == 'b':
        return -abs(c - 5) * 0.045
    else:
        return -abs(r - 5) * 0.045


def _bridge_score(move, my_stones, opp_stones):
    """
    Reward common Hex virtual-connection/bridge-like geometry.
    If two friendly stones share this empty as a connector, it is valuable.
    """
    r, c = move
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)
    score = 0.0

    friendly_neighbors = 0
    for nb in _neighbors(r, c):
        if nb in my_stones:
            friendly_neighbors += 1
    score += 0.55 * friendly_neighbors

    # Distance-2 patterns with two possible shared connectors.
    bridge_pairs = [
        ((-1, 0), (0, 1)),
        ((-1, 1), (0, -1)),
        ((0, -1), (1, 0)),
        ((0, 1), (1, -1)),
        ((1, -1), (-1, 0)),
        ((1, 0), (-1, 1)),
    ]

    for a, b in bridge_pairs:
        ar, ac = r + a[0], c + a[1]
        br, bc = r + b[0], c + b[1]
        if _inside(ar, ac) and _inside(br, bc):
            if (ar, ac) in my_stones and (br, bc) in my_stones:
                score += 0.75

    return score


def _evaluate_move(move, me, opp, color, base_my_dist, base_opp_dist, my_d1, my_d2, opp_d1, opp_d2):
    opp_color = _opp_color(color)
    me_set = set(me)
    opp_set = set(opp)

    r, c = move

    new_me = me_set | {move}
    my_dist = _connection_distance(new_me, opp_set, color)

    # From opponent perspective, our new move is a blocker.
    opp_dist = _connection_distance(opp_set, new_me, opp_color)

    score = 0.0

    # Main strategic objective.
    score += 9.0 * (base_my_dist - my_dist)
    score += 7.5 * (opp_dist - base_opp_dist)

    # Absolute path quality.
    score += -1.15 * my_dist
    score += 0.85 * opp_dist

    # Corridor score: low d_start + d_end means the move lies on a shortest/near-shortest path.
    cell_own_cost = 1
    my_corridor = my_d1[r][c] + my_d2[r][c] - cell_own_cost
    opp_corridor = opp_d1[r][c] + opp_d2[r][c] - cell_own_cost

    if my_corridor < 10 ** 8:
        score += 1.5 / (1.0 + my_corridor)
    if opp_corridor < 10 ** 8:
        score += 1.35 / (1.0 + opp_corridor)

    # Local tactical shape.
    score += _bridge_score(move, me_set, opp_set)
    score += 0.42 * _adj_count(move, me_set)
    score += 0.30 * _adj_count(move, opp_set)

    # Opening/positional bias.
    score += _center_score(r, c)
    score += _axis_score(r, c, color)

    # Avoid extreme corners unless tactically justified.
    if (r in (0, N - 1)) and (c in (0, N - 1)):
        score -= 0.35

    # Slight deterministic noise to avoid predictable ties.
    score += ((r * 37 + c * 17) % 13) * 0.0007

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    legal = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]

    # Absolute fallback: required to always return legal move.
    if not legal:
        return (0, 0)

    # Strong opening choices.
    if len(occupied) == 0:
        return (5, 5)
    if len(me_set) == 0:
        for mv in [(5, 5), (5, 4), (4, 5), (6, 5), (5, 6)]:
            if mv in legal:
                return mv

    opp_color = _opp_color(color)

    # 1. Take immediate win.
    for mv in legal:
        if _would_win(mv, me_set, opp_set, color):
            return mv

    # 2. Block immediate opponent win.
    urgent_blocks = []
    for mv in legal:
        if _would_win(mv, opp_set, me_set, opp_color):
            urgent_blocks.append(mv)
    if urgent_blocks:
        # Choose the block that is also best for us.
        base_my_dist = _connection_distance(me_set, opp_set, color)
        base_opp_dist = _connection_distance(opp_set, me_set, opp_color)
        my_d1, my_d2 = _two_sided_dist(me_set, opp_set, color)
        opp_d1, opp_d2 = _two_sided_dist(opp_set, me_set, opp_color)
        return max(
            urgent_blocks,
            key=lambda mv: _evaluate_move(
                mv, me_set, opp_set, color,
                base_my_dist, base_opp_dist,
                my_d1, my_d2, opp_d1, opp_d2
            )
        )

    base_my_dist = _connection_distance(me_set, opp_set, color)
    base_opp_dist = _connection_distance(opp_set, me_set, opp_color)

    my_d1, my_d2 = _two_sided_dist(me_set, opp_set, color)
    opp_d1, opp_d2 = _two_sided_dist(opp_set, me_set, opp_color)

    # Limit candidate set for speed? Board is only 121 cells, so full scan is fine.
    best_move = legal[0]
    best_score = -10 ** 18

    for mv in legal:
        sc = _evaluate_move(
            mv, me_set, opp_set, color,
            base_my_dist, base_opp_dist,
            my_d1, my_d2, opp_d1, opp_d2
        )
        if sc > best_score:
            best_score = sc
            best_move = mv

    # Final legality guard.
    if best_move not in occupied and _inside(*best_move):
        return best_move

    return legal[0]
