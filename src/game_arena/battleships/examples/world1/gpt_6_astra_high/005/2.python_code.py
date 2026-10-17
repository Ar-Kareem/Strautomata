
import random
import time
from bisect import bisect_right
from functools import lru_cache


# All possible placements, shared between calls.
_PLACEMENTS = {}
_CELLS = []

for _length in (5, 4, 3, 2):
    _records = []
    for _vertical in (False, True):
        _rows = 11 - _length if _vertical else 10
        _cols = 10 if _vertical else 11 - _length
        for _r in range(_rows):
            for _c in range(_cols):
                _cells = tuple(
                    (_r + (k if _vertical else 0)) * 10
                    + _c + (0 if _vertical else k)
                    for k in range(_length)
                )
                _mask = sum(1 << cell for cell in _cells)
                _pid = len(_CELLS)
                _CELLS.append(_cells)
                _records.append((_mask, _pid))
    _PLACEMENTS[_length] = _records


class _BudgetExpired(Exception):
    pass


def _fallback(board, unknown, misses, hits):
    """Fast placement-density policy, used if inference cannot finish."""
    remaining = [5, 4, 3, 3, 2]
    resolved = 0
    unseen_hits = {i for i in range(100) if hits & (1 << i)}
    components = []

    while unseen_hits:
        first = unseen_hits.pop()
        component = [first]
        stack = [first]
        while stack:
            cell = stack.pop()
            r, c = divmod(cell, 10)
            neighbors = []
            if r:
                neighbors.append(cell - 10)
            if r < 9:
                neighbors.append(cell + 10)
            if c:
                neighbors.append(cell - 1)
            if c < 9:
                neighbors.append(cell + 1)
            for other in neighbors:
                if other in unseen_hits:
                    unseen_hits.remove(other)
                    component.append(other)
                    stack.append(other)
        components.append(component)

    def closed(r, c):
        return not (0 <= r < 10 and 0 <= c < 10) or board[r][c] == -1

    # Recognize particularly convincing completed straight components.
    for component in sorted(components, key=len, reverse=True):
        size = len(component)
        if size not in remaining:
            continue
        rows = {cell // 10 for cell in component}
        cols = {cell % 10 for cell in component}
        if len(rows) == 1:
            r = next(iter(rows))
            lo, hi = min(cols), max(cols)
            blocked = closed(r, lo - 1) and closed(r, hi + 1)
        elif len(cols) == 1:
            c = next(iter(cols))
            lo, hi = min(rows), max(rows)
            blocked = closed(lo - 1, c) and closed(hi + 1, c)
        else:
            continue
        if blocked or size == max(remaining):
            remaining.remove(size)
            for cell in component:
                resolved |= 1 << cell

    active_hits = hits & ~resolved
    forbidden = misses | resolved
    scores = [0.0] * 100

    for length in remaining:
        for mask, pid in _PLACEMENTS[length]:
            if mask & forbidden:
                continue
            count = (mask & active_hits).bit_count()
            weight = 1.0 + 32.0 * count * count
            for cell in _CELLS[pid]:
                scores[cell] += weight

    best = max(
        unknown,
        key=lambda cell: (
            scores[cell],
            (cell // 10 + cell % 10) % 2 == 0,
            -abs(cell // 10 - 4.5) - abs(cell % 10 - 4.5),
        ),
    )
    return divmod(best, 10)


def policy(board: list[list[int]]) -> tuple[int, int]:
    started = time.perf_counter()
    deadline = started + 0.80
    count_deadline = started + 0.24

    unknown = []
    misses = 0
    hits = 0
    for r in range(10):
        for c in range(10):
            cell = 10 * r + c
            value = board[r][c]
            if value == 0:
                unknown.append(cell)
            elif value == -1:
                misses |= 1 << cell
            elif value == 1:
                hits |= 1 << cell

    # A completely fired-upon board has no legal action. The arena normally
    # terminates before presenting such a state.
    if not unknown:
        return (0, 0)
    if len(unknown) == 1:
        return divmod(unknown[0], 10)
    if not (misses | hits):
        return (4, 4)
    if hits.bit_count() >= 17:
        return divmod(unknown[0], 10)

    rng = random.Random(hits ^ (misses << 1) ^ 0x9E3779B97F4A7C15)

    # Group placements by the exact set of observed hits they contain.
    grouped = {}
    for length, records in _PLACEMENTS.items():
        groups = {}
        for mask, pid in records:
            if not mask & misses:
                hit_pattern = mask & hits
                groups.setdefault(hit_pattern, []).append((mask, pid))
        grouped[length] = groups

    lengths = (5, 4, 3, 3, 2)
    maps = [grouped[length] for length in lengths]
    if any(not groups for groups in maps):
        return _fallback(board, unknown, misses, hits)

    entries = [
        [(pattern, records, len(records))
         for pattern, records in groups.items()]
        for groups in maps
    ]

    capacity = [0] * 6
    possible_hits = [0] * 6
    for i in range(4, -1, -1):
        capacity[i] = capacity[i + 1] + lengths[i]
        union = 0
        for pattern in maps[i]:
            union |= pattern
        possible_hits[i] = possible_hits[i + 1] | union

    calls = 0

    @lru_cache(maxsize=None)
    def ways(i, uncovered):
        """Count hit-covering fleets, temporarily allowing unknown overlap."""
        nonlocal calls
        calls += 1
        if calls & 255 == 0:
            if time.perf_counter() >= count_deadline:
                raise _BudgetExpired

        if uncovered.bit_count() > capacity[i]:
            return 0
        if uncovered & ~possible_hits[i]:
            return 0
        if i == 4:
            records = maps[4].get(uncovered)
            return len(records) if records is not None else 0

        total = 0
        for pattern, records, multiplicity in entries[i]:
            if pattern & uncovered == pattern:
                total += multiplicity * ways(i + 1, uncovered ^ pattern)
        return total

    try:
        total_fleets = ways(0, hits)
    except _BudgetExpired:
        return _fallback(board, unknown, misses, hits)

    if not total_fleets:
        return _fallback(board, unknown, misses, hits)

    transition_cache = [{} for _ in range(4)]

    def transitions(i, uncovered):
        cached = transition_cache[i].get(uncovered)
        if cached is not None:
            return cached

        options = []
        cumulative = []
        total = 0
        for pattern, records, multiplicity in entries[i]:
            if pattern & uncovered != pattern:
                continue
            child_count = ways(i + 1, uncovered ^ pattern)
            if child_count:
                options.append((pattern, records, child_count))
                total += multiplicity * child_count
                cumulative.append(total)

        result = (options, cumulative, total)
        transition_cache[i][uncovered] = result
        return result

    placement_weight = [0.0] * len(_CELLS)
    weight_sum = 0.0
    attempts = 0
    importance_mode = False
    randrange = rng.randrange

    while True:
        if attempts & 63 == 0:
            if time.perf_counter() >= deadline:
                break
            # When ordinary rejection is inefficient, avoid collisions
            # locally and correct the resulting sampling bias with weights.
            if attempts >= 256 and weight_sum < 0.10 * attempts:
                importance_mode = True
        attempts += 1

        occupied = 0
        uncovered = hits
        chosen = []
        weight = 1.0
        valid_prefix = True

        for i in range(4):
            options, cumulative, relaxed_total = transitions(i, uncovered)

            if importance_mode and occupied:
                allowed_options = []
                allowed_cumulative = []
                allowed_total = 0

                for pattern, records, child_count in options:
                    legal = [
                        record for record in records
                        if not record[0] & occupied
                    ]
                    if legal:
                        allowed_total += len(legal) * child_count
                        allowed_options.append((pattern, legal))
                        allowed_cumulative.append(allowed_total)

                if not allowed_total:
                    valid_prefix = False
                    break

                weight *= allowed_total / relaxed_total
                index = bisect_right(
                    allowed_cumulative, randrange(allowed_total)
                )
                pattern, records = allowed_options[index]
                mask, pid = records[randrange(len(records))]
            else:
                index = bisect_right(
                    cumulative, randrange(relaxed_total)
                )
                pattern, records, _ = options[index]
                mask, pid = records[randrange(len(records))]
                if mask & occupied:
                    valid_prefix = False
                    break

            occupied |= mask
            uncovered ^= pattern
            chosen.append(pid)

        if not valid_prefix:
            continue

        final_records = maps[4].get(uncovered)
        if not final_records:
            continue

        if importance_mode or len(final_records) <= 24:
            # Integrate over the final ship instead of sampling it.
            legal_ids = [
                pid for mask, pid in final_records
                if not mask & occupied
            ]
            if not legal_ids:
                continue

            each_weight = weight / len(final_records)
            fleet_weight = each_weight * len(legal_ids)

            for pid in chosen:
                placement_weight[pid] += fleet_weight
            for pid in legal_ids:
                placement_weight[pid] += each_weight
            weight_sum += fleet_weight
        else:
            mask, pid = final_records[randrange(len(final_records))]
            if mask & occupied:
                continue

            for previous_pid in chosen:
                placement_weight[previous_pid] += weight
            placement_weight[pid] += weight
            weight_sum += weight

    if weight_sum <= 0.0:
        return _fallback(board, unknown, misses, hits)

    scores = [0.0] * 100
    for pid, weight in enumerate(placement_weight):
        if weight:
            for cell in _CELLS[pid]:
                scores[cell] += weight

    # Only unknown cells are eligible, regardless of inference outcome.
    best = max(
        unknown,
        key=lambda cell: (
            scores[cell],
            (cell // 10 + cell % 10) % 2 == 0,
            -abs(cell // 10 - 4.5) - abs(cell % 10 - 4.5),
        ),
    )
    return divmod(best, 10)
