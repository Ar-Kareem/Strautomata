
def policy(board: list[list[int]]) -> tuple[int, int]:
    import numpy as np
    
    b = np.array(board)
    ships = [5, 4, 3, 3, 2]
    
    hits = set(zip(*np.where(b == 1)))
    unknown = set(zip(*np.where(b == 0)))
    
    if not unknown:
        # Shouldn't happen, but fallback
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    return (r, c)
    
    # Find connected components of hits to identify potential unsunk ships
    def get_neighbors(r, c):
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 10 and 0 <= nc < 10:
                yield nr, nc
    
    # Find hit cells that have unknown neighbors (not fully explored)
    active_hits = []
    for hr, hc in hits:
        for nr, nc in get_neighbors(hr, hc):
            if (nr, nc) in unknown:
                active_hits.append((hr, hc))
                break
    
    prob = np.zeros((10, 10))
    
    # If we have active hits, prioritize continuing those
    if active_hits:
        for hr, hc in active_hits:
            # Check if this hit is part of a line
            # Horizontal line
            h_line = [(hr, hc)]
            for dc in [-1, 1]:
                nc = hc + dc
                while 0 <= nc < 10 and (hr, nc) in hits:
                    h_line.append((hr, nc))
                    nc += dc
            
            # Vertical line
            v_line = [(hr, hc)]
            for dr in [-1, 1]:
                nr = hr + dr
                while 0 <= nr < 10 and (nr, hc) in hits:
                    v_line.append((nr, hc))
                    nr += dr
            
            if len(h_line) > 1:
                # Continue horizontally
                min_c = min(c for _, c in h_line)
                max_c = max(c for _, c in h_line)
                if min_c > 0 and (hr, min_c - 1) in unknown:
                    prob[hr, min_c - 1] += 10000
                if max_c < 9 and (hr, max_c + 1) in unknown:
                    prob[hr, max_c + 1] += 10000
            elif len(v_line) > 1:
                # Continue vertically
                min_r = min(r for r, _ in v_line)
                max_r = max(r for r, _ in v_line)
                if min_r > 0 and (min_r - 1, hc) in unknown:
                    prob[min_r - 1, hc] += 10000
                if max_r < 9 and (max_r + 1, hc) in unknown:
                    prob[max_r + 1, hc] += 10000
            else:
                # Single hit, try all directions
                for nr, nc in get_neighbors(hr, hc):
                    if (nr, nc) in unknown:
                        prob[nr, nc] += 5000
    
    # Calculate base probability from ship placements
    for ship_len in ships:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - ship_len + 1):
                valid = True
                has_hit = False
                for i in range(ship_len):
                    if b[r, c + i] == -1:
                        valid = False
                        break
                    if b[r, c + i] == 1:
                        has_hit = True
                if valid:
                    weight = 10 if has_hit else 1
                    for i in range(ship_len):
                        if (r, c + i) in unknown:
                            prob[r, c + i] += weight
        
        # Vertical placements
        for r in range(10 - ship_len + 1):
            for c in range(10):
                valid = True
                has_hit = False
                for i in range(ship_len):
                    if b[r + i, c] == -1:
                        valid = False
                        break
                    if b[r + i, c] == 1:
                        has_hit = True
                if valid:
                    weight = 10 if has_hit else 1
                    for i in range(ship_len):
                        if (r + i, c) in unknown:
                            prob[r + i, c] += weight
    
    # Mask out already-fired cells
    prob[b != 0] = -1
    
    # Find best cell
    best_idx = np.argmax(prob)
    best_r, best_c = divmod(best_idx, 10)
    
    return (int(best_r), int(best_c))
