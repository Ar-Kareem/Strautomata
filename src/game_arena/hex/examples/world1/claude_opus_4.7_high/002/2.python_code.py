
import heapq

BOARD = 11

def neighbors(r, c):
    result = []
    for dr, dc in [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < BOARD and 0 <= nc < BOARD:
            result.append((nr, nc))
    return result

def dijkstra(me_set, opp_set, sources):
    INF = 10**9
    dist = [[INF]*BOARD for _ in range(BOARD)]
    pq = []
    for (r,c) in sources:
        if (r,c) in opp_set:
            continue
        cost = 0 if (r,c) in me_set else 1
        if cost < dist[r][c]:
            dist[r][c] = cost
            heapq.heappush(pq, (cost, r, c))
    while pq:
        d, r, c = heapq.heappop(pq)
        if d > dist[r][c]:
            continue
        for nr, nc in neighbors(r, c):
            if (nr,nc) in opp_set:
                continue
            nd = d + (0 if (nr,nc) in me_set else 1)
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                heapq.heappush(pq, (nd, nr, nc))
    return dist

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    total = len(me) + len(opp)

    if total == 0:
        return (5,5)
    if total <= 2 and (5,5) not in me_set and (5,5) not in opp_set:
        return (5,5)

    if color == 'b':
        my_e1 = [(0,c) for c in range(BOARD)]
        my_e2 = [(BOARD-1,c) for c in range(BOARD)]
        opp_e1 = [(r,0) for r in range(BOARD)]
        opp_e2 = [(r,BOARD-1) for r in range(BOARD)]
    else:
        my_e1 = [(r,0) for r in range(BOARD)]
        my_e2 = [(r,BOARD-1) for r in range(BOARD)]
        opp_e1 = [(0,c) for c in range(BOARD)]
        opp_e2 = [(BOARD-1,c) for c in range(BOARD)]

    md1 = dijkstra(me_set, opp_set, my_e1)
    md2 = dijkstra(me_set, opp_set, my_e2)
    od1 = dijkstra(opp_set, me_set, opp_e1)
    od2 = dijkstra(opp_set, me_set, opp_e2)

    INF = 10**9
    min_my = INF
    min_opp = INF
    for r in range(BOARD):
        for c in range(BOARD):
            if (r,c) in me_set or (r,c) in opp_set:
                continue
            mp = md1[r][c] + md2[r][c] - 1
            op = od1[r][c] + od2[r][c] - 1
            if mp < min_my: min_my = mp
            if op < min_opp: min_opp = op

    if min_my <= min_opp:
        w_my, w_opp = 1.0, 1.0
    else:
        w_my, w_opp = 1.0, 1.25

    best_score = -1e18
    best_move = None

    for r in range(BOARD):
        for c in range(BOARD):
            if (r,c) in me_set or (r,c) in opp_set:
                continue
            mp = md1[r][c] + md2[r][c] - 1
            op = od1[r][c] + od2[r][c] - 1
            mp = min(mp, 10000)
            op = min(op, 10000)
            score = -(mp * w_my + op * w_opp)
            score -= 0.001 * (abs(r-5) + abs(c-5))
            if score > best_score:
                best_score = score
                best_move = (r,c)

    if best_move is None:
        for r in range(BOARD):
            for c in range(BOARD):
                if (r,c) not in me_set and (r,c) not in opp_set:
                    return (r,c)

    return best_move
