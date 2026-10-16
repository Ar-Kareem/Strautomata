
import numpy as np

def policy(me, opp, valid_mask):
    corners = [(0, 0), (0, 14), (14, 14), (14, 0), (0, 7), (14, 7)]
    corners_set = set(corners)
    me_set = set(me)
    opp_set = set(opp)
    center = (7, 7)
    
    def is_on_edge(r, c):
        if (r, c) in corners_set:
            return False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
            nr, nc = r + dr, c + dc
            if not (0 <= nr < 15 and 0 <= nc < 15):
                return True
            if not valid_mask[nr][nc]:
                return True
        return False
    
    possible_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                possible_moves.append((r, c))
    
    best_score = -float('inf')
    best_move = possible_moves[0]
    
    for r, c in possible_moves:
        score = 0
        
        # Corner contribution: reward for being on or adjacent to corners
        if (r, c) in corners_set:
            score += 3
        adjacent_corners = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15 and (nr, nc) in corners_set:
                adjacent_corners += 1
        score += adjacent_corners
        
        # Edge contribution: reward for being on or adjacent to edges (excluding corners)
        edge_contrib = 0
        if is_on_edge(r, c):
            edge_contrib += 2
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15 and is_on_edge(nr, nc):
                edge_contrib += 1
        score += edge_contrib
        
        # Center contribution: reward for being closer to the center
        distance_to_center = abs(r - center[0]) + abs(c - center[1])
        score += 1000 / (distance_to_center + 1)
        
        # Connectivity: reward for connecting to existing stones
        connected = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in me:
                connected += 1
        score += 5 * connected
        
        # Update best move
        if score > best_score:
            best_score = score
            best_move = (r, c)
    
    return best_move
