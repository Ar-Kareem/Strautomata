
import heapq

N = 11
DIRS = [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]

def dijkstra(my_set, opp_set, color):
    INF = 10**9
    dist = {}
    pq = []
    
    if color == 'b':
        starts = [(0, c) for c in range(N)]
    else:
        starts = [(r, 0) for r in range(N)]
    
    for rc in starts:
        if rc in opp_set:
            continue
        d = 0 if rc in my_set else 1
        if rc not in dist or d < dist[rc]:
            dist[rc] = d
            heapq.heappush(pq, (d, rc[0], rc[1]))
    
    while pq:
        d, r, c = heapq.heappop(pq)
        if d > dist.get((r,c), INF):
            continue
        if (color == 'b' and r == N-1) or (color == 'w' and c == N-1):
            return d
        for dr, dc in DIRS:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N:
                nrc = (nr, nc)
                if nrc in opp_set:
                    continue
                nd = d + (0 if nrc in my_set else 1)
                if nd < dist.get(nrc, INF):
                    dist[nrc] = nd
                    heapq.heappush(pq, (nd, nr, nc))
    
    return INF

def policy(me, opp, color):
    my_set = set(me)
    opp_set = set(opp)
    opp_color = 'w' if color == 'b' else 'b'
    
    # Opening move
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    
    empty = [(r,c) for r in range(N) for c in range(N) 
             if (r,c) not in my_set and (r,c) not in opp_set]
    
    if not empty:
        return (0, 0)
    
    # If only one stone on board and we haven't played, take center-ish
    if len(me) == 0 and (5,5) not in opp_set:
        return (5, 5)
    
    best_score = -10**18
    best_move = empty[0]
    
    for (r, c) in empty:
        my_set.add((r, c))
        my_d = dijkstra(my_set, opp_set, color)
        opp_d = dijkstra(opp_set, my_set, opp_color)
        my_set.discard((r, c))
        
        # Clamp infinities for stable math
        if my_d >= 10**9:
            my_score = -10**6
        else:
            my_score = -my_d
        if opp_d >= 10**9:
            opp_score = 10**6
        else:
            opp_score = opp_d
        
        score = (opp_score + my_score) * 1000 - (abs(r-5) + abs(c-5))
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
