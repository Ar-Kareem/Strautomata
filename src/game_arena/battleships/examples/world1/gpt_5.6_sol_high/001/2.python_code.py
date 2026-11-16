
import random
import time


_SHIPS = (5, 4, 3, 3, 2)
_UNIQUE_LENGTHS = (2, 3, 4, 5)
_LENGTH_MULTIPLICITY = {2: 1, 3: 2, 4: 1, 5: 1}


def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.perf_counter()
    deadline = start_time + 0.70

    values = [board[r][c] for r in range(10) for c in range(10)]
    unknown_cells = [i for i, value in enumerate(values) if value == 0]

    # A legal unknown cell is expected whenever the policy is called.
    if not unknown_cells:
        return (0, 0)

    hit_mask = 0
    miss_mask = 0
    unknown_mask = 0

    for i, value in enumerate(values):
        bit = 1 << i
        if value == 1:
            hit_mask |= bit
        elif value == -1:
            miss_mask |= bit
        else:
            unknown_mask |= bit

    # Stable board-dependent random seed.
    seed = 1469598103934665603
    for value in values:
        seed ^= value + 2
        seed = (seed * 1099511628211) & ((1 << 64) - 1)
    rng = random.Random(seed)

    candidates = {length: [] for length in _UNIQUE_LENGTHS}
    covering = {
        length: [[] for _ in range(100)]
        for length in _UNIQUE_LENGTHS
    }

    # Enumerate every single-ship placement that does not cross a miss.
    for length in _UNIQUE_LENGTHS:
        placements = candidates[length]

        for row in range(10):
            row_start = row * 10
            for col in range(11 - length):
                mask = ((1 << length) - 1) << (row_start + col)
                if not (mask & miss_mask):
                    placements.append(mask)

        for row in range(11 - length):
            for col in range(10):
                mask = 0
                for offset in range(length):
                    mask |= 1 << ((row + offset) * 10 + col)
                if not (mask & miss_mask):
                    placements.append(mask)

        for mask in placements:
            bits = mask
            while bits:
                bit = bits & -bits
                cell = bit.bit_length() - 1
                covering[length][cell].append(mask)
                bits ^= bit

    # Local placement-density score, used as a fallback and tie-breaker.
    heuristic = [0.0] * 100
    for length in _UNIQUE_LENGTHS:
        multiplicity = _LENGTH_MULTIPLICITY[length]
        for mask in candidates[length]:
            covered_hits = (mask & hit_mask).bit_count()
            if covered_hits:
                weight = multiplicity * (5.0 ** covered_hits)
            else:
                weight = float(multiplicity)

            cells = mask & unknown_mask
            while cells:
                bit = cells & -cells
                cell = bit.bit_length() - 1
                heuristic[cell] += weight
                cells ^= bit

    occupancy_count = [0] * 100

    def remove_one(remaining, length):
        result = list(remaining)
        result.remove(length)
        return tuple(result)

    def solve_layout(remaining, occupied, budget):
        """Randomized bounded backtracking for one consistent fleet."""
        if budget[0] <= 0:
            return None
        budget[0] -= 1

        uncovered_hits = hit_mask & ~occupied

        if not remaining:
            return occupied if not uncovered_hits else None

        if uncovered_hits.bit_count() > sum(remaining):
            return None

        options = None

        if uncovered_hits:
            # Choose the hit with the fewest currently viable explanations.
            bits = uncovered_hits
            best_count = 10 ** 9

            while bits:
                bit = bits & -bits
                cell = bit.bit_length() - 1
                cell_options = []
                seen_lengths = set()

                for length in remaining:
                    if length in seen_lengths:
                        continue
                    seen_lengths.add(length)

                    for mask in covering[length][cell]:
                        if not (mask & occupied):
                            cell_options.append((length, mask))

                if not cell_options:
                    return None

                if len(cell_options) < best_count:
                    best_count = len(cell_options)
                    options = cell_options

                bits ^= bit

            # Randomize equal choices, while first trying placements that
            # explain several existing hits at once.
            rng.shuffle(options)
            options.sort(
                key=lambda item: (item[1] & uncovered_hits).bit_count(),
                reverse=True,
            )
        else:
            # All hits are explained. Place the remaining ships, choosing
            # the currently most constrained ship length first.
            best_available = None
            best_length = None
            seen_lengths = set()

            for length in remaining:
                if length in seen_lengths:
                    continue
                seen_lengths.add(length)

                available = [
                    mask for mask in candidates[length]
                    if not (mask & occupied)
                ]

                if not available:
                    return None

                if best_available is None or len(available) < len(best_available):
                    best_available = available
                    best_length = length

            rng.shuffle(best_available)
            options = [(best_length, mask) for mask in best_available]

        for length, mask in options:
            next_remaining = remove_one(remaining, length)
            result = solve_layout(
                next_remaining,
                occupied | mask,
                budget,
            )
            if result is not None:
                return result

        return None

    attempts = 0
    successes = 0

    while attempts < 6000 and time.perf_counter() < deadline:
        attempts += 1
        node_budget = [450]
        layout = solve_layout(_SHIPS, 0, node_budget)

        if layout is None:
            continue

        successes += 1
        possible_targets = layout & unknown_mask

        while possible_targets:
            bit = possible_targets & -possible_targets
            cell = bit.bit_length() - 1
            occupancy_count[cell] += 1
            possible_targets ^= bit

    # Always select from the explicitly verified list of unknown cells.
    # The final integer term gives deterministic board-dependent tie-breaking.
    best_cell = max(
        unknown_cells,
        key=lambda cell: (
            occupancy_count[cell],
            heuristic[cell],
            ((cell + 1) * 1103515245 + seed) & 0xFFFFFFFF,
        ),
    )

    return (best_cell // 10, best_cell % 10)
