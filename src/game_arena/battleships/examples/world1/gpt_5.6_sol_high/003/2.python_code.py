
import random
import time


# Precompute every horizontal and vertical placement for each ship length.
_SHIP_LENGTHS = (5, 4, 3, 3, 2)
_UNIQUE_LENGTHS = (5, 4, 3, 2)
_ALL_PLACEMENTS = {}
_PLACEMENT_CELLS = {}

for _length in _UNIQUE_LENGTHS:
    _placements = []

    for _row in range(10):
        for _col in range(11 - _length):
            _cells = tuple(_row * 10 + _col + k for k in range(_length))
            _mask = 0
            for _cell in _cells:
                _mask |= 1 << _cell
            _placements.append(_mask)
            _PLACEMENT_CELLS[_mask] = _cells

    for _row in range(11 - _length):
        for _col in range(10):
            _cells = tuple((_row + k) * 10 + _col for k in range(_length))
            _mask = 0
            for _cell in _cells:
                _mask |= 1 << _cell
            _placements.append(_mask)
            _PLACEMENT_CELLS[_mask] = _cells

    _ALL_PLACEMENTS[_length] = tuple(_placements)


def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.perf_counter()
    deadline = start_time + 0.68

    miss_mask = 0
    hit_mask = 0
    unknown_mask = 0
    unknown_cells = []

    seed = 0x9E3779B97F4A7C15

    for row in range(10):
        for col in range(10):
            value = board[row][col]
            cell = row * 10 + col
            bit = 1 << cell

            if value == 0:
                unknown_mask |= bit
                unknown_cells.append(cell)
                code = 0
            elif value == -1:
                miss_mask |= bit
                code = 1
            else:
                hit_mask |= bit
                code = 2

            seed ^= (cell + 1) * (code + 0xBF58476D1CE4E5B9)
            seed = ((seed << 13) | (seed >> 51)) & ((1 << 64) - 1)
            seed = (seed * 0x94D049BB133111EB) & ((1 << 64) - 1)

    # A normal game never requests a move after all 100 cells were fired upon.
    if not unknown_cells:
        return (0, 0)

    rng = random.Random(seed)

    # Placements that do not contradict known misses.
    valid_by_length = {
        length: [
            mask for mask in _ALL_PLACEMENTS[length]
            if not (mask & miss_mask)
        ]
        for length in _UNIQUE_LENGTHS
    }

    # Placements indexed by the cells they contain, used by the constraint solver.
    valid_by_cell = {
        length: [[] for _ in range(100)]
        for length in _UNIQUE_LENGTHS
    }

    for length in _UNIQUE_LENGTHS:
        indexed = valid_by_cell[length]
        for mask in valid_by_length[length]:
            for cell in _PLACEMENT_CELLS[mask]:
                indexed[cell].append(mask)

    sample_counts = [0] * 100
    sample_total = 0

    def make_valid_fleet():
        """Find a randomized complete fleet consistent with hits and misses."""
        state = [0] * 5
        node_count = 0

        def solve(remaining, occupied, uncovered_hits):
            nonlocal node_count
            node_count += 1

            if node_count > 5000:
                return False
            if (node_count & 255) == 0 and time.perf_counter() >= deadline:
                return False

            if not remaining:
                return uncovered_hits == 0

            if uncovered_hits:
                # Pick the uncovered hit with the fewest legal covering options.
                best_options = None
                bits = uncovered_hits

                while bits:
                    low = bits & -bits
                    cell = low.bit_length() - 1
                    options = []

                    for ship_index in remaining:
                        length = _SHIP_LENGTHS[ship_index]
                        for mask in valid_by_cell[length][cell]:
                            if not (mask & occupied):
                                options.append((ship_index, mask))

                    if not options:
                        return False

                    if best_options is None or len(options) < len(best_options):
                        best_options = options

                    bits ^= low

                options = best_options
            else:
                # Once all hits are covered, place larger remaining ships first.
                ship_index = max(
                    remaining,
                    key=lambda index: _SHIP_LENGTHS[index]
                )
                options = [
                    (ship_index, mask)
                    for mask in valid_by_length[_SHIP_LENGTHS[ship_index]]
                    if not (mask & occupied)
                ]

                if not options:
                    return False

            rng.shuffle(options)

            for ship_index, mask in options:
                new_remaining = tuple(
                    index for index in remaining if index != ship_index
                )
                new_uncovered = uncovered_hits & ~mask

                remaining_capacity = sum(
                    _SHIP_LENGTHS[index] for index in new_remaining
                )
                if new_uncovered.bit_count() > remaining_capacity:
                    continue

                state[ship_index] = mask

                if solve(
                    new_remaining,
                    occupied | mask,
                    new_uncovered
                ):
                    return True

                state[ship_index] = 0

            return False

        if solve((0, 1, 2, 3, 4), 0, hit_mask):
            return state
        return None

    def single_ship_update(state, ship_index):
        """Exact one-ship Gibbs update conditioned on the other four ships."""
        other = 0
        for index, mask in enumerate(state):
            if index != ship_index:
                other |= mask

        # Hits not covered by another ship must remain on this ship.
        required = hit_mask & ~other
        length = _SHIP_LENGTHS[ship_index]

        choices = [
            mask for mask in valid_by_length[length]
            if not (mask & other) and (mask & required) == required
        ]

        if choices:
            state[ship_index] = choices[rng.randrange(len(choices))]

    def two_ship_update(state):
        """
        Block Gibbs update for two ships. Unlike single-ship updates, this can
        transfer responsibility for a hit from one ship to another.
        """
        first = rng.randrange(5)
        second = rng.randrange(4)
        if second >= first:
            second += 1

        other = 0
        for index, mask in enumerate(state):
            if index != first and index != second:
                other |= mask

        required = hit_mask & ~other
        first_choices = valid_by_length[_SHIP_LENGTHS[first]]
        second_choices = valid_by_length[_SHIP_LENGTHS[second]]

        total_pairs = 0
        chosen_first = state[first]
        chosen_second = state[second]

        for first_mask in first_choices:
            if first_mask & other:
                continue

            remaining_required = required & ~first_mask
            blocked = other | first_mask

            legal_seconds = [
                second_mask for second_mask in second_choices
                if not (second_mask & blocked)
                and (second_mask & remaining_required) == remaining_required
            ]

            count = len(legal_seconds)
            if count == 0:
                continue

            # Weighted reservoir sampling selects uniformly among all pairs.
            if rng.randrange(total_pairs + count) < count:
                chosen_first = first_mask
                chosen_second = legal_seconds[rng.randrange(count)]

            total_pairs += count

        if total_pairs:
            state[first] = chosen_first
            state[second] = chosen_second

    # Sample consistent fleets. Restarts diversify the initial assignment of
    # hits, while Gibbs updates reduce bias within and between assignments.
    target_samples = 1400

    while sample_total < target_samples and time.perf_counter() < deadline:
        state = make_valid_fleet()
        if state is None:
            if time.perf_counter() >= deadline:
                break
            continue

        # Short burn-in.
        for _ in range(8):
            single_ship_update(state, rng.randrange(5))
        if time.perf_counter() < deadline:
            two_ship_update(state)

        chain_samples = 0

        while (
            chain_samples < 36
            and sample_total < target_samples
            and time.perf_counter() < deadline
        ):
            order = [0, 1, 2, 3, 4]
            rng.shuffle(order)
            for ship_index in order:
                single_ship_update(state, ship_index)

            if chain_samples % 8 == 7 and time.perf_counter() < deadline:
                two_ship_update(state)

            occupied = (
                state[0] | state[1] | state[2] | state[3] | state[4]
            )
            possible_targets = occupied & unknown_mask

            bits = possible_targets
            while bits:
                low = bits & -bits
                cell = low.bit_length() - 1
                sample_counts[cell] += 1
                bits ^= low

            sample_total += 1
            chain_samples += 1

    # Deterministic placement-density estimate stabilizes Monte Carlo noise and
    # also provides a complete fallback if sampling is interrupted.
    local_scores = [0.0] * 100
    multiplicity = {5: 1, 4: 1, 3: 2, 2: 1}

    for length in _UNIQUE_LENGTHS:
        placements = valid_by_length[length]
        if not placements:
            continue

        normalizer = multiplicity[length] / len(placements)

        for mask in placements:
            hit_count = (mask & hit_mask).bit_count()
            if hit_count:
                weight = normalizer * (4.0 ** min(hit_count, 3))
            else:
                weight = normalizer

            targets = mask & unknown_mask
            while targets:
                low = targets & -targets
                cell = low.bit_length() - 1
                local_scores[cell] += weight
                targets ^= low

    max_local = max((local_scores[cell] for cell in unknown_cells), default=0.0)

    best_cell = unknown_cells[0]
    best_score = float("-inf")

    for cell in unknown_cells:
        if sample_total:
            posterior = sample_counts[cell] / sample_total
        else:
            posterior = 0.0

        density = local_scores[cell] / max_local if max_local > 0.0 else 0.0

        row, col = divmod(cell, 10)

        # Density regularization, a very small parity preference, and a stable
        # center tie-break. The posterior remains the dominant term.
        score = posterior + 0.035 * density
        if (row + col) % 2 == 0:
            score += 0.0015
        score += 0.000001 * (9 - abs(2 * row - 9) - abs(2 * col - 9))

        if score > best_score:
            best_score = score
            best_cell = cell

    return divmod(best_cell, 10)
