
from typing import List, Tuple

BOARD_SIZE = 10
SHIPS = [5, 4, 3, 3, 2]

# Precompute all straight placements for each ship length.
# Each entry is: (cells_tuple, cells_frozenset)
PLACEMENTS = {2: [], 3: [], 4: [], 5: []}
for L in PLACEMENTS:
    # Horizontal
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE - L + 1):
            cells = tuple((r, c + i) for i in range(L))
            PLACEMENTS[L].append((cells, frozenset(cells)))
    # Vertical
    for r in range(BOARD_SIZE - L + 1):
        for c in range(BOARD_SIZE):
            cells = tuple((r + i, c) for i in range(L))
            PLACEMENTS[L].append((cells, frozenset(cells)))

# Mild center preference used for tie-breaking / hunt shaping.
CENTER_BONUS = [
    [6.0 - (abs(r - 4.5) + abs(c - 4.5)) * 0.6 for c in range(BOARD_SIZE)]
    for r in range(BOARD_SIZE)
]

DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _in_bounds(r: int, c: int) -> bool:
    return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE


def _adjacent_hit_count(board: List[List[int]], r: int, c: int) -> int:
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc) and board[nr][nc] == 1:
            cnt += 1
    return cnt


def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Collect board information.
    unknowns = []
    hits = []
    hit_set = set()

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            v = board[r][c]
            if v == 0:
                unknowns.append((r, c))
            elif v == 1:
                hits.append((r, c))
                hit_set.add((r, c))

    # Absolute safety fallback.
    if not unknowns:
        return (0, 0)

    any_hit = len(hits) > 0

    # Precompute hit-neighbor map for plausibility penalties.
    hit_neighbors = {}
    for r, c in hits:
        nbs = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if _in_bounds(nr, nc) and board[nr][nc] == 1:
                nbs.append((nr, nc))
        hit_neighbors[(r, c)] = nbs

    # Initialize scores with a tiny center bias.
    scores = [[CENTER_BONUS[r][c] * 0.05 for c in range(BOARD_SIZE)] for r in range(BOARD_SIZE)]

    # 1) Placement-density scoring.
    for L in SHIPS:
        for cells, cellset in PLACEMENTS[L]:
            valid = True
            local_hits = []

            for r, c in cells:
                v = board[r][c]
                if v == -1:
                    valid = False
                    break
                if v == 1:
                    local_hits.append((r, c))

            if not valid:
                continue

            hits_in = len(local_hits)

            if any_hit:
                if hits_in > 0:
                    # Strongly favor placements that explain current hits.
                    weight = (7.0 ** hits_in) * (1.0 + 0.08 * L)

                    # Penalize placements that include one hit from an adjacent hit group
                    # but exclude its neighboring hits. This discourages "splitting"
                    # likely same-ship runs, while still allowing touching ships.
                    conflicts = 0
                    for cell in local_hits:
                        for nb in hit_neighbors[cell]:
                            if nb not in cellset:
                                conflicts += 1
                    if conflicts:
                        weight *= (0.35 ** conflicts)
                else:
                    # Still allow hunting elsewhere a little, in case visible hits
                    # are from already-sunk ships and another ship remains hidden.
                    weight = 0.12
            else:
                # Pure hunt mode.
                weight = 1.0 + 0.05 * L

            for r, c in cells:
                if board[r][c] == 0:
                    scores[r][c] += weight

    # 2) Tactical bonuses around hits.
    if any_hit:
        # Adjacent-to-hit bonus.
        for r, c in hits:
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                if _in_bounds(nr, nc) and board[nr][nc] == 0:
                    scores[nr][nc] += 20.0

        # Extend horizontal runs of hits.
        for r in range(BOARD_SIZE):
            c = 0
            while c < BOARD_SIZE:
                if board[r][c] == 1:
                    start = c
                    while c < BOARD_SIZE and board[r][c] == 1:
                        c += 1
                    end = c - 1
                    run_len = end - start + 1
                    if run_len >= 2:
                        if start - 1 >= 0 and board[r][start - 1] == 0:
                            scores[r][start - 1] += 220.0 * run_len
                        if end + 1 < BOARD_SIZE and board[r][end + 1] == 0:
                            scores[r][end + 1] += 220.0 * run_len
                else:
                    c += 1

        # Extend vertical runs of hits.
        for c in range(BOARD_SIZE):
            r = 0
            while r < BOARD_SIZE:
                if board[r][c] == 1:
                    start = r
                    while r < BOARD_SIZE and board[r][c] == 1:
                        r += 1
                    end = r - 1
                    run_len = end - start + 1
                    if run_len >= 2:
                        if start - 1 >= 0 and board[start - 1][c] == 0:
                            scores[start - 1][c] += 220.0 * run_len
                        if end + 1 < BOARD_SIZE and board[end + 1][c] == 0:
                            scores[end + 1][c] += 220.0 * run_len
                else:
                    r += 1

        # Fill hit-gap-hit patterns.
        for r in range(BOARD_SIZE):
            for c in range(1, BOARD_SIZE - 1):
                if board[r][c] == 0 and board[r][c - 1] == 1 and board[r][c + 1] == 1:
                    scores[r][c] += 350.0

        for r in range(1, BOARD_SIZE - 1):
            for c in range(BOARD_SIZE):
                if board[r][c] == 0 and board[r - 1][c] == 1 and board[r + 1][c] == 1:
                    scores[r][c] += 350.0

    else:
        # 3) Hunt-mode parity preference.
        # Checkerboard is strong while many cells remain, since all ships are length >= 2.
        if len(unknowns) > 20:
            for r, c in unknowns:
                if (r + c) % 2 == 0:
                    scores[r][c] += 8.0

    # Choose the best legal move.
    best_move = unknowns[0]
    best_key = None

    for r, c in unknowns:
        adj_hits = _adjacent_hit_count(board, r, c)
        parity = 1 if ((r + c) % 2 == 0) else 0
        key = (
            scores[r][c],
            adj_hits,
            CENTER_BONUS[r][c],
            parity,
            -abs(r - 4.5) - abs(c - 4.5),
            -r,
            -c,
        )
        if best_key is None or key > best_key:
            best_key = key
            best_move = (r, c)

    return best_move
