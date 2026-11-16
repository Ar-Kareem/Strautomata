
from typing import List, Tuple
from collections import deque

SHIP_LENGTHS = (5, 4, 3, 3, 2)
N = 10


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Return the next Battleship shot as (row, col).

    board values:
      0  = unknown / unshot
      -1 = miss
      1  = hit
    """

    # Defensive fallback in case the arena gives an unexpected board.
    try:
        unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    except Exception:
        return (0, 0)

    if not unknowns:
        return (0, 0)

    hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]

    # ------------------------------------------------------------------
    # Build a general probability heat map from all placements that do
    # not contradict known misses.
    # ------------------------------------------------------------------
    heat = [[0.0 for _ in range(N)] for _ in range(N)]

    for length in SHIP_LENGTHS:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - length + 1):
                cells = [(r, c0 + k) for k in range(length)]
                if any(board[r][c] == -1 for r, c in cells):
                    continue

                hit_count = sum(1 for r, c in cells if board[r][c] == 1)

                # Placements that include known hits are much more important.
                weight = 1.0 + 7.5 * hit_count + 4.0 * hit_count * hit_count

                for r, c in cells:
                    if board[r][c] == 0:
                        heat[r][c] += weight

        # Vertical placements
        for r0 in range(N - length + 1):
            for c in range(N):
                cells = [(r0 + k, c) for k in range(length)]
                if any(board[r][c] == -1 for r, c in cells):
                    continue

                hit_count = sum(1 for r, c in cells if board[r][c] == 1)
                weight = 1.0 + 7.5 * hit_count + 4.0 * hit_count * hit_count

                for r, c in cells:
                    if board[r][c] == 0:
                        heat[r][c] += weight

    # ------------------------------------------------------------------
    # Target mode: find connected hit clusters and strongly prioritize
    # shots that extend them.
    # ------------------------------------------------------------------
    if hits:
        visited = set()
        clusters = []

        for start in hits:
            if start in visited:
                continue

            q = deque([start])
            visited.add(start)
            cluster = []

            while q:
                r, c = q.popleft()
                cluster.append((r, c))

                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if (
                        0 <= nr < N
                        and 0 <= nc < N
                        and board[nr][nc] == 1
                        and (nr, nc) not in visited
                    ):
                        visited.add((nr, nc))
                        q.append((nr, nc))

            clusters.append(cluster)

        target_scores = {}

        for cluster in clusters:
            rows = {r for r, _ in cluster}
            cols = {c for _, c in cluster}
            size = len(cluster)

            candidate_dirs = []

            if size >= 2 and len(rows) == 1:
                # Horizontal ship segment discovered.
                r = next(iter(rows))
                min_c = min(c for _, c in cluster)
                max_c = max(c for _, c in cluster)
                candidate_dirs.append((r, min_c - 1, 0, -1, 130.0 + 20.0 * size))
                candidate_dirs.append((r, max_c + 1, 0, 1, 130.0 + 20.0 * size))

            elif size >= 2 and len(cols) == 1:
                # Vertical ship segment discovered.
                c = next(iter(cols))
                min_r = min(r for r, _ in cluster)
                max_r = max(r for r, _ in cluster)
                candidate_dirs.append((min_r - 1, c, -1, 0, 130.0 + 20.0 * size))
                candidate_dirs.append((max_r + 1, c, 1, 0, 130.0 + 20.0 * size))

            else:
                # Single hit or irregular cluster: try all orthogonal neighbors.
                for r, c in cluster:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        candidate_dirs.append((r + dr, c + dc, dr, dc, 90.0 + 10.0 * size))

            for r, c, dr, dc, base in candidate_dirs:
                if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
                    # Estimate available run length through this candidate.
                    # More open space means it is more likely to fit a ship.
                    span = 1

                    rr, cc = r + dr, c + dc
                    while 0 <= rr < N and 0 <= cc < N and board[rr][cc] != -1:
                        span += 1
                        rr += dr
                        cc += dc

                    rr, cc = r - dr, c - dc
                    while 0 <= rr < N and 0 <= cc < N and board[rr][cc] != -1:
                        span += 1
                        rr -= dr
                        cc -= dc

                    score = base + heat[r][c] + 2.0 * span
                    if (r, c) not in target_scores or score > target_scores[(r, c)]:
                        target_scores[(r, c)] = score

        if target_scores:
            return max(
                target_scores,
                key=lambda x: (
                    target_scores[x],
                    heat[x[0]][x[1]],
                    -abs(x[0] - 4.5) - abs(x[1] - 4.5),
                    -x[0],
                    -x[1],
                ),
            )

    # ------------------------------------------------------------------
    # Hunt mode: use heat map, checkerboard parity, and center preference.
    # ------------------------------------------------------------------
    best_cell = None
    best_score = -10**18

    for r, c in unknowns:
        score = heat[r][c]

        # Checkerboard parity is efficient while ships of length >= 2 remain.
        if (r + c) % 2 == 0:
            score += 2.5

        # Mild center bias. Central cells participate in more placements.
        score += 0.15 * (9.0 - abs(r - 4.5) - abs(c - 4.5))

        # Deterministic tie-breaking.
        tie = -0.001 * (r * 10 + c)
        score += tie

        if score > best_score:
            best_score = score
            best_cell = (r, c)

    if best_cell is not None:
        return best_cell

    # Absolute legal fallback.
    return unknowns[0]
