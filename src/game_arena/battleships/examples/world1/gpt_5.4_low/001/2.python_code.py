
from typing import List, Tuple

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _neighbors(r: int, c: int):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc):
            yield nr, nc


def _find_hit_groups(board: List[List[int]]):
    seen = [[False] * N for _ in range(N)]
    groups = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                group = []
                while stack:
                    x, y = stack.pop()
                    group.append((x, y))
                    for nx, ny in _neighbors(x, y):
                        if board[nx][ny] == 1 and not seen[nx][ny]:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                groups.append(group)
    return groups


def _run_length(board: List[List[int]], r: int, c: int, dr: int, dc: int) -> int:
    """How many consecutive non-miss cells including (r,c) along a line."""
    length = 1
    x, y = r + dr, c + dc
    while _in_bounds(x, y) and board[x][y] != -1:
        length += 1
        x += dr
        y += dc
    x, y = r - dr, c - dc
    while _in_bounds(x, y) and board[x][y] != -1:
        length += 1
        x -= dr
        y -= dc
    return length


def _cell_hunt_score(board: List[List[int]], r: int, c: int) -> int:
    """Local estimate for a candidate cell based on line capacity."""
    if board[r][c] != 0:
        return -1
    horiz = _run_length(board, r, c, 0, 1)
    vert = _run_length(board, r, c, 1, 0)
    score = 0
    for L in SHIP_LENGTHS:
        if horiz >= L:
            score += horiz - L + 1
        if vert >= L:
            score += vert - L + 1
    return score


def _target_candidates(board: List[List[int]]):
    """
    Return high-priority target shots around existing hit groups.
    Produces list of (score, r, c).
    """
    groups = _find_hit_groups(board)
    candidates = {}

    for group in groups:
        rows = {r for r, _ in group}
        cols = {c for _, c in group}

        # Prefer larger groups strongly.
        base_bonus = 1000 + 100 * len(group)

        if len(group) >= 2 and len(rows) == 1:
            # Horizontal group: extend left/right.
            r = next(iter(rows))
            min_c = min(c for _, c in group)
            max_c = max(c for _, c in group)
            for c in (min_c - 1, max_c + 1):
                if _in_bounds(r, c) and board[r][c] == 0:
                    score = base_bonus + 50 + _cell_hunt_score(board, r, c)
                    candidates[(r, c)] = max(candidates.get((r, c), -10**9), score)

        elif len(group) >= 2 and len(cols) == 1:
            # Vertical group: extend up/down.
            c = next(iter(cols))
            min_r = min(r for r, _ in group)
            max_r = max(r for r, _ in group)
            for r in (min_r - 1, max_r + 1):
                if _in_bounds(r, c) and board[r][c] == 0:
                    score = base_bonus + 50 + _cell_hunt_score(board, r, c)
                    candidates[(r, c)] = max(candidates.get((r, c), -10**9), score)

        else:
            # Single-cell hit or irregular cluster: inspect neighbors.
            for r, c in group:
                for nr, nc in _neighbors(r, c):
                    if board[nr][nc] == 0:
                        score = base_bonus + _cell_hunt_score(board, nr, nc)

                        # If this shot aligns with multiple hits, boost it.
                        row_hits = 0
                        col_hits = 0
                        x = nc - 1
                        while x >= 0 and board[nr][x] == 1:
                            row_hits += 1
                            x -= 1
                        x = nc + 1
                        while x < N and board[nr][x] == 1:
                            row_hits += 1
                            x += 1
                        x = nr - 1
                        while x >= 0 and board[x][nc] == 1:
                            col_hits += 1
                            x -= 1
                        x = nr + 1
                        while x < N and board[x][nc] == 1:
                            col_hits += 1
                            x += 1

                        score += 20 * max(row_hits, col_hits)
                        candidates[(nr, nc)] = max(candidates.get((nr, nc), -10**9), score)

    result = [(s, r, c) for (r, c), s in candidates.items()]
    result.sort(reverse=True)
    return result


def _probability_heatmap(board: List[List[int]]):
    """
    Count valid ship placements for all ship lengths.
    A placement is valid if it contains no misses.
    Placements containing hits are rewarded.
    """
    heat = [[0] * N for _ in range(N)]
    any_hits = any(board[r][c] == 1 for r in range(N) for c in range(N))

    for L in SHIP_LENGTHS:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - L + 1):
                cells = [(r, c0 + k) for k in range(L)]
                vals = [board[x][y] for x, y in cells]
                if -1 in vals:
                    continue
                hit_count = sum(1 for v in vals if v == 1)
                placement_weight = 1 + 3 * hit_count
                # If there are known hits on board, slightly prefer placements that touch them.
                if any_hits and hit_count == 0:
                    placement_weight = 1
                for x, y in cells:
                    if board[x][y] == 0:
                        heat[x][y] += placement_weight

        # Vertical placements
        for r0 in range(N - L + 1):
            for c in range(N):
                cells = [(r0 + k, c) for k in range(L)]
                vals = [board[x][y] for x, y in cells]
                if -1 in vals:
                    continue
                hit_count = sum(1 for v in vals if v == 1)
                placement_weight = 1 + 3 * hit_count
                if any_hits and hit_count == 0:
                    placement_weight = 1
                for x, y in cells:
                    if board[x][y] == 0:
                        heat[x][y] += placement_weight

    # Mild parity preference during hunt, but don't suppress target-like positions.
    if not any_hits:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0 and (r + c) % 2 == 0:
                    heat[r][c] += 2

    return heat


def policy(board: List[List[int]]) -> Tuple[int, int]:
    # 1) Immediate target mode around hit groups
    targets = _target_candidates(board)
    if targets:
        for _, r, c in targets:
            if board[r][c] == 0:
                return (r, c)

    # 2) Hunt using probability heatmap
    heat = _probability_heatmap(board)
    best_score = -1
    best_cell = None

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                score = heat[r][c]
                # Tie-break by local line potential.
                score2 = _cell_hunt_score(board, r, c)
                key = (score, score2, -abs(r - 4.5) - abs(c - 4.5))
                if best_cell is None or key > best_key:
                    best_key = key
                    best_score = score
                    best_cell = (r, c)

    if best_cell is not None:
        return best_cell

    # 3) Guaranteed legal fallback
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)

    # Should never happen in a valid game state, but keep API total.
    return (0, 0)
