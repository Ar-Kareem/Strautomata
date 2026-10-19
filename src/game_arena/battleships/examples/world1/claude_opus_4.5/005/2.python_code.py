
def policy(board: list[list[int]]) -> tuple[int, int]:
    import random
    
    SHIP_LENGTHS = [5, 4, 3, 3, 2]
    
    # Find all hits
    hits = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hits.add((r, c))
    
    # Group hits into connected components
    def get_hit_clusters():
        visited = set()
        clusters = []
        for hit in hits:
            if hit in visited:
                continue
            cluster = []
            stack = [hit]
            while stack:
                curr = stack.pop()
                if curr in visited:
                    continue
                visited.add(curr)
                cluster.append(curr)
                r, c = curr
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in hits and (nr, nc) not in visited:
                        stack.append((nr, nc))
            clusters.append(cluster)
        return clusters
    
    # Target mode: prioritize extending hit clusters
    if hits:
        clusters = get_hit_clusters()
        targets = []
        
        for cluster in clusters:
            if len(cluster) == 1:
                r, c = cluster[0]
                for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        targets.append((nr, nc, 10))  # High priority
            else:
                # Determine orientation
                rows = [p[0] for p in cluster]
                cols = [p[1] for p in cluster]
                if len(set(rows)) == 1:  # Horizontal
                    r = rows[0]
                    min_c, max_c = min(cols), max(cols)
                    if min_c > 0 and board[r][min_c - 1] == 0:
                        targets.append((r, min_c - 1, 20))
                    if max_c < 9 and board[r][max_c + 1] == 0:
                        targets.append((r, max_c + 1, 20))
                elif len(set(cols)) == 1:  # Vertical
                    c = cols[0]
                    min_r, max_r = min(rows), max(rows)
                    if min_r > 0 and board[min_r - 1][c] == 0:
                        targets.append((min_r - 1, c, 20))
                    if max_r < 9 and board[max_r + 1][c] == 0:
                        targets.append((max_r + 1, c, 20))
                else:
                    # L-shaped cluster (shouldn't happen but handle it)
                    for r, c in cluster:
                        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                                targets.append((nr, nc, 5))
        
        if targets:
            targets.sort(key=lambda x: -x[2])
            return (targets[0][0], targets[0][1])
    
    # Hunt mode: probability density
    prob = [[0.0] * 10 for _ in range(10)]
    
    for length in SHIP_LENGTHS:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                valid = True
                for dc in range(length):
                    if board[r][c + dc] != 0:
                        valid = False
                        break
                if valid:
                    for dc in range(length):
                        prob[r][c + dc] += 1
        
        # Vertical placements
        for r in range(10 - length + 1):
            for c in range(10):
                valid = True
                for dr in range(length):
                    if board[r + dr][c] != 0:
                        valid = False
                        break
                if valid:
                    for dr in range(length):
                        prob[r + dr][c] += 1
    
    # Find cell with highest probability
    best_prob = -1
    best_cells = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if prob[r][c] > best_prob:
                    best_prob = prob[r][c]
                    best_cells = [(r, c)]
                elif prob[r][c] == best_prob:
                    best_cells.append((r, c))
    
    if best_cells:
        return random.choice(best_cells)
    
    # Fallback: any unknown cell
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)
