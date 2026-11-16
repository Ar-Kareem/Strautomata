
from __future__ import annotations

import random
import time
from functools import lru_cache

SIZE = 10
N = SIZE * SIZE

SHIP_LENGTHS = (5, 4, 3, 3, 2)
UNIQUE_LENGTHS = (2, 3, 4, 5)
MULTIPLICITY = {2: 1, 3: 2, 4: 1, 5: 1}

# Strong bias toward placements that pass through known hits.
TARGET_POW = (1, 15, 225, 3375, 50625, 759375)

CELL_MASKS = [1 << i for i in range(N)]
PARITY = [((i // SIZE) + (i % SIZE)) & 1 for i in range(N)]
CENTER = [
    -((i // SIZE - 4.5) ** 2 + (i % SIZE - 4.5) ** 2)
    for i in range(N)
]

NEIGHS = []
for i in range(N):
    r, c = divmod(i, SIZE)
    nbrs = []
    if r > 0:
        nbrs.append(i - SIZE)
    if r + 1 < SIZE:
        nbrs.append(i + SIZE)
    if c > 0:
        nbrs.append(i - 1)
    if c + 1 < SIZE:
        nbrs.append(i + 1)
    NEIGHS.append(tuple(nbrs))

# Precompute all straight ship placements.
PLACEMENTS = {L: [] for L in UNIQUE_LENGTHS}
COVER = {L: [[] for _ in range(N)] for L in UNIQUE_LENGTHS}

for L in UNIQUE_LENGTHS:
    plist = []

    # Horizontal
    for r in range(SIZE):
        for c in range(SIZE - L + 1):
            cells = tuple(r * SIZE + (c + k) for k in range(L))
            mask = 0
            for cell in cells:
                mask |= CELL_MASKS[cell]
            plist.append((mask, cells))

    # Vertical
    for r in range(SIZE - L + 1):
        for c in range(SIZE):
            cells = tuple((r + k) * SIZE + c for k in range(L))
            mask = 0
            for cell in cells:
                mask |= CELL_MASKS[cell]
            plist.append((mask, cells))

    PLACEMENTS[L] = plist
    for mask, cells in plist:
        for cell in cells:
            COVER[L][cell].append(mask)


def _board_seed(board: list[list[int]]) -> int:
    s = 0
    for row in board:
        for v in row:
            s = ((s * 3) + (v + 1)) & 0xFFFFFFFFFFFF
    return s


def policy(board: list[list[int]]) -> tuple[int, int]:
    unknown_cells = []
    unknown_bool = [False] * N
    unknown_mask = 0
    miss_mask = 0
    hit_mask = 0

    for r in range(SIZE):
        row = board[r]
        for c in range(SIZE):
            cell = r * SIZE + c
            bit = CELL_MASKS[cell]
            v = row[c]
            if v == 0:
                unknown_cells.append(cell)
                unknown_bool[cell] = True
                unknown_mask |= bit
            elif v == -1:
                miss_mask |= bit
            elif v == 1:
                hit_mask |= bit

    # Absolute safety fallback.
    if not unknown_cells:
        return (0, 0)

    # Unknown-degree tie breaker.
    unk_deg = [0] * N
    for cell in unknown_cells:
        cnt = 0
        for nb in NEIGHS[cell]:
            if unknown_bool[nb]:
                cnt += 1
        unk_deg[cell] = cnt

    # Build board-specific feasible placement lists.
    feasible_any = {L: [] for L in UNIQUE_LENGTHS}    # avoid misses
    feasible_clean = {L: [] for L in UNIQUE_LENGTHS}  # avoid misses and hits
    feasible_masks_any = {L: [] for L in UNIQUE_LENGTHS}
    cover_feasible = {L: [[] for _ in range(N)] for L in UNIQUE_LENGTHS}

    for L in UNIQUE_LENGTHS:
        any_list = []
        clean_list = []
        any_masks = []
        cover_list = [[] for _ in range(N)]

        for mask, cells in PLACEMENTS[L]:
            if mask & miss_mask:
                continue
            any_list.append((mask, cells))
            any_masks.append(mask)
            for cell in cells:
                cover_list[cell].append(mask)
            if not (mask & hit_mask):
                clean_list.append((mask, cells))

        feasible_any[L] = any_list
        feasible_clean[L] = clean_list
        feasible_masks_any[L] = any_masks
        cover_feasible[L] = cover_list

    def density_scores(feasible_map, weight_hits: bool) -> list[int]:
        scores = [0] * N
        if weight_hits:
            for L in UNIQUE_LENGTHS:
                mult = MULTIPLICITY[L]
                for mask, cells in feasible_map[L]:
                    h = (mask & hit_mask).bit_count()
                    w = mult * TARGET_POW[h]
                    for cell in cells:
                        if unknown_bool[cell]:
                            scores[cell] += w
        else:
            for L in UNIQUE_LENGTHS:
                mult = MULTIPLICITY[L]
                for _, cells in feasible_map[L]:
                    for cell in cells:
                        if unknown_bool[cell]:
                            scores[cell] += mult
        return scores

    def pick_by_scores(primary: list[int], secondary: list[int] | None, use_parity: bool) -> int:
        if secondary is None:
            secondary = [0] * N

        candidates = unknown_cells

        # Adaptive parity: use it in broader hunt phases, relax later.
        if use_parity and len(unknown_cells) > 40:
            even_cells = []
            odd_cells = []
            even_total = 0
            odd_total = 0

            for cell in unknown_cells:
                if PARITY[cell] == 0:
                    even_cells.append(cell)
                    even_total += primary[cell]
                else:
                    odd_cells.append(cell)
                    odd_total += primary[cell]

            preferred = even_cells if even_total >= odd_total else odd_cells
            if preferred:
                best_pref = max(primary[cell] for cell in preferred)
                if best_pref > 0:
                    candidates = preferred

        best = candidates[0]
        best_key = (primary[best], secondary[best], unk_deg[best], CENTER[best])

        for cell in candidates[1:]:
            key = (primary[cell], secondary[cell], unk_deg[cell], CENTER[cell])
            if key > best_key:
                best = cell
                best_key = key
        return best

    # No hits -> pure hunt mode.
    if hit_mask == 0:
        hunt_scores = density_scores(feasible_clean, weight_hits=False)
        best = pick_by_scores(hunt_scores, None, use_parity=True)
        r, c = divmod(best, SIZE)
        if board[r][c] == 0:
            return (r, c)

    # Hits exist -> target mode.
    target_heuristic = density_scores(feasible_any, weight_hits=True)

    # Small local adjacency bonus for targeting.
    for cell in unknown_cells:
        adj_hits = 0
        for nb in NEIGHS[cell]:
            if hit_mask & CELL_MASKS[nb]:
                adj_hits += 1
        if adj_hits:
            target_heuristic[cell] += 200 * adj_hits * adj_hits

    rng = random.Random(_board_seed(board))
    dead_cover = set()

    def all_hits_coverable(remaining: tuple[int, ...], occupied: int, uncovered: int) -> bool:
        rem_lengths = set(remaining)
        u = uncovered
        while u:
            bit = u & -u
            cell = bit.bit_length() - 1
            ok = False
            for L in rem_lengths:
                for mask in cover_feasible[L][cell]:
                    if not (mask & occupied):
                        ok = True
                        break
                if ok:
                    break
            if not ok:
                return False
            u ^= bit
        return True

    @lru_cache(maxsize=None)
    def can_fill(remaining: tuple[int, ...], occupied: int) -> bool:
        if not remaining:
            return True

        best_i = -1
        best_opts = None
        seen_lengths = set()

        for i, L in enumerate(remaining):
            if L in seen_lengths:
                continue
            seen_lengths.add(L)

            opts = []
            for mask in feasible_masks_any[L]:
                if not (mask & occupied):
                    opts.append(mask)

            if not opts:
                return False

            if best_opts is None or len(opts) < len(best_opts):
                best_i = i
                best_opts = opts
                if len(best_opts) == 1:
                    break

        new_remaining = remaining[:best_i] + remaining[best_i + 1 :]
        for mask in best_opts:
            if can_fill(new_remaining, occupied | mask):
                return True
        return False

    def sample_hit_cover(
        remaining: tuple[int, ...],
        occupied: int,
        uncovered: int,
        chosen_masks: list[int],
    ) -> bool:
        key = (remaining, occupied, uncovered)
        if key in dead_cover:
            return False

        if uncovered == 0:
            ok = can_fill(remaining, occupied)
            if not ok:
                dead_cover.add(key)
            return ok

        if not remaining or uncovered.bit_count() > sum(remaining):
            dead_cover.add(key)
            return False

        # Choose an uncovered hit with the fewest covering options.
        best_opts = None
        u = uncovered
        while u:
            bit = u & -u
            cell = bit.bit_length() - 1

            opts = []
            for i, L in enumerate(remaining):
                for mask in cover_feasible[L][cell]:
                    if not (mask & occupied):
                        opts.append((i, mask))

            if not opts:
                dead_cover.add(key)
                return False

            if best_opts is None or len(opts) < len(best_opts):
                best_opts = opts
                if len(best_opts) == 1:
                    break

            u ^= bit

        rng.shuffle(best_opts)
        best_opts.sort(key=lambda im: (-((im[1] & uncovered).bit_count()), -remaining[im[0]]))

        seen_next = set()
        for i, mask in best_opts:
            new_remaining = remaining[:i] + remaining[i + 1 :]
            new_occupied = occupied | mask
            new_uncovered = uncovered & ~mask
            next_state = (new_remaining, new_occupied, new_uncovered)

            if next_state in seen_next:
                continue
            seen_next.add(next_state)

            if not all_hits_coverable(new_remaining, new_occupied, new_uncovered):
                continue

            chosen_masks.append(mask)
            if sample_hit_cover(new_remaining, new_occupied, new_uncovered, chosen_masks):
                return True
            chosen_masks.pop()

        dead_cover.add(key)
        return False

    # Monte Carlo over fleets consistent with current hits/misses.
    target_counts = [0] * N
    attempts = 0
    successes = 0
    deadline = time.perf_counter() + 0.20

    while attempts < 256 and (attempts < 48 or time.perf_counter() < deadline):
        attempts += 1
        chosen = []
        if sample_hit_cover(SHIP_LENGTHS, 0, hit_mask, chosen):
            successes += 1
            target_union = 0
            for mask in chosen:
                target_union |= mask
            hidden_target_cells = target_union & unknown_mask
            while hidden_target_cells:
                bit = hidden_target_cells & -hidden_target_cells
                cell = bit.bit_length() - 1
                target_counts[cell] += 1
                hidden_target_cells ^= bit

    max_target = max(target_counts[cell] for cell in unknown_cells)

    # If sampling found likely hidden cells on already-hit ships, use that.
    if successes >= 8 and max_target > 0:
        best = pick_by_scores(target_counts, target_heuristic, use_parity=False)
        r, c = divmod(best, SIZE)
        if board[r][c] == 0:
            return (r, c)

    # If sampling strongly suggests all hit-bearing ships are already fully exposed,
    # resume hunting elsewhere while treating hit cells as occupied.
    if successes >= 8 and max_target == 0:
        clean_hunt = density_scores(feasible_clean, weight_hits=False)
        if max(clean_hunt[cell] for cell in unknown_cells) > 0:
            best = pick_by_scores(clean_hunt, None, use_parity=True)
            r, c = divmod(best, SIZE)
            if board[r][c] == 0:
                return (r, c)

    # Fallback target heuristic.
    best = pick_by_scores(target_heuristic, None, use_parity=False)
    r, c = divmod(best, SIZE)
    if board[r][c] == 0:
        return (r, c)

    # Final guaranteed-legal fallback.
    for cell in unknown_cells:
        r, c = divmod(cell, SIZE)
        if board[r][c] == 0:
            return (r, c)

    return (0, 0)
