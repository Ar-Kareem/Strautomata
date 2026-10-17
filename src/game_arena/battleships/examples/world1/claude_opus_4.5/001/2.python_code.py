
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # Find all cells by type
    unknown = set()
    hits = set()
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                unknown.add((r, c))
            elif board[r][c] == 1:
                hits.add((r, c))
    
    def adjacent(r, c):
        result = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                result.append((nr, nc))
        return result
    
    # Find "active" hits - hits with unknown neighbors (unsunk ships)
    active_hits = [h for h in hits if any(a in unknown for a in adjacent(*h))]
    
    if active_hits:
        # Target mode: try to sink the ship
        target_scores = {}
        
        for r, c in active_hits:
            # Find connected hits horizontally
            h_hits = [(r, c)]
            for dc in [-1, 1]:
                nc = c + dc
                while 0 <= nc < 10 and (r, nc) in hits:
                    h_hits.append((r, nc))
                    nc += dc
            
            # Find connected hits vertically
            v_hits = [(r, c)]
            for dr in [-1, 1]:
                nr = r + dr
                while 0 <= nr < 10 and (nr, c) in hits:
                    v_hits.append((nr, c))
                    nr += dr
            
            # If we have a horizontal line, extend it
            if len(h_hits) >= 2:
                min_c = min(cc for _, cc in h_hits)
                max_c = max(cc for _, cc in h_hits)
                if (r, min_c - 1) in unknown:
                    target_scores[(r, min_c - 1)] = target_scores.get((r, min_c - 1), 0) + 100 + len(h_hits) * 10
                if (r, max_c + 1) in unknown:
                    target_scores[(r, max_c + 1)] = target_scores.get((r, max_c + 1), 0) + 100 + len(h_hits) * 10
            
            # If we have a vertical line, extend it
            if len(v_hits) >= 2:
                min_r = min(rr for rr, _ in v_hits)
                max_r = max(rr for rr, _ in v_hits)
                if (min_r - 1, c) in unknown:
                    target_scores[(min_r - 1, c)] = target_scores.get((min_r - 1, c), 0) + 100 + len(v_hits) * 10
                if (max_r + 1, c) in unknown:
                    target_scores[(max_r + 1, c)] = target_scores.get((max_r + 1, c), 0) + 100 + len(v_hits) * 10
            
            # Single hit - try all adjacent
            if len(h_hits) == 1 and len(v_hits) == 1:
                for nr, nc in adjacent(r, c):
                    if (nr, nc) in unknown:
                        target_scores[(nr, nc)] = target_scores.get((nr, nc), 0) + 50
        
        if target_scores:
            best_score = max(target_scores.values())
            best_cells = [cell for cell, score in target_scores.items() if score == best_score]
            return random.choice(best_cells)
    
    # Hunt mode: use probability density
    ship_lengths = [5, 4, 3, 3, 2]
    cell_scores = {}
    
    for r, c in unknown:
        score = 0
        
        # Count ship placements that could include this cell
        for length in ship_lengths:
            # Horizontal placements
            for start_c in range(max(0, c - length + 1), min(10 - length + 1, c + 1)):
                valid = True
                for i in range(length):
                    cell = (r, start_c + i)
                    if cell not in unknown and cell not in hits:
                        valid = False
                        break
                if valid:
                    score += 1
            
            # Vertical placements
            for start_r in range(max(0, r - length + 1), min(10 - length + 1, r + 1)):
                valid = True
                for i in range(length):
                    cell = (start_r + i, c)
                    if cell not in unknown and cell not in hits:
                        valid = False
                        break
                if valid:
                    score += 1
        
        # Slight preference for center and checkerboard
        score += 0.1 * (5 - abs(r - 4.5)) * (5 - abs(c - 4.5))
        if (r + c) % 2 == 0:
            score += 0.5
        
        cell_scores[(r, c)] = score
    
    if cell_scores:
        best_score = max(cell_scores.values())
        best_cells = [cell for cell, score in cell_scores.items() if score >= best_score - 0.01]
        return random.choice(best_cells)
    
    # Fallback (shouldn't reach here)
    return list(unknown)[0] if unknown else (0, 0)
