
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10
    dirs = [(1,0), (-1,0), (0,1), (0,-1)]
    
    # Collect all hit cells
    hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]
    
    # --- TARGET MODE ---
    if hits:
        visited = set()
        candidates = {}
        
        for hr, hc in hits:
            if (hr, hc) in visited:
                continue
            # BFS to get cluster
            stack = [(hr, hc)]
            cluster = []
            visited.add((hr, hc))
            while stack:
                r, c = stack.pop()
                cluster.append((r, c))
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 1 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            
            rows = {r for r, _ in cluster}
            cols = {c for _, c in cluster}
            orientation = None
            if len(cluster) >= 2:
                if len(rows) == 1:
                    orientation = 'h'
                elif len(cols) == 1:
                    orientation = 'v'
            
            # Generate candidates based on orientation
            if orientation == 'h':
                row = cluster[0][0]
                minc = min(c for _, c in cluster)
                maxc = max(c for _, c in cluster)
                for nc in [minc - 1, maxc + 1]:
                    if 0 <= nc < N and board[row][nc] == 0:
                        candidates[(row, nc)] = candidates.get((row, nc), 0) + 2
            elif orientation == 'v':
                col = cluster[0][1]
                minr = min(r for r, _ in cluster)
                maxr = max(r for r, _ in cluster)
                for nr in [minr - 1, maxr + 1]:
                    if 0 <= nr < N and board[nr][col] == 0:
                        candidates[(nr, col)] = candidates.get((nr, col), 0) + 2
            else:
                # Single hit: check all neighbors
                for r, c in cluster:
                    for dr, dc in dirs:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                            candidates[(nr, nc)] = candidates.get((nr, nc), 0) + 1
        
        if candidates:
            # Choose candidate with max score
            max_score = max(candidates.values())
            best = [cell for cell, sc in candidates.items() if sc == max_score]
            return random.choice(best)
    
    # --- HUNT MODE ---
    lengths = [5, 4, 3, 3, 2]
    prob = [[0 for _ in range(N)] for _ in range(N)]
    
    for L in lengths:
        # Horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                cells = [(r, c+i) for i in range(L)]
                if all(board[rr][cc] != -1 for rr, cc in cells):
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            prob[rr][cc] += 1
        # Vertical placements
        for r in range(N - L + 1):
            for c in range(N):
                cells = [(r+i, c) for i in range(L)]
                if all(board[rr][cc] != -1 for rr, cc in cells):
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            prob[rr][cc] += 1
    
    # Choose best probability cell
    best_score = -1
    best_cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                score = prob[r][c]
                # small parity bonus
                if (r + c) % 2 == 0:
                    score += 0.1
                if score > best_score:
                    best_score = score
                    best_cells = [(r, c)]
                elif score == best_score:
                    best_cells.append((r, c))
    
    if best_cells:
        return random.choice(best_cells)
    
    # Fallback (shouldn't happen): pick any unknown
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    
    # If no moves, default
    return (0, 0)
