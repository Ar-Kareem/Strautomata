
from collections import deque

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return the next legal shot for a 10x10 Battleship-like board.

    board values:
      0  unknown / legal target
     -1  miss
      1  hit
    """
    unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknowns:
        # Should not happen during a normal game, but keep a safe tuple return.
        return (0, 0)

    scores = [[0.0 for _ in range(N)] for _ in range(N)]
    hit_cells = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]

    # ------------------------------------------------------------------
    # 1. Probability density from all ship placements consistent with misses.
    #    Placements containing known hits are weighted much more heavily.
    # ------------------------------------------------------------------
    for length in SHIP_LENGTHS:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - length + 1):
                cells = [(r, c0 + k) for k in range(length)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                hcount = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                if hcount == 0:
                    weight = 1.0
                else:
                    # Exponential weighting makes cells that continue hits very attractive.
                    weight = 25.0 * (6.0 ** hcount)

                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        scores[rr][cc] += weight

        # Vertical placements
        for r0 in range(N - length + 1):
            for c in range(N):
                cells = [(r0 + k, c) for k in range(length)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue

                hcount = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                if hcount == 0:
                    weight = 1.0
                else:
                    weight = 25.0 * (6.0 ** hcount)

                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        scores[rr][cc] += weight

    # ------------------------------------------------------------------
    # 2. Explicit target mode: extend connected hit clusters.
    # ------------------------------------------------------------------
    visited = [[False for _ in range(N)] for _ in range(N)]

    def inside(r: int, c: int) -> bool:
        return 0 <= r < N and 0 <= c < N

    def possible_line(required_cells, orientation: str) -> bool:
        """
        Check whether there exists a legal ship segment of some ship length
        containing all required cells and no known miss.
        orientation: 'H' or 'V'
        """
        if not required_cells:
            return False

        if orientation == "H":
            row = required_cells[0][0]
            if any(r != row for r, _ in required_cells):
                return False
            cols = [c for _, c in required_cells]
            lo, hi = min(cols), max(cols)
            span = hi - lo + 1

            for length in SHIP_LENGTHS:
                if length < span:
                    continue
                start_min = max(0, hi - length + 1)
                start_max = min(lo, N - length)
                for start in range(start_min, start_max + 1):
                    ok = True
                    for c in range(start, start + length):
                        if board[row][c] == -1:
                            ok = False
                            break
                    if ok:
                        return True
            return False

        else:
            col = required_cells[0][1]
            if any(c != col for _, c in required_cells):
                return False
            rows = [r for r, _ in required_cells]
            lo, hi = min(rows), max(rows)
            span = hi - lo + 1

            for length in SHIP_LENGTHS:
                if length < span:
                    continue
                start_min = max(0, hi - length + 1)
                start_max = min(lo, N - length)
                for start in range(start_min, start_max + 1):
                    ok = True
                    for r in range(start, start + length):
                        if board[r][col] == -1:
                            ok = False
                            break
                    if ok:
                        return True
            return False

    for sr, sc in hit_cells:
        if visited[sr][sc]:
            continue

        # BFS connected component of orthogonally adjacent hits.
        q = deque([(sr, sc)])
        visited[sr][sc] = True
        comp = []

        while q:
            r, c = q.popleft()
            comp.append((r, c))
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if inside(nr, nc) and not visited[nr][nc] and board[nr][nc] == 1:
                    visited[nr][nc] = True
                    q.append((nr, nc))

        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}
        clen = len(comp)

        # Single hit: try all four adjacent cells.
        if clen == 1:
            r, c = comp[0]
            for dr, dc, orient in ((1, 0, "V"), (-1, 0, "V"), (0, 1, "H"), (0, -1, "H")):
                nr, nc = r + dr, c + dc
                if inside(nr, nc) and board[nr][nc] == 0:
                    if possible_line([(r, c), (nr, nc)], orient):
                        scores[nr][nc] += 900.0
            continue

        # Linear horizontal cluster.
        if len(rows) == 1:
            r = next(iter(rows))
            cs = sorted(c for _, c in comp)
            left = cs[0] - 1
            right = cs[-1] + 1

            if inside(r, left) and board[r][left] == 0:
                req = comp + [(r, left)]
                if possible_line(req, "H"):
                    scores[r][left] += 1400.0 + 250.0 * clen

            if inside(r, right) and board[r][right] == 0:
                req = comp + [(r, right)]
                if possible_line(req, "H"):
                    scores[r][right] += 1400.0 + 250.0 * clen

        # Linear vertical cluster.
        elif len(cols) == 1:
            c = next(iter(cols))
            rs = sorted(r for r, _ in comp)
            up = rs[0] - 1
            down = rs[-1] + 1

            if inside(up, c) and board[up][c] == 0:
                req = comp + [(up, c)]
                if possible_line(req, "V"):
                    scores[up][c] += 1400.0 + 250.0 * clen

            if inside(down, c) and board[down][c] == 0:
                req = comp + [(down, c)]
                if possible_line(req, "V"):
                    scores[down][c] += 1400.0 + 250.0 * clen

        # Non-linear component, usually caused by touching ships.
        # Fall back to attacking any adjacent unknown around the component.
        else:
            for r, c in comp:
                for dr, dc, orient in ((1, 0, "V"), (-1, 0, "V"), (0, 1, "H"), (0, -1, "H")):
                    nr, nc = r + dr, c + dc
                    if inside(nr, nc) and board[nr][nc] == 0:
                        if possible_line([(r, c), (nr, nc)], orient):
                            scores[nr][nc] += 800.0

    # ------------------------------------------------------------------
    # 3. Gap targeting: if two hits are aligned with unknown cells between
    #    them and no miss blocks the line, shoot the gap.
    # ------------------------------------------------------------------
    for r in range(N):
        for c0 in range(N):
            for length in SHIP_LENGTHS:
                if c0 + length > N:
                    continue
                cells = [(r, c0 + k) for k in range(length)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                hcount = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                if hcount >= 2:
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            scores[rr][cc] += 500.0 * hcount

    for c in range(N):
        for r0 in range(N):
            for length in SHIP_LENGTHS:
                if r0 + length > N:
                    continue
                cells = [(r0 + k, c) for k in range(length)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                hcount = sum(1 for rr, cc in cells if board[rr][cc] == 1)
                if hcount >= 2:
                    for rr, cc in cells:
                        if board[rr][cc] == 0:
                            scores[rr][cc] += 500.0 * hcount

    # ------------------------------------------------------------------
    # 4. Hunt mode refinement.
    #    With no hits, prefer checkerboard cells because every ship has
    #    length at least 2.
    # ------------------------------------------------------------------
    if not hit_cells:
        for r, c in unknowns:
            if (r + c) % 2 == 0:
                scores[r][c] *= 1.25
            else:
                scores[r][c] *= 0.85

    # ------------------------------------------------------------------
    # 5. Choose best legal move with deterministic tie-breaking.
    # ------------------------------------------------------------------
    board_hash = 0
    mul = 1
    for r in range(N):
        for c in range(N):
            board_hash += (board[r][c] + 2) * mul
            mul = (mul * 37) % 1000003

    best = None
    best_key = None

    for r, c in unknowns:
        # Prefer high score, then central cells, then deterministic noise.
        centrality = -((r - 4.5) ** 2 + (c - 4.5) ** 2)
        noise = ((board_hash + r * 97 + c * 193) % 1009) / 1000000.0
        key = (scores[r][c], centrality, noise)

        if best_key is None or key > best_key:
            best_key = key
            best = (r, c)

    if best is not None and board[best[0]][best[1]] == 0:
        return best

    # Absolute fallback: first legal unknown cell.
    return unknowns[0]
