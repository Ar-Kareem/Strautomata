
from heapq import heappush, heappop

N = 11
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def side_dist(color, r, c):
    if color == 'b':
        return min(r, N - 1 - r)
    else:
        return min(c, N - 1 - c)


def progress_value(color, r, c):
    if color == 'b':
        return r
    else:
        return c


def dijkstra_cost(myset, oppset, color):
    INF = 10**9
    dist = [[INF] * N for _ in range(N)]
    pq = []

    if color == 'b':
        for c in range(N):
            if (0, c) in oppset:
                continue
            w = 0 if (0, c) in myset else 1
            if w < dist[0][c]:
                dist[0][c] = w
                heappush(pq, (w, 0, c))
        target_check = lambda r, c: r == N - 1
    else:
        for r in range(N):
            if (r, 0) in oppset:
                continue
            w = 0 if (r, 0) in myset else 1
            if w < dist[r][0]:
                dist[r][0] = w
                heappush(pq, (w, r, 0))
        target_check = lambda r, c: c == N - 1

    best = INF
    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        if target_check(r, c):
            best = d
            break
        for nr, nc in neighbors(r, c):
            if (nr, nc) in oppset:
                continue
            nd = d + (0 if (nr, nc) in myset else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heappush(pq, (nd, nr, nc))
    return best


def would_win_after(move, myset, oppset, color):
    new_my = set(myset)
    new_my.add(move)
    return dijkstra_cost(new_my, oppset, color) == 0


def local_score(move, myset, oppset, color):
    r, c = move
    score = 0.0

    # Neighbor structure
    friendly = 0
    enemy = 0
    empty = 0
    for nr, nc in neighbors(r, c):
        if (nr, nc) in myset:
            friendly += 1
        elif (nr, nc) in oppset:
            enemy += 1
        else:
            empty += 1

    score += 5.0 * friendly
    score += 1.2 * enemy

    # Reward linking multiple friendly groups around the point
    friendly_neighbors = [(nr, nc) for nr, nc in neighbors(r, c) if (nr, nc) in myset]
    if len(friendly_neighbors) >= 2:
        score += 4.0 + 1.5 * (len(friendly_neighbors) - 2)

    # Bridge-like support: if two-step shape has one stone and one empty support, reward
    # Use common virtual connection motifs adapted to board geometry.
    bridge_pairs = [
        ((r - 1, c), (r, c - 1), (r - 1, c - 1)),
        ((r - 1, c + 1), (r, c + 1), (r - 1, c + 2)),
        ((r, c - 1), (r + 1, c - 1), (r + 1, c - 2)),
        ((r + 1, c), (r + 1, c - 1), (r + 2, c - 1)),
        ((r - 1, c), (r - 1, c + 1), (r - 2, c + 1)),
        ((r, c + 1), (r + 1, c), (r + 1, c + 1)),
    ]
    for a, b, far in bridge_pairs:
        ar, ac = a
        br, bc = b
        fr, fc = far
        cond1 = 0 <= ar < N and 0 <= ac < N and (ar, ac) in myset
        cond2 = 0 <= br < N and 0 <= bc < N and (br, bc) in myset
        condf = 0 <= fr < N and 0 <= fc < N and (fr, fc) not in oppset
        if (cond1 or cond2) and condf:
            score += 1.5
        if cond1 and cond2:
            score += 2.0

    # Center preference, but not too much
    center = (N - 1) / 2.0
    score += 2.5 - 0.35 * (abs(r - center) + abs(c - center))

    # Progress toward target sides
    if color == 'b':
        score += 0.35 * min(r, N - 1 - r)
        score += 0.12 * (N - abs((N - 1) - 2 * r))
    else:
        score += 0.35 * min(c, N - 1 - c)
        score += 0.12 * (N - abs((N - 1) - 2 * c))

    # Slight preference for touching edge-relevant areas
    score -= 0.15 * side_dist(color, r, c)

    return score


def policy(me, opp, color):
    myset = set(me)
    oppset = set(opp)

    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in myset and (r, c) not in oppset]

    # Safety: always return legal move
    if not empties:
        return (0, 0)

    # Opening: strong center / swap-safe style
    if not me and not opp:
        return (5, 5)

    # Immediate win
    for mv in empties:
        if would_win_after(mv, myset, oppset, color):
            return mv

    # Immediate block
    opp_color = 'w' if color == 'b' else 'b'
    for mv in empties:
        if would_win_after(mv, oppset, myset, opp_color):
            return mv

    my_before = dijkstra_cost(myset, oppset, color)
    opp_before = dijkstra_cost(oppset, myset, opp_color)

    best_move = empties[0]
    best_score = -10**18

    for mv in empties:
        r, c = mv

        new_my = set(myset)
        new_my.add(mv)

        my_after = dijkstra_cost(new_my, oppset, color)

        # Approximate blocking value by considering this cell unavailable to opp
        new_opp_block = set(myset)
        new_opp_block.add(mv)
        opp_after = dijkstra_cost(oppset, new_opp_block, opp_color)

        score = 0.0

        # Main path terms
        score += 20.0 * (my_before - my_after)
        score += 16.0 * (opp_after - opp_before)

        # If move sits on both players' useful corridors, that's often critical
        if my_after <= my_before - 1 and opp_after >= opp_before + 1:
            score += 6.0

        # Local tactical/shape terms
        score += local_score(mv, myset, oppset, color)

        # Extra reward for connecting separated neighbors
        friendly_nbs = [(nr, nc) for nr, nc in neighbors(r, c) if (nr, nc) in myset]
        if len(friendly_nbs) >= 2:
            score += 3.0 * len(friendly_nbs)

        # Penalize moves too trapped by enemies unless they strongly improve path
        enemy_nbs = sum((nr, nc) in oppset for nr, nc in neighbors(r, c))
        if enemy_nbs >= 4 and my_after >= my_before:
            score -= 5.0

        # Slightly prefer lower raw shortest path after move
        score -= 1.5 * my_after
        score += 1.0 * opp_after

        # Deterministic tie-breaks
        score += 0.001 * (10 - abs(r - 5))
        score += 0.001 * (10 - abs(c - 5))

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move
