
from collections import deque

def policy(me, opp, color):
    N = 11
    INF = 10**9
    me_set = set(me)
    opp_set = set(opp)
    opp_color = 'w' if color == 'b' else 'b'

    # Opening: play the center if the board is empty
    if not me_set and not opp_set:
        return (5, 5)

    # Helper to compute the minimal number of stones needed for a player to connect
    def min_cost(p_set, o_set, col):
        # cost matrix: 0 for own stone, 1 for empty, INF for opponent stone
        cost = [[INF]*N for _ in range(N)]
        for r in range(N):
            for c in range(N):
                if (r, c) in p_set:
                    cost[r][c] = 0
                elif (r, c) not in o_set:
                    cost[r][c] = 1
        dist = [[INF]*N for _ in range(N)]
        dq = deque()
        # initialize source frontier
        if col == 'b':  # top row
            for c in range(N):
                if cost[0][c] != INF:
                    d = cost[0][c]
                    dist[0][c] = d
                    dq.appendleft((0, c)) if d == 0 else dq.append((0, c))
        else:  # left column
            for r in range(N):
                if cost[r][0] != INF:
                    d = cost[r][0]
                    dist[r][0] = d
                    dq.appendleft((r, 0)) if d == 0 else dq.append((r, 0))
        # 0-1 BFS
        while dq:
            r, c = dq.popleft()
            d = dist[r][c]
            nr_list = [(r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)]
            for nr, nc in nr_list:
                if 0 <= nr < N and 0 <= nc < N and cost[nr][nc] != INF:
                    nd = d + cost[nr][nc]
                    if nd < dist[nr][nc]:
                        dist[nr][nc] = nd
                        dq.appendleft((nr, nc)) if cost[nr][nc] == 0 else dq.append((nr, nc))
        # minimal distance to target edge
        min_dist = INF
        if col == 'b':  # bottom row
            for c in range(N):
                if dist[10][c] < min_dist:
                    min_dist = dist[10][c]
        else:  # right column
            for r in range(N):
                if dist[r][10] < min_dist:
                    min_dist = dist[r][10]
        return min_dist

    # compute current distances
    d_us = min_cost(me_set, opp_set, color)
    d_opp = min_cost(opp_set, me_set, opp_color)

    # list all legal moves
    empty = [(r, c) for r in range(N) for c in range(N) if (r, c) not in me_set and (r, c) not in opp_set]

    # 1) win immediately if possible
    for r, c in empty:
        me_set.add((r, c))
        if min_cost(me_set, opp_set, color) == 0:
            me_set.remove((r, c))
            return (r, c)
        me_set.remove((r, c))

    # 2) block opponent's immediate win
    must_block = []
    for r, c in empty:
        opp_set.add((r, c))
        if min_cost(opp_set, me_set, opp_color) == 0:
            must_block.append((r, c))
        opp_set.remove((r, c))
    if must_block:
        # pick the block that also helps us most
        best = None
        best_gain = -INF
        for r, c in must_block:
            me_set.add((r, c))
            d_new = min_cost(me_set, opp_set, color)
            me_set.remove((r, c))
            gain = d_us - d_new if d_us != INF else 0
            if gain > best_gain:
                best_gain = gain
                best = (r, c)
        return best if best is not None else must_block[0]

    # 3) evaluate all moves
    best_move = None
    best_score = (-INF, 0)  # (score, -centrality)
    for r, c in empty:
        # our new distance after playing (r,c)
        me_set.add((r, c))
        d_us_new = min_cost(me_set, opp_set, color)
        me_set.remove((r, c))
        # opponent's new distance after we block (r,c)
        me_blocked = me_set | {(r, c)}
        d_opp_new = min_cost(opp_set, me_blocked, opp_color)

        delta_us = d_us - d_us_new if d_us != INF else 0
        delta_opp = d_opp_new - d_opp if d_opp != INF else 0
        score = delta_us + delta_opp
        centrality = -(abs(r - 5) + abs(c - 5))  # more central is larger
        if (score, centrality) > best_score:
            best_score = (score, centrality)
            best_move = (r, c)

    # fallback: choose the most central cell if no move was selected
    if best_move is None:
        min_cen = INF
        for r, c in empty:
            cen = abs(r - 5) + abs(c - 5)
            if cen < min_cen:
                min_cen = cen
                best_move = (r, c)
    return best_move
