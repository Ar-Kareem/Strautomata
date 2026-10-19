
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10
    b = np.array(board)
    
    # Find connected components of hits
    visited = np.zeros((N, N), dtype=bool)
    hit_groups = []
    
    for r in range(N):
        for c in range(N):
            if b[r][c] == 1 and not visited[r][c]:
                # BFS
                group = []
                queue = deque([(r, c)])
                visited[r][c] = True
                while queue:
                    cr, cc = queue.popleft()
                    group.append((cr, cc))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < N and 0 <= nc < N and not visited[nr][nc] and b[nr][nc] == 1:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                hit_groups.append(group)
    
    # Determine if a hit group is "sunk" - no adjacent unknown cells
    def is_sunk(group):
        for r, c in group:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                    return False
        return True
    
    ship_lengths = [5, 4, 3, 3, 2]
    remaining_ships = list(ship_lengths)
    
    sunk_groups = []
    unsunk_groups = []
    for g in hit_groups:
        if is_sunk(g):
            sunk_groups.append(g)
        else:
            unsunk_groups.append(g)
    
    # Remove sunk ship lengths (greedy match largest first)
    sunk_sizes = sorted([len(g) for g in sunk_groups], reverse=True)
    for s in sunk_sizes:
        if s in remaining_ships:
            remaining_ships.remove(s)
    
    # Target mode: prioritize cells adjacent to unsunk hits
    if unsunk_groups:
        target_scores = np.full((N, N), -1.0)
        for g in unsunk_groups:
            cells = set(g)
            # Determine direction if linear
            if len(g) >= 2:
                rows = [r for r, c in g]
                cols = [c for r, c in g]
                if len(set(rows)) == 1:  # horizontal
                    directions = [(0, -1), (0, 1)]
                elif len(set(cols)) == 1:  # vertical
                    directions = [(-1, 0), (1, 0)]
                else:
                    directions = [(-1,0),(1,0),(0,-1),(0,1)]
            else:
                directions = [(-1,0),(1,0),(0,-1),(0,1)]
            
            for r, c in g:
                for dr, dc in directions:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < N and 0 <= nc < N and b[nr][nc] == 0:
                        target_scores[nr][nc] = max(target_scores[nr][nc], len(g))
        
        if np.any(target_scores >= 0):
            best = np.argwhere(target_scores == target_scores.max())
            # Pick closest to center
            center = np.array([4.5, 4.5])
            dists = [np.sum((np.array([r,c]) - center)**2) for r, c in best]
            idx = np.argmin(dists)
            return int(best[idx][0]), int(best[idx][1])
    
    # Hunt mode: probability density
    prob = np.zeros((N, N), dtype=float)
    
    for length in remaining_ships:
        for r in range(N):
            for c in range(N - length + 1):
                cells = [(r, c+i) for i in range(length)]
                if all(b[cr][cc] in (0, 1) for cr, cc in cells):
                    for cr, cc in cells:
                        if b[cr][cc] == 0:
                            prob[cr][cc] += 1
        for r in range(N - length + 1):
            for c in range(N):
                cells = [(r+i, c) for i in range(length)]
                if all(b[cr][cc] in (0, 1) for cr, cc in cells):
                    for cr, cc in cells:
                        if b[cr][cc] == 0:
                            prob[cr][cc] += 1
    
    # Apply parity bias for smallest remaining ship
    if remaining_ships:
        min_ship = min(remaining_ships)
        for r in range(N):
            for c in range(N):
                if b[r][c] == 0:
                    if (r + c) % 2 == (min_ship % 2):
                        prob[r][c] *= 1.1
    
    # Mask non-zero cells
    mask = (b == 0)
    prob[~mask] = 0
    
    if prob.max() > 0:
        best = np.argwhere(prob == prob.max())
        center = np.array([4.5, 4.5])
        dists = [np.sum((np.array([r,c]) - center)**2) for r, c in best]
        idx = np.argmin(dists)
        return int(best[idx][0]), int(best[idx][1])
    
    # Fallback: random unknown cell
    unknowns = np.argwhere(b == 0)
    if len(unknowns) > 0:
        choice = unknowns[np.random.randint(len(unknowns))]
        return int(choice[0]), int(choice[1])
    
    return (0, 0)
