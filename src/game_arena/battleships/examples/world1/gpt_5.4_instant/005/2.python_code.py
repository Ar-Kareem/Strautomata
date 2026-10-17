
from typing import List, Tuple

SHIP_LENGTHS = [5, 4, 3, 3, 2]
N = 10


def policy(board: List[List[int]]) -> Tuple[int, int]:
    unknowns = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknowns:
        return (0, 0)

    remaining = infer_remaining_ships(board)
    active_clusters = get_active_hit_clusters(board, remaining)

    # Target mode: pursue unresolved hits aggressively
    if active_clusters:
        move = target_move(board, active_clusters, remaining)
        if move is not None and board[move[0]][move[1]] == 0:
            return move

    # Hunt mode: probability over all valid ship placements
    move = hunt_move(board, remaining)
    if move is not None and board[move[0]][move[1]] == 0:
        return move

    # Fallback: always legal
    return unknowns[0]


def infer_remaining_ships(board: List[List[int]]) -> List[int]:
    """
    Infer sunk ships conservatively from hit clusters that can no longer be extended
    and whose size matches a ship length. Remove those lengths from remaining ships.
    """
    remaining = list(SHIP_LENGTHS)
    clusters = get_hit_clusters(board)

    sunk_lengths = []
    for cluster in clusters:
        if is_cluster_resolved(board, cluster):
            k = len(cluster)
            if k in remaining:
                remaining.remove(k)
                sunk_lengths.append(k)
    return remaining


def get_hit_clusters(board: List[List[int]]) -> List[List[Tuple[int, int]]]:
    seen = [[False] * N for _ in range(N)]
    clusters = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                comp = []
                while stack:
                    x, y = stack.pop()
                    comp.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < N and 0 <= ny < N and not seen[nx][ny] and board[nx][ny] == 1:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                clusters.append(comp)
    return clusters


def cluster_orientation(cluster: List[Tuple[int, int]]) -> str:
    rows = {r for r, _ in cluster}
    cols = {c for _, c in cluster}
    if len(cluster) <= 1:
        return "unknown"
    if len(rows) == 1:
        return "h"
    if len(cols) == 1:
        return "v"
    return "invalid"


def is_cluster_resolved(board: List[List[int]], cluster: List[Tuple[int, int]]) -> bool:
    """
    A cluster is resolved if there is no way to place any ship (length >= cluster size)
    through all its hit cells while extending into at least one unknown cell.
    """
    k = len(cluster)
    orient = cluster_orientation(cluster)

    candidate_lengths = [L for L in SHIP_LENGTHS if L >= k]
    if not candidate_lengths:
        return True

    cells = set(cluster)

    # Invalid L-shape should be treated as active, not resolved.
    if orient == "invalid":
        return False

    for L in candidate_lengths:
        if orient in ("h", "unknown"):
            rows = {r for r, _ in cluster}
            if orient == "unknown":
                for r, c in cluster:
                    for start_c in range(c - L + 1, c + 1):
                        end_c = start_c + L - 1
                        if 0 <= start_c and end_c < N:
                            placement = [(r, cc) for cc in range(start_c, end_c + 1)]
                            if cells.issubset(set(placement)) and placement_valid_for_cluster(board, placement, cells):
                                if any(board[x][y] == 0 for x, y in placement):
                                    return False
            else:
                r = next(iter(rows))
                cols = [c for _, c in cluster]
                min_c, max_c = min(cols), max(cols)
                for start_c in range(max_c - L + 1, min_c + 1):
                    end_c = start_c + L - 1
                    if 0 <= start_c and end_c < N:
                        placement = [(r, cc) for cc in range(start_c, end_c + 1)]
                        if cells.issubset(set(placement)) and placement_valid_for_cluster(board, placement, cells):
                            if any(board[x][y] == 0 for x, y in placement):
                                return False

        if orient in ("v", "unknown"):
            cols = {c for _, c in cluster}
            if orient == "unknown":
                for r, c in cluster:
                    for start_r in range(r - L + 1, r + 1):
                        end_r = start_r + L - 1
                        if 0 <= start_r and end_r < N:
                            placement = [(rr, c) for rr in range(start_r, end_r + 1)]
                            if cells.issubset(set(placement)) and placement_valid_for_cluster(board, placement, cells):
                                if any(board[x][y] == 0 for x, y in placement):
                                    return False
            else:
                c = next(iter(cols))
                rows = [r for r, _ in cluster]
                min_r, max_r = min(rows), max(rows)
                for start_r in range(max_r - L + 1, min_r + 1):
                    end_r = start_r + L - 1
                    if 0 <= start_r and end_r < N:
                        placement = [(rr, c) for rr in range(start_r, end_r + 1)]
                        if cells.issubset(set(placement)) and placement_valid_for_cluster(board, placement, cells):
                            if any(board[x][y] == 0 for x, y in placement):
                                return False

    return True


def placement_valid_for_cluster(board: List[List[int]], placement: List[Tuple[int, int]], cluster_cells: set) -> bool:
    placement_set = set(placement)
    for x, y in placement:
        if board[x][y] == -1:
            return False
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and (r, c) not in cluster_cells and (r, c) in placement_set:
                return False
    return True


def get_active_hit_clusters(board: List[List[int]], remaining: List[int]) -> List[List[Tuple[int, int]]]:
    clusters = get_hit_clusters(board)
    active = []
    rem_max = max(remaining) if remaining else 0
    for cl in clusters:
        if len(cl) > rem_max and rem_max > 0:
            continue
        if not is_cluster_resolved(board, cl):
            active.append(cl)
    return active


def target_move(board: List[List[int]], clusters: List[List[Tuple[int, int]]], remaining: List[int]) -> Tuple[int, int] | None:
    scores = [[0.0] * N for _ in range(N)]

    for cluster in clusters:
        add_target_scores(board, cluster, remaining, scores)

    best = None
    best_score = -1.0
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0 and scores[r][c] > best_score:
                best_score = scores[r][c]
                best = (r, c)

    if best is not None and best_score > 0:
        return best

    # Backup targeting: adjacent unknowns to any active hit
    for cluster in clusters:
        for r, c in cluster:
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    return (nr, nc)
    return None


def add_target_scores(board: List[List[int]], cluster: List[Tuple[int, int]], remaining: List[int], scores: List[List[float]]) -> None:
    cells = set(cluster)
    orient = cluster_orientation(cluster)
    lengths = [L for L in remaining if L >= len(cluster)]
    if not lengths:
        lengths = [L for L in SHIP_LENGTHS if L >= len(cluster)]

    for L in lengths:
        if orient in ("h", "unknown"):
            if orient == "unknown":
                r, c = cluster[0]
                for start_c in range(c - L + 1, c + 1):
                    end_c = start_c + L - 1
                    if 0 <= start_c and end_c < N:
                        placement = [(r, cc) for cc in range(start_c, end_c + 1)]
                        if cells.issubset(set(placement)) and placement_compatible(board, placement, cells):
                            weight = 5.0 + L
                            for x, y in placement:
                                if board[x][y] == 0:
                                    scores[x][y] += weight
            else:
                r = cluster[0][0]
                cols = [c for _, c in cluster]
                min_c, max_c = min(cols), max(cols)
                for start_c in range(max_c - L + 1, min_c + 1):
                    end_c = start_c + L - 1
                    if 0 <= start_c and end_c < N:
                        placement = [(r, cc) for cc in range(start_c, end_c + 1)]
                        if cells.issubset(set(placement)) and placement_compatible(board, placement, cells):
                            weight = 10.0 + 2 * L
                            for x, y in placement:
                                if board[x][y] == 0:
                                    scores[x][y] += weight

        if orient in ("v", "unknown"):
            if orient == "unknown":
                r, c = cluster[0]
                for start_r in range(r - L + 1, r + 1):
                    end_r = start_r + L - 1
                    if 0 <= start_r and end_r < N:
                        placement = [(rr, c) for rr in range(start_r, end_r + 1)]
                        if cells.issubset(set(placement)) and placement_compatible(board, placement, cells):
                            weight = 5.0 + L
                            for x, y in placement:
                                if board[x][y] == 0:
                                    scores[x][y] += weight
            else:
                c = cluster[0][1]
                rows = [r for r, _ in cluster]
                min_r, max_r = min(rows), max(rows)
                for start_r in range(max_r - L + 1, min_r + 1):
                    end_r = start_r + L - 1
                    if 0 <= start_r and end_r < N:
                        placement = [(rr, c) for rr in range(start_r, end_r + 1)]
                        if cells.issubset(set(placement)) and placement_compatible(board, placement, cells):
                            weight = 10.0 + 2 * L
                            for x, y in placement:
                                if board[x][y] == 0:
                                    scores[x][y] += weight

    # Local adjacency boost
    for r, c in cluster:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                if orient == "unknown":
                    scores[nr][nc] += 3.0
                elif orient == "h" and dr == 0:
                    scores[nr][nc] += 6.0
                elif orient == "v" and dc == 0:
                    scores[nr][nc] += 6.0


def placement_compatible(board: List[List[int]], placement: List[Tuple[int, int]], required_hits: set) -> bool:
    pset = set(placement)
    if not required_hits.issubset(pset):
        return False
    for x, y in placement:
        if board[x][y] == -1:
            return False
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and (r, c) not in pset and (r, c) in required_hits:
                return False
    return True


def hunt_move(board: List[List[int]], remaining: List[int]) -> Tuple[int, int] | None:
    if not remaining:
        remaining = [2]

    scores = [[0.0] * N for _ in range(N)]
    known_hits = {(r, c) for r in range(N) for c in range(N) if board[r][c] == 1}

    for L in remaining:
        # Horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                placement = [(r, cc) for cc in range(c, c + L)]
                if any(board[x][y] == -1 for x, y in placement):
                    continue
                if any((x, y) in known_hits for x, y in placement):
                    continue
                weight = float(L * L)
                for x, y in placement:
                    if board[x][y] == 0:
                        scores[x][y] += weight

        # Vertical placements
        for r in range(N - L + 1):
            for c in range(N):
                placement = [(rr, c) for rr in range(r, r + L)]
                if any(board[x][y] == -1 for x, y in placement):
                    continue
                if any((x, y) in known_hits for x, y in placement):
                    continue
                weight = float(L * L)
                for x, y in placement:
                    if board[x][y] == 0:
                        scores[x][y] += weight

    min_len = min(remaining) if remaining else 2

    best = None
    best_score = -1.0
    best_tiebreak = -1.0

    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue

            score = scores[r][c]

            # Parity preference, stronger when smallest remaining ship > 2
            parity = 1.0 if ((r + c) % 2 == 0) else 0.0
            if min_len >= 3:
                score += 0.5 * parity
            elif min_len == 2:
                score += 0.15 * parity

            # Mild centrality bias
            center_bias = 4.5 - (abs(r - 4.5) + abs(c - 4.5)) / 2.0

            if score > best_score or (score == best_score and center_bias > best_tiebreak):
                best_score = score
                best_tiebreak = center_bias
                best = (r, c)

    return best
