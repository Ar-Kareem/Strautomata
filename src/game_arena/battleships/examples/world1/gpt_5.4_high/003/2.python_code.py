
BOARD_SIZE = 10
SHIP_MULTIPLICITY = {5: 1, 4: 1, 3: 2, 2: 1}
TARGET_BONUS = 12.0

TARGET_BONUS_POW = {0: 1.0}
for _k in range(1, 6):
    TARGET_BONUS_POW[_k] = TARGET_BONUS_POW[_k - 1] * TARGET_BONUS

# Precompute all straight placements for each ship length.
# Each entry is: (cells, outside_cells, orientation)
# orientation: 0 = horizontal, 1 = vertical
PLACEMENTS_BY_LENGTH = {length: [] for length in SHIP_MULTIPLICITY}

for length in SHIP_MULTIPLICITY:
    # Horizontal
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE - length + 1):
            cells = tuple(r * BOARD_SIZE + (c + d) for d in range(length))
            outside = (
                r * BOARD_SIZE + (c - 1) if c > 0 else -1,
                r * BOARD_SIZE + (c + length) if c + length < BOARD_SIZE else -1,
            )
            PLACEMENTS_BY_LENGTH[length].append((cells, outside, 0))

    # Vertical
    for r in range(BOARD_SIZE - length + 1):
        for c in range(BOARD_SIZE):
            cells = tuple((r + d) * BOARD_SIZE + c for d in range(length))
            outside = (
                (r - 1) * BOARD_SIZE + c if r > 0 else -1,
                (r + length) * BOARD_SIZE + c if r + length < BOARD_SIZE else -1,
            )
            PLACEMENTS_BY_LENGTH[length].append((cells, outside, 1))

# Precompute neighbor lists and tie-break helpers.
NEIGHBORS = [[] for _ in range(BOARD_SIZE * BOARD_SIZE)]
CENTER_SCORE = [0.0 for _ in range(BOARD_SIZE * BOARD_SIZE)]
PARITY_PREF = [0 for _ in range(BOARD_SIZE * BOARD_SIZE)]

for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        idx = r * BOARD_SIZE + c
        if r > 0:
            NEIGHBORS[idx].append((r - 1) * BOARD_SIZE + c)
        if r + 1 < BOARD_SIZE:
            NEIGHBORS[idx].append((r + 1) * BOARD_SIZE + c)
        if c > 0:
            NEIGHBORS[idx].append(r * BOARD_SIZE + (c - 1))
        if c + 1 < BOARD_SIZE:
            NEIGHBORS[idx].append(r * BOARD_SIZE + (c + 1))

        CENTER_SCORE[idx] = -((r - 4.5) ** 2 + (c - 4.5) ** 2)
        PARITY_PREF[idx] = 1 if ((r + c) & 1) == 0 else 0


def _first_unknown(board):
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)


def _resolved_hit_orientations(board):
    """
    Mark hits that are part of a strongly resolved horizontal/vertical run.
    This suppresses wasting shots in the conflicting orientation.

    Horizontal run is considered resolved if:
    - length >= 5, or
    - length >= 2 and both ends are blocked by edge/miss.

    Same for vertical.
    """
    resolved_h = [False] * (BOARD_SIZE * BOARD_SIZE)
    resolved_v = [False] * (BOARD_SIZE * BOARD_SIZE)

    # Horizontal runs
    for r in range(BOARD_SIZE):
        c = 0
        while c < BOARD_SIZE:
            if board[r][c] == 1:
                start = c
                while c + 1 < BOARD_SIZE and board[r][c + 1] == 1:
                    c += 1
                end = c
                run_len = end - start + 1

                left_blocked = (start == 0) or (board[r][start - 1] == -1)
                right_blocked = (end == BOARD_SIZE - 1) or (board[r][end + 1] == -1)

                if run_len >= 5 or (run_len >= 2 and left_blocked and right_blocked):
                    base = r * BOARD_SIZE
                    for x in range(start, end + 1):
                        resolved_h[base + x] = True
            c += 1

    # Vertical runs
    for c in range(BOARD_SIZE):
        r = 0
        while r < BOARD_SIZE:
            if board[r][c] == 1:
                start = r
                while r + 1 < BOARD_SIZE and board[r + 1][c] == 1:
                    r += 1
                end = r
                run_len = end - start + 1

                up_blocked = (start == 0) or (board[start - 1][c] == -1)
                down_blocked = (end == BOARD_SIZE - 1) or (board[end + 1][c] == -1)

                if run_len >= 5 or (run_len >= 2 and up_blocked and down_blocked):
                    for x in range(start, end + 1):
                        resolved_v[x * BOARD_SIZE + c] = True
            r += 1

    return resolved_h, resolved_v


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        flat = []
        unknowns = []

        for r in range(BOARD_SIZE):
            row = board[r]
            for c in range(BOARD_SIZE):
                v = row[c]
                flat.append(v)
                if v == 0:
                    unknowns.append(r * BOARD_SIZE + c)

        if not unknowns:
            return (0, 0)

        resolved_h, resolved_v = _resolved_hit_orientations(board)

        scores = [0.0] * (BOARD_SIZE * BOARD_SIZE)

        for length, multiplicity in SHIP_MULTIPLICITY.items():
            base_weight = float(multiplicity)

            for cells, outside, orient in PLACEMENTS_BY_LENGTH[length]:
                hit_positions = []
                unknown_cells = []
                blocked = False
                conflict = False

                for pos, idx in enumerate(cells):
                    v = flat[idx]

                    if v == -1:
                        blocked = True
                        break

                    if v == 1:
                        # Suppress use of hits in a conflicting resolved orientation.
                        if orient == 0:
                            if resolved_v[idx]:
                                conflict = True
                                break
                        else:
                            if resolved_h[idx]:
                                conflict = True
                                break
                        hit_positions.append(pos)
                    else:
                        unknown_cells.append(idx)

                if blocked or conflict or not unknown_cells:
                    continue

                k = len(hit_positions)

                if k == 0:
                    weight = base_weight
                else:
                    # Ignore placements that visibly truncate a same-line hit run.
                    if (outside[0] != -1 and flat[outside[0]] == 1) or (
                        outside[1] != -1 and flat[outside[1]] == 1
                    ):
                        continue

                    span = hit_positions[-1] - hit_positions[0] + 1
                    weight = base_weight * TARGET_BONUS_POW[k] * (k / span)

                for idx in unknown_cells:
                    scores[idx] += weight

        # Pick best unknown cell. Tie-breakers:
        # 1) higher accumulated score
        # 2) more adjacent hits
        # 3) more adjacent non-miss cells
        # 4) more central
        # 5) parity preference
        best_idx = unknowns[0]
        best_key = (-1.0, -1, -1, -999.0, -1)

        for idx in unknowns:
            adj_hits = 0
            adj_open = 0

            for n in NEIGHBORS[idx]:
                v = flat[n]
                if v == 1:
                    adj_hits += 1
                if v != -1:
                    adj_open += 1

            key = (
                scores[idx],
                adj_hits,
                adj_open,
                CENTER_SCORE[idx],
                PARITY_PREF[idx],
            )

            if key > best_key:
                best_key = key
                best_idx = idx

        return (best_idx // BOARD_SIZE, best_idx % BOARD_SIZE)

    except Exception:
        # Absolute safety fallback: always return a legal unknown if possible.
        return _first_unknown(board)
