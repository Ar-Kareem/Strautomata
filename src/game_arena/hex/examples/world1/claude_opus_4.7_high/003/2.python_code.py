
from collections import deque

N = 11

def _get_neighbors(r, c):
    res = []
    for dr, dc in [(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0)]:
        nr, nc = r+dr, c+dc
        if 0 <= nr < N and 0 <= nc < N:
            res.append((nr,nc))
    return res

NEIGHBORS = [[_get_neighbors(r,c) for c in range(N)] for r in range(N)]

def shortest_path(my_set, opp_set, color):
    INF = 10**9
    dist = [[INF]*N for _ in range(N)]
    dq = deque()
    
    if color == 'b':
        starts = [(0, j) for j in range(N)]
        end_row_b = True
    else:
        starts = [(i, 0) for i in range(N)]
        end_row_b = False
    
    for r, c in starts:
        if (r,c) in opp_set:
            continue
        cost = 0 if (r,c) in my_set else 1
        if cost < dist[r][c]:
            dist[r][c] = cost
            if cost == 0:
                dq.appendleft((r,c))
            else:
                dq.append((r,c))
    
    best = INF
    while dq:
        r, c = dq.popleft()
        d = dist[r][c]
        if d >= best:
            continue
        if (end_row_b and r == N-1) or (not end_row_b and c == N-1):
            if d < best:
                best = d
            continue
        for nr, nc in NEIGHBORS[r][c]:
            if (nr,nc) in opp_set:
                continue
            w = 0 if (nr,nc) in my_set else 1
            nd = d + w
            if nd < dist[nr][nc]:
                dist[nr][nc] = nd
                if w == 0:
                    dq.appendleft((nr,nc))
                else:
                    dq.append((nr,nc))
    return best

def policy(me, opp, color):
    my_set = set(me)
    opp_set = set(opp)
    
    total = len(my_set) + len(opp_set)
    if total == 0:
        return (5, 5)
    
    opp_color = 'w' if color == 'b' else 'b'
    
    empties = [(r,c) for r in range(N) for c in range(N)
               if (r,c) not in my_set and (r,c) not in opp_set]
    
    if not empties:
        for r in range(N):
            for c in range(N):
                if (r,c) not in my_set and (r,c) not in opp_set:
                    return (r,c)
        return (0,0)
    
    # If very early for us, prefer center-ish opening
    if len(my_set) == 0:
        # respond near center, avoiding occupied
        preferred = [(5,5),(5,4),(4,5),(5,6),(6,5),(4,6),(6,4),(4,4),(6,6)]
        for p in preferred:
            if p not in my_set and p not in opp_set:
                # still evaluate, but bias ok
                break
    
    best_score = -10**18
    best_move = empties[0]
    center = (5, 5)
    
    for move in empties:
        my_set.add(move)
        my_d = shortest_path(my_set, opp_set, color)
        opp_d = shortest_path(opp_set, my_set, opp_color)
        my_set.discard(move)
        
        # If this move wins immediately, take it
        if my_d == 0:
            return move
        
        score = (opp_d - my_d) * 1000
        # Tiebreak: prefer central, shorter my path
        dc = -(abs(move[0]-center[0]) + abs(move[1]-center[1]))
        score = score + dc
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
