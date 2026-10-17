
def _neighbors(r, c):
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < 10 and 0 <= nc < 10:
            yield nr, nc

def _components(board):
    visited = [[False]*10 for _ in range(10)]
    comps = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and not visited[r][c]:
                stack = [(r, c)]
                visited[r][c] = True
                cur = []
                while stack:
                    cr, cc = stack.pop()
                    cur.append((cr, cc))
                    for nr, nc in _neighbors(cr, cc):
                        if board[nr][nc] == 1 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cur)
    return comps

def _classify(board, comps):
    remaining = [5, 4, 3, 3, 2]
    sunk_cells = set()
    unsunk_comps = []
    # process larger first so removal is stable
    comps_sorted = sorted(comps, key=len, reverse=True)
    for comp in comps_sorted:
        if len(comp) == 1:
            unsunk_comps.append(comp)
            continue
        rows = set(r for r, c in comp)
        cols = set(c for r, c in comp)
        if len(rows) > 1 and len(cols) > 1:
            # L-shape -> touching ships, keep as unsunk
            unsunk_comps.append(comp)
            continue
        # linear
        if len(rows) == 1:
            r = next(iter(rows))
            cmin = min(c for _, c in comp)
            cmax = max(c for _, c in comp)
            # check contiguity: connected linear implies contiguous
            # blocked ends?
            low_blocked = (cmin == 0) or (board[r][cmin-1] == -1)
            high_blocked = (cmax == 9) or (board[r][cmax+1] == -1)
            # also if there is sunk cell confusion, only use miss/edge
            if low_blocked and high_blocked:
                L = len(comp)
                # ensure contiguous (cmax-cmin+1 == L) else not simple sunk
                if (cmax - cmin + 1 == L) and (L in remaining):
                    remaining.remove(L)
                    for cell in comp:
                        sunk_cells.add(cell)
                    continue
            unsunk_comps.append(comp)
        else:
            c = next(iter(cols))
            rmin = min(r for r, _ in comp)
            rmax = max(r for r, _ in comp)
            low_blocked = (rmin == 0) or (board[rmin-1][c] == -1)
            high_blocked = (rmax == 9) or (board[rmax+1][c] == -1)
            if low_blocked and high_blocked:
                L = len(comp)
                if (rmax - rmin + 1 == L) and (L in remaining):
                    remaining.remove(L)
                    for cell in comp:
                        sunk_cells.add(cell)
                    continue
            unsunk_comps.append(comp)
    unsunk_cells = set()
    for comp in unsunk_comps:
        for cell in comp:
            unsunk_cells.add(cell)
    return remaining, sunk_cells, unsunk_cells, unsunk_comps

def _heatmap(board, remaining, sunk_cells, unsunk_cells):
    heat = [[0]*10 for _ in range(10)]
    has_target = len(unsunk_cells) > 0
    for L in remaining:
        # horizontal
        for r in range(10):
            for c in range(10 - L + 1):
                cells = [(r, c+i) for i in range(L)]
                bad = False
                touches = False
                for (rr, cc) in cells:
                    if board[rr][cc] == -1:
                        bad = True
                        break
                    if (rr, cc) in sunk_cells:
                        bad = True
                        break
                    if (rr, cc) in unsunk_cells:
                        touches = True
                if bad:
                    continue
                if has_target and not touches:
                    continue
                for (rr, cc) in cells:
                    heat[rr][cc] += 1
        # vertical
        for r in range(10 - L + 1):
            for c in range(10):
                cells = [(r+i, c) for i in range(L)]
                bad = False
                touches = False
                for (rr, cc) in cells:
                    if board[rr][cc] == -1:
                        bad = True
                        break
                    if (rr, cc) in sunk_cells:
                        bad = True
                        break
                    if (rr, cc) in unsunk_cells:
                        touches = True
                if bad:
                    continue
                if has_target and not touches:
                    continue
                for (rr, cc) in cells:
                    heat[rr][cc] += 1
    return heat

def _best_by_heat(cands, heat):
    # cands: iterable of (r,c)
    best = None
    best_key = None
    for (r, c) in cands:
        # key: heat desc, parity pref, center pref
        parity = 0 if (r + c) % 2 == 0 else 1
        center = abs(r - 4.5) + abs(c - 4.5)
        # use tuple for max: (heat, -parity, -center)
        key = (heat[r][c], -parity, -center)
        if best_key is None or key > best_key:
            best_key = key
            best = (r, c)
    return best

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        # sanitize board access
        b = [[0]*10 for _ in range(10)]
        for r in range(10):
            for c in range(10):
                try:
                    v = board[r][c]
                except Exception:
                    v = 0
                if v not in (-1, 0, 1):
                    v = 0
                b[r][c] = v

        comps = _components(b)
        remaining, sunk_cells, unsunk_cells, unsunk_comps = _classify(b, comps)
        if not remaining:
            remaining = [5, 4, 3, 3, 2]

        heat = _heatmap(b, remaining, sunk_cells, unsunk_cells)

        def is_unknown(r, c):
            return b[r][c] == 0

        # --- target mode ---
        if unsunk_cells:
            # gap cells between aligned unsunk hits
            gaps = set()
            # rows
            for r in range(10):
                cols = sorted([c for c in range(10) if (r, c) in unsunk_cells])
                for i in range(len(cols)-1):
                    c1, c2 = cols[i], cols[i+1]
                    d = c2 - c1
                    if 1 < d <= 5:
                        blocked = False
                        for k in range(c1+1, c2):
                            if b[r][k] == -1 or (r, k) in sunk_cells:
                                blocked = True
                                break
                        if not blocked:
                            for k in range(c1+1, c2):
                                if b[r][k] == 0:
                                    gaps.add((r, k))
            # cols
            for c in range(10):
                rows = sorted([r for r in range(10) if (r, c) in unsunk_cells])
                for i in range(len(rows)-1):
                    r1, r2 = rows[i], rows[i+1]
                    d = r2 - r1
                    if 1 < d <= 5:
                        blocked = False
                        for k in range(r1+1, r2):
                            if b[k][c] == -1 or (k, c) in sunk_cells:
                                blocked = True
                                break
                        if not blocked:
                            for k in range(r1+1, r2):
                                if b[k][c] == 0:
                                    gaps.add((k, c))
            gaps = [(r, c) for (r, c) in gaps if is_unknown(r, c)]
            if gaps:
                pick = _best_by_heat(gaps, heat)
                if pick is not None:
                    return pick

            ext = set()
            adj = set()
            for comp in unsunk_comps:
                if len(comp) == 1:
                    r, c = comp[0]
                    for nr, nc in _neighbors(r, c):
                        if is_unknown(nr, nc):
                            adj.add((nr, nc))
                else:
                    rows = set(r for r, c in comp)
                    cols = set(c for r, c in comp)
                    if len(rows) > 1 and len(cols) > 1:
                        for (r, c) in comp:
                            for nr, nc in _neighbors(r, c):
                                if is_unknown(nr, nc):
                                    adj.add((nr, nc))
                    elif len(rows) == 1:
                        r = next(iter(rows))
                        cmin = min(c for _, c in comp)
                        cmax = max(c for _, c in comp)
                        if cmin - 1 >= 0 and is_unknown(r, cmin-1):
                            ext.add((r, cmin-1))
                        if cmax + 1 < 10 and is_unknown(r, cmax+1):
                            ext.add((r, cmax+1))
                    else:
                        c = next(iter(cols))
                        rmin = min(r for r, _ in comp)
                        rmax = max(r for r, _ in comp)
                        if rmin - 1 >= 0 and is_unknown(rmin-1, c):
                            ext.add((rmin-1, c))
                        if rmax + 1 < 10 and is_unknown(rmax+1, c):
                            ext.add((rmax+1, c))
            if ext:
                pick = _best_by_heat(list(ext), heat)
                if pick is not None:
                    return pick
            if adj:
                pick = _best_by_heat(list(adj), heat)
                if pick is not None:
                    return pick
            # fallback within target: any neighbor unknown of unsunk
            # (covers edge cases)
            fallback_adj = []
            for (r, c) in unsunk_cells:
                for nr, nc in _neighbors(r, c):
                    if is_unknown(nr, nc):
                        fallback_adj.append((nr, nc))
            if fallback_adj:
                pick = _best_by_heat(fallback_adj, heat)
                if pick is not None:
                    return pick

        # --- hunt mode ---
        best = None
        best_key = None
        for r in range(10):
            for c in range(10):
                if not is_unknown(r, c):
                    continue
                parity = 0 if (r + c) % 2 == 0 else 1
                center = abs(r - 4.5) + abs(c - 4.5)
                key = (heat[r][c], -parity, -center, -(r*10+c))
                # we want max heat; iterate and keep max
                if best_key is None or key > best_key:
                    best_key = key
                    best = (r, c)
        if best is not None:
            return best

        # absolute fallback: first unknown
        for r in range(10):
            for c in range(10):
                if b[r][c] == 0:
                    return (r, c)
        # should never happen, but return legal-ish
        return (0, 0)
    except Exception:
        # guaranteed legal move
        try:
            for r in range(10):
                for c in range(10):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
