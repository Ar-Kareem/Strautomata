
from typing import List, Tuple
from collections import deque

N = 10
SHIP_LENGTHS = [5, 4, 3, 3, 2]


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N


def _neighbors(r: int, c: int):
    if r > 0:
        yield r - 1, c
    if r + 1 < N:
        yield r + 1, c
    if c > 0:
        yield r, c - 1
    if c + 1 < N:
        yield r, c + 1


def _get_hit_components(board: List[List[int]]):
    seen = [[False] * N for _ in range(N)]
    comps = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not seen[r][c]:
                q = deque([(r, c)])
                seen[r][c] = True
                cells = []
                while q:
                    x, y = q.popleft()
                    cells.append((x, y))
                    for nx, ny in _neighbors(x, y):
                        if board[nx][ny] == 1 and not seen[nx][ny]:
                            seen[nx][ny] = True
                            q.append((nx, ny))
                comps.append(cells)
    return comps


def _component_orientation(cells):
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}
    if len(cells) <= 1:
        return None
    if len(rows) == 1:
        return "H"
    if len(cols) == 1:
        return "V"
    return None


def _placement_cells(r: int, c: int, length: int, orient: str):
    if orient == "H":
        return [(r, c + k) for k in range(length)]
    else:
        return [(r + k, c) for k in range(length)]


def _valid_placement(board: List[List[int]], cells, required_hits_set=None):
    for r, c in cells:
        if not _in_bounds(r, c):
            return False
        if board[r][c] == -1:
            return False
    if required_hits_set is not None:
        for h in required_hits_set:
            if h not in cells:
                return False
    return True


def _all_unknowns(board: List[List[int]]):
    out = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                out.append((r, c))
    return out


def _parity_score(r: int, c: int) -> int:
    # Strong checkerboard bias, but not absolute.
    return 1 if (r + c) % 2 == 0 else 0


def policy(board: List[List[int]]) -> Tuple[int, int]:
    unknowns = _all_unknowns(board)
    if not unknowns:
        return (0, 0)

    score = [[0.0 for _ in range(N)] for _ in range(N)]

    hit_components = _get_hit_components(board)
    all_hits = {(r, c) for r in range(N) for c in range(N) if board[r][c] == 1}

    # 1. Strong target mode: extend existing hit components.
    for comp in hit_components:
        comp_set = set(comp)
        orient = _component_orientation(comp)

        candidate_lengths = [L for L in SHIP_LENGTHS if L >= len(comp)]
        if not candidate_lengths:
            candidate_lengths = [len(comp)]

        if orient == "H":
            row = comp[0][0]
            min_c = min(c for _, c in comp)
            max_c = max(c for _, c in comp)

            left = (row, min_c - 1)
            right = (row, max_c + 1)

            if _in_bounds(*left) and board[left[0]][left[1]] == 0:
                score[left[0]][left[1]] += 1000.0
            if _in_bounds(*right) and board[right[0]][right[1]] == 0:
                score[right[0]][right[1]] += 1000.0

            # Add probability from all placements covering this component.
            for L in candidate_lengths:
                for start_c in range(max(0, max_c - L + 1), min(min_c, N - L) + 1):
                    cells = [(row, start_c + k) for k in range(L)]
                    if _valid_placement(board, cells, comp_set):
                        for rr, cc in cells:
                            if board[rr][cc] == 0:
                                score[rr][cc] += 60.0

        elif orient == "V":
            col = comp[0][1]
            min_r = min(r for r, _ in comp)
            max_r = max(r for r, _ in comp)

            up = (min_r - 1, col)
            down = (max_r + 1, col)

            if _in_bounds(*up) and board[up[0]][up[1]] == 0:
                score[up[0]][up[1]] += 1000.0
            if _in_bounds(*down) and board[down[0]][down[1]] == 0:
                score[down[0]][down[1]] += 1000.0

            for L in candidate_lengths:
                for start_r in range(max(0, max_r - L + 1), min(min_r, N - L) + 1):
                    cells = [(start_r + k, col) for k in range(L)]
                    if _valid_placement(board, cells, comp_set):
                        for rr, cc in cells:
                            if board[rr][cc] == 0:
                                score[rr][cc] += 60.0

        else:
            # Single hit (or ambiguous): probe all four directions with placement support.
            r, c = comp[0]
            for nr, nc in _neighbors(r, c):
                if board[nr][nc] == 0:
                    score[nr][nc] += 200.0

            for L in candidate_lengths:
                # Horizontal placements including the hit
                start_min = max(0, c - L + 1)
                start_max = min(c, N - L)
                for start_c in range(start_min, start_max + 1):
                    cells = [(r, start_c + k) for k in range(L)]
                    if _valid_placement(board, cells, comp_set):
                        for rr, cc in cells:
                            if board[rr][cc] == 0:
                                score[rr][cc] += 40.0

                # Vertical placements including the hit
                start_min = max(0, r - L + 1)
                start_max = min(r, N - L)
                for start_r in range(start_min, start_max + 1):
                    cells = [(start_r + k, c) for k in range(L)]
                    if _valid_placement(board, cells, comp_set):
                        for rr, cc in cells:
                            if board[rr][cc] == 0:
                                score[rr][cc] += 40.0

    # 2. Global probability map from all legal ship placements.
    # Placements may cover known hits; they cannot cover misses.
    for L in SHIP_LENGTHS:
        # Horizontal
        for r in range(N):
            for c in range(N - L + 1):
                cells = [(r, c + k) for k in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                hit_count = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                base = 1.0 + 2.0 * hit_count
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += base

            # Vertical
        for r in range(N - L + 1):
            for c in range(N):
                cells = [(r + k, c) for k in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                hit_count = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                base = 1.0 + 2.0 * hit_count
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += base

    # 3. Local adjacency bonus around hits to finish discovered ships faster.
    for r, c in all_hits:
        for nr, nc in _neighbors(r, c):
            if board[nr][nc] == 0:
                score[nr][nc] += 8.0

    # 4. Search parity bias when not strongly targeting.
    has_hit = any(board[r][c] == 1 for r in range(N) for c in range(N))
    for r, c in unknowns:
        if not has_hit:
            score[r][c] += 1.5 * _parity_score(r, c)
        else:
            score[r][c] += 0.2 * _parity_score(r, c)

        # Mild center bias.
        center_dist = abs(r - 4.5) + abs(c - 4.5)
        score[r][c] += max(0.0, 0.6 - 0.06 * center_dist)

    # 5. Select best legal move deterministically.
    best = None
    best_score = -1e18
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                s = score[r][c]
                # deterministic tie-breakers:
                # better parity, then closer to center, then row-major
                tie1 = _parity_score(r, c)
                tie2 = -(abs(r - 4.5) + abs(c - 4.5))
                key = (s, tie1, tie2, -r, -c)
                if best is None or key > best_score:
                    best = (r, c)
                    best_score = key

    if best is not None:
        return best

    # Absolute fallback: always legal if any unknown exists.
    return unknowns[0]
