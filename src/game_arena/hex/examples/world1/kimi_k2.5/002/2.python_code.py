
import heapq
from typing import List, Tuple, Set

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[int, int]:
    N = 11
    me_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opp)
    
    # Hex grid adjacency: exclude (i-1,j-1) and (i+1,j+1) from 8-way
    DIRS = [(0, -1), (0, 1), (-1, 0), (-1, 1), (1, -1), (1, 0)]
    
    def shortest_path(player_color: str, player_stones: Set[Tuple[int, int]], blocker_stones: Set[Tuple[int, int]]) -> float:
        """Minimum empty cells needed for player to connect their sides. 0 = already connected."""
        dist = [[float('inf')] * N for _ in range(N)]
        pq = []
        
        if player_color == 'b':  # Black: top (row 0) to bottom (row 10)
            for c in range(N):
                if (0, c) in blocker_stones:
                    continue
                cost = 0 if (0, c) in player_stones else 1
                dist[0][c] = cost
                heapq.heappush(pq, (cost, 0, c))
            target_check = lambda r, c: r == N - 1
        else:  # White: left (col 0) to right (col 10)
            for r in range(N):
                if (r, 0) in blocker_stones:
                    continue
                cost = 0 if (r, 0) in player_stones else 1
                dist[r][0] = cost
                heapq.heappush(pq, (cost, r, 0))
            target_check = lambda r, c: c == N - 1
        
        while pq:
            d, r, c = heapq.heappop(pq)
            if target_check(r, c):
                return d
            if d > dist[r][c]:
                continue
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    if (nr, nc) in blocker_stones:
                        continue
                    cost = 0 if (nr, nc) in player_stones else 1
                    nd = d + cost
                    if nd < dist[nr][nc]:
                        dist[nr][nc] = nd
                        heapq.heappush(pq, (nd, nr, nc))
        return float('inf')
    
    # Get empty cells
    empty_cells = [(r, c) for r in range(N) for c in range(N) 
                   if (r, c) not in me_set and (r, c) not in opp_set]
    
    if not empty_cells:
        return (0, 0)  # Should not occur in valid game
    
    opp_color = 'w' if color == 'b' else 'b'
    
    # 1. Check for immediate winning move
    for r, c in empty_cells:
        if shortest_path(color, me_set | {(r, c)}, opp_set) == 0:
            return (r, c)
    
    # 2. Check for opponent's immediate win (must block)
    for r, c in empty_cells:
        if shortest_path(opp_color, opp_set | {(r, c)}, me_set) == 0:
            return (r, c)
    
    # 3. Evaluate all moves
    best_move = empty_cells[0]
    best_score = -float('inf')
    best_dist = float('inf')
    
    for r, c in empty_cells:
        new_me = me_set | {(r, c)}
        my_len = shortest_path(color, new_me, opp_set)
        opp_len = shortest_path(opp_color, opp_set, new_me)
        
        # If move is losing (cannot connect), heavily penalize but keep as option
        if my_len == float('inf'):
            score = -1000.0
        else:
            score = opp_len - my_len  # Higher is better
        
        # Prefer center on ties
        dist_center = (r - 5) ** 2 + (c - 5) ** 2
        if score > best_score or (abs(score - best_score) < 1e-9 and dist_center < best_dist):
            best_score = score
            best_move = (r, c)
            best_dist = dist_center
    
    return best_move
