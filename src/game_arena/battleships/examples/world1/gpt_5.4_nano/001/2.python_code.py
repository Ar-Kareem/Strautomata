
from typing import Tuple, List
import random

def policy(board: List[List[int]]) -> Tuple[int, int]:
    N = 10

    def inb(r, c):
        return 0 <= r < N and 0 <= c < N

    # Collect hit cells
    hits = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                hits.append((r, c))

    # Helpers to check if a cell is valid (unshot)
    def is_unknown(r, c):
        return board[r][c] == 0

    # Determine remaining ship sizes (standard fleet)
    ships = [5, 4, 3, 3, 2]

    # If we have hits, enter target mode
    if hits:
        # If multiple hits exist, infer orientation if possible
        rows = sorted(set(r for r, _ in hits))
        cols = sorted(set(c for _, c in hits))

        # Candidate directions
        candidates = []

        def add_continuations(dr, dc):
            # Given a direction, find min/max extent of current hit cluster projection
            rs = [r for r, c in hits]
            cs = [c for r, c in hits]
            # Determine extremes along that direction by checking along vector
            # We'll just walk from each hit and extend if contiguous hits exist, then pick the first unknown beyond.
            # But to avoid duplicates, gather all possible endpoint moves.
            seen = set()
            for r, c in hits:
                # Backward endpoint
                br, bc = r - dr, c - dc
                if inb(br, bc) and is_unknown(br, bc):
                    seen.add((br, bc))
                # Forward endpoint
                fr, fc = r + dr, c + dc
                if inb(fr, fc) and is_unknown(fr, fc):
                    seen.add((fr, fc))
            for cell in seen:
                candidates.append(cell)

        # If hits span same row -> horizontal, same col -> vertical; else both possible
        if len(rows) == 1 and len(cols) >= 1:
            add_continuations(0, 1)
        elif len(cols) == 1 and len(rows) >= 1:
            add_continuations(1, 0)
        else:
            # Orientation uncertain: try both directions, later we will score via local plausibility
            add_continuations(0, 1)
            add_continuations(1, 0)

        # Score candidates using local line plausibility: how many ship placements could cover them
        # considering that -1 cannot be part of any ship.
        # We'll compute a placement-count score on candidate cells only.
        miss = set()
        for r in range(N):
            for c in range(N):
                if board[r][c] == -1:
                    miss.add((r, c))
        hit_set = set(hits)

        def score_cell(r0, c0):
            score = 0
            for size in ships:
                # Horizontal segments containing (r0,c0)
                for start_c in range(c0 - size + 1, c0 + 1):
                    end_c = start_c + size - 1
                    if start_c < 0 or end_c >= N:
                        continue
                    # Segment cells
                    ok = True
                    must_cover_hit = False
                    for cc in range(start_c, end_c + 1):
                        if (r0, cc) in miss:
                            ok = False
                            break
                        if (r0, cc) in hit_set:
                            must_cover_hit = True
                    # In target mode we prefer placements consistent with existing hits; if no hits in this segment, allow but with low score
                    if not ok:
                        continue
                    if must_cover_hit:
                        score += 4
                    else:
                        score += 1

                # Vertical segments containing (r0,c0)
                for start_r in range(r0 - size + 1, r0 + 1):
                    end_r = start_r + size - 1
                    if start_r < 0 or end_r >= N:
                        continue
                    ok = True
                    must_cover_hit = False
                    for rr in range(start_r, end_r + 1):
                        if (rr, c0) in miss:
                            ok = False
                            break
                        if (rr, c0) in hit_set:
                            must_cover_hit = True
                    if not ok:
                        continue
                    if must_cover_hit:
                        score += 4
                    else:
                        score += 1
            return score

        # Filter candidates to unknown only
        candidates = [cell for cell in candidates if is_unknown(*cell)]
        if candidates:
            best_score = -1
            best_cells = []
            for (r, c) in candidates:
                s = score_cell(r, c)
                if s > best_score:
                    best_score = s
                    best_cells = [(r, c)]
                elif s == best_score:
                    best_cells.append((r, c))
            # break ties randomly for safety
            return random.choice(best_cells)

    # Hunt mode: build heatmap by counting placements of remaining ships for each cell
    miss = [[board[r][c] == -1 for c in range(N)] for r in range(N)]
    # Determine parity weighting (checkerboard)
    # We'll still allow any cell if heatmap dictates, but parity gives a strong prior.
    heat = [[0 for _ in range(N)] for _ in range(N)]

    # Precompute hit_set for forcing consistency
    hit_set = set((r, c) for r in range(N) for c in range(N) if board[r][c] == 1)

    # For each ship size, count all placements consistent with current board
    for size in ships:
        # Horizontal placements
        for r in range(N):
            for start_c in range(N - size + 1):
                end_c = start_c + size - 1
                # Check consistency: no misses in segment
                segment_miss = False
                segment_hits = 0
                for c in range(start_c, end_c + 1):
                    if miss[r][c]:
                        segment_miss = True
                        break
                    if (r, c) in hit_set:
                        segment_hits += 1
                if segment_miss:
                    continue
                # If there are existing hits, we should only consider placements that cover at least one hit,
                # but in hunt mode hits list is empty, so this condition doesn't restrict.
                for c in range(start_c, end_c + 1):
                    if board[r][c] == 0:
                        # Score with segment_hits bias (0 anyway if no hits)
                        heat[r][c] += (3 if segment_hits > 0 else 1)
        # Vertical placements
        for c in range(N):
            for start_r in range(N - size + 1):
                end_r = start_r + size - 1
                segment_miss = False
                segment_hits = 0
                for r in range(start_r, end_r + 1):
                    if miss[r][c]:
                        segment_miss = True
                        break
                    if (r, c) in hit_set:
                        segment_hits += 1
                if segment_miss:
                    continue
                for r in range(start_r, end_r + 1):
                    if board[r][c] == 0:
                        heat[r][c] += (3 if segment_hits > 0 else 1)

    # Apply parity and slight edge/corner smoothing
    best = None
    best_val = -10**9
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            val = heat[r][c]
            # Checkerboard prior
            if (r + c) % 2 == 0:
                val *= 1.05
            else:
                val *= 0.95
            # Small preference away from extreme edges (often irrelevant but helps break ties)
            dist = min(r, N-1-r, c, N-1-c)
            val += 0.01 * dist
            if val > best_val:
                best_val = val
                best = (r, c)

    # Fallback if something went wrong: choose any unknown cell
    if best is None:
        unknown = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        return random.choice(unknown)

    return best
