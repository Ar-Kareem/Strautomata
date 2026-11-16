
import random
import time

_LENGTHS = (5, 4, 3, 2)
_TYPES = (0, 1, 2, 2, 3)
_PAIRS = tuple((i, j) for i in range(5) for j in range(i + 1, 5))
_TRIPLES = tuple(
    (i, j, k)
    for i in range(5)
    for j in range(i + 1, 5)
    for k in range(j + 1, 5)
)
_BYTE_BITS = tuple(
    tuple(i for i in range(8) if x & (1 << i))
    for x in range(256)
)
_GEOMETRY = None
_CACHE = (0, 0, [])


def _geometry():
    global _GEOMETRY
    if _GEOMETRY is not None:
        return _GEOMETRY

    masks, cells, cover, full = [], [], [], []
    for length in _LENGTHS:
        group_cells = []
        for r in range(10):
            for c in range(11 - length):
                group_cells.append(tuple(10 * r + c + k for k in range(length)))
        for r in range(11 - length):
            for c in range(10):
                group_cells.append(tuple(10 * (r + k) + c for k in range(length)))

        group_masks = []
        group_cover = [0] * 100
        for p, occupied in enumerate(group_cells):
            mask = 0
            for cell in occupied:
                mask |= 1 << cell
                group_cover[cell] |= 1 << p
            group_masks.append(mask)

        masks.append(tuple(group_masks))
        cells.append(tuple(group_cells))
        cover.append(tuple(group_cover))
        full.append((1 << len(group_cells)) - 1)

    # conflict[g][p][h] is the bitset of length-h placements
    # that overlap placement p of length g.
    conflict = []
    for g in range(4):
        group_conflict = []
        for occupied in cells[g]:
            row = []
            for h in range(4):
                blocked = 0
                for cell in occupied:
                    blocked |= cover[h][cell]
                row.append(blocked)
            group_conflict.append(tuple(row))
        conflict.append(tuple(group_conflict))

    _GEOMETRY = (
        tuple(masks), tuple(cells), tuple(cover),
        tuple(full), tuple(conflict)
    )
    return _GEOMETRY


def _pick(bits):
    """Uniformly select the index of a set bit."""
    count = bits.bit_count()
    if count == 1:
        return bits.bit_length() - 1

    rank = random.randrange(count)
    if count <= 8:
        for _ in range(rank):
            bits &= bits - 1
        return (bits & -bits).bit_length() - 1

    offset = 0
    while bits.bit_length() > 8:
        split = bits.bit_length() // 2
        low = bits & ((1 << split) - 1)
        nlow = low.bit_count()
        if rank < nlow:
            bits = low
        else:
            rank -= nlow
            bits >>= split
            offset += split
    return offset + _BYTE_BITS[bits][rank]


def policy(board: list[list[int]]) -> tuple[int, int]:
    global _CACHE

    started = time.perf_counter()
    deadline = started + 0.82

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

    # A finished board has no legal action; normal game calls have an unknown.
    if not unknown:
        return (0, 0)
    if len(unknown) == 1:
        return divmod(unknown[0], 10)
    if not hits and not misses:
        return (4, 4)

    masks, cells, cover, full, conflict = _geometry()
    unknown_mask = 0
    for cell in unknown:
        unknown_mask |= 1 << cell

    legal = list(full)
    remaining_misses = misses
    while remaining_misses:
        bit = remaining_misses & -remaining_misses
        remaining_misses -= bit
        cell = bit.bit_length() - 1
        for g in range(4):
            legal[g] &= ~cover[g][cell]
    legal = tuple(legal)

    requirement_cache = [{0: full[g]} for g in range(4)]

    def containing(g, required):
        cache = requirement_cache[g]
        answer = cache.get(required)
        if answer is not None:
            return answer
        if required.bit_count() > _LENGTHS[g]:
            cache[required] = 0
            return 0
        answer = full[g]
        rest = required
        while rest and answer:
            bit = rest & -rest
            rest -= bit
            answer &= cover[g][bit.bit_length() - 1]
        cache[required] = answer
        return answer

    def fallback():
        # Used only if constructing a consistent fleet exceeds its budget.
        scores = [0.0] * 100
        for g in range(4):
            domain = legal[g]
            base = (2.0 if g == 2 else 1.0) / max(1, domain.bit_count())
            while domain:
                bit = domain & -domain
                domain -= bit
                p = bit.bit_length() - 1
                mask = masks[g][p]
                unseen = (mask & unknown_mask).bit_count()
                if not unseen:
                    continue
                nhit = (mask & hits).bit_count()
                weight = base
                if nhit:
                    weight *= 1.0 + 12.0 * nhit * nhit / unseen
                for cell in cells[g][p]:
                    if unknown_mask & (1 << cell):
                        scores[cell] += weight
        best = max(
            unknown,
            key=lambda x: scores[x] + 1e-10 * random.random()
        )
        return divmod(best, 10)

    def find_fleet(stop):
        answer = [-1] * 5
        nodes = 0

        def visit(remaining, domains, uncovered):
            nonlocal nodes
            nodes += 1
            if nodes == 1 or not (nodes & 31):
                if time.perf_counter() >= stop or nodes > 20000:
                    return None

            if not remaining:
                return tuple(answer) if not uncovered else None

            capacity = sum(_LENGTHS[_TYPES[i]] for i in remaining)
            if uncovered.bit_count() > capacity:
                return None

            representatives = []
            seen = set()
            for i in remaining:
                g = _TYPES[i]
                if not domains[g]:
                    return None
                if g not in seen:
                    seen.add(g)
                    representatives.append(i)

            if uncovered:
                # Branch on the hardest-to-cover observed hit.
                pivot = -1
                best_count = 10**9
                rest = uncovered
                while rest:
                    bit = rest & -rest
                    rest -= bit
                    cell = bit.bit_length() - 1
                    count = sum(
                        (domains[_TYPES[i]] & cover[_TYPES[i]][cell]).bit_count()
                        for i in representatives
                    )
                    if count == 0:
                        return None
                    if count < best_count:
                        best_count = count
                        pivot = cell

                options = []
                for i in representatives:
                    g = _TYPES[i]
                    domain = domains[g] & cover[g][pivot]
                    while domain:
                        bit = domain & -domain
                        domain -= bit
                        options.append((i, bit.bit_length() - 1))
                random.shuffle(options)
                options.sort(
                    key=lambda option: (
                        masks[_TYPES[option[0]]][option[1]] & uncovered
                    ).bit_count(),
                    reverse=True
                )
            else:
                i = min(
                    representatives,
                    key=lambda index: domains[_TYPES[index]].bit_count()
                )
                domain = domains[_TYPES[i]]
                options = []
                while domain:
                    bit = domain & -domain
                    domain -= bit
                    options.append((i, bit.bit_length() - 1))
                random.shuffle(options)

            for i, p in options:
                g = _TYPES[i]
                new_domains = tuple(
                    domains[h] & ~conflict[g][p][h] for h in range(4)
                )
                answer[i] = p
                result = visit(
                    tuple(j for j in remaining if j != i),
                    new_domains,
                    uncovered & ~masks[g][p]
                )
                if result is not None:
                    return result
                if not (nodes & 31) and time.perf_counter() >= stop:
                    return None
            return None

        return visit(tuple(range(5)), legal, hits)

    # Reuse particles only when all their previous observations still apply.
    old_hits, old_misses, old_particles = _CACHE
    seeds = []
    if not (old_hits & ~hits) and not (old_misses & ~misses):
        for fleet in old_particles:
            occupied = 0
            for i, p in enumerate(fleet):
                occupied |= masks[_TYPES[i]][p]
            if not (occupied & misses) and not (hits & ~occupied):
                seeds.append(fleet)

    if seeds:
        first = random.choice(seeds)
    else:
        first = find_fleet(min(deadline, started + 0.20))
        if first is None:
            return fallback()

    def update(fleet, selected, stop):
        """Exact conditional resampling of two or three labeled ships."""
        domains = list(legal)
        required = hits
        for i, p in enumerate(fleet):
            if i not in selected:
                g = _TYPES[i]
                required &= ~masks[g][p]
                blocked = conflict[g][p]
                for h in range(4):
                    domains[h] &= ~blocked[h]

        ordered = sorted(
            selected, key=lambda i: domains[_TYPES[i]].bit_count()
        )
        groups = [_TYPES[i] for i in ordered]
        ds = [domains[g] for g in groups]
        if any(not d for d in ds):
            return

        # With no required hits, independent rejection sampling is fast
        # and gives exactly the same conditional distribution.
        if not required:
            for _ in range(16):
                occupied = 0
                chosen = []
                for g, domain in zip(groups, ds):
                    p = _pick(domain)
                    mask = masks[g][p]
                    if mask & occupied:
                        break
                    occupied |= mask
                    chosen.append(p)
                if len(chosen) == len(ordered):
                    for i, p in zip(ordered, chosen):
                        fleet[i] = p
                    return

        count_ships = len(ordered)
        a = groups[0]
        z = groups[-1]
        da = ds[0]
        dz = ds[-1]

        # Hits that no later ship can cover must belong to the first ship.
        rest = required
        while rest:
            bit = rest & -rest
            rest -= bit
            cell = bit.bit_length() - 1
            if not any(
                ds[k] & cover[groups[k]][cell]
                for k in range(1, count_ships)
            ):
                da &= cover[a][cell]

        rows = []
        total = 0
        while da:
            abit = da & -da
            da -= abit
            pa = abit.bit_length() - 1
            need = required & ~masks[a][pa]
            last_domain = dz & ~conflict[a][pa][z]

            if count_ships == 2:
                options = last_domain & containing(z, need)
                n = options.bit_count()
                if n:
                    total += n
                    rows.append((pa, -1, options, total))
            else:
                if time.perf_counter() >= stop:
                    return
                b = groups[1]
                if need.bit_count() > _LENGTHS[b] + _LENGTHS[z]:
                    continue
                db = ds[1] & ~conflict[a][pa][b]
                rest = need
                while rest and db:
                    bit = rest & -rest
                    rest -= bit
                    cell = bit.bit_length() - 1
                    if not (last_domain & cover[z][cell]):
                        db &= cover[b][cell]

                while db:
                    bbit = db & -db
                    db -= bbit
                    pb = bbit.bit_length() - 1
                    options = (
                        last_domain
                        & ~conflict[b][pb][z]
                        & containing(z, need & ~masks[b][pb])
                    )
                    n = options.bit_count()
                    if n:
                        total += n
                        rows.append((pa, pb, options, total))

        if not total:
            return
        ticket = random.randrange(total)
        for pa, pb, options, cumulative in rows:
            if ticket < cumulative:
                fleet[ordered[0]] = pa
                if count_ships == 3:
                    fleet[ordered[1]] = pb
                fleet[ordered[-1]] = _pick(options)
                return

    placement_counts = [[0] * len(group) for group in masks]
    sample_count = 0
    particles = []
    particle_counter = 0
    hit_count = hits.bit_count()
    chains = 5

    for chain in range(chains):
        now = time.perf_counter()
        if now >= deadline:
            break

        if chain == 0:
            seed = first
        elif seeds and random.random() < 0.65:
            seed = random.choice(seeds)
        else:
            seed = find_fleet(min(deadline, now + 0.025))
            if seed is None:
                seed = random.choice(seeds) if seeds else first

        fleet = list(seed)
        now = time.perf_counter()
        chain_end = now + max(0.0, deadline - now) / (chains - chain)
        step = 0
        triple_period = 48 if hit_count >= 10 else 96

        while time.perf_counter() < chain_end:
            if hit_count >= 5 and step % triple_period == triple_period - 1:
                update(fleet, random.choice(_TRIPLES), chain_end)
            else:
                update(fleet, random.choice(_PAIRS), chain_end)

            step += 1
            if step > 32 and not (step & 1):
                sample_count += 1
                for i, p in enumerate(fleet):
                    placement_counts[_TYPES[i]][p] += 1

                if not (step & 31):
                    particle = tuple(fleet)
                    if len(particles) < 192:
                        particles.append(particle)
                    else:
                        particles[particle_counter % 192] = particle
                    particle_counter += 1

    if not sample_count:
        sample_count = 1
        for i, p in enumerate(first):
            placement_counts[_TYPES[i]][p] += 1

    _CACHE = (hits, misses, particles or [first])

    heat = [0.0] * 100
    target_heat = [0.0] * 100
    active = [0.0] * 4

    for g in range(4):
        for p, count in enumerate(placement_counts[g]):
            if not count:
                continue
            mask = masks[g][p]
            if not (mask & unknown_mask):
                continue
            active[g] += count
            is_target = bool(mask & hits)
            for cell in cells[g][p]:
                if unknown_mask & (1 << cell):
                    heat[cell] += count
                    if is_target:
                        target_heat[cell] += count

    minimum_length = 2
    for g in reversed(range(4)):
        if active[g] > 0.20 * sample_count:
            minimum_length = _LENGTHS[g]
            break

    # A mild lattice preference helps locate untouched ships without
    # overriding strong evidence around an existing hit.
    bonus = 0.035 if max(target_heat) > 0.20 * sample_count else 0.075
    best_cell = unknown[0]
    best_score = -1.0
    for cell in unknown:
        r, c = divmod(cell, 10)
        score = heat[cell]
        if (r + c) % minimum_length == 0:
            score += bonus * max(0.0, heat[cell] - target_heat[cell])
        score += 1e-7 * random.random()
        if score > best_score:
            best_score = score
            best_cell = cell

    return divmod(best_cell, 10)
