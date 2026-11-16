
import collections

SHIPS = [5, 4, 3, 3, 2]

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        return _policy(board)
    except Exception:
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)

def _policy(board):
    N = 10
    # collect hits
    hits = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                hits.append((r, c))

    hunt = _hunt_heat(board)

    if not hits:
        return _argmax_heat(hunt, board)

    clusters = _clusters(board)

    target = [[0]*N for _ in range(N)]
    _build_target_heat(board, clusters, target)

    candidates = _candidates(board, clusters)

    if not candidates:
        # no adjacent moves, fall back to hunt
        return _argmax_heat(hunt, board)

    # pick best candidate by (target, hunt)
    best = None
    best_key = (-1, -1)
    for (r, c) in candidates:
        key = (target[r][c], hunt[r][c])
        if key > best_key:
            best_key = key
            best = (r, c)
    if best is not None:
        return best
    return _argmax_heat(hunt, board)

def _hunt_heat(board):
    N = 10
    hunt = [[0]*N for _ in range(N)]
    for L in SHIPS:
        # horizontal
        for r in range(N):
            for sc in range(N - L + 1):
                ok = True
                for k in range(L):
                    if board[r][sc+k] == -1:
                        ok = False
                        break
                if not ok:
                    continue
                for k in range(L):
                    rr, cc = r, sc+k
                    if board[rr][cc] == 0:
                        hunt[rr][cc] += 1
                    elif board[rr][cc] == 1:
                        # placement covering a hit is still consistent,
                        # but don't score hit cells themselves
                        pass
        # vertical
        for c in range(N):
            for sr in range(N - L + 1):
                ok = True
                for k in range(L):
                    if board[sr+k][c] == -1:
                        ok = False
                        break
                if not ok:
                    continue
                for k in range(L):
                    rr, cc = sr+k, c
                    if board[rr][cc] == 0:
                        hunt[rr][cc] += 1
    return hunt

def _clusters(board):
    N = 10
    visited = [[False]*N for _ in range(N)]
    clusters = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1 and not visited[r][c]:
                q = collections.deque()
                q.append((r, c))
                visited[r][c] = True
                cur = []
                while q:
                    cr, cc = q.popleft()
                    cur.append((cr, cc))
                    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                        nr, nc = cr+dr, cc+dc
                        if 0 <= nr < N and 0 <= nc < N:
                            if not visited[nr][nc] and board[nr][nc] == 1:
                                visited[nr][nc] = True
                                q.append((nr, nc))
                clusters.append(cur)
    return clusters

def _build_target_heat(board, clusters, target):
    N = 10
    # use unique lengths with multiplicity to reflect two 3-ships
    for cl in clusters:
        if len(cl) == 1:
            r, c = cl[0]
            for L in SHIPS:
                # horizontal covering (r,c)
                for s in range(c - L + 1, c + 1):
                    if s < 0 or s + L > N:
                        continue
                    ok = True
                    for k in range(L):
                        if board[r][s+k] == -1:
                            ok = False
                            break
                    if not ok:
                        continue
                    for k in range(L):
                        cc = s+k
                        if board[r][cc] == 0:
                            target[r][cc] += 1
                # vertical covering (r,c)
                for s in range(r - L + 1, r + 1):
                    if s < 0 or s + L > N:
                        continue
                    ok = True
                    for k in range(L):
                        if board[s+k][c] == -1:
                            ok = False
                            break
                    if not ok:
                        continue
                    for k in range(L):
                        rr = s+k
                        if board[rr][c] == 0:
                            target[rr][c] += 1
        else:
            rows = set(r for r, c in cl)
            cols = set(c for r, c in cl)
            if len(rows) == 1:
                r = next(iter(rows))
                cmin = min(c for _, c in cl)
                cmax = max(c for _, c in cl)
                klen = cmax - cmin + 1
                # if gaps contain a miss, this cluster cannot be one ship,
                # but placements containing it are still filtered by miss check
                for L in SHIPS:
                    if L < klen:
                        continue
                    # also need L >= len(cl)
                    if L < len(cl):
                        continue
                    for s in range(cmax - L + 1, cmin + 1):
                        if s < 0 or s + L > N:
                            continue
                        ok = True
                        for kk in range(L):
                            if board[r][s+kk] == -1:
                                ok = False
                                break
                        if not ok:
                            continue
                        for kk in range(L):
                            cc = s+kk
                            if board[r][cc] == 0:
                                target[r][cc] += 1
            elif len(cols) == 1:
                c = next(iter(cols))
                rmin = min(r for r, _ in cl)
                rmax = max(r for r, _ in cl)
                klen = rmax - rmin + 1
                for L in SHIPS:
                    if L < klen:
                        continue
                    if L < len(cl):
                        continue
                    for s in range(rmax - L + 1, rmin + 1):
                        if s < 0 or s + L > N:
                            continue
                        ok = True
                        for kk in range(L):
                            if board[s+kk][c] == -1:
                                ok = False
                                break
                        if not ok:
                            continue
                        for kk in range(L):
                            rr = s+kk
                            if board[rr][c] == 0:
                                target[rr][c] += 1
            else:
                # L-shaped touching ships: no linear placement can contain it
                # leave target heat to singleton logic per cell as fallback
                # add small votes from each cell's placements
                for (r, c) in cl:
                    for L in SHIPS:
                        for s in range(c - L + 1, c + 1):
                            if s < 0 or s + L > N:
                                continue
                            ok = True
                            for k in range(L):
                                if board[r][s+k] == -1:
                                    ok = False
                                    break
                            if not ok:
                                continue
                            # only count if placement does not cross another hit
                            # that would break linearity? allow it
                            for k in range(L):
                                cc = s+k
                                if board[r][cc] == 0:
                                    # low weight
                                    pass
                        for s in range(r - L + 1, r + 1):
                            if s < 0 or s + L > N:
                                continue
                            ok = True
                            for k in range(L):
                                if board[s+k][c] == -1:
                                    ok = False
                                    break
                            if not ok:
                                continue
                pass

def _candidates(board, clusters):
    N = 10
    cand = set()
    for cl in clusters:
        if len(cl) == 1:
            r, c = cl[0]
            for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                nr, nc = r+dr, c+dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    cand.add((nr, nc))
        else:
            rows = set(r for r, c in cl)
            cols = set(c for r, c in cl)
            if len(rows) == 1:
                r = next(iter(rows))
                cmin = min(c for _, c in cl)
                cmax = max(c for _, c in cl)
                if cmin-1 >= 0 and board[r][cmin-1] == 0:
                    cand.add((r, cmin-1))
                if cmax+1 < N and board[r][cmax+1] == 0:
                    cand.add((r, cmax+1))
                # if both ends blocked, this cluster is done -> no candidates
            elif len(cols) == 1:
                c = next(iter(cols))
                rmin = min(r for r, _ in cl)
                rmax = max(r for r, _ in cl)
                if rmin-1 >= 0 and board[rmin-1][c] == 0:
                    cand.add((rmin-1, c))
                if rmax+1 < N and board[rmax+1][c] == 0:
                    cand.add((rmax+1, c))
            else:
                for (r, c) in cl:
                    for dr, dc in ((1,0),(-1,0),(0,1),(0,-1)):
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                            cand.add((nr, nc))
    return cand

def _argmax_heat(heat, board):
    N = 10
    best = None
    best_v = -1
    for r in range(N):
        for c in range(N):
            if board[r][c] != 0:
                continue
            v = heat[r][c]
            if v > best_v:
                best_v = v
                best = (r, c)
    if best is not None:
        return best
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)
