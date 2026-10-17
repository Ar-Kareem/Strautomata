
import heapq
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    BOARD_SIZE = 11
    
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    
    def get_neighbors(r, c):
        """Get all 6 hexagonal neighbors"""
        candidates = [
            (r-1, c), (r-1, c+1),
            (r, c-1), (r, c+1),
            (r+1, c-1), (r+1, c)
        ]
        return [(nr, nc) for nr, nc in candidates 
                if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE]
    
    def dijkstra_distance(my_stones, opp_stones, is_black):
        """Calculate minimum resistance path from one side to the other"""
        my_set = set(my_stones)
        opp_set = set(opp_stones)
        
        # Priority queue: (distance, row, col)
        pq = []
        dist = {}
        
        if is_black:
            # Black connects top to bottom (row 0 to row 10)
            for c in range(BOARD_SIZE):
                if (0, c) in my_set:
                    heapq.heappush(pq, (0, 0, c))
                    dist[(0, c)] = 0
                elif (0, c) not in opp_set:
                    heapq.heappush(pq, (1, 0, c))
                    dist[(0, c)] = 1
        else:
            # White connects left to right (col 0 to col 10)
            for r in range(BOARD_SIZE):
                if (r, 0) in my_set:
                    heapq.heappush(pq, (0, r, 0))
                    dist[(r, 0)] = 0
                elif (r, 0) not in opp_set:
                    heapq.heappush(pq, (1, r, 0))
                    dist[(r, 0)] = 1
        
        while pq:
            d, r, c = heapq.heappop(pq)
            
            if dist.get((r, c), float('inf')) < d:
                continue
            
            # Check if reached goal
            if is_black and r == BOARD_SIZE - 1:
                return d
            if not is_black and c == BOARD_SIZE - 1:
                return d
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opp_set:
                    continue
                
                cost = 0 if (nr, nc) in my_set else 1
                new_dist = d + cost
                
                if new_dist < dist.get((nr, nc), float('inf')):
                    dist[(nr, nc)] = new_dist
                    heapq.heappush(pq, (new_dist, nr, nc))
        
        return float('inf')
    
    def evaluate_position(my_stones, opp_stones):
        """Evaluate board position - lower is better for us"""
        is_black = (color == 'b')
        my_dist = dijkstra_distance(my_stones, opp_stones, is_black)
        opp_dist = dijkstra_distance(opp_stones, my_stones, not is_black)
        
        # We want low distance for us, high for opponent
        return my_dist - opp_dist * 1.5
    
    # Get all legal moves
    legal_moves = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                   if (r, c) not in occupied]
    
    if not legal_moves:
        return (0, 0)  # Should never happen
    
    # Opening move strategy
    if len(me) == 0:
        # First move - take center
        return (5, 5)
    
    if len(me) == 1 and len(opp) == 1:
        # Second move - respond strategically
        center_moves = [(5, 5), (5, 4), (4, 5), (6, 5), (5, 6), (4, 6), (6, 4)]
        for move in center_moves:
            if move in legal_moves:
                return move
    
    # Evaluate all moves
    best_move = None
    best_score = float('inf')
    
    current_score = evaluate_position(me, opp)
    
    for move in legal_moves:
        # Simulate placing our stone
        new_me = me_set | {move}
        
        # Calculate improvement
        new_score = evaluate_position(list(new_me), list(opp_set))
        
        # Bonus for moves near existing stones (connectivity)
        connectivity_bonus = 0
        for neighbor in get_neighbors(move[0], move[1]):
            if neighbor in me_set:
                connectivity_bonus -= 0.3
        
        # Bonus for blocking opponent
        blocking_bonus = 0
        for neighbor in get_neighbors(move[0], move[1]):
            if neighbor in opp_set:
                blocking_bonus -= 0.2
        
        # Center control bonus (early-mid game)
        if len(occupied) < 40:
            center_dist = abs(move[0] - 5) + abs(move[1] - 5)
            center_bonus = -center_dist * 0.05
        else:
            center_bonus = 0
        
        total_score = new_score + connectivity_bonus + blocking_bonus + center_bonus
        
        if total_score < best_score:
            best_score = total_score
            best_move = move
    
    return best_move if best_move else legal_moves[0]
