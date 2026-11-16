
import heapq
import math

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    size = 11
    # Directions for hex neighbors (row, col) offsets
    # Excluding (-1, -1) and (1, 1) because of hex geometry
    dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]

    # Precompute all cells
    all_cells = [(r, c) for r in range(size) for c in range(size)]

    # Set of occupied cells
    occupied = set(me) | set(opp)

    # If board empty, play center
    if not me and not opp:
        return (5, 5)

    # Helper: Dijkstra to find shortest virtual distance from side1 to side2
    # side1 and side2 are functions mapping (r,c) -> True if on that side
    def virtual_distance(player_stones, opponent_stones, side1_func, side2_func):
        INF = 10**9
        dist = [[INF] * size for _ in range(size)]
        heap = []

        for r in range(size):
            for c in range(size):
                if side1_func(r, c):
                    cost = 0 if (r, c) in player_stones else 1
                    dist[r][c] = cost
                    heapq.heappush(heap, (cost, r, c))

        while heap:
            d, r, c = heapq.heappop(heap)
            if d > dist[r][c]:
                continue
            if side2_func(r, c):
                # reached opposite side
                return d
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < size and 0 <= nc < size:
                    cost = 0 if (nr, nc) in player_stones else 1
                    nd = d + cost
                    if nd < dist[nr][nc]:
                        dist[nr][nc] = nd
                        heapq.heappush(heap, (nd, nr, nc))
        # Should not happen in hex
        return INF

    # Side functions
    if color == 'b':
        # black connects top (row 0) to bottom (row size-1)
        def side1(r, c): return r == 0
        def side2(r, c): return r == size - 1
        # white connects left (col 0) to right (col size-1)
        def opp_side1(r, c): return c == 0
        def opp_side2(r, c): return c == size - 1
    else:  # white
        # white connects left (col 0) to right (col size-1)
        def side1(r, c): return c == 0
        def side2(r, c): return c == size - 1
        # black connects top to bottom
        def opp_side1(r, c): return r == 0
        def opp_side2(r, c): return r == size - 1

    # Current virtual distances
    my_dist = virtual_distance(set(me), set(opp), side1, side2)
    opp_dist = virtual_distance(set(opp), set(me), opp_side1, opp_side2)

    # Generate candidate moves: only cells adjacent (distance <= 1) to any stone
    neighbor_cells = set()
    for r, c in occupied:
        neighbor_cells.add((r, c))
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < size and 0 <= nc < size:
                neighbor_cells.add((nr, nc))
    candidates = [cell for cell in neighbor_cells if cell not in occupied]

    # If no neighbor candidates (shouldn't happen), fallback to any empty cell
    if not candidates:
        candidates = [cell for cell in all_cells if cell not in occupied]

    # Evaluate each candidate
    best_score = -math.inf
    best_move = candidates[0]

    for move in candidates:
        # Try move for me
        new_me = me + [move]
        new_my_dist = virtual_distance(set(new_me), set(opp), side1, side2)
        # Opponent's distance if I move here
        new_opp_dist = virtual_distance(set(opp), set(new_me), opp_side1, opp_side2)

        # Score = reduction in my distance + increase in opponent's distance
        my_improve = my_dist - new_my_dist
        opp_worsen = new_opp_dist - opp_dist
        score = my_improve + opp_worsen

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
