
import random
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10
    ships = [5, 4, 3, 3, 2]

    # Helper to get neighbors
    def neighbors(r, c):
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0 <= nr < N and 0 <= nc < N:
                yield nr, nc

    # Find clusters of hits
    visited = [[False]*N for _ in range(N)]
    clusters = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not visited[r][c]:
                q = deque([(r,c)])
                visited[r][c] = True
                cluster = [(r,c)]
                while q:
                    cr, cc = q.popleft()
                    for nr, nc in neighbors(cr, cc):
                        if board[nr][nc] == 1 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            q.append((nr,nc))
                            cluster.append((nr,nc))
                clusters.append(cluster)

    # Probability map
    score = [[0]*N for _ in range(N)]

    for L in ships:
        # horizontal
        for r in range(N):
            for c in range(N-L+1):
                cells = [(r, c+i) for i in range(L)]
                if any(board[rr][cc] == -1 for rr,cc in cells):
                    continue
                hit_count = sum(1 for rr,cc in cells if board[rr][cc] == 1)
                weight = 1 + 4*hit_count
                for rr,cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += weight
        # vertical
        for r in range(N-L+1):
            for c in range(N):
                cells = [(r+i, c) for i in range(L)]
                if any(board[rr][cc] == -1 for rr,cc in cells):
                    continue
                hit_count = sum(1 for rr,cc in cells if board[rr][cc] == 1)
                weight = 1 + 4*hit_count
                for rr,cc in cells:
                    if board[rr][cc] == 0:
                        score[rr][cc] += weight

    # Target mode candidates
    candidates = set()
    for cluster in clusters:
        if len(cluster) >= 2:
            rows = {r for r,_ in cluster}
            cols = {c for _,c in cluster}
            if len(rows) == 1:
                # horizontal
                r = next(iter(rows))
                minc = min(c for _,c in cluster)
                maxc = max(c for _,c in cluster)
                for nc in [minc-1, maxc+1]:
                    if 0 <= nc < N and board[r][nc] == 0:
                        candidates.add((r,nc))
            elif len(cols) == 1:
                # vertical
                c = next(iter(cols))
                minr = min(r for r,_ in cluster)
                maxr = max(r for r,_ in cluster)
                for nr in [minr-1, maxr+1]:
                    if 0 <= nr < N and board[nr][c] == 0:
                        candidates.add((nr,c))
        else:
            r, c = cluster[0]
            for nr, nc in neighbors(r,c):
                if board[nr][nc] == 0:
                    candidates.add((nr,nc))

    # If we have candidates, choose the highest probability one
    if candidates:
        best = max(candidates, key=lambda rc: score[rc[0]][rc[1]])
        return best

    # Otherwise choose best from probability map
    max_score = -1
    best_cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                if score[r][c] > max_score:
                    max_score = score[r][c]
                    best_cells = [(r,c)]
                elif score[r][c] == max_score:
                    best_cells.append((r,c))
    if best_cells:
        return random.choice(best_cells)

    # Fallback (should not happen)
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r,c)
    return (0,0)
