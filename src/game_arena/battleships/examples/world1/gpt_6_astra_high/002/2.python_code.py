
import random
import math
import time
from bisect import bisect_right

_LENGTHS = (5, 4, 3, 3, 2)
_UNIQUE_LENGTHS = (5, 4, 3, 2)

# Precompute every geometrically possible ship placement.
_MASKS = []
_CELLS = []
_PLENGTH = []
_BY_LENGTH = {length: [] for length in _UNIQUE_LENGTHS}
_BY_CELL = {
    length: [[] for _ in range(100)]
    for length in _UNIQUE_LENGTHS
}

for _length in _UNIQUE_LENGTHS:
    for _vertical in (False, True):
        for _r in range(10):
            for _c in range(10):
                if _vertical:
                    if _r + _length > 10:
                        continue
                    _cells = tuple((_r + k) * 10 + _c
                                   for k in range(_length))
                else:
                    if _c + _length > 10:
                        continue
                    _cells = tuple(_r * 10 + _c + k
                                   for k in range(_length))
                _mask = sum(1 << cell for cell in _cells)
                _pid = len(_MASKS)
                _MASKS.append(_mask)
                _CELLS.append(_cells)
                _PLENGTH.append(_length)
                _BY_LENGTH[_length].append(_pid)
                for _cell in _cells:
                    _BY_CELL[_length][_cell].append(_pid)


def policy(board: list[list[int]]) -> tuple[int, int]:
    start = time.perf_counter()
    deadline = start + 0.86
    rng = random.Random()

    hits = 0
    misses = 0
    unknown = []
    for r in range(10):
        for c in range(10):
            cell = 10 * r + c
            value = board[r][c]
            if value == 0:
                unknown.append(cell)
            elif value == 1:
                hits |= 1 << cell
            else:
                misses |= 1 << cell

    # No legal action exists on a completely shot board; normal play ends
    # before this condition.
    if not unknown:
        return (0, 0)
    if len(unknown) == 1:
        return divmod(unknown[0], 10)
    if not hits and not misses:
        return (4, 4)

    masks = _MASKS
    domains = {
        length: tuple(p for p in _BY_LENGTH[length]
                      if not (masks[p] & misses))
        for length in _UNIQUE_LENGTHS
    }
    cover_cache = {
        length: {0: domains[length]}
        for length in _UNIQUE_LENGTHS
    }

    def covering(length, required):
        cache = cover_cache[length]
        result = cache.get(required)
        if result is not None:
            return result
        if required.bit_count() > length:
            cache[required] = ()
            return ()
        cell = (required & -required).bit_length() - 1
        result = tuple(
            p for p in _BY_CELL[length][cell]
            if not (masks[p] & misses)
            and masks[p] & required == required
        )
        cache[required] = result
        return result

    def fallback():
        scores = [0.0] * 100
        for length in _UNIQUE_LENGTHS:
            multiplicity = 2 if length == 3 else 1
            for p in domains[length]:
                h = (masks[p] & hits).bit_count()
                if h == length:
                    continue
                weight = multiplicity * (1.0 + 10.0 * h * h)
                for cell in _CELLS[p]:
                    r, c = divmod(cell, 10)
                    if board[r][c] == 0:
                        factor = 1.0 if h or (r + c) % 2 == 0 else 0.25
                        scores[cell] += weight * factor
        best = max(unknown, key=lambda cell: (scores[cell], -cell))
        return divmod(best, 10)

    if any(not domains[length] for length in _UNIQUE_LENGTHS):
        return fallback()

    # Find one consistent fleet with a constrained, randomized search.
    fleet = [-1] * 5
    nodes = 0
    aborted = False
    initialization_deadline = start + 0.14

    def initialize(remaining, occupied, uncovered):
        nonlocal nodes, aborted
        nodes += 1
        if aborted:
            return False
        if nodes % 32 == 0:
            if nodes > 6000 or time.perf_counter() > initialization_deadline:
                aborted = True
                return False

        capacity = sum(_LENGTHS[s] for s in remaining)
        if uncovered.bit_count() > capacity:
            return False
        if not remaining:
            return not uncovered

        if not uncovered:
            slot = remaining[0]
            choices = [
                p for p in domains[_LENGTHS[slot]]
                if not (masks[p] & occupied)
            ]
            rng.shuffle(choices)
            for p in choices:
                fleet[slot] = p
                if initialize(remaining[1:], occupied | masks[p], 0):
                    return True
                if aborted:
                    break
            return False

        best_choices = None
        bits = uncovered
        while bits:
            bit = bits & -bits
            bits ^= bit
            choices = []
            seen_lengths = set()
            for slot in remaining:
                length = _LENGTHS[slot]
                if length in seen_lengths:
                    continue
                seen_lengths.add(length)
                for p in covering(length, bit):
                    mask = masks[p]
                    if mask & occupied:
                        continue
                    if (uncovered & ~mask).bit_count() > capacity - length:
                        continue
                    choices.append((slot, p))
            if not choices:
                return False
            if best_choices is None or len(choices) < len(best_choices):
                best_choices = choices
                if len(choices) == 1:
                    break

        best_choices.sort(
            key=lambda item: (
                (masks[item[1]] & uncovered).bit_count()
                + 0.8 * rng.random()
            ),
            reverse=True
        )
        for slot, p in best_choices:
            fleet[slot] = p
            rest = tuple(s for s in remaining if s != slot)
            if initialize(rest, occupied | masks[p], uncovered & ~masks[p]):
                return True
            if aborted:
                break
        return False

    if not initialize(tuple(range(5)), 0, hits):
        return fallback()

    occupied = 0
    for p in fleet:
        occupied |= masks[p]

    hit_bits = []
    bits = hits
    while bits:
        bit = bits & -bits
        bits ^= bit
        hit_bits.append(bit)
    hit_bits.sort(
        key=lambda bit: sum(len(covering(length, bit))
                            for length in _LENGTHS)
    )

    # A whole-fleet independence proposal. Its exact proposal probability
    # is also evaluable, allowing a Metropolis correction.
    def fleet_proposal(existing=None):
        remaining = list(range(5))
        result = [-1] * 5
        used = 0
        uncovered = hits
        capacity = 17
        log_probability = 0.0

        while uncovered:
            pivot = next(bit for bit in hit_bits if bit & uncovered)
            candidates = []
            total = 0.0
            desired = None

            for slot in remaining:
                length = _LENGTHS[slot]
                scale = 1.0 / len(domains[length])
                for p in covering(length, pivot):
                    mask = masks[p]
                    if mask & used:
                        continue
                    left = uncovered & ~mask
                    if left.bit_count() > capacity - length:
                        continue
                    covered = (mask & uncovered).bit_count()
                    weight = scale * (4.0 ** (covered - 1))
                    candidates.append((slot, p, weight))
                    total += weight
                    if existing is not None and existing[slot] == p:
                        desired = (slot, p, weight)

            if not candidates:
                return None

            if existing is None:
                draw = rng.random() * total
                chosen = candidates[-1]
                for candidate in candidates:
                    draw -= candidate[2]
                    if draw <= 0:
                        chosen = candidate
                        break
            else:
                if desired is None:
                    return None
                chosen = desired

            slot, p, weight = chosen
            log_probability += math.log(weight / total)
            result[slot] = p
            remaining.remove(slot)
            used |= masks[p]
            uncovered &= ~masks[p]
            capacity -= _LENGTHS[slot]

        for slot in remaining:
            choices = [
                p for p in domains[_LENGTHS[slot]]
                if not (masks[p] & used)
            ]
            if not choices:
                return None
            if existing is None:
                p = rng.choice(choices)
            else:
                p = existing[slot]
                if p not in choices:
                    return None
            log_probability -= math.log(len(choices))
            result[slot] = p
            used |= masks[p]

        return result, log_probability

    histogram = [0] * len(masks)
    samples = 0
    iteration = 0

    while time.perf_counter() < deadline:
        iteration += 1

        if iteration % 48 == 0:
            proposal = fleet_proposal()
            if proposal is not None:
                current = fleet_proposal(fleet)
                if current is not None:
                    log_ratio = current[1] - proposal[1]
                    if math.log(max(rng.random(), 1e-300)) < log_ratio:
                        fleet = proposal[0]
                        occupied = 0
                        for p in fleet:
                            occupied |= masks[p]

        elif iteration % 4 == 0:
            # Exact one-ship conditional update.
            slot = rng.randrange(5)
            rest = occupied ^ masks[fleet[slot]]
            required = hits & ~rest
            choices = [
                p for p in covering(_LENGTHS[slot], required)
                if not (masks[p] & rest)
            ]
            if choices:
                p = rng.choice(choices)
                fleet[slot] = p
                occupied = rest | masks[p]

        else:
            # Joint updates can change which ship explains adjacent hits.
            a = rng.randrange(5)
            b = rng.randrange(4)
            if b >= a:
                b += 1

            rest = occupied ^ masks[fleet[a]] ^ masks[fleet[b]]
            required = hits & ~rest
            length_a = _LENGTHS[a]
            length_b = _LENGTHS[b]
            chosen_pair = None

            if not required:
                da = [p for p in domains[length_a]
                      if not (masks[p] & rest)]
                db = [p for p in domains[length_b]
                      if not (masks[p] & rest)]
                if da and db:
                    for _ in range(24):
                        pa = rng.choice(da)
                        pb = rng.choice(db)
                        if not (masks[pa] & masks[pb]):
                            chosen_pair = (pa, pb)
                            break
            else:
                groups = []
                cumulative = []
                total = 0
                local_b = {}

                for pa in domains[length_a]:
                    ma = masks[pa]
                    if ma & rest:
                        continue
                    needed_b = required & ~ma
                    if needed_b.bit_count() > length_b:
                        continue
                    bs = local_b.get(needed_b)
                    if bs is None:
                        bs = tuple(
                            p for p in covering(length_b, needed_b)
                            if not (masks[p] & rest)
                        )
                        local_b[needed_b] = bs
                    if bs:
                        total += len(bs)
                        groups.append((pa, bs))
                        cumulative.append(total)

                if total:
                    # Every proposed pair has equal probability before
                    # rejecting overlap. A capped rejection loop merely
                    # adds a state-independent self-transition.
                    for _ in range(32):
                        index = bisect_right(cumulative, rng.randrange(total))
                        pa, bs = groups[index]
                        pb = rng.choice(bs)
                        if not (masks[pa] & masks[pb]):
                            chosen_pair = (pa, pb)
                            break

            if chosen_pair is not None:
                pa, pb = chosen_pair
                fleet[a] = pa
                fleet[b] = pb
                occupied = rest | masks[pa] | masks[pb]

        if iteration > 64 and iteration % 2 == 0:
            samples += 1
            for p in fleet:
                histogram[p] += 1

    if not samples:
        for p in fleet:
            histogram[p] += 1
        samples = 1

    target = [0.0] * 100
    hunt = [0.0] * 100
    unseen_lengths = {length: 0.0 for length in _UNIQUE_LENGTHS}

    unknown_mask = 0
    for cell in unknown:
        unknown_mask |= 1 << cell

    for p, count in enumerate(histogram):
        if not count or not (masks[p] & unknown_mask):
            continue
        damaged = bool(masks[p] & hits)
        values = target if damaged else hunt
        if not damaged:
            unseen_lengths[_PLENGTH[p]] += count
        for cell in _CELLS[p]:
            if (1 << cell) & unknown_mask:
                values[cell] += count

    # Any undiscovered straight ship of length >= spacing intersects
    # every residue class of this diagonal search pattern.
    spacing = 2
    for length in (2, 3, 4, 5):
        if unseen_lengths[length] > 0.025 * samples:
            spacing = length
            break

    residue_counts = [0] * spacing
    residue_mass = [0.0] * spacing
    for cell in unknown:
        r, c = divmod(cell, 10)
        residue = (r + c) % spacing
        residue_counts[residue] += 1
        residue_mass[residue] += hunt[cell]

    possible_residues = [
        residue for residue in range(spacing)
        if residue_counts[residue]
    ]
    preferred = min(
        possible_residues,
        key=lambda residue: (
            residue_counts[residue],
            -residue_mass[residue],
            residue
        )
    )

    def shot_score(cell):
        r, c = divmod(cell, 10)
        search_factor = 1.0 if (r + c) % spacing == preferred else 0.22
        return (
            1.08 * target[cell] + search_factor * hunt[cell],
            rng.random()
        )

    best = max(unknown, key=shot_score)
    return divmod(best, 10)
