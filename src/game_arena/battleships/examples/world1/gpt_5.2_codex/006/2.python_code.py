
import random

SHIP_LENGTHS = [5, 4, 3, 3, 2]

def hunt_scores(board):
    scores = [[0 for _ in range(10)] for _ in range(10)]
    for L in SHIP_LENGTHS:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - L + 1):
                cells = [(r, c + k) for k in range(L)]
                if any(board[x][y] == -1 for x, y in cells):
                    continue
                for x, y in cells:
                    if board[x][y] == 0:
                        scores[x][y] += 1
        # Vertical placements
        for r in range(10 - L + 1):
            for c in range(10):
                cells = [(r + k, c) for k in range(L)]
                if any(board[x][y] == -1 for x, y in cells):
                    continue
                for x, y in cells:
                    if board[x][y] == 0:
                        scores[x][y] += 1
    return scores

def get_hit_clusters(board):
    visited = [[False]*10 for _ in range(10)]
    clusters = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and not visited[r][c]:
                stack = [(r,c)]
                visited[r][c] = True
                cluster = []
                while stack:
                    x,y = stack.pop()
                    cluster.append((x,y))
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx, ny = x+dx, y+dy
                        if 0 <= nx < 10 and 0 <= ny < 10:
                            if board[nx][ny] == 1 and not visited[nx][ny]:
                                visited[nx][ny] = True
                                stack.append((nx,ny))
                clusters.append(cluster)
    return clusters

def policy(board: list[list[int]]) -> tuple[int, int]:
    scores = hunt_scores(board)
    clusters = get_hit_clusters(board)
    candidates = []

    # Target mode: generate candidates around hits
    for cluster in clusters:
        if len(cluster) > 1:
            rows = {r for r,_ in cluster}
            cols = {c for _,c in cluster}
            if len(rows) == 1:  # horizontal
                r = next(iter(rows))
                minc = min(c for _,c in cluster)
                maxc = max(c for _,c in cluster)
                for nc in [minc-1, maxc+1]:
                    if 0 <= nc < 10 and board[r][nc] == 0:
                        candidates.append((r,nc))
            elif len(cols) == 1:  # vertical
                c = next(iter(cols))
                minr = min(r for r,_ in cluster)
                maxr = max(r for r,_ in cluster)
                for nr in [minr-1, maxr+1]:
                    if 0 <= nr < 10 and board[nr][c] == 0:
                        candidates.append((nr,c))
            else:
                # irregular cluster, treat like singles
                for r,c in cluster:
                    for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                            candidates.append((nr,nc))
        else:
            r,c = cluster[0]
            for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidates.append((nr,nc))

    if candidates:
        # choose candidate with highest score + adjacency bonus
        best = None
        best_score = -1
        for r,c in candidates:
            adj_hits = 0
            for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                nr, nc = r+dr, c+dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    adj_hits += 1
            s = scores[r][c] + 10*adj_hits
            if s > best_score:
                best_score = s
                best = (r,c)
        return best

    # Hunt mode: pick highest probability cell
    best = None
    best_score = -1
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                s = scores[r][c]
                if s > best_score:
                    best_score = s
                    best = (r,c)

    # Fallback: any unknown cell
    if best is not None:
        return best

    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r,c)

    # Should never happen
    return (0,0)
