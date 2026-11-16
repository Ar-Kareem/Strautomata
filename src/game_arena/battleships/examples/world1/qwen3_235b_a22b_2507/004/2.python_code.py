
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Ship lengths: two of length 3
    lengths = [5, 4, 3, 3, 2]
    n = 10
    
    # Precompute the weight map: how many ship placements cover each cell
    weights = [[0] * n for _ in range(n)]
    for L in lengths:
        # Horizontal placements
        for r in range(n):
            for c in range(n - L + 1):
                for k in range(L):
                    weights[r][c + k] += 1
        # Vertical placements
        for c in range(n):
            for r in range(n - L + 1):
                for k in range(L):
                    weights[r + k][c] += 1
    
    # Find all hit cells (where we have a hit)
    hit_cells = []
    for i in range(n):
        for j in range(n):
            if board[i][j] == 1:
                hit_cells.append((i, j))
    
    # If there are any hits, try to exploit them
    if hit_cells:
        # Find unknown cells adjacent to any hit
        candidates = set()
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        for (i, j) in hit_cells:
            for di, dj in directions:
                ni, nj = i + di, j + dj
                if 0 <= ni < n and 0 <= nj < n and board[ni][nj] == 0:
                    candidates.add((ni, nj))
        
        # If we have adjacent unknowns, try to extend aligned hits first
        if candidates:
            # Group hits by row and by column
            rows = {}
            cols = {}
            for (i, j) in hit_cells:
                if i not in rows:
                    rows[i] = []
                if j not in cols:
                    cols[j] = []
                rows[i].append(j)
                cols[j].append(i)
            
            # Sort the lists
            for k in rows:
                rows[k].sort()
            for k in cols:
                cols[k].sort()
            
            # Check for horizontal lines (same row, consecutive columns)
            for r in rows:
                if len(rows[r]) >= 2:
                    sorted_js = rows[r]
                    # Check if they are consecutive
                    if all(sorted_js[i+1] - sorted_js[i] == 1 for i in range(len(sorted_js)-1)):
                        minj, maxj = sorted_js[0], sorted_js[-1]
                        # Try extending left
                        if minj > 0 and (r, minj-1) in candidates:
                            return (r, minj-1)
                        # Try extending right
                        if maxj < n-1 and (r, maxj+1) in candidates:
                            return (r, maxj+1)
            
            # Check for vertical lines (same column, consecutive rows)
            for c in cols:
                if len(cols[c]) >= 2:
                    sorted_is = cols[c]
                    if all(sorted_is[i+1] - sorted_is[i] == 1 for i in range(len(sorted_is)-1)):
                        mini, maxi = sorted_is[0], sorted_is[-1]
                        # Extend up
                        if mini > 0 and (mini-1, c) in candidates:
                            return (mini-1, c)
                        # Extend down
                        if maxi < n-1 and (maxi+1, c) in candidates:
                            return (maxi+1, c)
            
            # If no directional extension, pick the best candidate by weight
            best_cell = None
            best_weight = -1
            for cell in candidates:
                i, j = cell
                if weights[i][j] > best_weight:
                    best_weight = weights[i][j]
                    best_cell = cell
            if best_cell:
                return best_cell
    
    # If no hits or no candidates from hits, fall back to weighted choice over all unknowns
    best_cell = None
    best_weight = -1
    for i in range(n):
        for j in range(n):
            if board[i][j] == 0:  # unknown
                if weights[i][j] > best_weight:
                    best_weight = weights[i][j]
                    best_cell = (i, j)
    return best_cell
