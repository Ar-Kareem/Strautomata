
from typing import List, Tuple

# Battleship targeting policy for 10x10 grid.
# Board encoding:
#   0 = unknown (not fired)
#  -1 = miss
#   1 = hit
#
# Strategy:
# - Compute a probability/heat map by enumerating all legal placements of each ship length
#   consistent with known misses. If there are any hits, only count placements that
#   include at least one hit (targeting mode). Otherwise use all placements (hunting mode).
# - Choose the unknown cell with highest score. Tie-break deterministically by row,col.
# - If no placement yields any score (rare), pick an unknown neighbor of a hit if possible,
#   else pick an unknown cell closest to board center (deterministic).
#
# Ships lengths: standard fleet [5,4,3,3,2]


def policy(board: List[List[int]]) -> Tuple[int, int]:
    n = len(board)
    # Standard fleet
    ships = [5, 4, 3, 3, 2]

    # Collect unknowns and whether there are any hits
    unknowns = []
    hits = []
    for r in range(n):
        for c in range(n):
            v = board[r][c]
            if v == 0:
                unknowns.append((r, c))
            elif v == 1:
                hits.append((r, c))

    if not unknowns:
        # No moves left; return something valid
        return 0, 0

    # Helper to check bounds
    def in_bounds(r, c):
        return 0 <= r < n and 0 <= c < n

    # Heat map initialization
    heat = [[0 for _ in range(n)] for _ in range(n)]

    has_hits = len(hits) > 0

    # Enumerate placements for each ship length
    for L in ships:
        # Horizontal (dr=0, dc=1) and Vertical (dr=1, dc=0)
        for dr, dc in ((0, 1), (1, 0)):
            # scanning start positions
            for r in range(n):
                for c in range(n):
                    # build cells of placement
                    cells = []
                    for k in range(L):
                        rr = r + k * dr
                        cc = c + k * dc
                        if not in_bounds(rr, cc):
                            break
                        cells.append((rr, cc))
                    if len(cells) != L:
                        continue
                    # Check placement validity: cannot include any known miss (-1)
                    invalid = False
                    includes_hit = False
                    for (rr, cc) in cells:
                        if board[rr][cc] == -1:
                            invalid = True
                            break
                        if board[rr][cc] == 1:
                            includes_hit = True
                    if invalid:
                        continue
                    # If there are hits anywhere, require that this placement covers at least one hit.
                    # This focuses probability around hits (target mode).
                    if has_hits and not includes_hit:
                        continue
                    # Valid placement: increment heat for unknown cells in placement
                    for (rr, cc) in cells:
                        if board[rr][cc] == 0:
                            heat[rr][cc] += 1

    # Find best unknown cell by heat
    best = None
    best_score = -1
    for (r, c) in unknowns:
        s = heat[r][c]
        if s > best_score or (s == best_score and (best is not None and (r, c) < best)):
            best_score = s
            best = (r, c)

    # If we found a scored cell (score > 0), choose it
    if best_score > 0 and best is not None:
        return best

    # If no placements produced heat (possible due to restrictive misses), try neighbor-of-hit heuristic:
    if has_hits:
        # For each hit, consider its 4-neighbors that are unknown; score them by adjacency to hits
        cand_scores = {}
        for (hr, hc) in hits:
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                rr, cc = hr + dr, hc + dc
                if not in_bounds(rr, cc):
                    continue
                if board[rr][cc] != 0:
                    continue
                # score neighbor by how many contiguous hits in that direction (favor extending lines)
                score = 0
                # count same-direction hits from this neighbor outward
                # check backward from neighbor towards the hit and forward
                # backward
                br, bc = rr - dr, cc - dc
                if in_bounds(br, bc) and board[br][bc] == 1:
                    score += 2
                # forward
                fr, fc = rr + dr, cc + dc
                if in_bounds(fr, fc) and board[fr][fc] == 1:
                    score += 2
                # adjacency to any hit
                for adr, adc in ((-1,0),(1,0),(0,-1),(0,1)):
                    ar, ac = rr + adr, cc + adc
                    if in_bounds(ar, ac) and board[ar][ac] == 1:
                        score += 1
                # fewer misses around preferred
                miss_count = 0
                for adr, adc in ((-1,0),(1,0),(0,-1),(0,1)):
                    ar, ac = rr + adr, cc + adc
                    if in_bounds(ar, ac) and board[ar][ac] == -1:
                        miss_count += 1
                score -= miss_count
                cand_scores[(rr, cc)] = max(cand_scores.get((rr, cc), 0), score)
        if cand_scores:
            # choose candidate with highest score, deterministic tie-breaker
            best_cell = None
            best_val = -10**9
            for cell, val in cand_scores.items():
                if val > best_val or (val == best_val and (best_cell is not None and cell < best_cell)):
                    best_val = val
                    best_cell = cell
            if best_cell is not None:
                return best_cell

    # Last fallback: choose unknown cell closest to center (deterministic). Break ties by row,col.
    center = ( (n-1)/2.0, (n-1)/2.0 )
    best_cell = None
    best_dist = None
    for (r, c) in unknowns:
        dist = (r - center[0])**2 + (c - center[1])**2
        if best_cell is None or dist < best_dist or (dist == best_dist and (r, c) < best_cell):
            best_cell = (r, c)
            best_dist = dist
    return best_cell
