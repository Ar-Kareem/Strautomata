
from typing import List, Tuple
from collections import deque

N = 10
SHIPS = [5, 4, 3, 3, 2]

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N

def _neighbors(r: int, c: int):
    for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc):
            yield nr, nc

def _first_legal(board: List[List[int]]) -> Tuple[int, int]:
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)

def _hit_components(board: List[List[int]]):
    seen = [[False] * N for _ in range(N)]
    comps = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                comp = []
                while q:
                    x, y = q.popleft()
                    comp.append((x, y))
                    for nx, ny in _neighbors(x, y):
                        if board[nx][ny] == 1 and not seen[nx][ny]:
                            seen[nx][ny] = True
                            q.append((nx, ny))
                comps.append(comp)
    return comps

def _placement_valid(board: List[List[int]], cells, require_hits=None) -> bool:
    # A placement may cover unknowns and hits, never misses.
    for r, c in cells:
        if board[r][c] == -1:
            return False
    if require_hits is not None:
        s = set(cells)
        for h in require_hits:
            if h not in s:
                return False
    return True

def _all_placements_for_length(board: List[List[int]], length: int):
    placements = []
    for r in range(N):
        for c in range(N - length + 1):
            cells = tuple((r, c + k) for k in range(length))
            if _placement_valid(board, cells):
                placements.append(cells)
    for r in range(N - length + 1):
        for c in range(N):
            cells = tuple((r + k, c) for k in range(length))
            if _placement_valid(board, cells):
                placements.append(cells)
    return placements

def _component_target_scores(board: List[List[int]]):
    scores = [[0.0] * N for _ in range(N)]
    comps = _hit_components(board)

    for comp in comps:
        comp_set = set(comp)
        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}

        candidate_placements = []
        for length in SHIPS:
            if length < len(comp):
                continue

            # If component is already aligned, enforce that orientation.
            if len(rows) == 1:
                r = next(iter(rows))
                minc = min(c for _, c in comp)
                maxc = max(c for _, c in comp)
                for start in range(max(0, maxc - length + 1), min(minc, N - length) + 1):
                    cells = tuple((r, start + k) for k in range(length))
                    if _placement_valid(board, cells, comp_set):
                        candidate_placements.append(cells)

            elif len(cols) == 1:
                c = next(iter(cols))
                minr = min(r for r, _ in comp)
                maxr = max(r for r, _ in comp)
                for start in range(max(0, maxr - length + 1), min(minr, N - length) + 1):
                    cells = tuple((start + k, c) for k in range(length))
                    if _placement_valid(board, cells, comp_set):
                        candidate_placements.append(cells)

            else:
                # Odd/nonlinear hit pattern may include touching ships; fall back to generic placements.
                for cells in _all_placements_for_length(board, length):
                    if comp_set.issubset(set(cells)):
                        candidate_placements.append(cells)

        for cells in candidate_placements:
            unk_count = sum(1 for r, c in cells if board[r][c] == 0)
            if unk_count == 0:
                continue
            # Strongly favor immediate continuation shots around known hits.
            weight = 25.0 + 3.0 * len(comp)
            for r, c in cells:
                if board[r][c] == 0:
                    scores[r][c] += weight

        # Extra endpoint emphasis for aligned clusters.
        if len(rows) == 1:
            r = next(iter(rows))
            for c in (min(c for _, c in comp) - 1, max(c for _, c in comp) + 1):
                if _in_bounds(r, c) and board[r][c] == 0:
                    scores[r][c] += 80.0 + 10.0 * len(comp)
        elif len(cols) == 1:
            c = next(iter(cols))
            for r in (min(r for r, _ in comp) - 1, max(r for r, _ in comp) + 1):
                if _in_bounds(r, c) and board[r][c] == 0:
                    scores[r][c] += 80.0 + 10.0 * len(comp)
        else:
            for r, c in comp:
                for nr, nc in _neighbors(r, c):
                    if board[nr][nc] == 0:
                        scores[nr][nc] += 50.0

    return scores

def _hunt_scores(board: List[List[int]]):
    scores = [[0.0] * N for _ in range(N)]

    for length in SHIPS:
        for cells in _all_placements_for_length(board, length):
            # Prefer placements that are compatible with current hits too;
            # each covered unknown gets credit.
            hit_count = sum(1 for r, c in cells if board[r][c] == 1)
            weight = 1.0 + hit_count * 5.0
            for r, c in cells:
                if board[r][c] == 0:
                    scores[r][c] += weight

    # Hunt parity: helpful before many hits have been found.
    hit_total = sum(1 for r in range(N) for c in range(N) if board[r][c] == 1)
    if hit_total == 0:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0 and ((r + c) % 2 == 0):
                    scores[r][c] += 1.5
    else:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0 and ((r + c) % 2 == 0):
                    scores[r][c] += 0.35

    # Slight central bias because more placements cross central cells.
    center = 4.5
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                dist = abs(r - center) + abs(c - center)
                scores[r][c] += max(0.0, 4.5 - dist) * 0.05

    return scores

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        best = None
        best_score = -1e18

        target = _component_target_scores(board)
        hunt = _hunt_scores(board)

        any_target = any(target[r][c] > 0 for r in range(N) for c in range(N) if board[r][c] == 0)

        for r in range(N):
            for c in range(N):
                if board[r][c] != 0:
                    continue

                if any_target:
                    score = target[r][c] * 10.0 + hunt[r][c]
                else:
                    score = hunt[r][c]

                # Deterministic tie-breaker: mild preference for center and checkerboard.
                score -= 0.001 * (abs(r - 4.5) + abs(c - 4.5))
                if (r + c) % 2 == 0:
                    score += 0.0001

                if score > best_score:
                    best_score = score
                    best = (r, c)

        if best is not None:
            return best

        return _first_legal(board)

    except Exception:
        return _first_legal(board)
