
def policy(board):
    N = 10
    SHIPS = (5, 4, 3, 3, 2)
    DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))

    hits = [[board[r][c] == 1 for c in range(N)] for r in range(N)]
    miss = [[board[r][c] == -1 for c in range(N)] for r in range(N)]
    unk = [[board[r][c] == 0 for c in range(N)] for r in range(N)]

    # ---- connected components of hits ----
    seen = [[False] * N for _ in range(N)]
    clusters = []
    for r0 in range(N):
        for c0 in range(N):
            if hits[r0][c0] and not seen[r0][c0]:
                comp, stack = [], [(r0, c0)]
                seen[r0][c0] = True
                while stack:
                    x, y = stack.pop()
                    comp.append((x, y))
                    for dx, dy in DIRS:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < N and 0 <= ny < N and hits[nx][ny] and not seen[nx][ny]:
                            seen[nx][ny] = True
                            stack.append((nx, ny))
                clusters.append(comp)

    # ---- classify clusters: sunk (closed) vs active ----
    remaining = list(SHIPS)
    active = []
    blocked = [[miss[r][c] for c in range(N)] for r in range(N)]

    def decompose(total):
        best = None
        m = len(remaining)
        for mask in range(1, 1 << m):
            s = cnt = 0
            has2 = False
            for i in range(m):
                if mask >> i & 1:
                    s += remaining[i]
                    cnt += 1
                    if remaining[i] == 2:
                        has2 = True
            if s == total:
                key = (has2, cnt)  # prefer keeping the 2-ship, then fewer ships
                if best is None or key < best[0]:
                    best = (key, mask)
        return best[1] if best else None

    for comp in clusters:
        if len(comp) == 1:
            r, c = comp[0]
            isolated = True
            for dx, dy in DIRS:
                nx, ny = r + dx, c + dy
                if 0 <= nx < N and 0 <= ny < N and not miss[nx][ny]:
                    isolated = False
                    break
            if isolated:
                blocked[r][c] = True
            else:
                active.append((r, c))
            continue
        rows = set(p[0] for p in comp)
        cols = set(p[1] for p in comp)
        if len(rows) == 1:
            r = comp[0][0]
            cs = sorted(p[1] for p in comp)
            ends = ((r, cs[0] - 1), (r, cs[-1] + 1))
        elif len(cols) == 1:
            c = comp[0][1]
            rs = sorted(p[0] for p in comp)
            ends = ((rs[0] - 1, c), (rs[-1] + 1, c))
        else:
            active.extend(comp)  # bent cluster => touching ships
            continue
        closed = True
        for er, ec in ends:
            if 0 <= er < N and 0 <= ec < N and not miss[er][ec]:
                closed = False
                break
        if closed:
            mask = decompose(len(comp))
            if mask is not None:
                for i in range(len(remaining) - 1, -1, -1):
                    if mask >> i & 1:
                        remaining.pop(i)
            for (r, c) in comp:
                blocked[r][c] = True
        else:
            active.extend(comp)

    if not remaining:
        remaining = [2, 3, 4, 5]

    # ---- all straight placements crossing no blocked cell ----
    def placements(L):
        for r in range(N):
            for c in range(N - L + 1):
                cells = [(r, c + i) for i in range(L)]
                if not any(blocked[x][y] for x, y in cells):
                    yield cells
        for c in range(N):
            for r in range(N - L + 1):
                cells = [(r + i, c) for i in range(L)]
                if not any(blocked[x][y] for x, y in cells):
                    yield cells

    center = [[-(abs(r - 4.5) + abs(c - 4.5)) for c in range(N)] for r in range(N)]

    # ---- TARGET MODE ----
    if active:
        active_set = set(active)
        for ship_lengths in (remaining, list(SHIPS)):
            heat = [[0.0] * N for _ in range(N)]
            for L in ship_lengths:
                for cells in placements(L):
                    cover = sum(1 for cell in cells if cell in active_set)
                    if cover == 0:
                        continue
                    w = 1.0 if cover == 1 else float(cover) ** 6
                    for (x, y) in cells:
                        if unk[x][y]:
                            heat[x][y] += w
            best = best_key = None
            for r in range(N):
                for c in range(N):
                    if unk[r][c] and heat[r][c] > 0:
                        key = (heat[r][c], center[r][c])
                        if best_key is None or key > best_key:
                            best_key, best = key, (r, c)
            if best is not None:
                return best
        for (r, c) in active:  # fallback: any unknown neighbour of a hit
            for dx, dy in DIRS:
                nx, ny = r + dx, c + dy
                if 0 <= nx < N and 0 <= ny < N and unk[nx][ny]:
                    return (nx, ny)

    # ---- HUNT MODE ----
    heat = [[0.0] * N for _ in range(N)]
    for L in remaining:
        for cells in placements(L):
            for (x, y) in cells:
                if unk[x][y]:
                    heat[x][y] += 1.0
    m = max(2, min(remaining))
    res_sum = [0.0] * m
    for r in range(N):
        for c in range(N):
            if unk[r][c]:
                res_sum[(r + c) % m] += heat[r][c]
    best_res = max(range(m), key=lambda k: res_sum[k])
    best = best_key = None
    for r in range(N):
        for c in range(N):
            if unk[r][c] and (r + c) % m == best_res:
                key = (heat[r][c], center[r][c])
                if best_key is None or key > best_key:
                    best_key, best = key, (r, c)
    if best is None:  # residue exhausted -> any unknown
        for r in range(N):
            for c in range(N):
                if unk[r][c]:
                    key = (heat[r][c], center[r][c])
                    if best_key is None or key > best_key:
                        best_key, best = key, (r, c)
    if best is not None:
        return best
    for r in range(N):  # absolute fallback
        for c in range(N):
            if unk[r][c]:
                return (r, c)
    return (0, 0)
