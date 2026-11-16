
import numpy as np

def get_neighbors(r, c, board_size=15):
    """Hexagonal neighbors for Havannah mapping."""
    # Based on the prompt's neighbor description:
    # (r+1, c), (r-1, c)
    # (r-1, c-1), (r, c-1) -> 'left'
    # (r, c+1), (r+1, c+1) -> 'right'
    potential = [
        (r - 1, c), (r + 1, c),
        (r, c - 1), (r, c + 1),
        (r - 1, c - 1), (r + 1, c + 1)
    ]
    return [(nr, nc) for nr, nc in potential if 0 <= nr < board_size and 0 <= nc < board_size]

def policy(me: list[tuple[int, int], ...], opp: list[tuple[int, int], ...], valid_mask) -> tuple[int, int]:
    N = 15
    occ_me = set(me)
    occ_opp = set(opp)
    occupied = occ_me.union(occ_opp)

    best_move = None
    max_score = -float('inf')

    # Pre-calculate center preference
    center = N // 2
    
    # Priority 1: Take the very center if available
    if valid_mask[center][center] and (center, center) not in occupied:
        return (center, center)

    for r in range(N):
        for c in range(N):
            if not valid_mask[r][c] or (r, c) in occupied:
                continue
            
            score = 0
            neighbors = get_neighbors(r, c, N)
            
            me_neighbors = 0
            opp_neighbors = 0
            for nr, nc in neighbors:
                if (nr, nc) in occ_me:
                    me_neighbors += 1
                elif (nr, nc) in occ_opp:
                    opp_neighbors += 1
            
            # 1. Connectivity: Prefer placing near our own stones
            score += me_neighbors * 10
            
            # 2. Block: Urgently block if opponent has many neighbors (building a path)
            score += opp_neighbors * 12
            
            # 3. Structural Importance: Nearness to edges/corners
            # Edges: r=0, c=0, r=14, c=14, etc. (adjusted for hex board shape)
            is_edge = False
            # Corners (approximate for the 15x15 mask)
            corners = [(0,0), (0,7), (7,0), (14,7), (7,14), (14,14)]
            if (r, c) in corners:
                score += 5
                
            # 4. Centrality: Favor moves closer to center to keep options open
            dist_to_center = abs(r - center) + abs(c - center)
            score -= dist_to_center * 0.5

            # 5. Lookahead: Check if move creates 'bridge' or 'fork' potential
            # (Simplified: value empty neighbors that are also valid)
            for nr, nc in neighbors:
                if valid_mask[nr][nc] and (nr, nc) not in occupied:
                    score += 1

            if score > max_score:
                max_score = score
                best_move = (r, c)

    # Fallback to any valid move
    if best_move is None:
        for r in range(N):
            for c in range(N):
                if valid_mask[r][c] and (r, c) not in occupied:
                    return (r, c)

    return best_move
