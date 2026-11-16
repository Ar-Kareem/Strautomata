
from heapq import heappush, heappop
from math import inf

N = 11

DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]

    if not empties:
        return (0, 0)

    # Opening preference: center or near-center.
    if len(occupied) == 0:
        return (5, 5)

    # If center is available early, it is usually strong.
    if len(occupied) <= 2 and (5, 5) in empties:
        return (5, 5)

    opp_color = "w" if color == "b" else "b"

    # 1. Win immediately if possible.
    for mv in ordered_by_center(empties):
        if is_win(me_set | {mv}, color):
            return mv

    # 2. Block opponent's immediate win.
    opp_winning_moves = []
    for mv in empties:
        if is_win(opp_set | {mv}, opp_color):
            opp_winning_moves.append(mv)

    if opp_winning_moves:
        # If multiple blocks exist, choose the one that is also best for us.
        return max(
            opp_winning_moves,
            key=lambda m: move_static_score(m, me_set, opp_set, color)
        )

    # Current distances for comparison.
    my_current_dist = shortest_connection(me_set, opp_set, color)
    opp_current_dist = shortest_connection(opp_set, me_set, opp_color)

    best_move = empties[0]
    best_score = -10**18

    # Score all legal moves.
    for mv in empties:
        new_me = me_set | {mv}

        my_dist = shortest_connection(new_me, opp_set, color)
        opp_dist = shortest_connection(opp_set, new_me, opp_color)

        # How good would this cell be for opponent if we do not take it?
        opp_if_they_take = shortest_connection(opp_set | {mv}, me_set, opp_color)

        score = 0.0

        # Main strategic objective.
        score += 120.0 * (my_current_dist - my_dist)
        score += 95.0 * (opp_dist - opp_current_dist)

        # Blocking urgent opponent paths.
        score += 75.0 * (opp_current_dist - opp_if_they_take)

        # Absolute distance priorities.
        score += -45.0 * my_dist
        score += 32.0 * opp_dist

        # Local shape / center / connection heuristics.
        score += move_static_score(mv, me_set, opp_set, color)

        # Prefer moves on relevant axis.
        r, c = mv
        if color == "b":
            # Black wants top-bottom, so central columns are valuable.
            score += 3.0 * (5 - abs(c - 5))
        else:
            # White wants left-right, so central rows are valuable.
            score += 3.0 * (5 - abs(r - 5))

        # Slightly discourage extreme corners unless tactically justified.
        if mv in {(0, 0), (0, 10), (10, 0), (10, 10)}:
            score -= 8.0

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move in occupied:
        return empties[0]

    return best_move


def neighbors(cell):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield (nr, nc)


def ordered_by_center(cells):
    return sorted(cells, key=lambda x: abs(x[0] - 5) + abs(x[1] - 5))


def is_win(stones, color):
    """
    BFS connectivity win test.
    Black connects top to bottom.
    White connects left to right.
    """
    if not stones:
        return False

    stack = []
    seen = set()

    if color == "b":
        for c in range(N):
            if (0, c) in stones:
                stack.append((0, c))
                seen.add((0, c))

        while stack:
            cell = stack.pop()
            r, c = cell
            if r == N - 1:
                return True
            for nb in neighbors(cell):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    else:
        for r in range(N):
            if (r, 0) in stones:
                stack.append((r, 0))
                seen.add((r, 0))

        while stack:
            cell = stack.pop()
            r, c = cell
            if c == N - 1:
                return True
            for nb in neighbors(cell):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    return False


def shortest_connection(my_stones, enemy_stones, color):
    """
    Dijkstra connection distance.
    Own stones cost 0.
    Empty cells cost 1.
    Enemy stones are blocked.
    Lower is better.
    """
    dist = [[inf] * N for _ in range(N)]
    pq = []

    def cell_cost(cell):
        if cell in enemy_stones:
            return inf
        if cell in my_stones:
            return 0
        return 1

    if color == "b":
        # Start from top edge.
        for c in range(N):
            cell = (0, c)
            cost = cell_cost(cell)
            if cost < inf:
                dist[0][c] = cost
                heappush(pq, (cost, 0, c))

        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if r == N - 1:
                return d
            for nr, nc in neighbors((r, c)):
                cost = cell_cost((nr, nc))
                if cost == inf:
                    continue
                nd = d + cost
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))

    else:
        # Start from left edge.
        for r in range(N):
            cell = (r, 0)
            cost = cell_cost(cell)
            if cost < inf:
                dist[r][0] = cost
                heappush(pq, (cost, r, 0))

        while pq:
            d, r, c = heappop(pq)
            if d != dist[r][c]:
                continue
            if c == N - 1:
                return d
            for nr, nc in neighbors((r, c)):
                cost = cell_cost((nr, nc))
                if cost == inf:
                    continue
                nd = d + cost
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))

    return 9999


def move_static_score(mv, me_set, opp_set, color):
    """
    Fast local heuristic for shape quality.
    Rewards center, friendly adjacency, useful blocking contact,
    and loose bridge-like formations.
    """
    r, c = mv
    score = 0.0

    # Center control.
    score += 2.2 * (10 - (abs(r - 5) + abs(c - 5)))

    friendly_adj = 0
    enemy_adj = 0
    empty_adj = 0

    for nb in neighbors(mv):
        if nb in me_set:
            friendly_adj += 1
        elif nb in opp_set:
            enemy_adj += 1
        else:
            empty_adj += 1

    # Friendly contact is good, but too much clumping has diminishing return.
    if friendly_adj == 0:
        score -= 1.5
    elif friendly_adj == 1:
        score += 6.0
    elif friendly_adj == 2:
        score += 10.5
    else:
        score += 12.0 + friendly_adj

    # Contact with enemy can be a useful block.
    score += 3.0 * enemy_adj

    # Keep liberties.
    score += 0.6 * empty_adj

    # Edge relevance.
    if color == "b":
        # Top/bottom edges are meaningful for black.
        if r == 0 or r == N - 1:
            score += 4.0
        if c == 0 or c == N - 1:
            score -= 1.0
    else:
        # Left/right edges are meaningful for white.
        if c == 0 or c == N - 1:
            score += 4.0
        if r == 0 or r == N - 1:
            score -= 1.0

    # Bridge-like virtual connections.
    # In Hex, stones separated by certain two-step offsets can form strong templates.
    bridge_offsets = [
        (-1, -1), (-1, 2),
        (1, -2), (1, 1),
        (-2, 1), (2, -1),
    ]

    for dr, dc in bridge_offsets:
        other = (r + dr, c + dc)
        if not (0 <= other[0] < N and 0 <= other[1] < N):
            continue
        if other in me_set:
            commons = common_neighbors(mv, other)
            empty_common = 0
            blocked_common = 0
            for x in commons:
                if x in opp_set:
                    blocked_common += 1
                elif x not in me_set:
                    empty_common += 1
            if empty_common >= 2:
                score += 7.0
            elif empty_common == 1 and blocked_common == 0:
                score += 3.0

        elif other in opp_set:
            # Occupying a bridge point near enemy stones can be an important cut.
            commons = common_neighbors(mv, other)
            if any(x not in me_set and x not in opp_set for x in commons):
                score += 2.0

    return score


def common_neighbors(a, b):
    sa = set(neighbors(a))
    return [x for x in neighbors(b) if x in sa]
