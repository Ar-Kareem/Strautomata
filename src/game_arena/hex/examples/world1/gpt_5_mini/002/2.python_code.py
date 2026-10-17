
import heapq
import random

# Hex policy for 11x11 board
# API:
# def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]

N = 11
INF = 10**6

def neighbors(r, c):
    # 6 hex neighbors as described:
    # (r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)
    for nr, nc in ((r, c-1), (r, c+1), (r-1, c), (r-1, c+1), (r+1, c), (r+1, c-1)):
        if 0 <= nr < N and 0 <= nc < N:
            yield nr, nc

def build_grid(me, opp):
    # grid values: 1 for me, -1 for opp, 0 for empty
    grid = [[0]*N for _ in range(N)]
    for (r,c) in me:
        grid[r][c] = 1
    for (r,c) in opp:
        grid[r][c] = -1
    return grid

def shortest_path_cost(grid, player_color):
    # Returns minimal cost to connect player's two sides.
    # Costs: own stone = 0, empty = 1, opponent stone = blocked
    # player_color: 'b' or 'w'
    # For 'b' connect top (row 0) to bottom (row N-1)
    # For 'w' connect left (col 0) to right (col N-1)
    own = 1
    opp = -1
    # If computing for opponent we need to interpret grid values accordingly.
    # Here grid uses 1 for caller's 'me' and -1 for caller's 'opp'.
    # But this function will be called with a grid built from perspective of the policy:
    # when computing for a specific player_color, we need to map which numeric value corresponds to "own".
    # The grid currently has 1 meaning policy's stones, -1 meaning opponent's stones.
    # We'll treat 'player_color' mapping outside: we call this function with grid where
    # 1==player's stones, -1==opponent's stones when requesting for the policy's player.
    # To compute shortest path for opponent we will pass a swapped grid or interpret accordingly.
    # For simplicity, this function assumes "own" stones are values == 1, and opponent stones == -1.
    # So callers should supply grid where 1 matches the player being evaluated.
    dist = [[INF]*N for _ in range(N)]
    heap = []
    if player_color == 'b':
        # sources: all row 0
        for c in range(N):
            val = grid[0][c]
            if val == -1:  # blocked
                continue
            cost = 0 if val == 1 else 1
            dist[0][c] = cost
            heapq.heappush(heap, (cost, 0, c))
        target_row = N-1
        while heap:
            d, r, c = heapq.heappop(heap)
            if d != dist[r][c]:
                continue
            if r == target_row:
                return d
            for nr, nc in neighbors(r, c):
                if grid[nr][nc] == -1:
                    continue
                w = 0 if grid[nr][nc] == 1 else 1
                nd = d + w
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(heap, (nd, nr, nc))
        return INF
    else:
        # 'w' player: sources are col 0, targets col N-1
        for r in range(N):
            val = grid[r][0]
            if val == -1:
                continue
            cost = 0 if val == 1 else 1
            dist[r][0] = cost
            heapq.heappush(heap, (cost, r, 0))
        target_col = N-1
        while heap:
            d, r, c = heapq.heappop(heap)
            if d != dist[r][c]:
                continue
            if c == target_col:
                return d
            for nr, nc in neighbors(r, c):
                if grid[nr][nc] == -1:
                    continue
                w = 0 if grid[nr][nc] == 1 else 1
                nd = d + w
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(heap, (nd, nr, nc))
        return INF

def map_grid_for_player(grid_orig, player_is_policy):
    # Convert a grid built with policy's perspective (1 for policy stones, -1 for opponent)
    # into a grid where 1 means stones of the player we want to evaluate.
    # If player_is_policy is True, just return copy of grid_orig.
    # If False, flip signs.
    grid = [[0]*N for _ in range(N)]
    if player_is_policy:
        for r in range(N):
            for c in range(N):
                grid[r][c] = grid_orig[r][c]
    else:
        for r in range(N):
            for c in range(N):
                grid[r][c] = -grid_orig[r][c]
    return grid

def policy(me, opp, color):
    """
    Determine next move for Hex 11x11.
    me: list of (r,c) of my stones
    opp: list of (r,c) of opponent stones
    color: 'b' or 'w' for policy's color
    returns (r,c) tuple for next move (must be an empty cell)
    """
    grid_base = build_grid(me, opp)
    # List empty cells
    empties = [(r,c) for r in range(N) for c in range(N) if grid_base[r][c] == 0]
    if not empties:
        # No empty (shouldn't happen), but return arbitrary in-bounds
        return (0,0)

    # compute base distances
    # base_my: compute distance for our color; need grid where 1==our stones
    grid_for_me = map_grid_for_player(grid_base, True)
    base_my = shortest_path_cost(grid_for_me, color)
    # compute opponent color char
    opp_color = 'b' if color == 'w' else 'w'
    grid_for_opp = map_grid_for_player(grid_base, False)  # flip so 1==opponent stones
    base_opp = shortest_path_cost(grid_for_opp, opp_color)

    # center coordinate for tie-breaking
    center = ((N-1)/2.0, (N-1)/2.0)

    best_move = None
    best_score = -INF
    best_tuple = None

    # If board is mostly empty and it's the very first move, choose center deterministically
    if len(me) + len(opp) == 0:
        center_cell = (N//2, N//2)
        return center_cell

    for (r,c) in empties:
        # simulate placing our stone at (r,c)
        grid_sim = [row[:] for row in grid_base]
        grid_sim[r][c] = 1  # our stone

        # my distance after move
        grid_me_sim = map_grid_for_player(grid_sim, True)
        my_after = shortest_path_cost(grid_me_sim, color)
        # opponent distance after move (we flip so 1==opponent stones)
        grid_opp_sim = map_grid_for_player(grid_sim, False)
        opp_after = shortest_path_cost(grid_opp_sim, opp_color)

        # scoring: prefer big reductions for us and big increases for opponent
        delta_my = base_my - my_after
        delta_opp = opp_after - base_opp
        score = 3*delta_my + 2*delta_opp

        # strong immediate win preference
        if my_after == 0:
            score += 100000  # immediate winning move

        # discourage moves that don't help and open no block: small center preference
        # closer to center is slightly better
        distc = abs(r - center[0]) + abs(c - center[1])
        score -= 0.01 * distc

        # tie-breaking: more reduction in my distance, then larger harm to opp, then center
        tie_tuple = (delta_my, delta_opp, -distc, - (r* N + c))  # deterministic

        if score > best_score or (abs(score - best_score) < 1e-9 and tie_tuple > best_tuple):
            best_score = score
            best_move = (r,c)
            best_tuple = tie_tuple

    if best_move is None:
        # fallback: random empty
        return random.choice(empties)
    return best_move

# For compatibility if module is imported: expose policy as main API
if __name__ == "__main__":
    # small self-test: empty board, black to move
    print(policy([], [], 'b'))
