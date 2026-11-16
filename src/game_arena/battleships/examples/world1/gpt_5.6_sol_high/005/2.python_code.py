
from __future__ import annotations

import random
import time


FLEET = (5, 4, 3, 3, 2)
MULTIPLICITY = {5: 1, 4: 1, 3: 2, 2: 1}


def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.perf_counter()

    miss_mask = 0
    hit_mask = 0
    unknown_mask = 0
    unknown_cells: list[int] = []

    for row in range(10):
        for col in range(10):
            idx = row * 10 + col
            bit = 1 << idx
            value = board[row][col]

            if value == 0:
                unknown_mask |= bit
                unknown_cells.append(idx)
            elif value == -1:
                miss_mask |= bit
            elif value == 1:
                hit_mask |= bit

    # A normal game never calls the policy after every cell has been fired at.
    if not unknown_cells:
        return (0, 0)

    seed = (
        miss_mask * 0x9E3779B97F4A7C15
        + hit_mask * 0xD1B54A32D192ED03
        + len(unknown_cells) * 0x94D049BB133111EB
    ) & ((1 << 128) - 1)
    rng = random.Random(seed)

    # Enumerate every straight placement that does not cross a known miss.
    placements: dict[int, list[int]] = {}
    cover: dict[int, list[list[int]]] = {}

    for length in (2, 3, 4, 5):
        masks: list[int] = []

        horizontal_shape = (1 << length) - 1
        for row in range(10):
            row_offset = row * 10
            for col in range(11 - length):
                mask = horizontal_shape << (row_offset + col)
                if not (mask & miss_mask):
                    masks.append(mask)

        for row in range(11 - length):
            for col in range(10):
                mask = 0
                pos = row * 10 + col
                for k in range(length):
                    mask |= 1 << (pos + 10 * k)
                if not (mask & miss_mask):
                    masks.append(mask)

        placements[length] = masks

        by_cell: list[list[int]] = [[] for _ in range(100)]
        for mask in masks:
            cells = mask
            while cells:
                bit = cells & -cells
                idx = bit.bit_length() - 1
                by_cell[idx].append(mask)
                cells ^= bit
        cover[length] = by_cell

    # A fast placement-density model is both a fallback and a stabilizing
    # prior for the Monte Carlo fleet model.
    base_score = [0.0] * 100

    for length in (2, 3, 4, 5):
        multiplicity = MULTIPLICITY[length]

        for mask in placements[length]:
            number_of_hits = (mask & hit_mask).bit_count()
            weight = float(multiplicity)

            if hit_mask:
                if number_of_hits:
                    # Placements explaining multiple aligned hits are much
                    # more likely to be the ship currently being targeted.
                    weight *= 4.0 * (3.2 ** (number_of_hits - 1))
                else:
                    # Some ships do not contain existing hits, so these
                    # placements remain possible but receive less emphasis.
                    weight *= 0.45

            cells = mask & unknown_mask
            while cells:
                bit = cells & -cells
                idx = bit.bit_length() - 1
                base_score[idx] += weight
                cells ^= bit

    occupancy_count = [0] * 100
    successful_samples = 0

    # Construct a complete fleet consistent with all observations. When hits
    # are uncovered, the most constrained hit is assigned first. This makes
    # late-game configurations practical without rejection sampling.
    def build_fleet(
        occupied: int,
        uncovered_hits: int,
        remaining: tuple[int, ...],
        budget: list[int],
    ) -> int | None:
        budget[0] -= 1
        if budget[0] < 0:
            return None

        if not remaining:
            return occupied if uncovered_hits == 0 else None

        unique_lengths: list[int] = []
        for length in remaining:
            if length not in unique_lengths:
                unique_lengths.append(length)

        if uncovered_hits:
            best_options: list[tuple[int, int]] | None = None
            bits = uncovered_hits

            while bits:
                hit_bit = bits & -bits
                hit_idx = hit_bit.bit_length() - 1
                options: list[tuple[int, int]] = []

                for length in unique_lengths:
                    for mask in cover[length][hit_idx]:
                        if not (mask & occupied):
                            options.append((length, mask))

                # If even one uncovered hit cannot be assigned to a remaining
                # ship, this partial fleet is impossible.
                if not options:
                    return None

                if best_options is None or len(options) < len(best_options):
                    best_options = options

                bits ^= hit_bit

            assert best_options is not None
            rng.shuffle(best_options)

            for length, mask in best_options:
                next_remaining = list(remaining)
                next_remaining.remove(length)

                result = build_fleet(
                    occupied | mask,
                    uncovered_hits & ~mask,
                    tuple(next_remaining),
                    budget,
                )
                if result is not None:
                    return result

            return None

        # All known hits are covered. Fill the rest of the fleet, choosing the
        # currently most constrained ship length first.
        chosen_length = -1
        chosen_options: list[int] | None = None

        for length in unique_lengths:
            options = [
                mask for mask in placements[length]
                if not (mask & occupied)
            ]

            if not options:
                return None

            if chosen_options is None or len(options) < len(chosen_options):
                chosen_length = length
                chosen_options = options

        assert chosen_options is not None
        rng.shuffle(chosen_options)

        next_remaining = list(remaining)
        next_remaining.remove(chosen_length)
        next_remaining_tuple = tuple(next_remaining)

        for mask in chosen_options:
            result = build_fleet(
                occupied | mask,
                0,
                next_remaining_tuple,
                budget,
            )
            if result is not None:
                return result

        return None

    # Leave headroom under the one-second execution limit.
    deadline = start_time + 0.72
    target_samples = 10000
    attempts = 0
    maximum_attempts = 30000

    while (
        successful_samples < target_samples
        and attempts < maximum_attempts
    ):
        if attempts % 8 == 0 and time.perf_counter() >= deadline:
            break

        attempts += 1
        fleet_mask = build_fleet(
            occupied=0,
            uncovered_hits=hit_mask,
            remaining=FLEET,
            budget=[220],
        )

        if fleet_mask is None:
            continue

        successful_samples += 1
        possible_targets = fleet_mask & unknown_mask

        while possible_targets:
            bit = possible_targets & -possible_targets
            idx = bit.bit_length() - 1
            occupancy_count[idx] += 1
            possible_targets ^= bit

    base_max = max(base_score[idx] for idx in unknown_cells)
    best_idx = unknown_cells[0]
    best_value = float("-inf")

    if successful_samples:
        # Reduce Monte Carlo influence if an unusually constrained board
        # yielded very few successful samples.
        reliability = min(1.0, successful_samples / 500.0)
        prior_weight = 0.10 if hit_mask == 0 else 0.035

        for idx in unknown_cells:
            posterior = occupancy_count[idx] / successful_samples
            prior = base_score[idx] / base_max if base_max > 0 else 0.0

            value = (
                reliability * posterior
                + (1.0 - reliability) * prior
                + prior_weight * prior
            )

            row, col = divmod(idx, 10)

            # Checkerboard and centrality only break near-exact ties.
            if (row + col) % 2 == 0:
                value += 2e-8
            value -= 1e-10 * (
                (row - 4.5) * (row - 4.5)
                + (col - 4.5) * (col - 4.5)
            )
            value += rng.random() * 1e-12

            if value > best_value:
                best_value = value
                best_idx = idx
    else:
        # Sampling can only fail on extremely constrained or inconsistent
        # inputs; placement density still guarantees a legal action.
        for idx in unknown_cells:
            value = base_score[idx]
            row, col = divmod(idx, 10)

            if (row + col) % 2 == 0:
                value += 1e-8
            value -= 1e-10 * (
                (row - 4.5) * (row - 4.5)
                + (col - 4.5) * (col - 4.5)
            )

            if value > best_value:
                best_value = value
                best_idx = idx

    row, col = divmod(best_idx, 10)

    # Defensive legality guard.
    if board[row][col] != 0:
        row, col = divmod(unknown_cells[0], 10)

    return (row, col)
