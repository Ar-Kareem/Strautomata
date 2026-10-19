
#!/usr/bin/env python3
import random
from collections import deque

N = 11                # board size
INF = 10**9           # used as “infinite” distance

# --------------------------------------------------------------
# Helper: hex‑grid neighbours for a cell (0‑based row, column)
# --------------------------------------------------------------
def hex_neighbors(r: int, c: int):
    """
    Return a list of valid neighbour coordinates for (r,c) on an
    11×11 hex board.  The neighbour pattern changes depending on the row
    parity (even/odd) as described in the problem statement.
    """
    # even row – e.g. (4,1) : (4,0) (4,2) (3,1) (3,2) (5,1) (5,0)
    if r % 2 == 0:
        offsets = [(0, -1), (0, +1), (-1, 0), (-1, +1),
                   (+1, 0), (+1, -1)]
    else:  # odd row – pattern is shifted
        offsets = [(0, -1), (0, +1), (-1, -1), (-1, 0),
                   (+1, 0), (+1, +1)]

    return [(r + dr, c + dc)
            for dr, dc in offsets
            if 0 <= r + dr < N and 0 <= c + dc < N]


# --------------------------------------------------------------
# Multi‑source BFS from a set of source cells; occupied cells are walls
# --------------------------------------------------------------
def bfs_start(sources, occupied):
    """
    Perform BFS from all source cells that are empty.  Return a 2‑D array
    of shortest distances (0 for source cells, INF for unreachable).
    """
    dist = [[INF] * N for _ in range(N)]
    q = deque()

    for sr, sc in sources:
        if (sr, sc) not in occupied:          # source must be empty
            dist[sr][sc] = 0
            q.append((sr, sc))

    while q:
        r, c = q.popleft()
        d = dist[r][c]
        for nr, nc in hex_neighbors(r, c):
            if dist[nr][nc] == INF and (nr, nc) not in occupied:
                dist[nr][nc] = d + 1
                q.append((nr, nc))
    return dist


# --------------------------------------------------------------
# Policy implementation
# --------------------------------------------------------------
def policy(me: list[tuple[int, int]],
          opp: list[tuple[int, int]],
          color: str) -> tuple[int, int]:
    """
    Return a legal move (row, col) for the current player.
    """
    # fast look‑ups
    me_set = set(map(tuple, me))
    opp_set = set(map(tuple, opp))
    occupied = me_set | opp_set

    # all legal moves
    empty_cells = [(r, c)
                   for r in range(N) for c in range(N)
                   if (r, c) not in occupied]
    if not empty_cells:               # safety fallback
        return (0, 0)

    # ----------------------------------------------------------
    # 1) Immediate opponent threats – block them first
    # ----------------------------------------------------------
    opponent_threat = []
    for cell in empty_cells:
        # count how many opponent stones are adjacent to this empty cell
        cnt = sum(1 for o in opp_set if cell in hex_neighbors(o[0], o[1]))
        if cnt >= 2:
            opponent_threat.append(cell)
    if opponent_threat:
        # any threat cell wins the opponent next turn; block the first one
        return opponent_threat[0]

    # ----------------------------------------------------------
    # 2) Compute distances to our two goal sides
    # ----------------------------------------------------------
    if color == 'b':                     # black: top ↔ bottom
        top_cells = [(0, c) for c in range(N)]
        bot_cells = [(N-1, c) for c in range(N)]
        top_dist = bfs_start(top_cells, occupied)
        bot_dist = bfs_start(bot_cells, occupied)

        def total(cell):
            r, c = cell
            return top_dist[r][c] + bot_dist[r][c]
    else:                               # white: left ↔ right
        left_cells = [(r, 0) for r in range(N)]
        right_cells = [(r, N-1) for r in range(N)]
        left_dist = bfs_start(left_cells, occupied)
        right_dist = bfs_start(right_cells, occupied)

        def total(cell):
            r, c = cell
            return left_dist[r][c] + right_dist[r][c]

    # ----------------------------------------------------------
    # 3) Choose the best empty cell according to our heuristic
    # ----------------------------------------------------------
    best_total = INF
    best_candidates = []                # (total, degree, cell)

    for cell in empty_cells:
        t = total(cell)
        if t == INF:                    # unreachable to one side → ignore
            continue

        # degree = number of our stones touching the cell
        degree = sum(1 for nb in hex_neighbors(cell[0], cell[1])
                     if nb in me_set)

        # keep the best so far
        if t < best_total or (t == best_total and degree > best_total):
            best_total = t
            best_candidates = [(t, degree, cell)]
        elif t == best_total and degree == best_total:
            best_candidates.append((t, degree, cell))

    # If every cell was unreachable, fall back to a random legal move
    if not best_candidates:
        return random.choice(empty_cells)

    # Sort: primary key = total distance, secondary = degree,
    # tie‑breaker = random to avoid deterministic patterns
    best_candidates.sort(key=lambda x: (x[0], x[1], random.random()))
    return best_candidates[0][2]
