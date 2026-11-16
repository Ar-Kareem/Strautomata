
SHIP_LENGTHS = (5, 4, 3, 3, 2)
N = 10


def policy(board: list[list[int]]) -> tuple[int, int]:
    unknowns = []
    hits = []

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                unknowns.append((r, c))
            elif board[r][c] == 1:
                hits.append((r, c))

    # Should not happen in a normal game, but keep API total.
    if not unknowns:
        return (0, 0)

    target = [[0.0 for _ in range(N)] for _ in range(N)]
    hunt = [[0.0 for _ in range(N)] for _ in range(N)]

    def in_bounds(r: int, c: int) -> bool:
        return 0 <= r < N and 0 <= c < N

    def add_target(r: int, c: int, value: float) -> None:
        if in_bounds(r, c) and board[r][c] == 0:
            target[r][c] += value

    def center_bonus(r: int, c: int) -> float:
        # Tiny tie-breaker favoring central cells.
        return 0.02 * (9.0 - abs(r - 4.5) - abs(c - 4.5))

    def board_hash() -> int:
        h = 2166136261
        for rr in range(N):
            for cc in range(N):
                h ^= (board[rr][cc] + 2) * (rr * N + cc + 1)
                h = (h * 16777619) & 0xFFFFFFFF
        return h

    hval = board_hash()

    # ------------------------------------------------------------------
    # 1. Explicit target logic around connected hit clusters.
    # ------------------------------------------------------------------
    hit_set = set(hits)
    visited = set()
    dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))

    for start in hits:
        if start in visited:
            continue

        stack = [start]
        visited.add(start)
        comp = []

        while stack:
            r, c = stack.pop()
            comp.append((r, c))
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if (nr, nc) in hit_set and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    stack.append((nr, nc))

        comp_len = len(comp)

        if comp_len == 1:
            r, c = comp[0]

            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if not (in_bounds(nr, nc) and board[nr][nc] == 0):
                    continue

                # Estimate how much room exists along this direction.
                span = 1

                tr, tc = r + dr, c + dc
                while in_bounds(tr, tc) and board[tr][tc] != -1:
                    span += 1
                    tr += dr
                    tc += dc

                tr, tc = r - dr, c - dc
                while in_bounds(tr, tc) and board[tr][tc] != -1:
                    span += 1
                    tr -= dr
                    tc -= dc

                if span >= 2:
                    add_target(nr, nc, 6000.0 + 120.0 * min(span, 5))

        else:
            rows = {r for r, _ in comp}
            cols = {c for _, c in comp}

            # Straight horizontal hit cluster.
            if len(rows) == 1:
                r = next(iter(rows))
                cs = sorted(c for _, c in comp)
                min_c, max_c = cs[0], cs[-1]

                # Only extend clusters that could still be part of a length <= 5 ship.
                if max_c - min_c + 1 == comp_len and comp_len < 5:
                    add_target(r, min_c - 1, 9000.0 + 1200.0 * comp_len)
                    add_target(r, max_c + 1, 9000.0 + 1200.0 * comp_len)

            # Straight vertical hit cluster.
            elif len(cols) == 1:
                c = next(iter(cols))
                rs = sorted(r for r, _ in comp)
                min_r, max_r = rs[0], rs[-1]

                if max_r - min_r + 1 == comp_len and comp_len < 5:
                    add_target(min_r - 1, c, 9000.0 + 1200.0 * comp_len)
                    add_target(max_r + 1, c, 9000.0 + 1200.0 * comp_len)

            # Irregular cluster, likely touching ships; try all orthogonal edges.
            else:
                for r, c in comp:
                    for dr, dc in dirs:
                        add_target(r + dr, c + dc, 3500.0)

    # ------------------------------------------------------------------
    # 2. Placement probability scoring.
    #
    # target: placements containing known hits
    # hunt: placements containing no known hits, for undiscovered ships
    # ------------------------------------------------------------------
    def score_segment(cells: list[tuple[int, int]], length: int) -> None:
        miss_count = 0
        hit_positions = []
        unknown_positions = []

        for idx, (r, c) in enumerate(cells):
            val = board[r][c]
            if val == -1:
                miss_count += 1
                break
            elif val == 1:
                hit_positions.append(idx)
            elif val == 0:
                unknown_positions.append((idx, r, c))

        if miss_count:
            return

        hit_count = len(hit_positions)

        if hit_count:
            # A possible continuation of an already hit ship.
            base = 85.0 * hit_count * hit_count + 12.0 * length
            for idx, r, c in unknown_positions:
                nearest = min(abs(idx - hp) for hp in hit_positions)
                target[r][c] += base / max(1, nearest)
        else:
            # A possible completely unhit ship placement.
            base = 1.0 + 0.08 * length
            for _, r, c in unknown_positions:
                hunt[r][c] += base

    for length in SHIP_LENGTHS:
        # Horizontal placements.
        for r in range(N):
            for c0 in range(N - length + 1):
                cells = [(r, c0 + k) for k in range(length)]
                score_segment(cells, length)

        # Vertical placements.
        for c in range(N):
            for r0 in range(N - length + 1):
                cells = [(r0 + k, c) for k in range(length)]
                score_segment(cells, length)

    # ------------------------------------------------------------------
    # 3. Choose a target shot if any plausible target continuation exists.
    # ------------------------------------------------------------------
    best_target = 0.0
    for r, c in unknowns:
        if target[r][c] > best_target:
            best_target = target[r][c]

    if best_target > 0.0:
        best_score = -1e100
        candidates = []

        for r, c in unknowns:
            score = target[r][c] + 0.01 * hunt[r][c] + center_bonus(r, c)
            if score > best_score + 1e-9:
                best_score = score
                candidates = [(r, c)]
            elif abs(score - best_score) <= 1e-9:
                candidates.append((r, c))

        return candidates[hval % len(candidates)]

    # ------------------------------------------------------------------
    # 4. Hunt mode.
    #
    # Checkerboard bias is strong because every remaining ship has length
    # at least 2, so each ship must occupy both parities.
    # ------------------------------------------------------------------
    parity_total = [0.0, 0.0]
    parity_count = [0, 0]

    for r, c in unknowns:
        p = (r + c) & 1
        parity_total[p] += hunt[r][c] + center_bonus(r, c)
        parity_count[p] += 1

    if parity_count[0] and parity_count[1]:
        if abs(parity_total[0] - parity_total[1]) < 1e-9:
            preferred_parity = hval & 1
        else:
            preferred_parity = 0 if parity_total[0] > parity_total[1] else 1
    elif parity_count[0]:
        preferred_parity = 0
    else:
        preferred_parity = 1

    # Prefer checkerboard cells when possible.
    restricted = [
        (r, c)
        for r, c in unknowns
        if ((r + c) & 1) == preferred_parity
    ]

    if not restricted:
        restricted = unknowns

    best_score = -1e100
    candidates = []

    for r, c in restricted:
        score = hunt[r][c] + center_bonus(r, c)

        # Small deterministic jitter to avoid always choosing the same
        # symmetric cell when many are equivalent.
        jitter = (((r * 31 + c * 17 + hval) & 1023) / 1024.0) * 1e-5
        score += jitter

        if score > best_score + 1e-9:
            best_score = score
            candidates = [(r, c)]
        elif abs(score - best_score) <= 1e-9:
            candidates.append((r, c))

    if candidates:
        return candidates[hval % len(candidates)]

    # Absolute legal fallback.
    return unknowns[0]
