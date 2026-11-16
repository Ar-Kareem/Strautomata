
import random
from collections import deque
from typing import List, Tuple

N = 11  # board size

# neighbour offsets for a hex grid (all 8 neighbours except (‑1,‑1) and (+1,+1))
NEIGH = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]

INF = 10 ** 9


def _inside(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _build_board(me: List[Tuple[int, int]], opp: List[Tuple[int, int]]) -> List[List[int]]:
    """
    Returns a board where
        1  -> our stone
        -1 -> opponent stone
        0  -> empty
    """
    board = [[0] * N for _ in range(N)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = -1
    return board


def _zero_one_bfs(board: List[List[int]], side_cells: List[Tuple[int, int]]) -> List[List[int]]:
    """
    0‑1 BFS from a set of starting cells.
    Cost to step onto a cell = 0 if our stone, 1 if empty, INF if opponent.
    Returns a distance matrix.
    """
    dist = [[INF] * N for _ in range(N)]
    dq = deque()

    for r, c in side_cells:
        if board[r][c] == -1:          # opponent blocks this side cell
            continue
        w = 0 if board[r][c] == 1 else 1   # our stone -> 0, empty -> 1
        dist[r][c] = w
        if w == 0:
            dq.appendleft((r, c))
        else:
            dq.append((r, c))

    while dq:
        r, c = dq.popleft()
        d_cur = dist[r][c]
        for dr, dc in NEIGH:
            nr, nc = r + dr, c + dc
            if not _inside(nr, nc):
                continue
            cell_val = board[nr][nc]
            if cell_val == -1:          # opponent stone – cannot pass
                continue
            w = 0 if cell_val == 1 else 1
            nd = d_cur + w
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                if w == 0:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))
    return dist


def _side_cells(color: str, start: bool) -> List[Tuple[int, int]]:
    """Return the list of coordinates belonging to the chosen side."""
    cells = []
    if color == 'b':               # black connects top ↔ bottom
        if start:                  # top side
            rows = [0]
            cols = range(N)
        else:                      # bottom side
            rows = [N - 1]
            cols = range(N)
        for r in rows:
            for c in cols:
                cells.append((r, c))
    else:                         # white connects left ↔ right
        if start:                  # left side
            cols = [0]
            rows = range(N)
        else:                      # right side
            cols = [N - 1]
            rows = range(N)
        for r in rows:
            for c in cols:
                cells.append((r, c))
    return cells


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    """
    Return a legal move (row, col) for the current player.
    The move is chosen to minimise the number of empty cells that still
    have to be occupied to connect the two opposite sides.
    """
    board = _build_board(me, opp)

    # distance from our start side and from our target side
    start_side = _side_cells(color, start=True)
    target_side = _side_cells(color, start=False)

    dist_start = _zero_one_bfs(board, start_side)
    dist_target = _zero_one_bfs(board, target_side)

    best_move = None
    best_score = INF

    # examine every empty cell
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:        # not empty
                continue
            d1 = dist_start[r][c]
            d2 = dist_target[r][c]
            if d1 == INF or d2 == INF:
                continue                # cell cannot belong to any path currently
            score = d1 + d2 - 1          # after playing here its cost becomes 0
            if score < best_score:
                best_score = score
                best_move = (r, c)

    # If for any reason we did not find a candidate (should not happen), pick random empty
    if best_move is None:
        empties = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        best_move = random.choice(empties)

    return best_move
