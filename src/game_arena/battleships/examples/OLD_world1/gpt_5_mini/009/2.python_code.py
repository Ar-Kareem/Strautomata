import time

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Battleship targeting policy for a 10x10 grid.
    board: 10x10 list of ints: 0 unknown, -1 miss, 1 hit
    returns: (row, col) of a cell not previously fired at (board cell == 0)
    """
    N = 10
    # Ship lengths for standard Battleship: carrier(5), battleship(4), cruiser(3), submarine(3), destroyer(2)
    ship_lengths = [5, 4, 3, 3, 2]

    # Flatten helpers: bitmask index for cell
    def pos_to_bit(r, c):
        return 1 << (r * N + c)

    # Build masks for hits, misses, and unknown cells
    hits_mask = 0
    misses_mask = 0
    unknown_positions = []
    for r in range(N):
        for c in range(N):
            v = board[r][c]
            bit = pos_to_bit(r, c)
            if v == 1:
                hits_mask |= bit
            elif v == -1:
                misses_mask |= bit
            else:  # 0
                unknown_positions.append((r, c))

    # If no unknowns (shouldn't happen), return (0,0)
    if not unknown_positions:
        return (0, 0)

    # Precompute all candidate placements for each ship length as bitmasks
    placements_by_length = {}
    for L in set(ship_lengths):
        placements = []
        # horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                mask = 0
                valid = True
                for k in range(L):
                    bit = pos_to_bit(r, c + k)
                    if (misses_mask & bit) != 0:
                        valid = False
                        break
                    mask |= bit
                if valid:
                    placements.append(mask)
        # vertical placements
        for c in range(N):
            for r in range(N - L + 1):
                mask = 0
                valid = True
                for k in range(L):
                    bit = pos_to_bit(r + k, c)
                    if (misses_mask & bit) != 0:
                        valid = False
                        break
                    mask |= bit
                if valid:
                    placements.append(mask)
        placements_by_length[L] = placements

    # If there are hits, try a quick targeted approach: if hits form a contiguous line detect orientation and extend
    # But we'll primarily use full-placement enumeration below. This quick check helps fallback behavior.
    def find_target_adjacent_to_hits():
        # find all hit coords
        hit_coords = []
        for r in range(N):
            for c in range(N):
                if board[r][c] == 1:
                    hit_coords.append((r, c))
        if not hit_coords:
            return None
        # For each connected cluster of hits, attempt to deduce orientation and pick an extension cell
        visited = set()
        clusters = []
        for hr, hc in hit_coords:
            if (hr, hc) in visited:
                continue
            # BFS cluster
            stack = [(hr, hc)]
            cluster = []
            while stack:
                x, y = stack.pop()
                if (x, y) in visited:
                    continue
                visited.add((x, y))
                cluster.append((x, y))
                for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < N and 0 <= ny < N and board[nx][ny] == 1 and (nx, ny) not in visited:
                        stack.append((nx, ny))
            clusters.append(cluster)
        # For each cluster, try to extend along likely orientations
        best_candidate = None
        for cluster in clusters:
            if len(cluster) == 1:
                r, c = cluster[0]
                # prefer orthogonal neighbors that are unknown
                for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                        return (nr, nc)
            else:
                # determine orientation
                xs = [p[0] for p in cluster]
                ys = [p[1] for p in cluster]
                if len(set(xs)) == 1:
                    # horizontal row constant x => vary y; actually same row -> horizontal orientation (vary columns)
                    r = xs[0]
                    minc = min(ys)
                    maxc = max(ys)
                    # extend left
                    left = (r, minc - 1)
                    right = (r, maxc + 1)
                    if 0 <= left[0] < N and 0 <= left[1] < N and board[left[0]][left[1]] == 0:
                        return left
                    if 0 <= right[0] < N and 0 <= right[1] < N and board[right[0]][right[1]] == 0:
                        return right
                elif len(set(ys)) == 1:
                    # vertical
                    c = ys[0]
                    minr = min(xs)
                    maxr = max(xs)
                    up = (minr - 1, c)
                    down = (maxr + 1, c)
                    if 0 <= up[0] < N and 0 <= up[1] < N and board[up[0]][up[1]] == 0:
                        return up
                    if 0 <= down[0] < N and 0 <= down[1] < N and board[down[0]][down[1]] == 0:
                        return down
                else:
                    # irregular cluster (shouldn't happen), try neighbors of any part
                    for r, c in cluster:
                        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                                return (nr, nc)
        return best_candidate

    # If there are hits and there is a clear adjacent unknown to fire at, use it as a fast-target
    if hits_mask != 0:
        adj = find_target_adjacent_to_hits()
        if adj is not None:
            return adj

    # Build per-ship candidate lists (masks) for each ship instance (we treat repeated lengths as separate ships)
    ship_instances = []
    for L in ship_lengths:
        # copy placements list for this instance
        placements = placements_by_length.get(L, []).copy()
        ship_instances.append({
            "length": L,
            "placements": placements
        })

    # Sort ship instances by number of placements (smallest first) to improve DFS pruning
    ship_instances.sort(key=lambda s: len(s["placements"]))

    # Precompute for each ship instance a map hit_bit -> list of placement masks that include that hit
    for s in ship_instances:
        placements = s["placements"]
        by_hit = {}
        for mask in placements:
            m = mask
            # iterate bits set in mask
            mm = m
            while mm:
                lb = mm & -mm
                by_hit.setdefault(lb, []).append(mask)
                mm -= lb
        s["placements_by_hit"] = by_hit

    # DFS to enumerate full-fleet placements consistent with misses and covering all hits
    heatmap = [0] * (N * N)
    placements_count = 0
    MAX_PLACEMENTS = 20000  # safety cap
    TIME_LIMIT = 0.9  # seconds
    t_start = time.time()

    total_ships = len(ship_instances)
    hits_mask_global = hits_mask

    # Helper to iterate hit bits
    def iter_bits(mask):
        while mask:
            lb = mask & -mask
            yield lb
            mask -= lb

    # Quick feasibility check: can uncovered hits be covered by remaining ships given current occupied mask?
    def can_cover_uncovered_hits(occupied_mask, remaining_indices, covered_mask):
        uncovered = hits_mask_global & (~covered_mask)
        if uncovered == 0:
            return True
        # For each uncovered hit bit, check if any remaining ship has a placement covering it that doesn't intersect occupied_mask
        for bit in iter_bits(uncovered):
            possible = False
            for idx in remaining_indices:
                s = ship_instances[idx]
                # placements that include this hit bit
                lst = s["placements_by_hit"].get(bit)
                if not lst:
                    continue
                # check if any such placement is available (no overlap with occupied)
                for pmask in lst:
                    if (pmask & occupied_mask) == 0:
                        possible = True
                        break
                if possible:
                    break
            if not possible:
                return False
        return True

    # Order of placing ships: indices list
    ship_order = list(range(total_ships))

    # DFS recursion
    chosen_masks_stack = [0] * total_ships  # store chosen mask for each depth
    def dfs(depth, occupied_mask, covered_mask):
        nonlocal placements_count, heatmap, t_start
        # time check
        if time.time() - t_start > TIME_LIMIT:
            return False  # signal to stop due to time
        if placements_count >= MAX_PLACEMENTS:
            return True  # reached cap, stop exploring further but indicate to upper layers
        if depth == total_ships:
            # full placement: ensure all hits are covered
            if covered_mask == hits_mask_global:
                placements_count += 1
                # add to heatmap
                for i in range(N * N):
                    if (occupied_mask >> i) & 1:
                        heatmap[i] += 1
            return False  # continue search
        idx = ship_order[depth]
        s = ship_instances[idx]
        placements = s["placements"]
        # Try placements for this ship that don't intersect occupied_mask
        for pmask in placements:
            if (pmask & occupied_mask) != 0:
                continue
            new_occupied = occupied_mask | pmask
            new_covered = covered_mask | (pmask & hits_mask_global)
            # Prune: check whether uncovered hits can still be covered by remaining ships
            remaining = ship_order[depth+1:]
            if not can_cover_uncovered_hits(new_occupied, remaining, new_covered):
                continue
            # Recurse
            stop_due_to_time_or_cap = dfs(depth + 1, new_occupied, new_covered)
            if time.time() - t_start > TIME_LIMIT:
                return False
            if stop_due_to_time_or_cap and placements_count >= MAX_PLACEMENTS:
                return True
        return False

    # Run DFS
    try:
        dfs(0, 0, 0)
    except RecursionError:
        # fallback if recursion depth problems (shouldn't happen)
        pass

    # If we collected some placements, pick the unknown cell with highest heatmap value
    best_cell = None
    if placements_count > 0:
        best_score = -1
        for r in range(N):
            for c in range(N):
                if board[r][c] != 0:
                    continue
                idx = r * N + c
                score = heatmap[idx]
                if score > best_score:
                    best_score = score
                    best_cell = (r, c)
        if best_cell is not None:
            return best_cell

    # If DFS yielded no placements (or time cap), fall back to simpler heuristics

    # 1) If there are hits, pick unknown adjacent to hits (had earlier but could be time-limited); do again
    if hits_mask != 0:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 1:
                    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                            return (nr, nc)
        # If none adjacent, pick unknown cell in same row/col with hits maybe
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    # if same row or column has a hit, prefer
                    row_has_hit = any(board[r][j] == 1 for j in range(N))
                    col_has_hit = any(board[i][c] == 1 for i in range(N))
                    if row_has_hit or col_has_hit:
                        return (r, c)

    # 2) Parity hunt: prefer cells on a checkerboard sized by largest remaining ship length
    max_len = max(ship_lengths)
    best_cell = None
    best_value = -1
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            # parity score: only consider cells where (r+c) % (max_len) fits pattern to maximize spacing
            parity_score = 1 if ((r + c) % 2 == 0) else 0
            # Also add heuristic: count how many ship placements (single-ship) could cover this cell (ignoring other ships)
            count_possible = 0
            for L in ship_lengths:
                for pmask in placements_by_length.get(L, []):
                    if (pmask >> (r * N + c)) & 1:
                        count_possible += 1
            score = parity_score * 10 + count_possible
            # tie-breaker choose center-proximal
            center_dist = abs(r - (N-1)/2) + abs(c - (N-1)/2)
            score -= center_dist * 0.01
            if score > best_value:
                best_value = score
                best_cell = (r, c)
    if best_cell is not None:
        return best_cell

    # As a final fallback, return the first unknown cell
    return unknown_positions[0]