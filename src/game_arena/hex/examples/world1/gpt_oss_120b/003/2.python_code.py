
import heapq
import random
from typing import List, Tuple, Set

# board size
N = 11
INF = 10 ** 9

def neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    """Six hex neighbours according to the problem statement."""
    cand = [
        (r - 1, c), (r - 1, c + 1),
        (r, c - 1), (r, c + 1),
        (r + 1, c - 1), (r + 1, c)
    ]
    return [(i, j) for i, j in cand if 0 <= i < N and 0 <= j < N]

def bfs_connect(stones: Set[Tuple[int, int]],
                start_cells: Set[Tuple[int, int]],
                goal_cells: Set[Tuple[int, int]]) -> bool:
    """True iff there is a path of `stones` from any start cell to any goal cell."""
    seen = set()
    stack = list(start_cells & stones)
    while stack:
        v = stack.pop()
        if v in goal_cells:
            return True
        for nb in neighbors(*v):
            if nb in stones and nb not in seen:
                seen.add(nb)
                stack.append(nb)
    return False

def shortest_path_cost(me: Set[Tuple[int, int]],
                       opp: Set[Tuple[int, int]],
                       extra_zero: Set[Tuple[int, int]],
                       start: Set[Tuple[int, int]],
                       goal: Set[Tuple[int, int]]) -> int:
    """
    Dijkstra on the board where:
        own stone or cell in extra_zero -> cost 0
        empty                           -> cost 1
        opponent stone                  -> cost INF
    Returns minimal cost to reach any goal cell.
    """
    dist = [[INF] * N for _ in range(N)]
    heap = []

    for r, c in start:
        if (r, c) in opp:
            continue          # cannot start on opponent stone
        cost = 0 if (r, c) in me or (r, c) in extra_zero else 1
        dist[r][c] = cost
        heapq.heappush(heap, (cost, r, c))

    while heap:
        d, r, c = heapq.heappop(heap)
        if d != dist[r][c]:
            continue
        if (r, c) in goal:
            return d
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp:
                continue
            nd = d + (0 if (nr, nc) in me or (nr, nc) in extra_zero else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heapq.heappush(heap, (nd, nr, nc))
    return INF

def immediate_win_or_block(me: Set[Tuple[int, int]],
                           opp: Set[Tuple[int, int]],
                           color: str) -> None:
    """Detect one‑move win for us or opponent and return the needed cell."""
    # define side cells
    if color == 'b':   # black: top ↔ bottom
        start = {(0, c) for c in range(N)}
        goal  = {(N - 1, c) for c in range(N)}
        opp_start = {(0, c) for c in range(N)}
        opp_goal  = {(N - 1, c) for c in range(N)}
    else:               # white: left ↔ right
        start = {(r, 0) for r in range(N)}
        goal  = {(r, N - 1) for r in range(N)}
        opp_start = {(r, 0) for r in range(N)}
        opp_goal  = {(r, N - 1) for r in range(N)}

    empty = {(r, c) for r in range(N) for c in range(N)} - me - opp

    # opponent threat?
    for cell in empty:
        if bfs_connect(opp | {cell}, opp_start, opp_goal):
            return cell  # block

    # our winning move?
    for cell in empty:
        if bfs_connect(me | {cell}, start, goal):
            return cell

    return None

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           color: str) -> Tuple[int, int]:
    me_set = set(me)
    opp_set = set(opp)
    empty = {(r, c) for r in range(N) for c in range(N)} - me_set - opp_set

    # 1. Immediate win / block
    urgent = immediate_win_or_block(me_set, opp_set, color)
    if urgent is not None:
        return urgent

    # 2. Prepare side sets
    if color == 'b':   # black: top ↔ bottom
        start = {(0, c) for c in range(N)}
        goal  = {(N - 1, c) for c in range(N)}
    else:               # white: left ↔ right
        start = {(r, 0) for r in range(N)}
        goal  = {(r, N - 1) for r in range(N)}

    # current best distance (without extra move)
    base_dist = shortest_path_cost(me_set, opp_set, set(), start, goal)

    best_cell = None
    best_improve = -INF
    best_dist = base_dist

    # evaluate every empty cell
    for cell in empty:
        new_dist = shortest_path_cost(me_set, opp_set, {cell}, start, goal)
        improve = base_dist - new_dist
        if improve > best_improve or (improve == best_improve and new_dist < best_dist):
            best_improve = improve
            best_dist = new_dist
            best_cell = cell
        elif improve == best_improve and best_cell is not None:
            # tie‑breaker: pick the cell nearer the centre
            def dist_center(x):
                return abs(x[0] - (N - 1) / 2) + abs(x[1] - (N - 1) / 2)
            if dist_center(cell) < dist_center(best_cell):
                best_cell = cell

    # 3. Fallback – centre if something went wrong
    if best_cell is None:
        centre = (N // 2, N // 2)
        if centre in empty:
            return centre
        return random.choice(list(empty))

    return best_cell
