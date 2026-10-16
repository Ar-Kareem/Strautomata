
from __future__ import annotations
from collections import deque
import math
import random

BOARD_N = 11

# Neighbor relation for Hex on a skewed grid representation (row, col).
# Using the commonly used axial-like adjacency for 2D array:
# Neighbors: (r-1,c), (r+1,c), (r,c-1), (r,c+1), (r-1,c+1), (r+1,c-1)
NEIGHBORS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    my = set(me)
    en = set(opp)

    # Legal moves are those not occupied.
    empties = [(r, c) for r in range(BOARD_N) for c in range(BOARD_N) if (r, c) not in my and (r, c) not in en]

    # Safety: if no empties, shouldn't happen in Hex, but return something legal fallback.
    if not empties:
        return (0, 0)

    # Determine target edges based on color.
    # Black connects top (row 0) to bottom (row N-1).
    # White connects left (col 0) to right (col N-1).
    if color == 'b':
        my_start = [(0, c) for c in range(BOARD_N)]
        my_goal_cols = set()  # not used
        def is_my_goal(cell: tuple[int, int]) -> bool:
            r, c = cell
            return r == BOARD_N - 1
        def is_my_start(cell: tuple[int, int]) -> bool:
            r, c = cell
            return r == 0
    else:  # 'w'
        my_start = [(r, 0) for r in range(BOARD_N)]
        def is_my_goal(cell: tuple[int, int]) -> bool:
            r, c = cell
            return c == BOARD_N - 1
        def is_my_start(cell: tuple[int, int]) -> bool:
            r, c = cell
            return c == 0

    # Opponent edges
    opp_color = 'w' if color == 'b' else 'b'
    if opp_color == 'b':
        def is_opp_goal(cell: tuple[int, int]) -> bool:
            r, c = cell
            return r == BOARD_N - 1
        def is_opp_start(cell: tuple[int, int]) -> bool:
            r, c = cell
            return r == 0
    else:
        def is_opp_goal(cell: tuple[int, int]) -> bool:
            r, c = cell
            return c == BOARD_N - 1
        def is_opp_start(cell: tuple[int, int]) -> bool:
            r, c = cell
            return c == 0

    def inb(r: int, c: int) -> bool:
        return 0 <= r < BOARD_N and 0 <= c < BOARD_N

    def neighbors(cell: tuple[int, int]):
        r, c = cell
        for dr, dc in NEIGHBORS:
            rr, cc = r + dr, c + dc
            if inb(rr, cc):
                yield (rr, cc)

    def has_winning_path(stones: set[tuple[int, int]], starter_pred, goal_pred) -> bool:
        # BFS over own stones only.
        # Start from stones that touch the starting edge.
        q = deque()
        visited = set()
        for s in stones:
            if starter_pred(s):
                q.append(s)
                visited.add(s)
        while q:
            cur = q.popleft()
            if goal_pred(cur):
                return True
            for nb in neighbors(cur):
                if nb in stones and nb not in visited:
                    visited.add(nb)
                    q.append(nb)
        return False

    def shortest_connection_distance(stones_you: set[tuple[int, int]], stones_block: set[tuple[int, int]],
                                        start_pred, goal_pred) -> int:
        # Dijkstra/BFS where:
        # - stepping onto an existing stone cost 0
        # - stepping onto empty cost 1
        # - stepping onto opponent stone is forbidden
        # We compute minimal "number of empty cells" needed.
        # Graph nodes are all cells; edges between neighboring cells with cost of destination cell.
        # Standard 0-1 BFS.
        INF = 10**9
        dist = {cell: INF for cell in [(r, c) for r in range(BOARD_N) for c in range(BOARD_N)]}
        dq = deque()

        # Initialize frontier from start edge cells.
        for r in range(BOARD_N):
            for c in range(BOARD_N):
                cell = (r, c)
                if not start_pred(cell):
                    continue
                if cell in stones_block:
                    continue
                cost = 0 if cell in stones_you else 1
                if cost < dist[cell]:
                    dist[cell] = cost
                    if cost == 0:
                        dq.appendleft(cell)
                    else:
                        dq.append(cell)

        best = INF
        while dq:
            cur = dq.popleft()
            dcur = dist[cur]
            if dcur >= best:
                continue
            if goal_pred(cur):
                best = min(best, dcur)
                # Can't early-exit fully since 0-1 BFS; but this is good enough.
            for nb in neighbors(cur):
                if nb in stones_block:
                    continue
                nd = dcur + (0 if nb in stones_you else 1)
                if nd < dist[nb]:
                    dist[nb] = nd
                    if nd == 0:
                        dq.appendleft(nb)
                    else:
                        dq.append(nb)
        return best

    # 1) Win in one move
    for mv in empties:
        new_my = my | {mv}
        if has_winning_path(new_my, is_my_start, is_my_goal):
            return mv

    # 2) Block opponent win in one move
    for mv in empties:
        new_opp = en | {mv}
        if has_winning_path(new_opp, is_opp_start, is_opp_goal):
            return mv

    # 3) Evaluate moves by connectivity distances
    # Defensive weight: value opponent distance after our move.
    # Smaller distance means closer to connection; we want to minimize our distance and maximize opp distance.
    # We'll use: score = our_dist - A*opp_dist
    # Lower is better.
    A = 0.85

    # Precompute current distances for slight normalization (not required but helps).
    my_dist_now = shortest_connection_distance(my, en, is_my_start, is_my_goal)
    opp_dist_now = shortest_connection_distance(en, my, is_opp_start, is_opp_goal)

    def edge_bonus(cell):
        r, c = cell
        if color == 'b':
            # Encourage top/bottom proximity
            return (1 if r == 0 else 0) * 0.15 + (1 if r == BOARD_N - 1 else 0) * 0.15 + (10 - abs(r - (BOARD_N-1)/2)) * 0.005
        else:
            return (1 if c == 0 else 0) * 0.15 + (1 if c == BOARD_N - 1 else 0) * 0.15 + (10 - abs(c - (BOARD_N-1)/2)) * 0.005

    def neighbor_support(cell, stones: set[tuple[int, int]]):
        # Count adjacent stones of 'stones'
        return sum(1 for nb in neighbors(cell) if nb in stones)

    best_moves = []
    best_score = None

    # Add a small random jitter to break ties (determinism not required).
    rng = random.Random(12345)

    for mv in empties:
        # If we place mv, update sets virtually.
        # Our distance computed treating opponent stones as blocked.
        # Opp distance computed treating our stones (including mv) as blocked.
        new_my = my | {mv}

        # Compute connectivity distances
        my_dist = shortest_connection_distance(new_my, en, is_my_start, is_my_goal)
        opp_dist = shortest_connection_distance(en, new_my, is_opp_start, is_opp_goal)

        # Heuristic score
        score = (my_dist - my_dist_now) - A * (opp_dist - opp_dist_now)

        # Tie-breakers:
        score -= 0.02 * neighbor_support(mv, new_my)          # prefer connecting to our network
        score -= 0.01 * neighbor_support(mv, en)             # if we touch opponent, may be needed to block (small)
        score -= edge_bonus(mv)

        # Jitter to avoid pathological ties
        score += rng.uniform(-1e-4, 1e-4)

        if best_score is None or score < best_score - 1e-12:
            best_score = score
            best_moves = [mv]
        elif abs(score - best_score) <= 1e-12:
            best_moves.append(mv)

    # Choose among best moves (deterministically with a hash-like rule)
    # to be stable: pick the move with max support then min distance (recheck).
    if len(best_moves) == 1:
        return best_moves[0]

    # secondary selection
    def secondary(cell):
        new_my = my | {cell}
        my_dist = shortest_connection_distance(new_my, en, is_my_start, is_my_goal)
        opp_dist = shortest_connection_distance(en, new_my, is_opp_start, is_opp_goal)
        return ( -neighbor_support(cell, new_my),  my_dist, -opp_dist, cell[0], cell[1])

    best_moves.sort(key=secondary)
    return best_moves[0]
