
from heapq import heappush, heappop
from math import inf

N = 11

DIRS = (
    (0, -1), (0, 1),
    (-1, 0), (-1, 1),
    (1, 0), (1, -1),
)

CENTER = (5, 5)


def in_bounds(r, c):
    return 0 <= r < N and 0 <= c < N


def neighbors(cell):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def other_color(color):
    return 'w' if color == 'b' else 'b'


def has_win(stones, color):
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

        while stack:
            r, c = stack.pop()
            if r == N - 1:
                return True
            for nb in neighbors((r, c)):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    else:
        for r in range(N):
            if (r, 0) in stones:
                stack.append((r, 0))
                seen.add((r, 0))

        while stack:
            r, c = stack.pop()
            if c == N - 1:
                return True
            for nb in neighbors((r, c)):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)

    return False


def shortest_distance(my_stones, opp_stones, color):
    """
    Dijkstra connection distance.
    Own stones cost 0, empty cells cost 1, opponent stones are blocked.
    """
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)

    dist = [[inf] * N for _ in range(N)]
    pq = []

    def cell_cost(cell):
        if cell in opp_stones:
            return inf
        if cell in my_stones:
            return 0
        return 1

    if color == 'b':
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

    return inf


def local_score(move, my_stones, opp_stones, color):
    r, c = move
    my_stones = set(my_stones)
    opp_stones = set(opp_stones)

    score = 0.0

    # Prefer central cells, especially early.
    score -= 0.35 * (abs(r - 5) + abs(c - 5))

    # Prefer axis progress.
    if color == 'b':
        score -= 0.08 * abs(c - 5)
    else:
        score -= 0.08 * abs(r - 5)

    # Local friendly contact is good, but do not over-clump too much.
    friendly_adj = 0
    enemy_adj = 0
    for nb in neighbors(move):
        if nb in my_stones:
            friendly_adj += 1
        elif nb in opp_stones:
            enemy_adj += 1

    score += 1.4 * friendly_adj
    score += 0.8 * enemy_adj

    # Reward common Hex "bridge-ish" virtual connection patterns.
    bridge_offsets = (
        (-1, -1), (-1, 2),
        (1, -2), (1, 1),
        (-2, 1), (2, -1),
    )
    for dr, dc in bridge_offsets:
        br, bc = r + dr, c + dc
        if in_bounds(br, bc) and (br, bc) in my_stones:
            score += 1.2

    # Slight edge relevance.
    if color == 'b':
        if r == 0 or r == N - 1:
            score += 0.45
    else:
        if c == 0 or c == N - 1:
            score += 0.45

    return score


def evaluate_state(my_stones, opp_stones, color):
    opp_color = other_color(color)

    if has_win(my_stones, color):
        return 100000.0
    if has_win(opp_stones, opp_color):
        return -100000.0

    my_d = shortest_distance(my_stones, opp_stones, color)
    opp_d = shortest_distance(opp_stones, my_stones, opp_color)

    if my_d == inf:
        my_d = 99
    if opp_d == inf:
        opp_d = 99

    return 100.0 * (opp_d - my_d)


def all_empty(my_stones, opp_stones):
    occupied = set(my_stones) | set(opp_stones)
    return [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]


def candidate_moves(my_stones, opp_stones, limit=None):
    occupied = set(my_stones) | set(opp_stones)
    empties = []
    stones = list(occupied)

    if not stones:
        return [CENTER]

    cand = set()

    # Candidates near existing stones are usually the only relevant tactical moves.
    for r, c in stones:
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in occupied:
                    # Hex-ish radius filter.
                    if max(abs(dr), abs(dc), abs(dr + dc)) <= 2:
                        cand.add((nr, nc))

    # Always include center neighborhood if available.
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            nr, nc = CENTER[0] + dr, CENTER[1] + dc
            if in_bounds(nr, nc) and (nr, nc) not in occupied:
                cand.add((nr, nc))

    if not cand:
        cand = set(all_empty(my_stones, opp_stones))

    empties = list(cand)

    if limit is not None and len(empties) > limit:
        empties = empties[:limit]

    return empties


def static_move_score(move, my_stones, opp_stones, color):
    opp_color = other_color(color)

    new_me = list(my_stones) + [move]

    if has_win(new_me, color):
        return 1000000.0

    my_d_before = shortest_distance(my_stones, opp_stones, color)
    opp_d_before = shortest_distance(opp_stones, my_stones, opp_color)

    my_d_after = shortest_distance(new_me, opp_stones, color)
    opp_d_after = shortest_distance(opp_stones, new_me, opp_color)

    if my_d_before == inf:
        my_d_before = 99
    if opp_d_before == inf:
        opp_d_before = 99
    if my_d_after == inf:
        my_d_after = 99
    if opp_d_after == inf:
        opp_d_after = 99

    score = 0.0
    score += 130.0 * (my_d_before - my_d_after)
    score += 105.0 * (opp_d_after - opp_d_before)
    score += 100.0 * (opp_d_after - my_d_after)
    score += local_score(move, my_stones, opp_stones, color)

    return score


def best_ordered_candidates(my_stones, opp_stones, color, max_count):
    cands = candidate_moves(my_stones, opp_stones)
    scored = [(static_move_score(m, my_stones, opp_stones, color), m) for m in cands]
    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored[:max_count]]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me = [tuple(x) for x in me]
    opp = [tuple(x) for x in opp]

    occupied = set(me) | set(opp)
    empties = all_empty(me, opp)

    if not empties:
        return (0, 0)

    # Opening: center or close to center.
    if not me and not opp:
        return CENTER

    if CENTER not in occupied and len(occupied) <= 2:
        return CENTER

    opp_color = other_color(color)

    # 1. Take immediate win.
    for m in empties:
        if has_win(me + [m], color):
            return m

    # 2. Block immediate opponent win.
    opp_winning = []
    for m in empties:
        if has_win(opp + [m], opp_color):
            opp_winning.append(m)

    if opp_winning:
        # If several blocks are needed, choose the one that is also best for us.
        best = max(opp_winning, key=lambda x: static_move_score(x, me, opp, color))
        return best

    # 3. Shallow minimax over promising moves.
    move_count = len(occupied)

    if move_count < 8:
        own_width = 24
        reply_width = 12
    elif move_count < 35:
        own_width = 20
        reply_width = 10
    else:
        own_width = 16
        reply_width = 8

    own_cands = best_ordered_candidates(me, opp, color, own_width)

    if not own_cands:
        return empties[0]

    best_move = own_cands[0]
    best_value = -inf

    for m in own_cands:
        new_me = me + [m]

        if has_win(new_me, color):
            return m

        # Evaluate opponent's strongest replies.
        opp_replies = best_ordered_candidates(opp, new_me, opp_color, reply_width)

        if not opp_replies:
            value = evaluate_state(new_me, opp, color) + local_score(m, me, opp, color)
        else:
            worst = inf
            for om in opp_replies:
                new_opp = opp + [om]

                if has_win(new_opp, opp_color):
                    reply_value = -100000.0
                else:
                    reply_value = evaluate_state(new_me, new_opp, color)

                if reply_value < worst:
                    worst = reply_value

            value = worst + 0.15 * static_move_score(m, me, opp, color)

        if value > best_value:
            best_value = value
            best_move = m

    # Final legality safety.
    if best_move in occupied or not in_bounds(best_move[0], best_move[1]):
        return empties[0]

    return best_move
