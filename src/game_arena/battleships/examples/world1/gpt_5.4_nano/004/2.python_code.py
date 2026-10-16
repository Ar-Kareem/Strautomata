
import numpy as np
from typing import List, Tuple

def policy(board: list[list[int]]) -> Tuple[int, int]:
    """
    Battleship policy for a 10x10 grid.
    board values: 0=unknown, -1=miss, 1=hit
    Must return (row, col) with board[row][col] == 0.
    """

    B = np.array(board, dtype=int)
    N = 10

    # Remaining ship lengths for standard fleet: 5,4,3,3,2
    ship_lengths = [5, 4, 3, 3, 2]

    # Collect info about hits
    hits = np.argwhere(B == 1)
    hits_set = set((int(r), int(c)) for r, c in hits)

    def in_bounds(r, c):
        return 0 <= r < N and 0 <= c < N

    # If we have hits, go into targeting mode
    if len(hits) > 0:
        # Determine orientation if possible: if multiple hits align
        # If not aligned, try each direction around a hit.
        hit_rows = sorted(set(int(r) for r, _ in hits))
        hit_cols = sorted(set(int(c) for _, c in hits))

        directions = []
        if len(hit_rows) == 1 and len(hit_cols) >= 2:
            # Horizontal ship (same row)
            directions = [(0, -1), (0, 1)]
            fixed_r = hit_rows[0]
            # Candidates are to the left/right of the current hit segment
            row = fixed_r
            cols = sorted(int(c) for _, c in hits)
            left_c = cols[0] - 1
            right_c = cols[-1] + 1
            candidates = []
            if in_bounds(row, left_c) and B[row, left_c] == 0:
                candidates.append((row, left_c))
            if in_bounds(row, right_c) and B[row, right_c] == 0:
                candidates.append((row, right_c))
            if candidates:
                # Prefer the candidate that gives longer contiguous potential (simple heuristic)
                def segment_potential(cell):
                    rr, cc = cell
                    # count how far we can extend until blocked by miss or boundary
                    # extend one side only (from the edge outward) for bias
                    d1 = (0, -1) if cc > cols[0] else (0, 1)
                    dr, dc = d1
                    steps = 0
                    rrr, ccc = rr + dr, cc + dc
                    while in_bounds(rrr, ccc) and B[rrr, ccc] != -1:
                        if B[rrr, ccc] == 0 or B[rrr, ccc] == 1:
                            steps += 1
                            rrr += dr
                            ccc += dc
                        else:
                            break
                    return steps

                candidates.sort(key=segment_potential, reverse=True)
                return candidates[0]

        if len(hit_cols) == 1 and len(hit_rows) >= 2:
            # Vertical ship (same col)
            directions = [(-1, 0), (1, 0)]
            fixed_c = hit_cols[0]
            col = fixed_c
            rows = sorted(int(r) for r, _ in hits)
            top_r = rows[0] - 1
            bot_r = rows[-1] + 1
            candidates = []
            if in_bounds(top_r, col) and B[top_r, col] == 0:
                candidates.append((top_r, col))
            if in_bounds(bot_r, col) and B[bot_r, col] == 0:
                candidates.append((bot_r, col))
            if candidates:
                return candidates[0]

        # If orientation unclear (single hit or scattered hits), try neighbors of hits
        # in a prioritized order based on probability-like scoring local extension.
        candidate_cells = set()
        for r, c in hits_set:
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc) and B[rr, cc] == 0:
                    candidate_cells.add((rr, cc))

        if candidate_cells:
            # Score candidates by how well they fit any ship length with current hit cluster
            # We'll use a quick local scan: count maximum consecutive cells (ignoring misses)
            # that include candidate and existing hits in each direction.
            def max_run_through(cell):
                rr, cc = cell
                best = 0
                for (dr, dc) in [(1,0),(0,1)]:  # check both axes by scanning both directions
                    # extend backward
                    r1, c1 = rr-dr, cc-dc
                    back = 0
                    while in_bounds(r1, c1) and B[r1, c1] != -1:
                        # miss blocks; hits/unknown ok
                        back += 1
                        r1 -= dr
                        c1 -= dc
                    # extend forward
                    r2, c2 = rr+dr, cc+dc
                    fwd = 0
                    while in_bounds(r2, c2) and B[r2, c2] != -1:
                        fwd += 1
                        r2 += dr
                        c2 += dc
                    run = 1 + back + fwd
                    if run > best:
                        best = run
                return best

            best_cell = None
            best_score = -1
            for cell in candidate_cells:
                score = max_run_through(cell)
                if score > best_score:
                    best_score = score
                    best_cell = cell
            return best_cell

        # Fallback (should be rare): use hunt mode
        # Continue to hunt below.

    # HUNT mode: probability heatmap based on all valid placements consistent with known misses/hits
    heat = np.zeros((N, N), dtype=int)

    # For each ship length, count all placements consistent with board knowledge:
    # - placements cannot cover a known miss (-1)
    # - placements may cover hits (1) and unknowns (0)
    for L in ship_lengths:
        # Horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                segment = B[r, c:c+L]
                if np.any(segment == -1):
                    continue
                # If there are hits, the placement should ideally cover at least one hit,
                # but allowing misses keeps hunt robust when targeting failed.
                # We'll softly bias by filtering placements that cover no hits when there are hits on board.
                if len(hits) > 0 and not np.any(segment == 1):
                    continue
                heat[r, c:c+L] += 1

        # Vertical placements
        for c in range(N):
            for r in range(N - L + 1):
                segment = B[r:r+L, c]
                if np.any(segment == -1):
                    continue
                if len(hits) > 0 and not np.any(segment == 1):
                    continue
                heat[r:r+L, c] += 1

    # Choose the best cell that is unknown (0)
    unknown = np.argwhere(B == 0)
    if len(unknown) == 0:
        # Should never happen; but return (0,0) if forced.
        return (0, 0)

    # Small optimization: parity bias in early/mid game (helps beat random)
    # Prefer checkerboard cells for larger ships.
    # If multiple max-heat cells, pick with parity preference.
    max_heat = int(heat[unknown[:,0], unknown[:,1]].max())
    candidates = unknown[heat[unknown[:,0], unknown[:,1]] == max_heat]

    # Parity preference: for ships length >=2, classic checkerboard works.
    # We also avoid making it too rigid: if none by parity, take any.
    parity_pref = []
    for r, c in candidates:
        if (r + c) % 2 == 0:
            parity_pref.append((int(r), int(c)))
    if parity_pref:
        # Tie-breaker: slightly favor cells adjacent to hits (if any)
        def adj_to_hit(cell):
            r, c = cell
            for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                rr, cc = r+dr, c+dc
                if in_bounds(rr, cc) and B[rr, cc] == 1:
                    return 1
            return 0

        parity_pref.sort(key=adj_to_hit, reverse=True)
        return parity_pref[0]

    # Otherwise pick any candidate, tie-break by adjacency to hits
    cand_list = [(int(r), int(c)) for r, c in candidates]

    def adj_to_hit(cell):
        r, c = cell
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            rr, cc = r+dr, c+dc
            if in_bounds(rr, cc) and B[rrr:=rr, cc] == 1:
                return 1
        return 0

    # Fix for potential typo above (safe recalculation)
    def adj_to_hit(cell):
        r, c = cell
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            rr, cc = r+dr, c+dc
            if 0 <= rr < N and 0 <= cc < N and B[rr, cc] == 1:
                return 1
        return 0

    cand_list.sort(key=adj_to_hit, reverse=True)
    return cand_list[0]
