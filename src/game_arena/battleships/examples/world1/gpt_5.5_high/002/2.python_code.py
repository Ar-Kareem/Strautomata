
N = 10
SHIPS = (5, 4, 3, 3, 2)


def _build_placements():
    """Precompute every straight placement for lengths 2..5."""
    placements = {}
    for length in range(2, 6):
        arr = []

        # Horizontal placements.
        for r in range(N):
            for c in range(N - length + 1):
                cells = tuple((r, c + k) for k in range(length))
                arr.append((cells, 0, 1))

        # Vertical placements.
        for r in range(N - length + 1):
            for c in range(N):
                cells = tuple((r + k, c) for k in range(length))
                arr.append((cells, 1, 0))

        placements[length] = tuple(arr)
    return placements


PLACEMENTS = _build_placements()

# Tiny deterministic tie-breaker: prefer central cells.
CENTER_BONUS = [
    [100.0 - ((r - 4.5) * (r - 4.5) + (c - 4.5) * (c - 4.5)) for c in range(N)]
    for r in range(N)
]


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def policy(board: list[list[int]]) -> tuple[int, int]:
    unknown = []
    hits = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                unknown.append((r, c))
            elif board[r][c] == 1:
                hits.append((r, c))

    # Should not happen during a live game, but keep a total fallback.
    if not unknown:
        return (0, 0)

    # Count orthogonal hit-neighbors for each hit.  Singleton hits are treated
    # differently from hits that are already part of a line/cluster.
    hit_neighbors = [[0] * N for _ in range(N)]
    for r, c in hits:
        cnt = 0
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if _inside(rr, cc) and board[rr][cc] == 1:
                cnt += 1
        hit_neighbors[r][c] = cnt

    # ------------------------------------------------------------------
    # TARGET MODE
    # ------------------------------------------------------------------
    # Score cells that plausibly continue or complete known hit patterns.
    target = [[0.0] * N for _ in range(N)]

    for length in SHIPS:
        for cells, dr, dc in PLACEMENTS[length]:
            hit_pos = []
            bad = False

            for i, (r, c) in enumerate(cells):
                v = board[r][c]
                if v == -1:
                    bad = True
                    break
                if v == 1:
                    hit_pos.append(i)

            if bad or not hit_pos:
                continue

            h = len(hit_pos)

            if h == 1:
                # For a true singleton hit, shoot adjacent cells along any
                # possible ship orientation.  If the hit already touches another
                # hit, avoid wasting shots perpendicular to the known line.
                i = hit_pos[0]
                r, c = cells[i]
                if hit_neighbors[r][c] != 0:
                    continue

                weight = 18.0
                for j in (i - 1, i + 1):
                    if 0 <= j < length:
                        rr, cc = cells[j]
                        if board[rr][cc] == 0:
                            target[rr][cc] += weight

            else:
                mn = hit_pos[0]
                mx = hit_pos[-1]

                # Do not let shorter sub-placements of an already-known longer
                # hit line create bogus extension shots.  If an adjacent hit lies
                # just outside this placement in the same direction, this
                # placement cannot be the whole explanation for that line.
                if mn == 0:
                    rr = cells[0][0] - dr
                    cc = cells[0][1] - dc
                    if _inside(rr, cc) and board[rr][cc] == 1:
                        continue
                if mx == length - 1:
                    rr = cells[-1][0] + dr
                    cc = cells[-1][1] + dc
                    if _inside(rr, cc) and board[rr][cc] == 1:
                        continue

                # Multiple hits in the same candidate placement are valuable.
                # Gaps between hits are especially valuable because they are
                # forced if those hits belong to the same ship.
                base = 35.0 * (2.2 ** min(h - 2, 3))

                # Fill internal gaps first.
                for j in range(mn + 1, mx):
                    rr, cc = cells[j]
                    if board[rr][cc] == 0:
                        target[rr][cc] += base * 8.0

                # Then extend the line at either end.
                for j in (mn - 1, mx + 1):
                    if 0 <= j < length:
                        rr, cc = cells[j]
                        if board[rr][cc] == 0:
                            target[rr][cc] += base

    # ------------------------------------------------------------------
    # HUNT MODE
    # ------------------------------------------------------------------
    # Probability-like heat map from all legal all-unknown windows.  Known hits
    # are blocked here because hit-following is handled by target mode.
    hunt = [[0.0] * N for _ in range(N)]

    for length in SHIPS:
        valid = []
        for cells, _, _ in PLACEMENTS[length]:
            ok = True
            for r, c in cells:
                if board[r][c] != 0:
                    ok = False
                    break
            if ok:
                valid.append(cells)

        if not valid:
            continue

        inc = 1.0 / len(valid)
        for cells in valid:
            for r, c in cells:
                hunt[r][c] += inc

    # ------------------------------------------------------------------
    # MOVE SELECTION
    # ------------------------------------------------------------------
    target_max = max(target[r][c] for r, c in unknown)

    if target_max > 0.0:
        # In target mode, any plausible finishing shot is much more valuable
        # than blind hunting.
        best = None
        best_score = -1e100
        for r, c in unknown:
            score = target[r][c] * 1000.0 + hunt[r][c] + CENTER_BONUS[r][c] * 1e-6
            if score > best_score:
                best_score = score
                best = (r, c)

        if best is not None and board[best[0]][best[1]] == 0:
            return best

    # Hunt mode: checkerboard search is efficient because all ships have length
    # at least 2.  Use parity 0 when possible, then relax if necessary.
    candidates = [(r, c) for r, c in unknown if ((r + c) & 1) == 0 and hunt[r][c] > 0.0]

    if not candidates:
        candidates = [(r, c) for r, c in unknown if hunt[r][c] > 0.0]

    if not candidates:
        candidates = unknown

    best = None
    best_score = -1e100
    for r, c in candidates:
        score = hunt[r][c] + CENTER_BONUS[r][c] * 1e-5
        if score > best_score:
            best_score = score
            best = (r, c)

    if best is not None and board[best[0]][best[1]] == 0:
        return best

    # Absolute final safety fallback.
    return unknown[0]
