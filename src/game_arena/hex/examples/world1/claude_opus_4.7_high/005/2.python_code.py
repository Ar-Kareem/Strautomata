
import heapq

DIRS = [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]

def dijkstra(my_set, opp_set, sources):
    INF = 9999
    dist = [[INF]*11 for _ in range(11)]
    heap = []
    for r, c in sources:
        if (r, c) in opp_set:
            continue
        cost = 0 if (r, c) in my_set else 1
        if cost < dist[r][c]:
            dist[r][c] = cost
            heapq.heappush(heap, (cost, r, c))
    while heap:
        d, r, c = heapq.heappop(heap)
        if d > dist[r][c]:
            continue
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < 11 and 0 <= nc < 11:
                if (nr, nc) in opp_set:
                    continue
                add = 0 if (nr, nc) in my_set else 1
                nd = d + add
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heapq.heappush(heap, (nd, nr, nc))
    return dist

def policy(me, opp, color):
    me_set = set(me)
    opp_set = set(opp)
    
    if not me_set and not opp_set:
        return (5, 5)
    
    if color == 'b':
        my_src1 = [(0, c) for c in range(11)]
        my_src2 = [(10, c) for c in range(11)]
        opp_src1 = [(r, 0) for r in range(11)]
        opp_src2 = [(r, 10) for r in range(11)]
    else:
        my_src1 = [(r, 0) for r in range(11)]
        my_src2 = [(r, 10) for r in range(11)]
        opp_src1 = [(0, c) for c in range(11)]
        opp_src2 = [(10, c) for c in range(11)]
    
    my_d1 = dijkstra(me_set, opp_set, my_src1)
    my_d2 = dijkstra(me_set, opp_set, my_src2)
    opp_d1 = dijkstra(opp_set, me_set, opp_src1)
    opp_d2 = dijkstra(opp_set, me_set, opp_src2)
    
    best_score = -1e18
    best_move = None
    
    for r in range(11):
        for c in range(11):
            if (r, c) in me_set or (r, c) in opp_set:
                continue
            my_path = my_d1[r][c] + my_d2[r][c]
            opp_path = opp_d1[r][c] + opp_d2[r][c]
            # Cap to avoid weird INF interactions
            if my_path > 200: my_path = 200
            if opp_path > 200: opp_path = 200
            # Prefer cells on both critical paths
            score = -(my_path + opp_path)
            # Tiebreaker: prefer central cells
            score -= 0.001 * (abs(r - 5) + abs(c - 5))
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    if best_move is None:
        for r in range(11):
            for c in range(11):
                if (r, c) not in me_set and (r, c) not in opp_set:
                    return (r, c)
    
    return best_move
