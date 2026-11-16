
# Battleship policy for a 10x10 board.
# Required API:
#   policy(board: list[list[int]]) -> tuple[int, int]

from typing import List, Tuple, Set


BOARD_SIZE = 10
FLEET = [5, 4, 3, 3, 2]
FLEET_LENGTHS = set(FLEET)


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the next legal shot as (row, col), where board[row][col] == 0.

    board values:
      0  unknown
     -1  miss
      1  hit
    """

    n = BOARD_SIZE

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < n and 0 <= c < n

    unknowns = [(r, c) for r in range(n) for c in range(n) if board[r][c] == 0]
    if not unknowns:
        # Should not occur in normal play, but keep the API total.
        return (0, 0)

    hits = {(r, c) for r in range(n) for c in range(n) if board[r][c] == 1}

    # ------------------------------------------------------------
    # Heuristic sunk/resolved detection.
    # If a straight contiguous run of hits has blocked ends and no
    # perpendicular hit branches, it is probably a completed ship.
    # We then avoid treating those cells as active targets.
    # ------------------------------------------------------------
    resolved: Set[Tuple[int, int]] = set()

    def is_blocked(r: int, c: int) -> bool:
        return not in_bounds(r, c) or board[r][c] != 0

    # Horizontal runs
    for r in range(n):
        c = 0
        while c < n:
            if board[r][c] != 1:
                c += 1
                continue
            start = c
            while c < n and board[r][c] == 1:
                c += 1
            end = c - 1
            length = end - start + 1

            if length >= 2:
                left_blocked = is_blocked(r, start - 1)
                right_blocked = is_blocked(r, end + 1)

                clean = True
                for cc in range(start, end + 1):
                    if (in_bounds(r - 1, cc) and board[r - 1][cc] == 1) or (
                        in_bounds(r + 1, cc) and board[r + 1][cc] == 1
                    ):
                        clean = False
                        break

                if clean and (length == 5 or (length in FLEET_LENGTHS and left_blocked and right_blocked)):
                    for cc in range(start, end + 1):
                        resolved.add((r, cc))

    # Vertical runs
    for c in range(n):
        r = 0
        while r < n:
            if board[r][c] != 1:
                r += 1
                continue
            start = r
            while r < n and board[r][c] == 1:
                r += 1
            end = r - 1
            length = end - start + 1

            if length >= 2:
                up_blocked = is_blocked(start - 1, c)
                down_blocked = is_blocked(end + 1, c)

                clean = True
                for rr in range(start, end + 1):
                    if (in_bounds(rr, c - 1) and board[rr][c - 1] == 1) or (
                        in_bounds(rr, c + 1) and board[rr][c + 1] == 1
                    ):
                        clean = False
                        break

                if clean and (length == 5 or (length in FLEET_LENGTHS and up_blocked and down_blocked)):
                    for rr in range(start, end + 1):
                        resolved.add((rr, c))

    active_hits = hits - resolved

    # Remove active hits that cannot belong to any still-extendable placement.
    # This prevents isolated fully boxed-in hits from dominating forever.
    possibly_active = set()
    for hr, hc in active_hits:
        can_extend = False
        for L in FLEET:
            for start_c in range(hc - L + 1, hc + 1):
                if 0 <= start_c and start_c + L <= n:
                    cells = [(hr, cc) for cc in range(start_c, start_c + L)]
                    if all(board[rr][cc] != -1 and (rr, cc) not in resolved for rr, cc in cells):
                        if any(board[rr][cc] == 0 for rr, cc in cells):
                            can_extend = True
                            break
            if can_extend:
                break
            for start_r in range(hr - L + 1, hr + 1):
                if 0 <= start_r and start_r + L <= n:
                    cells = [(rr, hc) for rr in range(start_r, start_r + L)]
                    if all(board[rr][cc] != -1 and (rr, cc) not in resolved for rr, cc in cells):
                        if any(board[rr][cc] == 0 for rr, cc in cells):
                            can_extend = True
                            break
            if can_extend:
                break
        if can_extend:
            possibly_active.add((hr, hc))

    active_hits = possibly_active

    score = [[0.0 for _ in range(n)] for _ in range(n)]

    # ------------------------------------------------------------
    # Probability density over all valid ship placements.
    # Placements containing active hits are weighted heavily.
    # ------------------------------------------------------------
    for L in FLEET:
        # Horizontal placements
        for r in range(n):
            for c0 in range(n - L + 1):
                cells = [(r, c) for c in range(c0, c0 + L)]

                if any(board[rr][cc] == -1 or (rr, cc) in resolved for rr, cc in cells):
                    continue

                hit_cells = [cell for cell in cells if cell in active_hits]
                unknown_cells = [cell for cell in cells if board[cell[0]][cell[1]] == 0]
                if not unknown_cells:
                    continue

                h = len(hit_cells)
                if h:
                    # Strong target score. More known hits in the same legal line
                    # makes the remaining cells much more attractive.
                    base = (220.0 * h * h + 25.0 * L) / max(1, len(unknown_cells))
                    for ur, uc in unknown_cells:
                        dist = min(abs(uc - hc) for _, hc in hit_cells)
                        score[ur][uc] += base / max(1, dist)
                else:
                    # Hunt score. Larger ships occupy more cells, but every fleet
                    # member is represented by iterating over FLEET, including the
                    # duplicate length-3 ship.
                    base = 1.0 + 0.20 * L
                    for ur, uc in unknown_cells:
                        score[ur][uc] += base

        # Vertical placements
        for c in range(n):
            for r0 in range(n - L + 1):
                cells = [(r, c) for r in range(r0, r0 + L)]

                if any(board[rr][cc] == -1 or (rr, cc) in resolved for rr, cc in cells):
                    continue

                hit_cells = [cell for cell in cells if cell in active_hits]
                unknown_cells = [cell for cell in cells if board[cell[0]][cell[1]] == 0]
                if not unknown_cells:
                    continue

                h = len(hit_cells)
                if h:
                    base = (220.0 * h * h + 25.0 * L) / max(1, len(unknown_cells))
                    for ur, uc in unknown_cells:
                        dist = min(abs(ur - hr) for hr, _ in hit_cells)
                        score[ur][uc] += base / max(1, dist)
                else:
                    base = 1.0 + 0.20 * L
                    for ur, uc in unknown_cells:
                        score[ur][uc] += base

    # ------------------------------------------------------------
    # Extra target-mode bonuses.
    # Fill gaps between aligned hits and extend hit runs.
    # ------------------------------------------------------------
    if active_hits:
        # Neighbor bonus for isolated or uncertain hits.
        for r, c in active_hits:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if in_bounds(rr, cc) and board[rr][cc] == 0:
                    score[rr][cc] += 600.0

        # Horizontal aligned-hit bonuses.
        for r in range(n):
            cols = [c for (rr, c) in active_hits if rr == r]
            cols.sort()

            # Consecutive runs.
            i = 0
            while i < len(cols):
                j = i
                while j + 1 < len(cols) and cols[j + 1] == cols[j] + 1:
                    j += 1
                run_len = j - i + 1
                if run_len >= 2:
                    left = cols[i] - 1
                    right = cols[j] + 1
                    if in_bounds(r, left) and board[r][left] == 0 and run_len < 5:
                        score[r][left] += 5000.0 + 500.0 * run_len
                    if in_bounds(r, right) and board[r][right] == 0 and run_len < 5:
                        score[r][right] += 5000.0 + 500.0 * run_len
                i = j + 1

            # Gaps between hits in the same row.
            for a in range(len(cols)):
                for b in range(a + 1, len(cols)):
                    c1, c2 = cols[a], cols[b]
                    span = c2 - c1 + 1
                    if span > 5:
                        break
                    between = [(r, c) for c in range(c1 + 1, c2)]
                    if between and all(board[rr][cc] != -1 and (rr, cc) not in resolved for rr, cc in between):
                        for rr, cc in between:
                            if board[rr][cc] == 0:
                                score[rr][cc] += 8000.0

        # Vertical aligned-hit bonuses.
        for c in range(n):
            rows = [r for (r, cc) in active_hits if cc == c]
            rows.sort()

            # Consecutive runs.
            i = 0
            while i < len(rows):
                j = i
                while j + 1 < len(rows) and rows[j + 1] == rows[j] + 1:
                    j += 1
                run_len = j - i + 1
                if run_len >= 2:
                    up = rows[i] - 1
                    down = rows[j] + 1
                    if in_bounds(up, c) and board[up][c] == 0 and run_len < 5:
                        score[up][c] += 5000.0 + 500.0 * run_len
                    if in_bounds(down, c) and board[down][c] == 0 and run_len < 5:
                        score[down][c] += 5000.0 + 500.0 * run_len
                i = j + 1

            # Gaps between hits in the same column.
            for a in range(len(rows)):
                for b in range(a + 1, len(rows)):
                    r1, r2 = rows[a], rows[b]
                    span = r2 - r1 + 1
                    if span > 5:
                        break
                    between = [(r, c) for r in range(r1 + 1, r2)]
                    if between and all(board[rr][cc] != -1 and (rr, cc) not in resolved for rr, cc in between):
                        for rr, cc in between:
                            if board[rr][cc] == 0:
                                score[rr][cc] += 8000.0

    # ------------------------------------------------------------
    # Small hunt-mode refinements:
    # - checkerboard bias is useful because all ships have length >= 2
    # - slight center preference breaks ties sensibly
    # ------------------------------------------------------------
    for r, c in unknowns:
        if not active_hits and (r + c) % 2 == 0:
            score[r][c] += 0.35

        # Center cells participate in more placements on an empty board.
        center_bias = 9.0 - (abs(r - 4.5) + abs(c - 4.5))
        score[r][c] += 0.01 * center_bias

    # Pick the highest-scoring legal unknown cell.
    best = None
    best_score = float("-inf")

    for r, c in unknowns:
        s = score[r][c]
        if s > best_score:
            best_score = s
            best = (r, c)

    if best is not None and board[best[0]][best[1]] == 0:
        return best

    # Absolute safety fallback.
    return unknowns[0]
