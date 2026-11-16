
import heapq
import random

BOARD_SIZE = 11

def neighbors(r, c):
    for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            yield nr, nc

def shortest_path(player, opponent, color):
    INF = 10**9
    dist = [[INF]*BOARD_SIZE for _ in range(BOARD_SIZE)]
    pq = []
    if color == 'b':  # top to bottom
        for c in range(BOARD_SIZE):
            r = 0
            if (r,c) in opponent: 
                continue
            cost = 0 if (r,c) in player else 1
            dist[r][c] = cost
            heapq.heappush(pq, (cost, r, c))
        target_row = BOARD_SIZE - 1
        def is_target(r,c): return r == target_row
    else:  # white, left to right
        for r in range(BOARD_SIZE):
            c = 0
            if (r,c) in opponent: 
                continue
            cost = 0 if (r,c) in player else 1
            dist[r][c] = cost
            heapq.heappush(pq, (cost, r, c))
        target_col = BOARD_SIZE - 1
        def is_target(r,c): return c == target_col

    while pq:
        d, r, c = heapq.heappop(pq)
        if d != dist[r][c]:
            continue
        if is_target(r,c):
            return d
        for nr, nc in neighbors(r,c):
            if (nr,nc) in opponent:
                continue
            nd = d + (0 if (nr,nc) in player else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heapq.heappush(pq, (nd, nr, nc))
    return INF

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    empty = [(r,c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE)
             if (r,c) not in me_set and (r,c) not in opp_set]
    if not empty:
        return (0,0)

    opp_color = 'w' if color == 'b' else 'b'

    best_score = -10**9
    best_moves = []

    for move in empty:
        new_me = me_set | {move}
        # compute my distance
        my_dist = shortest_path(new_me, opp_set, color)
        if my_dist == 0:
            return move  # immediate win
        # compute opponent distance after blocking
        opp_dist = shortest_path(opp_set, new_me, opp_color)
        # centrality heuristic
        center_bonus = -0.01 * (abs(move[0]-5) + abs(move[1]-5))
        score = (opp_dist - my_dist) + center_bonus
        if score > best_score + 1e-6:
            best_score = score
            best_moves = [move]
        elif abs(score - best_score) <= 1e-6:
            best_moves.append(move)

    return random.choice(best_moves)
