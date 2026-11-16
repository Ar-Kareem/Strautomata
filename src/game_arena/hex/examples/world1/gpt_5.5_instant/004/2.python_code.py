
from heapq import heappush, heappop
import math

N = 11
DIRS = ((0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0))


def _neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def _is_win(stones, color):
    stones = set(stones)
    if not stones:
        return False

    stack = []
    seen = set()

    if color == "b":
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


def _dist_map(my, enemy, color):
    """
    Dijkstra from one edge to every cell.
    Cost of entering own stone: 0. Empty: 1. Enemy: blocked.
    Returns dist matrix and best total connection distance.
    """
    my = set(my)
    enemy = set(enemy)
    inf = 10 ** 9
    dist = [[inf] * N for _ in range(N)]
    pq = []

    def enter_cost(cell):
        if cell in enemy:
            return inf
        return 0 if cell in my else 1

    if color == "b":
        for c in range(N):
            cell = (0, c)
            cost = enter_cost(cell)
            if cost < inf:
                dist[0][c] = cost
                heappush(pq, (cost, 0, c))
    else:
        for r in range(N):
            cell = (r, 0)
            cost = enter_cost(cell)
            if cost < inf:
                dist[r][0] = cost
                heappush(pq, (cost, r, 0))

    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        for nr, nc in _neighbors(r, c):
            cost = enter_cost((nr, nc))
            if cost >= inf:
                continue
            nd = d + cost
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    if color == "b":
        best = min(dist[N - 1][c] for c in range(N))
    else:
        best = min(dist[r][N - 1] for r in range(N))
    return dist, best


def _two_sided_distance(my, enemy, color):
    """
    Approximate connection value for each empty/own cell by combining distances
    from both target edges. Lower is better.
    """
    d1, best1 = _dist_map(my, enemy, color)

    # Mirror board/color target by running Dijkstra from opposite edge manually.
    my = set(my)
    enemy = set(enemy)
    inf = 10 ** 9
    d2 = [[inf] * N for _ in range(N)]
    pq = []

    def enter_cost(cell):
        if cell in enemy:
            return inf
        return 0 if cell in my else 1

    if color == "b":
        for c in range(N):
            cell = (N - 1, c)
            cost = enter_cost(cell)
            if cost < inf:
                d2[N - 1][c] = cost
                heappush(pq, (cost, N - 1, c))
    else:
        for r in range(N):
            cell = (r, N - 1)
            cost = enter_cost(cell)
            if cost < inf:
                d2[r][N - 1] = cost
                heappush(pq, (cost, r, N - 1))

    while pq:
        d, r, c = heappop(pq)
        if d != d2[r][c]:
            continue
        for nr, nc in _neighbors(r, c):
            cost = enter_cost((nr, nc))
            if cost >= inf:
                continue
            nd = d + cost
            if nd < d2[nr][nc]:
                d2[nr][nc] = nd
                heappush(pq, (nd, nr, nc))

    if color == "b":
        best2 = min(d2[0][c] for c in range(N))
    else:
        best2 = min(d2[r][0] for r in range(N))

    return d1, d2, min(best1, best2)


def _local_score(cell, my, opp, color):
    r, c = cell
    my = set(my)
    opp = set(opp)

    score = 0.0

    friendly = 0
    enemy = 0
    empty = 0
    for nb in _neighbors(r, c):
        if nb in my:
            friendly += 1
        elif nb in opp:
            enemy += 1
        else:
            empty += 1

    score += 1.9 * friendly
    score += 0.8 * enemy
    score += 0.15 * empty

    # Edge affinity for own goal edges, but avoid hugging side edges too much.
    if color == "b":
        score += 0.55 if r in (0, N - 1) else 0.0
        score -= 0.18 * (abs(c - 5) / 5.0)
        score += 0.22 * (1.0 - abs(r - 5) / 5.0)
    else:
        score += 0.55 if c in (0, N - 1) else 0.0
        score -= 0.18 * (abs(r - 5) / 5.0)
        score += 0.22 * (1.0 - abs(c - 5) / 5.0)

    # Prefer center early.
    score += 0.45 * (1.0 - (abs(r - 5) + abs(c - 5)) / 10.0)

    # Hex bridge patterns: if two friendly stones share this as a common connector,
    # this move is valuable.
    bridge_pairs = [
        ((-1, 0), (0, 1)),
        ((-1, 1), (0, -1)),
        ((0, -1), (1, -1)),
        ((0, 1), (1, 0)),
        ((1, -1), (-1, 0)),
        ((1, 0), (-1, 1)),
    ]
    for (a, b) in bridge_pairs:
        ar, ac = r + a[0], c + a[1]
        br, bc = r + b[0], c + b[1]
        if 0 <= ar < N and 0 <= ac < N and 0 <= br < N and 0 <= bc < N:
            if (ar, ac) in my and (br, bc) in my:
                score += 2.7
            if (ar, ac) in opp and (br, bc) in opp:
                score += 2.0

    return score


def _candidate_moves(me, opp):
    occupied = set(me) | set(opp)
    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
    if not empties:
        return []

    if len(occupied) <= 1:
        for move in [(5, 5), (5, 4), (4, 5), (6, 5), (5, 6)]:
            if move not in occupied:
                return [move]

    cand = set()
    for s in occupied:
        r, c = s
        cand.add(s)
        for nb in _neighbors(r, c):
            cand.add(nb)
            for nb2 in _neighbors(*nb):
                cand.add(nb2)

    cand = [x for x in cand if 0 <= x[0] < N and 0 <= x[1] < N and x not in occupied]

    # If candidate set is somehow too small, add central empties.
    if len(cand) < 12:
        center_sorted = sorted(
            empties,
            key=lambda x: (abs(x[0] - 5) + abs(x[1] - 5), abs(x[0] - x[1]))
        )
        cand.extend(center_sorted[:20])

    # Limit for speed, using rough centrality.
    cand = list(dict.fromkeys(cand))
    if len(cand) > 70:
        cand.sort(key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))
        cand = cand[:70]
    return cand


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    occupied = set(me) | set(opp)
    legal = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]
    if not legal:
        return (0, 0)  # Should never happen in a legal game.

    opp_color = "w" if color == "b" else "b"

    # Strong deterministic opening.
    if not occupied:
        return (5, 5)
    if len(occupied) == 1 and (5, 5) not in occupied:
        return (5, 5)

    candidates = _candidate_moves(me, opp)
    if not candidates:
        return legal[0]

    # Immediate win.
    for mv in candidates:
        if _is_win(set(me) | {mv}, color):
            return mv

    # Must block opponent immediate win.
    opp_winners = []
    for mv in candidates:
        if _is_win(set(opp) | {mv}, opp_color):
            opp_winners.append(mv)
    if opp_winners:
        # Choose the blocking point that is also best for us.
        d_me_a, d_me_b, _ = _two_sided_distance(me, opp, color)
        return min(
            opp_winners,
            key=lambda x: d_me_a[x[0]][x[1]] + d_me_b[x[0]][x[1]] + 0.01 * (abs(x[0] - 5) + abs(x[1] - 5))
        )

    my_d1, my_d2, my_base = _two_sided_distance(me, opp, color)
    op_d1, op_d2, op_base = _two_sided_distance(opp, me, opp_color)

    best_move = candidates[0]
    best_score = -10 ** 18

    for mv in candidates:
        r, c = mv

        # Tactical path importance before full re-evaluation.
        my_path_value = -(my_d1[r][c] + my_d2[r][c])
        op_path_value = -(op_d1[r][c] + op_d2[r][c])

        new_my_dist = _dist_map(set(me) | {mv}, opp, color)[1]
        new_op_dist = _dist_map(opp, set(me) | {mv}, opp_color)[1]

        improve = my_base - new_my_dist
        block = new_op_dist - op_base

        score = 0.0
        score += 11.5 * improve
        score += 9.0 * block
        score += 1.35 * my_path_value
        score += 1.10 * op_path_value
        score += _local_score(mv, me, opp, color)

        # Prefer moves on cells that lie on both our and opponent's shortest corridors.
        if my_d1[r][c] < 10 ** 8 and my_d2[r][c] < 10 ** 8:
            score += 3.0 / (1.0 + my_d1[r][c] + my_d2[r][c])
        if op_d1[r][c] < 10 ** 8 and op_d2[r][c] < 10 ** 8:
            score += 2.6 / (1.0 + op_d1[r][c] + op_d2[r][c])

        # Tiny deterministic tie breaker.
        score += ((r * 13 + c * 7) % 17) * 1e-5

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move not in occupied and 0 <= best_move[0] < N and 0 <= best_move[1] < N:
        return best_move

    # Absolute safety fallback.
    return legal[0]
