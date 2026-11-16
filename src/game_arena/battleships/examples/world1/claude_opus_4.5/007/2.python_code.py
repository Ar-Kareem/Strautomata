
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # Find all hits, misses, and unknowns
    hits = set()
    unknowns = set()
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.add((r, c))
            elif board[r][c] == 0:
                unknowns.add((r, c))
    
    if not unknowns:
        return (0, 0)  # Shouldn't happen
    
    # TARGET MODE: If we have hits, prioritize adjacent cells intelligently
    if hits:
        # Find connected components of hits and their orientations
        candidates = {}
        
        for r, c in hits:
            # Check if this hit has adjacent hits (to determine direction)
            has_horizontal = ((r, c-1) in hits or (r, c+1) in hits)
            has_vertical = ((r-1, c) in hits or (r+1, c) in hits)
            
            directions = []
            if has_horizontal:
                directions = [(0, 1), (0, -1)]
            elif has_vertical:
                directions = [(1, 0), (-1, 0)]
            else:
                directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (nr, nc) in unknowns:
                    # Weight by how many hits are in line
                    weight = 1
                    # Count consecutive hits in opposite direction
                    tr, tc = r - dr, c - dc
                    while (tr, tc) in hits:
                        weight += 1
                        tr -= dr
                        tc -= dc
                    candidates[(nr, nc)] = candidates.get((nr, nc), 0) + weight
        
        if candidates:
            # Return the candidate with highest weight
            best = max(candidates.keys(), key=lambda x: candidates[x])
            return best
    
    # HUNT MODE: Use probability density based on ship placements
    ships = [5, 4, 3, 3, 2]
    
    # Estimate which ships might be sunk based on hit clusters
    # Simple heuristic: count total hits and subtract likely sunk ships
    total_hits = len(hits)
    remaining_ships = ships.copy()
    
    # Try to identify sunk ships by finding isolated hit segments
    # (This is a simplification - we mark segments that could be complete ships)
    visited = set()
    segments = []
    
    for start in hits:
        if start in visited:
            continue
        # BFS to find connected hit component
        segment = []
        queue = [start]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            segment.append(curr)
            r, c = curr
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in hits and (nr, nc) not in visited:
                    queue.append((nr, nc))
        segments.append(segment)
    
    # Check if segments are "closed" (no adjacent unknowns) - likely sunk
    for seg in segments:
        is_closed = True
        for r, c in seg:
            for dr, dc in [(0,1), (0,-1), (1,0), (-1,0)]:
                if (r+dr, c+dc) in unknowns:
                    is_closed = False
                    break
            if not is_closed:
                break
        
        if is_closed and len(seg) in remaining_ships:
            remaining_ships.remove(len(seg))
    
    # Calculate probability density for each unknown cell
    density = {cell: 0 for cell in unknowns}
    
    for ship_len in remaining_ships:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - ship_len + 1):
                cells = [(r, c + i) for i in range(ship_len)]
                # Check if placement is valid (no misses, all unknown or hit)
                valid = all(board[cr][cc] != -1 for cr, cc in cells)
                if valid and any((cr, cc) in unknowns for cr, cc in cells):
                    for cr, cc in cells:
                        if (cr, cc) in unknowns:
                            density[(cr, cc)] += 1
        
        # Vertical placements
        for r in range(10 - ship_len + 1):
            for c in range(10):
                cells = [(r + i, c) for i in range(ship_len)]
                valid = all(board[cr][cc] != -1 for cr, cc in cells)
                if valid and any((cr, cc) in unknowns for cr, cc in cells):
                    for cr, cc in cells:
                        if (cr, cc) in unknowns:
                            density[(cr, cc)] += 1
    
    if density:
        # Add slight preference for center and checkerboard pattern
        for cell in density:
            r, c = cell
            # Checkerboard bonus
            if (r + c) % 2 == 0:
                density[cell] += 0.5
            # Center bonus
            center_dist = abs(r - 4.5) + abs(c - 4.5)
            density[cell] += (9 - center_dist) * 0.1
        
        max_density = max(density.values())
        best_cells = [cell for cell, d in density.items() if d == max_density]
        return random.choice(best_cells)
    
    # Fallback
    return random.choice(list(unknowns))
