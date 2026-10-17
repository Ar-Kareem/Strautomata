
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Parse the board to get all hits
    hit_set = set()
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                hit_set.add((r, c))

    # If there are no hits, do a random hunt.
    if not hit_set:
        available = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    available.append((r, c))
        return random.choice(available)

    # Group the hits by 4-connectivity (contiguous hits)
    visited = set()
    groups = []

    for hit in hit_set:
        if hit in visited:
            continue
        group = []
        queue = deque([hit])
        while queue:
            node = queue.popleft()
            if node in visited:
                continue
            visited.add(node)
            group.append(node)
            # Check neighbors
            r, c = node
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if (nr, nc) in hit_set and (nr, nc) not in visited:
                    queue.append((nr, nc))
        groups.append(group)

    # Filter groups that are straight (horizontal or vertical)
    active_targets = []
    for group in groups:
        if len(group) == 1:
            active_targets.append(group)
        else:
            rows = {hit[0] for hit in group}
            cols = {hit[1] for hit in group}
            if len(rows) == 1:
                active_targets.append(group)  # horizontal
            elif len(cols) == 1:
                active_targets.append(group)  # vertical
            # else: skip non-straight groups (shouldn't happen per rules)

    # For each active target, compute candidate cells for extension
    candidate_targets = []  # list of (group, candidates_set)

    for group in active_targets:
        candidates = set()
        if len(group) == 1:
            # Single hit: try all four adjacent cells
            r, c = group[0]
            for dr, dc in [(-1,0), (1,0), (0,-1), (0,1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidates.add((nr, nc))
        else:
            # Multiple hits: determine orientation and extend
            rows = {hit[0] for hit in group}
            cols = {hit[1] for hit in group}
            if len(rows) == 1:  # horizontal
                r = group[0][0]
                min_c = min(hit[1] for hit in group)
                max_c = max(hit[1] for hit in group)
                # Extend left
                if min_c-1 >= 0 and board[r][min_c-1] == 0:
                    candidates.add((r, min_c-1))
                # Extend right
                if max_c+1 < 10 and board[r][max_c+1] == 0:
                    candidates.add((r, max_c+1))
            elif len(cols) == 1:  # vertical
                c = group[0][1]
                min_r = min(hit[0] for hit in group)
                max_r = max(hit[0] for hit in group)
                # Extend up
                if min_r-1 >= 0 and board[min_r-1][c] == 0:
                    candidates.add((min_r-1, c))
                # Extend down
                if max_r+1 < 10 and board[max_r+1][c] == 0:
                    candidates.add((max_r+1, c))

        if candidates:
            candidate_targets.append((group, candidates))

    # Choose the best target and a random candidate from it
    if candidate_targets:
        # Prioritize targets with more hits
        candidate_targets.sort(key=lambda x: len(x[0]), reverse=True)
        group, candidates = candidate_targets[0]
        return random.choice(list(candidates))
    else:
        # No candidate from active targets: random hunt
        available = []
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    available.append((r, c))
        return random.choice(available)
