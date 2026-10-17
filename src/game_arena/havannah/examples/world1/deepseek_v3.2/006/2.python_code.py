
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = 15
    # Convert to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opp)
    
    # Get all valid moves
    valid_moves = [(r, c) for r in range(N) for c in range(N) if valid_mask[r][c]]
    if not valid_moves:
        # Should not happen, but fallback
        return (7, 7) if valid_mask[7][7] else valid_moves[0]
    
    # Direction vectors for hexagonal neighbors
    # For even rows (0-indexed):
    # Neighbors: (r-1,c), (r-1,c+1), (r,c-1), (r,c+1), (r+1,c), (r+1,c+1)
    # For odd rows:
    # Neighbors: (r-1,c-1), (r-1,c), (r,c-1), (r,c+1), (r+1,c-1), (r+1,c)
    
    def get_neighbors(r, c):
        if r % 2 == 0:  # Even row
            return [(r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c), (r+1, c+1)]
        else:  # Odd row
            return [(r-1, c-1), (r-1, c), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)]
    
    # BFS to find connected component
    def bfs_connected(start, stones_set):
        visited = set()
        queue = deque([start])
        component = []
        while queue:
            r, c = queue.popleft()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            component.append((r, c))
            for nr, nc in get_neighbors(r, c):
                if 0 <= nr < N and 0 <= nc < N:
                    if (nr, nc) in stones_set and (nr, nc) not in visited:
                        queue.append((nr, nc))
        return component
    
    # Check if a set of stones contains a bridge (connects two corners)
    def has_bridge(stones_set):
        corners = [(0, 0), (0, 7), (0, 14), (7, 0), (7, 14), (14, 0), (14, 7), (14, 14)]
        # Actually Havannah has 6 corners: (0,0), (0,14), (7,0), (7,14), (14,0), (14,14)
        # But we'll use all corner/edge points
        corner_stones = [c for c in corners if c in stones_set]
        if len(corner_stones) < 2:
            return False
        
        # Check connectivity between each pair
        for i in range(len(corner_stones)):
            for j in range(i+1, len(corner_stones)):
                # BFS to check if connected
                visited = set()
                queue = deque([corner_stones[i]])
                target = corner_stones[j]
                found = False
                while queue and not found:
                    r, c = queue.popleft()
                    if (r, c) == target:
                        found = True
                        break
                    if (r, c) in visited:
                        continue
                    visited.add((r, c))
                    for nr, nc in get_neighbors(r, c):
                        if 0 <= nr < N and 0 <= nc < N:
                            if (nr, nc) in stones_set and (nr, nc) not in visited:
                                queue.append((nr, nc))
                if found:
                    return True
        return False
    
    # Check if a set of stones contains a fork (connects three edges)
    def has_fork(stones_set):
        # Define edges (excluding corners)
        edges = []
        # Top edge (row 0, cols 1-13)
        edges.append([(0, c) for c in range(1, 14)])
        # Bottom edge (row 14, cols 1-13)
        edges.append([(14, c) for c in range(1, 14)])
        # Left edge (cols 0, all rows except corners at 0 and 14)
        edges.append([(r, 0) for r in range(1, 14)])
        # Right edge (cols 14, all rows except corners at 0 and 14)
        edges.append([(r, 14) for r in range(1, 14)])
        # NW-SE diagonal edges (more complex in hex grid)
        # We'll simplify: check if connected to multiple edges
        
        edge_connections = [False] * 4
        for idx, edge_cells in enumerate(edges):
            for cell in edge_cells:
                if cell in stones_set:
                    edge_connections[idx] = True
                    break
        
        # Count how many edges we touch
        edges_touched = sum(edge_connections)
        if edges_touched < 3:
            return False
        
        # Check if they're all connected through the stones
        # Find one stone from each touched edge
        edge_reps = []
        for idx, edge_cells in enumerate(edges):
            if edge_connections[idx]:
                for cell in edge_cells:
                    if cell in stones_set:
                        edge_reps.append(cell)
                        break
        
        # Check if all representatives are connected
        for i in range(len(edge_reps)):
            for j in range(i+1, len(edge_reps)):
                # BFS between edge_reps[i] and edge_reps[j]
                visited = set()
                queue = deque([edge_reps[i]])
                target = edge_reps[j]
                found = False
                while queue and not found:
                    r, c = queue.popleft()
                    if (r, c) == target:
                        found = True
                        break
                    if (r, c) in visited:
                        continue
                    visited.add((r, c))
                    for nr, nc in get_neighbors(r, c):
                        if 0 <= nr < N and 0 <= nc < N:
                            if (nr, nc) in stones_set and (nr, nc) not in visited:
                                queue.append((nr, nc))
                if not found:
                    return False
        return True
    
    # Check if a set of stones contains a ring
    def has_ring(stones_set):
        # Simplified ring check: look for cycles of length >= 6
        # We'll use DFS to find cycles
        if len(stones_set) < 6:
            return False
        
        visited = set()
        parent = {}
        
        def dfs_cycle(v, par):
            visited.add(v)
            for nb in get_neighbors(*v):
                if 0 <= nb[0] < N and 0 <= nb[1] < N and nb in stones_set:
                    if nb not in visited:
                        parent[nb] = v
                        if dfs_cycle(nb, v):
                            return True
                    elif nb != par:
                        # Found a cycle
                        # Check cycle length
                        cycle_len = 1
                        current = v
                        while current != nb:
                            current = parent[current]
                            cycle_len += 1
                        if cycle_len >= 6:
                            return True
            return False
        
        for stone in stones_set:
            if stone not in visited:
                if dfs_cycle(stone, None):
                    return True
        return False
    
    # Check if placing a stone at (r,c) would win for player
    def would_win(r, c, stones_set, is_me=True):
        # Create new set with the move
        new_set = set(stones_set)
        new_set.add((r, c))
        
        # Check all win conditions
        if has_bridge(new_set):
            return True
        if has_fork(new_set):
            return True
        if has_ring(new_set):
            return True
        return False
    
    # Evaluate move quality
    def evaluate_move(r, c):
        score = 0
        
        # Immediate win check
        if would_win(r, c, my_stones, True):
            score += 10000
        
        # Block opponent's immediate win
        temp_opp = set(opp_stones)
        temp_opp.add((r, c))
        if would_win(r, c, opp_stones, False):
            score += 5000
        
        # Connection to our stones
        my_connections = 0
        for nr, nc in get_neighbors(r, c):
            if 0 <= nr < N and 0 <= nc < N:
                if (nr, nc) in my_stones:
                    my_connections += 1
        score += my_connections * 50
        
        # Block opponent connections
        opp_connections = 0
        for nr, nc in get_neighbors(r, c):
            if 0 <= nr < N and 0 <= nc < N:
                if (nr, nc) in opp_stones:
                    opp_connections += 1
        score += opp_connections * 30
        
        # Distance to center (good for rings)
        center_dist = abs(r - 7) + abs(c - 7)
        score += (14 - center_dist) * 2
        
        # Edge proximity (good for bridges/forks)
        if r == 0 or r == 14 or c == 0 or c == 14:
            score += 10
        elif r == 1 or r == 13 or c == 1 or c == 13:
            score += 5
        
        # Corner proximity (good for bridges)
        if (r == 0 and c == 0) or (r == 0 and c == 14) or \
           (r == 14 and c == 0) or (r == 14 and c == 14) or \
           (r == 7 and c == 0) or (r == 7 and c == 14):
            score += 20
        
        # Avoid being too close to opponent's strong groups
        for or_, oc in opp_stones:
            dist = abs(r - or_) + abs(c - oc)
            if dist <= 2:
                score -= 5
            elif dist == 1:
                score += 10  # Actually good to block
        
        # Prefer moves that expand our territory
        if len(my_stones) > 0:
            min_dist_to_mine = min(abs(r - mr) + abs(c - mc) for mr, mc in my_stones)
            if min_dist_to_mine <= 3:
                score += 20
        
        return score
    
    # Check for immediate winning moves
    for r, c in valid_moves:
        if would_win(r, c, my_stones, True):
            return (r, c)
    
    # Check for moves that block opponent's immediate win
    for r, c in valid_moves:
        temp_opp = set(opp_stones)
        temp_opp.add((r, c))
        if would_win(r, c, opp_stones, False):
            return (r, c)
    
    # Otherwise, choose best evaluated move
    best_score = -float('inf')
    best_move = valid_moves[0]
    
    for r, c in valid_moves:
        score = evaluate_move(r, c)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
