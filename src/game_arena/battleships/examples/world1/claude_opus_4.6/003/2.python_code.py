
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = [row[:] for row in board]  # copy
    N = 10
    ship_lengths = [5, 4, 3, 3, 2]
    
    # Find connected components of hits
    visited = [[False]*N for _ in range(N)]
    hit_components = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not visited[r][c]:
                comp = []
                queue = deque([(r, c)])
                visited[r][c] = True
                while queue:
                    cr, cc = queue.popleft()
                    comp.append((cr, cc))
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < N and 0 <= nc < N and not visited[nr][nc] and board[nr][nc] == 1:
                            visited[nr][nc] = True
                            queue.append((nr, nc))
                hit_components.append(comp)
    
    # Determine which components are "sunk" (all neighbors are non-zero or edge)
    def is_sunk(comp):
        for r, c in comp:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    return False
        return True
    
    sunk_lengths = []
    unsunk_hits = []
    for comp in hit_components:
        if is_sunk(comp):
            sunk_lengths.append(len(comp))
        else:
            unsunk_hits.extend(comp)
    
    # Match sunk components to ship lengths greedily
    remaining_ships = list(ship_lengths)
    sunk_lengths_sorted = sorted(sunk_lengths, reverse=True)
    for sl in sunk_lengths_sorted:
        if sl in remaining_ships:
            remaining_ships.remove(sl)
    
    # Target mode: cells adjacent to unsunk hits
    target_cells = set()
    for r, c in unsunk_hits:
        # Determine orientation hint from component
        comp = [cp for cp in hit_components if (r,c) in cp][0] if hit_components else [(r,c)]
        if len(comp) >= 2:
            rows = [p[0] for p in comp]
            cols = [p[1] for p in comp]
            if len(set(rows)) == 1:  # horizontal
                dirs = [(0,-1),(0,1)]
            elif len(set(cols)) == 1:  # vertical
                dirs = [(-1,0),(1,0)]
            else:
                dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        else:
            dirs = [(-1,0),(1,0),(0,-1),(0,1)]
        for dr, dc in dirs:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                target_cells.add((nr, nc))
    
    # Probability density map
    density = np.zeros((N, N), dtype=float)
    
    for length in remaining_ships:
        for r in range(N):
            for c in range(N - length + 1):
                cells = [(r, c+i) for i in range(length)]
                if all(board[cr][cc] in (0, 1) for cr, cc in cells):
                    has_unsunk = any(board[cr][cc] == 1 and (cr,cc) in unsunk_hits for cr, cc in cells)
                    hits_only = all(board[cr][cc] == 1 for cr, cc in cells if board[cr][cc] == 1)
                    weight = 10.0 if has_unsunk else 1.0
                    for cr, cc in cells:
                        if board[cr][cc] == 0:
                            density[cr][cc] += weight
        for r in range(N - length + 1):
            for c in range(N):
                cells = [(r+i, c) for i in range(length)]
                if all(board[cr][cc] in (0, 1) for cr, cc in cells):
                    has_unsunk = any(board[cr][cc] == 1 and (cr,cc) in unsunk_hits for cr, cc in cells)
                    weight = 10.0 if has_unsunk else 1.0
                    for cr, cc in cells:
                        if board[cr][cc] == 0:
                            density[cr][cc] += weight
    
    # If we have target cells, heavily prefer them
    if target_cells:
        best_val = -1
        best_cell = None
        for r, c in target_cells:
            val = density[r][c]
            # Tie-break: center preference
            center_dist = abs(r - 4.5) + abs(c - 4.5)
            score = val * 1000 - center_dist
            if score > best_val or best_cell is None:
                best_val = score
                best_cell = (r, c)
        if best_cell:
            return best_cell
    
    # Hunt mode: pick highest density cell
    best_val = -1
    best_cell = None
    min_ship = min(remaining_ships) if remaining_ships else 2
    
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                val = density[r][c]
                # Parity bonus
                parity_bonus = 1.0 if (r + c) % min_ship == 0 else 0.0
                center_dist = abs(r - 4.5) + abs(c - 4.5)
                score = val + parity_bonus * 0.1 - center_dist * 0.001
                if score > best_val or best_cell is None:
                    best_val = score
                    best_cell = (r, c)
    
    if best_cell:
        return best_cell
    
    # Fallback: any unknown cell
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    
    return (0, 0)
