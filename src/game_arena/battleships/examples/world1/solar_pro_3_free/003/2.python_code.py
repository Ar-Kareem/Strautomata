
import random
from typing import List, Tuple

# Ship lengths that the opponent must have placed
SHIP_LENGTHS: List[int] = [5, 4, 3, 3, 2]
BOARD_SIZE: int = 10

def _placements_covering_cell(
    board: List[List[int]],
    r: int,
    c: int,
) -> int:
    """
    Count how many legal ship placements of any length could cover the
    cell (r, c) while also hitting at least one other cell that is already
    known to be a hit.  Horizontal placements keep the same row,
    vertical placements keep the same column.

    Weight = 1 for placements that contain a hit, 2 otherwise.
    """
    score = 0
    # Horizontal placements (same row)
    for L in SHIP_LENGTHS:
        max_start = min(BOARD_SIZE - L, c)
        min_start = max(0, c - L + 1)
        for start in range(min_start, max_start + 1):
            # check if this segment runs over any miss
            ok = True
            hit_in_segment = False
            for dc in range(start, start + L):
                if board[r][dc] == -1:
                    ok = False
                    break
                if board[r][dc] == 1:
                    hit_in_segment = True
            if not ok:
                continue
            # add weight
            score += 2 if hit_in_segment else 1
    # Vertical placements (same column)
    for L in SHIP_LENGTHS:
        max_start = min(BOARD_SIZE - L, r)
        min_start = max(0, r - L + 1)
        for start in range(min_start, max_start + 1):
            ok = True
            hit_in_segment = False
            for dr in range(start, start + L):
                if board[dr][c] == -1:
                    ok = False
                    break
                if board[dr][c] == 1:
                    hit_in_segment = True
            if not ok:
                continue
            score += 2 if hit_in_segment else 1
    return score


def _start_spiral() -> List[Tuple[int, int]]:
    """
    Generate a deterministic outward‑spiral starting from the centre of the board.
    The order is: centre, right, down, left, up, left‑down, right‑down, right‑up,
    left‑up, outer ring, etc.
    """
    order = [
        (4, 4), (4, 5), (5, 5), (5, 4),
        (3, 4), (4, 3), (5, 3), (6, 3),
        (3, 3), (3, 5), (6, 5), (6, 3),
        # outer ring (example)
        (2, 4), (4, 2), (4, 6), (2, 6),
        (7, 4), (4, 7), (7, 7), (7, 2),
        (2, 2), (2, 7), (7, 2), (7, 7),
    ]
    # Filter out cells that are out of bounds (shouldn’t happen) and duplicate hits
    return [(r, c) for r, c in order if 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE]


def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Main entry point required by the arena.
    Returns a legal move (row, col) – a cell that hasn’t been shot yet.
    """
    # Phase 1 – first turn (board contains no hits yet)
    if not any(cell == 1 for row in board for cell in row):
        # Return the next coordinate in the spiral order that is still unknown
        spiral = _start_spiral()
        for (r, c) in spiral:
            if board[r][c] == 0:
                return r, c
        # Fallback – just pick the first unknown cell in row‑major order
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == 0:
                    return r, c

    # Phase 2 – board has at least one hit
    heat: List[List[int]] = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                continue  # only consider unknown cells
            heat[r][c] = _placements_covering_cell(board, r, c)

    best_score = -1
    best_pos: Tuple[int, int] = (0, 0)
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if heat[r][c] > best_score:
                best_score = heat[r][c]
                best_pos = (r, c)
            # Deterministic tie‑breaking: first row, then column
            # (random tie‑break would be fine but deterministic is enough)
    # Safety net – sanity check (should never be needed)
    if board[best_pos[0]][best_pos[1]] != 0:
        # Something went wrong; fall back to first unknown cell in row‑major order
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if board[r][c] == 0:
                    best_pos = (r, c)
                    break
        else:
            raise RuntimeError("No legal unknown cells found in board")
    return best_pos


# The file can be executed directly for debugging
if __name__ == "__main__":
    import sys, json
    if len(sys.argv) != 2:
        print("Usage: python policy.py <json_board>")
        sys.exit(1)
    try:
        board = json.loads(sys.argv[1])
    except Exception:
        print("Invalid JSON board")
        sys.exit(1)
    print(json.dumps(policy(board)))
