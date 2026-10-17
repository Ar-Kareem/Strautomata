
from typing import List, Tuple

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10

def policy(board: List[List[int]]) -> Tuple[int, int]:
    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < N and 0 <= c < N

    def unknown_cells():
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    yield (r, c)

    def first_legal():
        for r, c in unknown_cells():
            return (r, c)
        return (0, 0)

    # Collect hit components
    visited = [[False] * N for _ in range(N)]
    hit_groups = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not visited[r][c]:
                stack = [(r, c)]
                visited[r][c] = True
                group = []
                while stack:
                    x, y = stack.pop()
                    group.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny) and not visited[nx][ny] and board[nx][ny] == 1:
                            visited[nx][ny] = True
                            stack.append((nx, ny))
                hit_groups.append(group)

    # Target mode: prioritize finishing discovered ships
    target_scores = [[0.0] * N for _ in range(N)]

    for group in hit_groups:
        if not group:
            continue

        rows = {r for r, _ in group}
        cols = {c for _, c in group}

        if len(group) == 1:
            r, c = group[0]
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and board[nr][nc] == 0:
                    target_scores[nr][nc] += 50.0
        elif len(rows) == 1:
            # Horizontal group
            r = next(iter(rows))
            min_c = min(c for _, c in group)
            max_c = max(c for _, c in group)

            if in_bounds(r, min_c - 1) and board[r][min_c - 1] == 0:
                target_scores[r][min_c - 1] += 100.0
            if in_bounds(r, max_c + 1) and board[r][max_c + 1] == 0:
                target_scores[r][max_c + 1] += 100.0

            # Slightly prefer cells aligned with this ship
            for c in range(min_c - 2, max_c + 3):
                if in_bounds(r, c) and board[r][c] == 0:
                    target_scores[r][c] += 5.0
        elif len(cols) == 1:
            # Vertical group
            c = next(iter(cols))
            min_r = min(r for r, _ in group)
            max_r = max(r for r, _ in group)

            if in_bounds(min_r - 1, c) and board[min_r - 1][c] == 0:
                target_scores[min_r - 1][c] += 100.0
            if in_bounds(max_r + 1, c) and board[max_r + 1][c] == 0:
                target_scores[max_r + 1][c] += 100.0

            for r in range(min_r - 2, max_r + 3):
                if in_bounds(r, c) and board[r][c] == 0:
                    target_scores[r][c] += 5.0
        else:
            # If somehow an irregular hit pattern exists, target all adjacent unknowns
            for r, c in group:
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if in_bounds(nr, nc) and board[nr][nc] == 0:
                        target_scores[nr][nc] += 40.0

    # If we have target candidates, combine with probability map and choose best
    prob = [[0.0] * N for _ in range(N)]

    # Probability map from all ship placements consistent with misses/hits
    for L in SHIP_LENGTHS:
        # Horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                cells = [(r, c + k) for k in range(L)]
                # Cannot include known misses
                if any(board[x][y] == -1 for x, y in cells):
                    continue
                # Placements cannot pass through already-fired non-ship unknown? only misses matter;
                # hits are allowed and encouraged.
                hit_count = sum(1 for x, y in cells if board[x][y] == 1)
                weight = 1.0 + 6.0 * hit_count
                for x, y in cells:
                    if board[x][y] == 0:
                        prob[x][y] += weight

        # Vertical placements
        for r in range(N - L + 1):
            for c in range(N):
                cells = [(r + k, c) for k in range(L)]
                if any(board[x][y] == -1 for x, y in cells):
                    continue
                hit_count = sum(1 for x, y in cells if board[x][y] == 1)
                weight = 1.0 + 6.0 * hit_count
                for x, y in cells:
                    if board[x][y] == 0:
                        prob[x][y] += weight

    # Determine whether we are in target mode
    has_targets = any(target_scores[r][c] > 0 and board[r][c] == 0 for r in range(N) for c in range(N))

    best = None
    best_score = -1.0

    # Parity preference in hunt mode
    unknown_count = sum(1 for r in range(N) for c in range(N) if board[r][c] == 0)

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            score = prob[r][c]

            if has_targets:
                score += target_scores[r][c] * 1000.0
            else:
                # Hunt mode parity bias
                if (r + c) % 2 == 0:
                    score *= 1.15
                # Tiny center preference
                score += 0.01 * (9 - abs(4.5 - r) - abs(4.5 - c))

            # Tie-breakers
            if score > best_score:
                best_score = score
                best = (r, c)
            elif score == best_score and best is not None:
                # Prefer center, then parity, then lexicographic
                br, bc = best
                center_d = abs(4.5 - r) + abs(4.5 - c)
                best_center_d = abs(4.5 - br) + abs(4.5 - bc)
                if center_d < best_center_d:
                    best = (r, c)
                elif center_d == best_center_d:
                    if ((r + c) % 2 == 0) and ((br + bc) % 2 != 0):
                        best = (r, c)
                    elif (r, c) < best:
                        best = (r, c)

    if best is not None and board[best[0]][best[1]] == 0:
        return best

    return first_legal()
