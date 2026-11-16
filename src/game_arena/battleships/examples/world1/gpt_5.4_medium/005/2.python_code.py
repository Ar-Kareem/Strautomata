
import time
import random

# Fleet specification
SHIP_LENGTHS = [5, 4, 3, 3, 2]
UNIQUE_LENGTHS = [5, 4, 3, 2]
LENGTH_MULTIPLICITY = {5: 1, 4: 1, 3: 2, 2: 1}

# Precompute all possible placements on a 10x10 board.
# Each placement is stored as (bitmask, tuple_of_cell_indices).
ALL_PLACEMENTS = {L: [] for L in UNIQUE_LENGTHS}
for L in UNIQUE_LENGTHS:
    # Horizontal
    for r in range(10):
        for c in range(11 - L):
            cells = tuple(r * 10 + (c + k) for k in range(L))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            ALL_PLACEMENTS[L].append((mask, cells))
    # Vertical
    for r in range(11 - L):
        for c in range(10):
            cells = tuple((r + k) * 10 + c for k in range(L))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            ALL_PLACEMENTS[L].append((mask, cells))

# Neighbor lists and center bias for tie-breaking.
NEIGHBORS = [[] for _ in range(100)]
CENTER_BIAS = [0.0] * 100
for r in range(10):
    for c in range(10):
        idx = r * 10 + c
        if r > 0:
            NEIGHBORS[idx].append((r - 1) * 10 + c)
        if r < 9:
            NEIGHBORS[idx].append((r + 1) * 10 + c)
        if c > 0:
            NEIGHBORS[idx].append(r * 10 + (c - 1))
        if c < 9:
            NEIGHBORS[idx].append(r * 10 + (c + 1))
        # Higher near center
        CENTER_BIAS[idx] = -((r - 4.5) ** 2 + (c - 4.5) ** 2)


def _compute_weighted_heatmap(miss_mask: int, hit_mask: int, unknown_mask: int):
    """
    Placement-count heatmap.
    If hits exist, heavily upweight placements that include hits.
    """
    scores = [0] * 100
    has_hits = hit_mask != 0

    for L in UNIQUE_LENGTHS:
        mult = LENGTH_MULTIPLICITY[L]
        for mask, cells in ALL_PLACEMENTS[L]:
            if mask & miss_mask:
                continue

            if has_hits:
                k = (mask & hit_mask).bit_count()
                weight = mult if k == 0 else mult * (20 ** k)
            else:
                weight = mult

            for idx in cells:
                if (unknown_mask >> idx) & 1:
                    scores[idx] += weight

    return scores


def _select_best_cell(primary_scores, secondary_scores, unknown_idxs, unknown_mask, use_parity):
    """
    Choose the best unknown cell by score, with optional parity restriction
    and deterministic tie-breaking.
    """
    candidates = unknown_idxs

    if use_parity and unknown_idxs:
        even_cells = []
        odd_cells = []
        even_total = 0
        odd_total = 0

        for idx in unknown_idxs:
            r, c = divmod(idx, 10)
            if ((r + c) & 1) == 0:
                even_cells.append(idx)
                even_total += primary_scores[idx]
            else:
                odd_cells.append(idx)
                odd_total += primary_scores[idx]

        preferred = even_cells if even_total >= odd_total else odd_cells
        if preferred:
            candidates = preferred

    best_idx = candidates[0]
    best_key = None

    for idx in candidates:
        unknown_neighbors = 0
        for j in NEIGHBORS[idx]:
            unknown_neighbors += (unknown_mask >> j) & 1

        key = (
            primary_scores[idx],
            secondary_scores[idx] if secondary_scores is not None else 0,
            unknown_neighbors,
            CENTER_BIAS[idx],
        )
        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return divmod(best_idx, 10)


def policy(board: list[list[int]]) -> tuple[int, int]:
    miss_mask = 0
    hit_mask = 0
    unknown_mask = 0
    unknown_idxs = []

    for r in range(10):
        row = board[r]
        for c in range(10):
            idx = r * 10 + c
            v = row[c]
            if v == -1:
                miss_mask |= 1 << idx
            elif v == 1:
                hit_mask |= 1 << idx
            else:
                unknown_mask |= 1 << idx
                unknown_idxs.append(idx)

    # Safety fallback if no legal moves exist (should not normally happen).
    if not unknown_idxs:
        return (0, 0)

    # Build per-call valid placements and hit-coverage lists filtered by misses.
    valid_masks = {L: [] for L in UNIQUE_LENGTHS}
    cover_lists = {L: [[] for _ in range(100)] for L in UNIQUE_LENGTHS}

    for L in UNIQUE_LENGTHS:
        for mask, cells in ALL_PLACEMENTS[L]:
            if mask & miss_mask:
                continue
            valid_masks[L].append(mask)
            for idx in cells:
                cover_lists[L][idx].append(mask)

    # General fallback heatmap.
    fallback_scores = _compute_weighted_heatmap(miss_mask, hit_mask, unknown_mask)

    # If there are hits, do Monte Carlo sampling of full consistent fleets.
    if hit_mask:
        start = time.perf_counter()
        deadline = start + 0.88

        # Deterministic seed from current knowledge, for reproducibility.
        seed = hit_mask ^ (miss_mask << 1) ^ 0x9E3779B97F4A7C15
        rng = random.Random(seed)

        sample_scores = [0] * 100
        samples = 0
        failures = 0

        base_counts = [0] * 6
        base_counts[2] = 1
        base_counts[3] = 2
        base_counts[4] = 1
        base_counts[5] = 1

        def fill_random_remaining(counts, occupied):
            """
            Randomly complete the rest of the fleet once all known hits are covered.
            A few retries are enough on a 10x10 board.
            """
            remaining = []
            for L in SHIP_LENGTHS:
                # Use the remaining counts to rebuild the multiset
                # without mutating counts.
                pass
            remaining = []
            for L in (5, 4, 3, 2):
                remaining.extend([L] * counts[L])

            for _ in range(18):
                occ = occupied
                placed = []
                rem = remaining[:]

                ok = True
                while rem:
                    distinct_lengths = set(rem)
                    best_L = None
                    best_cands = None

                    for L in distinct_lengths:
                        cands = [m for m in valid_masks[L] if (m & occ) == 0]
                        if not cands:
                            ok = False
                            best_cands = None
                            break
                        if best_cands is None or len(cands) < len(best_cands):
                            best_L = L
                            best_cands = cands

                    if not ok or not best_cands:
                        ok = False
                        break

                    chosen = rng.choice(best_cands)
                    occ |= chosen
                    placed.append(chosen)
                    rem.remove(best_L)

                if ok:
                    return placed

            return None

        def search_cover_hits(counts, occupied, hits_left, placed):
            """
            Randomized backtracking:
            choose placements so that all known hit cells are covered exactly once
            by the fleet, while respecting misses and non-overlap.
            """
            if time.perf_counter() > deadline:
                return None

            remaining_capacity = counts[2] * 2 + counts[3] * 3 + counts[4] * 4 + counts[5] * 5
            if hits_left.bit_count() > remaining_capacity:
                return None

            if hits_left == 0:
                rest = fill_random_remaining(counts, occupied)
                if rest is None:
                    return None
                return placed + rest

            # Choose the most constrained uncovered hit.
            best_candidates = None
            hm = hits_left
            while hm:
                lsb = hm & -hm
                hit_idx = lsb.bit_length() - 1
                candidates = []

                for L in UNIQUE_LENGTHS:
                    if counts[L] == 0:
                        continue
                    for mask in cover_lists[L][hit_idx]:
                        if (mask & occupied) == 0:
                            candidates.append((L, mask))

                if not candidates:
                    return None

                if best_candidates is None or len(candidates) < len(best_candidates):
                    best_candidates = candidates
                    if len(best_candidates) == 1:
                        break

                hm ^= lsb

            rng.shuffle(best_candidates)
            # Prefer placements that explain more currently uncovered hits.
            best_candidates.sort(
                key=lambda item: (item[1] & hits_left).bit_count(),
                reverse=True,
            )

            for L, mask in best_candidates:
                counts[L] -= 1
                placed.append(mask)

                result = search_cover_hits(
                    counts,
                    occupied | mask,
                    hits_left & ~mask,
                    placed,
                )

                placed.pop()
                counts[L] += 1

                if result is not None:
                    return result

                if time.perf_counter() > deadline:
                    return None

            return None

        while samples < 300 and time.perf_counter() < deadline and failures < 12:
            counts = base_counts[:]
            solution = search_cover_hits(counts, 0, hit_mask, [])

            if solution is None:
                failures += 1
                continue

            failures = 0
            fleet_mask = 0
            for m in solution:
                fleet_mask |= m

            remaining_targets = fleet_mask & unknown_mask
            while remaining_targets:
                lsb = remaining_targets & -remaining_targets
                idx = lsb.bit_length() - 1
                sample_scores[idx] += 1
                remaining_targets ^= lsb

            samples += 1

        if samples >= 5:
            return _select_best_cell(
                primary_scores=sample_scores,
                secondary_scores=fallback_scores,
                unknown_idxs=unknown_idxs,
                unknown_mask=unknown_mask,
                use_parity=False,
            )

    # Hunt mode or fallback mode.
    return _select_best_cell(
        primary_scores=fallback_scores,
        secondary_scores=None,
        unknown_idxs=unknown_idxs,
        unknown_mask=unknown_mask,
        use_parity=(hit_mask == 0),
    )
