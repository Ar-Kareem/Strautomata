
import random
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Battleship AI policy.

    It first checks for any hits on the opponent's board. If hits exist,
    it builds a set of candidate cells that are directly adjacent (Manhattan
    distance <= 2) to at least one hit and that lie in the same row/col gap
    or at the ends of a horizontal/vertical cluster. Candidates are scored
    by the number of adjacent hits; the highest‑scoring candidates are
    returned, with random tie‑breaking.

    If there are no hits or no viable candidates, it falls back to a
    deterministic scan of the remaining unknown cells. The scan follows a
    left‑to‑right, top‑to‑bottom order and remembers the last guessed cell
    so that subsequent scans continue where they left off.

    The implementation retains persistent state across calls through the
    function object, so previous shots are implicitly stored.
    """

    # ------------------------------------------------------------------
    # Persistent state (function attribute) – remembers the last guess to
    # continue the scan across calls.
    # ------------------------------------------------------------------
    if not hasattr(policy, "_LAST_SCAN"):
        policy._LAST_SCAN = (-1, -1)

    # ------------------------------------------------------------------
    # Helper utilities
    # ------------------------------------------------------------------
    def linear(rc: Tuple[int, int]) -> int:
        """Convert (row, col) to a linear index 0‑99 used for ordering."""
        return rc[0] * 10 + rc[1]

    def adjacent_hits(pos: Tuple[int, int]) -> int:
        """Count hits (value 1) in the eight neighbours of `pos`."""
        r, c = pos
        cnt = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1:
                    cnt += 1
        return cnt

    # ------------------------------------------------------------------
    # Identify hits and still‑unknown cells on the current board
    # ------------------------------------------------------------------
    hits: List[Tuple[int, int]] = [
        (r, c) for r in range(10) for c in range(10)
        if board[r][c] == 1
    ]
    unknown_cells: List[Tuple[int, int]] = [
        (r, c) for r in range(10) for c in range(10)
        if board[r][c] == 0
    ]

    # ------------------------------------------------------------------
    # 1. Hit‑expansion phase – guess near known hits first
    # ------------------------------------------------------------------
    if hits:
        candidates: set = set()

        # Group hits by row and by column
        hit_by_row: dict = {}
        hit_by_col: dict = {}
        for r, c in hits:
            hit_by_row.setdefault(r, []).append(c)
            hit_by_col.setdefault(c, []).append(r)

        # ---- Horizontal (row) clusters ----
        for r, cols in hit_by_row.items():
            cols = sorted(cols)          # left → right
            minc, maxc = cols[0], cols[-1]

            # Cells inside the gap (including the immediate neighbour cells)
            for c in range(minc - 1, maxc + 2):
                if 0 <= c < 10 and board[r][c] == 0:
                    candidates.add((r, c))

            # Immediate extensions beyond the known ends
            for c in (minc - 1, maxc + 1):
                if 0 <= c < 10 and board[r][c] == 0:
                    candidates.add((r, c))

        # ---- Vertical (column) clusters ----
        for c, rows in hit_by_col.items():
            rows = sorted(rows)          # top → bottom
            minr, maxr = rows[0], rows[-1]

            # Cells inside the gap
            for r in range(minr - 1, maxr + 2):
                if 0 <= r < 10 and board[r][c] == 0:
                    candidates.add((r, c))

            # Immediate extensions beyond the known ends
            for r in (minr - 1, maxr + 1):
                if 0 <= r < 10 and board[r][c] == 0:
                    candidates.add((r, c))

        # If the candidate set is empty (e.g. no adjacent unknown cells),
        # switch to the scan fallback.
        if not candidates:
            return _scan_fallback(board, unknown_cells, policy._LAST_SCAN)

        # Score candidates by how many adjacent hits they have.
        scores = {pos: adjacent_hits(pos) for pos in candidates}
        max_score = max(scores.values())

        # Randomised tie‑breaking among the top‑scoring candidates.
        # Keep only up to three of them to avoid expensive random‑choice on huge lists.
        top_candidates = [pos for pos, s in scores.items() if s == max_score][:3]
        chosen = random.choice(top_candidates)

        # Remember the last guessed coordinate for the scan fallback.
        policy._LAST_SCAN = chosen
        return chosen

    # ------------------------------------------------------------------
    # 2. Scanning phase – systematic left‑to‑right, top‑to‑bottom search
    # ------------------------------------------------------------------
    return _scan_fallback(board, unknown_cells, policy._LAST_SCAN)


# ----------------------------------------------------------------------
# Helper: deterministic scan that continues from the last guessed cell.
# ----------------------------------------------------------------------
def _scan_fallback(board: List[List[int]],
                  unknown_cells: List[Tuple[int, int]],
                  last: Tuple[int, int]) -> Tuple[int, int]:
    """
    Returns the next cell to guess when we have no useful hit‑expansion
    candidates. The scan follows a lexicographic order (row, then column)
    and remembers `last` so that the next guess is the next unknown cell
    after `last` in that order. If `last` has already exceeded the last
    unknown cell we wrap around to the beginning.
    """
    if not unknown_cells:
        # This should never happen during a normal game, but we guard
        # against it by returning a legal cell (if any) arbitrarily.
        return random.choice([pos for pos in unknown_cells])  # will raise IndexError if empty

    if last == (-1, -1):
        return unknown_cells[0]

    last_lin = linear(last)
    nxt = None
    for rc in unknown_cells:
        lin = linear(rc)
        if lin > last_lin:
            nxt = rc
            break

    if nxt is None:           # wrap to the first cell after we have scanned all unknown cells
        nxt = unknown_cells[0]

    policy._LAST_SCAN = nxt
    return nxt
