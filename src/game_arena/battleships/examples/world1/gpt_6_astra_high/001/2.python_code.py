
import random
import time
from bisect import bisect_right
from collections import OrderedDict, deque

_LENGTHS = (5, 4, 3, 3, 2)
_PAIRS = tuple((i, j) for i in range(5) for j in range(i + 1, 5))

# Every possible placement, represented by a 100-bit integer.
_PLACEMENTS = {}
for _length in (2, 3, 4, 5):
    _positions = []
    for _row in range(10):
        for _col in range(11 - _length):
            _positions.append(
                ((1 << _length) - 1) << (10 * _row + _col)
            )
    for _row in range(11 - _length):
        for _col in range(10):
            _positions.append(
                sum(
                    1 << (10 * (_row + offset) + _col)
                    for offset in range(_length)
                )
            )
    _PLACEMENTS[_length] = tuple(_positions)

# Optional warm starts. Correctness does not depend on persistent memory.
_MEMORY = (0, 0, [])


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _MEMORY

    clock = time.perf_counter
    started = clock()
    deadline = started + 0.82
    rng = random.Random()

    hits = 0
    misses = 0
    unknown = 0
    legal = []

    for r in range(10):
        for c in range(10):
            index = 10 * r + c
            bit = 1 << index
            value = board[r][c]
            if value == 0:
                legal.append(index)
                unknown |= bit
            elif value == 1:
                hits |= bit
            elif value == -1:
                misses |= bit

    if not legal:
        # A terminal board has no legal action.
        return (0, 0)
    if len(legal) == 1:
        return divmod(legal[0], 10)
    if hits.bit_count() >= 17:
        return divmod(rng.choice(legal), 10)
    if not hits and not misses:
        _MEMORY = (0, 0, [])
        return rng.choice(((4, 4), (4, 5), (5, 4), (5, 5)))

    available = {
        length: tuple(
            p for p in _PLACEMENTS[length] if not (p & misses)
        )
        for length in (2, 3, 4, 5)
    }

    def fallback():
        """Fast, placement-based scoring; always chooses an unknown cell."""
        score = [0.0] * 100
        for length, multiplicity in ((5, 1), (4, 1), (3, 2), (2, 1)):
            positions = available[length]
            scale = multiplicity / max(1, len(positions))
            for p in positions:
                cells = p & unknown
                if not cells:
                    continue
                covered = (p & hits).bit_count()
                weight = scale * (1.0 + 8.0 * covered * covered)
                while cells:
                    bit = cells & -cells
                    score[bit.bit_length() - 1] += weight
                    cells ^= bit
        best = max(legal, key=lambda x: (score[x], rng.random()))
        return divmod(best, 10)

    hit_bits = []
    remaining_bits = hits
    while remaining_bits:
        bit = remaining_bits & -remaining_bits
        hit_bits.append(bit)
        remaining_bits ^= bit

    by_hit = {
        length: {
            bit: tuple(p for p in available[length] if p & bit)
            for bit in hit_bits
        }
        for length in (2, 3, 4, 5)
    }
    cover_cache = {
        length: {0: available[length]} for length in (2, 3, 4, 5)
    }

    def covering(length, required):
        """Placements containing every required hit, before overlap checks."""
        cache = cover_cache[length]
        result = cache.get(required)
        if result is not None:
            return result

        if required.bit_count() > length:
            result = ()
        else:
            pivot = required & -required
            result = tuple(
                p for p in by_hit[length][pivot]
                if (p & required) == required
            )
        cache[required] = result
        return result

    search_deadline = min(started + 0.14, deadline - 0.08)

    def make_seed():
        """Randomized exact-cover search for a consistent complete fleet."""
        fleet = [0] * 5

        def search(remaining, occupied):
            if clock() >= search_deadline:
                raise TimeoutError

            uncovered = hits & ~occupied
            if not remaining:
                return tuple(fleet) if not uncovered else None

            capacity = sum(_LENGTHS[i] for i in remaining)
            if uncovered.bit_count() > capacity:
                return None

            if uncovered:
                best_options = None
                bits = uncovered

                while bits:
                    bit = bits & -bits
                    bits ^= bit
                    options = []
                    seen_lengths = set()

                    for i in remaining:
                        length = _LENGTHS[i]
                        if length in seen_lengths:
                            continue
                        seen_lengths.add(length)

                        for p in by_hit[length][bit]:
                            if p & occupied:
                                continue
                            if (
                                uncovered & ~p
                            ).bit_count() > capacity - length:
                                continue
                            options.append((i, p))

                    if not options:
                        return None
                    if (
                        best_options is None
                        or len(options) < len(best_options)
                    ):
                        best_options = options
                    if len(best_options) == 1:
                        break

                # Combining collinear hits is usually a productive seed,
                # while randomization supplies alternative explanations.
                best_options.sort(
                    key=lambda item: (
                        (item[1] & uncovered).bit_count()
                        + 2.5 * rng.random()
                    ),
                    reverse=True,
                )
                options = best_options
            else:
                best_positions = None
                best_index = None
                seen_lengths = set()

                for i in remaining:
                    length = _LENGTHS[i]
                    if length in seen_lengths:
                        continue
                    seen_lengths.add(length)
                    positions = [
                        p for p in available[length]
                        if not (p & occupied)
                    ]
                    if not positions:
                        return None
                    if (
                        best_positions is None
                        or len(positions) < len(best_positions)
                    ):
                        best_positions = positions
                        best_index = i

                rng.shuffle(best_positions)
                options = [(best_index, p) for p in best_positions]

            for i, p in options:
                fleet[i] = p
                rest = tuple(j for j in remaining if j != i)
                result = search(rest, occupied | p)
                if result is not None:
                    return result
            return None

        return search((0, 1, 2, 3, 4), 0)

    seeds = []
    old_hits, old_misses, old_fleets = _MEMORY
    if not (old_hits & ~hits) and not (old_misses & ~misses):
        seen = set()
        for fleet in old_fleets:
            if fleet in seen:
                continue
            seen.add(fleet)
            occupied = 0
            for p in fleet:
                occupied |= p
            if not (occupied & misses) and (occupied & hits) == hits:
                seeds.append(fleet)
        rng.shuffle(seeds)
        seeds = seeds[:6]

    while len(seeds) < 6 and clock() < search_deadline:
        try:
            seed = make_seed()
        except TimeoutError:
            break
        if seed is None:
            break
        seeds.append(seed)

    if not seeds:
        _MEMORY = (hits, misses, [])
        return fallback()

    # Pair-conditionals are often reused once several ships are pinned down.
    pair_cache = OrderedDict()

    def update_pair(fleet, occupied, i, j):
        first_length = _LENGTHS[i]
        second_length = _LENGTHS[j]
        fixed = occupied ^ fleet[i] ^ fleet[j]
        required = hits & ~fixed

        # This condition depends only on the fixed ships, so skipping this
        # block does not distort the Gibbs stationary distribution.
        if not required:
            return occupied

        key = (first_length, second_length, fixed)
        entry = pair_cache.get(key)

        if entry is None:
            anchor = min(
                (bit for bit in hit_bits if bit & required),
                key=lambda bit: (
                    len(by_hit[first_length][bit])
                    + len(by_hit[second_length][bit])
                ),
            )

            ends = []
            groups = []
            total = 0

            # Exactly one of the two ships covers the anchor. Enumerating
            # both cases counts every legal labeled pair exactly once.
            for orientation in (0, 1):
                if orientation == 0:
                    a_length, b_length = first_length, second_length
                else:
                    a_length, b_length = second_length, first_length

                for a in by_hit[a_length][anchor]:
                    if a & fixed:
                        continue
                    need_b = required & ~a
                    if need_b.bit_count() > b_length:
                        continue
                    blocked = fixed | a
                    choices = tuple(
                        b for b in covering(b_length, need_b)
                        if not (b & blocked)
                    )
                    if choices:
                        total += len(choices)
                        ends.append(total)
                        groups.append((orientation, a, choices))

            if not total:
                return occupied

            entry = (ends, groups)
            pair_cache[key] = entry
            if len(pair_cache) > 128:
                pair_cache.popitem(last=False)
        else:
            pair_cache.move_to_end(key)

        ends, groups = entry
        draw = rng.randrange(ends[-1])
        group_index = bisect_right(ends, draw)
        offset = draw - (ends[group_index - 1] if group_index else 0)
        orientation, a, choices = groups[group_index]
        b = choices[offset]

        if orientation == 0:
            fleet[i], fleet[j] = a, b
        else:
            fleet[i], fleet[j] = b, a
        return fixed | a | b

    chains = [list(fleet) for fleet in seeds]
    occupancies = []
    for fleet in chains:
        occupied = 0
        for p in fleet:
            occupied |= p
        occupancies.append(occupied)

    ages = [0] * len(chains)
    placement_counts = {}
    minimum_length_counts = [0] * 7
    recent = deque(maxlen=90)
    samples = 0
    turn = 0

    while clock() < deadline:
        fleet = chains[turn]
        occupied = occupancies[turn]

        # A full single-ship Gibbs sweep.
        for i, length in enumerate(_LENGTHS):
            old = fleet[i]
            fixed = occupied ^ old
            required = hits & old
            choices = [
                p for p in covering(length, required)
                if not (p & fixed)
            ]
            if choices:
                new = rng.choice(choices)
                fleet[i] = new
                occupied = fixed | new

        # Two-ship updates can change which ship explains an observed hit.
        if hits:
            i, j = rng.choice(_PAIRS)
            occupied = update_pair(fleet, occupied, i, j)

        occupancies[turn] = occupied
        ages[turn] += 1

        if ages[turn] > 24:
            samples += 1
            minimum_length = 6
            for i, p in enumerate(fleet):
                placement_counts[p] = placement_counts.get(p, 0) + 1
                if p & unknown:
                    # Lengths are ordered from largest to smallest.
                    minimum_length = _LENGTHS[i]
            minimum_length_counts[minimum_length] += 1

            if samples % 7 == 0:
                recent.append(tuple(fleet))

        turn += 1
        if turn == len(chains):
            turn = 0

    # Defensive handling if the process was interrupted by unusual scheduling.
    if samples == 0:
        for fleet in chains:
            samples += 1
            minimum_length = 6
            for i, p in enumerate(fleet):
                placement_counts[p] = placement_counts.get(p, 0) + 1
                if p & unknown:
                    minimum_length = _LENGTHS[i]
            minimum_length_counts[minimum_length] += 1

    _MEMORY = (
        hits,
        misses,
        (list(recent) + [tuple(fleet) for fleet in chains])[-96:],
    )

    heat = [0] * 100
    continuation = [0] * 100

    for p, count in placement_counts.items():
        cells = p & unknown
        follows_hit = bool(p & hits)
        while cells:
            bit = cells & -cells
            index = bit.bit_length() - 1
            heat[index] += count
            if follows_hit:
                continuation[index] += count
            cells ^= bit

    # A small continuation preference breaks near-ties in favor of finishing
    # damaged ships without overwhelming the estimated hit probability.
    scores = [
        heat[i] + 0.03 * continuation[i] for i in range(100)
    ]
    best = max(legal, key=lambda i: (scores[i], rng.random()))

    if max(continuation[i] for i in legal) < 0.17 * samples:
        # Hunt on a lattice. Increase its spacing only when the posterior
        # strongly indicates that all shorter ships are already sunk.
        spacing = 2
        for length in (3, 4, 5):
            if sum(minimum_length_counts[length:]) >= 0.97 * samples:
                spacing = length

        lattices = [[] for _ in range(spacing)]
        for index in legal:
            if heat[index] > 0:
                r, c = divmod(index, 10)
                lattices[(r + c) % spacing].append(index)

        candidates = []
        for cells in lattices:
            if not cells:
                continue
            candidate = max(
                cells, key=lambda i: (scores[i], rng.random())
            )
            if scores[candidate] >= 0.90 * scores[best]:
                candidates.append((len(cells), -scores[candidate], candidate))

        if candidates:
            # Prefer a pattern with fewer plausible cells left to search.
            best = min(candidates)[2]

    return divmod(best, 10)
