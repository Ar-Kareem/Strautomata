
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    b = np.array(board)
    all_ship_lengths = [5, 4, 3, 3, 2]
    
    # Find connected components of hits
    visited = np.zeros((10, 10), dtype=bool)
    hit_groups = []
    
    for r in range(10):
        for c in range(10):
            if b[r][c] == 1 and not visited[r][c]:
                # BFS to find connected component
                group = []
                queue = deque([(r, c)])
                visited[r][c] = True
                while queue:
                    cr, cc = queue.popleft()
                    group.append((cr, cc))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < 10 and 0 <= nc < 10 and not visited[nr][nc] and b[nr][nc] == 1:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                hit_groups.append(group)
    
    # Determine which groups are sunk (fully surrounded by miss/edge)
    remaining_lengths = list(all_ship_lengths)
    for group in hit_groups:
        is_sunk = True
        for r, c in group:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and b[nr][nc] == 0:
                    is_sunk = False
                    break
            if not is_sunk:
                break
        if is_sunk:
            gl = len(group)
            if gl in remaining_lengths:
                remaining_lengths.remove(gl)
    
    if not remaining_lengths:
        remaining_lengths = [2]
    
    # Calculate probability density
    prob = np.zeros((10, 10), dtype=float)
    
    for length in remaining_lengths:
        for r in range(10):
            for c in range(10):
                # Horizontal
                if c + length <= 10:
                    cells = [(r, c+i) for i in range(length)]
                    if all(b[cr][cc] in (0, 1) for cr, cc in cells):
                        hits_in = sum(1 for cr, cc in cells if b[cr][cc] == 1)
                        weight = 1.0 + hits_in * 100.0
                        for cr, cc in cells:
                            if b[cr][cc] == 0:
                                prob[cr][cc] += weight
                # Vertical
                if r + length <= 10:
                    cells = [(r+i, c) for i in range(length)]
                    if all(b[cr][cc] in (0, 1) for cr, cc in cells):
                        hits_in = sum(1 for cr, cc in cells if b[cr][cc] == 1)
                        weight = 1.0 + hits_in * 100.0
                        for cr, cc in cells:
                            if b[cr][cc] == 0:
                                prob[cr][cc] += weight
    
    # Mask already-fired cells
    for r in range(10):
        for c in range(10):
            if b[r][c] != 0:
                prob[r][c] = -1
    
    # Parity bonus in hunt mode (no active hits)
    has_active_hits = any(not all(
        b[r+dr][c+dc] != 0 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)] if 0 <= r+dr < 10 and 0 <= c+dc < 10
    ) for group in hit_groups for r, c in group) if hit_groups else False
    
    if not has_active_hits:
        for r in range(10):
            for c in range(10):
                if b[r][c] == 0 and (r + c) % 2 == 0:
                    prob[r][c] *= 1.05
    
    best = np.unravel_index(np.argmax(prob), prob.shape)
    return (int(best[0]), int(best[1]))
