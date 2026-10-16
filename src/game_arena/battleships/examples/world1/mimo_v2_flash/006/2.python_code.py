
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    # 1. Identify known hits and misses
    hits = []
    misses = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.append((r, c))
            elif board[r][c] == -1:
                misses.add((r, c))
    
    # 2. Identify ships that are currently "active" (not sunk)
    # We infer sunk ships by looking for 5 hits in a line or clusters of hits that are fully surrounded by misses/bounds
    # However, a simpler logic is: if we have hits, we have an active ship unless we know it's sunk.
    # Since we don't have explicit sunk info, we assume hits are active unless a complex deduction says otherwise.
    # For this implementation, we will treat any cluster of hits as a target.
    
    # Group hits into clusters (connected components)
    visited = set()
    clusters = []
    for r, c in hits:
        if (r, c) not in visited:
            cluster = [(r, c)]
            queue = [(r, c)]
            visited.add((r, c))
            while queue:
                curr_r, curr_c = queue.pop(0)
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = curr_r + dr, curr_c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and (nr, nc) not in visited and board[nr][nc] == 1:
                        visited.add((nr, nc))
                        cluster.append((nr, nc))
                        queue.append((nr, nc))
            clusters.append(cluster)

    # 3. Target Logic (if we have active clusters)
    target_moves = []
    
    for cluster in clusters:
        # Determine orientation
        rs = [p[0] for p in cluster]
        cs = [p[1] for p in cluster]
        
        # Sort cluster to find ends easily
        if len(set(rs)) == 1: # Horizontal
            cluster.sort(key=lambda x: x[1])
            start, end = cluster[0], cluster[-1]
            # Check left
            if start[1] > 0:
                target_moves.append((start[0], start[1] - 1))
            # Check right
            if end[1] < 9:
                target_moves.append((end[0], end[1] + 1))
                
        elif len(set(cs)) == 1: # Vertical
            cluster.sort(key=lambda x: x[0])
            start, end = cluster[0], cluster[-1]
            # Check up
            if start[0] > 0:
                target_moves.append((start[0] - 1, start[1]))
            # Check down
            if end[0] < 9:
                target_moves.append((end[0] + 1, end[1]))
        
        else: # Scattered hits (L-shape or separate)
            # Check neighbors of all hits
            for r, c in cluster:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    target_moves.append((r + dr, c + dc))

    # Filter target moves
    valid_targets = []
    for r, c in target_moves:
        if 0 <= r < 10 and 0 <= c < 10 and board[r][c] == 0:
            valid_targets.append((r, c))
            
    if valid_targets:
        # Prefer targets that reduce entropy or are central to the cluster
        # For simplicity, pick random valid target (or the first one)
        return random.choice(valid_targets)

    # 4. Hunt Logic (if no targets)
    # Probability calculation with Parity optimization
    # Remaining ships: 5, 4, 3, 3, 2. 
    # Parity constraint: Since 2 is the smallest, we can use a checkerboard pattern.
    # (r + c) % 2 == 0 covers all possible placements because any ship of length > 1 covers both parities,
    # so hitting only one parity guarantees a hit on every ship.
    
    weights = [[0] * 10 for _ in range(10)]
    
    for r in range(10):
        for c in range(10):
            if board[r][c] != 0:
                continue
            
            # Checkerboard parity check
            if (r + c) % 2 != 0:
                continue 
                
            # Weights based on remaining ships (simple heuristic)
            # Higher weight for center, lower for edges.
            # Center bias: 4.5 is center.
            dist_from_center = abs(r - 4.5) + abs(c - 4.5)
            weight = 10 - dist_from_center
            
            # Add to weights
            weights[r][c] = weight

    # Find max weight
    max_w = -1
    best_moves = []
    
    for r in range(10):
        for c in range(10):
            if weights[r][c] > max_w:
                max_w = weights[r][c]
                best_moves = [(r, c)]
            elif weights[r][c] == max_w:
                best_moves.append((r, c))
    
    if best_moves:
        return random.choice(best_moves)
    
    # Fallback if everything else fails (should not happen on empty board)
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
                
    # Should never reach here
    return (0, 0)
