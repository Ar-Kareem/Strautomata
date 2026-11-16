
import numpy as np
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    b = np.array(board)
    
    # Find all hit positions and cluster them (4-directional adjacency)
    hits = [(i, j) for i in range(10) for j in range(10) if b[i, j] == 1]
    visited = set()
    clusters = []
    for h in hits:
        if h not in visited:
            cluster = []
            stack = [h]
            while stack:
                curr = stack.pop()
                if curr not in visited and b[curr[0], curr[1]] == 1:
                    visited.add(curr)
                    cluster.append(curr)
                    for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        ni, nj = curr[0] + di, curr[1] + dj
                        if 0 <= ni < 10 and 0 <= nj < 10 and (ni, nj) not in visited and b[ni, nj] == 1:
                            stack.append((ni, nj))
            clusters.append(cluster)
    
    # Determine target cells from unsunk clusters
    target_cells = set()
    for cluster in clusters:
        if not cluster:
            continue
        # Determine if horizontal or vertical
        rows = {r for r, c in cluster}
        cols = {c for r, c in cluster}
        if len(rows) == 1:  # Horizontal
            row = list(rows)[0]
            c_min = min(c for r, c in cluster)
            c_max = max(c for r, c in cluster)
            is_sunk = True
            if c_min - 1 >= 0 and b[row, c_min - 1] == 0:
                is_sunk = False
                target_cells.add((row, c_min - 1))
            if c_max + 1 < 10 and b[row, c_max + 1] == 0:
                is_sunk = False
                target_cells.add((row, c_max + 1))
        elif len(cols) == 1:  # Vertical
            col = list(cols)[0]
            r_min = min(r for r, c in cluster)
            r_max = max(r for r, c in cluster)
            is_sunk = True
            if r_min - 1 >= 0 and b[r_min - 1, col] == 0:
                is_sunk = False
                target_cells.add((r_min - 1, col))
            if r_max + 1 < 10 and b[r_max + 1, col] == 0:
                is_sunk = False
                target_cells.add((r_max + 1, col))
        # Note: Ignore mixed clusters as they shouldn't occur in straight-line ships
    
    # Choose action
    if target_cells:
        candidates = list(target_cells)
        return random.choice(candidates)
    else:
        # Hunt mode: Prefer (i+j) % 2 == 0
        candidates = [(i, j) for i in range(10) for j in range(10) if b[i, j] == 0 and (i + j) % 2 == 0]
        if not candidates:
            candidates = [(i, j) for i in range(10) for j in range(10) if b[i, j] == 0]
        return random.choice(candidates)
