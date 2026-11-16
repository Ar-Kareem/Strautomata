
from typing import List, Tuple

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy for a 10x10 board.
    board values:
      0  unknown / legal target
     -1  known miss
      1  known hit
    returns (row, col) where board[row][col] == 0
    """
    try:
        unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
        if not unknowns:
            return (0, 0)  # Should not happen in normal play.

        hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]
        hit_set = set(hits)

        # Generate all placements for each ship length that do not cross misses.
        # We allow placements to include hits, since unknown sunk-status is unavailable.
        placements_by_len = {}
        for L in set(SHIP_LENGTHS):
            pls = []
            # horizontal
            for r in range(N):
                for c in range(N - L + 1):
                    cells = tuple((r, c + k) for k in range(L))
                    if all(board[rr][cc] != -1 for rr, cc in cells):
                        hit_count = sum((cell in hit_set) for cell in cells)
                        pls.append((cells, hit_count))
            # vertical
            for r in range(N - L + 1):
                for c in range(N):
                    cells = tuple((r + k, c) for k in range(L))
                    if all(board[rr][cc] != -1 for rr, cc in cells):
                        hit_count = sum((cell in hit_set) for cell in cells)
                        pls.append((cells, hit_count))
            placements_by_len[L] = pls

        heat = [[0.0 for _ in range(N)] for _ in range(N)]

        # Baseline hunt mode:
        # Count legal ship placements. Placements containing hits get boosted,
        # because they represent possible continuations/completions.
        for L in SHIP_LENGTHS:
            for cells, hcnt in placements_by_len.get(L, []):
                # If there are hits, prefer placements explaining them.
                # Square boost strongly emphasizes multi-hit alignments.
                weight = 1.0 + 5.0 * hcnt + 12.0 * hcnt * hcnt
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        heat[rr][cc] += weight

        # Target mode:
        # For every connected hit cluster, heavily favor unknown cells that can
        # extend a line through that cluster or touch isolated hits.
        seen = set()
        clusters = []
        for h in hits:
            if h in seen:
                continue
            stack = [h]
            seen.add(h)
            comp = []
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for dx, dy in ((1,0), (-1,0), (0,1), (0,-1)):
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in hit_set and (nx, ny) not in seen:
                        seen.add((nx, ny))
                        stack.append((nx, ny))
            clusters.append(comp)

        for comp in clusters:
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}

            if len(comp) >= 2 and len(rows) == 1:
                # Horizontal hit run: shoot either end if open.
                r = next(iter(rows))
                minc = min(c for _, c in comp)
                maxc = max(c for _, c in comp)
                for c in (minc - 1, maxc + 1):
                    if 0 <= c < N and board[r][c] == 0:
                        heat[r][c] += 10000 + 500 * len(comp)

                # Also fill gaps inside the bounding segment if any.
                for c in range(minc, maxc + 1):
                    if board[r][c] == 0:
                        heat[r][c] += 9000 + 500 * len(comp)

            elif len(comp) >= 2 and len(cols) == 1:
                # Vertical hit run: shoot either end if open.
                c = next(iter(cols))
                minr = min(r for r, _ in comp)
                maxr = max(r for r, _ in comp)
                for r in (minr - 1, maxr + 1):
                    if 0 <= r < N and board[r][c] == 0:
                        heat[r][c] += 10000 + 500 * len(comp)

                # Also fill gaps inside the bounding segment if any.
                for r in range(minr, maxr + 1):
                    if board[r][c] == 0:
                        heat[r][c] += 9000 + 500 * len(comp)

            else:
                # Isolated or irregular hits: check all four neighbors.
                for r, c in comp:
                    for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                            heat[nr][nc] += 7000

        # Parity hunt bonus: while not actively targeting, checkerboard-like
        # probing is efficient for ships of length >= 2. Use multiple modular
        # patterns so it remains useful late game.
        if not hits:
            for r, c in unknowns:
                if (r + c) % 2 == 0:
                    heat[r][c] += 8
                if (r * 3 + c * 5) % 4 == 0:
                    heat[r][c] += 2

        # Prefer cells with more open space around them as a tie-breaker.
        for r, c in unknowns:
            open_neighbors = 0
            for dr, dc in ((1,0), (-1,0), (0,1), (0,-1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    open_neighbors += 1
            heat[r][c] += 0.01 * open_neighbors

        # Select best legal cell. Deterministic tie-break favors central squares.
        best = None
        best_score = -1e100
        center = 4.5
        for r, c in unknowns:
            score = heat[r][c] - 0.001 * ((r - center) ** 2 + (c - center) ** 2)
            if score > best_score:
                best_score = score
                best = (r, c)

        if best is not None and board[best[0]][best[1]] == 0:
            return best

        # Absolute fallback: return first legal unknown.
        return unknowns[0]

    except Exception:
        # Never fail to return a legal move if possible.
        for r in range(10):
            for c in range(10):
                try:
                    if board[r][c] == 0:
                        return (r, c)
                except Exception:
                    pass
        return (0, 0)
