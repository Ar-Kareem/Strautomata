
import random
import time
from typing import List, Tuple


# The fleet contains two ships of length 3.
_FLEET = (5, 4, 3, 3, 2)
_UNIQUE_LENGTHS = (5, 4, 3, 2)
_COUNTS = {5: 1, 4: 1, 3: 2, 2: 1}
_FULL_MASK = (1 << 100) - 1


def _make_placements():
    placements = {length: [] for length in _UNIQUE_LENGTHS}
    cover = {
        length: [[] for _ in range(100)]
        for length in _UNIQUE_LENGTHS
    }

    for length in _UNIQUE_LENGTHS:
        # Horizontal placements.
        for row in range(10):
            for start_col in range(11 - length):
                mask = 0
                for col in range(start_col, start_col + length):
                    mask |= 1 << (row * 10 + col)
                placements[length].append(mask)
                for col in range(start_col, start_col + length):
                    cover[length][row * 10 + col].append(mask)

        # Vertical placements.
        for col in range(10):
            for start_row in range(11 - length):
                mask = 0
                for row in range(start_row, start_row + length):
                    mask |= 1 << (row * 10 + col)
                placements[length].append(mask)
                for row in range(start_row, start_row + length):
                    cover[length][row * 10 + col].append(mask)

    return placements, cover


_PLACEMENTS, _COVER = _make_placements()


def _board_seed(board: List[List[int]]) -> int:
    """Stable state-dependent seed, avoiding dependence on Python's hash seed."""
    value = 0xCBF29CE484222325
    for row in range(10):
        for col in range(10):
            cell = int(board[row][col])
            code = 0 if cell == -1 else (2 if cell == 1 else 1)
            value ^= code + 3 * (row * 10 + col + 1)
            value = (value * 0x100000001B3) & 0xFFFFFFFFFFFFFFFF
    return value ^ 0x9E3779B97F4A7C15


def _sample_layout(
    rng: random.Random,
    hit_cells: List[int],
    hit_mask: int,
    miss_mask: int,
    valid: dict,
):
    """
    Construct one complete fleet consistent with observations.

    Ships covering known hits are selected first. The returned weight is the
    reciprocal of the construction proposal probability, up to constants.
    """
    occupied = 0
    remaining = dict(_COUNTS)
    weight = 1.0

    # Assign every hit to a compatible ship. Choosing the most constrained
    # uncovered hit first greatly reduces failed constructions.
    while True:
        uncovered = hit_mask & ~occupied
        if not uncovered:
            break

        best_options = None
        best_size = 10 ** 9

        for cell in hit_cells:
            bit = 1 << cell
            if not (uncovered & bit):
                continue

            options = []
            for length in _UNIQUE_LENGTHS:
                if remaining[length] == 0:
                    continue
                for mask in _COVER[length][cell]:
                    if not (mask & miss_mask) and not (mask & occupied):
                        options.append((length, mask))

            option_count = len(options)
            if option_count == 0:
                return None

            if option_count < best_size:
                best_size = option_count
                best_options = options
                if option_count == 1:
                    break

        length, mask = best_options[rng.randrange(best_size)]
        weight *= best_size
        occupied |= mask
        remaining[length] -= 1

    # Place ships that do not contain any as-yet-unassigned hits.
    for length in _UNIQUE_LENGTHS:
        for _ in range(remaining[length]):
            options = [
                mask for mask in valid[length]
                if not (mask & occupied)
            ]
            count = len(options)
            if count == 0:
                return None

            mask = options[rng.randrange(count)]
            weight *= count
            occupied |= mask

    return occupied, weight


def _heuristic_scores(
    unknown_mask: int,
    hit_mask: int,
    valid: dict,
) -> List[float]:
    """Placement-density and hit-continuation fallback scores."""
    scores = [0.0] * 100

    for length in _FLEET:
        for mask in valid[length]:
            hit_count = (mask & hit_mask).bit_count()
            if hit_count:
                placement_weight = 12.0 * (3.0 ** (hit_count - 1))
            else:
                placement_weight = 1.0

            cells = mask & unknown_mask
            while cells:
                bit = cells & -cells
                scores[bit.bit_length() - 1] += placement_weight
                cells ^= bit

    # Additional local targeting support around hits.
    hits = hit_mask
    while hits:
        bit = hits & -hits
        index = bit.bit_length() - 1
        row, col = divmod(index, 10)

        if row > 0:
            neighbor = index - 10
            if unknown_mask & (1 << neighbor):
                scores[neighbor] += 24.0
        if row < 9:
            neighbor = index + 10
            if unknown_mask & (1 << neighbor):
                scores[neighbor] += 24.0
        if col > 0:
            neighbor = index - 1
            if unknown_mask & (1 << neighbor):
                scores[neighbor] += 24.0
        if col < 9:
            neighbor = index + 1
            if unknown_mask & (1 << neighbor):
                scores[neighbor] += 24.0

        hits ^= bit

    return scores


def policy(board: list[list[int]]) -> tuple[int, int]:
    hit_mask = 0
    miss_mask = 0
    unknown_mask = 0
    unknown_cells = []
    hit_cells = []

    for row in range(10):
        for col in range(10):
            index = row * 10 + col
            value = int(board[row][col])
            if value == 0:
                unknown_mask |= 1 << index
                unknown_cells.append(index)
            elif value == 1:
                hit_mask |= 1 << index
                hit_cells.append(index)
            else:
                miss_mask |= 1 << index

    # Normally the game never requests a move when no legal moves remain.
    if not unknown_cells:
        return (0, 0)

    valid = {
        length: [
            mask for mask in _PLACEMENTS[length]
            if not (mask & miss_mask)
        ]
        for length in _UNIQUE_LENGTHS
    }

    seed = _board_seed(board)
    rng = random.Random(seed)

    weighted_counts = [0.0] * 100
    raw_counts = [0] * 100
    total_weight = 0.0
    squared_weight = 0.0
    successes = 0
    attempts = 0

    hit_count = len(hit_cells)
    if hit_count <= 2:
        target_samples = 6500
    elif hit_count <= 8:
        target_samples = 5000
    else:
        target_samples = 4000

    max_attempts = target_samples * 6 + 200
    deadline = time.perf_counter() + 0.78

    while successes < target_samples and attempts < max_attempts:
        attempts += 1
        result = _sample_layout(
            rng, hit_cells, hit_mask, miss_mask, valid
        )

        if result is not None:
            occupied, weight = result
            possible_targets = occupied & unknown_mask

            while possible_targets:
                bit = possible_targets & -possible_targets
                index = bit.bit_length() - 1
                weighted_counts[index] += weight
                raw_counts[index] += 1
                possible_targets ^= bit

            total_weight += weight
            squared_weight += weight * weight
            successes += 1

        if attempts & 31 == 0 and time.perf_counter() >= deadline:
            break

    heuristic = _heuristic_scores(unknown_mask, hit_mask, valid)
    heuristic_max = max((heuristic[i] for i in unknown_cells), default=1.0)
    if heuristic_max <= 0.0:
        heuristic_max = 1.0

    if successes > 0 and total_weight > 0.0:
        # Low effective sample sizes are stabilized with the unweighted
        # proposal estimate.
        if squared_weight > 0.0:
            effective_samples = (
                total_weight * total_weight / squared_weight
            )
        else:
            effective_samples = 0.0

        weighted_fraction = min(1.0, effective_samples / 300.0)

        best_cell = unknown_cells[0]
        best_score = -1.0
        best_tiebreak = -1

        for index in unknown_cells:
            weighted_probability = (
                weighted_counts[index] / total_weight
            )
            raw_probability = raw_counts[index] / successes

            score = (
                weighted_fraction * weighted_probability
                + (1.0 - weighted_fraction) * raw_probability
            )

            # Only affects essentially tied posterior probabilities.
            score += 0.0001 * heuristic[index] / heuristic_max

            tiebreak = (
                (seed ^ ((index + 1) * 0x9E3779B97F4A7C15))
                & 0xFFFFFFFFFFFFFFFF
            )

            if score > best_score or (
                score == best_score and tiebreak > best_tiebreak
            ):
                best_score = score
                best_tiebreak = tiebreak
                best_cell = index

        return divmod(best_cell, 10)

    # Guaranteed legal fallback if sampling cannot find a compatible layout.
    best_cell = unknown_cells[0]
    best_score = heuristic[best_cell]
    best_tiebreak = -1

    for index in unknown_cells:
        tiebreak = (
            (seed ^ ((index + 1) * 0xD6E8FEB86659FD93))
            & 0xFFFFFFFFFFFFFFFF
        )
        if heuristic[index] > best_score or (
            heuristic[index] == best_score and tiebreak > best_tiebreak
        ):
            best_score = heuristic[index]
            best_tiebreak = tiebreak
            best_cell = index

    return divmod(best_cell, 10)
