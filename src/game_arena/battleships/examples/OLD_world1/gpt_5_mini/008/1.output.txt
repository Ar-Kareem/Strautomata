import numpy as np
from collections import deque

# Ship lengths for standard Battleship
SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10

def _find_hit_clusters(board):
    """Return list of clusters; each cluster is list of (r,c) tuples for cells == 1."""
    visited = np.zeros((N, N), dtype=bool)
    clusters = []
    for r in range(N):
        for c in range(N):
            if board[r, c] == 1 and not visited[r, c]:
                q = deque()
                q.append((r, c))
                comp = []
                visited[r, c] = True
                while q:
                    x, y = q.popleft()
                    comp.append((x, y))
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < N and 0 <= ny < N and not visited[nx, ny] and board[nx, ny] == 1:
                            visited[nx, ny] = True
                            q.append((nx, ny))
                clusters.append(comp)
    return clusters

def _adjacent_candidates_for_cluster(cluster, board):
    """Given a cluster of hits, return set of adjacent unknown cells prioritized for targeting.
       If cluster length >1, orientation is inferred and candidates are extensions at both ends.
       If single cell, all 4-adjacent unknown cells are candidates.
    """
    candidates = set()
    if len(cluster) == 0:
        return candidates
    if len(cluster) == 1:
        r,c = cluster[0]
        for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                candidates.add((nr, nc))
        return candidates

    # multiple cells: determine orientation
    rows = [p[0] for p in cluster]
    cols = [p[1] for p in cluster]
    if all(r == rows[0] for r in rows):
        # horizontal
        row = rows[0]
        minc = min(cols)
        maxc = max(cols)
        left = (row, minc-1)
        right = (row, maxc+1)
        for nr,nc in (left, right):
            if 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                candidates.add((nr, nc))
    elif all(c == cols[0] for c in cols):
        # vertical
        col = cols[0]
        minr = min(rows)
        maxr = max(rows)
        up = (minr-1, col)
        down = (maxr+1, col)
        for nr,nc in (up, down):
            if 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                candidates.add((nr, nc))
    else:
        # Rare non-linear cluster (shouldn't happen). Fall back to neighbors of all cells.
        for r,c in cluster:
            for dr,dc in ((1,0),(-1,0),(0,1),(0,-1)):
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and board[nr, nc] == 0:
                    candidates.add((nr, nc))
    return candidates

def _compute_heatmap(board):
    """Compute probability-like heatmap: count number of ways ships could occupy each unknown cell
       given only misses (cells -1) as constraints. This is the classic placement-summing approach.
    """
    heat = np.zeros((N, N), dtype=int)
    for length in SHIP_LENGTHS:
        # horizontal placements
        for r in range(N):
            for c in range(N - length + 1):
                segment = board[r, c:c+length]
                # placement invalid if any miss present in the segment
                if np.any(segment == -1):
                    continue
                # valid placement: increment unknown cells in segment
                for k in range(length):
                    if board[r, c+k] == 0:
                        heat[r, c+k] += 1
        # vertical placements
        for c in range(N):
            for r in range(N - length + 1):
                segment = board[r:r+length, c]
                if np.any(segment == -1):
                    continue
                for k in range(length):
                    if board[r+k, c] == 0:
                        heat[r+k, c] += 1
    return heat

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert to numpy array for convenience
    arr = np.array(board, dtype=int)
    # Sanity: ensure shape is NxN
    if arr.shape != (N, N):
        # fallback: return first unknown
        for i in range(arr.shape[0]):
            for j in range(arr.shape[1]):
                if arr[i,j] == 0:
                    return (int(i), int(j))
        return (0,0)

    heat = _compute_heatmap(arr)

    # If there are any hits, produce targeting candidates and choose the best among them by heat
    clusters = _find_hit_clusters(arr)
    hit_cells = np.argwhere(arr == 1)
    if hit_cells.size > 0:
        candidate_set = set()
        for cluster in clusters:
            candidate_set.update(_adjacent_candidates_for_cluster(cluster, arr))

        # If no adjacent candidates found (e.g., surrounded by misses), fall back to heatmap global pick
        if candidate_set:
            # pick candidate with highest heat; tie-breaker: smaller row then col
            best = None
            best_score = -1
            for (r,c) in candidate_set:
                score = int(heat[r,c])
                # Slightly boost candidates that align with longer unsunk ship possibility:
                # if adjacent to a hit, give small bonus proportional to cluster size
                # find cluster size it is adjacent to
                adj_bonus = 0
                for cl in clusters:
                    for (hr,hc) in cl:
                        if abs(hr-r) + abs(hc-c) == 1:
                            adj_bonus = max(adj_bonus, len(cl))
                score = score * 10 + adj_bonus  # multiply to prioritize heat primarily
                if score > best_score or (score == best_score and (r, c) < best):
                    best_score = score
                    best = (r, c)
            if best is not None:
                return (int(best[0]), int(best[1]))

    # No hits or couldn't target: choose highest-heat unknown cell.
    # If multiple maxima, prefer parity (checkerboard) to be efficient: prefer (r+c)%2==0
    max_heat = -1
    best_cells = []
    for r in range(N):
        for c in range(N):
            if arr[r, c] != 0:
                continue
            h = int(heat[r, c])
            if h > max_heat:
                max_heat = h
                best_cells = [(r, c)]
            elif h == max_heat:
                best_cells.append((r, c))

    if max_heat <= 0:
        # heatmap gave no info (e.g., many misses). Fall back to parity hunting or first unknown.
        # Prefer checkerboard pattern that suits largest remaining ship length
        # Choose parity based on largest remaining ship length to maximize coverage:
        remaining_lengths = SHIP_LENGTHS.copy()
        # We can't know which ships remain, but use max length
        parity = 0  # prefer even parity by default
        for (r,c) in [(i,j) for i in range(N) for j in range(N)]:
            if arr[r,c] == 0 and (r+c) % 2 == parity:
                return (int(r), int(c))
        # otherwise pick first unknown
        for r in range(N):
            for c in range(N):
                if arr[r,c] == 0:
                    return (int(r), int(c))
        # safety
        return (0,0)

    # From best_cells, prefer parity (even) and then smallest row,col
    best_cells.sort()
    for (r,c) in best_cells:
        if (r + c) % 2 == 0:
            return (int(r), int(c))
    # else return first best
    r,c = best_cells[0]
    return (int(r), int(c))