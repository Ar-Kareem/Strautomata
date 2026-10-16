
import random
import time
from heapq import heappush, heappop

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    
    def get_neighbors(r, c):
        candidates = [(r-1,c), (r-1,c+1), (r,c-1), (r,c+1), (r+1,c-1), (r+1,c)]
        return [(nr, nc) for nr, nc in candidates if 0 <= nr < SIZE and 0 <= nc < SIZE]
    
    def get_empty():
        return [(r, c) for r in range(SIZE) for c in range(SIZE) if (r,c) not in me_set and (r,c) not in opp_set]
    
    empty = get_empty()
    if not empty:
        return (0, 0)
    
    if len(me) == 0:
        return (5, 5) if (5, 5) in empty else empty[0]
    
    def dijkstra_distance(stones, opponent, is_black):
        dist = [[float('inf')] * SIZE for _ in range(SIZE)]
        pq = []
        
        if is_black:
            for c in range(SIZE):
                if (0, c) in stones:
                    dist[0][c] = 0
                    heappush(pq, (0, 0, c))
                elif (0, c) not in opponent:
                    dist[0][c] = 1
                    heappush(pq, (1, 0, c))
        else:
            for r in range(SIZE):
                if (r, 0) in stones:
                    dist[r][0] = 0
                    heappush(pq, (0, r, 0))
                elif (r, 0) not in opponent:
                    dist[r][0] = 1
                    heappush(pq, (1, r, 0))
        
        while pq:
            d, r, c = heappop(pq)
            if d > dist[r][c]:
                continue
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opponent:
                    continue
                nd = d if (nr, nc) in stones else d + 1
                if nd < dist[nr][nc]:
                    dist[nr][nc] = nd
                    heappush(pq, (nd, nr, nc))
        
        if is_black:
            return min(dist[SIZE-1][c] for c in range(SIZE))
        else:
            return min(dist[r][SIZE-1] for r in range(SIZE))
    
    is_black = (color == 'b')
    
    best_move = None
    best_score = float('inf')
    
    for move in empty:
        new_me = me_set | {move}
        my_dist = dijkstra_distance(new_me, opp_set, is_black)
        opp_dist = dijkstra_distance(opp_set, new_me, not is_black)
        
        score = my_dist - opp_dist * 0.9
        
        r, c = move
        center_bonus = -0.1 * (5.5 - abs(r - 5)) * (5.5 - abs(c - 5)) / 30
        score += center_bonus
        
        if score < best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move else empty[0]
