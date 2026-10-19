
from typing import List, Tuple

SHIP_SLOTS = [5, 4, 3, 3, 2]

# Precompute all straight placements for each ship length.
PLACEMENTS_BY_LENGTH = {}
for L in {2, 3, 4, 5}:
    placements = []

    # Horizontal
    for r in range(10):
        for c in range(11 - L):
            cells = tuple(r * 10 + c + k for k in range(L))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            placements.append((cells, mask))

    # Vertical
    for r in range(11 - L):
        for c in range(10):
            cells = tuple((r + k) * 10 + c for k in range(L))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            placements.append((cells, mask))

    PLACEMENTS_BY_LENGTH[L] = placements

# Small tie-break bias toward the center.
CENTER_BIAS = []
for r in range(10):
    for c in range(10):
        CENTER_BIAS.append(4.5 - 0.5 * (abs(r - 4.5) + abs(c - 4.5)))

# Fast fallback target weights: placements covering more known hits get much larger weight.
APPROX_HIT_WEIGHT = [0, 50, 2500, 125000, 6250000, 312500000]

# Limits for deeper target enumeration.
EXACT_LEAF_LIMIT = 20000
EXACT_HIT_LIMIT = 12
EXACT_CANDIDATE_LIMIT = 220


def _best_by_key(candidates, key_fn):
    best = candidates[0]
    best_key = key_fn(best)
    for idx in candidates[1:]:
        k = key_fn(idx)
        if k > best_key:
            best = idx
            best_key = k
    return best


def _exact_target_score(slot_hit_lists, unknown_only_by_slot):
    """
    Enumerate ways to assign current hit cells to actual ship slots, respecting:
    - ship lengths
    - non-overlap
    - current misses/hits compatibility

    Returns a target score over unknown cells that could belong to already-hit ships.
    """
    num_slots = len(slot_hit_lists)
    if num_slots == 0:
        return None, False

    H = len(slot_hit_lists[0])
    if H == 0:
        return None, False

    all_hits_mask = (1 << H) - 1
    target = [0] * 100
    leaf_count = 0
    overflow = False
    count_cache = {}

    def disjoint_count(slot: int, occupied: int) -> int:
        # Count placements for an untouched ship slot that stay on unknown cells
        # and do not overlap already-selected hit-covering ships.
        key = (slot, occupied)
        cached = count_cache.get(key)
        if cached is not None:
            return cached

        cnt = 0
        for mask in unknown_only_by_slot[slot]:
            if not (mask & occupied):
                cnt += 1
        count_cache[key] = cnt
        return cnt

    def dfs(used_slots: int, covered_hits: int, occupied: int, target_unknown: int) -> None:
        nonlocal leaf_count, overflow
        if overflow:
            return

        if covered_hits == all_hits_mask:
            leaf_count += 1
            if leaf_count > EXACT_LEAF_LIMIT:
                overflow = True
                return

            # Softly weight by how much room remains for untouched ships.
            weight = 1
            for slot in range(num_slots):
                if used_slots & (1 << slot):
                    continue
                cnt = disjoint_count(slot, occupied)
                if cnt == 0:
                    return
                weight *= cnt

            m = target_unknown
            while m:
                bit = m & -m
                idx = bit.bit_length() - 1
                target[idx] += weight
                m ^= bit
            return

        # Pick the uncovered hit with the fewest legal assignments to prune quickly.
        remaining = all_hits_mask ^ covered_hits
        best_options = None

        bits = remaining
        while bits:
            bit = bits & -bits
            hit_idx = bit.bit_length() - 1

            options = []
            for slot in range(num_slots):
                if used_slots & (1 << slot):
                    continue
                for cand in slot_hit_lists[slot][hit_idx]:
                    if not (cand[0] & occupied):
                        options.append((slot, cand))

            if not options:
                return

            if best_options is None or len(options) < len(best_options):
                best_options = options
                if len(best_options) == 1:
                    break

            bits ^= bit

        for slot, cand in best_options:
            cell_mask, hit_mask, unk_mask = cand
            dfs(
                used_slots | (1 << slot),
                covered_hits | hit_mask,
                occupied | cell_mask,
                target_unknown | unk_mask,
            )
            if overflow:
                return

    dfs(0, 0, 0, 0)
    return target, overflow


def policy(board: List[List[int]]) -> Tuple[int, int]:
    flat = [board[r][c] for r in range(10) for c in range(10)]
    unknown = [i for i, v in enumerate(flat) if v == 0]

    # If somehow called on a full board, return a deterministic in-range cell.
    if not unknown:
        return (0, 0)

    hits = [i for i, v in enumerate(flat) if v == 1]
    H = len(hits)

    hit_bit = [0] * 100
    for i, idx in enumerate(hits):
        hit_bit[idx] = 1 << i

    hunt = [0] * 100
    approx_target = [0] * 100

    # For the deeper target search.
    unknown_only_by_slot = [[] for _ in SHIP_SLOTS]
    slot_hit_lists = [[[] for _ in range(H)] for _ in SHIP_SLOTS]
    total_hit_candidates = 0

    # Build hunt heatmap + target candidates in one pass.
    for slot, L in enumerate(SHIP_SLOTS):
        for cells, cell_mask in PLACEMENTS_BY_LENGTH[L]:
            hits_mask = 0
            unk_mask = 0
            hit_count = 0
            valid = True

            for idx in cells:
                v = flat[idx]
                if v == -1:
                    valid = False
                    break
                if v == 1:
                    hits_mask |= hit_bit[idx]
                    hit_count += 1
                else:
                    unk_mask |= 1 << idx

            if not valid:
                continue

            if hits_mask == 0:
                # All cells are unknown here.
                unknown_only_by_slot[slot].append(cell_mask)
                for idx in cells:
                    hunt[idx] += 1
            else:
                total_hit_candidates += 1

                # Fast approximate target score.
                if unk_mask:
                    w = APPROX_HIT_WEIGHT[hit_count]
                    m = unk_mask
                    while m:
                        bit = m & -m
                        idx = bit.bit_length() - 1
                        approx_target[idx] += w
                        m ^= bit

                # Candidate for deeper exact-ish target reasoning.
                cand = (cell_mask, hits_mask, unk_mask)
                bits = hits_mask
                while bits:
                    bit = bits & -bits
                    hit_idx = bit.bit_length() - 1
                    slot_hit_lists[slot][hit_idx].append(cand)
                    bits ^= bit

    # Try deeper target reasoning when the state is manageable.
    exact_target = None
    exact_overflow = False
    if 0 < H <= EXACT_HIT_LIMIT and total_hit_candidates <= EXACT_CANDIDATE_LIMIT:
        exact_target, exact_overflow = _exact_target_score(slot_hit_lists, unknown_only_by_slot)

    # If exact target mode says some unknown cells can still belong to hit ships, prioritize that.
    if exact_target is not None and not exact_overflow:
        exact_positive = any(exact_target[idx] > 0 for idx in unknown)
        if exact_positive:
            best = _best_by_key(
                unknown,
                lambda idx: (
                    exact_target[idx],   # primary: exact local consistency with current hits
                    approx_target[idx],  # secondary: fast placement pressure
                    hunt[idx],           # tertiary: general ship density
                    CENTER_BIAS[idx],
                    -idx,
                ),
            )
            return (best // 10, best % 10)

    # Fallback target mode: weighted hit-aware heatmap.
    approx_positive = any(approx_target[idx] > 0 for idx in unknown)
    if approx_positive and H > 0:
        best = _best_by_key(
            unknown,
            lambda idx: (
                approx_target[idx],
                hunt[idx],
                CENTER_BIAS[idx],
                -idx,
            ),
        )
        return (best // 10, best % 10)

    # Hunt mode: all-unknown placement heatmap + mild checkerboard preference.
    parity_totals = [0.0, 0.0]
    for idx in unknown:
        r, c = divmod(idx, 10)
        parity_totals[(r + c) & 1] += hunt[idx]

    preferred_parity = 0 if parity_totals[0] >= parity_totals[1] else 1
    max_hunt = max(hunt[idx] for idx in unknown)

    if max_hunt > 0:
        def hunt_key(idx: int):
            r, c = divmod(idx, 10)
            parity = (r + c) & 1
            boosted = hunt[idx] * (1.10 if parity == preferred_parity else 1.0)
            return (boosted, CENTER_BIAS[idx], -idx)

        best = _best_by_key(unknown, hunt_key)
        return (best // 10, best % 10)

    # Last-resort legal fallback.
    best = _best_by_key(unknown, lambda idx: (CENTER_BIAS[idx], -idx))
    return (best // 10, best % 10)
