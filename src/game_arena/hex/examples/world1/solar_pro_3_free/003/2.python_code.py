
import random
from collections import deque
from typing import List, Tuple

# Hex board size
BOARD_SIZE = 11

# Neighbor offsets for a hexagonal grid
NEIGH: List[Tuple[int, int]] = [(-1, 0), (-1, 1),
                                (0, -1), (0, 1),
                                (1, 0), (1, -1)]

def bfs(sources: List[Tuple[int, int]], traversable: set) -> dict:
    """
    Multi‑source BFS returning the shortest distance from any source to every reachable cell.
    Reachable cells are those in `traversable` (including the sources themselves).
    Cells not reachable are omitted from the dict.
    """
    dist = {}
    for src in sources:
        if src in traversable:
            dist[src] = 0
    if not dist:
        return {}                     # no starting points

    q = deque(dist.keys())
    while q:
        r, c = q.popleft()
        d = dist[(r, c)]
        for dr, dc in NEIGH:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                nb = (nr, nc)
                if nb in traversable and nb not in dist:
                    dist[nb] = d + 1
                    q.append(nb)
    return dist

def policy(me: List[Tuple[int, int]],
          opp: List[Tuple[int, int]],
          color: str) -> Tuple[int, int]:
    """
    Choose a legal move for the current player.
    `me` – list of (row, col) coordinates occupied by this player.
    `opp` – list of coordinates occupied by the opponent.
    `color` – 'b' for black (connect top‑bottom) or 'w' for white (connect left‑right).
    Returns (row, col) of the chosen empty cell.
    """
    # Convert input lists to sets for fast lookup
    me_set = set(me)
    opp_set = set(opp)

    # All cells on the board
    board = {(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)}
    empties = board - (me_set | opp_set)          # legal moves

    # Determine side cells depending on player colour
    if color == 'b':  # black: top‑bottom
        my_sides = {(0, c) for c in range(BOARD_SIZE)} | {(10, c) for c in range(BOARD_SIZE)}
        opp_sides = {(r, 0) for r in range(BOARD_SIZE)} | {(r, 10) for r in range(BOARD_SIZE)}
    else:  # white: left‑right
        my_sides = {(r, 0) for r in range(BOARD_SIZE)} | {(r, 10) for r in range(BOARD_SIZE)}
        opp_sides = {(0, c) for c in range(BOARD_SIZE)} | {(10, c) for c in range(BOARD_SIZE)}

    # Cells considered walkable for each player (own stones + empty cells)
    traversable_me = me_set | empties
    traversable_opp = opp_set | empties

    # Sources are side cells that are actually walkable
    sources_me = list(my_sides - opp_set)          # side cells not occupied by opponent
    sources_opp = list(opp_sides - me_set)         # side cells not occupied by us

    # Run BFS from each player's sides
    dist_me = bfs(sources_me, traversable_me)
    dist_opp = bfs(sources_opp, traversable_opp)

    INF = 10**9
    best_score = INF
    best_moves = []

    for cell in empties:
        d_me = dist_me.get(cell, INF)
        d_opp = dist_opp.get(cell, INF)
        score = d_me + d_opp
        if score < best_score:
            best_score = score
            best_moves = [cell]
        elif score == best_score:
            best_moves.append(cell)

    # Random tie‑break (any deterministic choice also works)
    move = random.choice(best_moves)

    # Ensure the move is legal (it always will be because `move` ∈ empties)
    return move

# The module API requires the function `policy` to be defined.
# It will be imported and called by the arena evaluator.
