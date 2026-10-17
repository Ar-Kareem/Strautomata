
import random
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    BOARD_SIZE = 11
    
    # Get all empty cells
    occupied = set(me + opp)
    empty_cells = [(i, j) for i in range(BOARD_SIZE) for j in range(BOARD_SIZE) if (i, j) not in occupied]
    
    if not empty_cells:
        return (0, 0)  # Should never happen in legal game
    
    # First move heuristic - take center
    if len(me) == 0:
        return (5, 5)
    
    def get_neighbors(pos):
        """Get the 6 hexagonal neighbors of a position"""
        i, j = pos
        neighbors = []
        for di, dj in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            ni, nj = i + di, j + dj
            if 0 <= ni < BOARD_SIZE and 0 <= nj < BOARD_SIZE:
                neighbors.append((ni, nj))
        return neighbors
    
    def dijkstra_distance(stones, target_color, empty_positions):
        """Calculate minimum resistance path from one side to the other"""
        import heapq
        
        # Initialize distances
        dist = {}
        heap = []
        
        if target_color == 'b':
            # Black connects top (row 0) to bottom (row 10)
            # Add all top edge positions
            for j in range(BOARD_SIZE):
                if (0, j) in stones:
                    dist[(0, j)] = 0
                    heapq.heappush(heap, (0, (0, j)))
                elif (0, j) in empty_positions:
                    dist[(0, j)] = 1
                    heapq.heappush(heap, (1, (0, j)))
        else:
            # White connects left (col 0) to right (col 10)
            for i in range(BOARD_SIZE):
                if (i, 0) in stones:
                    dist[(i, 0)] = 0
                    heapq.heappush(heap, (0, (i, 0)))
                elif (i, 0) in empty_positions:
                    dist[(i, 0)] = 1
                    heapq.heappush(heap, (1, (i, 0)))
        
        while heap:
            d, pos = heapq.heappop(heap)
            
            if d > dist.get(pos, float('inf')):
                continue
            
            for neighbor in get_neighbors(pos):
                if neighbor in stones:
                    new_dist = d
                elif neighbor in empty_positions:
                    new_dist = d + 1
                else:
                    continue
                
                if new_dist < dist.get(neighbor, float('inf')):
                    dist[neighbor] = new_dist
                    heapq.heappush(heap, (new_dist, neighbor))
        
        # Find minimum distance to target edge
        min_dist = float('inf')
        if target_color == 'b':
            for j in range(BOARD_SIZE):
                min_dist = min(min_dist, dist.get((10, j), float('inf')))
        else:
            for i in range(BOARD_SIZE):
                min_dist = min(min_dist, dist.get((i, 10), float('inf')))
        
        return min_dist
    
    def evaluate_move(move):
        """Evaluate the quality of a move"""
        # Simulate placing the stone
        my_stones_with_move = set(me + [move])
        empty_with_move = set(empty_cells) - {move}
        
        # Calculate my connection strength with this move
        my_dist = dijkstra_distance(my_stones_with_move, color, empty_with_move)
        
        # Calculate opponent's connection strength if they played here
        opp_stones_with_move = set(opp + [move])
        opp_color = 'w' if color == 'b' else 'b'
        opp_dist = dijkstra_distance(opp_stones_with_move, opp_color, empty_with_move)
        
        # Current opponent distance without this move
        opp_dist_current = dijkstra_distance(set(opp), opp_color, set(empty_cells))
        
        # Score: favor moves that improve our position and block opponent
        blocking_value = max(0, opp_dist_current - opp_dist) * 2
        connection_value = 20 - my_dist
        
        # Bonus for center control early game
        center_bonus = 0
        if len(me) < 5:
            center_dist = abs(move[0] - 5) + abs(move[1] - 5)
            center_bonus = (10 - center_dist) * 0.5
        
        return connection_value + blocking_value + center_bonus
    
    # Evaluate all empty cells
    best_score = -float('inf')
    best_moves = []
    
    for cell in empty_cells:
        score = evaluate_move(cell)
        if score > best_score:
            best_score = score
            best_moves = [cell]
        elif score == best_score:
            best_moves.append(cell)
    
    # Return best move (random tie-break)
    return random.choice(best_moves) if best_moves else empty_cells[0]
