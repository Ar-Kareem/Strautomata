
def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        N = 10
        # helpers to safely read board
        def val(r, c):
            try:
                return board[r][c]
            except Exception:
                return -1

        # collect hits
        hits = []
        for r in range(N):
            for c in range(N):
                try:
                    if board[r][c] == 1:
                        hits.append((r, c))
                except Exception:
                    continue

        # find orthogonal hit components via BFS
        hit_set = set(hits)
        visited = set()
        comps = []
        dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for h in hits:
            if h in visited:
                continue
            stack = [h]
            visited.add(h)
            comp = []
            while stack:
                cr, cc = stack.pop()
                comp.append((cr, cc))
                for dr, dc in dirs:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < N and 0 <= nc < N and (nr, nc) in hit_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
            comps.append(comp)

        # classify active vs inactive: active has orthogonal unknown neighbour
        active_set = set()
        inactive_set = set()
        active_comps = []
        inactive_comps = []
        for comp in comps:
            is_active = False
            for (r, c) in comp:
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N:
                        try:
                            if board[nr][nc] == 0:
                                is_active = True
                                break
                        except Exception:
                            continue
                if is_active:
                    break
            if is_active:
                active_comps.append(comp)
                for cell in comp:
                    active_set.add(cell)
            else:
                inactive_comps.append(comp)
                for cell in comp:
                    inactive_set.add(cell)

        # estimate remaining fleet
        remaining = [5, 4, 3, 3, 2]
        for comp in inactive_comps:
            if not comp:
                continue
            rs = set(r for r, _ in comp)
            cs = set(c for _, c in comp)
            straight = (len(rs) == 1 or len(cs) == 1)
            if straight:
                k = len(comp)
                if k in remaining:
                    remaining.remove(k)
                # else: touching / anomaly, do not remove
            # non-straight (touching ships) -> do not remove
        if not remaining:
            # all sunk (should be game over) keep a dummy for scoring
            remaining_for_score = [2]
        else:
            remaining_for_score = remaining

        # allowed cells for new ship placements: unknown or active hit
        # blocked = miss or inactive hit
        def is_allowed(r, c):
            if (r, c) in active_set:
                return True
            try:
                return board[r][c] == 0
            except Exception:
                return False

        def is_unknown(r, c):
            try:
                return board[r][c] == 0
            except Exception:
                return False

        # precompute valid placements per length to reuse
        # placement list: (cells_list, touches_active)
        # for speed compute on fly per length
        # hunt scores: counts of valid placements covering cell
        hunt = [[0]*N for _ in range(N)]
        # target scores: valid placements covering cell AND touching active_set
        target = [[0]*N for _ in range(N)]

        has_active = len(active_set) > 0

        for L in remaining_for_score:
            # horizontal
            for r in range(N):
                for c in range(N - L + 1):
                    ok = True
                    touches = False
                    for k in range(L):
                        cc = c + k
                        if not is_allowed(r, cc):
                            ok = False
                            break
                        if (r, cc) in active_set:
                            touches = True
                    if not ok:
                        continue
                    for k in range(L):
                        cc = c + k
                        if is_unknown(r, cc):
                            hunt[r][cc] += 1
                            if touches and has_active:
                                target[r][cc] += 1
            # vertical
            for r in range(N - L + 1):
                for c in range(N):
                    ok = True
                    touches = False
                    for k in range(L):
                        rr = r + k
                        if not is_allowed(rr, c):
                            ok = False
                            break
                        if (rr, c) in active_set:
                            touches = True
                    if not ok:
                        continue
                    for k in range(L):
                        rr = r + k
                        if is_unknown(rr, c):
                            hunt[rr][c] += 1
                            if touches and has_active:
                                target[rr][c] += 1

        def first_unknown():
            for r in range(N):
                for c in range(N):
                    if is_unknown(r, c):
                        return (r, c)
            return (0, 0)

        if has_active:
            frontier = []
            for r in range(N):
                for c in range(N):
                    if not is_unknown(r, c):
                        continue
                    adj = False
                    for dr, dc in dirs:
                        nr, nc = r + dr, c + dc
                        if (nr, nc) in active_set:
                            adj = True
                            break
                    if adj:
                        frontier.append((r, c))
            if not frontier:
                # fallback to hunt among unknowns
                best = None
                best_key = None
                for r in range(N):
                    for c in range(N):
                        if not is_unknown(r, c):
                            continue
                        parity = 1 if (r + c) % 2 == 0 else 0
                        center = -(abs(r - 4.5) + abs(c - 4.5))
                        key = (hunt[r][c], parity, center)
                        if best_key is None or key > best_key:
                            best_key = key
                            best = (r, c)
                if best is not None:
                    return best
                return first_unknown()

            # orientation-aware filtering: for aligned multi-hit comps, prefer ends
            # Build set of preferred end cells
            end_cells = set()
            multi_aligned_exists = False
            for comp in active_comps:
                if len(comp) <= 1:
                    continue
                rs = set(r for r, _ in comp)
                cs = set(c for _, c in comp)
                if len(rs) == 1:
                    multi_aligned_exists = True
                    r0 = next(iter(rs))
                    minc = min(c for _, c in comp)
                    maxc = max(c for _, c in comp)
                    for cc in (minc - 1, maxc + 1):
                        if 0 <= cc < N and is_unknown(r0, cc):
                            end_cells.add((r0, cc))
                elif len(cs) == 1:
                    multi_aligned_exists = True
                    c0 = next(iter(cs))
                    minr = min(r for r, _ in comp)
                    maxr = max(r for r, _ in comp)
                    for rr in (minr - 1, maxr + 1):
                        if 0 <= rr < N and is_unknown(rr, c0):
                            end_cells.add((rr, c0))
                else:
                    pass

            # if we have end cells, restrict to them if they intersect frontier
            # but only if they belong to a component that still needs extension
            # keep all frontier if end_cells empty
            candidates = frontier
            filtered = [cell for cell in frontier if cell in end_cells]
            # Only filter if filtered non-empty and there is at least one multi-aligned comp
            # To avoid ignoring a second single-hit component, only filter when
            # all active comps are multi-aligned? Better: if filtered exists, boost them
            # rather than hard filter. We implement boosting via bonus.
            best = None
            best_key = None
            for (r, c) in candidates:
                bonus_end = 1000000 if (r, c) in end_cells else 0
                # primary: target + bonus, secondary hunt, then parity/center
                # bonus_end ensures ends chosen first
                key = (bonus_end + target[r][c], hunt[r][c], 1 if (r + c) % 2 == 0 else 0, -(abs(r - 4.5) + abs(c - 4.5)))
                if best_key is None or key > best_key:
                    best_key = key
                    best = (r, c)
            if best is not None:
                return best
            return first_unknown()
        else:
            # hunt mode
            best = None
            best_key = None
            for r in range(N):
                for c in range(N):
                    if not is_unknown(r, c):
                        continue
                    parity = 1 if (r + c) % 2 == 0 else 0
                    center = -(abs(r - 4.5) + abs(c - 4.5))
                    key = (hunt[r][c], parity, center)
                    if best_key is None or key > best_key:
                        best_key = key
                        best = (r, c)
            if best is not None:
                return best
            return first_unknown()
    except Exception:
        # absolute failsafe: scan for unknown
        try:
            for r in range(10):
                for c in range(10):
                    try:
                        if board[r][c] == 0:
                            return (r, c)
                    except Exception:
                        continue
        except Exception:
            pass
        return (0, 0)
