
import random
from collections import deque

N = 10
FLEET = (5, 4, 3, 3, 2)

_SEGMENTS = None
_SEGMENTS_BY_ORIENT = None


def _build_segments():
    """Precompute all horizontal and vertical ship segments."""
    global _SEGMENTS, _SEGMENTS_BY_ORIENT

    if _SEGMENTS is not None:
        return

    _SEGMENTS = {L: [] for L in set(FLEET)}
    _SEGMENTS_BY_ORIENT = {(L, "H"): [] for L in set(FLEET)}
    _SEGMENTS_BY_ORIENT.update({(L, "V"): [] for L in set(FLEET)})

    for L in set(FLEET):
        # Horizontal
        for r in range(N):
            for c in range(N - L + 1):
                cells = tuple(r * N + (c + k) for k in range(L))
                mask = 0
                for idx in cells:
                    mask |= 1 << idx
                seg = (mask, cells, "H")
                _SEGMENTS[L].append(seg)
                _SEGMENTS_BY_ORIENT[(L, "H")].append(seg)

        # Vertical
        for r in range(N - L + 1):
            for c in range(N):
                cells = tuple((r + k) * N + c for k in range(L))
                mask = 0
                for idx in cells:
                    mask |= 1 << idx
                seg = (mask, cells, "V")
                _SEGMENTS[L].append(seg)
                _SEGMENTS_BY_ORIENT[(L, "V")].append(seg)


def _fallback(board):
    """Return any legal move, preferring central cells."""
    best = None
    best_dist = 10**9

    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                d = abs(r - 4.5) + abs(c - 4.5)
                if d < best_dist:
                    best_dist = d
                    best = (r, c)

    if best is not None:
        return best

    # The game should normally be over before this happens.
    return (0, 0)


def _components(hit_cells):
    """Find orthogonally connected components of hit cells."""
    hit_set = set(hit_cells)
    comps = []

    while hit_set:
        start = hit_set.pop()
        q = deque([start])
        comp = [start]

        while q:
            idx = q.popleft()
            r, c = divmod(idx, N)

            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < N and 0 <= nc < N:
                    nidx = nr * N + nc
                    if nidx in hit_set:
                        hit_set.remove(nidx)
                        q.append(nidx)
                        comp.append(nidx)

        comps.append(comp)

    return comps


def policy(board: list[list[int]]) -> tuple[int, int]:
    _build_segments()

    miss_mask = 0
    hit_mask = 0
    unknown = []
    hit_cells = []

    for r in range(N):
        for c in range(N):
            idx = r * N + c
            v = board[r][c]
            if v == -1:
                miss_mask |= 1 << idx
            elif v == 1:
                hit_mask |= 1 << idx
                hit_cells.append(idx)
            else:
                unknown.append(idx)

    if not unknown:
        return (0, 0)

    unknown_set = set(unknown)

    # ------------------------------------------------------------------
    # TARGET MODE
    # ------------------------------------------------------------------
    # Score unknown cells that could complete or extend known hit clusters.
    target_score = [0.0] * (N * N)

    if hit_cells:
        comps = _components(hit_cells)

        for comp in comps:
            comp_mask = 0
            for idx in comp:
                comp_mask |= 1 << idx

            rows = {idx // N for idx in comp}
            cols = {idx % N for idx in comp}
            size = len(comp)

            # If the component is a clean line, only extend in that direction.
            # This avoids wasting many shots beside an already-complete ship.
            if size == 1:
                orientations = ("H", "V")
                effective_parts = [comp]
            elif len(rows) == 1:
                orientations = ("H",)
                effective_parts = [comp]
            elif len(cols) == 1:
                orientations = ("V",)
                effective_parts = [comp]
            else:
                # Rare case: touching ships can create an L/T-shaped hit group.
                # Treat each hit as a singleton so we still return a strong target.
                orientations = ("H", "V")
                effective_parts = [[idx] for idx in comp]

            for part in effective_parts:
                part_mask = 0
                for idx in part:
                    part_mask |= 1 << idx

                part_size = len(part)
                part_coords = [(idx // N, idx % N) for idx in part]

                for orient in orientations:
                    for L in FLEET:
                        if L < part_size:
                            continue

                        for mask, cells, _ in _SEGMENTS_BY_ORIENT[(L, orient)]:
                            if mask & miss_mask:
                                continue
                            if part_mask & ~mask:
                                continue

                            extra_hits = (mask & hit_mask).bit_count() - part_size
                            base = 900.0 * part_size * part_size + 90.0 * L + 250.0 * max(0, extra_hits)

                            for idx in cells:
                                if idx not in unknown_set:
                                    continue

                                r, c = divmod(idx, N)
                                dist = min(abs(r - hr) + abs(c - hc) for hr, hc in part_coords)
                                if dist <= 0:
                                    dist = 1

                                # Adjacent cells to a hit are much more valuable than far cells.
                                target_score[idx] += base / dist

        max_target = max(target_score[idx] for idx in unknown)
        if max_target > 0:
            best = [idx for idx in unknown if abs(target_score[idx] - max_target) < 1e-9]
            choice = random.choice(best)
            return divmod(choice, N)

    # ------------------------------------------------------------------
    # HUNT MODE
    # ------------------------------------------------------------------
    # Count how often each unknown cell appears in a legal remaining ship
    # placement.  When no active target exists, known hit cells are treated
    # as occupied and avoided by new hunt placements.
    hunt_score = [0.0] * (N * N)
    blocked = miss_mask
    if hit_cells:
        blocked |= hit_mask

    for L in FLEET:
        for mask, cells, _ in _SEGMENTS[L]:
            if mask & blocked:
                continue

            # Slightly favor longer placements because they represent more
            # remaining ship mass and central flexibility.
            weight = 1.0 + 0.08 * L

            for idx in cells:
                if idx in unknown_set:
                    hunt_score[idx] += weight

    # Early game checkerboard parity: since the smallest ship length is 2,
    # firing one color of a checkerboard cannot miss every ship.
    candidates = list(unknown)

    if not hit_cells and len(unknown) > 35:
        even_total = sum(hunt_score[idx] for idx in unknown if ((idx // N) + (idx % N)) % 2 == 0)
        odd_total = sum(hunt_score[idx] for idx in unknown if ((idx // N) + (idx % N)) % 2 == 1)
        preferred_parity = 0 if even_total >= odd_total else 1

        parity_candidates = [
            idx for idx in unknown
            if ((idx // N) + (idx % N)) % 2 == preferred_parity
        ]

        if parity_candidates:
            candidates = parity_candidates

    max_hunt = max(hunt_score[idx] for idx in candidates)
    if max_hunt > 0:
        best = [idx for idx in candidates if abs(hunt_score[idx] - max_hunt) < 1e-9]
        choice = random.choice(best)
        return divmod(choice, N)

    # Absolute safety fallback.
    return _fallback(board)
