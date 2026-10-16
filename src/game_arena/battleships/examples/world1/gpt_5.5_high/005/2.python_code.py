
# Battleship policy for a 10x10 board.
# Required API:
#     def policy(board: list[list[int]]) -> tuple[int, int]

N = 10
ALL_MASK = (1 << 100) - 1

# Fleet: carrier, battleship, cruiser, submarine, destroyer
BASE_COUNTS = {5: 1, 4: 1, 3: 2, 2: 1}
SHIP_LENGTHS = (5, 4, 3, 3, 2)

_BITS = [1 << i for i in range(100)]
_ALL_PLACEMENTS = None
_PLACEMENTS_BY_LEN = None


def _init():
    global _ALL_PLACEMENTS, _PLACEMENTS_BY_LEN
    if _ALL_PLACEMENTS is not None:
        return

    by_len = {2: [], 3: [], 4: [], 5: []}
    all_places = []

    for L in (2, 3, 4, 5):
        # Horizontal placements
        for r in range(N):
            for c in range(N - L + 1):
                cells = tuple(r * N + (c + k) for k in range(L))
                mask = 0
                for idx in cells:
                    mask |= _BITS[idx]
                entry = (L, mask, cells, "H")
                by_len[L].append(entry)
                all_places.append(entry)

        # Vertical placements
        for r in range(N - L + 1):
            for c in range(N):
                cells = tuple((r + k) * N + c for k in range(L))
                mask = 0
                for idx in cells:
                    mask |= _BITS[idx]
                entry = (L, mask, cells, "V")
                by_len[L].append(entry)
                all_places.append(entry)

    _PLACEMENTS_BY_LEN = by_len
    _ALL_PLACEMENTS = all_places


def _iter_bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def _fallback(board):
    try:
        for r in range(len(board)):
            row = board[r]
            for c in range(len(row)):
                if row[c] == 0 and 0 <= r < 10 and 0 <= c < 10:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)


def _components_from_mask(mask):
    comps = []
    seen = 0

    for start in _iter_bits(mask):
        bit = _BITS[start]
        if seen & bit:
            continue

        comp = []
        stack = [start]
        seen |= bit

        while stack:
            idx = stack.pop()
            comp.append(idx)
            r, c = divmod(idx, N)

            if r > 0:
                nb = idx - N
                b = _BITS[nb]
                if (mask & b) and not (seen & b):
                    seen |= b
                    stack.append(nb)
            if r < N - 1:
                nb = idx + N
                b = _BITS[nb]
                if (mask & b) and not (seen & b):
                    seen |= b
                    stack.append(nb)
            if c > 0:
                nb = idx - 1
                b = _BITS[nb]
                if (mask & b) and not (seen & b):
                    seen |= b
                    stack.append(nb)
            if c < N - 1:
                nb = idx + 1
                b = _BITS[nb]
                if (mask & b) and not (seen & b):
                    seen |= b
                    stack.append(nb)

        comps.append(comp)

    return comps


def _analyze_hits(board, hit_mask):
    """
    Returns:
      active_hit_mask: hits still worth targeting
      finished_mask: hits that appear to form completed ships
      counts: estimated remaining ship counts
      comp_id_by_idx: component id for active hits
      comp_constraints: for active straight components, required orientation/mask
    """
    counts = dict(BASE_COUNTS)
    finished_mask = 0

    components = _components_from_mask(hit_mask)

    # Temporary component ids before removing finished components.
    raw_comp_id = [-1] * 100
    for cid, comp in enumerate(components):
        for idx in comp:
            raw_comp_id[idx] = cid

    finished_components = set()

    for cid, comp in enumerate(components):
        size = len(comp)
        rows = {idx // N for idx in comp}
        cols = {idx % N for idx in comp}

        orient = None
        if size >= 2 and len(rows) == 1:
            orient = "H"
        elif size >= 2 and len(cols) == 1:
            orient = "V"

        finished = False

        # Straight contiguous hit run that cannot be extended is probably sunk.
        # A length-5 straight run is always complete because no ship is longer.
        if orient is not None and size in BASE_COUNTS:
            if size == 5:
                finished = True
            else:
                if orient == "H":
                    r = next(iter(rows))
                    cs = [idx % N for idx in comp]
                    cmin, cmax = min(cs), max(cs)
                    open_end = False
                    if cmin - 1 >= 0 and board[r][cmin - 1] == 0:
                        open_end = True
                    if cmax + 1 < N and board[r][cmax + 1] == 0:
                        open_end = True
                    if not open_end:
                        finished = True
                else:
                    c = next(iter(cols))
                    rs = [idx // N for idx in comp]
                    rmin, rmax = min(rs), max(rs)
                    open_end = False
                    if rmin - 1 >= 0 and board[rmin - 1][c] == 0:
                        open_end = True
                    if rmax + 1 < N and board[rmax + 1][c] == 0:
                        open_end = True
                    if not open_end:
                        finished = True

        if finished:
            finished_components.add(cid)
            for idx in comp:
                finished_mask |= _BITS[idx]
            if counts.get(size, 0) > 0:
                counts[size] -= 1

    active_hit_mask = hit_mask & ~finished_mask

    # Rebuild active component ids and orientation constraints.
    active_components = _components_from_mask(active_hit_mask)
    comp_id_by_idx = [-1] * 100
    comp_constraints = {}

    for cid, comp in enumerate(active_components):
        cmask = 0
        for idx in comp:
            comp_id_by_idx[idx] = cid
            cmask |= _BITS[idx]

        size = len(comp)
        rows = {idx // N for idx in comp}
        cols = {idx % N for idx in comp}

        if 2 <= size <= 5 and len(rows) == 1:
            comp_constraints[cid] = ("H", cmask)
        elif 2 <= size <= 5 and len(cols) == 1:
            comp_constraints[cid] = ("V", cmask)

    return active_hit_mask, finished_mask, counts, comp_id_by_idx, comp_constraints


def _candidate_allowed(mask, orient, hp, comp_id_by_idx, comp_constraints):
    checked = set()
    m = hp

    while m:
        bit = m & -m
        idx = bit.bit_length() - 1
        m ^= bit

        cid = comp_id_by_idx[idx]
        if cid < 0 or cid in checked:
            continue
        checked.add(cid)

        if cid in comp_constraints:
            req_orient, req_mask = comp_constraints[cid]
            if orient != req_orient:
                return False
            if (mask & req_mask) != req_mask:
                return False

    return True


def _configuration_scores(candidates, by_hit, active_hit_mask, counts):
    """
    Approximate enumeration of ways to cover all active hits with remaining ships.
    This is capped for speed and used as a probability-like target refinement.
    """
    scores = [0.0] * 100
    total_weight = 0.0
    nodes = 0
    leaves = 0

    MAX_NODES = 180000
    MAX_LEAVES = 40000

    selected_unknown_masks = []

    def avail_count(L, c2, c3, c4, c5):
        if L == 2:
            return c2
        if L == 3:
            return c3
        if L == 4:
            return c4
        return c5

    def dec_counts(L, c2, c3, c4, c5):
        if L == 2:
            return c2 - 1, c3, c4, c5
        if L == 3:
            return c2, c3 - 1, c4, c5
        if L == 4:
            return c2, c3, c4 - 1, c5
        return c2, c3, c4, c5 - 1

    def dfs(rem, occupied, c2, c3, c4, c5, weight):
        nonlocal total_weight, nodes, leaves

        if nodes >= MAX_NODES or leaves >= MAX_LEAVES:
            return
        nodes += 1

        if rem == 0:
            leaves += 1
            total_weight += weight
            for um in selected_unknown_masks:
                m = um
                while m:
                    bit = m & -m
                    idx = bit.bit_length() - 1
                    scores[idx] += weight
                    m ^= bit
            return

        # Quick capacity prune.
        if rem.bit_count() > (2 * c2 + 3 * c3 + 4 * c4 + 5 * c5):
            return

        # Pick the remaining hit with the fewest feasible covering placements.
        best_idx = -1
        best_list = None
        best_len = 10 ** 9

        m = rem
        while m:
            bit = m & -m
            idx = bit.bit_length() - 1
            m ^= bit

            feasible = []
            for cid in by_hit.get(idx, ()):
                L, pmask, _cells, _orient, hp, _um = candidates[cid]
                if pmask & occupied:
                    continue
                if avail_count(L, c2, c3, c4, c5) <= 0:
                    continue
                feasible.append(cid)

            flen = len(feasible)
            if flen == 0:
                return
            if flen < best_len:
                best_len = flen
                best_idx = idx
                best_list = feasible
                if flen == 1:
                    break

        if best_idx < 0 or not best_list:
            return

        for cid in best_list:
            if nodes >= MAX_NODES or leaves >= MAX_LEAVES:
                return

            L, pmask, _cells, _orient, hp, um = candidates[cid]
            available = avail_count(L, c2, c3, c4, c5)
            if available <= 0 or (pmask & occupied):
                continue

            nc2, nc3, nc4, nc5 = dec_counts(L, c2, c3, c4, c5)

            selected_unknown_masks.append(um)
            dfs(rem & ~hp, occupied | pmask, nc2, nc3, nc4, nc5, weight * available)
            selected_unknown_masks.pop()

    dfs(
        active_hit_mask,
        0,
        counts.get(2, 0),
        counts.get(3, 0),
        counts.get(4, 0),
        counts.get(5, 0),
        1.0,
    )

    return scores, total_weight


def _add_tactical_scores(scores, board, active_hit_mask):
    """Simple local target bonuses around active hit components."""
    for comp in _components_from_mask(active_hit_mask):
        size = len(comp)

        if size == 1:
            idx = comp[0]
            r, c = divmod(idx, N)
            for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                    scores[nr * N + nc] += 25.0
            continue

        rows = {idx // N for idx in comp}
        cols = {idx % N for idx in comp}

        if len(rows) == 1:
            r = next(iter(rows))
            cs = [idx % N for idx in comp]
            cmin, cmax = min(cs), max(cs)
            bonus = 70.0 + 15.0 * size

            if cmin - 1 >= 0 and board[r][cmin - 1] == 0:
                scores[r * N + (cmin - 1)] += bonus
            if cmax + 1 < N and board[r][cmax + 1] == 0:
                scores[r * N + (cmax + 1)] += bonus

        elif len(cols) == 1:
            c = next(iter(cols))
            rs = [idx // N for idx in comp]
            rmin, rmax = min(rs), max(rs)
            bonus = 70.0 + 15.0 * size

            if rmin - 1 >= 0 and board[rmin - 1][c] == 0:
                scores[(rmin - 1) * N + c] += bonus
            if rmax + 1 < N and board[rmax + 1][c] == 0:
                scores[(rmax + 1) * N + c] += bonus

        else:
            # Irregular cluster: be conservative and probe neighboring unknowns.
            for idx in comp:
                r, c = divmod(idx, N)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0:
                        scores[nr * N + nc] += 8.0


def _target_scores(board, miss_mask, hit_mask, active_hit_mask, finished_mask, counts,
                   comp_id_by_idx, comp_constraints):
    scores = [0.0] * 100
    if active_hit_mask == 0:
        return scores

    known_ship_mask = hit_mask
    unknown_mask = ALL_MASK & ~(miss_mask | known_ship_mask)
    block_mask = miss_mask | finished_mask

    candidates = []
    by_hit = {}

    # Direct placement scoring.
    for L, mask, cells, orient in _ALL_PLACEMENTS:
        multiplicity = counts.get(L, 0)
        if multiplicity <= 0:
            continue
        if mask & block_mask:
            continue

        hp = mask & active_hit_mask
        if not hp:
            continue

        if not _candidate_allowed(mask, orient, hp, comp_id_by_idx, comp_constraints):
            continue

        um = mask & unknown_mask

        cid = len(candidates)
        candidates.append((L, mask, cells, orient, hp, um))

        for hidx in _iter_bits(hp):
            by_hit.setdefault(hidx, []).append(cid)

        if um:
            hc = hp.bit_count()
            # Strongly prefer placements explaining multiple aligned hits.
            w = multiplicity * (hc ** 3) * (1.0 + 0.03 * L)
            for idx in _iter_bits(um):
                scores[idx] += w

    for hidx, ids in by_hit.items():
        ids.sort(
            key=lambda cid: (
                -candidates[cid][4].bit_count(),
                candidates[cid][5].bit_count(),
                -candidates[cid][0],
            )
        )

    # Approximate global consistency refinement.
    if candidates:
        cfg_scores, total = _configuration_scores(candidates, by_hit, active_hit_mask, counts)
        if total > 0:
            for i in range(100):
                if cfg_scores[i] > 0:
                    scores[i] += 60.0 * (cfg_scores[i] / total)

    _add_tactical_scores(scores, board, active_hit_mask)
    return scores


def _hunt_scores(miss_mask, hit_mask, counts):
    """Probability map for finding ships not already hit."""
    scores = [0.0] * 100
    block = miss_mask | hit_mask

    for L in (5, 4, 3, 2):
        cnt = counts.get(L, 0)
        if cnt <= 0:
            continue

        valid = []
        for entry in _PLACEMENTS_BY_LEN[L]:
            _L, mask, _cells, _orient = entry
            if not (mask & block):
                valid.append(entry)

        if not valid:
            continue

        # Normalize per ship length so constrained ships matter.
        w = float(cnt) / float(len(valid))
        for _L, _mask, cells, _orient in valid:
            for idx in cells:
                scores[idx] += w

    return scores


def _openness(board, idx):
    r, c = divmod(idx, N)
    total = 0

    # Count nearby unknown runway length in four directions.
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        steps = 0
        while 0 <= nr < N and 0 <= nc < N and board[nr][nc] == 0 and steps < 4:
            total += 1
            steps += 1
            nr += dr
            nc += dc

    return total


def _choose_cell(board, unknowns, scores, use_parity):
    candidates = unknowns

    if use_parity and unknowns:
        parity_sum = [0.0, 0.0]
        parity_count = [0, 0]

        for idx in unknowns:
            r, c = divmod(idx, N)
            p = (r + c) & 1
            parity_sum[p] += max(scores[idx], 0.0)
            parity_count[p] += 1

        preferred = 0 if parity_sum[0] >= parity_sum[1] else 1
        parity_candidates = []
        for idx in unknowns:
            r, c = divmod(idx, N)
            if ((r + c) & 1) == preferred:
                parity_candidates.append(idx)

        if parity_candidates:
            candidates = parity_candidates

    best = candidates[0]
    best_key = None

    for idx in candidates:
        r, c = divmod(idx, N)
        # Center preference for ties.
        center = -((r - 4.5) * (r - 4.5) + (c - 4.5) * (c - 4.5))
        open_score = _openness(board, idx)
        key = (scores[idx], center, open_score, -idx)

        if best_key is None or key > best_key:
            best_key = key
            best = idx

    return divmod(best, N)


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        _init()

        miss_mask = 0
        hit_mask = 0
        unknowns = []

        for r in range(N):
            row = board[r]
            for c in range(N):
                v = row[c]
                idx = r * N + c
                if v == 0:
                    unknowns.append(idx)
                elif v == 1:
                    hit_mask |= _BITS[idx]
                else:
                    miss_mask |= _BITS[idx]

        if not unknowns:
            return (0, 0)

        active_hit_mask, finished_mask, counts, comp_id_by_idx, comp_constraints = _analyze_hits(
            board, hit_mask
        )

        # Target mode: finish likely active ships.
        target = _target_scores(
            board,
            miss_mask,
            hit_mask,
            active_hit_mask,
            finished_mask,
            counts,
            comp_id_by_idx,
            comp_constraints,
        )

        max_target = max(target[idx] for idx in unknowns)

        if max_target > 1e-12:
            hunt = _hunt_scores(miss_mask, hit_mask, counts)
            combined = [0.0] * 100
            for idx in unknowns:
                combined[idx] = target[idx] * 1000000.0 + hunt[idx]
            move = _choose_cell(board, unknowns, combined, use_parity=False)
        else:
            # Hunt mode: probability heat map plus checkerboard search.
            hunt = _hunt_scores(miss_mask, hit_mask, counts)

            # If every score is zero, legal fallback scoring still chooses a central unknown.
            move = _choose_cell(board, unknowns, hunt, use_parity=True)

        r, c = move
        if 0 <= r < N and 0 <= c < N and board[r][c] == 0:
            return (r, c)

    except Exception:
        pass

    return _fallback(board)
