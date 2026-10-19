
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = 15
    me_set = set(me)
    opp_set = set(opp)
    empty_cells = [(i, j) for i in range(N) for j in range(N) 
                   if valid_mask[i][j] and (i,j) not in me_set and (i,j) not in opp_set]
    
    # Directions for hexagonal grid (row, col) - indexing may need adjustment
    directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
    
    def is_corner(r, c):
        return (r == 0 and c == 0) or (r == 0 and c == N-1) or \
               (r == N-1 and c == 0) or (r == N-1 and c == N-1) or \
               (r == N//2 and c == 0) or (r == N//2 and c == N-1)
    
    def is_edge(r, c):
        return r == 0 or r == N-1 or c == 0 or c == N-1 or \
               (r <= N//2 and c == N-1 - r) or (r > N//2 and c == r - N//2)
    
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N:
                neighbors.append((nr, nc))
        return neighbors
    
    # Check if move would complete a ring for player
    def would_complete_ring(move, stones):
        visited = set()
        q = deque()
        start = move
        # Start from a neighbor of the new stone
        for neighbor in get_neighbors(*start):
            if neighbor in stones:
                q.append((neighbor, [start, neighbor]))
                visited.add(neighbor)
        
        while q:
            current, path = q.popleft()
            for neighbor in get_neighbors(*current):
                if neighbor == start and len(path) >= 4 and len(path) % 2 == 0:
                    # Check if it forms a ring (returns to start with even length)
                    return True
                if neighbor in stones and neighbor != path[-1]:
                    new_path = path + [neighbor]
                    q.append((neighbor, new_path))
        return False
    
    # Check if move would complete a bridge or fork
    def would_complete_connection(move, stones):
        corners = [ (0,0), (0, N-1), (N-1, 0), (N-1, N-1), (N//2, 0), (N//2, N-1) ]
        edges = set()
        connected_corners = 0
        connected_edges = 0
        
        # BFS to find connections
        visited = set()
        q = deque()
        q.append(move)
        visited.add(move)
        
        while q:
            r, c = q.popleft()
            if is_corner(r, c):
                connected_corners += 1
                if connected_corners >= 2:
                    return "bridge"
            if is_edge(r, c):
                edge = None
                if r == 0: edge = "top"
                elif r == N-1: edge = "bottom"
                elif c == 0: edge = "left"
                elif c == N-1: edge = "right"
                elif r <= N//2 and c == N-1 - r: edge = "top_right"
                elif r > N//2 and c == r - N//2: edge = "bottom_right"
                
                if edge is not None:
                    edges.add(edge)
                    if len(edges) >= 3:
                        return "fork"
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    q.append((nr, nc))
        
        return None
    
    # Check for immediate win for me
    for r, c in empty_cells:
        if would_complete_ring((r, c), me_set.union({(r, c)})):
            return (r, c)
        connection = would_complete_connection((r, c), me_set.union({(r, c)}))
        if connection in ["bridge", "fork"]:
            return (r, c)
    
    # Check for opponent's immediate threat
    for r, c in empty_cells:
        if would_complete_ring((r, c), opp_set.union({(r, c)})):
            return (r, c)
        connection = would_complete_connection((r, c), opp_set.union({(r, c)}))
        if connection in ["bridge", "fork"]:
            return (r, c)
    
    # Evaluation function for non-critical moves
    def evaluate_move(r, c):
        score = 0
        
        # Central control (hexagonal distance)
        center = (N//2, N//2)
        hex_dist = max(abs(r - center[0]), 
                       abs(c - center[1]), 
                       abs((r - center[0]) - (c - center[1])))
        score += (N - hex_dist) * 0.5
        
        # Connectivity to existing stones
        connections = 0
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in me_set:
                connections += 1
        score += connections * 10
        
        # Potential connections
        potential = 0
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and valid_mask[nr][nc] and (nr, nc) not in me_set and (nr, nc) not in opp_set:
                potential += 1
        score += potential * 2
        
        # Corner/edge value
        if is_corner(r, c):
            score += 5
        elif is_edge(r, c):
            score += 3
            
        return score
    
    # Find best non-critical move
    best_move = empty_cells[0]
    best_score = -1
    for r, c in empty_cells:
        score = evaluate_move(r, c)
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
