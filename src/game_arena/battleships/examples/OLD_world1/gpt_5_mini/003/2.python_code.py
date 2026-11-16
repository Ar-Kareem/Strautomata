
import numpy as np
from collections import deque, Counter

# Battleship ship lengths
DEFAULT_SHIPS = [5, 4, 3, 3, 2]

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Given a 10x10 board with values:
      0 -> unknown
     -1 -> miss
      1 -> hit
    Return a (row, col) of an unshot cell to fire at next.
    Strategy: hybrid hunt/target using placement-based heatmap and focused target-mode when there are hits.
    """
    # Convert to numpy array for convenience
    b = np.array(board, dtype=int)
    n = b.shape[0]
    assert n == 10 and b.shape[1] == 10

    # Helper: find connected clusters of hits (orthogonally connected)
    def find_hit_clusters():
        visited = np.zeros_like(b, dtype=bool)
        clusters = []
        for r in range(n):
            for c in range(n):
                if b[r, c] == 1 and not visited[r, c]:
                    q = deque()
                    q.append((r, c))
                    visited[r, c] = True
                    comp = [(r, c)]
                    while q:
                        x, y = q.popleft()
                        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                            nx_, ny_ = x+dx, y+dy
                            if 0 <= nx_ < n and 0 <= ny_ < n and not visited[nx_, ny_] and b[nx_, ny_] == 1:
                                visited[nx_, ny_] = True
                                q.append((nx_, ny_))
                                comp.append((nx_, ny_))
                    clusters.append(comp)
        return clusters

    # Heuristic: determine which ships remain by detecting sunk clusters
    def infer_remaining_ships(clusters):
        ships = list(DEFAULT_SHIPS)
        # For each cluster, if it is aligned and both ends are blocked by either miss or board edge,
        # and its size matches an available ship length, consider it sunk and remove that length once.
        for comp in clusters:
            if len(comp) == 0:
                continue
            # Determine if aligned horizontally or vertically
            rows = [p[0] for p in comp]
            cols = [p[1] for p in comp]
            minr, maxr = min(rows), max(rows)
            minc, maxc = min(cols), max(cols)
            sunk = False
            if minr == maxr:
                # horizontal
                left = (minr, minc - 1)
                right = (minr, maxc + 1)
                left_blocked = not (0 <= left[0] < n and 0 <= left[1] < n) or b[left] == -1
                right_blocked = not (0 <= right[0] < n and 0 <= right[1] < n) or b[right] == -1
                if left_blocked and right_blocked:
                    length = len(comp)
                    # Remove one ship of this length if available
                    if length in ships:
                        ships.remove(length)
                        sunk = True
            elif minc == maxc:
                # vertical
                up = (minr - 1, minc)
                down = (maxr + 1, minc)
                up_blocked = not (0 <= up[0] < n and 0 <= up[1] < n) or b[up] == -1
                down_blocked = not (0 <= down[0] < n and 0 <= down[1] < n) or b[down] == -1
                if up_blocked and down_blocked:
                    length = len(comp)
                    if length in ships:
                        ships.remove(length)
                        sunk = True
            # single-cell cluster can't be confidently sunk unless both sides blocked and matches a ship length,
            # but ships min length is 2 so skip further logic.
            # continue
        return ships

    clusters = find_hit_clusters()
    ships_remaining = infer_remaining_ships(clusters)

    # Build heatmap: for each possible placement of each remaining ship,
    # if the placement doesn't overlap any misses and is consistent with hits (i.e., only covers hits or unknowns),
    # count each placement by incrementing counts on its cells.
    heat = np.zeros_like(b, dtype=float)

    # If we have any hits, we bias placements to include at least one hit (target focus)
    any_hits = np.any(b == 1)

    for L in ships_remaining:
        # Horizontal placements
        for r in range(n):
            for c in range(n - L + 1):
                cells = [(r, c + k) for k in range(L)]
                values = [b[x, y] for (x, y) in cells]
                if any(v == -1 for v in values):
                    continue
                if any_hits:
                    # prefer placements that include at least one hit
                    if not any(v == 1 for v in values):
                        continue
                # Additionally, ensure we don't place a ship that would overlap a hit that is impossible:
                # if any existing hit lies outside placement but adjacent in-between negatives? (Hard to fully enforce)
                # For simplicity, we allow placement as long as it doesn't conflict with misses.
                for (x, y) in cells:
                    heat[x, y] += 1.0
        # Vertical placements
        for r in range(n - L + 1):
            for c in range(n):
                cells = [(r + k, c) for k in range(L)]
                values = [b[x, y] for (x, y) in cells]
                if any(v == -1 for v in values):
                    continue
                if any_hits:
                    if not any(v == 1 for v in values):
                        continue
                for (x, y) in cells:
                    heat[x, y] += 1.0

    # If no placements were added (possible if ships_removed logic too aggressive), fall back to counting ignoring hits constraint
    if np.all(heat == 0):
        for L in ships_remaining:
            for r in range(n):
                for c in range(n - L + 1):
                    cells = [(r, c + k) for k in range(L)]
                    values = [b[x, y] for (x, y) in cells]
                    if any(v == -1 for v in values):
                        continue
                    for (x, y) in cells:
                        heat[x, y] += 1.0
            for r in range(n - L + 1):
                for c in range(n):
                    cells = [(r + k, c) for k in range(L)]
                    values = [b[x, y] for (x, y) in cells]
                    if any(v == -1 for v in values):
                        continue
                    for (x, y) in cells:
                        heat[x, y] += 1.0

    # Penalize already-shot cells heavily so they won't be chosen
    # We'll set their heat to -inf
    mask_unknown = (b == 0)
    heat_masked = np.where(mask_unknown, heat, -1e9)

    # Target-mode candidate generation: when there are hits, try to target the cluster(s)
    target_candidates = set()
    if any_hits:
        for comp in clusters:
            if len(comp) == 0:
                continue
            # If oriented (len >=2), try extending along orientation
            rows = [p[0] for p in comp]
            cols = [p[1] for p in comp]
            minr, maxr = min(rows), max(rows)
            minc, maxc = min(cols), max(cols)
            if minr == maxr:
                # horizontal: try extend left and right
                r = minr
                left = (r, minc - 1)
                if 0 <= left[0] < n and 0 <= left[1] < n and b[left] == 0:
                    target_candidates.add(left)
                right = (r, maxc + 1)
                if 0 <= right[0] < n and 0 <= right[1] < n and b[right] == 0:
                    target_candidates.add(right)
                # also add orthogonal neighbors for singletons or if extensions blocked
                if not target_candidates:
                    for (x, y) in comp:
                        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                            nx, ny = x+dx, y+dy
                            if 0 <= nx < n and 0 <= ny < n and b[nx, ny] == 0:
                                target_candidates.add((nx, ny))
            elif minc == maxc:
                # vertical: extend up and down
                c = minc
                up = (minr - 1, c)
                if 0 <= up[0] < n and 0 <= up[1] < n and b[up] == 0:
                    target_candidates.add(up)
                down = (maxr + 1, c)
                if 0 <= down[0] < n and 0 <= down[1] < n and b[down] == 0:
                    target_candidates.add(down)
                if not target_candidates:
                    for (x, y) in comp:
                        for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                            nx, ny = x+dx, y+dy
                            if 0 <= nx < n and 0 <= ny < n and b[nx, ny] == 0:
                                target_candidates.add((nx, ny))
            else:
                # Irregular shape (shouldn't happen often) - add neighbors
                for (x, y) in comp:
                    for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < n and 0 <= ny < n and b[nx, ny] == 0:
                            target_candidates.add((nx, ny))
        # Filter out any already-shot (shouldn't be present)
        target_candidates = {p for p in target_candidates if b[p] == 0}

    # If we have target candidates, pick the one with highest heat among them
    if target_candidates:
        best = None
        best_score = -1e9
        for (r, c) in target_candidates:
            score = heat_masked[r, c]
            # Boost candidates that are in-line with multiple hits (prefer continuing a line)
            # Count how many neighboring hits are aligned with this candidate
            neigh_hits = 0
            for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                nx, ny = r+dx, c+dy
                if 0 <= nx < n and 0 <= ny < n and b[nx, ny] == 1:
                    neigh_hits += 1
            score += 0.5 * neigh_hits
            # Slight center bias to break ties toward center
            center_dist = abs(r - (n-1)/2) + abs(c - (n-1)/2)
            score -= 0.01 * center_dist
            if score > best_score:
                best_score = score
                best = (r, c)
        if best is not None:
            return best

    # Otherwise, pick unknown cell with highest heat. Tie-break by center proximity then row-major.
    # As an additional small improvement, favor a checkerboard parity pattern: multiply heat by 1.05 for parity cells
    parity_boost = np.where(((np.add.outer(np.arange(n), np.arange(n)) % 2) == 0), 1.05, 1.0)
    heat_adj = heat_masked * parity_boost

    # Choose max
    max_val = np.max(heat_adj)
    if max_val <= -1e8:
        # no unknown cells (should not happen) - return first cell fallback
        for r in range(n):
            for c in range(n):
                if b[r, c] == 0:
                    return (r, c)
        return (0, 0)

    # Collect indices with max value
    candidates = list(zip(*np.where(heat_adj == max_val)))
    # Tie-break: choose candidate closest to center
    center = ( (n-1)/2.0, (n-1)/2.0 )
    def center_dist(p):
        return abs(p[0]-center[0]) + abs(p[1]-center[1])
    candidates.sort(key=lambda p: (center_dist(p), p[0], p[1]))
    return candidates[0]
