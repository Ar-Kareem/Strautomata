
from __future__ import annotations

N = 10
BOARD_CELLS = N * N
SHIP_LENGTHS = (5, 4, 3, 3, 2)

BITS = [1 << i for i in range(BOARD_CELLS)]
ROWS = [i // N for i in range(BOARD_CELLS)]
COLS = [i % N for i in range(BOARD_CELLS)]

NEIGHBORS = []
for i in range(BOARD_CELLS):
    r, c = ROWS[i], COLS[i]
    ns = []
    if r > 0:
        ns.append(i - N)
    if r < N - 1:
        ns.append(i + N)
    if c > 0:
        ns.append(i - 1)
    if c < N - 1:
        ns.append(i + 1)
    NEIGHBORS.append(tuple(ns))

# Tiny center preference for tie-breaking.
CENTER_BONUS = []
for i in range(BOARD_CELLS):
    dist = abs(ROWS[i] - 4.5) + abs(COLS[i] - 4.5)
    CENTER_BONUS.append((9.0 - dist) * 1e-4)

# All straight placements for each distinct ship length.
PLACEMENTS = {L: [] for L in set(SHIP_LENGTHS)}
for L in set(SHIP_LENGTHS):
    # Horizontal placements
    for r in range(N):
        for c in range(N - L + 1):
            cells = tuple(r * N + c + k for k in range(L))
            mask = 0
            for idx in cells:
                mask |= BITS[idx]
            PLACEMENTS[L].append((mask, cells))

    # Vertical placements
    for r in range(N - L + 1):
        for c in range(N):
            cells = tuple((r + k) * N + c for k in range(L))
            mask = 0
            for idx in cells:
                mask |= BITS[idx]
            PLACEMENTS[L].append((mask, cells))


def _read_board(board):
    miss_mask = 0
    hit_mask = 0
    unknown_mask = 0
    unknown_cells = []

    for r in range(N):
        row = board[r]
        base = r * N
        for c in range(N):
            idx = base + c
            v = row[c]
            if v == 0:
                unknown_mask |= BITS[idx]
                unknown_cells.append(idx)
            elif v == 1:
                hit_mask |= BITS[idx]
            else:
                miss_mask |= BITS[idx]

    return miss_mask, hit_mask, unknown_mask, unknown_cells


def _component_can_fit_length(component_mask, length, block_mask):
    """Can a ship of this length contain the whole hit component without crossing blocked cells?"""
    if component_mask.bit_count() > length:
        return False

    for mask, _cells in PLACEMENTS[length]:
        if (mask & component_mask) == component_mask and not (mask & block_mask):
            return True
    return False


def _estimate_remaining_lengths(hit_mask, miss_mask):
    """
    Infer straight hit components that are effectively resolved.

    A straight component is considered sunk if no still-available longer ship can
    contain it. This handles max-length ships, blocked ends, and cases where
    larger ships have already been resolved.
    """
    remaining = list(SHIP_LENGTHS)
    sunk_mask = 0

    components = []
    seen = 0

    for start in range(BOARD_CELLS):
        b = BITS[start]
        if not (hit_mask & b) or (seen & b):
            continue

        stack = [start]
        seen |= b
        comp = []
        comp_mask = 0

        while stack:
            i = stack.pop()
            comp.append(i)
            comp_mask |= BITS[i]
            for nb in NEIGHBORS[i]:
                nb_bit = BITS[nb]
                if (hit_mask & nb_bit) and not (seen & nb_bit):
                    seen |= nb_bit
                    stack.append(nb)

        L = len(comp)

        same_row = all(ROWS[i] == ROWS[comp[0]] for i in comp)
        same_col = all(COLS[i] == COLS[comp[0]] for i in comp)

        is_straight_contiguous = False
        if same_row:
            cs = [COLS[i] for i in comp]
            is_straight_contiguous = (max(cs) - min(cs) + 1 == L)
        elif same_col:
            rs = [ROWS[i] for i in comp]
            is_straight_contiguous = (max(rs) - min(rs) + 1 == L)

        components.append((comp_mask, L, is_straight_contiguous))

    # Iterate because resolving one component can make another component forced.
    changed = True
    while changed:
        changed = False
        for comp_mask, L, is_line in components:
            if not is_line:
                continue
            if comp_mask & sunk_mask:
                continue
            if L not in remaining:
                continue

            block_mask = miss_mask | sunk_mask
            can_be_longer = False
            for longer in set(remaining):
                if longer > L and _component_can_fit_length(comp_mask, longer, block_mask):
                    can_be_longer = True
                    break

            if not can_be_longer:
                remaining.remove(L)
                sunk_mask |= comp_mask
                changed = True

    return tuple(remaining), sunk_mask


def _target_scores(block_mask, active_hit_mask, unknown_mask, lengths):
    """
    Score unknown cells near unresolved hits.

    Placements covering multiple hits are weighted heavily, which quickly follows
    a discovered line. Single-hit placements are used only for isolated hits, so
    the policy does not waste perpendicular shots once a line is known.
    """
    scores = [0.0] * BOARD_CELLS

    if active_hit_mask == 0 or unknown_mask == 0:
        return scores

    adjacent_hit_mask = 0
    near_hit_mask = 0

    m = active_hit_mask
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        has_adjacent_hit = False

        for nb in NEIGHBORS[i]:
            nb_bit = BITS[nb]
            if active_hit_mask & nb_bit:
                has_adjacent_hit = True
            elif unknown_mask & nb_bit:
                near_hit_mask |= nb_bit

        if has_adjacent_hit:
            adjacent_hit_mask |= lsb

        m ^= lsb

    for L in lengths:
        for placement_mask, cells in PLACEMENTS[L]:
            if placement_mask & block_mask:
                continue

            hits_in_placement = placement_mask & active_hit_mask
            if not hits_in_placement:
                continue

            unknowns_in_placement = placement_mask & unknown_mask
            if not unknowns_in_placement:
                continue

            k = hits_in_placement.bit_count()

            # If this is only one hit and that hit already has a neighbor hit,
            # avoid perpendicular probing; keep following the line instead.
            if k == 1 and (hits_in_placement & adjacent_hit_mask):
                continue

            if k == 1:
                weight = 4.0 + 0.35 * L
            else:
                weight = 18.0 * (k - 1) * (k - 1) + 6.0 * k + 0.35 * L

            u = unknowns_in_placement
            while u:
                lsb = u & -u
                idx = lsb.bit_length() - 1

                add = weight
                if near_hit_mask & lsb:
                    add *= 1.65

                scores[idx] += add
                u ^= lsb

    return scores


def _hunt_scores(miss_mask, hit_mask, unknown_mask, unknown_cells, lengths):
    """
    Probability-density hunt map for undiscovered ships.
    Known hit cells are treated as occupied/blocked for the remaining fleet.
    """
    scores = [0.0] * BOARD_CELLS
    if not lengths:
        lengths = SHIP_LENGTHS

    block_mask = miss_mask | hit_mask

    for L in lengths:
        valid_count = 0
        for placement_mask, _cells in PLACEMENTS[L]:
            if not (placement_mask & block_mask):
                valid_count += 1

        if valid_count == 0:
            continue

        weight = 1.0 / valid_count
        for placement_mask, cells in PLACEMENTS[L]:
            if placement_mask & block_mask:
                continue
            for idx in cells:
                scores[idx] += weight

    # Modulo search pattern. If the smallest remaining ship has length s, one
    # diagonal class modulo s intersects every possible straight ship of length s.
    min_len = min(lengths) if lengths else 2
    if min_len > 1:
        phase_totals = [0.0] * min_len
        for idx in unknown_cells:
            phase_totals[(ROWS[idx] + COLS[idx]) % min_len] += scores[idx]

        phase = 0
        best_total = phase_totals[0]
        for p in range(1, min_len):
            if phase_totals[p] > best_total:
                best_total = phase_totals[p]
                phase = p

        if best_total > 0.0:
            off_factor = 0.38 if min_len == 2 else 0.25
            for idx in unknown_cells:
                if (ROWS[idx] + COLS[idx]) % min_len == phase:
                    scores[idx] *= 1.08
                else:
                    scores[idx] *= off_factor

    return scores


def _max_score(scores, unknown_cells):
    best = 0.0
    for idx in unknown_cells:
        if scores[idx] > best:
            best = scores[idx]
    return best


def _best_index(unknown_cells, scores, miss_mask, hit_mask):
    best_idx = unknown_cells[0]
    best_score = -1e100

    # Deterministic microscopic jitter for stable but nontrivial tie-breaking.
    seed = (miss_mask ^ (hit_mask << 1)) & ((1 << 64) - 1)

    for idx in unknown_cells:
        jitter = (((seed >> (idx % 29)) ^ (idx * 1000003)) & 0xFFFF) * 1e-12
        s = scores[idx] + CENTER_BONUS[idx] + jitter
        if s > best_score:
            best_score = s
            best_idx = idx

    return best_idx


def policy(board: list[list[int]]) -> tuple[int, int]:
    miss_mask, hit_mask, unknown_mask, unknown_cells = _read_board(board)

    # No legal move exists on a full board, but keep the function total.
    if not unknown_cells:
        return (0, 0)

    remaining, sunk_mask = _estimate_remaining_lengths(hit_mask, miss_mask)
    lengths = remaining if remaining else SHIP_LENGTHS

    active_hit_mask = hit_mask & ~sunk_mask

    hunt = _hunt_scores(miss_mask, hit_mask, unknown_mask, unknown_cells, lengths)

    # If inference was too aggressive and no hunt placements remain, fall back.
    if _max_score(hunt, unknown_cells) <= 0.0 and lengths != SHIP_LENGTHS:
        hunt = _hunt_scores(miss_mask, hit_mask, unknown_mask, unknown_cells, SHIP_LENGTHS)

    final_scores = hunt

    if active_hit_mask:
        target = _target_scores(miss_mask | sunk_mask, active_hit_mask, unknown_mask, lengths)
        target_max = _max_score(target, unknown_cells)

        # Robust fallback if length inference removed too much.
        if target_max <= 0.0 and lengths != SHIP_LENGTHS:
            target = _target_scores(miss_mask | sunk_mask, active_hit_mask, unknown_mask, SHIP_LENGTHS)
            target_max = _max_score(target, unknown_cells)

        if target_max > 0.0:
            final_scores = [0.0] * BOARD_CELLS
            for idx in unknown_cells:
                # Target dominates; hunt is only a tie-breaker.
                final_scores[idx] = target[idx] + 0.01 * hunt[idx]

    idx = _best_index(unknown_cells, final_scores, miss_mask, hit_mask)
    r, c = ROWS[idx], COLS[idx]

    # Final legality guard.
    if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
        return (r, c)

    for rr in range(N):
        for cc in range(N):
            if board[rr][cc] == 0:
                return (rr, cc)

    return (0, 0)
