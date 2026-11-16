
import numpy as np
from collections import Counter

def policy(board: list[list[int]]) -> tuple[int, int]:
    grid = np.array(board, dtype=int)
    rows, cols = grid.shape
    ships = [5, 4, 3, 3, 2]

    # --- Helper Functions ---
    def get_neighbors(r, c):
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                yield nr, nc

    # --- 1. Analyze Board State ---
    visited = np.zeros_like(grid, dtype=bool)
    sunk_lengths = []
    active_components = [] # List of lists of (r, c)

    for r in range(rows):
        for c in range(cols):
            if grid[r, c] == 1 and not visited[r, c]:
                # Find connected component
                component = []
                stack = [(r, c)]
                visited[r, c] = True
                while stack:
                    curr_r, curr_c = stack.pop()
                    component.append((curr_r, curr_c))
                    for nr, nc in get_neighbors(curr_r, curr_c):
                        if grid[nr, nc] == 1 and not visited[nr, nc]:
                            visited[nr, nc] = True
                            stack.append((nr, nc))
                
                # Check if sunk (no adjacent 0s)
                is_sunk = True
                for cr, cc in component:
                    for nr, nc in get_neighbors(cr, cc):
                        if grid[nr, nc] == 0:
                            is_sunk = False
                            break
                    if not is_sunk:
                        break
                
                if is_sunk:
                    sunk_lengths.append(len(component))
                else:
                    active_components.append(component)

    # --- 2. Determine Remaining Ships ---
    remaining_ships = []
    counts = Counter(ships)
    for length in sunk_lengths:
        if counts[length] > 0:
            counts[length] -= 1
    for length, count in counts.items():
        remaining_ships.extend([length] * count)

    # --- 3. Target Mode ---
    def calculate_score(component, target_cell):
        tr, tc = target_cell
        r_vals = [x[0] for x in component] + [tr]
        c_vals = [x[1] for x in component] + [tc]
        
        is_horizontal = (len(set(r_vals)) == 1)
        is_vertical = (len(set(c_vals)) == 1)
        
        if not is_horizontal and not is_vertical:
            return 0
            
        score = 0
        min_r, max_r = min(r_vals), max(r_vals)
        min_c, max_c = min(c_vals), max(c_vals)
        segment_len = (max_c - min_c + 1) if is_horizontal else (max_r - min_r + 1)
        
        for L in remaining_ships:
            if L < segment_len: continue
            
            if is_horizontal:
                row = r_vals[0]
                c_min = max_c - L + 1
                c_max = min_c
                for c_start in range(c_min, c_max + 1):
                    c_end = c_start + L
                    if c_start < 0 or c_end > cols: continue
                    if np.any(grid[row, c_start:c_end] == -1): continue
                    if c_start <= tc < c_end:
                        score += 1
            elif is_vertical:
                col = c_vals[0]
                r_min = max_r - L + 1
                r_max = min_r
                for r_start in range(r_min, r_max + 1):
                    r_end = r_start + L
                    if r_start < 0 or r_end > rows: continue
                    if np.any(grid[r_start:r_end, col] == -1): continue
                    if r_start <= tr < r_end:
                        score += 1
        return score

    if active_components:
        best_move = None
        max_score = -1
        
        for component in active_components:
            candidates = set()
            
            if len(component) == 1:
                r, c = component[0]
                for nr, nc in get_neighbors(r, c):
                    if grid[nr, nc] == 0:
                        candidates.add((nr, nc))
            else:
                r1, c1 = component[0]
                r2, c2 = component[1]
                dr = 0 if r1 == r2 else (1 if r2 > r1 else -1)
                dc = 0 if c1 == c2 else (1 if c2 > c1 else -1)
                
                if dr != 0: # Vertical
                    sorted_comp = sorted(component, key=lambda x: x[0])
                else: # Horizontal
                    sorted_comp = sorted(component, key=lambda x: x[1])
                
                tip1 = sorted_comp[0]
                tip2 = sorted_comp[-1]
                
                ext1 = (tip1[0] - dr, tip1[1] - dc)
                if 0 <= ext1[0] < rows and 0 <= ext1[1] < cols and grid[ext1] == 0:
                    candidates.add(ext1)
                
                ext2 = (tip2[0] + dr, tip2[1] + dc)
                if 0 <= ext2[0] < rows and 0 <= ext2[1] < cols and grid[ext2] == 0:
                    candidates.add(ext2)

            for cand in candidates:
                s = calculate_score(component, cand)
                if s > max_score:
                    max_score = s
                    best_move = cand
        
        if best_move:
            return best_move

    # --- 4. Hunt Mode ---
    prob = np.zeros_like(grid, dtype=float)
    
    for L in remaining_ships:
        # Horizontal
        for r in range(rows):
            for c in range(cols - L + 1):
                if np.any(grid[r, c:c+L] == -1):
                    continue
                for k in range(L):
                    if grid[r, c+k] == 0:
                        prob[r, c+k] += 1
        # Vertical
        for r in range(rows - L + 1):
            for c in range(cols):
                if np.any(grid[r:r+L, c] == -1):
                    continue
                for k in range(L):
                    if grid[r+k, c] == 0:
                        prob[r+k, c] += 1
    
    prob[grid != 0] = -1 
    max_val = np.max(prob)
    
    if max_val <= 0:
        for r in range(rows):
            for c in range(cols):
                if grid[r,c] == 0: return (r,c)
        return (0,0)

    indices = np.where(prob == max_val)
    # Tie-breaker: Checkerboard Parity
    best_r, best_c = -1, -1
    for i in range(len(indices[0])):
        r, c = indices[0][i], indices[1][i]
        if (r + c) % 2 == 0:
            best_r, best_c = r, c
            break
    
    if best_r != -1:
        return (int(best_r), int(best_c))
    else:
        return (int(indices[0][0]), int(indices[1][0]))
