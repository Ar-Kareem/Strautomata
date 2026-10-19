
import numpy as np
from collections import deque
import heapq

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    BOARD_SIZE = 11
    
    # Convert to sets for faster lookup
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    # Get all empty cells
    empty_cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                   if (r, c) not in occupied]
    
    if not empty_cells:
        return (0, 0)  # Shouldn't happen
    
    # Helper function to get neighbors in Hex
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, -1), (-1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                neighbors.append((nr, nc))
        return neighbors
    
    # Dijkstra to find shortest path
    def shortest_path_distance(my_stones, opponent_stones, is_black):
        stones_set = set(my_stones)
        opp_set = set(opponent_stones)
        
        # Priority queue: (distance, row, col)
        pq = []
        dist = {}
        
        if is_black:
            # Connect top (row 0) to bottom (row 10)
            for c in range(BOARD_SIZE):
                if (0, c) in stones_set:
                    heapq.heappush(pq, (0, 0, c))
                    dist[(0, c)] = 0
                elif (0, c) not in opp_set:
                    heapq.heappush(pq, (1, 0, c))
                    dist[(0, c)] = 1
        else:
            # Connect left (col 0) to right (col 10)
            for r in range(BOARD_SIZE):
                if (r, 0) in stones_set:
                    heapq.heappush(pq, (0, r, 0))
                    dist[(r, 0)] = 0
                elif (r, 0) not in opp_set:
                    heapq.heappush(pq, (1, r, 0))
                    dist[(r, 0)] = 1
        
        min_distance = float('inf')
        
        while pq:
            d, r, c = heapq.heappop(pq)
            
            if d > dist.get((r, c), float('inf')):
                continue
            
            # Check if we reached the goal
            if is_black and r == BOARD_SIZE - 1:
                min_distance = min(min_distance, d)
                continue
            elif not is_black and c == BOARD_SIZE - 1:
                min_distance = min(min_distance, d)
                continue
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opp_set:
                    continue
                
                new_dist = d + (0 if (nr, nc) in stones_set else 1)
                
                if new_dist < dist.get((nr, nc), float('inf')):
                    dist[(nr, nc)] = new_dist
                    heapq.heappush(pq, (new_dist, nr, nc))
        
        return min_distance, dist
    
    is_black = (color == 'b')
    
    # Evaluate each empty cell
    best_move = None
    best_score = -float('inf')
    
    # Get baseline distances
    my_dist, my_path_dist = shortest_path_distance(me, opp, is_black)
    opp_dist, opp_path_dist = shortest_path_distance(opp, me, not is_black)
    
    for cell in empty_cells:
        score = 0
        r, c = cell
        
        # How much does this move improve our path?
        my_new_dist, _ = shortest_path_distance(me + [cell], opp, is_black)
        score += (my_dist - my_new_dist) * 100
        
        # How much does this move block opponent?
        opp_new_dist, _ = shortest_path_distance(opp, me + [cell], not is_black)
        score += (opp_new_dist - opp_dist) * 80
        
        # Prefer cells on our shortest path
        if cell in my_path_dist and my_path_dist[cell] <= my_dist:
            score += 50
        
        # Prefer cells on opponent's shortest path (blocking)
        if cell in opp_path_dist and opp_path_dist[cell] <= opp_dist:
            score += 60
        
        # Prefer center positions early in game
        center_bonus = 10 - abs(r - 5) - abs(c - 5)
        if len(me) + len(opp) < 20:
            score += center_bonus * 2
        
        # Connection to existing stones
        neighbor_count = sum(1 for n in get_neighbors(r, c) if n in me_set)
        score += neighbor_count * 15
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    return best_move if best_move else empty_cells[0]
