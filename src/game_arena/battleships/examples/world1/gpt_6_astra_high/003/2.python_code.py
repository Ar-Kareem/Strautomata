
import random
import time


_LENGTHS = (5, 4, 3, 2)
_FLEET = (5, 4, 3, 3, 2)
_MULTIPLICITY = {5: 1, 4: 1, 3: 2, 2: 1}


def _make_geometry():
    result = {}
    for length in _LENGTHS:
        placements = []
        for r in range(10):
            for c in range(11 - length):
                mask = 0
                for k in range(length):
                    mask |= 1 << (10 * r + c + k)
                placements.append(mask)
        for r in range(11 - length):
            for c in range(10):
                mask = 0
                for k in range(length):
                    mask |= 1 << (10 * (r + k) + c)
                placements.append(mask)
        result[length] = tuple(placements)
    return result


_GEOMETRY = _make_geometry()


class _SearchTimeout(Exception):
    pass


def policy(board: list[list[int]]) -> tuple[int, int]:
    start = time.perf_counter()
    deadline = start + 0.80
    rng = random.Random()

    hits = 0
    misses = 0
    unknown_mask = 0
    unknown = []

    for r in range(10):
        for c in range(10):
            index = 10 * r + c
            bit = 1 << index
            value = board[r][c]
            if value == 0:
                unknown.append(index)
                unknown_mask |= bit
            elif value == 1:
                hits |= bit
            else:
                misses |= bit

    # A terminal board has no legal action; normal games never request one.
    if not unknown:
        return (0, 0)
    if len(unknown) == 1:
        return divmod(unknown[0], 10)

    if not hits and not misses:
        return rng.choice(((4, 4), (4, 5), (5, 4), (5, 5)))

    placements = {
        length: tuple(m for m in _GEOMETRY[length] if not (m & misses))
        for length in _LENGTHS
    }

    hit_bits = []
    remaining = hits
    while remaining:
        bit = remaining & -remaining
        hit_bits.append(bit)
        remaining ^= bit

    containing = {
        length: {
            bit: tuple(m for m in placements[length] if m & bit)
            for bit in hit_bits
        }
        for length in _LENGTHS
    }
    cover_cache = {length: {0: placements[length]} for length in _LENGTHS}

    def covering(length, required):
        cache = cover_cache[length]
        cached = cache.get(required)
        if cached is not None:
            return cached
        if required.bit_count() > length:
            result = ()
        else:
            anchor = required & -required
            result = tuple(
                m for m in containing[length].get(anchor, ())
                if (m & required) == required
            )
        cache[required] = result
        return result

    def choose_from_scores(scores):
        best = max(scores[i] for i in unknown)
        tolerance = max(1.0, abs(best)) * 1e-11
        candidates = [
            i for i in unknown if scores[i] >= best - tolerance
        ]
        return divmod(rng.choice(candidates), 10)

    def fallback():
        scores = [0.0] * 100
        for length in _LENGTHS:
            options = placements[length]
            scale = _MULTIPLICITY[length] / max(1, len(options))
            for mask in options:
                hit_count = (mask & hits).bit_count()
                weight = scale * (1.0 + 8.0 * hit_count * hit_count)
                cells = mask & unknown_mask
                while cells:
                    bit = cells & -cells
                    scores[bit.bit_length() - 1] += weight
                    cells ^= bit
        return choose_from_scores(scores)

    def search_fleets(first_only, limit):
        """
        Exact-cover search over observed hits. Identical ships are not
        distinguished, so each physical fleet is counted once.
        """
        counts = dict(_MULTIPLICITY)
        chosen = []
        seeds = []
        scores = [0] * 100
        configurations = 0
        nodes = 0

        def check_time():
            nonlocal nodes
            nodes += 1
            if nodes % 64 == 1 and time.perf_counter() >= limit:
                raise _SearchTimeout

        def record(occupied):
            nonlocal configurations
            configurations += 1

            if first_only:
                seeds.append(chosen.copy())
                return True

            cells = occupied & unknown_mask
            while cells:
                bit = cells & -cells
                scores[bit.bit_length() - 1] += 1
                cells ^= bit

            if len(seeds) < 4:
                seeds.append(chosen.copy())
            else:
                j = rng.randrange(configurations)
                if j < 4:
                    seeds[j] = chosen.copy()
            return False

        def fill_empty(todo, depth, occupied, previous):
            check_time()
            if depth == len(todo):
                return record(occupied)

            length = todo[depth]
            options = [
                m for m in placements[length]
                if not (m & occupied)
                and not (
                    depth > 0
                    and todo[depth - 1] == length
                    and m <= previous
                )
            ]
            if first_only:
                rng.shuffle(options)

            for mask in options:
                chosen.append((length, mask))
                found = fill_empty(
                    todo, depth + 1, occupied | mask, mask
                )
                chosen.pop()
                if found:
                    return True
            return False

        def visit(required, occupied, capacity):
            check_time()

            if not required:
                todo = [
                    length
                    for length in _LENGTHS
                    for _ in range(counts[length])
                ]
                return fill_empty(todo, 0, occupied, -1)

            hit_count = required.bit_count()
            if hit_count > capacity:
                return False
            slack = capacity - hit_count

            # Branch on the uncovered hit with the fewest legal explanations.
            best_options = None
            bits = required
            while bits:
                bit = bits & -bits
                bits ^= bit
                options = []

                for length in _LENGTHS:
                    if not counts[length]:
                        continue
                    minimum_hits = length - slack
                    for mask in containing[length][bit]:
                        if mask & occupied:
                            continue
                        if (
                            minimum_hits > 1
                            and (mask & required).bit_count() < minimum_hits
                        ):
                            continue
                        options.append((length, mask))

                if not options:
                    return False
                if best_options is None or len(options) < len(best_options):
                    best_options = options
                    if len(options) == 1:
                        break

            # Find plausible complete fleets quickly, while allowing
            # different interpretations of touching ships.
            best_options.sort(
                key=lambda item:
                    (item[1] & required).bit_count() + 2.5 * rng.random(),
                reverse=True,
            )

            for length, mask in best_options:
                counts[length] -= 1
                chosen.append((length, mask))
                found = visit(
                    required & ~mask,
                    occupied | mask,
                    capacity - length,
                )
                chosen.pop()
                counts[length] += 1
                if found:
                    return True
            return False

        complete = True
        try:
            visit(hits, 0, 17)
        except _SearchTimeout:
            complete = False

        return complete, configurations, scores, seeds

    seeds = []

    # With thirteen hits, at most one entire ship can remain undiscovered.
    # Exact enumeration is often very inexpensive in this regime.
    if hits.bit_count() >= 13:
        complete, count, scores, seeds = search_fleets(
            False, min(start + 0.23, deadline - 0.35)
        )
        if complete and count:
            return choose_from_scores(scores)

    init_limit = min(deadline - 0.25, time.perf_counter() + 0.12)
    while len(seeds) < 4 and time.perf_counter() < init_limit:
        _, _, _, new_seeds = search_fleets(True, init_limit)
        if not new_seeds:
            break
        seeds.extend(new_seeds)

    if not seeds and time.perf_counter() < deadline - 0.05:
        _, _, _, seeds = search_fleets(True, deadline - 0.05)

    if not seeds:
        return fallback()

    chains = []
    for seed in seeds[:4]:
        buckets = {length: [] for length in _LENGTHS}
        for length, mask in seed:
            buckets[length].append(mask)
        fleet = [buckets[length].pop() for length in _FLEET]
        occupied = 0
        for mask in fleet:
            occupied |= mask
        chains.append([fleet, occupied, 0])

    mass = {
        length: {mask: 0.0 for mask in placements[length]}
        for length in _LENGTHS
    }

    def block_options(length, occupied, required, capacity_after):
        if capacity_after == 0:
            return [
                m for m in covering(length, required)
                if not (m & occupied)
            ]
        if required.bit_count() <= capacity_after:
            return [
                m for m in placements[length]
                if not (m & occupied)
            ]
        return [
            m for m in placements[length]
            if not (m & occupied)
            and (required & ~m).bit_count() <= capacity_after
        ]

    def block_update(fleet, occupied, triple):
        """
        Independence Metropolis-Hastings update of two or three ships.
        Proposal-count correction preserves the uniform fleet posterior.
        """
        if triple:
            indices = rng.sample(range(5), 3)
        elif hit_bits:
            anchor = rng.choice(hit_bits)
            first = next(i for i in range(5) if fleet[i] & anchor)
            second = rng.randrange(4)
            if second >= first:
                second += 1
            indices = [first, second]
            if rng.getrandbits(1):
                indices.reverse()
            # Pair-selection probability depends only on the total hits
            # owned by the pair, which this update leaves unchanged.
        else:
            indices = rng.sample(range(5), 2)

        fixed = occupied
        old = []
        lengths = []
        for i in indices:
            fixed ^= fleet[i]
            old.append(fleet[i])
            lengths.append(_FLEET[i])

        required = hits & ~fixed
        new = []
        blocked = fixed
        need = required
        capacity = sum(lengths)
        forward_product = 1

        for j, length in enumerate(lengths):
            capacity -= length
            options = block_options(length, blocked, need, capacity)
            if not options:
                return occupied
            if j:
                forward_product *= len(options)
            mask = rng.choice(options)
            new.append(mask)
            blocked |= mask
            need &= ~mask

        # The first proposal domain is identical in both directions.
        reverse_product = 1
        blocked_old = fixed | old[0]
        need_old = required & ~old[0]
        capacity = sum(lengths[1:])

        for j in range(1, len(indices)):
            length = lengths[j]
            capacity -= length
            options = block_options(
                length, blocked_old, need_old, capacity
            )
            reverse_product *= len(options)
            blocked_old |= old[j]
            need_old &= ~old[j]

        if (
            forward_product >= reverse_product
            or rng.random() * reverse_product < forward_product
        ):
            for i, mask in zip(indices, new):
                fleet[i] = mask
            return blocked
        return occupied

    sample_sweeps = 0
    chain_index = 0
    order = list(range(5))

    while time.perf_counter() < deadline:
        chain = chains[chain_index]
        fleet, occupied, steps = chain

        for _ in range(12):
            if time.perf_counter() >= deadline:
                break

            occupied = block_update(
                fleet, occupied, triple=(steps % 12 == 11)
            )
            collect = steps >= 20
            rng.shuffle(order)

            for i in order:
                length = _FLEET[i]
                others = occupied ^ fleet[i]
                required = hits & ~others
                options = [
                    m for m in covering(length, required)
                    if not (m & others)
                ]

                # The current placement always belongs to this set.
                if not options:
                    continue

                if collect:
                    weight = 1.0 / len(options)
                    table = mass[length]
                    for mask in options:
                        table[mask] += weight

                fleet[i] = rng.choice(options)
                occupied = others | fleet[i]

            if collect:
                sample_sweeps += 1
            steps += 1

        chain[1] = occupied
        chain[2] = steps
        chain_index = (chain_index + 1) % len(chains)

    if not sample_sweeps:
        return fallback()

    scores = [0.0] * 100
    for length in _LENGTHS:
        for mask, weight in mass[length].items():
            if not weight:
                continue
            cells = mask & unknown_mask
            while cells:
                bit = cells & -cells
                scores[bit.bit_length() - 1] += weight
                cells ^= bit

    return choose_from_scores(scores)
