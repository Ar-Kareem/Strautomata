
import random
from typing import List, Tuple

def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10

    # --- Helpers ---
    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N

    def unknown_cells():
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    yield r, c

    def get_hits():
        hits = []
        for r in range(N):
            for c in range(N):
                if board[r][c] == 1:
                    hits.append((r, c))
        return hits

    # Determine remaining ship lengths. We can’t know exact sunk ships,
    # but we can infer upper bounds from remaining hits constraints.
    # A strong heuristic: ship lengths are fixed [5,4,3,3,2]; we use all of them
    # but only count placements consistent with current evidence.
    SHIPS = [5, 4, 3, 3, 2]

    # --- Heatmap probability from all consistent ship placements ---
    # Computes for each cell the number of ways any ship can be placed such that:
    # - ship cells do not overlap misses (-1)
    # - ship covers all currently known hits if those hits are on the ship segment
    # We don't force covering *all* hits at once (since we don't know which ship each hit belongs to),
    # but we ensure a candidate placement doesn't conflict with hits distribution.
    def compute_heatmap():
        heat = [[0]*N for _ in range(N)]
        hits = get_hits()
        hit_set = set(hits)

        # For each ship length, count placements consistent with evidence.
        for L in SHIPS:
            # Horizontal placements
            for r in range(N):
                for c0 in range(N - L + 1):
                    cells = [(r, c0+i) for i in range(L)]
                    ok = True
                    # placement cannot include any miss
                    for (rr, cc) in cells:
                        if board[rr][cc] == -1:
                            ok = False
                            break
                    if not ok:
                        continue
                    # If placement includes some hits, that's fine.
                    # But if there are hits, we can allow placements that cover only a subset.
                    # However, for better targeting, we will slightly favor placements that
                    # include hits by requiring that if there are hits, the placement must be
                    # compatible with them: it cannot "cross" hits in an impossible way is hard,
                    # so we simply allow any non-miss placement.
                    # Still, we can weight placements that include more hits.
                    include_hits = sum(1 for (rr, cc) in cells if (rr, cc) in hit_set)
                    # Weight: base 1, plus extra for each included hit.
                    w = 1 + 3*include_hits
                    for (rr, cc) in cells:
                        if board[rr][cc] == 0:
                            heat[rr][cc] += w

            # Vertical placements
            for c in range(N):
                for r0 in range(N - L + 1):
                    cells = [(r0+i, c) for i in range(L)]
                    ok = True
                    for (rr, cc) in cells:
                        if board[rr][cc] == -1:
                            ok = False
                            break
                    if not ok:
                        continue
                    include_hits = sum(1 for (rr, cc) in cells if (rr, cc) in hit_set)
                    w = 1 + 3*include_hits
                    for (rr, cc) in cells:
                        if board[rr][cc] == 0:
                            heat[rr][cc] += w

        return heat

    # --- Targeting logic using existing hits ---
    def adjacent_unknown_score(r, c):
        # score adjacent unknown neighbors using heatmap to break ties
        heat = compute_heatmap()
        best = None
        bestv = -1
        for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
            rr, cc = r+dr, c+dc
            if in_bounds(rr, cc) and board[rr][cc] == 0:
                v = heat[rr][cc]
                if v > bestv:
                    bestv = v
                    best = (rr, cc)
        return best

    hits = get_hits()

    # If we have hits, try to extend them intelligently.
    if hits:
        hit_set = set(hits)

        # Group hits by whether they line up in a potential orientation.
        # Find a cluster: pick one hit and BFS through adjacent hits (4-neighborhood).
        start = hits[0]
        cluster = set([start])
        stack = [start]
        while stack:
            r, c = stack.pop()
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r+dr, c+dc
                if in_bounds(rr, cc) and (rr, cc) in hit_set and (rr, cc) not in cluster:
                    cluster.add((rr, cc))
                    stack.append((rr, cc))
        cluster = list(cluster)

        # Determine if cluster suggests orientation
        rows = {r for r, c in cluster}
        cols = {c for r, c in cluster}

        heat = compute_heatmap()

        # If cluster is more aligned in rows or cols
        if len(rows) == 1 and len(cols) > 1:
            # horizontal orientation
            r = next(iter(rows))
            cmin = min(cols)
            cmax = max(cols)
            candidates = []
            left = (r, cmin-1)
            right = (r, cmax+1)
            if in_bounds(*left) and board[left[0]][left[1]] == 0:
                candidates.append(left)
            if in_bounds(*right) and board[right[0]][right[1]] == 0:
                candidates.append(right)
            if candidates:
                # choose by heat
                candidates.sort(key=lambda x: heat[x[0]][x[1]], reverse=True)
                return candidates[0]

        if len(cols) == 1 and len(rows) > 1:
            # vertical orientation
            c = next(iter(cols))
            rmin = min(rows)
            rmax = max(rows)
            candidates = []
            up = (rmin-1, c)
            down = (rmax+1, c)
            if in_bounds(*up) and board[up[0]][up[1]] == 0:
                candidates.append(up)
            if in_bounds(*down) and board[down[0]][down[1]] == 0:
                candidates.append(down)
            if candidates:
                candidates.sort(key=lambda x: heat[x[0]][x[1]], reverse=True)
                return candidates[0]

        # Otherwise, we have isolated hits or ambiguous cluster: try all adjacent cells around hits
        best = None
        bestv = -1
        for r, c in hits:
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                rr, cc = r+dr, c+dc
                if in_bounds(rr, cc) and board[rr][cc] == 0:
                    v = heat[rr][cc]
                    if v > bestv:
                        bestv = v
                        best = (rr, cc)
        if best is not None:
            return best

        # Fallback: shoot highest heat among all unknowns
        heat = compute_heatmap()
        best = None
        bestv = -1
        for r, c in unknown_cells():
            v = heat[r][c]
            if v > bestv:
                bestv = v
                best = (r, c)
        if best is not None:
            return best

    # --- Hunt mode ---
    heat = compute_heatmap()

    # Optional: checkerboard bias to reduce waste (only if heat is similar).
    # We'll incorporate it lightly by multiplying heat on one parity.
    parity = random.randint(0, 1)
    best = None
    bestv = -1
    for r, c in unknown_cells():
        v = heat[r][c]
        if (r + c) % 2 == parity:
            v *= 1.15
        if v > bestv:
            bestv = v
            best = (r, c)

    # Ensure legality
    if best is None:
        # should not happen, but be safe
        for r, c in unknown_cells():
            return (r, c)
    return best
