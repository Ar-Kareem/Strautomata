
import random

SIZE = 10
FULL_FLEET = (5, 4, 3, 3, 2)


def _build_placements():
    placements = {2: [], 3: [], 4: [], 5: []}
    for length in placements:
        for r in range(SIZE):
            for c in range(SIZE - length + 1):
                placements[length].append(tuple((r, c + i) for i in range(length)))
        for c in range(SIZE):
            for r in range(SIZE - length + 1):
                placements[length].append(tuple((r + i, c) for i in range(length)))
    return placements


_PLACEMENTS = _build_placements()


def _subset_sum(pool, target):
    items = sorted(pool, reverse=True)

    def rec(i, remaining):
        if remaining == 0:
            return []
        if i >= len(items) or remaining < 0:
            return None
        taken = rec(i + 1, remaining - items[i])
        if taken is not None:
            return [items[i]] + taken
        return rec(i + 1, remaining)

    return rec(0, target)


def _detect_runs(board, hits):
    """Maximal straight hit-runs of length >= 2 plus isolated single hits."""
    runs = []  # (cells, axis, any_open_end)
    in_run = set()
    for r in range(SIZE):
        c = 0
        while c < SIZE:
            if board[r][c] == 1:
                c1 = c
                while c + 1 < SIZE and board[r][c + 1] == 1:
                    c += 1
                c2 = c
                if c2 > c1:
                    left_open = c1 > 0 and board[r][c1 - 1] == 0
                    right_open = c2 < SIZE - 1 and board[r][c2 + 1] == 0
                    cells = [(r, cc) for cc in range(c1, c2 + 1)]
                    runs.append((cells, 'h', left_open or right_open))
                    in_run.update(cells)
            c += 1
    for c in range(SIZE):
        r = 0
        while r < SIZE:
            if board[r][c] == 1:
                r1 = r
                while r + 1 < SIZE and board[r + 1][c] == 1:
                    r += 1
                r2 = r
                if r2 > r1:
                    up_open = r1 > 0 and board[r1 - 1][c] == 0
                    down_open = r2 < SIZE - 1 and board[r2 + 1][c] == 0
                    cells = [(rr, c) for rr in range(r1, r2 + 1)]
                    runs.append((cells, 'v', up_open or down_open))
                    in_run.update(cells)
            r += 1
    singles = [cell for cell in hits if cell not in in_run]
    return runs, singles


def _infer_remaining(runs):
    """Remove ship lengths explained by closed (sunk) runs."""
    rem = list(FULL_FLEET)
    for cells, _axis, any_open in sorted(runs, key=lambda x: -len(x[0])):
        n = len(cells)
        if any_open and n < 5:
            continue  # unfinished run: ship identity still unknown
        if n in rem:
            rem.remove(n)
        else:
            sub = _subset_sum(rem, n)
            if sub:
                for x in sub:
                    rem.remove(x)
    return rem


def _target_scores(board, runs, singles, rem):
    """Count placements of remaining ships that extend unresolved hits."""
    scores = [[0] * SIZE for _ in range(SIZE)]

    def score_span(first, last, axis):
        span = (last[1] - first[1] + 1) if axis == 'h' else (last[0] - first[0] + 1)
        for length in rem:
            if length <= span:
                continue
            if axis == 'h':
                r = first[0]
                c1, c2 = first[1], last[1]
                lo = max(0, c2 - length + 1)
                hi = min(c1, SIZE - length)
                for s in range(lo, hi + 1):
                    unknowns = []
                    ok = True
                    for i in range(length):
                        v = board[r][s + i]
                        if v == -1:
                            ok = False
                            break
                        if v == 0:
                            unknowns.append((r, s + i))
                    if ok and unknowns:
                        for rr, cc in unknowns:
                            scores[rr][cc] += 1
            else:
                c = first[1]
                r1, r2 = first[0], last[0]
                lo = max(0, r2 - length + 1)
                hi = min(r1, SIZE - length)
                for s in range(lo, hi + 1):
                    unknowns = []
                    ok = True
                    for i in range(length):
                        v = board[s + i][c]
                        if v == -1:
                            ok = False
                            break
                        if v == 0:
                            unknowns.append((s + i, c))
                    if ok and unknowns:
                        for rr, cc in unknowns:
                            scores[rr][cc] += 1

    for cells, axis, any_open in runs:
        if any_open and len(cells) < 5:
            score_span(cells[0], cells[-1], axis)
    for r, c in singles:
        if any(0 <= r + dr < SIZE and 0 <= c + dc < SIZE and board[r + dr][c + dc] == 0
               for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            score_span((r, c), (r, c), 'h')
            score_span((r, c), (r, c), 'v')
    return scores


def _hunt_scores(board, rem):
    """Count placements of remaining ships lying entirely in unknown water."""
    scores = [[0] * SIZE for _ in range(SIZE)]
    for length in rem:
        for placement in _PLACEMENTS[length]:
            ok = True
            for r, c in placement:
                if board[r][c] != 0:
                    ok = False
                    break
            if ok:
                for r, c in placement:
                    scores[r][c] += 1
    return scores


def _best_cell(scores, rng, parity_mod=1):
    best = 0
    cands = []
    for r in range(SIZE):
        row = scores[r]
        for c in range(SIZE):
            v = row[c]
            if v > best:
                best = v
                cands = [(r, c)]
            elif v == best and best > 0:
                cands.append((r, c))
    if not cands:
        return None
    if parity_mod > 1:
        lattice = [cell for cell in cands if (cell[0] + cell[1]) % parity_mod == 0]
        if lattice:
            cands = lattice
    return cands[rng.randrange(len(cands))]


def policy(board):
    unknown = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 0]
    if not unknown:
        return (0, 0)  # nothing legal left; game is already decided
    hits = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == 1]
    rng = random.Random(hash(tuple(tuple(row) for row in board)) & 0xFFFFFFFF)
    rem = list(FULL_FLEET)

    # --- Target mode: finish off damaged ships first ---
    if hits:
        runs, singles = _detect_runs(board, hits)
        rem = _infer_remaining(runs)
        has_active_run = any(any_open and len(cells) < 5 for cells, _, any_open in runs)
        if has_active_run or singles:
            scores = _target_scores(board, runs, singles, rem or list(FULL_FLEET))
            cell = _best_cell(scores, rng)
            if cell is None:  # fleet inference may be off; retry with every length
                scores = _target_scores(board, runs, singles, list(FULL_FLEET))
                cell = _best_cell(scores, rng)
            if cell is not None:
                return cell

    # --- Hunt mode: maximum-likelihood search of open water ---
    if not rem:
        rem = list(FULL_FLEET)
    scores = _hunt_scores(board, rem)
    cell = _best_cell(scores, rng, parity_mod=min(rem))
    if cell is None:
        scores = _hunt_scores(board, list(FULL_FLEET))
        cell = _best_cell(scores, rng, parity_mod=2)
    if cell is not None:
        return cell

    # --- Last resort: any unfired cell (always legal) ---
    return unknown[rng.randrange(len(unknown))]
