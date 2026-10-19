
import heapq
from typing import Set, Tuple, List

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    SIZE = 11
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    def neighbors(r, c):
        """Return valid hex neighbors of (r,c)"""
        for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                yield (nr, nc)
    
    def dijkstra_distance(player_stones: Set, is_black: bool) -> float:
        """Calculate minimum virtual distance to connect sides"""
        pq = []
        dist = {}
        
        # Start from one side
        if is_black:  # Connect top (row 0) to bottom (row 10)
            for c in range(SIZE):
                if (0, c) in player_stones:
                    heapq.heappush(pq, (0, 0, c))
                    dist[(0, c)] = 0
                elif (0, c) not in opp_set:
                    heapq.heappush(pq, (1, 0, c))
                    dist[(0, c)] = 1
        else:  # Connect left (col 0) to right (col 10)
            for r in range(SIZE):
                if (r, 0) in player_stones:
                    heapq.heappush(pq, (0, r, 0))
                    dist[(r, 0)] = 0
                elif (r, 0) not in opp_set:
                    heapq.heappush(pq, (1, r, 0))
                    dist[(r, 0)] = 1
        
        while pq:
            d, r, c = heapq.heappop(pq)
            if dist.get((r, c), float('inf')) < d:
                continue
            
            # Check if reached other side
            if is_black and r == SIZE - 1:
                return d
            if not is_black and c == SIZE - 1:
                return d
            
            for nr, nc in neighbors(r, c):
                if (nr, nc) in opp_set:
                    continue
                cost = 0 if (nr, nc) in player_stones else 1
                nd = d + cost
                if nd < dist.get((nr, nc), float('inf')):
                    dist[(nr, nc)] = nd
                    heapq.heappush(pq, (nd, nr, nc))
        
        return float('inf')
    
    def evaluate():
        """Evaluate position: negative is good for us"""
        my_dist = dijkstra_distance(me_set, color == 'b')
        opp_dist = dijkstra_distance(opp_set, color != 'b')
        return my_dist - opp_dist
    
    # Opening moves
    if len(me) == 0:
        if (5, 5) not in occupied:
            return (5, 5)
        return (5, 4)
    
    # Generate candidate moves - prioritize near existing stones and center
    candidates = []
    for r in range(SIZE):
        for c in range(SIZE):
            if (r, c) not in occupied:
                # Score for move ordering
                center_dist = abs(r - 5) + abs(c - 5)
                near_me = min((abs(r-mr) + abs(c-mc) for mr, mc in me), default=5)
                priority = center_dist + near_me * 2
                candidates.append((priority, r, c))
    
    candidates.sort()
    candidates = [(r, c) for _, r, c in candidates[:30]]  # Top 30 candidates
    
    best_move = candidates[0]
    best_score = float('inf')
    
    for r, c in candidates:
        # Simulate move
        me_set.add((r, c))
        score = evaluate()
        me_set.remove((r, c))
        
        if score < best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
