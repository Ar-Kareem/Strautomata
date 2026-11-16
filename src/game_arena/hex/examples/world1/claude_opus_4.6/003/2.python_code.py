
import random
import time
import math

def policy(me, opp, color):
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    empty = [(r, c) for r in range(SIZE) for c in range(SIZE) if (r, c) not in occupied]
    
    if not empty:
        return (0, 0)
    
    if len(me) == 0 and len(opp) == 0:
        return (5, 5)
    if len(me) == 0 and len(opp) == 1 and (5, 5) in opp_set:
        return (4, 5)
    if len(me) == 0 and (5, 5) not in opp_set:
        return (5, 5)
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                yield nr, nc
    
    class UnionFind:
        def __init__(self):
            self.parent = {}
            self.rank = {}
        
        def find(self, x):
            while self.parent.get(x, x) != x:
                self.parent[x] = self.parent.get(self.parent[x], self.parent[x])
                x = self.parent[x]
            return x
        
        def union(self, a, b):
            a, b = self.find(a), self.find(b)
            if a == b:
                return
            ra, rb = self.rank.get(a, 0), self.rank.get(b, 0)
            if ra < rb:
                a, b = b, a
            self.parent[b] = a
            if ra == rb:
                self.rank[a] = ra + 1
    
    def check_win(stones, player_color):
        if len(stones) < SIZE:
            return False
        uf = UnionFind()
        SIDE_A = 'SIDE_A'
        SIDE_B = 'SIDE_B'
        uf.parent[SIDE_A] = SIDE_A
        uf.parent[SIDE_B] = SIDE_B
        
        for (r, c) in stones:
            uf.parent[(r, c)] = (r, c)
        
        for (r, c) in stones:
            if player_color == 'b':
                if r == 0:
                    uf.union((r, c), SIDE_A)
                if r == SIZE - 1:
                    uf.union((r, c), SIDE_B)
            else:
                if c == 0:
                    uf.union((r, c), SIDE_A)
                if c == SIZE - 1:
                    uf.union((r, c), SIDE_B)
            for nr, nc in neighbors(r, c):
                if (nr, nc) in stones:
                    uf.union((r, c), (nr, nc))
        
        return uf.find(SIDE_A) == uf.find(SIDE_B)
    
    opp_color = 'w' if color == 'b' else 'b'
    
    # Check immediate wins
    for move in empty:
        test = me_set | {move}
        if check_win(test, color):
            return move
    
    # Block immediate opponent wins
    for move in empty:
        test = opp_set | {move}
        if check_win(test, opp_color):
            return move
    
    # MCTS
    # Precompute neighbor sets for prioritization
    me_neighbors = set()
    for r, c in me_set:
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in occupied:
                me_neighbors.add((nr, nc))
    
    # Dijkstra-based evaluation for both players
    import heapq
    
    def dijkstra_cost(stones_set, player_color, all_occupied):
        # Compute shortest path cost to connect two sides
        # Cost 0 to traverse own stone, cost 1 to traverse empty cell, infinity for opponent
        dist = {}
        heap = []
        
        if player_color == 'b':
            # Connect top (row 0) to bottom (row 10)
            for c in range(SIZE):
                if (0, c) in stones_set:
                    cost = 0
                elif (0, c) not in all_occupied:
                    cost = 1
                else:
                    continue
                if cost < dist.get((0, c), float('inf')):
                    dist[(0, c)] = cost
                    heapq.heappush(heap, (cost, 0, c))
            
            while heap:
                d, r, c = heapq.heappop(heap)
                if d > dist.get((r, c), float('inf')):
                    continue
                if r == SIZE - 1:
                    return d
                for nr, nc in neighbors(r, c):
                    if (nr, nc) in stones_set:
                        nd = d
                    elif (nr, nc) not in all_occupied:
                        nd = d + 1
                    else:
                        continue
                    if nd < dist.get((nr, nc), float('inf')):
                        dist[(nr, nc)] = nd
                        heapq.heappush(heap, (nd, nr, nc))
        else:
            for r in range(SIZE):
                if (r, 0) in stones_set:
                    cost = 0
                elif (r, 0) not in all_occupied:
                    cost = 1
                else:
                    continue
                if cost < dist.get((r, 0), float('inf')):
                    dist[(r, 0)] = cost
                    heapq.heappush(heap, (cost, r, 0))
            
            while heap:
                d, r, c = heapq.heappop(heap)
                if d > dist.get((r, c), float('inf')):
                    continue
                if c == SIZE - 1:
                    return d
                for nr, nc in neighbors(r, c):
                    if (nr, nc) in stones_set:
                        nd = d
                    elif (nr, nc) not in all_occupied:
                        nd = d + 1
                    else:
                        continue
                    if nd < dist.get((nr, nc), float('inf')):
                        dist[(nr, nc)] = nd
                        heapq.heappush(heap, (nd, nr, nc))
        
        return float('inf')
    
    # Score moves by reduction in our dijkstra cost and increase in opponent's
    move_scores = {}
    my_cost = dijkstra_cost(me_set, color, occupied)
    opp_cost = dijkstra_cost(opp_set, opp_color, occupied)
    
    candidates = empty
    if len(candidates) > 40:
        # Prioritize nearby and center moves
        scored = []
        for mv in candidates:
            r, c = mv
            center_dist = abs(r - 5) + abs(c - 5)
            near_me = 1 if mv in me_neighbors else 0
            scored.append((-near_me, center_dist, mv))
        scored.sort()
        candidates = [s[2] for s in scored[:40]]
    
    best_score = -float('inf')
    best_move = empty[0]
    
    for mv in candidates:
        new_me = me_set | {mv}
        new_occ = occupied | {mv}
        nc = dijkstra_cost(new_me, color, new_occ)
        no = dijkstra_cost(opp_set, opp_color, new_occ)
        score = (my_cost - nc) + (no - opp_cost) * 0.9
        # Small center bonus
        r, c = mv
        score += (5.5 - abs(r - 5)) * 0.05 + (5.5 - abs(c - 5)) * 0.05
        if score > best_score:
            best_score = score
            best_move = mv
    
    return best_move
