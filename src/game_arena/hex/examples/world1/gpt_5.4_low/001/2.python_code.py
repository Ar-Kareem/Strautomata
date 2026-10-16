
from heapq import heappush, heappop

N = 11
INF = 10**9

# Hex neighbors for coordinates described in the prompt:
# (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)
def neighbors(r, c):
    cand = [
        (r, c - 1),
        (r, c + 1),
        (r - 1, c),
        (r - 1, c + 1),
        (r + 1, c),
        (r + 1, c - 1),
    ]
    out = []
    for rr, cc in cand:
        if 0 <= rr < N and 0 <= cc < N:
            out.append((rr, cc))
    return out


def has_connection(stones, color):
    """Check whether the given stone set already wins for color."""
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
        target_row = N - 1
        while stack:
            r, c = stack.pop()
            if r == target_row:
                return True
            for nb in neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    else:  # white connects left-right
        for r in range(N):
            if (r, 0) in stones:
                stack.append((r, 0))
                seen.add((r, 0))
        target_col = N - 1
        while stack:
            r, c = stack.pop()
            if c == target_col:
                return True
            for nb in neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
    return False


def shortest_path_cost(my_stones, opp_stones, color):
    """
    Dijkstra-style connection cost:
    - own stones cost 0
    - empty cells cost 1
    - opponent stones blocked
    Returns estimated number of empty cells still needed to connect sides.
    """
    my = set(my_stones)
    opp = set(opp_stones)

    dist = [[INF] * N for _ in range(N)]
    pq = []

    def cell_cost(r, c):
        if (r, c) in opp:
            return INF
        return 0 if (r, c) in my else 1

    if color == 'b':
        # Start from top edge, aim for bottom edge
        for c in range(N):
            w = cell_cost(0, c)
            if w < INF:
                dist[0][c] = w
                heappush(pq, (w, 0, c))
        goal = lambda r, c: r == N - 1
    else:
        # Start from left edge, aim for right edge
        for r in range(N):
            w = cell_cost(r, 0)
            if w < INF:
                dist[r][0] = w
                heappush(pq, (w, r, 0))
        goal = lambda r, c: c == N - 1

    best_goal = INF

    while pq:
        d, r, c = heappop(pq)
        if d != dist[r][c]:
            continue
        if d >= best_goal:
            continue
        if goal(r, c):
            best_goal = d
            continue
        for rr, cc in neighbors(r, c):
            w = cell_cost(rr, cc)
            if w >= INF:
                continue
            nd = d + w
            if nd < dist[rr][cc]:
                dist[rr][cc] = nd
                heappush(pq, (nd, rr, cc))

    return best_goal


def immediate_winning_moves(player_stones, opp_stones, color, empties):
    """Return list of empty cells that immediately win for the player."""
    wins = []
    pset = set(player_stones)
    for mv in empties:
        pset.add(mv)
        if has_connection(pset, color):
            wins.append(mv)
        pset.remove(mv)
    return wins


def local_features(move, my_set, opp_set, color):
    """Small tactical/local heuristic."""
    r, c = move
    own_n = 0
    opp_n = 0
    empty_n = 0
    for nb in neighbors(r, c):
        if nb in my_set:
            own_n += 1
        elif nb in opp_set:
            opp_n += 1
        else:
            empty_n += 1

    # Mild center bias
    center_bias = - (abs(r - 5) + abs(c - 5))

    # Encourage touching both directions of objective a bit
    if color == 'b':
        edge_touch = (1 if r == 0 else 0) + (1 if r == N - 1 else 0)
    else:
        edge_touch = (1 if c == 0 else 0) + (1 if c == N - 1 else 0)

    # Tiny preference for being somewhat central on the non-goal axis
    if color == 'b':
        axis_bias = -abs(c - 5)
    else:
        axis_bias = -abs(r - 5)

    return 4 * own_n + 1 * opp_n + 0.5 * empty_n + 0.4 * center_bias + 1.5 * edge_touch + 0.6 * axis_bias


def choose_central_legal(empties):
    prefs = [
        (5, 5), (5, 4), (4, 5), (5, 6), (6, 5),
        (4, 6), (6, 4), (4, 4), (6, 6),
        (5, 3), (3, 5), (5, 7), (7, 5),
        (4, 7), (7, 4), (3, 6), (6, 3), (4, 3), (3, 4), (6, 7), (7, 6),
    ]
    eset = set(empties)
    for mv in prefs:
        if mv in eset:
            return mv
    return empties[0]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)

    empties = []
    for r in range(N):
        for c in range(N):
            if (r, c) not in me_set and (r, c) not in opp_set:
                empties.append((r, c))

    # Absolute safety: always return a legal move if possible
    if not empties:
        return (0, 0)

    opp_color = 'w' if color == 'b' else 'b'

    # Opening preference
    total_stones = len(me) + len(opp)
    if total_stones == 0:
        return choose_central_legal(empties)

    # 1) Immediate winning move
    my_wins = immediate_winning_moves(me_set, opp_set, color, empties)
    if my_wins:
        # If multiple, prefer the most central/supportive one
        best = None
        best_score = -10**18
        for mv in my_wins:
            score = local_features(mv, me_set, opp_set, color)
            if score > best_score:
                best_score = score
                best = mv
        return best

    # 2) Immediate block if opponent would win next
    opp_wins = immediate_winning_moves(opp_set, me_set, opp_color, empties)
    if opp_wins:
        # Block one of them; if multiple, choose best strategic block
        best = None
        best_score = -10**18
        for mv in opp_wins:
            new_me = set(me_set)
            new_me.add(mv)
            my_dist = shortest_path_cost(new_me, opp_set, color)
            opp_dist = shortest_path_cost(opp_set, new_me, opp_color)
            score = 12 * opp_dist - 10 * my_dist + local_features(mv, me_set, opp_set, color)
            if score > best_score:
                best_score = score
                best = mv
        return best

    # Small early-game centrality preference
    if total_stones <= 2:
        central = choose_central_legal(empties)
        # Use it if it is not obviously poor compared to others by local support
        if local_features(central, me_set, opp_set, color) >= -3:
            return central

    # 3) Heuristic search over all legal moves
    best_move = None
    best_score = -10**18

    for mv in empties:
        new_me = set(me_set)
        new_me.add(mv)

        my_dist = shortest_path_cost(new_me, opp_set, color)
        opp_dist = shortest_path_cost(opp_set, new_me, opp_color)

        # Main balance: reduce our path cost, increase theirs
        score = 12 * opp_dist - 10 * my_dist

        # Local tactical shape / adjacency
        score += local_features(mv, me_set, opp_set, color)

        # Slight bonus if move touches one of our existing groups
        touches_own = any(nb in me_set for nb in neighbors(mv[0], mv[1]))
        if touches_own:
            score += 2.0

        # Slight bonus if it interferes with opponent nearby
        touches_opp = any(nb in opp_set for nb in neighbors(mv[0], mv[1]))
        if touches_opp:
            score += 1.5

        # Prefer more central moves as a tiebreaker
        score += -0.1 * (abs(mv[0] - 5) + abs(mv[1] - 5))

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is not None:
        return best_move

    # Fallback: guaranteed legal
    return empties[0]
