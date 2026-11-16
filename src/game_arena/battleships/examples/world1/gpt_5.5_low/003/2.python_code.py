
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    N = 10
    SHIPS = [5, 4, 3, 3, 2]

    # Safety fallback: collect all legal moves.
    unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknowns:
        return (0, 0)

    hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]
    hit_set = set(hits)

    score = [[0.0 for _ in range(N)] for _ in range(N)]

    # ------------------------------------------------------------------
    # Probability density over all ship placements consistent with misses.
    # Placements containing known hits are weighted heavily.
    # ------------------------------------------------------------------
    for length in SHIPS:
        # Horizontal placements
        for r in range(N):
            for c in range(N - length + 1):
                cells = [(r, c + k) for k in range(length)]

                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                hit_count = sum(1 for rr, cc in cells if board[rr][cc] == 1)

                # Base weight for possible ship placement.
                # Strongly increase if it explains known hits.
                weight = 1.0
                if hit_count:
                    weight += 35.0 * hit_count * hit_count

                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += weight

        # Vertical placements
        for r in range(N - length + 1):
            for c in range(N):
                cells = [(r + k, c) for k in range(length)]

                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                hit_count = sum(1 for rr, cc in cells if board[rr][cc] == 1)

                weight = 1.0
                if hit_count:
                    weight += 35.0 * hit_count * hit_count

                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += weight

    # ------------------------------------------------------------------
    # Tactical target mode around connected hit clusters.
    # This helps finish ships quickly once we have a hit.
    # ------------------------------------------------------------------
    seen = set()

    for start in hits:
        if start in seen:
            continue

        # BFS connected component of hits.
        stack = [start]
        seen.add(start)
        comp = []

        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 1 and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))

        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}

        # If a cluster is horizontal, prioritize its two ends.
        if len(rows) == 1 and len(comp) >= 2:
            r = next(iter(rows))
            min_c = min(c for _, c in comp)
            max_c = max(c for _, c in comp)

            for nc in (min_c - 1, max_c + 1):
                if 0 <= nc < N and board[r][nc] == 0:
                    score[r][nc] += 1000.0 + 100.0 * len(comp)

        # If a cluster is vertical, prioritize its two ends.
        elif len(cols) == 1 and len(comp) >= 2:
            c = next(iter(cols))
            min_r = min(r for r, _ in comp)
            max_r = max(r for r, _ in comp)

            for nr in (min_r - 1, max_r + 1):
                if 0 <= nr < N and board[nr][c] == 0:
                    score[nr][c] += 1000.0 + 100.0 * len(comp)

        # Single isolated hit: try all four neighbors.
        else:
            for r, c in comp:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                        score[nr][nc] += 550.0

    # ------------------------------------------------------------------
    # Hunt-mode parity bias.
    # Since the smallest ship has length 2, checkerboard parity is useful.
    # The probability density remains dominant.
    # ------------------------------------------------------------------
    for r, c in unknowns:
        if (r + c) % 2 == 0:
            score[r][c] += 0.25

        # Mild centrality preference as a tie-breaker.
        center_dist = abs(r - 4.5) + abs(c - 4.5)
        score[r][c] += (9.0 - center_dist) * 0.01

    # Choose the highest-scoring legal unknown cell.
    best = unknowns[0]
    best_score = score[best[0]][best[1]]

    for r, c in unknowns[1:]:
        s = score[r][c]
        if s > best_score:
            best_score = s
            best = (r, c)

    return best
