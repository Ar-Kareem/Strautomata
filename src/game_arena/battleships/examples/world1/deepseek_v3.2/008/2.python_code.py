
import random

# Global state
untried_set = set((r, c) for r in range(10) for c in range(10))
hit_set = set()
miss_set = set()
clusters = []  # list of sets of hits that are connected and not yet sunk
pending_targets = []   # queue of cells to try next
pending_set = set()    # to avoid duplicates in pending_targets

def policy(board: list[list[int]]) -> tuple[int, int]:
    global untried_set, hit_set, miss_set, clusters, pending_targets, pending_set

    # 1. Update our knowledge from the board
    for r in range(10):
        for c in range(10):
            val = board[r][c]
            if val == 1 and (r, c) not in hit_set:
                hit_set.add((r, c))
                if (r, c) in untried_set:
                    untried_set.remove((r, c))
            elif val == -1 and (r, c) not in miss_set:
                miss_set.add((r, c))
                if (r, c) in untried_set:
                    untried_set.remove((r, c))

    # 2. Rebuild clusters from current hits
    remaining_hits = hit_set.copy()
    new_clusters = []
    while remaining_hits:
        start = remaining_hits.pop()
        stack = [start]
        cluster = {start}
        while stack:
            r, c = stack.pop()
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if (nr, nc) in remaining_hits:
                    remaining_hits.remove((nr, nc))
                    cluster.add((nr, nc))
                    stack.append((nr, nc))
        new_clusters.append(cluster)

    # 3. Determine which clusters are sunk (no unknown orthogonal neighbors)
    unsunk_clusters = []
    for cluster in new_clusters:
        sunk = True
        for (r, c) in cluster:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10:
                    if (nr, nc) not in hit_set and (nr, nc) not in miss_set:
                        sunk = False
                        break
            if not sunk:
                break
        if not sunk:
            unsunk_clusters.append(cluster)
    clusters = unsunk_clusters

    # 4. If there are unsunk clusters, generate target cells around them
    if clusters:
        # Prioritize larger clusters (closer to sinking)
        clusters.sort(key=len, reverse=True)
        for cluster in clusters:
            if len(cluster) == 1:
                r, c = next(iter(cluster))
                for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10:
                        if (nr, nc) in untried_set and (nr, nc) not in pending_set:
                            pending_targets.append((nr, nc))
                            pending_set.add((nr, nc))
            else:
                rows = [r for (r, c) in cluster]
                cols = [c for (r, c) in cluster]
                if len(set(rows)) == 1:   # horizontal
                    row = rows[0]
                    min_col = min(cols)
                    max_col = max(cols)
                    # left end
                    if min_col - 1 >= 0 and (row, min_col - 1) in untried_set and (row, min_col - 1) not in pending_set:
                        pending_targets.append((row, min_col - 1))
                        pending_set.add((row, min_col - 1))
                    # right end
                    if max_col + 1 < 10 and (row, max_col + 1) in untried_set and (row, max_col + 1) not in pending_set:
                        pending_targets.append((row, max_col + 1))
                        pending_set.add((row, max_col + 1))
                elif len(set(cols)) == 1:   # vertical
                    col = cols[0]
                    min_row = min(rows)
                    max_row = max(rows)
                    # top end
                    if min_row - 1 >= 0 and (min_row - 1, col) in untried_set and (min_row - 1, col) not in pending_set:
                        pending_targets.append((min_row - 1, col))
                        pending_set.add((min_row - 1, col))
                    # bottom end
                    if max_row + 1 < 10 and (max_row + 1, col) in untried_set and (max_row + 1, col) not in pending_set:
                        pending_targets.append((max_row + 1, col))
                        pending_set.add((max_row + 1, col))
                else:
                    # Cluster is not a straight line (touching ships). Add all orthogonal neighbors.
                    for (r, c) in cluster:
                        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 10 and 0 <= nc < 10:
                                if (nr, nc) in untried_set and (nr, nc) not in pending_set:
                                    pending_targets.append((nr, nc))
                                    pending_set.add((nr, nc))

    # 5. If no pending targets, enter hunting mode: pick the best unknown cell.
    if not pending_targets:
        best_cell = None
        best_score = -1
        for (r, c) in untried_set:
            # Count unknown cells in the same row and column (including itself)
            row_count = sum(1 for j in range(10) if (r, j) in untried_set)
            col_count = sum(1 for i in range(10) if (i, c) in untried_set)
            # Slight preference for even parity (checkerboard pattern)
            parity_bonus = 1 if (r + c) % 2 == 0 else 0
            score = row_count + col_count + parity_bonus
            if score > best_score:
                best_score = score
                best_cell = (r, c)
        if best_cell is not None:
            pending_targets.append(best_cell)
            pending_set.add(best_cell)

    # 6. Select the next target from the queue, ensuring it's still untried.
    while pending_targets:
        candidate = pending_targets.pop(0)
        pending_set.remove(candidate)
        if candidate in untried_set:
            return candidate

    # Fallback: any untried cell (should not happen)
    if untried_set:
        return next(iter(untried_set))
    else:
        # No untried cells left (game over)
        return (0, 0)
