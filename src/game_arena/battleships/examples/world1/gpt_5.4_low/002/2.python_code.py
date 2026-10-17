
from collections import deque

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10


def policy(board: list[list[int]]) -> tuple[int, int]:
    # Safety fallback: first legal move
    def first_legal():
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)  # Should never happen in a valid game state

    try:
        # Basic validation
        if not isinstance(board, list) or len(board) != N:
            return first_legal()
        for row in board:
            if not isinstance(row, list) or len(row) != N:
                return first_legal()

        unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        if not unknowns:
            return (0, 0)

        score = [[0.0 for _ in range(N)] for _ in range(N)]

        # Mild center bias for hunt mode / tie-breaking
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    dist = abs(r - 4.5) + abs(c - 4.5)
                    score[r][c] += max(0.0, 5.0 - 0.5 * dist)

        # Find connected components of hits
        hit_components = get_hit_components(board)

        # Global placement scoring:
        # Count all ship placements that do not cross misses.
        # Boost placements that include hits.
        total_hits = sum(1 for r in range(N) for c in range(N) if board[r][c] == 1)
        for L in SHIP_LENGTHS:
            # Horizontal placements
            for r in range(N):
                for c in range(N - L + 1):
                    cells = [(r, c + k) for k in range(L)]
                    if any(board[rr][cc] == -1 for rr, cc in cells):
                        continue
                    hits_in_place = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                    # Base weight + stronger if placement explains hits
                    w = 1.0 + 4.0 * hits_in_place
                    # If there are hits on board, prefer placements that include some hit
                    if total_hits > 0 and hits_in_place == 0:
                        w *= 0.35
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            score[rr][cc] += w

            # Vertical placements
            for r in range(N - L + 1):
                for c in range(N):
                    cells = [(r + k, c) for k in range(L)]
                    if any(board[rr][cc] == -1 for rr, cc in cells):
                        continue
                    hits_in_place = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                    w = 1.0 + 4.0 * hits_in_place
                    if total_hits > 0 and hits_in_place == 0:
                        w *= 0.35
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            score[rr][cc] += w

        # Target mode enhancements for hit components
        if hit_components:
            for comp in hit_components:
                enhance_component_targeting(board, score, comp)

        # Strong local adjacency bonus around hits
        for r in range(N):
            for c in range(N):
                if board[r][c] == 1:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < N and 0 <= cc < N and board[rr][cc] == 0:
                            score[rr][cc] += 12.0

        # Choose highest-scoring legal cell
        best = None
        best_score = -1e18
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    s = score[r][c]
                    # Deterministic tie-breakers:
                    # 1) higher local openness
                    # 2) closer to center
                    openness = local_openness(board, r, c)
                    center = -(abs(r - 4.5) + abs(c - 4.5))
                    key = (s, openness, center, -r, -c)
                    if best is None or key > best_score:
                        best = (r, c)
                        best_score = key

        if best is not None and board[best[0]][best[1]] == 0:
            return best

        return first_legal()

    except Exception:
        return first_legal()


def get_hit_components(board):
    seen = [[False for _ in range(N)] for _ in range(N)]
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
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        xx, yy = x + dx, y + dy
                        if 0 <= xx < N and 0 <= yy < N and not seen[xx][yy] and board[xx][yy] == 1:
                            seen[xx][yy] = True
                            q.append((xx, yy))
                comps.append(comp)
    return comps


def enhance_component_targeting(board, score, comp):
    rows = {r for r, _ in comp}
    cols = {c for _, c in comp}
    size = len(comp)

    # If aligned horizontally
    if len(rows) == 1:
        r = next(iter(rows))
        cmin = min(c for _, c in comp)
        cmax = max(c for _, c in comp)

        # Strongly prefer extending both ends
        for cc in (cmin - 1, cmax + 1):
            if 0 <= cc < N and board[r][cc] == 0:
                score[r][cc] += 80.0 + 10.0 * size

        # Prefer any legal placement covering the whole component
        cover_component_line(board, score, comp, horizontal=True)

    # If aligned vertically
    elif len(cols) == 1:
        c = next(iter(cols))
        rmin = min(r for r, _ in comp)
        rmax = max(r for r, _ in comp)

        for rr in (rmin - 1, rmax + 1):
            if 0 <= rr < N and board[rr][c] == 0:
                score[rr][c] += 80.0 + 10.0 * size

        cover_component_line(board, score, comp, horizontal=False)

    # If single hit or irregular cluster, prefer adjacent unknowns
    else:
        # Battleship ships are straight, so irregular clusters usually mean uncertain info
        # from multiple nearby ships/sunk states; target their boundaries.
        for r, c in comp:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < N and 0 <= cc < N and board[rr][cc] == 0:
                    score[rr][cc] += 35.0 + 5.0 * size


def cover_component_line(board, score, comp, horizontal):
    size = len(comp)
    if horizontal:
        r = comp[0][0]
        cmin = min(c for _, c in comp)
        cmax = max(c for _, c in comp)
        segment_len = cmax - cmin + 1
        # Consider placements that cover the whole contiguous hit run
        for L in SHIP_LENGTHS:
            if L < segment_len:
                continue
            start_min = cmax - L + 1
            start_max = cmin
            for start in range(start_min, start_max + 1):
                if not (0 <= start and start + L - 1 < N):
                    continue
                cells = [(r, start + k) for k in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                # Require all component cells in placement
                cellset = set(cells)
                if not all((rr, cc) in cellset for rr, cc in comp):
                    continue
                w = 20.0 + 6.0 * size + 2.0 * L
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += w
    else:
        c = comp[0][1]
        rmin = min(r for r, _ in comp)
        rmax = max(r for r, _ in comp)
        segment_len = rmax - rmin + 1
        for L in SHIP_LENGTHS:
            if L < segment_len:
                continue
            start_min = rmax - L + 1
            start_max = rmin
            for start in range(start_min, start_max + 1):
                if not (0 <= start and start + L - 1 < N):
                    continue
                cells = [(start + k, c) for k in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                cellset = set(cells)
                if not all((rr, cc) in cellset for rr, cc in comp):
                    continue
                w = 20.0 + 6.0 * size + 2.0 * L
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += w


def local_openness(board, r, c):
    # Count nearby non-miss cells; useful as a tie-breaker
    val = 0
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (-2, 0), (0, 2), (0, -2)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N and board[rr][cc] != -1:
            val += 1
    return val
