
from typing import List, Tuple

BOARD_SIZE = 10
BOARD_AREA = BOARD_SIZE * BOARD_SIZE

# Fleet: 5, 4, 3, 3, 2
# Two different length-3 ships, so length 3 gets multiplicity 2.
SHIP_MULT = {
    5: 1,
    4: 1,
    3: 2,
    2: 1,
}

# Strongly prefer placements that explain multiple existing hits.
TARGET_WEIGHT = {k: 8 ** k for k in range(1, 6)}


def _generate_placements():
    placements = {}
    for length in SHIP_MULT:
        lst = []

        # Horizontal
        for r in range(BOARD_SIZE):
            base = r * BOARD_SIZE
            for c in range(BOARD_SIZE - length + 1):
                lst.append(tuple(base + c + d for d in range(length)))

        # Vertical
        for r in range(BOARD_SIZE - length + 1):
            for c in range(BOARD_SIZE):
                lst.append(tuple((r + d) * BOARD_SIZE + c for d in range(length)))

        placements[length] = lst
    return placements


def _generate_neighbors():
    neighbors = [[] for _ in range(BOARD_AREA)]
    for idx in range(BOARD_AREA):
        r = idx // BOARD_SIZE
        c = idx % BOARD_SIZE
        if r > 0:
            neighbors[idx].append(idx - BOARD_SIZE)
        if r + 1 < BOARD_SIZE:
            neighbors[idx].append(idx + BOARD_SIZE)
        if c > 0:
            neighbors[idx].append(idx - 1)
        if c + 1 < BOARD_SIZE:
            neighbors[idx].append(idx + 1)
    return neighbors


PLACEMENTS_BY_LEN = _generate_placements()
NEIGHBORS = _generate_neighbors()
ROWS = [i // BOARD_SIZE for i in range(BOARD_AREA)]
COLS = [i % BOARD_SIZE for i in range(BOARD_AREA)]
PARITY = [(ROWS[i] + COLS[i]) & 1 for i in range(BOARD_AREA)]

# Higher is better. This favors central cells as a tie-breaker.
CENTER_SCORE = [
    -((2 * ROWS[i] - (BOARD_SIZE - 1)) ** 2 + (2 * COLS[i] - (BOARD_SIZE - 1)) ** 2)
    for i in range(BOARD_AREA)
]


def policy(board: list[list[int]]) -> tuple[int, int]:
    flat = [cell for row in board for cell in row]
    unknowns = [i for i, v in enumerate(flat) if v == 0]

    # Should not happen in a normal game state, but keep function total.
    if not unknowns:
        return (0, 0)

    hunt = [0] * BOARD_AREA
    target = [0] * BOARD_AREA

    # Score every legal placement.
    for length, mult in SHIP_MULT.items():
        for placement in PLACEMENTS_BY_LEN[length]:
            hit_count = 0
            valid = True

            for idx in placement:
                v = flat[idx]
                if v == -1:
                    valid = False
                    break
                if v == 1:
                    hit_count += 1

            if not valid:
                continue

            if hit_count == 0:
                # Hunt score: placements that avoid all current hits.
                for idx in placement:
                    if flat[idx] == 0:
                        hunt[idx] += mult
            else:
                # Target score: placements that extend/complete known hits.
                w = mult * TARGET_WEIGHT[hit_count]
                for idx in placement:
                    if flat[idx] == 0:
                        target[idx] += w

    # Small tie-break helper: cells adjacent to more known hits are preferred in target mode.
    adj_hits = [0] * BOARD_AREA
    for idx in unknowns:
        cnt = 0
        for n in NEIGHBORS[idx]:
            if flat[n] == 1:
                cnt += 1
        adj_hits[idx] = cnt

    # If any target score exists, always stay in target mode.
    max_target = max(target[idx] for idx in unknowns)
    if max_target > 0:
        best = max(
            unknowns,
            key=lambda i: (
                target[i],
                adj_hits[i],
                hunt[i],
                CENTER_SCORE[i],
                -i,
            ),
        )
        return (ROWS[best], COLS[best])

    # Hunt mode: use checkerboard parity when possible.
    parity_sum = [0, 0]
    for idx in unknowns:
        parity_sum[PARITY[idx]] += hunt[idx]

    preferred_parity = 0 if parity_sum[0] >= parity_sum[1] else 1
    parity_cells = [i for i in unknowns if PARITY[i] == preferred_parity]

    if any(hunt[i] > 0 for i in parity_cells):
        search_cells = parity_cells
    else:
        search_cells = unknowns

    best = max(
        search_cells,
        key=lambda i: (
            hunt[i],
            CENTER_SCORE[i],
            -i,
        ),
    )
    return (ROWS[best], COLS[best])
