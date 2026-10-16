
from collections import deque

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Safe fallback: first legal move
    fallback = None
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                fallback = (r, c)
                break
        if fallback is not None:
            break
    if fallback is None:
        return (0, 0)  # should not happen in a valid game

    # Build hit components
    comps, comp_id = _hit_components(board)

    # Score grid
    score = [[0.0 for _ in range(N)] for _ in range(N)]

    # Strong target-mode scoring around hit components
    _add_target_scores(board, comps, score)

    # Probability heatmap from all plausible ship placements
    _add_placement_scores(board, comps, comp_id, score)

    # Slight parity preference in hunt mode / weak-hit situations
    hit_count = sum(1 for r in range(N) for c in range(N) if board[r][c] == 1)
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                if (r + c) % 2 == 0:
                    score[r][c] += 0.15
                # Central cells participate in more placements
                score[r][c] += 0.02 * (4.5 - abs(r - 4.5) + 4.5 - abs(c - 4.5))
                if hit_count == 0 and (r + c) % 2 == 1:
                    score[r][c] -= 0.05

    # Choose best legal move
    best = fallback
    best_score = -10**18
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                s = score[r][c]
                if s > best_score:
                    best_score = s
                    best = (r, c)

    return best


def _hit_components(board):
    comp_id = [[-1] * N for _ in range(N)]
    comps = []
    cid = 0

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and comp_id[r][c] == -1:
                q = deque([(r, c)])
                comp_id[r][c] = cid
                cells = []

                while q:
                    x, y = q.popleft()
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < N and 0 <= ny < N and board[nx][ny] == 1 and comp_id[nx][ny] == -1:
                            comp_id[nx][ny] = cid
                            q.append((nx, ny))

                rows = {x for x, _ in cells}
                cols = {y for _, y in cells}
                if len(rows) == 1 and len(cells) > 1:
                    orient = "H"
                elif len(cols) == 1 and len(cells) > 1:
                    orient = "V"
                else:
                    orient = "S"  # single hit or unusual shape

                comps.append({
                    "cells": cells,
                    "set": set(cells),
                    "orient": orient,
                    "rows": rows,
                    "cols": cols,
                    "min_r": min(x for x, _ in cells),
                    "max_r": max(x for x, _ in cells),
                    "min_c": min(y for _, y in cells),
                    "max_c": max(y for _, y in cells),
                    "size": len(cells),
                })
                cid += 1

    return comps, comp_id


def _add_target_scores(board, comps, score):
    for comp in comps:
        cells = comp["cells"]
        orient = comp["orient"]

        if comp["size"] == 1 or orient == "S":
            # Single hit: prefer 4-neighbors
            r, c = cells[0]
            for dr, dc, w in ((1, 0, 60), (-1, 0, 60), (0, 1, 60), (0, -1, 60)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    score[nr][nc] += w

            # Small bonus for cells two steps away if one-step blocked by boundary/miss
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + 2 * dr, c + 2 * dc
                mr, mc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    if not (0 <= mr < N and 0 <= mc < N) or board[mr][mc] == -1:
                        score[nr][nc] += 5

        elif orient == "H":
            r = next(iter(comp["rows"]))
            left = comp["min_c"] - 1
            right = comp["max_c"] + 1
            if 0 <= left < N and board[r][left] == 0:
                score[r][left] += 120 + 8 * comp["size"]
            if 0 <= right < N and board[r][right] == 0:
                score[r][right] += 120 + 8 * comp["size"]

            # Slightly discourage perpendicular shots near a resolved line
            for _, c in cells:
                for rr in (r - 1, r + 1):
                    if 0 <= rr < N and board[rr][c] == 0:
                        score[rr][c] -= 1.5

        elif orient == "V":
            c = next(iter(comp["cols"]))
            up = comp["min_r"] - 1
            down = comp["max_r"] + 1
            if 0 <= up < N and board[up][c] == 0:
                score[up][c] += 120 + 8 * comp["size"]
            if 0 <= down < N and board[down][c] == 0:
                score[down][c] += 120 + 8 * comp["size"]

            for r, _ in cells:
                for cc in (c - 1, c + 1):
                    if 0 <= cc < N and board[r][cc] == 0:
                        score[r][cc] -= 1.5


def _add_placement_scores(board, comps, comp_id, score):
    for L in SHIP_LENGTHS:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - L + 1):
                cells = [(r, c0 + k) for k in range(L)]
                if not _placement_clear_of_misses(board, cells):
                    continue
                if not _placement_consistent_with_hits(cells, comps, comp_id):
                    continue

                placement_weight = 1.0 + 0.25 * sum(1 for x, y in cells if board[x][y] == 1)
                for x, y in cells:
                    if board[x][y] == 0:
                        score[x][y] += placement_weight

        # Vertical placements
        for r0 in range(N - L + 1):
            for c in range(N):
                cells = [(r0 + k, c) for k in range(L)]
                if not _placement_clear_of_misses(board, cells):
                    continue
                if not _placement_consistent_with_hits(cells, comps, comp_id):
                    continue

                placement_weight = 1.0 + 0.25 * sum(1 for x, y in cells if board[x][y] == 1)
                for x, y in cells:
                    if board[x][y] == 0:
                        score[x][y] += placement_weight


def _placement_clear_of_misses(board, cells):
    for x, y in cells:
        if board[x][y] == -1:
            return False
    return True


def _placement_consistent_with_hits(cells, comps, comp_id):
    cell_set = set(cells)
    touched = set()

    for x, y in cells:
        cid = comp_id[x][y]
        if cid != -1:
            touched.add(cid)

    for cid in touched:
        comp = comps[cid]
        comp_cells = comp["set"]
        orient = comp["orient"]

        # If you touch a known component, you must cover all known hit cells in that component.
        if not comp_cells.issubset(cell_set):
            return False

        # And orientation must match for line components.
        if orient == "H":
            rows = {x for x, _ in cells}
            if len(rows) != 1:
                return False
            if next(iter(comp["rows"])) not in rows:
                return False
        elif orient == "V":
            cols = {y for _, y in cells}
            if len(cols) != 1:
                return False
            if next(iter(comp["cols"])) not in cols:
                return False

    return True
