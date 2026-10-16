
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    known_miss = (board == -1)
    known_hit = (board == 1)
    possible = (board == 0)  # unvisited
    ships = [5, 4, 3, 3, 2]
    
    # Step 1: If there are hits, expand from them
    if np.any(known_hit):
        # Get all hit positions
        hit_positions = np.where(known_hit)
        hits = list(zip(hit_positions[0], hit_positions[1]))
        
        # Directions: up, down, left, right
        dirs = [(-1,0), (1,0), (0,-1), (0,1)]
        for r, c in hits:
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and possible[nr, nc]:
                    return (nr, nc)
    
    # Step 2: Use ship-fitting probability heatmap
    heatmap = np.zeros((10, 10), dtype=int)
    for ship_len in ships:
        # Horizontal and vertical placements
        for r in range(10):
            for c in range(10):
                if not possible[r, c] and np.sum(known_hit) == 0:
                    continue  # skip if cell is known and we're not building full map
                # Horizontal
                if c + ship_len <= 10:
                    if np.all(possible[r, c:c+ship_len] | (board[r, c:c+ship_len] == 1)):
                        # Check no miss in segment
                        if np.any(board[r, c:c+ship_len] == -1):
                            continue
                        heatmap[r, c:c+ship_len] += 1
                # Vertical
                if r + ship_len <= 10:
                    if np.all(possible[r:r+ship_len, c] | (board[r:r+ship_len, c] == 1)):
                        if np.any(board[r:r+ship_len, c] == -1):
                            continue
                        heatmap[r:r+ship_len, c] += 1

    # Avoid already fired cells
    heatmap[~possible] = 0

    # If all heatmap is zero, fallback to checkerboard pattern
    if np.max(heatmap) == 0:
        # Use parity grid: focus on cells where (i+j) % 2 == 0 (even parity) first
        for r in range(10):
            for c in range(10):
                if possible[r, c] and (r + c) % 2 == 0:
                    return (r, c)
        # If all even done, pick any
        coords = np.where(possible)
        if len(coords[0]) > 0:
            return (coords[0][0], coords[1][0])

    # Find best cells by heatmap score
    max_val = np.max(heatmap)
    best = np.where(heatmap == max_val)
    best_coords = list(zip(best[0], best[1]))
    
    # Among best, prefer parity cells if not deep in game
    if np.sum(known_hit) == 0:
        for r, c in best_coords:
            if (r + c) % 2 == 0:
                return (r, c)
    
    # Return first best
    return best_coords[0]
