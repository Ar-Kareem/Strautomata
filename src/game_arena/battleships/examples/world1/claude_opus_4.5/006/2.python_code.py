
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    SHIPS = [5, 4, 3, 3, 2]
    
    # Find all hits, misses, and unknown cells
    hits = set()
    unknown = set()
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.add((r, c))
            elif board[r][c] == 0:
                unknown.add((r, c))
    
    if not unknown:
        # Shouldn't happen, but fallback
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    return (r, c)
    
    # If we have hits, prioritize completing ships
    if hits:
        # Find connected components of hits
        def get_neighbors(r, c):
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10:
                    yield nr, nc
        
        # For each hit, check if it has unknown neighbors
        priority_targets = []
        
        for r, c in hits:
            # Determine if this hit is part of a horizontal or vertical line
            h_hits = [(r, c)]
            for dc in [-1, 1]:
                nc = c + dc
                while 0 <= nc < 10 and (r, nc) in hits:
                    h_hits.append((r, nc))
                    nc += dc
            
            v_hits = [(r, c)]
            for dr in [-1, 1]:
                nr = r + dr
                while 0 <= nr < 10 and (nr, c) in hits:
                    v_hits.append((nr, c))
                    nr += dr
            
            # If horizontal line of 2+ hits, extend horizontally
            if len(h_hits) >= 2:
                min_c = min(p[1] for p in h_hits)
                max_c = max(p[1] for p in h_hits)
                if min_c > 0 and (r, min_c - 1) in unknown:
                    priority_targets.append(((r, min_c - 1), len(h_hits) + 10))
                if max_c < 9 and (r, max_c + 1) in unknown:
                    priority_targets.append(((r, max_c + 1), len(h_hits) + 10))
            
            # If vertical line of 2+ hits, extend vertically
            if len(v_hits) >= 2:
                min_r = min(p[0] for p in v_hits)
                max_r = max(p[0] for p in v_hits)
                if min_r > 0 and (min_r - 1, c) in unknown:
                    priority_targets.append(((min_r - 1, c), len(v_hits) + 10))
                if max_r < 9 and (max_r + 1, c) in unknown:
                    priority_targets.append(((max_r + 1, c), len(v_hits) + 10))
            
            # Single hit - try all directions
            if len(h_hits) == 1 and len(v_hits) == 1:
                for nr, nc in get_neighbors(r, c):
                    if (nr, nc) in unknown:
                        priority_targets.append(((nr, nc), 5))
        
        if priority_targets:
            # Sort by priority (higher is better) and pick the best
            priority_targets.sort(key=lambda x: -x[1])
            best_score = priority_targets[0][1]
            best_targets = [t[0] for t in priority_targets if t[1] == best_score]
            return random.choice(best_targets)
    
    # Hunt mode: calculate probability density
    prob = [[0.0] * 10 for _ in range(10)]
    
    for ship_len in SHIPS:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - ship_len + 1):
                valid = True
                has_hit = False
                for i in range(ship_len):
                    if board[r][c + i] == -1:
                        valid = False
                        break
                    if board[r][c + i] == 1:
                        has_hit = True
                if valid and not has_hit:
                    for i in range(ship_len):
                        if board[r][c + i] == 0:
                            prob[r][c + i] += 1
        
        # Vertical placements
        for r in range(10 - ship_len + 1):
            for c in range(10):
                valid = True
                has_hit = False
                for i in range(ship_len):
                    if board[r + i][c] == -1:
                        valid = False
                        break
                    if board[r + i][c] == 1:
                        has_hit = True
                if valid and not has_hit:
                    for i in range(ship_len):
                        if board[r + i][c] == 0:
                            prob[r + i][c] += 1
    
    # Find cell with highest probability
    best_prob = -1
    best_cells = []
    for r, c in unknown:
        if prob[r][c] > best_prob:
            best_prob = prob[r][c]
            best_cells = [(r, c)]
        elif prob[r][c] == best_prob:
            best_cells.append((r, c))
    
    if best_cells:
        return random.choice(best_cells)
    
    # Fallback
    return random.choice(list(unknown))
