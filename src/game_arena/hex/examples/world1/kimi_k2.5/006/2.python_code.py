
import heapq
from collections import deque
from typing import List, Tuple, Set

SIZE = 11

def _neighbors(r: int, c: int) -> List[Tuple[int, int]]:
    """Return the 6 neighboring coordinates of a hex cell on an 11x11 board."""
    deltas = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0)]
    neigh = []
    for dr, dc in deltas:
        nr, nc = r + dr, c + dc
        if 0 <= nr < SIZE and 0 <= nc < SIZE:
            neigh.append((nr, nc))
    return neigh

def _shortest_path_cost(stones: Set[Tuple[int, int]], opp: Set[Tuple[int, int]], color: str) -> float:
    """
    0-1 BFS to compute shortest path cost.
    Cost: 0 for own stone, 1 for empty, infinity (unreachable) for opponent stone.
    Returns the minimum sum of costs to connect the two sides for `color`.
    """
    n = SIZE
    dist = [[float('inf')] * n for _ in range(n)]
    dq = deque()

    # Initialize frontier (source side)
    if color == 'b':  # Black: top (row 0) to bottom (row 10)
        for c in range(n):
            if (0, c) in opp:
                continue
            cost = 0 if (0, c) in stones else 1
            dist[0][c] = cost
            if cost == 0:
                dq.appendleft((0, c))
            else:
                dq.append((0, c))
    else:  # White: left (col 0) to right (col 10)
        for r in range(n):
            if (r, 0) in opp:
                continue
            cost = 0 if (r, 0) in stones else 1
            dist[r][0] = cost
            if cost == 0:
                dq.appendleft((r, 0))
            else:
                dq.append((r, 0))

    while dq:
        r, c = dq.popleft()
        d = dist[r][c]

        # Early exit if we reached the target side
        if color == 'b' and r == n - 1:
            return d
        if color == 'w' and c == n - 1:
            return d

        for nr, nc in _neighbors(r, c):
            if (nr, nc) in opp:
                continue
            nd = d + (0 if (nr, nc) in stones else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                if nd == d:
                    dq.appendleft((nr, nc))
                else:
                    dq.append((nr, nc))

    return float('inf')

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    me_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)
    opp_color = 'w' if color == 'b' else 'b'

    # Generate empty cells
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE)
             if (r, c) not in me_set and (r, c) not in opp_set]

    if not empty:
        # Should never happen in a legal game state
        return (0, 0)

    # Opening: take center on first move
    if len(me) == 0 and len(opp) == 0:
        return (SIZE // 2, SIZE // 2)

    # Check for immediate winning move
    for r, c in empty:
        me_set.add((r, c))
        if _shortest_path_cost(me_set, opp_set, color) == 0:
            return (r, c)
        me_set.remove((r, c))

    # Check if opponent can win immediately (path cost == 1) and block
    opp_current = _shortest_path_cost(opp_set, me_set, opp_color)
    if opp_current == 1:
        # Find a cell that would give opponent a win and block it
        for r, c in empty:
            opp_set.add((r, c))
            if _shortest_path_cost(opp_set, me_set, opp_color) == 0:
                opp_set.remove((r, c))
                return (r, c)
            opp_set.remove((r, c))

    # Evaluate all candidate moves
    best_score = -float('inf')
    best_move = empty[0]
    my_base = _shortest_path_cost(me_set, opp_set, color)

    for r, c in empty:
        # Simulate placing our stone
        me_set.add((r, c))
        my_new = _shortest_path_cost(me_set, opp_set, color)
        
        # Calculate opponent's path length after our move (we may have blocked them)
        opp_new = _shortest_path_cost(opp_set, me_set, opp_color)
        
        me_set.remove((r, c))

        # Scoring: higher is better. Prioritize reducing own path and increasing opponent's path.
        if my_new == float('inf'):
            score = -10000  # Losing position, avoid
        elif opp_new == float('inf'):
            score = 10000   # Opponent blocked, excellent
        else:
            score = (opp_new - my_new)

        # Tie-break: prefer central cells for better connectivity
        center_dist = abs(r - 5) + abs(c - 5)
        best_center_dist = abs(best_move[0] - 5) + abs(best_move[1] - 5)

        if score > best_score or (score == best_score and center_dist < best_center_dist):
            best_score = score
            best_move = (r, c)

    return best_move
