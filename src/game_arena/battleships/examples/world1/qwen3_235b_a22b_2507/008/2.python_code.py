
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board)
    unknown = (board == 0)
    if not np.any(unknown):
        # Should not happen, but fallback
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    return (i, j)
    
    # First, collect all hit cells
    hits = np.where(board == 1)
    hit_cells = list(zip(hits[0], hits[1]))
    
    # If we have hits, check if we can extend in any direction
    if len(hit_cells) > 0:
        # Try to find a continuation from existing hits
        directions = [(0,1), (1,0), (0,-1), (-1,0)]
        for r, c in hit_cells:
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    return (nr, nc)
    
    # Otherwise: use ship fitting heuristic
    # All ship lengths (two of length 3)
    ships = [5, 4, 3, 3, 2]
    count = np.zeros((10, 10), dtype=int)
    
    for r in range(10):
        for c in range(10):
            if board[r][c] != 0:
                continue
            # For each cell, count how many ships can fit covering it
            for ship_len in ships:
                # Horizontal placements
                for offset in range(ship_len):
                    sr = r
                    sc = c - offset
                    valid = True
                    for k in range(ship_len):
                        cc = sc + k
                        if not (0 <= cc < 10) or board[sr][cc] == -1:
                            valid = False
                            break
                    if valid:
                        count[r][c] += 1
                # Vertical placements
                for offset in range(ship_len):
                    sr = r - offset
                    sc = c
                    valid = True
                    for k in range(ship_len):
                        cr = sr + k
                        if not (0 <= cr < 10) or board[cr][sc] == -1:
                            valid = False
                            break
                    if valid:
                        count[r][c] += 1
    
    # Avoid cells already fired
    count[board != 0] = 0
    
    # Find cell with maximum count
    max_val = np.max(count)
    candidates = np.where(count == max_val)
    candidates = list(zip(candidates[0], candidates[1]))
    
    # Optional: add small bias to center to break ties (center is generally better)
    if len(candidates) > 1:
        center_dist = [-(abs(r-4.5) + abs(c-4.5)) for r, c in candidates]
        best_idx = np.argmax(center_dist)
        return candidates[best_idx]
    
    return candidates[0]
