
from heapq import heappush, heappop

N = 11

# Hex neighbors for coordinates described in the prompt:
# same row:      (r, c-1), (r, c+1)
# row above:     (r-1, c), (r-1, c+1)
# row below:     (r+1, c), (r+1, c-1)
DIRS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc


def is_on_start_side(cell, color):
    r, c = cell
    return r == 0 if color == 'b' else c == 0


def is_on_goal_side(cell, color):
    r, c = cell
    return r == N - 1 if color == 'b' else c == N - 1


def connection_cost(myset, oppset, color):
    """
    Minimum number of additional empty cells needed for `color` to connect its sides.
    Own stones cost 0, empty cells cost 1, opponent stones are blocked.
    """
    INF = 10**9
    dist = {}
    pq = []

    if color == 'b':
        starts = [(0, c) for c in range(N)]
    else:
        starts = [(r, 0) for r in range(N)]

    for cell in starts:
        if cell in oppset:
            continue
        w = 0 if cell in myset else 1
        if w < dist.get(cell, INF):
            dist[cell] = w
            heappush(pq, (w, cell))

    best = INF
    while pq:
        d, cell = heappop(pq)
        if d != dist.get(cell, INF):
            continue
        if is_on_goal_side(cell, color):
            best = d
            break
        r, c = cell
        for nb in neighbors(r, c):
            if nb in oppset:
                continue
            nd = d + (0 if nb in myset else 1)
            if nd < dist.get(nb, INF):
                dist[nb] = nd
                heappush(pq, (nd, nb))
    return best


def has_winning_connection(myset, color):
    """
    True if myset already forms a completed connection for color.
    """
    stack = []
    seen = set()

    if color == 'b':
        for c in range(N):
            cell = (0, c)
            if cell in myset:
                stack.append(cell)
                seen.add(cell)
        goal = lambda rc: rc[0] == N - 1
    else:
        for r in range(N):
            cell = (r, 0)
            if cell in myset:
                stack.append(cell)
                seen.add(cell)
        goal = lambda rc: rc[1] == N - 1

    while stack:
        cell = stack.pop()
        if goal(cell):
            return True
        r, c = cell
        for nb in neighbors(r, c):
            if nb in myset and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False


def centrality(cell):
    r, c = cell
    # Favor center; max around center, lower near corners.
    return -((r - 5) ** 2 + (c - 5) ** 2)


def axis_bonus(cell, color):
    r, c = cell
    # Favor progress along our connection direction, mildly prefer middle of the orthogonal axis.
    if color == 'b':
        # black wants top-bottom, so central columns are useful
        return -(c - 5) ** 2
    else:
        # white wants left-right, so central rows are useful
        return -(r - 5) ** 2


def local_synergy(move, myset, oppset, color):
    """
    Local shape heuristic:
    - prefer adjacency to our stones
    - prefer moves that connect multiple friendly groups
    - prefer reducing opponent local influence
    """
    r, c = move
    my_adj = 0
    opp_adj = 0
    friendly_groups = set()

    # identify neighboring friendly components approximately by representative stone itself
    # lightweight and good enough as a heuristic
    for nb in neighbors(r, c):
        if nb in myset:
            my_adj += 1
            friendly_groups.add(nb)
        elif nb in oppset:
            opp_adj += 1

    score = 2.5 * my_adj - 1.7 * opp_adj

    # Bridges / loose connections one step away
    second_my = 0
    second_opp = 0
    checked = set()
    for nb in neighbors(r, c):
        for nn in neighbors(*nb):
            if nn == (r, c) or nn in checked:
                continue
            checked.add(nn)
            if nn in myset:
                second_my += 1
            elif nn in oppset:
                second_opp += 1

    score += 0.25 * second_my - 0.15 * second_opp

    # Touching both "forward" and "backward" directions can matter
    if color == 'b':
        vertical_touch = 0
        for nr, nc in neighbors(r, c):
            if (nr, nc) in myset:
                if nr < r:
                    vertical_touch += 1
                elif nr > r:
                    vertical_touch += 1
        score += 0.4 * vertical_touch
    else:
        horizontal_touch = 0
        for nr, nc in neighbors(r, c):
            if (nr, nc) in myset:
                if nc < c:
                    horizontal_touch += 1
                elif nc > c:
                    horizontal_touch += 1
        score += 0.4 * horizontal_touch

    return score


def choose_fallback(empty_cells, color):
    # Deterministic legal fallback: center-most by suitable ordering
    center = (5, 5)
    best = None
    best_key = None
    for cell in empty_cells:
        r, c = cell
        key = ((r - center[0]) ** 2 + (c - center[1]) ** 2, r, c)
        if best_key is None or key < best_key:
            best_key = key
            best = cell
    return best


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    myset = set(me)
    oppset = set(opp)

    occupied = myset | oppset
    empty_cells = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]

    # Must always return a legal move
    if not empty_cells:
        return (0, 0)

    # 1) Immediate winning move
    for mv in empty_cells:
        trial = set(myset)
        trial.add(mv)
        if has_winning_connection(trial, color):
            return mv

    # 2) Immediate block if opponent could win next move
    opp_color = 'w' if color == 'b' else 'b'
    opp_wins = []
    for mv in empty_cells:
        trial = set(oppset)
        trial.add(mv)
        if has_winning_connection(trial, opp_color):
            opp_wins.append(mv)
    if opp_wins:
        # If multiple blocks exist, choose the best among them by our heuristic.
        candidates = opp_wins
    else:
        candidates = empty_cells

    base_my_cost = connection_cost(myset, oppset, color)
    base_opp_cost = connection_cost(oppset, myset, opp_color)

    best_move = None
    best_score = None

    for mv in candidates:
        new_my = set(myset)
        new_my.add(mv)

        my_cost = connection_cost(new_my, oppset, color)
        opp_cost = connection_cost(oppset, new_my, opp_color)

        improve_me = base_my_cost - my_cost
        hurt_opp = opp_cost - base_opp_cost

        score = 0.0
        score += 14.0 * improve_me
        score += 10.0 * hurt_opp
        score += 0.18 * centrality(mv)
        score += 0.10 * axis_bonus(mv, color)
        score += local_synergy(mv, myset, oppset, color)

        # Small preference for owning strategic center early
        if mv == (5, 5):
            score += 1.5
        elif mv in [(5, 4), (4, 5), (5, 6), (6, 5), (4, 6), (6, 4)]:
            score += 0.6

        # Tie-break deterministically
        tie_key = (score, -abs(mv[0] - 5) - abs(mv[1] - 5), -mv[0], -mv[1])

        if best_score is None or tie_key > best_score:
            best_score = tie_key
            best_move = mv

    if best_move is None or best_move in occupied:
        return choose_fallback(empty_cells, color)
    return best_move
