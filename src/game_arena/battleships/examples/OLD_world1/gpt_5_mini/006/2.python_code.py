import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy for a 10x10 grid.
    board: 10x10 list of lists with values:
      0 -> unknown
     -1 -> miss
      1 -> hit

    Returns a tuple (row, col) of an unknown cell to fire at next.
    """
    n = 10
    a = np.array(board)
    unknown = (a == 0)
    miss = (a == -1)
    hit = (a == 1)

    # Standard Battleship ship lengths
    ship_lengths = [5, 4, 3, 3, 2]

    # Heat map accumulation from all possible ship placements
    heat = np.zeros((n, n), dtype=int)

    for L in ship_lengths:
        # horizontal placements
        for r in range(n):
            for c in range(n - L + 1):
                # cells covered by this placement
                cols = slice(c, c + L)
                segment = a[r, cols]
                # placement invalid if any miss in covered cells
                if np.any(segment == -1):
                    continue
                # valid placement: increment unknown cells in it
                for cc in range(c, c + L):
                    if unknown[r, cc]:
                        heat[r, cc] += 1
        # vertical placements
        for c in range(n):
            for r in range(n - L + 1):
                rows = slice(r, r + L)
                segment = a[rows, c]
                if np.any(segment == -1):
                    continue
                for rr in range(r, r + L):
                    if unknown[rr, c]:
                        heat[rr, c] += 1

    # Targeting: find connected hit clusters and heavily weight extensions that continue them
    target_boost = 1000  # large weight to prefer finishing ships we've hit
    visited = np.zeros((n, n), dtype=bool)
    dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for i in range(n):
        for j in range(n):
            if hit[i, j] and not visited[i, j]:
                # BFS/DFS to collect cluster
                stack = [(i, j)]
                cluster = []
                visited[i, j] = True
                while stack:
                    x, y = stack.pop()
                    cluster.append((x, y))
                    for dx, dy in dirs:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < n and 0 <= ny < n and not visited[nx, ny] and hit[nx, ny]:
                            visited[nx, ny] = True
                            stack.append((nx, ny))
                # Analyze cluster
                if len(cluster) == 1:
                    x, y = cluster[0]
                    # single hit: try all four neighbors
                    for dx, dy in dirs:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < n and 0 <= ny < n and unknown[nx, ny]:
                            heat[nx, ny] += target_boost
                else:
                    rows = [p[0] for p in cluster]
                    cols = [p[1] for p in cluster]
                    if len(set(rows)) == 1:
                        # horizontal cluster: extend left/right
                        r0 = rows[0]
                        minc, maxc = min(cols), max(cols)
                        left = (r0, minc - 1)
                        right = (r0, maxc + 1)
                        if 0 <= left[1] < n and unknown[left]:
                            heat[left] += target_boost
                        if 0 <= right[1] < n and unknown[right]:
                            heat[right] += target_boost
                    elif len(set(cols)) == 1:
                        # vertical cluster: extend up/down
                        c0 = cols[0]
                        minr, maxr = min(rows), max(rows)
                        up = (minr - 1, c0)
                        down = (maxr + 1, c0)
                        if 0 <= up[0] < n and unknown[up]:
                            heat[up] += target_boost
                        if 0 <= down[0] < n and unknown[down]:
                            heat[down] += target_boost
                    else:
                        # Irregular shape (shouldn't happen with correct hits), fallback: boost neighbors
                        for x, y in cluster:
                            for dx, dy in dirs:
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < n and 0 <= ny < n and unknown[nx, ny]:
                                    heat[nx, ny] += target_boost

    # Do not consider non-unknown cells
    heat_masked = np.where(unknown, heat, -1)

    # If there are no positive heat values, fall back to parity hunt (checkerboard) to improve efficiency
    max_heat = int(heat_masked.max())
    if max_heat <= 0:
        # Prefer parity where ships of length >=2 will fit: use 2-cell parity (checkerboard)
        candidates = [(i, j) for i in range(n) for j in range(n) if unknown[i, j] and ((i + j) % 2 == 0)]
        if not candidates:
            candidates = [(i, j) for i in range(n) for j in range(n) if unknown[i, j]]
        # deterministic tie-breaker: choose smallest (row, col)
        candidates.sort()
        return (int(candidates[0][0]), int(candidates[0][1]))

    # Otherwise pick the unknown cell(s) with maximum heat
    ys, xs = np.where(heat_masked == max_heat)
    choices = list(zip(ys.tolist(), xs.tolist()))
    choices.sort()
    chosen = choices[0]
    return (int(chosen[0]), int(chosen[1]))