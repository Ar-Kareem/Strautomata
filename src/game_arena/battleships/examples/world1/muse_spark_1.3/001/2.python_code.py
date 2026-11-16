
_SHIPS = [5, 4, 3, 3, 2]

_PLACS = []
_CELL_MAP = {}

def _build():
    global _PLACS, _CELL_MAP
    for r in range(10):
        for c in range(10):
            _CELL_MAP[(r, c)] = []
    for L in _SHIPS:
        # horizontal
        for r in range(10):
            for c in range(10 - L + 1):
                cells = [(r, c + i) for i in range(L)]
                idx = len(_PLACS)
                _PLACS.append(cells)
                for cell in cells:
                    _CELL_MAP[cell].append(idx)
        # vertical
        for r in range(10 - L + 1):
            for c in range(10):
                cells = [(r + i, c) for i in range(L)]
                idx = len(_PLACS)
                _PLACS.append(cells)
                for cell in cells:
                    _CELL_MAP[cell].append(idx)

_build()

_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        # fast access, support list of lists
        # build miss / hit info
        hits = []
        for r in range(10):
            row = board[r]
            for c in range(10):
                if row[c] == 1:
                    hits.append((r, c))

        nplac = len(_PLACS)
        valid = [True] * nplac
        # filter placements that hit a miss
        for i in range(nplac):
            cells = _PLACS[i]
            for (rr, cc) in cells:
                if board[rr][cc] == -1:
                    valid[i] = False
                    break

        # hunt scores for all unknown cells
        hunt = [[0] * 10 for _ in range(10)]
        for i in range(nplac):
            if not valid[i]:
                continue
            cells = _PLACS[i]
            for (rr, cc) in cells:
                if board[rr][cc] == 0:
                    hunt[rr][cc] += 1

        if hits:
            visited = [[False] * 10 for _ in range(10)]
            hit_set = set(hits)
            clusters = []
            for (hr, hc) in hits:
                if visited[hr][hc]:
                    continue
                stack = [(hr, hc)]
                visited[hr][hc] = True
                comp = []
                while stack:
                    cr, cc = stack.pop()
                    comp.append((cr, cc))
                    for dr, dc in _DIRS:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 10 and 0 <= nc < 10:
                            if not visited[nr][nc] and (nr, nc) in hit_set:
                                visited[nr][nc] = True
                                stack.append((nr, nc))
                clusters.append(comp)

            active = []  # list of (comp, frontier set)
            for comp in clusters:
                frontier = set()
                for (hr, hc) in comp:
                    for dr, dc in _DIRS:
                        nr, nc = hr + dr, hc + dc
                        if 0 <= nr < 10 and 0 <= nc < 10:
                            if board[nr][nc] == 0:
                                frontier.add((nr, nc))
                if frontier:
                    active.append((comp, frontier))

            if active:
                maxsz = max(len(comp) for comp, fr in active)
                best_frontier = set()
                for comp, fr in active:
                    if len(comp) == maxsz:
                        best_frontier.update(fr)

                # score frontier with targeted placements
                best_cell = None
                best_key = None
                # sorted for determinism
                for (cr, cc) in sorted(best_frontier):
                    # neighbouring hits
                    neigh = []
                    for dr, dc in _DIRS:
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 10 and 0 <= nc < 10:
                            if board[nr][nc] == 1:
                                neigh.append((nr, nc))
                    if not neigh:
                        continue
                    neigh_set = set(neigh)
                    tscore = 0
                    for pi in _CELL_MAP[(cr, cc)]:
                        if not valid[pi]:
                            continue
                        cells = _PLACS[pi]
                        # must contain at least one neighbour hit
                        contains_neigh = False
                        for cell in cells:
                            if cell in neigh_set:
                                contains_neigh = True
                                break
                        if not contains_neigh:
                            continue
                        # count total hits covered
                        h = 0
                        for (rr, cc2) in cells:
                            if board[rr][cc2] == 1:
                                h += 1
                        # h >=1 guaranteed
                        tscore += 1 + 5 * (h - 1)
                    hscore = hunt[cr][cc]
                    parity = 1 if ((cr + cc) & 1) == 0 else 0
                    cdist = abs(cr - 4.5) + abs(cc - 4.5)
                    key = (tscore, hscore, parity, -cdist)
                    if best_key is None or key > best_key:
                        best_key = key
                        best_cell = (cr, cc)
                if best_cell is not None:
                    return (int(best_cell[0]), int(best_cell[1]))
                # if frontier scoring failed, fall through to hunt

        # hunt mode: pick max hunt score among unknowns
        best_cell = None
        best_key = None
        for r in range(10):
            for c in range(10):
                if board[r][c] != 0:
                    continue
                hscore = hunt[r][c]
                parity = 1 if ((r + c) & 1) == 0 else 0
                cdist = abs(r - 4.5) + abs(c - 4.5)
                key = (hscore, parity, -cdist)
                if best_key is None or key > best_key:
                    best_key = key
                    best_cell = (r, c)
        if best_cell is not None:
            return (int(best_cell[0]), int(best_cell[1]))
    except Exception:
        pass
    # guaranteed legal fallback
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
