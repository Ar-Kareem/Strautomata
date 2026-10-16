
import random

# Precompute all possible placements for each ship length
SHIPS = [5, 4, 3, 3, 2]
PLACEMENTS = {}
for L in set(SHIPS):
    placements = []
    # Horizontal
    for r in range(10):
        for c in range(10 - L + 1):
            placements.append([(r, c + i) for i in range(L)])
    # Vertical
    for r in range(10 - L + 1):
        for c in range(10):
            placements.append([(r + i, c) for i in range(L)])
    PLACEMENTS[L] = placements


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Locate hits and unknown cells
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
    unknown = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    
    if not unknown:
        return (0, 0)  # safety fallback

    # Build orthogonally connected hit clusters
    visited = set()
    clusters = []
    for hit in hits:
        if hit not in visited:
            cluster = []
            stack = [hit]
            visited.add(hit)
            while stack:
                r, c = stack.pop()
                cluster.append((r, c))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1 and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            clusters.append(cluster)
    
    # Determine remaining ships and target cells
    active_ships = [5, 4, 3, 3, 2]
    target_cells = set()
    
    for cluster in clusters:
        rows = set(r for r, c in cluster)
        cols = set(c for r, c in cluster)
        
        if len(cluster) == 1:
            # Single hit: orientation unknown, add all orthogonal unknowns
            r, c = cluster[0]
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    target_cells.add((nr, nc))
        elif len(rows) == 1:
            # Horizontal line
            r = rows.pop()
            sorted_cols = sorted(c for _, c in cluster)
            min_c, max_c = sorted_cols[0], sorted_cols[-1]
            left = (r, min_c - 1) if min_c - 1 >= 0 and board[r][min_c - 1] == 0 else None
            right = (r, max_c + 1) if max_c + 1 < 10 and board[r][max_c + 1] == 0 else None
            if left:
                target_cells.add(left)
            if right:
                target_cells.add(right)
            if not left and not right:
                # Ship completely bounded – mark as sunk
                L = len(cluster)
                if L in active_ships:
                    active_ships.remove(L)
        elif len(cols) == 1:
            # Vertical line
            c = cols.pop()
            sorted_rows = sorted(r for r, _ in cluster)
            min_r, max_r = sorted_rows[0], sorted_rows[-1]
            up = (min_r - 1, c) if min_r - 1 >= 0 and board[min_r - 1][c] == 0 else None
            down = (max_r + 1, c) if max_r + 1 < 10 and board[max_r + 1][c] == 0 else None
            if up:
                target_cells.add(up)
            if down:
                target_cells.add(down)
            if not up and not down:
                L = len(cluster)
                if L in active_ships:
                    active_ships.remove(L)
        else:
            # Non-straight cluster (touching ships) – add all orthogonal unknowns
            for r, c in cluster:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        target_cells.add((nr, nc))
    
    # Build heatmap using only the remaining ships
    heatmap = [[0] * 10 for _ in range(10)]
    for L in active_ships:
        for placement in PLACEMENTS[L]:
            valid = True
            for r, c in placement:
                if board[r][c] == -1:
                    valid = False
                    break
            if valid:
                for r, c in placement:
                    heatmap[r][c] += 1
    
    if target_cells:
        # Target mode: shoot the candidate with the highest heatmap score
        best_cell = max(target_cells, key=lambda x: heatmap[x[0]][x[1]])
        return best_cell
    else:
        # Hunt mode: highest heatmap among all unknowns; tie-break with parity
        max_val = -1
        best_cells = []
        for r, c in unknown:
            val = heatmap[r][c]
            if val > max_val:
                max_val = val
                best_cells = [(r, c)]
            elif val == max_val:
                best_cells.append((r, c))
        
        # Prefer cells with even parity (r + c) % 2 == 0
        even_cells = [cell for cell in best_cells if (cell[0] + cell[1]) % 2 == 0]
        if even_cells:
            return random.choice(even_cells)
        else:
            return random.choice(best_cells)
