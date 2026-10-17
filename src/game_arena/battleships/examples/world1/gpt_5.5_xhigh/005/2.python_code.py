
N = 10
NUM_CELLS = 100

HORIZONTAL = 0
VERTICAL = 1
ANY_ORIENT = -1

# Fleet: 5, 4, 3, 3, 2
UNIQUE_LENGTHS = (5, 4, 3, 2)
PREFERRED_RESIDUE = {2: 0, 3: 2, 4: 0, 5: 3}

BITS = tuple(1 << i for i in range(NUM_CELLS))
MASK64 = (1 << 64) - 1


def _build_geometry():
    neighbors = []
    center_score = []
    for idx in range(NUM_CELLS):
        r, c = divmod(idx, N)
        ns = []
        if r > 0:
            ns.append(idx - N)
        if r < N - 1:
            ns.append(idx + N)
        if c > 0:
            ns.append(idx - 1)
        if c < N - 1:
            ns.append(idx + 1)
        neighbors.append(tuple(ns))

        # Higher near the center. Used only as a tie-breaker / fallback.
        center_score.append(200 - ((2 * r - 9) ** 2 + (2 * c - 9) ** 2))
    return tuple(neighbors), tuple(center_score)


NEIGHBORS, CENTER_SCORE = _build_geometry()


def _build_placements():
    placements = {2: [], 3: [], 4: [], 5: []}

    for length in placements:
        # Horizontal placements
        for r in range(N):
            for c in range(N - length + 1):
                cells = tuple(r * N + c + k for k in range(length))
                mask = 0
                for idx in cells:
                    mask |= BITS[idx]
                placements[length].append((mask, cells, HORIZONTAL))

        # Vertical placements
        for r in range(N - length + 1):
            for c in range(N):
                cells = tuple((r + k) * N + c for k in range(length))
                mask = 0
                for idx in cells:
                    mask |= BITS[idx]
                placements[length].append((mask, cells, VERTICAL))

    return placements


PLACEMENTS_BY_LEN = _build_placements()

TARGET_POWER = [1]
for _ in range(1, 18):
    TARGET_POWER.append(TARGET_POWER[-1] * 14)


def _fresh_counts():
    return {5: 1, 4: 1, 3: 2, 2: 1}


def _noise(idx, salt):
    x = (salt + (idx + 1) * 0x9E3779B97F4A7C15) & MASK64
    x ^= x >> 30
    x = (x * 0xBF58476D1CE4E5B9) & MASK64
    x ^= x >> 27
    x = (x * 0x94D049BB133111EB) & MASK64
    x ^= x >> 31
    return x & MASK64


def _neighbor_count(idx, mask):
    count = 0
    for nb in NEIGHBORS[idx]:
        if mask & BITS[nb]:
            count += 1
    return count


def _find_components(hit_mask):
    comp_id = [-1] * NUM_CELLS
    comps = []

    for start in range(NUM_CELLS):
        if not (hit_mask & BITS[start]) or comp_id[start] != -1:
            continue

        cid = len(comps)
        stack = [start]
        comp_id[start] = cid
        cells = []
        mask = 0

        while stack:
            idx = stack.pop()
            cells.append(idx)
            mask |= BITS[idx]

            for nb in NEIGHBORS[idx]:
                if (hit_mask & BITS[nb]) and comp_id[nb] == -1:
                    comp_id[nb] = cid
                    stack.append(nb)

        cells.sort()
        size = len(cells)

        if size > 1:
            row0 = cells[0] // N
            col0 = cells[0] % N
            if all(cell // N == row0 for cell in cells):
                orient = HORIZONTAL
            elif all(cell % N == col0 for cell in cells):
                orient = VERTICAL
            else:
                orient = ANY_ORIENT
        else:
            orient = ANY_ORIENT

        comps.append((mask, tuple(cells), size, orient))

    return comps, comp_id


def _placement_extends_component(length, orient, comp_mask, miss_mask, sunk_mask):
    for pmask, _cells, porient in PLACEMENTS_BY_LEN[length]:
        if porient != orient:
            continue
        if pmask & miss_mask:
            continue
        if pmask & sunk_mask:
            continue
        if (pmask & comp_mask) == comp_mask:
            return True
    return False


def _infer_sunk_components(comps, miss_mask):
    counts = _fresh_counts()
    sunk_flags = [False] * len(comps)
    sunk_mask = 0

    if not comps:
        return counts, sunk_flags, sunk_mask

    # Larger confirmed segments first; this helps remove carrier/battleship info early.
    order = sorted(range(len(comps)), key=lambda i: comps[i][2], reverse=True)

    changed = True
    while changed:
        changed = False

        for ci in order:
            if sunk_flags[ci]:
                continue

            comp_mask, _cells, size, orient = comps[ci]

            if orient not in (HORIZONTAL, VERTICAL):
                continue
            if size < 2 or size > 5:
                continue
            if counts.get(size, 0) <= 0:
                continue

            can_extend = False
            if size < 5:
                for length in UNIQUE_LENGTHS:
                    if length <= size or counts.get(length, 0) <= 0:
                        continue
                    if _placement_extends_component(
                        length, orient, comp_mask, miss_mask, sunk_mask
                    ):
                        can_extend = True
                        break

            # A length-5 straight component is complete. Smaller straight components
            # are considered complete when no remaining longer ship can legally fit.
            if size == 5 or not can_extend:
                sunk_flags[ci] = True
                sunk_mask |= comp_mask
                counts[size] -= 1
                changed = True

    return counts, sunk_flags, sunk_mask


def _target_scores(
    unknown_mask,
    miss_mask,
    hit_mask,
    comps,
    comp_id,
    counts,
    sunk_flags,
    sunk_mask,
):
    scores = [0] * NUM_CELLS
    unsunk_hit_mask = hit_mask & ~sunk_mask

    if not unsunk_hit_mask:
        return scores

    blocked = miss_mask | sunk_mask

    for length in UNIQUE_LENGTHS:
        ship_count = counts.get(length, 0)
        if ship_count <= 0:
            continue

        length_weight = ship_count * (length + 1)

        for pmask, cells, porient in PLACEMENTS_BY_LEN[length]:
            if pmask & blocked:
                continue
            if not (pmask & unsunk_hit_mask):
                continue
            if not (pmask & unknown_mask):
                continue

            comp_counts = {}
            hit_cells = []
            ok = True

            for idx in cells:
                if hit_mask & BITS[idx]:
                    cid = comp_id[idx]
                    if cid < 0 or sunk_flags[cid]:
                        ok = False
                        break
                    comp_counts[cid] = comp_counts.get(cid, 0) + 1
                    hit_cells.append(idx)

            if not ok or not hit_cells:
                continue

            covered_hits = 0

            for cid, count in comp_counts.items():
                _cmask, _ccells, csize, corient = comps[cid]

                # Once adjacent hits reveal a straight direction, only consider
                # placements that include the whole straight component.
                if corient in (HORIZONTAL, VERTICAL) and csize > 1:
                    if porient != corient or count != csize:
                        ok = False
                        break
                    covered_hits += csize
                else:
                    covered_hits += count

            if not ok or covered_hits <= 0:
                continue

            base_weight = length_weight * TARGET_POWER[covered_hits]

            for idx in cells:
                if not (unknown_mask & BITS[idx]):
                    continue

                r, c = divmod(idx, N)
                best_dist = 99
                for h in hit_cells:
                    hr, hc = divmod(h, N)
                    dist = abs(r - hr) + abs(c - hc)
                    if dist < best_dist:
                        best_dist = dist

                proximity = 7 - best_dist
                if proximity < 1:
                    proximity = 1

                scores[idx] += base_weight * proximity

    return scores


def _hunt_scores(unknown_mask, miss_mask, hit_mask, counts):
    scores = [0] * NUM_CELLS

    # During pure hunting, already-hit cells are occupied by known ships, so
    # remaining unknown ship cells cannot overlap them.
    blocked = miss_mask | hit_mask

    for length in UNIQUE_LENGTHS:
        ship_count = counts.get(length, 0)
        if ship_count <= 0:
            continue

        weight = ship_count * length

        for pmask, cells, _orient in PLACEMENTS_BY_LEN[length]:
            if pmask & blocked:
                continue

            for idx in cells:
                if unknown_mask & BITS[idx]:
                    scores[idx] += weight

    return scores


def _choose_target(scores, unknown_indices, unknown_mask, hit_mask, salt):
    best_idx = None
    best_key = None

    for idx in unknown_indices:
        score = scores[idx]
        if score <= 0:
            continue

        key = (
            score,
            _neighbor_count(idx, hit_mask),
            CENTER_SCORE[idx],
            _neighbor_count(idx, unknown_mask),
            _noise(idx, salt),
        )

        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return best_idx


def _choose_hunt(scores, unknown_indices, unknown_mask, counts, salt):
    if not unknown_indices:
        return None

    active_lengths = [length for length in UNIQUE_LENGTHS if counts.get(length, 0) > 0]
    step = min(active_lengths) if active_lengths else 2
    if step < 2:
        step = 2

    global_max = max(scores[idx] for idx in unknown_indices)
    residue = PREFERRED_RESIDUE.get(step, 0) % step

    pattern_indices = [
        idx for idx in unknown_indices if ((idx // N + idx % N) % step) == residue
    ]

    candidates = unknown_indices
    if pattern_indices:
        pattern_max = max(scores[idx] for idx in pattern_indices)
        # Prefer a guaranteed modulo hunting pattern, unless inference made that
        # pattern useless while other legal placements still have probability.
        if pattern_max > 0 or global_max == 0:
            candidates = pattern_indices

    best_idx = None
    best_key = None

    for idx in candidates:
        key = (
            scores[idx],
            CENTER_SCORE[idx],
            _neighbor_count(idx, unknown_mask),
            _noise(idx, salt),
        )

        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return best_idx


def _fallback_choice(unknown_indices, unknown_mask, hit_mask, salt):
    best_idx = None
    best_key = None

    for idx in unknown_indices:
        key = (
            _neighbor_count(idx, hit_mask),
            CENTER_SCORE[idx],
            _neighbor_count(idx, unknown_mask),
            _noise(idx, salt),
        )
        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx

    return best_idx


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        miss_mask = 0
        hit_mask = 0
        unknown_mask = 0
        unknown_indices = []

        for r in range(N):
            row = board[r]
            for c in range(N):
                idx = r * N + c
                value = row[c]

                if value == 0:
                    unknown_mask |= BITS[idx]
                    unknown_indices.append(idx)
                elif value == 1:
                    hit_mask |= BITS[idx]
                else:
                    miss_mask |= BITS[idx]

        if not unknown_indices:
            return (0, 0)

        salt = (
            miss_mask * 0x9E3779B97F4A7C15
            + hit_mask * 0xBF58476D1CE4E5B9
        ) & MASK64

        comps, comp_id = _find_components(hit_mask)
        counts, sunk_flags, sunk_mask = _infer_sunk_components(comps, miss_mask)

        # Target mode: exploit known hits first.
        t_scores = _target_scores(
            unknown_mask,
            miss_mask,
            hit_mask,
            comps,
            comp_id,
            counts,
            sunk_flags,
            sunk_mask,
        )
        target = _choose_target(t_scores, unknown_indices, unknown_mask, hit_mask, salt)

        if target is not None:
            r, c = divmod(target, N)
            if board[r][c] == 0:
                return (r, c)

        # Hunt mode: probability density over all remaining legal ship placements.
        h_scores = _hunt_scores(unknown_mask, miss_mask, hit_mask, counts)
        hunt = _choose_hunt(h_scores, unknown_indices, unknown_mask, counts, salt)

        if hunt is not None:
            r, c = divmod(hunt, N)
            if board[r][c] == 0:
                return (r, c)

        # Final safety fallback.
        fallback = _fallback_choice(unknown_indices, unknown_mask, hit_mask, salt)
        if fallback is not None:
            r, c = divmod(fallback, N)
            if board[r][c] == 0:
                return (r, c)

    except Exception:
        pass

    # Absolute safety fallback: return the first legal unknown cell.
    for r in range(10):
        for c in range(10):
            try:
                if board[r][c] == 0:
                    return (r, c)
            except Exception:
                continue

    return (0, 0)
