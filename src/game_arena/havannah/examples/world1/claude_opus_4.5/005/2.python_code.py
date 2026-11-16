
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    N = len(valid_mask)
    me_set = set(me)
    opp_set = set(opp)
    
    # Get valid moves
    valid_moves = [(r, c) for r in range(N) for c in range(N) 
                   if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set]
    
    if not valid_moves:
        # Fallback: return any valid cell
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c]:
                    return (r, c)
    
    if len(valid_moves) == 1:
        return valid_moves[0]
    
    # Hexagonal neighbors
    def get_neighbors(r, c):
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]
        return [(r + dr, c + dc) for dr, dc in offsets if 0 <= r + dr < N and 0 <= c + dc < N and valid_mask[r + dr][c + dc]]
    
    # Identify corners and edges
    corners = set()
    edges = {i: set() for i in range(6)}
    
    for r in range(N):
        for c in range(N):
            if not valid_mask[r][c]:
                continue
            neighs = get_neighbors(r, c)
            valid_neighs = [n for n in neighs if valid_mask[n[0]][n[1]]]
            if len(valid_neighs) <= 3:
                corners.add((r, c))
            elif len(valid_neighs) == 4:
                # Edge cell - categorize by position
                if r == 0:
                    edges[0].add((r, c))
                elif c == 0 and r < N // 2:
                    edges[1].add((r, c))
                elif c == 0 and r >= N // 2:
                    edges[2].add((r, c))
                elif r == N - 1:
                    edges[3].add((r, c))
                elif c == N - 1 and r >= N // 2:
                    edges[4].add((r, c))
                else:
                    edges[5].add((r, c))
    
    # Score each move
    center = N // 2
    best_score = -float('inf')
    best_move = valid_moves[0]
    
    for move in valid_moves:
        r, c = move
        score = 0
        
        # Centrality bonus
        dist_to_center = abs(r - center) + abs(c - center)
        score += (N - dist_to_center) * 2
        
        # Connectivity to own stones
        neighs = get_neighbors(r, c)
        own_neighbors = sum(1 for n in neighs if n in me_set)
        score += own_neighbors * 15
        
        # Block opponent connections
        opp_neighbors = sum(1 for n in neighs if n in opp_set)
        score += opp_neighbors * 10
        
        # Corner proximity for bridge potential
        if move in corners:
            score += 25
        
        # Edge for fork potential
        for edge_set in edges.values():
            if move in edge_set:
                score += 8
                break
        
        # Prefer moves that extend our connected components toward different strategic areas
        if own_neighbors > 0:
            score += 20
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
