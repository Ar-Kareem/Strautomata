
import collections
from typing import List, Tuple, Set

# ----------------------------------------------------------------------
# Helper functions -----------------------------------------------------
# ----------------------------------------------------------------------

def neighbors(i: int, j: int) -> List[Tuple[int, int]]:
    """Hex neighbours according to the description."""
    dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    res = []
    for di, dj in dirs:
        ni, nj = i + di, j + dj
        if 0 <= ni < 11 and 0 <= nj < 11:
            res.append((ni, nj))
    return res


def shortest_path_len(color: str,
                      my_set: Set[Tuple[int, int]],
                      opp_set: Set[Tuple[int, int]]) -> int:
    """
    0‑1 BFS: returns the minimal number of empty cells that must be filled
    for `color` to connect its two sides, given our stones `my_set`
    and opponent stones `opp_set`.  Returns a large number if no path exists.
    """
    INF = 10 ** 9
    dist = [[INF] * 11 for _ in range(11)]
    dq = collections.deque()

    # initialise start frontier
    if color == 'b':            # Black connects top (row 0) ↔ bottom (row 10)
        start_rows = [0]
        goal_rows = [10]
        start_cells = [(0, c) for c in range(11)]
    else:                       # White connects left (col 0) ↔ right (col 10)
        start_rows = [0]
        goal_rows = [10]
        start_cells = [(r, 0) for r in range(11)]

    for i, j in start_cells:
        if (i, j) in opp_set:
            continue            # blocked by opponent
        cost = 0 if (i, j) in my_set else 1
        if dist[i][j] > cost:
            dist[i][j] = cost
            if cost == 0:
                dq.appendleft((i, j))
            else:
                dq.append((i, j))

    # 0‑1 BFS
    while dq:
        i, j = dq.popleft()
        cur = dist[i][j]
        for ni, nj in neighbors(i, j):
            if (ni, nj) in opp_set:
                continue        # cannot step onto opponent stone
            ncost = 0 if (ni, nj) in my_set else 1
            nd = cur + ncost
            if nd < dist[ni][nj]:
                dist[ni][nj] = nd
                if ncost == 0:
                    dq.appendleft((ni, nj))
                else:
                    dq.append((ni, nj))

    # extract best distance among goal cells
    best = INF
    if color == 'b':
        for c in range(11):
            best = min(best, dist[10][c])
    else:
        for r in range(11):
            best = min(best, dist[r][10])
    return best


# ----------------------------------------------------------------------
# Policy ---------------------------------------------------------------
# ----------------------------------------------------------------------

def policy(me: List[Tuple[int, int]],
           opp: List[Tuple[int, int]],
           color: str) -> Tuple[int, int]:
    """
    Returns a legal move (row, col) for `color` on an 11×11 Hex board.
    The move is chosen by minimising our own shortest‑path length
    and, secondarily, maximising the opponent's shortest‑path length.
    """
    my_set = set(me)
    opp_set = set(opp)

    # pre‑compute opponent colour
    opp_color = 'w' if color == 'b' else 'b'

    # all empty cells
    empty = [(i, j) for i in range(11) for j in range(11)
             if (i, j) not in my_set and (i, j) not in opp_set]

    best_move = None
    best_my_dist = 10 ** 9
    best_opp_dist = -1

    for cell in empty:
        # our distance after playing this cell
        my_new_dist = shortest_path_len(color,
                                        my_set | {cell},
                                        opp_set)

        # opponent distance after we block this cell
        opp_new_dist = shortest_path_len(opp_color,
                                         opp_set,
                                         my_set | {cell})

        # primary: minimise my distance
        if my_new_dist < best_my_dist:
            best_my_dist = my_new_dist
            best_opp_dist = opp_new_dist
            best_move = cell
        # secondary: maximise opponent distance when tied
        elif my_new_dist == best_my_dist and opp_new_dist > best_opp_dist:
            best_opp_dist = opp_new_dist
            best_move = cell

    # fallback (should never happen) – pick first empty cell
    if best_move is None:
        best_move = empty[0]
    return best_move
