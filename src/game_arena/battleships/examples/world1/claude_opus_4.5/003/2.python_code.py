
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Ship lengths in the game
    SHIPS = [5, 4, 3, 3, 2]
    
    # Classify cells
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
        return (0, 0)
    
    def neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                yield (nr, nc)
    
    # Find hits with unknown neighbors (unsunk ship parts)
    active_hits = [h for h in hits if any(n in unknown for n in neighbors(*h))]
    
    # TARGET MODE: If we have active hits, focus on sinking ships
    if active_hits:
        target_scores = {}
        
        for hit in active_hits:
            r, c = hit
            
            # Find connected hits in each direction
            # Horizontal line
            h_hits = [hit]
            for dc in [-1, 1]:
                nc = c + dc
                while 0 <= nc < 10 and (r, nc) in hits:
                    h_hits.append((r, nc))
                    nc += dc
            
            # Vertical line
            v_hits = [hit]
            for dr in [-1, 1]:
                nr = r + dr
                while 0 <= nr < 10 and (nr, c) in hits:
                    v_hits.append((nr, c))
                    nr += dr
            
            # If we have a horizontal line, prioritize extending it
            if len(h_hits) > 1:
                min_c = min(p[1] for p in h_hits)
                max_c = max(p[1] for p in h_hits)
                if (r, min_c - 1) in unknown:
                    target_scores[(r, min_c - 1)] = target_scores.get((r, min_c - 1), 0) + 100 + len(h_hits)
                if (r, max_c + 1) in unknown:
                    target_scores[(r, max_c + 1)] = target_scores.get((r, max_c + 1), 0) + 100 + len(h_hits)
            
            # If we have a vertical line, prioritize extending it
            if len(v_hits) > 1:
                min_r = min(p[0] for p in v_hits)
                max_r = max(p[0] for p in v_hits)
                if (min_r - 1, c) in unknown:
                    target_scores[(min_r - 1, c)] = target_scores.get((min_r - 1, c), 0) + 100 + len(v_hits)
                if (max_r + 1, c) in unknown:
                    target_scores[(max_r + 1, c)] = target_scores.get((max_r + 1, c), 0) + 100 + len(v_hits)
            
            # Single isolated hit - try all directions
            if len(h_hits) == 1 and len(v_hits) == 1:
                for n in neighbors(r, c):
                    if n in unknown:
                        target_scores[n] = target_scores.get(n, 0) + 10
        
        if target_scores:
            best_target = max(target_scores.keys(), key=lambda x: target_scores[x])
            return best_target
    
    # HUNT MODE: Calculate probability density for each cell
    prob = [[0.0] * 10 for _ in range(10)]
    
    for length in SHIPS:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                cells = [(r, c + i) for i in range(length)]
                # Valid if all cells are unknown (no misses, no existing hits for hunt)
                if all(cell in unknown for cell in cells):
                    for cell in cells:
                        prob[cell[0]][cell[1]] += 1
        
        # Vertical placements
        for r in range(10 - length + 1):
            for c in range(10):
                cells = [(r + i, c) for i in range(length)]
                if all(cell in unknown for cell in cells):
                    for cell in cells:
                        prob[cell[0]][cell[1]] += 1
    
    # Add small bonus for checkerboard pattern (parity optimization)
    for r in range(10):
        for c in range(10):
            if (r, c) in unknown:
                if (r + c) % 2 == 0:
                    prob[r][c] += 0.1
    
    # Find the cell with highest probability
    best_cell = None
    best_prob = -1
    
    for r in range(10):
        for c in range(10):
            if (r, c) in unknown and prob[r][c] > best_prob:
                best_prob = prob[r][c]
                best_cell = (r, c)
    
    if best_cell:
        return best_cell
    
    # Fallback: return any unknown cell
    return next(iter(unknown))
