
import random

N = 10
SHIPS = (5, 4, 3, 3, 2)
HIT_WEIGHT = 100.0
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _hit_components(hits):
    """Connected components (4-neighbourhood) of hit cells."""
    comps = []
    seen = set()
    for h in hits:
        if h in seen:
            continue
        comp = []
        stack = [h]
        seen.add(h)
        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in DIRS:
                nb = (r + dr, c + dc)
                if nb in hits and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        comps.append(comp)
    return comps


def _subset_summing(items, target):
    """Sub-multiset of items summing to target; prefer fewest, then largest."""
    best_key = None
    best = None
    n = len(items)
    for mask in range(1, 1 << n):
        total = 0
        chosen = []
        for i in range(n):
            if (mask >> i) & 1:
                total += items[i]
                chosen.append(items[i])
        if total == target:
            key = (len(chosen), tuple(-x for x in sorted(chosen, reverse=True)))
            if best_key is None or key < best_key:
                best_key = key
                best = chosen
    return best


def _classify(board, comps, remaining):
    """Split hit cells into 'live' (unfinished ships) and 'sunk' (fully
    revealed). Removes identified sunk ships from `remaining`."""
    live = set()
    sunk = set()
    info = []
    for comp in comps:
        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}
        straight = False
        closed = False
        if len(comp) == 1:
            # A lone hit is orientation-ambiguous: only treat as resolved
            # when completely boxed in by misses/edges.
            straight = True
            r, c = comp[0]
            closed = True
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] != -1:
                    closed = False
                    break
        elif len(rows) == 1:
            straight = True
            r = next(iter(rows))
            cs = sorted(c for _, c in comp)
            closed = ((cs[0] == 0 or board[r][cs[0] - 1] == -1) and
                      (cs[-1] == N - 1 or board[r][cs[-1] + 1] == -1))
        elif len(cols) == 1:
            straight = True
            c = next(iter(cols))
            rs = sorted(r for r, _ in comp)
            closed = ((rs[0] == 0 or board[rs[0] - 1][c] == -1) and
                      (rs[-1] == N - 1 or board[rs[-1] + 1][c] == -1))
        info.append((len(comp), straight, closed, comp))
    # Longest runs claim their ships first.
    info.sort(key=lambda t: -t[0])
    for size, straight, closed, comp in info:
        if straight and closed:
            chosen = _subset_summing(remaining, size)
            if chosen:
                for s in chosen:
                    remaining.remove(s)
            # Cells of a closed straight run are certainly fully revealed,
            # so block them even when the exact ship mix is ambiguous.
            sunk.update(comp)
        else:
            live.update(comp)
    return live, sunk


def _placements(board, sunk, L):
    """Yield all straight length-L placements avoiding misses/sunk cells."""
    for r in range(N):
        for c0 in range(N - L + 1):
            ok = True
            cells = []
            for c in range(c0, c0 + L):
                if board[r][c] == -1 or (r, c) in sunk:
                    ok = False
                    break
                cells.append((r, c))
            if ok:
                yield cells
    for c in range(N):
        for r0 in range(N - L + 1):
            ok = True
            cells = []
            for r in range(r0, r0 + L):
                if board[r][c] == -1 or (r, c) in sunk:
                    ok = False
                    break
                cells.append((r, c))
            if ok:
                yield cells


def _prune_unsupported(board, remaining, live, sunk):
    """Live hits no remaining-ship placement can reach must already be sunk
    (e.g. rectangular clusters of touching ships); block them, cascading."""
    for _ in range(2 * N):
        if not live or not remaining:
            return
        supported = set()
        for L in remaining:
            for cells in _placements(board, sunk, L):
                has_unknown = False
                for r, c in cells:
                    if board[r][c] == 0:
                        has_unknown = True
                        break
                if not has_unknown:
                    continue
                for cell in cells:
                    if cell in live:
                        supported.add(cell)
        unsupported = live - supported
        if not unsupported:
            return
        sunk.update(unsupported)
        live.difference_update(unsupported)


def _score(board, remaining, live, sunk):
    """Probability density: count placements covering each unknown cell,
    massively up-weighting placements that explain live hits."""
    scores = [[0.0] * N for _ in range(N)]
    for L in remaining:
        for cells in _placements(board, sunk, L):
            n_hits = 0
            unknown_cells = []
            for cell in cells:
                r, c = cell
                if board[r][c] == 0:
                    unknown_cells.append(cell)
                elif cell in live:
                    n_hits += 1
            if not unknown_cells:
                continue
            weight = HIT_WEIGHT ** n_hits if n_hits else 1.0
            for r, c in unknown_cells:
                scores[r][c] += weight
    return scores


def _argmax(scores, cells):
    best = -1.0
    best_cells = []
    for r, c in cells:
        s = scores[r][c]
        if s > best + 1e-9:
            best = s
            best_cells = [(r, c)]
        elif s > best - 1e-9:
            best_cells.append((r, c))
    return best, best_cells


def policy(board):
    hits = set()
    unknowns = []
    for r in range(N):
        for c in range(N):
            v = board[r][c]
            if v == 1:
                hits.add((r, c))
            elif v == 0:
                unknowns.append((r, c))
    if not unknowns:
        return (0, 0)

    remaining = list(SHIPS)
    comps = _hit_components(hits)
    live, sunk = _classify(board, comps, remaining)
    _prune_unsupported(board, remaining, live, sunk)
    scores = _score(board, remaining, live, sunk)

    # ---- Target mode: finish damaged ships first. ----
    if live:
        best, best_cells = _argmax(scores, unknowns)
        if best > 0.0:
            return random.choice(best_cells)
        # Fallback: probe next to live hits.
        adjacent = [(r, c) for (r, c) in unknowns
                    if any((r + dr, c + dc) in live for dr, dc in DIRS)]
        if adjacent:
            return random.choice(adjacent)
        return random.choice(unknowns)

    # ---- Hunt mode: density + parity of smallest remaining ship. ----
    if remaining:
        m = min(remaining)
        totals = [0.0] * m
        for r, c in unknowns:
            totals[(r + c) % m] += scores[r][c]
        for res in sorted(range(m), key=lambda i: -totals[i]):
            if totals[res] <= 0.0:
                break
            best, best_cells = _argmax(
                scores, [(r, c) for (r, c) in unknowns if (r + c) % m == res])
            if best > 0.0:
                return random.choice(best_cells)

    # ---- Final fallbacks: always return a legal cell. ----
    best, best_cells = _argmax(scores, unknowns)
    if best > 0.0:
        return random.choice(best_cells)
    return random.choice(unknowns)
