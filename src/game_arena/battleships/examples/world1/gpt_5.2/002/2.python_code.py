
import random
from collections import deque
from typing import List, Tuple


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship policy for a 10x10 board.
    board[r][c]: 0 unknown, -1 miss, 1 hit.
    Returns an unshot cell (r, c) where board[r][c] == 0.
    """
    N = 10
    lengths = [5, 4, 3, 3, 2]
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Collect unknown cells; must always choose one of these
    unknown = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]
    if not unknown:
        # Should not happen in valid games; return something safe.
        return (0, 0)

    hits = [(r, c) for r in range(N) for c in range(N) if board[r][c] == 1]

    scores = [[0.0 for _ in range(N)] for _ in range(N)]

    def inb(r: int, c: int) -> bool:
        return 0 <= r < N and 0 <= c < N

    # --- Global probability heatmap via placement enumeration ---
    # Placements cannot include known misses. Hits are allowed.
    # Placements that include at least one hit are weighted more to focus fire.
    for L in lengths:
        # Horizontal placements
        for r in range(N):
            for c0 in range(N - L + 1):
                cells = [(r, c0 + k) for k in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                w = 1.0
                if any(board[rr][cc] == 1 for rr, cc in cells):
                    w = 4.0
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        scores[rr][cc] += w

        # Vertical placements
        for c in range(N):
            for r0 in range(N - L + 1):
                cells = [(r0 + k, c) for k in range(L)]
                if any(board[rr][cc] == -1 for rr, cc in cells):
                    continue
                w = 1.0
                if any(board[rr][cc] == 1 for rr, cc in cells):
                    w = 4.0
                for rr, cc in cells:
                    if board[rr][cc] == 0:
                        scores[rr][cc] += w

    # --- Targeting heuristics when we have hits ---
    if hits:
        # Strongly prioritize immediate neighbors of hits
        for r, c in hits:
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if inb(nr, nc) and board[nr][nc] == 0:
                    scores[nr][nc] += 25.0

        # Connected-component clustering of hits for line extension
        vis = [[False for _ in range(N)] for _ in range(N)]

        def get_cluster(sr: int, sc: int):
            q = deque([(sr, sc)])
            vis[sr][sc] = True
            cluster = [(sr, sc)]
            while q:
                r, c = q.popleft()
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if inb(nr, nc) and not vis[nr][nc] and board[nr][nc] == 1:
                        vis[nr][nc] = True
                        q.append((nr, nc))
                        cluster.append((nr, nc))
            return cluster

        for r, c in hits:
            if not vis[r][c]:
                cluster = get_cluster(r, c)
                if len(cluster) >= 2:
                    rows = {rr for rr, _ in cluster}
                    cols = {cc for _, cc in cluster}
                    # If aligned horizontally, extend left/right
                    if len(rows) == 1:
                        rr = next(iter(rows))
                        minc = min(cc for _, cc in cluster)
                        maxc = max(cc for _, cc in cluster)
                        for nc in (minc - 1, maxc + 1):
                            if inb(rr, nc) and board[rr][nc] == 0:
                                scores[rr][nc] += 40.0
                    # If aligned vertically, extend up/down
                    elif len(cols) == 1:
                        cc = next(iter(cols))
                        minr = min(rr for rr, _ in cluster)
                        maxr = max(rr for rr, _ in cluster)
                        for nr in (minr - 1, maxr + 1):
                            if inb(nr, cc) and board[nr][cc] == 0:
                                scores[nr][cc] += 40.0
                else:
                    # Single hit already handled by neighbor boost.
                    pass
    else:
        # No hits: mild checkerboard preference helps find longer ships sooner,
        # while still letting the heatmap dominate.
        for r, c in unknown:
            if (r + c) % 2 == 0:
                scores[r][c] += 0.5

    # Small center bias for tie-breaking (very small so it doesn't override evidence)
    center = (N - 1) / 2.0
    for r, c in unknown:
        dist = abs(r - center) + abs(c - center)
        scores[r][c] += (5.0 - dist) * 0.01

    # Choose best unknown cell(s)
    best_score = None
    best_moves = []
    for r, c in unknown:
        s = scores[r][c]
        if best_score is None or s > best_score + 1e-12:
            best_score = s
            best_moves = [(r, c)]
        elif abs(s - best_score) <= 1e-12:
            best_moves.append((r, c))

    # Deterministic tie-break based on board hash
    seed = 0
    for r in range(N):
        for c in range(N):
            # map -1->0, 0->1, 1->2 to keep non-negative
            v = board[r][c] + 1
            seed = (seed * 1315423911 + v * 2654435761) & 0xFFFFFFFF

    rng = random.Random(seed)
    return rng.choice(best_moves)
