
from collections import deque
from typing import List, Tuple, Set

N = 11
INF = 10**9

# Hex neighbors for coordinates (r, c):
# same row:      (r, c-1), (r, c+1)
# row above:     (r-1, c), (r-1, c+1)
# row below:     (r+1, c), (r+1, c-1)
DIRS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, 0), (1, -1)]


def in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def neighbors(r: int, c: int):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if in_bounds(nr, nc):
            yield nr, nc


def edge_starts(color: str):
    if color == 'b':
        return [(0, c) for c in range(N)]
    else:
        return [(r, 0) for r in range(N)]


def edge_goals(color: str):
    if color == 'b':
        return {(N - 1, c) for c in range(N)}
    else:
        return {(r, N - 1) for r in range(N)}


def connected(stones: Set[Tuple[int, int]], color: str) -> bool:
    """Check whether stones already form a winning connection."""
    dq = deque()
    seen = set()

    if color == 'b':
        for c in range(N):
            cell = (0, c)
            if cell in stones:
                dq.append(cell)
                seen.add(cell)
        goal_row = N - 1
        while dq:
            r, c = dq.popleft()
            if r == goal_row:
                return True
            for nb in neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    dq.append(nb)
    else:
        for r in range(N):
            cell = (r, 0)
            if cell in stones:
                dq.append(cell)
                seen.add(cell)
        goal_col = N - 1
        while dq:
            r, c = dq.popleft()
            if c == goal_col:
                return True
            for nb in neighbors(r, c):
                if nb in stones and nb not in seen:
                    seen.add(nb)
                    dq.append(nb)

    return False


def shortest_path_cost_and_path(
    my_stones: Set[Tuple[int, int]],
    opp_stones: Set[Tuple[int, int]],
    color: str,
):
    """
    0-1 BFS shortest connection path:
      - my stones cost 0
      - empty cells cost 1
      - opp stones blocked
    Returns:
      (best_cost, path_cells_set)
    where best_cost is the minimum number of extra stones needed to connect.
    """
    dist = {}
    prev = {}
    dq = deque()

    def cell_cost(cell):
        if cell in opp_stones:
            return INF
        return 0 if cell in my_stones else 1

    # initialize from start edge
    for cell in edge_starts(color):
        if cell in opp_stones:
            continue
        w = cell_cost(cell)
        dist[cell] = w
        prev[cell] = None
        if w == 0:
            dq.appendleft(cell)
        else:
            dq.append(cell)

    while dq:
        u = dq.popleft()
        du = dist[u]
        ur, uc = u
        for v in neighbors(ur, uc):
            if v in opp_stones:
                continue
            w = 0 if v in my_stones else 1
            nd = du + w
            if nd < dist.get(v, INF):
                dist[v] = nd
                prev[v] = u
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    best_goal = None
    best_cost = INF
    goals = edge_goals(color)
    for g in goals:
        dg = dist.get(g, INF)
        if dg < best_cost:
            best_cost = dg
            best_goal = g

    path_cells = set()
    if best_goal is not None and best_cost < INF:
        cur = best_goal
        while cur is not None:
            path_cells.add(cur)
            cur = prev.get(cur)

    return best_cost, path_cells


def center_score(move: Tuple[int, int]) -> float:
    r, c = move
    return -0.12 * (abs(r - 5) + abs(c - 5))


def local_shape_score(
    move: Tuple[int, int],
    me: Set[Tuple[int, int]],
    opp: Set[Tuple[int, int]],
) -> float:
    r, c = move
    own_n = 0
    opp_n = 0
    empty_n = 0
    for nb in neighbors(r, c):
        if nb in me:
            own_n += 1
        elif nb in opp:
            opp_n += 1
        else:
            empty_n += 1

    # Favor connecting to own stones, slightly punish being surrounded by opp
    score = 1.9 * own_n - 0.7 * opp_n + 0.05 * empty_n

    # Tiny bonus for "bridging" opportunities:
    # count friendly stones at distance-2 via two-step reachable cells
    two_step_friends = 0
    seen = set()
    for nb in neighbors(r, c):
        for nb2 in neighbors(*nb):
            if nb2 != (r, c) and nb2 not in seen:
                seen.add(nb2)
                if nb2 in me:
                    two_step_friends += 1
    score += 0.08 * two_step_friends

    return score


def choose_best(
    candidates,
    me_set: Set[Tuple[int, int]],
    opp_set: Set[Tuple[int, int]],
    color: str,
):
    opp_color = 'w' if color == 'b' else 'b'

    my_before, my_path_before = shortest_path_cost_and_path(me_set, opp_set, color)
    opp_before, opp_path_before = shortest_path_cost_and_path(opp_set, me_set, opp_color)

    best_move = None
    best_score = -10**18

    for mv in candidates:
        new_me = set(me_set)
        new_me.add(mv)

        if connected(new_me, color):
            return mv

        my_after, _ = shortest_path_cost_and_path(new_me, opp_set, color)
        opp_after, _ = shortest_path_cost_and_path(opp_set, new_me, opp_color)

        score = 0.0
        score += 20.0 * (my_before - my_after)
        score += 18.0 * (opp_after - opp_before)

        if mv in my_path_before:
            score += 2.8
        if mv in opp_path_before:
            score += 2.4

        score += local_shape_score(mv, me_set, opp_set)
        score += center_score(mv)

        # Slight side-orientation preference
        r, c = mv
        if color == 'b':
            score += -0.03 * abs(c - 5)
        else:
            score += -0.03 * abs(r - 5)

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)

    occupied = me_set | opp_set
    empties = [(r, c) for r in range(N) for c in range(N) if (r, c) not in occupied]

    # Guaranteed legal fallback
    if not empties:
        return (0, 0)

    # Opening: center is usually strong
    if not me and not opp and (5, 5) in empties:
        return (5, 5)

    # 1) Immediate winning move
    winning_moves = []
    for mv in empties:
        new_me = set(me_set)
        new_me.add(mv)
        if connected(new_me, color):
            winning_moves.append(mv)
    if winning_moves:
        # Pick the best among winning moves, typically more central / connected
        best = None
        best_s = -10**18
        for mv in winning_moves:
            s = local_shape_score(mv, me_set, opp_set) + center_score(mv)
            if s > best_s:
                best_s = s
                best = mv
        return best

    # 2) Block opponent immediate winning move(s)
    opp_color = 'w' if color == 'b' else 'b'
    opp_winning_moves = []
    for mv in empties:
        new_opp = set(opp_set)
        new_opp.add(mv)
        if connected(new_opp, opp_color):
            opp_winning_moves.append(mv)

    if opp_winning_moves:
        # Must block one of these if possible
        move = choose_best(opp_winning_moves, me_set, opp_set, color)
        if move is not None and move in empties:
            return move

    # 3) General evaluation over all legal moves
    move = choose_best(empties, me_set, opp_set, color)
    if move is not None and move in empties:
        return move

    # Final safety fallback
    return empties[0]
