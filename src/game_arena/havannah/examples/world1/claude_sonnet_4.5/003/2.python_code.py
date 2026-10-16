
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Smart Havannah policy that detects wins, blocks threats, and plays strategically.
    """
    N = len(valid_mask)
    
    # Get neighbors on hexagonal grid
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0), (1, -1), (-1, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc]:
                neighbors.append((nr, nc))
        return neighbors
    
    # Check if position is corner or edge
    def get_board_features(r, c):
        corners = [(0, 0), (0, 7), (7, 0), (7, 14), (14, 7), (14, 14)]
        is_corner = (r, c) in corners
        
        # Edges (not corners)
        is_edge = False
        edge_id = -1
        if r == 0 and c > 0 and c < 7:
            is_edge, edge_id = True, 0
        elif r == 0 and c > 7:
            is_edge, edge_id = True, 1
        elif c == 0 and r > 0 and r < 7:
            is_edge, edge_id = True, 2
        elif c == 14 and r > 7 and r < 14:
            is_edge, edge_id = True, 3
        elif r == 14 and c < 14 and c > 7:
            is_edge, edge_id = True, 4
        elif r == 14 and c < 7:
            is_edge, edge_id = True, 5
        
        return is_corner, is_edge, edge_id
    
    # Check winning conditions for a player
    def check_win(stones):
        if len(stones) < 6:
            return False
        
        stone_set = set(stones)
        
        # Build connectivity using Union-Find
        parent = {s: s for s in stones}
        
        def find(x):
            if parent[x] != x:
                parent[x] = find(parent[x])
            return parent[x]
        
        def union(x, y):
            px, py = find(x), find(y)
            if px != py:
                parent[px] = py
        
        # Connect adjacent stones
        for stone in stones:
            for neighbor in get_neighbors(*stone):
                if neighbor in stone_set:
                    union(stone, neighbor)
        
        # Group stones by component
        components = {}
        for stone in stones:
            root = find(stone)
            if root not in components:
                components[root] = []
            components[root].append(stone)
        
        # Check each component for winning conditions
        for component in components.values():
            comp_set = set(component)
            
            # Check bridge (connects 2 corners)
            corners = [(0, 0), (0, 7), (7, 0), (7, 14), (14, 7), (14, 14)]
            corner_count = sum(1 for c in corners if c in comp_set)
            if corner_count >= 2:
                return True
            
            # Check fork (connects 3 edges)
            edges = [set() for _ in range(6)]
            for r, c in component:
                _, is_edge, edge_id = get_board_features(r, c)
                if is_edge:
                    edges[edge_id].add((r, c))
            
            edge_touched = sum(1 for e in edges if len(e) > 0)
            if edge_touched >= 3:
                return True
            
            # Check ring using BFS to find cycle
            if len(component) >= 6:
                for start in component:
                    visited = {start}
                    queue = deque([(start, [start])])
                    
                    while queue:
                        current, path = queue.popleft()
                        
                        for neighbor in get_neighbors(*current):
                            if neighbor in comp_set:
                                if neighbor == start and len(path) >= 6:
                                    return True
                                if neighbor not in visited:
                                    visited.add(neighbor)
                                    queue.append((neighbor, path + [neighbor]))
        
        return False
    
    # Find best move
    valid_moves = [(r, c) for r in range(N) for c in range(N) 
                   if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp]
    
    if not valid_moves:
        return (0, 0)  # Should never happen
    
    # Check if we can win
    for move in valid_moves:
        if check_win(me + [move]):
            return move
    
    # Check if we must block opponent win
    for move in valid_moves:
        if check_win(opp + [move]):
            return move
    
    # Strategic evaluation
    def evaluate_move(move):
        r, c = move
        score = 0
        
        is_corner, is_edge, edge_id = get_board_features(r, c)
        
        # Corners are very valuable
        if is_corner:
            score += 50
        
        # Edges are valuable
        if is_edge:
            score += 30
        
        # Center control
        center_dist = abs(r - 7) + abs(c - 7)
        score += max(0, 20 - center_dist)
        
        # Connectivity to our stones
        my_neighbors = sum(1 for n in get_neighbors(r, c) if n in me)
        score += my_neighbors * 15
        
        # Disruption of opponent
        opp_neighbors = sum(1 for n in get_neighbors(r, c) if n in opp)
        score += opp_neighbors * 10
        
        return score
    
    # First move: take center
    if not me and not opp:
        return (7, 7)
    
    # Find best strategic move
    best_move = max(valid_moves, key=evaluate_move)
    return best_move
