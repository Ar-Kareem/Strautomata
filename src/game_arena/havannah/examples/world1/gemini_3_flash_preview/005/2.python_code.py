
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    size = 15
    occupied = set(me) | set(opp)
    
    def get_neighbors(r, c):
        # Hexagonal neighbors as defined in the prompt:
        # Same col: (r+1, c), (r-1, c)
        # Left col: (r-1, c-1), (r, c-1)
        # Right col: (r, c+1), (r+1, c+1)
        candidates = [
            (r + 1, c), (r - 1, c),
            (r, c - 1), (r - 1, c - 1),
            (r, c + 1), (r + 1, c + 1)
        ]
        return [(nr, nc) for nr, nc in candidates if 0 <= nr < size and 0 <= nc < size and valid_mask[nr][nc]]

    def score_move(r, c):
        # Base score favors the center
        center = size // 2
        dist_to_center = abs(r - center) + abs(c - center)
        score = (size - dist_to_center) * 0.1
        
        neighbors = get_neighbors(r, c)
        
        me_count = 0
        opp_count = 0
        for nr, nc in neighbors:
            if (nr, nc) in me:
                me_count += 1
            elif (nr, nc) in opp:
                opp_count += 1
        
        # Priority 1: Blocking the opponent from clustering
        score += opp_count * 2.5
        # Priority 2: Connecting own stones
        score += me_count * 3.0
        
        # Corner and Edge detection for Havannah logic
        # Corners (approximate indices for 15x15 hex layout)
        corners = [(0, 0), (0, 7), (7, 0), (7, 14), (14, 7), (14, 14)]
        if (r, c) in corners:
            score += 5.0
            
        # Edges (non-corners)
        is_edge = False
        if r == 0 or r == size-1 or c == 0 or c == size-1:
            is_edge = True
        
        # Heuristic for bridge/fork potential
        if is_edge:
            score += 1.5
            
        return score

    best_move = None
    max_score = -float('inf')
    
    # Iterate through all valid points
    for r in range(size):
        for c in range(size):
            if valid_mask[r][c] and (r, c) not in occupied:
                s = score_move(r, c)
                # Add a tiny bit of noise to avoid deterministic ties
                s += (hash((r, c)) % 100) * 0.001
                if s > max_score:
                    max_score = s
                    best_move = (r, c)
    
    # Fallback if no move found (should not happen given logic)
    if best_move is None:
        for r in range(size):
            for c in range(size):
                if valid_mask[r][c] and (r, c) not in occupied:
                    return (r, c)

    return best_move
