import random
import time


_SHIPS = (5, 4, 3, 3, 2)


def _generate_placements():
    result = {}
    for length in set(_SHIPS):
        masks = []

        for row in range(10):
            for col in range(11 - length):
                mask = 0
                for offset in range(length):
                    mask |= 1 << (row * 10 + col + offset)
                masks.append(mask)

        for row in range(11 - length):
            for col in range(10):
                mask = 0
                for offset in range(length):
                    mask |= 1 << ((row + offset) * 10 + col)
                masks.append(mask)

        result[length] = tuple(masks)

    return result


_ALL_PLACEMENTS = _generate_placements()


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Return an unfired cell with high posterior probability of containing
    an opponent ship.
    """
    start_time = time.perf_counter()
    deadline = start_time + 0.72

    hit_mask = 0
    miss_mask = 0
    unknown_mask = 0
    unknown_cells = []

    seed = 1469598103934665603
    for row in range(10):
        for col in range(10):
            value = board[row][col]
            index = row * 10 + col
            bit = 1 << index

            if value == 0:
                unknown_mask |= bit
                unknown_cells.append(index)
            elif value == 1:
                hit_mask |= bit
            else:
                miss_mask |= bit

            seed ^= value + 2
            seed = (seed * 1099511628211) & ((1 << 64) - 1)

    # A terminal board has no legal action. Normally policy is never called
    # in that state.
    if not unknown_cells:
        return (0, 0)

    rng = random.Random(seed)

    # Remove every placement contradicted by a known miss.
    placements = {
        length: [
            mask for mask in _ALL_PLACEMENTS[length]
            if not (mask & miss_mask)
        ]
        for length in set(_SHIPS)
    }

    # Index placements by the cells they contain, used by the initial CSP.
    by_cell = {}
    for length, pool in placements.items():
        indexed = [[] for _ in range(100)]
        for mask in pool:
            cells = mask
            while cells:
                bit = cells & -cells
                indexed[bit.bit_length() - 1].append(mask)
                cells -= bit
        by_cell[length] = indexed

    # Independent-placement score. This is useful both as a fallback and as
    # a very small amount of smoothing for Monte Carlo estimates.
    tactical_score = [0] * 100
    for length in _SHIPS:
        for mask in placements[length]:
            known_hits = (mask & hit_mask).bit_count()
            weight = 1 << (2 * min(known_hits, 5))
            cells = mask & unknown_mask
            while cells:
                bit = cells & -cells
                tactical_score[bit.bit_length() - 1] += weight
                cells -= bit

    assignment = [0] * len(_SHIPS)

    def find_configuration(node_limit):
        """Find one complete fleet consistent with every observation."""
        nodes = 0

        def search(remaining, occupied, uncovered_hits):
            nonlocal nodes
            nodes += 1

            if nodes > node_limit:
                return None
            if (nodes & 127) == 0 and time.perf_counter() >= deadline:
                return None

            if not remaining:
                if uncovered_hits == 0:
                    return assignment.copy()
                return None

            if uncovered_hits:
                # Choose the uncovered hit having the fewest possible
                # covering placements (minimum-remaining-values heuristic).
                best_options = None
                pending = uncovered_hits

                while pending:
                    hit_bit = pending & -pending
                    cell = hit_bit.bit_length() - 1
                    options = []
                    seen_lengths = set()

                    for ship_index in remaining:
                        length = _SHIPS[ship_index]
                        if length in seen_lengths:
                            continue
                        seen_lengths.add(length)

                        for mask in by_cell[length][cell]:
                            if not (mask & occupied):
                                options.append((ship_index, mask))

                    if not options:
                        return None

                    if best_options is None or len(options) < len(best_options):
                        best_options = options
                    pending -= hit_bit

                rng.shuffle(best_options)

                for ship_index, mask in best_options:
                    assignment[ship_index] = mask
                    next_remaining = tuple(
                        index for index in remaining if index != ship_index
                    )
                    result = search(
                        next_remaining,
                        occupied | mask,
                        uncovered_hits & ~mask,
                    )
                    if result is not None:
                        return result
                    assignment[ship_index] = 0

                return None

            # All hits are covered. Place the remaining ships without overlap.
            # Pick the ship with the fewest currently available placements.
            selected_index = None
            selected_options = None
            seen_lengths = set()

            for ship_index in remaining:
                length = _SHIPS[ship_index]
                if length in seen_lengths:
                    continue
                seen_lengths.add(length)

                options = [
                    mask for mask in placements[length]
                    if not (mask & occupied)
                ]
                if not options:
                    return None

                if selected_options is None or len(options) < len(selected_options):
                    selected_index = ship_index
                    selected_options = options

            rng.shuffle(selected_options)
            next_remaining = tuple(
                index for index in remaining if index != selected_index
            )

            for mask in selected_options:
                assignment[selected_index] = mask
                result = search(
                    next_remaining,
                    occupied | mask,
                    uncovered_hits,
                )
                if result is not None:
                    return result
                assignment[selected_index] = 0

            return None

        return search(tuple(range(len(_SHIPS))), 0, hit_mask)

    fleet = find_configuration(60000)

    # If a configuration cannot be found within the budget, use the
    # deterministic tactical placement-density fallback.
    if fleet is None:
        def fallback_key(index):
            row, col = divmod(index, 10)
            adjacent_hits = 0
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = row + dr, col + dc
                if 0 <= nr < 10 and 0 <= nc < 10:
                    if board[nr][nc] == 1:
                        adjacent_hits += 1

            center_distance = abs(2 * row - 9) + abs(2 * col - 9)
            return (
                tactical_score[index],
                adjacent_hits,
                int((row + col) % 2 == 0),
                -center_distance,
                -index,
            )

        choice = max(unknown_cells, key=fallback_key)
        return divmod(choice, 10)

    counts = [0] * 100
    samples = 0
    updates = 0
    burn_in = 80

    # Gibbs sampling: with the other four ships fixed, uniformly reposition
    # one ship among every placement that still covers all required hits.
    while True:
        if (updates & 63) == 0 and time.perf_counter() >= deadline:
            break

        # Periodic randomized restarts help reach modes that single-ship
        # Gibbs moves cannot cross, especially when ships touch.
        if updates and updates % 6000 == 0:
            new_fleet = find_configuration(14000)
            if new_fleet is not None:
                fleet = new_fleet
                burn_in = 40

        ship_index = rng.randrange(len(_SHIPS))
        other_ships = 0
        for index, mask in enumerate(fleet):
            if index != ship_index:
                other_ships |= mask

        required_hits = hit_mask & ~other_ships
        candidates = []

        for mask in placements[_SHIPS[ship_index]]:
            if mask & other_ships:
                continue
            if required_hits & ~mask:
                continue
            candidates.append(mask)

        # The current placement is always a candidate for a valid fleet.
        if candidates:
            fleet[ship_index] = candidates[rng.randrange(len(candidates))]

        updates += 1

        if burn_in:
            burn_in -= 1
            continue

        occupied = 0
        for mask in fleet:
            occupied |= mask

        cells = occupied & unknown_mask
        while cells:
            bit = cells & -cells
            counts[bit.bit_length() - 1] += 1
            cells -= bit
        samples += 1

    if samples == 0:
        choice = max(
            unknown_cells,
            key=lambda index: (
                tactical_score[index],
                -abs(2 * (index // 10) - 9) - abs(2 * (index % 10) - 9),
                -index,
            ),
        )
        return divmod(choice, 10)

    maximum_tactical = max(
        tactical_score[index] for index in unknown_cells
    ) or 1

    def final_key(index):
        row, col = divmod(index, 10)
        posterior = counts[index] / samples

        # Very small smoothing stabilizes nearly tied Monte Carlo estimates.
        smoothed = posterior + (
            0.001 * tactical_score[index] / maximum_tactical
        )
        center_distance = abs(2 * row - 9) + abs(2 * col - 9)

        return (
            smoothed,
            tactical_score[index],
            int((row + col) % 2 == 0),
            -center_distance,
            -index,
        )

    choice = max(unknown_cells, key=final_key)
    return divmod(choice, 10)
