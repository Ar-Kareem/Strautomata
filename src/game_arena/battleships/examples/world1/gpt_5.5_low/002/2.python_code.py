
from typing import List, Tuple

BOARD_SIZE = 10
SHIP_LENGTHS = (5, 4, 3, 3, 2)


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the next shot as (row, col).

    board values:
      0  = unknown / legal target
     -1  = known miss
      1  = known hit
    """

    n = BOARD_SIZE

    # Collect legal cells and hits.
    unknowns = []
    hits = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                unknowns.append((r, c))
            elif board[r][c] == 1:
                hits.append((r, c))

    # Absolute safety fallback.
    if not unknowns:
        return (0, 0)

    # Score grid.
    score = [[0.0 for _ in range(n)] for _ in range(n)]

    # ------------------------------------------------------------------
    # 1. Probability density from all placements that do not cross misses.
    #    Placements covering known hits are weighted more strongly.
    # ------------------------------------------------------------------
    for length in SHIP_LENGTHS:
        # Horizontal placements.
        for r in range(n):
            for c0 in range(n - length + 1):
                cells = [(r, c0 + k) for k in range(length)]

                blocked = False
                hit_count = 0
                unknown_count = 0

                for rr, cc in cells:
                    v = board[rr][cc]
                    if v == -1:
                        blocked = True
                        break
                    elif v == 1:
                        hit_count += 1
                    else:
                        unknown_count += 1

                if blocked or unknown_count == 0:
                    continue

                # Strongly value placements that explain existing hits.
                weight = 1.0
                if hit_count:
                    weight += 8.0 * hit_count * hit_count

                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += weight

        # Vertical placements.
        for r0 in range(n - length + 1):
            for c in range(n):
                cells = [(r0 + k, c) for k in range(length)]

                blocked = False
                hit_count = 0
                unknown_count = 0

                for rr, cc in cells:
                    v = board[rr][cc]
                    if v == -1:
                        blocked = True
                        break
                    elif v == 1:
                        hit_count += 1
                    else:
                        unknown_count += 1

                if blocked or unknown_count == 0:
                    continue

                weight = 1.0
                if hit_count:
                    weight += 8.0 * hit_count * hit_count

                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += weight

    # ------------------------------------------------------------------
    # 2. Explicit target mode for connected hit clusters.
    #    Continue along a known direction when possible.
    # ------------------------------------------------------------------
    seen = set()
    hit_set = set(hits)

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < n and 0 <= c < n

    for start in hits:
        if start in seen:
            continue

        # BFS connected component of hits.
        stack = [start]
        seen.add(start)
        cluster = []

        while stack:
            r, c = stack.pop()
            cluster.append((r, c))

            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if (nr, nc) in hit_set and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))

        rows = {r for r, _ in cluster}
        cols = {c for _, c in cluster}

        # If the cluster has a clear orientation, heavily score extensions.
        if len(cluster) >= 2 and len(rows) == 1:
            r = next(iter(rows))
            cs = sorted(c for _, c in cluster)
            left = (r, cs[0] - 1)
            right = (r, cs[-1] + 1)

            for rr, cc in (left, right):
                if in_bounds(rr, cc) and board[rr][cc] == 0:
                    score[rr][cc] += 1000.0 + 100.0 * len(cluster)

        elif len(cluster) >= 2 and len(cols) == 1:
            c = next(iter(cols))
            rs = sorted(r for r, _ in cluster)
            up = (rs[0] - 1, c)
            down = (rs[-1] + 1, c)

            for rr, cc in (up, down):
                if in_bounds(rr, cc) and board[rr][cc] == 0:
                    score[rr][cc] += 1000.0 + 100.0 * len(cluster)

        else:
            # Isolated hit or irregular cluster: try all orthogonal neighbors.
            for r, c in cluster:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 0:
                        score[nr][nc] += 650.0

    # ------------------------------------------------------------------
    # 3. Hunt-mode refinements: parity and center preference.
    # ------------------------------------------------------------------
    any_active_neighbor = False
    for r, c in hits:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and board[nr][nc] == 0:
                any_active_neighbor = True
                break
        if any_active_neighbor:
            break

    for r, c in unknowns:
        # Checkerboard parity is useful while searching because every ship
        # of length >= 2 touches at least one square of each parity.
        if not any_active_neighbor:
            if (r + c) % 2 == 0:
                score[r][c] += 2.5

        # Mild center bias.
        center_dist = abs(r - 4.5) + abs(c - 4.5)
        score[r][c] += (9.0 - center_dist) * 0.05

    # ------------------------------------------------------------------
    # 4. Choose the best legal cell. Deterministic tie-breaker.
    # ------------------------------------------------------------------
    best_cell = unknowns[0]
    best_score = score[best_cell[0]][best_cell[1]]

    for r, c in unknowns:
        s = score[r][c]

        if s > best_score:
            best_score = s
            best_cell = (r, c)
        elif s == best_score:
            # Prefer more central cells on exact ties.
            old_center = abs(best_cell[0] - 4.5) + abs(best_cell[1] - 4.5)
            new_center = abs(r - 4.5) + abs(c - 4.5)
            if new_center < old_center:
                best_cell = (r, c)

    # Final legality guard.
    br, bc = best_cell
    if 0 <= br < n and 0 <= bc < n and board[br][bc] == 0:
        return best_cell

    # Guaranteed legal fallback.
    return unknowns[0]
