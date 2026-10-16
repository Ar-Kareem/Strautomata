
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    
    # Find connected components of hits
    visited = np.zeros((10, 10), dtype=bool)
    hit_groups = []
    
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and not visited[r][c]:
                # BFS to find connected component
                group = []
                queue = deque([(r, c)])
                visited[r][c] = True
                while queue:
                    cr, cc = queue.popleft()
                    group.append((cr, cc))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < 10 and 0 <= nc < 10 and not visited[nr][nc] and board[nr][nc] == 1:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                hit_groups.append(group)
    
    # Determine if a group is sunk (no adjacent unknown cells)
    ship_lengths = [5, 4, 3, 3, 2]
    sunk_lengths = []
    unsunk_hits = []
    
    for group in hit_groups:
        has_adjacent_unknown = False
        for (gr, gc) in group:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = gr+dr, gc+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    has_adjacent_unknown = True
                    break
            if has_adjacent_unknown:
                break
        if not has_adjacent_unknown:
            sunk_lengths.append(len(group))
        else:
            unsunk_hits.extend(group)
    
    # Determine remaining ship lengths
    remaining = list(ship_lengths)
    for sl in sunk_lengths:
        if sl in remaining:
            remaining.remove(sl)
    
    if not remaining:
        remaining = [2]  # fallback
    
    # Build probability density map
    prob = np.zeros((10, 10), dtype=float)
    
    for length in remaining:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - length + 1):
                cells = [(r, c+i) for i in range(length)]
                if all(board[cr][cc] in (0, 1) for cr, cc in cells):
                    for cr, cc in cells:
                        if board[cr][cc] == 0:
                            prob[cr][cc] += 1
        # Vertical placements
        for r in range(10 - length + 1):
            for c in range(10):
                cells = [(r+i, c) for i in range(length)]
                if all(board[cr][cc] in (0, 1) for cr, cc in cells):
                    for cr, cc in cells:
                        if board[cr][cc] == 0:
                            prob[cr][cc] += 1
    
    # Boost cells adjacent to unsunk hits significantly
    for (hr, hc) in unsunk_hits:
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = hr+dr, hc+dc
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                prob[nr][nc] *= 20
    
    # Mask already-fired cells
    prob[board != 0] = -1
    
    # Find best cell
    if prob.max() <= 0:
        # Fallback: pick any unknown cell
        unknowns = list(zip(*np.where(board == 0)))
        if unknowns:
            idx = np.random.randint(len(unknowns))
            return (int(unknowns[idx][0]), int(unknowns[idx][1]))
    
    # Tie-break with center preference
    max_val = prob.max()
    candidates = list(zip(*np.where(prob == max_val)))
    
    # Prefer center
    center = 4.5
    best = min(candidates, key=lambda x: (x[0]-center)**2 + (x[1]-center)**2)
    return (int(best[0]), int(best[1]))
