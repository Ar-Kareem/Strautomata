
from heapq import heappush, heappop

N = 11
DIRS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def side_a_cells(color):
    if color == 'b':  # top
        return [(0, c) for c in range(N)]
    else:  # left
        return [(r, 0) for r in range(N)]


def side_b_cells(color):
    if color == 'b':  # bottom
        return [(N - 1, c) for c in range(N)]
    else:  # right
        return [(r, N - 1) for r in range(N)]


def cell_cost(cell, my_set, opp_set):
    if cell in my_set:
        return 0
    if cell in opp_set:
        return None
    return 1


def shortest_path_distance(my_set, opp_set, color):
    starts = side_a_cells(color)
    targets = set(side_b_cells(color))
    pq = []
    dist = {}

    for s in starts:
        c = cell_cost(s, my_set, opp_set)
        if c is None:
            continue
        dist[s] = c
        heappush(pq, (c, s))

    best_target = None
    best_cost = None

    while pq:
        d, u = heappop(pq)
        if d != dist.get(u):
            continue
        if u in targets:
            best_target = u
            best_cost = d
            break
        ur, uc = u
        for v in neighbors(ur, uc):
            c = cell_cost(v, my_set, opp_set)
            if c is None:
                continue
            nd = d + c
            if nd < dist.get(v, 10**9):
                dist[v] = nd
                heappush(pq, (nd, v))

    if best_target is None:
        return 10**9
    return best_cost


def shortest_path_with_parents(my_set, opp_set, color):
    starts = side_a_cells(color)
    targets = set(side_b_cells(color))
    pq = []
    dist = {}
    parent = {}

    for s in starts:
        c = cell_cost(s, my_set, opp_set)
        if c is None:
            continue
        if c < dist.get(s, 10**9):
            dist[s] = c
            parent[s] = None
            heappush(pq, (c, s))

    best_target = None

    while pq:
        d, u = heappop(pq)
        if d != dist.get(u):
            continue
        if u in targets:
            best_target = u
            break
        ur, uc = u
        for v in neighbors(ur, uc):
            c = cell_cost(v, my_set, opp_set)
            if c is None:
                continue
            nd = d + c
            old = dist.get(v, 10**9)
            if nd < old:
                dist[v] = nd
                parent[v] = u
                heappush(pq, (nd, v))

    if best_target is None:
        return 10**9, []

    path = []
    cur = best_target
    while cur is not None:
        path.append(cur)
        cur = parent.get(cur)
    path.reverse()
    return dist[best_target], path


def is_win(my_set, opp_set, color):
    return shortest_path_distance(my_set, opp_set, color) == 0


def centrality(r, c):
    return -((r - 5) ** 2 + (c - 5) ** 2)


def progress_coord(cell, color):
    r, c = cell
    return r if color == 'b' else c


def span_score(my_set, color):
    if not my_set:
        return 0
    vals = [progress_coord(x, color) for x in my_set]
    return max(vals) - min(vals)


def connection_bonus(move, my_set):
    r, c = move
    bonus = 0
    my_neighbors = 0
    second_ring = 0

    for nb in neighbors(r, c):
        if nb in my_set:
            my_neighbors += 1

    # second-order connectivity through nearby cells
    seen = set()
    for nb in neighbors(r, c):
        nr, nc = nb
        for nn in neighbors(nr, nc):
            if nn != move and nn in my_set and nn not in seen:
                seen.add(nn)
                second_ring += 1

    bonus += 14 * my_neighbors
    bonus += 3 * second_ring

    # reward bridging patterns: two distinct friendly neighbors around move
    friendly = [nb for nb in neighbors(r, c) if nb in my_set]
    bonus += 8 * max(0, len(friendly) - 1)

    return bonus


def edge_goal_bonus(move, color):
    r, c = move
    if color == 'b':
        return 6 if r in (0, N - 1) else 0
    else:
        return 6 if c in (0, N - 1) else 0


def opening_move(empties, color):
    prefs = [
        (5, 5), (5, 4), (4, 5), (6, 5), (5, 6),
        (4, 6), (6, 4), (4, 4), (6, 6),
        (5, 3), (3, 5), (7, 5), (5, 7)
    ]
    if color == 'b':
        prefs += [(4, 5), (6, 5), (3, 5), (7, 5)]
    else:
        prefs += [(5, 4), (5, 6), (5, 3), (5, 7)]
    for mv in prefs:
        if mv in empties:
            return mv
    return min(empties)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(map(tuple, me))
    opp_set = set(map(tuple, opp))

    empties = []
    occupied = me_set | opp_set
    for r in range(N):
        for c in range(N):
            if (r, c) not in occupied:
                empties.append((r, c))

    if not empties:
        return (0, 0)

    empty_set = set(empties)

    # Opening
    if not me_set and not opp_set:
        return opening_move(empty_set, color)
    if len(occupied) <= 2:
        om = opening_move(empty_set, color)
        if om in empty_set:
            return om

    opp_color = 'w' if color == 'b' else 'b'

    # 1. Immediate win
    for mv in empties:
        new_me = set(me_set)
        new_me.add(mv)
        if is_win(new_me, opp_set, color):
            return mv

    # 2. Immediate block
    opp_winning_moves = []
    for mv in empties:
        new_opp = set(opp_set)
        new_opp.add(mv)
        if is_win(new_opp, me_set, opp_color):
            opp_winning_moves.append(mv)
    if opp_winning_moves:
        # If multiple winning threats, choose the best legal block among them.
        if len(opp_winning_moves) == 1:
            return opp_winning_moves[0]
        # choose the threat point that also helps us most
        best = None
        best_score = -10**18
        base_my = shortest_path_distance(me_set, opp_set, color)
        base_opp = shortest_path_distance(opp_set, me_set, opp_color)
        for mv in opp_winning_moves:
            new_me = set(me_set)
            new_me.add(mv)
            myd = shortest_path_distance(new_me, opp_set, color)
            oppd = shortest_path_distance(opp_set, new_me, opp_color)
            score = 100000 * (base_my - myd) + 10000 * (oppd - base_opp)
            score += connection_bonus(mv, me_set) + centrality(*mv)
            if score > best_score:
                best_score = score
                best = mv
        if best is not None:
            return best

    # Candidate set: all empties, but prioritize cells on best paths
    _, my_path = shortest_path_with_parents(me_set, opp_set, color)
    _, opp_path = shortest_path_with_parents(opp_set, me_set, opp_color)

    candidates = set(empties)
    for cell in my_path + opp_path:
        if cell in empty_set:
            candidates.add(cell)
        for nb in neighbors(*cell):
            if nb in empty_set:
                candidates.add(nb)

    base_my = shortest_path_distance(me_set, opp_set, color)
    base_opp = shortest_path_distance(opp_set, me_set, opp_color)
    base_span = span_score(me_set, color)

    best_move = None
    best_score = -10**18

    for mv in candidates:
        r, c = mv
        new_me = set(me_set)
        new_me.add(mv)

        myd = shortest_path_distance(new_me, opp_set, color)
        oppd = shortest_path_distance(opp_set, new_me, opp_color)
        new_span = span_score(new_me, color)

        score = 0
        score += 5000 * (base_my - myd)          # improve our path
        score += 3200 * (oppd - base_opp)        # hinder theirs
        score += 120 * (new_span - base_span)    # extend overall reach
        score += connection_bonus(mv, me_set)    # local connection power
        score += edge_goal_bonus(mv, color)      # useful side contact
        score += 2 * centrality(r, c)            # central preference

        # Penalize helping opponent locally
        opp_adj = sum((nb in opp_set) for nb in neighbors(r, c))
        score -= 7 * opp_adj

        # Prefer progress along our goal axis
        score += 4 * progress_coord(mv, color)
        score -= 2 * abs((c if color == 'b' else r) - 5)

        # Tie-breaker: deterministic
        score += (10 - r) * 1e-3 + (10 - c) * 1e-4

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move in empty_set:
        return best_move

    # Safe fallback
    return empties[0]
