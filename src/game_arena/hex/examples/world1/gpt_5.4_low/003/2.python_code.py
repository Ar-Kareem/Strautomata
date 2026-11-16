
from collections import deque

N = 11
INF = 10**9

# Hex neighbors:
# (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)
NEIGHBORS = [[] for _ in range(N * N)]
for r in range(N):
    for c in range(N):
        i = r * N + c
        cand = [
            (r, c - 1),
            (r, c + 1),
            (r - 1, c),
            (r - 1, c + 1),
            (r + 1, c),
            (r + 1, c - 1),
        ]
        for rr, cc in cand:
            if 0 <= rr < N and 0 <= cc < N:
                NEIGHBORS[i].append(rr * N + cc)

BLACK_SOURCES = [0 * N + c for c in range(N)]
BLACK_TARGETS = [10 * N + c for c in range(N)]
WHITE_SOURCES = [r * N + 0 for r in range(N)]
WHITE_TARGETS = [r * N + 10 for r in range(N)]


def idx(rc):
    return rc[0] * N + rc[1]


def rc(i):
    return (i // N, i % N)


def shortest_path_cost(own, opp, color):
    """
    0-1 BFS shortest connection cost.
    own cells have cost 0, empty cells cost 1, opp cells blocked.
    Returns minimum number of empty cells still needed to connect sides.
    """
    dist = [INF] * (N * N)
    dq = deque()

    if color == 'b':
        sources = BLACK_SOURCES
        targets = BLACK_TARGETS
    else:
        sources = WHITE_SOURCES
        targets = WHITE_TARGETS

    for s in sources:
        if s in opp:
            continue
        w = 0 if s in own else 1
        if w < dist[s]:
            dist[s] = w
            if w == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in NEIGHBORS[u]:
            if v in opp:
                continue
            w = 0 if v in own else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    best = INF
    for t in targets:
        if dist[t] < best:
            best = dist[t]
    return best


def local_heuristic(move_i, me_set, opp_set, color):
    r, c = rc(move_i)
    my_n = 0
    opp_n = 0
    for nb in NEIGHBORS[move_i]:
        if nb in me_set:
            my_n += 1
        elif nb in opp_set:
            opp_n += 1

    score = 0.0
    score += 1.9 * my_n
    score += 1.2 * opp_n

    # Center preference
    score -= 0.18 * ((r - 5) * (r - 5) + (c - 5) * (c - 5))

    # Slight preference for the useful axis
    if color == 'b':
        score -= 0.20 * abs(c - 5)
        if r == 0 or r == 10:
            score += 0.3
    else:
        score -= 0.20 * abs(r - 5)
        if c == 0 or c == 10:
            score += 0.3

    return score


def choose_best(cands, me_set, opp_set, color, cur_my, cur_opp):
    opp_color = 'w' if color == 'b' else 'b'
    best_move = None
    best_score = -10**18

    for mv in cands:
        new_me = set(me_set)
        new_me.add(mv)

        my_after = shortest_path_cost(new_me, opp_set, color)
        opp_after = shortest_path_cost(opp_set, new_me, opp_color)

        my_improve = cur_my - my_after
        opp_hurt = opp_after - cur_opp

        score = 0.0
        score += 24.0 * opp_after
        score -= 26.0 * my_after
        score += 7.0 * my_improve
        score += 9.0 * opp_hurt
        score += local_heuristic(mv, me_set, opp_set, color)

        # Tiny deterministic tie-breaker
        r, c = rc(mv)
        score += 1e-4 * (100 - (r * 11 + c))

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = {idx(x) for x in me}
    opp_set = {idx(x) for x in opp}

    empties = [i for i in range(N * N) if i not in me_set and i not in opp_set]
    if not empties:
        return (0, 0)  # unreachable in normal play, but keeps function total

    # Opening: take center or nearest available
    if not me_set and not opp_set:
        empties_sorted = sorted(
            empties,
            key=lambda i: ((rc(i)[0] - 5) ** 2 + (rc(i)[1] - 5) ** 2, i)
        )
        return rc(empties_sorted[0])

    opp_color = 'w' if color == 'b' else 'b'
    cur_my = shortest_path_cost(me_set, opp_set, color)
    cur_opp = shortest_path_cost(opp_set, me_set, opp_color)

    # 1) Immediate winning move
    winning_moves = []
    for mv in empties:
        new_me = set(me_set)
        new_me.add(mv)
        if shortest_path_cost(new_me, opp_set, color) == 0:
            winning_moves.append(mv)

    if winning_moves:
        best = choose_best(winning_moves, me_set, opp_set, color, cur_my, cur_opp)
        return rc(best)

    # 2) Immediate block if opponent can win next move
    threats = []
    for mv in empties:
        new_opp = set(opp_set)
        new_opp.add(mv)
        if shortest_path_cost(new_opp, me_set, opp_color) == 0:
            threats.append(mv)

    if threats:
        best = choose_best(threats, me_set, opp_set, color, cur_my, cur_opp)
        return rc(best)

    # 3) General move selection
    best = choose_best(empties, me_set, opp_set, color, cur_my, cur_opp)

    # Guaranteed legal fallback
    if best is None or best in me_set or best in opp_set:
        best = empties[0]

    return rc(best)
