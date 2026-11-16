
def policy(board):
    N = 10
    # helper: find clusters of hits
    visited = [[False]*N for _ in range(N)]
    clusters = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not visited[r][c]:
                # BFS
                q = [(r,c)]
                visited[r][c] = True
                cells = []
                while q:
                    x,y = q.pop()
                    cells.append((x,y))
                    for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                        nx,ny = x+dx, y+dy
                        if 0 <= nx < N and 0 <= ny < N and not visited[nx][ny] and board[nx][ny]==1:
                            visited[nx][ny] = True
                            q.append((nx,ny))
                clusters.append(cells)

    # density map for tie-break and hunt
    def compute_density():
        lengths = [5,4,3,3,2]
        density = [[0]*N for _ in range(N)]
        for L in lengths:
            # horizontal
            for r in range(N):
                for c in range(N-L+1):
                    ok = True
                    for i in range(L):
                        if board[r][c+i] == -1:
                            ok = False
                            break
                    if ok:
                        for i in range(L):
                            density[r][c+i] += 1
            # vertical
            for c in range(N):
                for r in range(N-L+1):
                    ok = True
                    for i in range(L):
                        if board[r+i][c] == -1:
                            ok = False
                            break
                    if ok:
                        for i in range(L):
                            density[r+i][c] += 1
        return density

    density = compute_density()

    # helper: line run length (not through misses)
    def line_run(r,c,dr,dc):
        count = 1
        # forward
        x,y = r+dr, c+dc
        while 0 <= x < N and 0 <= y < N and board[x][y] != -1:
            count += 1
            x,y = x+dr, y+dc
        # backward
        x,y = r-dr, c-dc
        while 0 <= x < N and 0 <= y < N and board[x][y] != -1:
            count += 1
            x,y = x-dr, y-dc
        return count

    # build candidate list if we have hits
    candidates = []
    for cells in clusters:
        size = len(cells)
        rows = {r for r,c in cells}
        cols = {c for r,c in cells}
        orientation = None
        if len(rows) == 1:
            orientation = 'H'
        elif len(cols) == 1:
            orientation = 'V'

        if orientation == 'H':
            r = next(iter(rows))
            minc = min(c for _,c in cells)
            maxc = max(c for _,c in cells)
            for nc in [minc-1, maxc+1]:
                if 0 <= nc < N and board[r][nc] == 0:
                    score = size*100 + line_run(r,nc,0,1) + density[r][nc]
                    candidates.append((score, r, nc))
        elif orientation == 'V':
            c = next(iter(cols))
            minr = min(r for r,_ in cells)
            maxr = max(r for r,_ in cells)
            for nr in [minr-1, maxr+1]:
                if 0 <= nr < N and board[nr][c] == 0:
                    score = size*100 + line_run(nr,c,1,0) + density[nr][c]
                    candidates.append((score, nr, c))
        else:
            # unknown orientation: try neighbors
            seen = set()
            for r,c in cells:
                for dr,dc in [(1,0),(-1,0),(0,1),(0,-1)]:
                    nr,nc = r+dr, c+dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                        if (nr,nc) in seen: 
                            continue
                        seen.add((nr,nc))
                        score = size*100 + max(line_run(nr,nc,1,0), line_run(nr,nc,0,1)) + density[nr][nc]
                        candidates.append((score, nr, nc))

    if candidates:
        # choose best score, tie by smallest row/col
        candidates.sort(key=lambda x: (-x[0], x[1], x[2]))
        _, r, c = candidates[0]
        return (r,c)

    # Hunt mode: choose highest density unknown
    best = None
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                score = density[r][c]
                if best is None or score > best[0] or (score == best[0] and (r,c) < (best[1],best[2])):
                    best = (score, r, c)
    if best:
        return (best[1], best[2])

    # fallback (should never happen)
    return (0,0)
