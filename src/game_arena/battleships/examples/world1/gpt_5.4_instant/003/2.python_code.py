
from typing import List, Tuple

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10

def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < N and 0 <= c < N

def _neighbors4(r: int, c: int):
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc):
            yield nr, nc

def _get_hit_clusters(board: List[List[int]]):
    seen = [[False] * N for _ in range(N)]
    clusters = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for nr, nc in _neighbors4(cr, cc):
                        if board[nr][nc] == 1 and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                clusters.append(cells)
    return clusters

def _cluster_orientation(cluster):
    rows = {r for r, _ in cluster}
    cols = {c for _, c in cluster}
    if len(cluster) <= 1:
        return None
    if len(rows) == 1:
        return "H"
    if len(cols) == 1:
        return "V"
    return "B"  # should not normally happen in legal play knowledge

def _placement_cells(r: int, c: int, length: int, orient: str):
    if orient == "H":
        return [(r, c + k) for k in range(length)]
    else:
        return [(r + k, c) for k in range(length)]

def _placement_valid(board: List[List[int]], cells):
    for r, c in cells:
        if not _in_bounds(r, c):
            return False
        if board[r][c] == -1:
            return False
    return True

def _placement_covers_cluster(cells_set, cluster):
    for cell in cluster:
        if cell not in cells_set:
            return False
    return True

def _placement_matches_cluster_orientation(cells, cluster, orient):
    if orient is None:
        return True
    if orient == "H":
        row = cluster[0][0]
        return all(r == row for r, _ in cells)
    if orient == "V":
        col = cluster[0][1]
        return all(c == col for _, c in cells)
    return True

def policy(board: List[List[int]]) -> Tuple[int, int]:
    unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknowns:
        return (0, 0)

    clusters = _get_hit_clusters(board)

    # Base score map
    scores = [[0.0 for _ in range(N)] for _ in range(N)]

    # Mild parity preference in hunt mode; weaker when hits exist.
    has_hits = any(board[r][c] == 1 for r in range(N) for c in range(N))
    for r, c in unknowns:
        if (r + c) % 2 == 0:
            scores[r][c] += 0.15 if not has_hits else 0.03

    # Centrality tie-break preference
    for r, c in unknowns:
        dist_center = abs(r - 4.5) + abs(c - 4.5)
        scores[r][c] += 0.001 * (10 - dist_center)

    # Enumerate all placements consistent with board misses and existing hit clusters.
    # Score every unknown cell by frequency of occurrence in consistent placements.
    for length in SHIP_LENGTHS:
        for orient in ("H", "V"):
            rmax = N if orient == "H" else N - length + 1
            cmax = N - length + 1 if orient == "H" else N
            for r in range(rmax):
                for c in range(cmax):
                    cells = _placement_cells(r, c, length, orient)
                    if not _placement_valid(board, cells):
                        continue
                    cells_set = set(cells)

                    # Placement must not partially intersect any hit cluster:
                    # if it touches a cluster, it must explain the whole cluster.
                    ok = True
                    cluster_hits_covered = 0
                    for cluster in clusters:
                        inter = sum((cell in cells_set) for cell in cluster)
                        if inter > 0:
                            if inter != len(cluster):
                                ok = False
                                break
                            cl_orient = _cluster_orientation(cluster)
                            if not _placement_matches_cluster_orientation(cells, cluster, cl_orient):
                                ok = False
                                break
                            cluster_hits_covered += inter
                    if not ok:
                        continue

                    # Prefer placements that explain known hits.
                    weight = 1.0 + 2.5 * cluster_hits_covered

                    for pr, pc in cells:
                        if board[pr][pc] == 0:
                            scores[pr][pc] += weight

    # Strong target-mode local bonuses near hit clusters.
    for cluster in clusters:
        orient = _cluster_orientation(cluster)
        if orient == "H":
            row = cluster[0][0]
            cols = sorted(c for _, c in cluster)
            for tc in (cols[0] - 1, cols[-1] + 1):
                if _in_bounds(row, tc) and board[row][tc] == 0:
                    scores[row][tc] += 100.0 + 10.0 * len(cluster)
        elif orient == "V":
            col = cluster[0][1]
            rows = sorted(r for r, _ in cluster)
            for tr in (rows[0] - 1, rows[-1] + 1):
                if _in_bounds(tr, col) and board[tr][col] == 0:
                    scores[tr][col] += 100.0 + 10.0 * len(cluster)
        else:
            # Single hit or ambiguous: probe orthogonal neighbors.
            for r, c in cluster:
                for nr, nc in _neighbors4(r, c):
                    if board[nr][nc] == 0:
                        scores[nr][nc] += 40.0

    # Choose best legal move.
    best = None
    best_score = None
    for r, c in unknowns:
        s = scores[r][c]
        if best is None or s > best_score:
            best = (r, c)
            best_score = s

    if best is not None and board[best[0]][best[1]] == 0:
        return best

    # Safety fallback: always return a legal unknown cell.
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)

    return (0, 0)
