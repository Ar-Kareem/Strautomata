
def policy(board: list[list[int]]) -> tuple[int, int]:
    N = 10
    try:
        # --- collect hits ---
        # BFS for 4-connected hit components
        visited = set()
        comps = []
        for r in range(N):
            for c in range(N):
                if board[r][c] == 1 and (r, c) not in visited:
                    stack = [(r, c)]
                    visited.add((r, c))
                    comp = []
                    while stack:
                        cr, cc = stack.pop()
                        comp.append((cr, cc))
                        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < N and 0 <= nc < N:
                                if board[nr][nc] == 1 and (nr, nc) not in visited:
                                    visited.add((nr, nc))
                                    stack.append((nr, nc))
                    comps.append(comp)

        sunk_set = set()
        active_comps = []

        for comp in comps:
            rows = set(r for r, c in comp)
            cols = set(c for r, c in comp)
            # non-linear -> must be touching ships, treat as active
            if len(rows) > 1 and len(cols) > 1:
                active_comps.append(comp)
                continue
            if len(comp) == 1:
                r, c = comp[0]
                # if surrounded with no unknown neighbour, ignore (inconsistent)
                has_unknown = False
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                        has_unknown = True
                        break
                if has_unknown:
                    active_comps.append(comp)
                else:
                    sunk_set.update(comp)
                continue
            # len >= 2 linear
            if len(rows) == 1:  # horizontal
                r = next(iter(rows))
                minc = min(cols)
                maxc = max(cols)
                left_blocked = (minc - 1 < 0 or board[r][minc - 1] == -1)
                right_blocked = (maxc + 1 >= N or board[r][maxc + 1] == -1)
                # if neighbour is a hit it would be in same comp, so only miss/edge blocks
                # also if neighbour is out of comp but is hit of other comp touching side-by-side?
                # that would imply non-linear merge, already handled; for ends, hit would merge
                if left_blocked and right_blocked:
                    sunk_set.update(comp)
                else:
                    active_comps.append(comp)
            else:  # vertical
                c = next(iter(cols))
                minr = min(rows)
                maxr = max(rows)
                top_blocked = (minr - 1 < 0 or board[minr - 1][c] == -1)
                bot_blocked = (maxr + 1 >= N or board[maxr + 1][c] == -1)
                if top_blocked and bot_blocked:
                    sunk_set.update(comp)
                else:
                    active_comps.append(comp)

        # --- remaining fleet ---
        full_fleet = [5, 4, 3, 3, 2]
        remaining = list(full_fleet)
        # remove one ship per sunk component if length matches
        for comp in comps:
            # check if this comp is sunk (all cells in sunk_set)
            if all((r, c) in sunk_set for r, c in comp):
                L = len(comp)
                if L in remaining:
                    remaining.remove(L)
                # if L > 5 or not in remaining (merged ships), do nothing
        if not remaining:
            # all sunk or inconsistent; use smallest to keep heatmap defined
            # if game not over this happens only on inconsistency
            lengths_for_heat = list(full_fleet)
        else:
            lengths_for_heat = remaining

        # helper to compute heatmap
        def compute_heat(require_active, active_set):
            heat = [[0] * N for _ in range(N)]
            for L in lengths_for_heat:
                # horizontal
                for r in range(N):
                    for c in range(N - L + 1):
                        cells = [(r, c + k) for k in range(L)]
                        ok = True
                        touches = False
                        for (rr, cc) in cells:
                            if board[rr][cc] == -1:
                                ok = False
                                break
                            if (rr, cc) in sunk_set:
                                ok = False
                                break
                            if (rr, cc) in active_set:
                                touches = True
                        if not ok:
                            continue
                        if require_active and not touches:
                            continue
                        for (rr, cc) in cells:
                            if board[rr][cc] == 0:
                                heat[rr][cc] += 1
                # vertical
                for r in range(N - L + 1):
                    for c in range(N):
                        cells = [(r + k, c) for k in range(L)]
                        ok = True
                        touches = False
                        for (rr, cc) in cells:
                            if board[rr][cc] == -1:
                                ok = False
                                break
                            if (rr, cc) in sunk_set:
                                ok = False
                                break
                            if (rr, cc) in active_set:
                                touches = True
                        if not ok:
                            continue
                        if require_active and not touches:
                            continue
                        for (rr, cc) in cells:
                            if board[rr][cc] == 0:
                                heat[rr][cc] += 1
            return heat

        # --- target mode ---
        if active_comps:
            active_set = set()
            for comp in active_comps:
                active_set.update(comp)

            frontier = set()
            for comp in active_comps:
                if len(comp) == 1:
                    r, c = comp[0]
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                            frontier.add((nr, nc))
                else:
                    rows = set(r for r, c in comp)
                    cols = set(c for r, c in comp)
                    if len(rows) == 1:  # horizontal, only ends
                        r = next(iter(rows))
                        minc = min(cols)
                        maxc = max(cols)
                        for cc in (minc - 1, maxc + 1):
                            if 0 <= cc < N and board[r][cc] == 0:
                                frontier.add((r, cc))
                    else:  # vertical, only ends
                        c = next(iter(cols))
                        minr = min(rows)
                        maxr = max(rows)
                        for rr in (minr - 1, maxr + 1):
                            if 0 <= rr < N and board[rr][c] == 0:
                                frontier.add((rr, c))
            # fallback if ends blocked but still active (should not happen)
            if not frontier:
                for (r, c) in active_set:
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                            frontier.add((nr, nc))

            if frontier:
                thet = compute_heat(True, active_set)
                # if target heat all zero (over-constrained), fall back to hunt heat
                max_t = max(thet[r][c] for r, c in frontier)
                if max_t <= 0:
                    thet = compute_heat(False, set())
                    # mask to avoid sunk? already avoided
                best = None
                best_key = None
                for (r, c) in frontier:
                    h = thet[r][c]
                    # tie-break: centre proximity (prefer centre slightly)
                    dist = abs(r - 4.5) + abs(c - 4.5)
                    key = (h, -dist)
                    if best_key is None or key > best_key:
                        best_key = key
                        best = (r, c)
                if best is not None and board[best[0]][best[1]] == 0:
                    return (int(best[0]), int(best[1]))

        # --- hunt mode ---
        active_empty = set()
        heat = compute_heat(False, active_empty)
        best = None
        best_key = None
        for r in range(N):
            for c in range(N):
                if board[r][c] != 0:
                    continue
                h = heat[r][c]
                parity = 1 if (r + c) % 2 == 0 else 0
                dist = abs(r - 4.5) + abs(c - 4.5)
                key = (h, parity, -dist)
                if best_key is None or key > best_key:
                    best_key = key
                    best = (r, c)
        if best is not None:
            return (int(best[0]), int(best[1]))

        # ultimate fallback
        for r in range(N):
            for c in range(N):
                if board[r][c] == 0:
                    return (r, c)
        return (0, 0)
    except Exception:
        # guarantee legal move
        try:
            for r in range(10):
                for c in range(10):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
