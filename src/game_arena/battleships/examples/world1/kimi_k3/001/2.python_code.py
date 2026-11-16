
import random

N = 10
SHIP_LENGTHS = (5, 4, 3, 3, 2)


def _make_placements():
    placements = {length: [] for length in set(SHIP_LENGTHS)}
    for r in range(N):
        for c in range(N):
            for length in placements:
                if c + length <= N:
                    mask = 0
                    for k in range(length):
                        mask |= 1 << (r * N + c + k)
                    placements[length].append(mask)
                if r + length <= N:
                    mask = 0
                    for k in range(length):
                        mask |= 1 << ((r + k) * N + c)
                    placements[length].append(mask)
    return placements


PLACEMENTS = _make_placements()
RC = tuple((i // N, i % N) for i in range(N * N))


def _bits(mask):
    while mask:
        low = mask & -mask
        yield low.bit_length() - 1
        mask ^= low


def _hit_runs(hit_mask):
    """Maximal horizontal/vertical hit runs. Isolated hits become size-1 runs."""
    runs = []
    long_mask = 0

    for r in range(N):
        c = 0
        while c < N:
            if (hit_mask >> (r * N + c)) & 1:
                start = c
                mask = 0
                while c < N and ((hit_mask >> (r * N + c)) & 1):
                    mask |= 1 << (r * N + c)
                    c += 1
                size = c - start
                if size >= 2:
                    runs.append((mask, size))
                    long_mask |= mask
            else:
                c += 1

    for c in range(N):
        r = 0
        while r < N:
            if (hit_mask >> (r * N + c)) & 1:
                start = r
                mask = 0
                while r < N and ((hit_mask >> (r * N + c)) & 1):
                    mask |= 1 << (r * N + c)
                    r += 1
                size = r - start
                if size >= 2:
                    runs.append((mask, size))
                    long_mask |= mask
            else:
                r += 1

    isolated = hit_mask & ~long_mask
    for i in _bits(isolated):
        runs.append((1 << i, 1))
    return runs


def _infer_closed_runs(runs, miss_mask, unknown_mask):
    """
    A hit run is closed when no remaining ship length can contain it while also
    containing at least one unknown cell. Closed runs are blocked and, when the
    run length exactly matches a remaining ship, remove one such ship.
    """
    remaining = list(SHIP_LENGTHS)
    closed_mask = 0

    changed = True
    while changed:
        changed = False
        bad = miss_mask | closed_mask
        lengths = set(remaining)

        for run_mask, size in runs:
            if run_mask & closed_mask:
                continue

            extendable = False
            for length in lengths:
                if length < size:
                    continue
                for placement in PLACEMENTS[length]:
                    if placement & bad:
                        continue
                    if (placement & run_mask) == run_mask and (placement & unknown_mask):
                        extendable = True
                        break
                if extendable:
                    break

            if not extendable:
                closed_mask |= run_mask
                try:
                    remaining.remove(size)
                except ValueError:
                    # Over-long adjacent-hit runs are still blocked, but we do not
                    # guess an ambiguous decomposition into multiple ships.
                    pass
                changed = True

    return closed_mask, remaining


def _valid_placement_map(remaining_lengths, bad_mask):
    counts = {}
    for length in remaining_lengths:
        counts[length] = counts.get(length, 0) + 1

    valid = {}
    for length in counts:
        arr = [p for p in PLACEMENTS[length] if not (p & bad_mask)]
        if arr:
            valid[length] = arr
    return counts, valid


def _heat_map(counts, valid, unknown_mask):
    heat = [0.0] * (N * N)
    for length, arr in valid.items():
        mult = counts.get(length, 0)
        if mult <= 0:
            continue
        weight = mult / len(arr)
        for placement in arr:
            cells = placement & unknown_mask
            for i in _bits(cells):
                heat[i] += weight
    return heat


def _run_target_scores(runs, counts, valid, unknown_mask):
    """
    For each hit run, condition on that run being covered by remaining ships.
    Unknown cells in covering placements get weight / total_covering_weight.
    """
    scores = [0.0] * (N * N)
    has_positive = False

    for run_mask, size in runs:
        total = 0.0
        contributions = []

        for length, arr in valid.items():
            mult = counts.get(length, 0)
            if mult <= 0 or length < size:
                continue
            weight = mult / len(arr)
            for placement in arr:
                if (placement & run_mask) != run_mask:
                    continue
                total += weight
                cells = placement & unknown_mask
                if cells:
                    contributions.append((cells, weight))

        if total > 0.0 and contributions:
            inv_total = 1.0 / total
            for cells, weight in contributions:
                add = weight * inv_total
                for i in _bits(cells):
                    scores[i] += add
                    has_positive = True

    return scores, has_positive


def policy(board: list[list[int]]) -> tuple[int, int]:
    hit_mask = 0
    miss_mask = 0
    unknown_mask = 0

    for r in range(N):
        base = r * N
        row = board[r]
        for c in range(N):
            v = row[c]
            bit = 1 << (base + c)
            if v == 0:
                unknown_mask |= bit
            elif v == 1:
                hit_mask |= bit
            elif v == -1:
                miss_mask |= bit
            # Any unexpected value is treated as unavailable for safety.

    legal = list(_bits(unknown_mask))
    if not legal:
        return (0, 0)

    seed = (hit_mask ^ (miss_mask << 1) ^ (unknown_mask << 7)) & ((1 << 64) - 1)
    rng = random.Random(seed)

    runs = _hit_runs(hit_mask) if hit_mask else []
    if hit_mask:
        closed_mask, remaining = _infer_closed_runs(runs, miss_mask, unknown_mask)
    else:
        closed_mask, remaining = 0, list(SHIP_LENGTHS)

    bad_mask = miss_mask | closed_mask
    counts, valid = _valid_placement_map(remaining, bad_mask)
    heat = _heat_map(counts, valid, unknown_mask) if valid else [0.0] * (N * N)

    # Target mode: finish extendable hit runs first. Multi-cell runs reveal
    # orientation, so they outrank isolated hits.
    if hit_mask:
        open_runs = [(mask, size) for mask, size in runs if not (mask & closed_mask)]
        multi_runs = [x for x in open_runs if x[1] >= 2]

        scores = [0.0] * (N * N)
        has_target = False
        if multi_runs:
            scores, has_target = _run_target_scores(multi_runs, counts, valid, unknown_mask)

        if not has_target:
            single_runs = [x for x in open_runs if x[1] == 1]
            if single_runs:
                scores, has_target = _run_target_scores(single_runs, counts, valid, unknown_mask)

        if has_target:
            order = legal[:]
            rng.shuffle(order)
            best = None
            best_score = -1.0
            best_heat = -1.0
            for i in order:
                score = scores[i]
                if score > best_score + 1e-15 or (
                    abs(score - best_score) <= 1e-15 and heat[i] > best_heat + 1e-15
                ):
                    best = i
                    best_score = score
                    best_heat = heat[i]
            if best is not None and best_score > 0.0:
                return RC[best]

    # Hunt mode: generalized checkerboard using the smallest usable remaining
    # ship length, then choose the hottest legal cell inside that residue class.
    cells = legal
    usable_lengths = [length for length in remaining if valid.get(length)]
    if usable_lengths:
        modulo = min(usable_lengths)
        if modulo > 1:
            residue_sum = [0.0] * modulo
            for i in legal:
                r, c = RC[i]
                residue_sum[(r + c) % modulo] += heat[i]

            residues = list(range(modulo))
            rng.shuffle(residues)
            best_residue = max(residues, key=lambda x: residue_sum[x])
            restricted = [
                i for i in legal
                if (RC[i][0] + RC[i][1]) % modulo == best_residue
            ]
            if restricted:
                cells = restricted

    order = cells[:]
    rng.shuffle(order)
    best = None
    best_heat = -1.0
    for i in order:
        if heat[i] > best_heat + 1e-15:
            best = i
            best_heat = heat[i]

    if best is None:
        best = legal[0]
    return RC[best]
