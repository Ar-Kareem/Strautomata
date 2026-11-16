
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = 15
    
    # Get neighbors for hexagonal grid
    def get_neighbors(r, c):
        neighbors = [
            (r-1, c), (r+1, c),  # same column
            (r, c-1), (r, c+1),  # left and right
            (r-1, c-1), (r+1, c+1)  # diagonals for hex
        ]
        return [(nr, nc) for nr, nc in neighbors if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]]
    
    # Check if position is corner
    def is_corner(r, c):
        corners = [(0, 0), (0, 14), (7, 0), (7, 14), (14, 0), (14, 14)]
        # Actual hex corners depend on valid_mask shape
        if not valid_mask[r][c]:
            return False
        # Check if it's an actual corner (has valid_mask but at extreme positions)
        corner_candidates = []
        for rr in range(N):
            for cc in range(N):
                if valid_mask[rr][cc]:
                    corner_candidates.append((rr, cc))
        # Find 6 corners based on extremes
        corners_found = set()
        # This is approximation - we'll check degree
        neighbor_count = len(get_neighbors(r, c))
        return neighbor_count <= 2
    
    # Check if position is on edge (not corner)
    def is_edge(r, c):
        if not valid_mask[r][c]:
            return False
        neighbor_count = len(get_neighbors(r, c))
        return 3 <= neighbor_count <= 4
    
    # Find connected component
    def get_connected_component(stones_set):
        if not stones_set:
            return []
        visited = set()
        components = []
        for stone in stones_set:
            if stone in visited:
                continue
            component = []
            queue = deque([stone])
            visited.add(stone)
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in stones_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            components.append(component)
        return components
    
    # Check if adding a stone creates a win
    def creates_win(stones, new_stone):
        test_stones = set(stones + [new_stone])
        components = get_connected_component(test_stones)
        if not components:
            return False
        main_component = max(components, key=len)
        comp_set = set(main_component)
        
        # Check bridge (connects 2 corners)
        corners_in_comp = sum(1 for r, c in comp_set if is_corner(r, c))
        if corners_in_comp >= 2:
            return True
        
        # Check fork (connects 3 edges)
        edges_touched = set()
        for r, c in comp_set:
            if r == 0 or r == N-1 or c == 0 or c == N-1:
                # Determine which edge
                if r <= 2:
                    edges_touched.add('top')
                if r >= N-3:
                    edges_touched.add('bottom')
                if c <= 2:
                    edges_touched.add('left')
                if c >= N-3:
                    edges_touched.add('right')
        if len(edges_touched) >= 3:
            return True
        
        # Check ring (simplified - checks if there's a cycle)
        if len(comp_set) >= 6:
            # Simple heuristic: if component has high connectivity, might be ring
            pass
        
        return False
    
    # Get all valid moves
    valid_moves = []
    occupied = set(me + opp)
    for r in range(N):
        for c in range(N):
            if valid_mask[r][c] and (r, c) not in occupied:
                valid_moves.append((r, c))
    
    if not valid_moves:
        # Fallback - should not happen
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c]:
                    return (r, c)
    
    # Check for immediate win
    for move in valid_moves:
        if creates_win(me, move):
            return move
    
    # Check for blocking opponent win
    for move in valid_moves:
        if creates_win(opp, move):
            return move
    
    # Score remaining moves
    me_set = set(me)
    opp_set = set(opp)
    
    best_score = -float('inf')
    best_move = valid_moves[0]
    
    for r, c in valid_moves:
        score = 0
        
        # Prefer corners
        if is_corner(r, c):
            score += 30
        elif is_edge(r, c):
            score += 15
        else:
            # Prefer center
            center_dist = abs(r - 7) + abs(c - 7)
            score += max(0, 10 - center_dist)
        
        # Connectivity to our stones
        my_neighbors = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in me_set)
        score += my_neighbors * 10
        
        # Block opponent connectivity
        opp_neighbors = sum(1 for nr, nc in get_neighbors(r, c) if (nr, nc) in opp_set)
        score += opp_neighbors * 8
        
        # Add randomness to break ties
        score += np.random.random() * 0.1
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
