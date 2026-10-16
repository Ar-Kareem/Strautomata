
# Battleship policy for a 10x10 board.
# API:
#     policy(board: list[list[int]]) -> tuple[int, int]

from collections import deque

N = 10
FLEET = (5, 4, 3, 3, 2)
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _build_placements():
    placements = {}
    for length in set(FLEET):
        arr = []

        # Horizontal placements
        for r in range(N):
            for c in range(N - length + 1):
                cells = [(r, c + i) for i in range(length)]
                mask = 0
                for rr, cc in cells:
                    mask |= 1 << (rr * N + cc)
                arr.append((mask, cells))

        # Vertical placements
        for r in range(N - length + 1):
            for c in range(N):
                cells = [(r + i, c) for i in range(length)]
                mask = 0
                for rr, cc in cells:
                    mask |= 1 << (rr * N + cc)
                arr.append((mask, cells))

        placements[length] = arr
    return placements


PLACEMENTS = _build_placements()


def _inside(r, c):
    return 0 <= r < N and 0 <= c < N


def _first_unknown(board):
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def _components(board):
    seen = [[False] * N for _ in range(N)]
    comps = []

    for sr in range(N):
        for sc in range(N):
            if board[sr][sc] != 1 or seen[sr][sc]:
                continue

            q = deque([(sr, sc)])
            seen[sr][sc] = True
            comp = []

            while q:
                r, c = q.popleft()
                comp.append((r, c))
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if _inside(nr, nc) and not seen[nr][nc] and board[nr][nc] == 1:
                        seen[nr][nc] = True
                        q.append((nr, nc))

            comps.append(comp)

    return comps


def _clear_space(board, r, c, dr, dc, limit):
    """Count non-miss cells in a ray, starting at r,c."""
    count = 0
    while limit > 0 and _inside(r, c) and board[r][c] != -1:
        count += 1
        r += dr
        c += dc
        limit -= 1
    return count


def _add_hunt_scores(board, score, miss_mask, hit_mask, have_hits):
    """
    General probability-density hunt score.
    When hits exist, this is downweighted and ignores placements crossing hits,
    because target logic handles damaged ships.
    """
    base = 0.18 if have_hits else 1.0

    for length in FLEET:
        for mask, cells in PLACEMENTS[length]:
            if mask & miss_mask:
                continue
            if have_hits and (mask & hit_mask):
                continue

            # Slightly favor longer ships because they have fewer possible locations
            # and are valuable to locate early.
            weight = base * (1.0 + 0.06 * length)

            for r, c in cells:
                if board[r][c] == 0:
                    score[r][c] += weight


def _add_target_placement_scores(board, score, miss_mask, hit_mask):
    """
    Score unknown cells that lie in legal ship placements containing known hits.
    This finds extensions and gap-filling shots.
    """
    if hit_mask == 0:
        return

    for length in FLEET:
        for mask, cells in PLACEMENTS[length]:
            if mask & miss_mask:
                continue

            hit_positions = []
            for i, (r, c) in enumerate(cells):
                if board[r][c] == 1:
                    hit_positions.append(i)

            k = len(hit_positions)
            if k == 0:
                continue

            # Multiple hits in one legal line are very informative.
            base = 70.0 * k * k

            for i, (r, c) in enumerate(cells):
                if board[r][c] != 0:
                    continue

                nearest = min(abs(i - hp) for hp in hit_positions)
                nearest = max(1, nearest)

                add = base / nearest

                # Big bonus for filling a gap between two hits.
                left_hit = any(hp < i for hp in hit_positions)
                right_hit = any(hp > i for hp in hit_positions)
                if left_hit and right_hit:
                    add *= 3.5

                # Adjacent unknowns are usually the most urgent target shots.
                if nearest == 1:
                    add *= 1.7

                score[r][c] += add


def _add_component_scores(board, score, comps):
    """
    Direct tactical targeting from connected hit clusters.
    Linear clusters are extended from their ends.
    Single hits score all four neighboring cells.
    Non-linear clusters may be touching ships, so all adjacent unknowns are useful.
    """
    fleet_lengths = FLEET

    for comp in comps:
        m = len(comp)
        rows = {r for r, _ in comp}
        cols = {c for _, c in comp}

        possible = sum(1 for L in fleet_lengths if L >= m)
        longer = sum(1 for L in fleet_lengths if L > m)

        if possible == 0:
            continue

        # If a component already has length 5, no single ship can extend it.
        # It may be touching ships, but placement scoring/hunt can handle that.
        longer_ratio = longer / possible if possible else 0.0

        if m == 1:
            r, c = comp[0]
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if not _inside(nr, nc) or board[nr][nc] != 0:
                    continue

                forward = _clear_space(board, nr, nc, dr, dc, 4)
                backward = _clear_space(board, r - dr, c - dc, -dr, -dc, 4)
                score[nr][nc] += 950.0 * (1.0 + 0.14 * (forward + backward))
            continue

        # Horizontal line component.
        if len(rows) == 1:
            r = next(iter(rows))
            sorted_cols = sorted(c for _, c in comp)
            lo, hi = sorted_cols[0], sorted_cols[-1]

            # If somehow not contiguous, let placement scoring handle gaps.
            if hi - lo + 1 != m:
                continue

            if longer_ratio <= 0:
                continue

            weight = 1600.0 * m * longer_ratio

            for nc, dc in ((lo - 1, -1), (hi + 1, 1)):
                if _inside(r, nc) and board[r][nc] == 0:
                    space = _clear_space(board, r, nc, 0, dc, 5 - m)
                    score[r][nc] += weight * (1.0 + 0.18 * space)

        # Vertical line component.
        elif len(cols) == 1:
            c = next(iter(cols))
            sorted_rows = sorted(r for r, _ in comp)
            lo, hi = sorted_rows[0], sorted_rows[-1]

            if hi - lo + 1 != m:
                continue

            if longer_ratio <= 0:
                continue

            weight = 1600.0 * m * longer_ratio

            for nr, dr in ((lo - 1, -1), (hi + 1, 1)):
                if _inside(nr, c) and board[nr][c] == 0:
                    space = _clear_space(board, nr, c, dr, 0, 5 - m)
                    score[nr][c] += weight * (1.0 + 0.18 * space)

        # Non-linear connected hits: could be adjacent ships.
        else:
            for r, c in comp:
                for dr, dc in DIRS:
                    nr, nc = r + dr, c + dc
                    if _inside(nr, nc) and board[nr][nc] == 0:
                        score[nr][nc] += 850.0


def _center_bias(r, c):
    # Tiny deterministic tie-breaker toward central cells.
    return 0.001 * (10 - (abs(r - 4.5) + abs(c - 4.5)))


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        unknown_exists = False
        miss_mask = 0
        hit_mask = 0

        for r in range(N):
            for c in range(N):
                v = board[r][c]
                bit = 1 << (r * N + c)
                if v == 0:
                    unknown_exists = True
                elif v == -1:
                    miss_mask |= bit
                elif v == 1:
                    hit_mask |= bit

        if not unknown_exists:
            return (0, 0)

        have_hits = hit_mask != 0
        score = [[0.0 for _ in range(N)] for _ in range(N)]

        # Baseline probability hunt.
        _add_hunt_scores(board, score, miss_mask, hit_mask, have_hits)

        if have_hits:
            comps = _components(board)
            _add_target_placement_scores(board, score, miss_mask, hit_mask)
            _add_component_scores(board, score, comps)

        # Checkerboard hunt bias when there is no active target.
        # This improves search efficiency because every remaining ship has length >= 2.
        if not have_hits:
            for r in range(N):
                for c in range(N):
                    if board[r][c] == 0 and ((r + c) & 1) == 0:
                        score[r][c] *= 1.22

        best = None
        best_value = -1e100

        for r in range(N):
            for c in range(N):
                if board[r][c] != 0:
                    continue

                value = score[r][c] + _center_bias(r, c)

                if value > best_value:
                    best_value = value
                    best = (r, c)

        if best is not None and board[best[0]][best[1]] == 0:
            return best

        return _first_unknown(board)

    except Exception:
        # Safety fallback: never fail to return a legal move if one exists.
        return _first_unknown(board)
