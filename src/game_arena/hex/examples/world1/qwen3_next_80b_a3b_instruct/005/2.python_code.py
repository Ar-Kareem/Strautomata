
import heapq
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Precomputed hexagonal neighbor offsets
    # For a cell (r, c), neighbors are:
    # (r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)
    # This corresponds to the hex grid where even rows have neighbors shifted
    # But in our coordinate system, the 6 neighbors are:
    # (i-1, j-1), (i-1, j), (i, j-1), (i, j+1), (i+1, j-1), (i+1, j) 
    # However, the problem states: "every cell touches 6 others, excluding (i-1,j-1) and (i+1,j+1)"
    # Actually, the example clarifies: (4,1) touches (4,0), (4,2), (5,1), (5,0), (3,1), (3,2)
    # So for (i,j), the neighbors are:
    # (i, j-1), (i, j+1)
    # (i-1, j), (i-1, j+1)
    # (i+1, j-1), (i+1, j)
    
    neighbors = [
        (-1, 0), (-1, 1),
        (0, -1), (0, 1),
        (1, -1), (1, 0)
    ]
    
    # Build set of occupied cells for O(1) lookup
    occupied = set(me + opp)
    
    # Function to check if a move is legal
    def is_legal(r, c):
        return 0 <= r <= 10 and 0 <= c <= 10 and (r, c) not in occupied
    
    # Function to get valid neighbors of a cell
    def get_neighbors(r, c):
        for dr, dc in neighbors:
            nr, nc = r + dr, c + dc
            if is_legal(nr, nc):
                yield (nr, nc)
    
    # Check if a player has won
    def has_won(player_stones, player_color):
        if player_color == 'b':
            # Black connects top (row 0) to bottom (row 10)
            top_stones = [(r, c) for r, c in player_stones if r == 0]
            bottom_stones = [(r, c) for r, c in player_stones if r == 10]
            if not top_stones or not bottom_stones:
                return False
            
            # BFS to see if any top stone connects to any bottom stone
            visited = set()
            queue = deque(top_stones)
            for stone in top_stones:
                visited.add(stone)
            
            while queue:
                r, c = queue.popleft()
                if r == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in player_stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
        else:  # color == 'w'
            # White connects left (col 0) to right (col 10)
            left_stones = [(r, c) for r, c in player_stones if c == 0]
            right_stones = [(r, c) for r, c in player_stones if c == 10]
            if not left_stones or not right_stones:
                return False
            
            # BFS to see if any left stone connects to any right stone
            visited = set()
            queue = deque(left_stones)
            for stone in left_stones:
                visited.add(stone)
            
            while queue:
                r, c = queue.popleft()
                if c == 10:
                    return True
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in player_stones and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return False
    
    # Check if current player has an immediate winning move
    for r in range(11):
        for c in range(11):
            if is_legal(r, c):
                # Simulate placing stone
                me_copy = me + [(r, c)]
                if has_won(me_copy, color):
                    return (r, c)
    
    # Check if opponent has an immediate winning move - block it
    opp_color = 'w' if color == 'b' else 'b'
    for r in range(11):
        for c in range(11):
            if is_legal(r, c):
                # Simulate opponent placing stone
                opp_copy = opp + [(r, c)]
                if has_won(opp_copy, opp_color):
                    return (r, c)
    
    # For strategic moves, prioritize based on edge connections and centrality
    best_move = None
    best_score = -1
    
    # Preferred positions: edges and center
    for r in range(11):
        for c in range(11):
            if not is_legal(r, c):
                continue
            
            # Calculate score for this move
            score = 0
            
            # 1. Edge connection bonus
            if color == 'b':
                if r == 0 or r == 10:
                    score += 5
                # Center bonus
                score += 2 - abs(5.5 - r) - abs(5.5 - c)
            else:  # color == 'w'
                if c == 0 or c == 10:
                    score += 5
                # Center bonus
                score += 2 - abs(5.5 - r) - abs(5.5 - c)
            
            # 2. Connection to own stones
            for dr, dc in neighbors:
                nr, nc = r + dr, c + dc
                if (nr, nc) in me:
                    score += 3
            
            # 3. Block opponent's potential connections
            for dr, dc in neighbors:
                nr, nc = r + dr, c + dc
                if (nr, nc) in opp:
                    score += 1
            
            # 4. Number of liberties (empty adjacent spaces) - more is better for flexibility
            liberties = 0
            for dr, dc in neighbors:
                nr, nc = r + dr, c + dc
                if is_legal(nr, nc):
                    liberties += 1
            score += liberties * 0.5
            
            # 5. Avoid placing on a spot that creates a dead-end (only one connection)
            connections_to_me = sum(1 for dr, dc in neighbors if (r + dr, c + dc) in me)
            if connections_to_me == 0:
                score -= 1  # Isolated move
            elif connections_to_me == 1:
                score += 0.5  # Single connection - better than none
            
            # Update best move
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    # Fallback: return first available move (should be handled by above, but safety)
    if best_move is None:
        for r in range(11):
            for c in range(11):
                if is_legal(r, c):
                    return (r, c)
    
    return best_move
