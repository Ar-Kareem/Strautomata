
from __future__ import annotations

_N = 10
_SIZE = _N * _N

_FLEET = (5, 4, 3, 3, 2)
_LENGTHS = (5, 4, 3, 2)
_MULTIPLICITY = {5: 1.0, 4: 1.0, 3: 2.0, 2: 1.0}

_BITS = tuple(1 << i for i in range(_SIZE))
_HIT_WEIGHTS = (0.0, 8.0, 64.0, 512.0, 4096.0, 32768.0)


def _build_placements():
    placements = {length: [] for length in _LENGTHS}

    for length in _LENGTHS:
        # Horizontal placements
        for r in range(_N):
            for c in range(_N - length + 1):
                cells = tuple(r * _N + c + k for k in range(length))
                mask = 0
                for idx in cells:
                    mask |= _BITS[idx]

                end_mask = 0
                if c > 0:
                    end_mask |= _BITS[r * _N + c - 1]
                if c + length < _N:
                    end_mask |= _BITS[r * _N + c + length]

                placements[length].append((mask, cells, end_mask))

        # Vertical placements
        for r in range(_N - length + 1):
            for c in range(_N):
                cells = tuple((r + k) * _N + c for k in range(length))
                mask = 0
                for idx in cells:
                    mask |= _BITS[idx]

                end_mask = 0
                if r > 0:
                    end_mask |= _BITS[(r - 1) * _N + c]
                if r + length < _N:
                    end_mask |= _BITS[(r + length) * _N + c]

                placements[length].append((mask, cells, end_mask))

    return placements


def _build_parity0():
    mask = 0
    for r in range(_N):
        for c in range(_N):
            if (r + c) % 2 == 0:
                mask |= _BITS[r * _N + c]
    return mask


_PLACEMENTS = _build_placements()
_PARITY0 = _build_parity0()


def _scan_board(board):
    legal_mask = 0
    miss_mask = 0
    hit_mask = 0

    for r in range(_N):
        for c in range(_N):
            idx = r * _N + c
            bit = _BITS[idx]
            try:
                value = board[r][c]
            except Exception:
                value = -1

            if value == 0:
                legal_mask |= bit
            elif value == 1:
                hit_mask |= bit
            else:
                miss_mask |= bit

    return legal_mask, miss_mask, hit_mask


def _adjacent_hit_cells(hit_mask):
    """Hit cells that touch another hit orthogonally."""
    out = 0
    m = hit_mask

    while m:
        bit = m & -m
        idx = bit.bit_length() - 1
        r = idx // _N
        c = idx - r * _N

        adjacent = False
        if r > 0 and (hit_mask & _BITS[idx - _N]):
            adjacent = True
        elif r + 1 < _N and (hit_mask & _BITS[idx + _N]):
            adjacent = True
        elif c > 0 and (hit_mask & _BITS[idx - 1]):
            adjacent = True
        elif c + 1 < _N and (hit_mask & _BITS[idx + 1]):
            adjacent = True

        if adjacent:
            out |= bit

        m ^= bit

    return out


def _hunt_scores(legal_mask, miss_mask, hit_mask):
    """
    Scores unknown cells by how many still-possible unhit ship placements pass
    through them. Known hits are treated as occupied/blocking here; active hit
    ships are handled separately by target mode.
    """
    scores = [0.0] * _SIZE
    blocked = miss_mask | hit_mask

    for length in _LENGTHS:
        valid_count = 0
        for mask, _, _ in _PLACEMENTS[length]:
            if (mask & blocked) == 0:
                valid_count += 1

        if valid_count == 0:
            continue

        weight = 1000.0 * _MULTIPLICITY[length] / valid_count

        for mask, cells, _ in _PLACEMENTS[length]:
            if mask & blocked:
                continue
            for idx in cells:
                if legal_mask & _BITS[idx]:
                    scores[idx] += weight

    return scores


def _target_scores(legal_mask, miss_mask, hit_mask):
    """
    Scores cells that could complete/extend already-hit ships. Placements
    covering more hits get exponentially more weight.
    """
    scores = [0.0] * _SIZE
    adjacent_hits = _adjacent_hit_cells(hit_mask)

    for length in _LENGTHS:
        valid_count = 0
        for mask, _, _ in _PLACEMENTS[length]:
            if (mask & miss_mask) == 0:
                valid_count += 1

        if valid_count == 0:
            continue

        base_weight = 1000.0 * _MULTIPLICITY[length] / valid_count

        for mask, cells, end_mask in _PLACEMENTS[length]:
            if mask & miss_mask:
                continue

            hit_part = mask & hit_mask
            if not hit_part:
                continue

            # Do not cut a known straight run of hits in the middle.
            if end_mask & hit_mask:
                continue

            h = hit_part.bit_count()

            # If a hit already has an adjacent hit, prefer the established line
            # rather than shooting perpendicular single-hit guesses.
            if h == 1 and (hit_part & adjacent_hits):
                continue

            if (mask & legal_mask) == 0:
                continue

            weight = base_weight * _HIT_WEIGHTS[h]

            for idx in cells:
                if legal_mask & _BITS[idx]:
                    scores[idx] += weight

    return scores


def _positive_mask(scores, mask):
    out = 0
    m = mask
    while m:
        bit = m & -m
        idx = bit.bit_length() - 1
        if scores[idx] > 0.0:
            out |= bit
        m ^= bit
    return out


def _max_on_mask(scores, mask):
    best = 0.0
    m = mask
    while m:
        bit = m & -m
        idx = bit.bit_length() - 1
        if scores[idx] > best:
            best = scores[idx]
        m ^= bit
    return best


def _select(scores, candidate_mask, legal_mask, state):
    mask = candidate_mask & legal_mask
    if mask == 0:
        mask = legal_mask
    if mask == 0:
        return (0, 0)

    best_idx = -1
    best_key = None

    while mask:
        bit = mask & -mask
        idx = bit.bit_length() - 1
        mask ^= bit

        r = idx // _N
        c = idx - r * _N

        # Prefer high score, then central cells, then deterministic jitter.
        center = -((2 * r - 9) * (2 * r - 9) + (2 * c - 9) * (2 * c - 9))
        jitter = (((idx + 1) * 1103515245 + state) & 0xFFFF)

        key = (scores[idx], center, jitter)
        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return (best_idx // _N, best_idx % _N)


def policy(board: list[list[int]]) -> tuple[int, int]:
    legal_mask, miss_mask, hit_mask = _scan_board(board)

    if legal_mask == 0:
        return (0, 0)

    state = (miss_mask ^ (hit_mask << 11) ^ (hit_mask >> 17)) & 0xFFFFFFFF

    # Target mode: pursue known hits if there is a plausible continuation.
    if hit_mask:
        target = _target_scores(legal_mask, miss_mask, hit_mask)
        target_mask = _positive_mask(target, legal_mask)

        if target_mask:
            hunt = _hunt_scores(legal_mask, miss_mask, hit_mask)
            combined = target[:]
            for idx in range(_SIZE):
                if legal_mask & _BITS[idx]:
                    combined[idx] += 0.001 * hunt[idx]
            return _select(combined, target_mask, legal_mask, state)

    # Hunt mode: probability heat-map, restricted to checkerboard parity when useful.
    hunt = _hunt_scores(legal_mask, miss_mask, hit_mask)

    parity_candidates = legal_mask & _PARITY0
    if parity_candidates and _max_on_mask(hunt, parity_candidates) > 0.0:
        return _select(hunt, parity_candidates, legal_mask, state)

    return _select(hunt, legal_mask, legal_mask, state)
