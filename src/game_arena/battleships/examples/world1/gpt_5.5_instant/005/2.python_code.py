
from typing import List, Tuple
import random

FLEET = [5, 4, 3, 3, 2]
N = 10

def _neighbors(r: int, c: int):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < N and 0 <= nc < N:
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
                stack = [(r, c)]
                seen[r][c] = True
                comp = []
                while stack:
                    x, y = stack.pop()
                    comp.append((x, y))
                    for nx, ny in _neighbors(x, y):
                        if board[nx][ny] == 1 and not seen[nx][ny]:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                comps.append(comp)
    return comps

def _valid_segment(board: List[List[int]], cells):
    for r, c in cells:
        if board[r][c] == -1:
            return False
    return True

def _segment_contains_all(cells_set, comp):
    for cell in comp:
        if cell not in cells_set:
            return False
    return True

def _target_score(board: List[List[int]]) -> List[List[float]]:
    scores = [[0.0] * N for _ in range(N)]
    comps = _hit_components(board)

    for comp in comps:
        comp_set = set(comp)
        comp_len = len(comp)

        if comp_len >= 2:
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}
            orientations = []
            if len(rows) == 1:
                orientations.append((0, 1))
            if len(cols) == 1:
                orientations.append((1, 0))
            if not orientations:
                orientations = [(0, 1), (1, 0)]
        else:
            orientations = [(0, 1), (1, 0)]

        for L in FLEET:
            if L < comp_len:
                continue
            for dr, dc in orientations:
                if dr == 0:
                    row = comp[0][0]
                    min_col = min(c for _, c in comp)
                    max_col = max(c for _, c in comp)
                    for start_c in range(max(0, max_col - L + 1), min(min_col, N - L) + 1):
                        cells = [(row, start_c + k) for k in range(L)]
                        cells_set = set(cells)
                        if _segment_contains_all(cells_set, comp) and _valid_segment(board, cells):
                            unknowns = [(r, c) for r, c in cells if board[r][c] == 0]
                            weight = 25.0 + 5.0 * comp_len + L
                            for cell in unknowns:
                                scores[cell[0]][cell[1]] += weight
                else:
                    col = comp[0][1]
                    min_row = min(r for r, _ in comp)
                    max_row = max(r for r, _ in comp)
                    for start_r in range(max(0, max_row - L + 1), min(min_row, N - L) + 1):
                        cells = [(start_r + k, col) for k in range(L)]
                        cells_set = set(cells)
                        if _segment_contains_all(cells_set, comp) and _valid_segment(board, cells):
                            unknowns = [(r, c) for r, c in cells if board[r][c] == 0]
                            weight = 25.0 + 5.0 * comp_len + L
                            for cell in unknowns:
                                scores[cell[0]][cell[1]] += weight

        # Extra emphasis on immediate extensions from aligned hit runs.
        if comp_len >= 2:
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}
            if len(rows) == 1:
                row = next(iter(rows))
                left = min(c for _, c in comp) - 1
                right = max(c for _, c in comp) + 1
                if 0 <= left < N and board[row][left] == 0:
                    scores[row][left] += 200.0 + 20.0 * comp_len
                if 0 <= right < N and board[row][right] == 0:
                    scores[row][right] += 200.0 + 20.0 * comp_len
            if len(cols) == 1:
                col = next(iter(cols))
                up = min(r for r, _ in comp) - 1
                down = max(r for r, _ in comp) + 1
                if 0 <= up < N and board[up][col] == 0:
                    scores[up][col] += 200.0 + 20.0 * comp_len
                if 0 <= down < N and board[down][col] == 0:
                    scores[down][col] += 200.0 + 20.0 * comp_len
        else:
            r, c = comp[0]
            for nr, nc in _neighbors(r, c):
                if board[nr][nc] == 0:
                    scores[nr][nc] += 80.0

    return scores

def _hunt_score(board: List[List[int]]) -> List[List[float]]:
    scores = [[0.0] * N for _ in range(N)]

    # Count all legal placements consistent with misses. Hits increase placement value.
    for L in FLEET:
        for r in range(N):
            for c in range(N - L + 1):
                cells = [(r, c + k) for k in range(L)]
                if all(board[x][y] != -1 for x, y in cells):
                    hits = sum(1 for x, y in cells if board[x][y] == 1)
                    weight = 1.0 + 6.0 * hits
                    for x, y in cells:
                        if board[x][y] == 0:
                            scores[x][y] += weight

        for r in range(N - L + 1):
            for c in range(N):
                cells = [(r + k, c) for k in range(L)]
                if all(board[x][y] != -1 for x, y in cells):
                    hits = sum(1 for x, y in cells if board[x][y] == 1)
                    weight = 1.0 + 6.0 * hits
                    for x, y in cells:
                        if board[x][y] == 0:
                            scores[x][y] += weight

    # Mild parity bias in pure hunting: all ships have length >= 2.
    any_hit = any(board[r][c] == 1 for r in range(N) for c in range(N))
    if not any_hit:
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    if (r + c) % 2 == 0:
                        scores[r][c] *= 1.18
                    # Center squares participate in more possible placements.
                    center_bonus = 1.0 + 0.025 * (9 - abs(2 * r - 9) - abs(2 * c - 9))
                    scores[r][c] *= center_bonus

    return scores

def policy(board: List[List[int]]) -> Tuple[int, int]:
    try:
        best = None
        best_score = -1.0

        target_scores = _target_score(board)
        max_target = max(target_scores[r][c] for r in range(N) for c in range(N) if board[r][c] == 0)

        if max_target > 0:
            scores = target_scores
        else:
            scores = _hunt_score(board)

        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    score = scores[r][c]
                    # Deterministic tiny tie-break favoring central cells.
                    score += 0.001 * (18 - abs(2 * r - 9) - abs(2 * c - 9))
                    if score > best_score:
                        best_score = score
                        best = (r, c)

        if best is not None and board[best[0]][best[1]] == 0:
            return best

        return _first_legal(board)

    except Exception:
        return _first_legal(board)
