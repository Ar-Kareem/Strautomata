
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # Categorize cells
    hits = set()
    unknown = set()
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.add((r, c))
            elif board[r][c] == 0:
                unknown.add((r, c))
    
    if not unknown:
        return (0, 0)  # Shouldn't happen
    
    # Target mode: if we have hits, try to sink ships
    if hits:
        # Find connected components of hits and determine best targets
        targets_with_priority = []
        
        for r, c in hits:
            # Check for line patterns and extend them
            for dr, dc in [(0, 1), (1, 0)]:  # horizontal and vertical
                # Count hits in positive direction
                pos_hits = 0
                nr, nc = r + dr, c + dc
                while (nr, nc) in hits:
                    pos_hits += 1
                    nr, nc = nr + dr, nc + dc
                pos_unknown = (nr, nc) in unknown
                
                # Count hits in negative direction
                neg_hits = 0
                nr, nc = r - dr, c - dc
                while (nr, nc) in hits:
                    neg_hits += 1
                    nr, nc = nr - dr, nc - dc
                neg_unknown = (nr, nc) in unknown
                
                line_length = 1 + pos_hits + neg_hits
                
                # If we have a line of 2+ hits, strongly prefer extending it
                if line_length >= 2:
                    if pos_unknown:
                        ext_r, ext_c = r + dr * (pos_hits + 1), c + dc * (pos_hits + 1)
                        targets_with_priority.append(((ext_r, ext_c), 100 + line_length))
                    if neg_unknown:
                        ext_r, ext_c = r - dr * (neg_hits + 1), c - dc * (neg_hits + 1)
                        targets_with_priority.append(((ext_r, ext_c), 100 + line_length))
            
            # Also consider single-hit adjacents
            for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in unknown:
                    targets_with_priority.append(((nr, nc), 1))
        
        if targets_with_priority:
            # Pick highest priority target
            targets_with_priority.sort(key=lambda x: x[1], reverse=True)
            best_priority = targets_with_priority[0][1]
            best_targets = list(set(t[0] for t in targets_with_priority if t[1] == best_priority))
            return random.choice(best_targets)
    
    # Hunt mode: calculate probability density
    ship_lengths = [5, 4, 3, 3, 2]
    # Estimate remaining ships (rough heuristic based on total hits)
    total_ship_cells = sum(ship_lengths)  # 17
    remaining_cells = total_ship_cells - len(hits)
    
    # For simplicity, assume all ships might still be there
    # Calculate density
    density = {}
    for cell in unknown:
        density[cell] = 0
    
    for length in ship_lengths:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                cells = [(r, c + i) for i in range(length)]
                # Check if placement is valid (all cells unknown or hit)
                valid = all(cell in unknown or cell in hits for cell in cells)
                if valid:
                    for cell in cells:
                        if cell in unknown:
                            density[cell] += 1
        
        # Vertical placements
        for r in range(10 - length + 1):
            for c in range(10):
                cells = [(r + i, c) for i in range(length)]
                valid = all(cell in unknown or cell in hits for cell in cells)
                if valid:
                    for cell in cells:
                        if cell in unknown:
                            density[cell] += 1
    
    if density:
        max_density = max(density.values())
        if max_density > 0:
            best_cells = [cell for cell, d in density.items() if d == max_density]
            # Prefer checkerboard pattern among best cells
            checkerboard_best = [cell for cell in best_cells if (cell[0] + cell[1]) % 2 == 0]
            if checkerboard_best:
                return random.choice(checkerboard_best)
            return random.choice(best_cells)
    
    # Fallback: checkerboard pattern
    checkerboard = [(r, c) for r, c in unknown if (r + c) % 2 == 0]
    if checkerboard:
        return random.choice(checkerboard)
    
    return random.choice(list(unknown))
