
from __future__ import annotations

N = 10

# Fleet: one each of 5, 4, 2 and two ships of length 3.
_LENGTH_MULT = {2: 1, 3: 2, 4: 1, 5: 1}
_LENGTHS = (2, 3, 4, 5)

# Precomputed placements:
# each item is (mask, cells, before_cell, after_cell)
_PLACEMENTS = {}


def _build_placements():
    for length in _LENGTHS:
        placements = []

        # Horizontal placements
        for r in range(N):
            for c in range(N - length + 1):
                cells = tuple(r * N + (c + k) for k in range(length))
                mask = 0
                for idx in cells:
                    mask |= 1 << idx
                before = r * N + (c - 1) if c > 0 else -1
                after = r * N + (c + length) if c + length < N else -1
                placements.append((mask, cells, before, after))

        # Vertical placements
        for r in range(N - length + 1):
            for c in range(N):
                cells = tuple((r + k) * N + c for k in range(length))
                mask = 0
                for idx in cells:
                    mask |= 1 << idx
                before = (r - 1) * N + c if r > 0 else -1
                after = (r + length) * N + c if r + length < N else -1
                placements.append((mask, cells, before, after))

        _PLACEMENTS[length] = placements


_build_placements()

# Neighbor masks for hit-run detection.
_NEIGH_MASK = [0] * (N * N)
for r in range(N):
    for c in range(N):
        idx = r * N + c
        m = 0
        if r > 0:
            m |= 1 << ((r - 1) * N + c)
        if r + 1 < N:
            m |= 1 << ((r + 1) * N + c)
        if c > 0:
            m |= 1 << (r * N + c - 1)
        if c + 1 < N:
            m |= 1 << (r * N + c + 1)
        _NEIGH_MASK[idx] = m


def _mix32(x: int) -> int:
    """Small deterministic mixer for tie-breaking."""
    x &= 0xFFFFFFFF
    x ^= x >> 16
    x = (x * 0x7FEB352D) & 0xFFFFFFFF
    x ^= x >> 15
    x = (x * 0x846CA68B) & 0xFFFFFFFF
    x ^= x >> 16
    return x & 0xFFFFFFFF


def _fallback_space(flat: list[int], idx: int) -> int:
    """Tie-breaker favoring cells in larger unfired open lines."""
    r, c = divmod(idx, N)
    score = 0

    # Horizontal open segment through idx.
    length = 1
    cc = c - 1
    while cc >= 0 and flat[r * N + cc] == 0:
        length += 1
        cc -= 1
    cc = c + 1
    while cc < N and flat[r * N + cc] == 0:
        length += 1
        cc += 1
    score += length * length

    # Vertical open segment through idx.
    length = 1
    rr = r - 1
    while rr >= 0 and flat[rr * N + c] == 0:
        length += 1
        rr -= 1
    rr = r + 1
    while rr < N and flat[rr * N + c] == 0:
        length += 1
        rr += 1
    score += length * length

    return score


def policy(board: list[list[int]]) -> tuple[int, int]:
    flat = []
    unknowns = []
    miss_mask = 0
    hit_mask = 0

    for r in range(N):
        row = board[r]
        for c in range(N):
            v = row[c]
            idx = r * N + c
            flat.append(v)
            if v == 0:
                unknowns.append(idx)
            elif v == -1:
                miss_mask |= 1 << idx
            elif v == 1:
                hit_mask |= 1 << idx

    # No legal move exists on a full board; this should not happen before game end.
    if not unknowns:
        return (0, 0)

    fired_mask = miss_mask | hit_mask

    # ------------------------------------------------------------------
    # Hunt score: placement density for undiscovered ship cells.
    # Known hits are treated as blockers here because target mode handles
    # extensions of already-discovered ships.
    # ------------------------------------------------------------------
    hunt = [0.0] * (N * N)

    valid_hunt_counts = {}
    for length in _LENGTHS:
        count = 0
        for mask, cells, before, after in _PLACEMENTS[length]:
            if mask & fired_mask == 0:
                count += 1
        valid_hunt_counts[length] = count

    for length in _LENGTHS:
        count = valid_hunt_counts[length]
        if count <= 0:
            continue
        w = _LENGTH_MULT[length] / count
        for mask, cells, before, after in _PLACEMENTS[length]:
            if mask & fired_mask:
                continue
            for idx in cells:
                hunt[idx] += w

    # ------------------------------------------------------------------
    # Target score: placements that include known hits and avoid misses.
    # This strongly prefers extending hit runs and filling gaps.
    # ------------------------------------------------------------------
    target = [0.0] * (N * N)

    if hit_mask:
        hit_has_neighbor = [False] * (N * N)
        for idx in range(N * N):
            if (hit_mask >> idx) & 1:
                hit_has_neighbor[idx] = bool(_NEIGH_MASK[idx] & hit_mask)

        valid_target_counts = {}
        for length in _LENGTHS:
            count = 0
            for mask, cells, before, after in _PLACEMENTS[length]:
                if mask & miss_mask == 0:
                    count += 1
            valid_target_counts[length] = count

        for length in _LENGTHS:
            denom = valid_target_counts[length]
            if denom <= 0:
                continue

            mult = _LENGTH_MULT[length]

            for mask, cells, before, after in _PLACEMENTS[length]:
                if mask & miss_mask:
                    continue

                hm = mask & hit_mask
                if not hm:
                    continue

                hc = hm.bit_count()
                remaining_cells = length - hc
                if remaining_cells <= 0:
                    continue

                # Do not split an already-contiguous hit run by choosing
                # a placement whose immediate extension is also a hit.
                if before >= 0 and ((hit_mask >> before) & 1):
                    continue
                if after >= 0 and ((hit_mask >> after) & 1):
                    continue

                # If this placement contains only one hit and that hit is
                # already adjacent to another hit, the ship orientation is
                # probably known; avoid perpendicular distractions.
                if hc == 1:
                    low_bit = hm & -hm
                    hidx = low_bit.bit_length() - 1
                    if hit_has_neighbor[hidx]:
                        continue

                hit_positions = []
                unknown_positions = []

                for pos, idx in enumerate(cells):
                    v = flat[idx]
                    if v == 1:
                        hit_positions.append(pos)
                    elif v == 0:
                        unknown_positions.append((pos, idx))

                if not unknown_positions or not hit_positions:
                    continue

                lo = min(hit_positions)
                hi = max(hit_positions)

                # Approximate posterior weight:
                # - more included hits => much stronger evidence
                # - fewer unknown cells left in the placement => stronger
                # - normalized by number of legal placements of that length
                base = mult * 10000.0 * (hc * hc) / (denom * remaining_cells)

                for pos, idx in unknown_positions:
                    d = min(abs(pos - hp) for hp in hit_positions)
                    if d <= 0:
                        continue

                    factor = 1.0 / d

                    # Adjacent extensions are usually the most informative.
                    if d == 1:
                        factor *= 1.7

                    # Unknown cells between two known hits are especially valuable.
                    if lo < pos < hi:
                        factor *= 3.0

                    target[idx] += base * factor

    seed = _mix32((miss_mask ^ (hit_mask * 0x9E3779B1)) & 0xFFFFFFFF)

    def jitter(idx: int) -> int:
        return _mix32(seed ^ (idx * 0x85EBCA6B))

    # If there is a plausible target shot, take it.
    best_target_value = 0.0
    for idx in unknowns:
        if target[idx] > best_target_value:
            best_target_value = target[idx]

    if best_target_value > 0.0:
        best = max(
            unknowns,
            key=lambda i: (
                target[i],
                hunt[i],
                _fallback_space(flat, i),
                jitter(i),
            ),
        )
        return divmod(best, N)

    # Otherwise hunt. Prefer one checkerboard color: every remaining ship
    # of length >= 2 must occupy at least one cell of each parity.
    parity_candidates = [
        i for i in unknowns
        if ((i // N + i % N) & 1) == 0 and hunt[i] > 0.0
    ]

    if parity_candidates:
        candidates = parity_candidates
    else:
        # If that parity is exhausted or impossible, use any legal unknown.
        nonzero = [i for i in unknowns if hunt[i] > 0.0]
        candidates = nonzero if nonzero else unknowns

    best = max(
        candidates,
        key=lambda i: (
            hunt[i],
            _fallback_space(flat, i),
            jitter(i),
        ),
    )

    return divmod(best, N)
