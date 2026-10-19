
import numpy as np
from collections import deque
from typing import List, Tuple, Set

# Hex adjacency offsets (the six touching cells, excluding (i-1,j-1) and (i+1,j+1))
NEIGHBORS = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, 0), (1, -1)]

def bfs_distance(
    me: Set[Tuple[int, int]],
    opp: Set[Tuple[int, int]],
    start_cells: List[Tuple[int, int]],
) -> np.ndarray:
    """
    Compute shortest “distance” from the given start cells to every board cell.
    Moving onto an opponent stone is prohibited.
    Moving onto an empty cell costs 1, moving onto a friendly stone costs 0.
    Returns a 11x11 integer matrix with INF = 10**9 for unreachable cells.
    """
    INF = 10 ** 9
    dist = np.full((11, 11), INF, dtype=int)
    dq = deque()
    for r, c in start_cells:
        dist[r, c] = 0
        dq.append((r, c))

    while dq:
        r, c = dq.popleft()
        d = dist[r, c]
        # 0‑1 BFS: push zero‑cost moves to the right side, one‑cost moves to the left side
        for dr, dc in NEIGHBORS:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 11 and 0 <= nc < 11):
                continue
            if (nr, nc) in opp:
                continue          # cannot walk through opponent stones
            nd = d if (nr, nc) in me else d + 1
            if nd < dist[nr, nc]:
                dist[nr, nc] = nd
                if nd == d:
                    dq.append((nr, nc))
                else:
                    dq.appendleft((nr, nc))

    return dist


def has_winning_move(move: Tuple[int, int],
                    me: Set[Tuple[int, int]],
                    opp: Set[Tuple[int, int]],
                    color: str) -> bool:
    """
    After temporarily playing `move`, check whether our stones connect the required sides.
    Returns True if the move is an instant win.
    """
    new_me = set(me)
    new_me.add(move)

    visited: Set[Tuple[int, int]] = set()
    win = False

    if color == 'b':  # black: connect top (row 0) and bottom (row 10)
        for stone in new_me:
            if stone in visited:
                continue
            stack = [(stone)]
            visited.add(stone)
            top_flag = False
            bot_flag = False
            while stack:
                cur = stack.pop()
                if cur[0] == 0:
                    top_flag = True
                if cur[0] == 10:
                    bot_flag = True
                for dr, dc in NEIGHBORS:
                    nxt = (cur[0] + dr, cur[1] + dc)
                    if nxt in new_me and nxt not in visited:
                        visited.add(nxt)
                        stack.append(nxt)
            if top_flag and bot_flag:
                win = True
                break
    else:  # white: connect left (col 0) and right (col 10)
        for stone in new_me:
            if stone in visited:
                continue
            stack = [(stone)]
            visited.add(stone)
            left_flag = False
            right_flag = False
            while stack:
                cur = stack.pop()
                if cur[1] == 0:
                    left_flag = True
                if cur[1] == 10:
                    right_flag = True
                for dr, dc in NEIGHBORS:
                    nxt = (cur[0] + dr, cur[1] + dc)
                    if nxt in new_me and nxt not in visited:
                        visited.add(nxt)
                        stack.append(nxt)
            if left_flag and right_flag:
                win = True
                break

    return win


def policy(me: List[Tuple[int, int]],
          opp: List[Tuple[int, int]],
          color: str) -> Tuple[int, int]:
    """
    Returns the next legal move for the given board state.
    """
    # Convert inputs to sets for O(1) membership tests
    me_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)

    # All empty cells on the 11x11 board
    empty_cells: List[Tuple[int, int]] = [
        (r, c) for r in range(11) for c in range(11)
        if (r, c) not in me_set and (r, c) not in opp_set
    ]

    # Helper to keep a sorted list of candidate moves
    candidates = []

    # --------------------------------------------------------------------
    # 1) Check for immediate winning moves
    # --------------------------------------------------------------------
    winning_moves = []
    for move in empty_cells:
        if has_winning_move(move, me_set, opp_set, color):
            winning_moves.append(move)

    if winning_moves:
        # pick the winning move that looks best according to the distance heuristic
        # (use the same distance maps as below)
        if color == 'b':
            # distances from top and bottom sides
            dist_top = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if r == 0])
            dist_bot = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if r == 10])
            win_scores = {}
            for mv in winning_moves:
                d_top = dist_top[mv]
                d_bot = dist_bot[mv]
                if d_top == INF or d_bot == INF:
                    continue          # unreachable side – ignore
                win_scores[mv] = d_top + d_bot
            # choose the one with smallest combined distance
            chosen = min(win_scores.items(), key=lambda x: x[1])[0]
        else:  # white
            dist_left = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if c == 0])
            dist_right = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if c == 10])
            win_scores = {}
            for mv in winning_moves:
                d_left = dist_left[mv]
                d_right = dist_right[mv]
                if d_left == INF or d_right == INF:
                    continue
                win_scores[mv] = d_left + d_right
            chosen = min(win_scores.items(), key=lambda x: x[1])[0]
        return chosen

    # --------------------------------------------------------------------
    # 2) No immediate win – select move with smallest distance‑to‑side sum
    # --------------------------------------------------------------------
    if color == 'b':
        dist_top = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if r == 0])
        dist_bot = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if r == 10])
        heuristic: List[Tuple[int, int]] = []
        for mv in empty_cells:
            d_top = dist_top[mv]
            d_bot = dist_bot[mv]
            if d_top == INF or d_bot == INF:
                continue
            heuristic.append((mv, d_top + d_bot))
        if heuristic:
            # choose smallest sum, tie‑break by row then column
            chosen = min(heuristic, key=lambda tup: (tup[1], tup[0][0], tup[0][1]))[0]
            return chosen
        # Fallback: all sums are INF (we have no stones on the required side yet)
        # pick the central empty cell to keep maximum flexibility
        empty_sorted = sorted(empty_cells, key=lambda rc: (rc[0], rc[1]))
        chosen = empty_sorted[len(empty_sorted) // 2]
        return chosen
    else:  # white
        dist_left = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if c == 0])
        dist_right = bfs_distance(me_set, opp_set, [(r, c) for r, c in me_set if c == 10])
        heuristic: List[Tuple[int, int]] = []
        for mv in empty_cells:
            d_left = dist_left[mv]
            d_right = dist_right[mv]
            if d_left == INF or d_right == INF:
                continue
            heuristic.append((mv, d_left + d_right))
        if heuristic:
            chosen = min(heuristic, key=lambda tup: (tup[1], tup[0][0], tup[0][1]))[0]
            return chosen
        # Fallback – centre
        empty_sorted = sorted(empty_cells, key=lambda rc: (rc[0], rc[1]))
        chosen = empty_sorted[len(empty_sorted) // 2]
        return chosen
