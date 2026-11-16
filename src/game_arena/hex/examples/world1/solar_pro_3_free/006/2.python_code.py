
from collections import deque
import random
from typing import List, Tuple

BOARD_SIZE = 11
INF = 10**9

def _neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    """Return the six neighbours of (r,c) in the axial‑coordinate representation."""
    return [(r - 1, c), (r - 1, c + 1),
            (r + 1, c), (r + 1, c + 1),
            (r, c - 1), (r, c + 1)]

def _bfs(start_set: List[Tuple[int, int]],
         blocked: set,
         size: int = BOARD_SIZE) -> dict:
    """Breadth‑first search from the cells in start_set, treating blocked cells as walls."""
    dist = {}
    q = deque()
    # initialise distances for start cells that are not blocked
    for cell in start_set:
        if cell not in blocked:
            dist[cell] = 0
            q.append(cell)

    while q:
        cur = q.popleft()
        d = dist[cur]
        for nb in _neighbors(cur[0], cur[1]):
            if 0 <= nb[0] < size and 0 <= nb[1] < size:
                nxt = nb
                if nxt not in dist and nxt not in blocked:
                    dist[nxt] = d + 1
                    q.append(nxt)
    return dist

def _empty_cells(me: List[Tuple[int, int]], opp: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    my_set = set(me)
    opp_set = set(opp)
    return [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
            if (r, c) not in my_set and (r, c) not in opp_set]

def policy(me: List[Tuple[int, int]],
          opp: List[Tuple[int, int]],
          color: str) -> Tuple[int, int]:
    # Convert to sets for fast membership checks
    my_set = set(me)
    opp_set = set(opp)

    # Determine which sides belong to me and which belong to the opponent
    if color == 'b':           # Black – connect top and bottom
        my_targets = [(0, c) for c in range(BOARD_SIZE)],   # top row
        [(size - 1, c) for c in range(BOARD_SIZE)]        # bottom row
        opp_targets = [(r, 0) for r in range(BOARD_SIZE)],   # left column
        [(r, size - 1) for r in range(BOARD_SIZE)]        # right column
    elif color == 'w':         # White – connect left and right
        my_targets = [(r, 0) for r in range(BOARD_SIZE)],   # left column
        [(r, size - 1) for r in range(BOARD_SIZE)]        # right column
        opp_targets = [(0, c) for c in range(BOARD_SIZE)],   # top row
        [(size - 1, c) for c in range(BOARD_SIZE)]        # bottom row
    else:
        raise ValueError("color must be 'b' or 'w'")

    # Run BFSs from the start cells
    # my stones are passable, opponent stones are blocked for my connectivity
    my_dist_top = _bfs(my_targets[0], opp_set)
    my_dist_bottom = _bfs(my_targets[1], opp_set)

    # opponent stones are passable, my stones are blocked for opponent connectivity
    opp_dist_left = _bfs(opp_targets[0], my_set)
    opp_dist_right = _bfs(opp_targets[1], my_set)

    empty = _empty_cells(me, opp)
    best_move = None
    best_score = -INF

    # Helper to evaluate a candidate cell
    def evaluate(r: int, c: int) -> Tuple[int, int]:
        nonlocal best_move, best_score
        cell = (r, c)
        # Determine which sides belong to me (according to colour)
        if color == 'b':
            own_dist = my_dist_top.get(cell, INF) + my_dist_bottom.get(cell, INF)
            opp_dist = opp_dist_left.get(cell, INF) + opp_dist_right.get(cell, INF)
        else:  # color == 'w'
            own_dist = opp_dist_left.get(cell, INF) + opp_dist_right.get(cell, INF)
            opp_dist = my_dist_top.get(cell, INF) + my_dist_bottom.get(cell, INF)

        advantage = opp_dist - own_dist
        # Count empty neighbours (freedom)
        freedoms = 0
        for nb in _neighbors(r, c):
            if (nb[0], nb[1]) in empty:
                freedoms += 1

        # Very generous weight for advantage so it dominates freedom counts
        score = advantage * 1000 + freedoms

        if score > best_score:
            best_score = score
            best_move = cell
        elif score == best_score:
            # random tie‑break to diversify play
            if random.random() > 0.5:
                best_move = cell

    # 1️⃣ Immediate win detection
    if color == 'b':
        for r, c in empty:
            d_top = my_dist_top.get((r, c))
            d_bot = my_dist_bottom.get((r, c))
            if d_top is not None and d_bot is not None and d_top + d_bot <= 2:
                # This move would connect the two sides in one step
                return (r, c)
    else:  # white
        for r, c in empty:
            d_left = opp_dist_left.get((r, c))
            d_right = opp_dist_right.get((r, c))
            if d_left is not None and d_right is not None and d_left + d_right <= 2:
                return (r, c)

    # 2️⃣ Heuristic evaluation
    for r, c in empty:
        evaluate(r, c)

    # 3️⃣ Fallback – random legal move
    if best_move is None:
        best_move = random.choice(empty)

    return best_move
