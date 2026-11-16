
N = 10
SIZE = N * N
FLEET = (5, 4, 3, 3, 2)

_BITS = [1 << i for i in range(SIZE)]
_PLACEMENTS = {}
_ADJ = []
_READY = False

_MAX_DP_HITS = 13
_MAX_DP_STATES = 12000


def _init():
    global _READY, _PLACEMENTS, _ADJ
    if _READY:
        return

    _ADJ = [[] for _ in range(SIZE)]
    for r in range(N):
        for c in range(N):
            i = r * N + c
            if r > 0:
                _ADJ[i].append(i - N)
            if r < N - 1:
                _ADJ[i].append(i + N)
            if c > 0:
                _ADJ[i].append(i - 1)
            if c < N - 1:
                _ADJ[i].append(i + 1)

    for L in set(FLEET):
        placements = []

        for r in range(N):
            for c in range(N - L + 1):
                cells = tuple(r * N + c + k for k in range(L))
                mask = 0
                for idx in cells:
                    mask |= _BITS[idx]
                placements.append((mask, cells))

        for c in range(N):
            for r in range(N - L + 1):
                cells = tuple((r + k) * N + c for k in range(L))
                mask = 0
                for idx in cells:
                    mask |= _BITS[idx]
                placements.append((mask, cells))

        _PLACEMENTS[L] = placements

    _READY = True


def _first_unknown(board):
    for r in range(N):
        try:
            row = board[r]
        except Exception:
            continue
        for c in range(N):
            try:
                if row[c] == 0:
                    return (r, c)
            except Exception:
                pass
    return (0, 0)


def _board_masks(board):
    miss = 0
    hit = 0
    unknown = 0

    for r in range(N):
        row = board[r]
        base = r * N
        for c in range(N):
            idx = base + c
            v = row[c]
            if v == 0:
                unknown |= _BITS[idx]
            elif v == 1:
                hit |= _BITS[idx]
            elif v == -1:
                miss |= _BITS[idx]

    return miss, hit, unknown


def _components(mask):
    comps = []
    remaining = mask

    while remaining:
        b = remaining & -remaining
        idx = b.bit_length() - 1
        remaining ^= b

        stack = [idx]
        cells = [idx]
        comp_mask = b

        while stack:
            cur = stack.pop()
            for nb in _ADJ[cur]:
                nb_bit = _BITS[nb]
                if remaining & nb_bit:
                    remaining ^= nb_bit
                    comp_mask |= nb_bit
                    stack.append(nb)
                    cells.append(nb)

        comps.append((comp_mask, cells))

    return comps


def _line_info(cells, board):
    n = len(cells)
    if n < 2:
        return False, False

    r0 = cells[0] // N
    c0 = cells[0] % N

    same_r = True
    same_c = True
    min_r = max_r = r0
    min_c = max_c = c0

    for idx in cells[1:]:
        r = idx // N
        c = idx % N

        if r != r0:
            same_r = False
        if c != c0:
            same_c = False

        if r < min_r:
            min_r = r
        if r > max_r:
            max_r = r
        if c < min_c:
            min_c = c
        if c > max_c:
            max_c = c

    if same_r:
        if max_c - min_c + 1 != n:
            return False, False
        before_open = min_c > 0 and board[r0][min_c - 1] == 0
        after_open = max_c < N - 1 and board[r0][max_c + 1] == 0
        return True, (not before_open and not after_open)

    if same_c:
        if max_r - min_r + 1 != n:
            return False, False
        before_open = min_r > 0 and board[min_r - 1][c0] == 0
        after_open = max_r < N - 1 and board[max_r + 1][c0] == 0
        return True, (not before_open and not after_open)

    return False, False


def _infer_solved(board, hit_mask):
    remaining = list(FLEET)
    solved = 0
    changed = True

    while changed and remaining:
        changed = False
        active_hits = hit_mask & ~solved
        comps = _components(active_hits)
        comps.sort(key=lambda x: len(x[1]), reverse=True)

        max_remaining = max(remaining)

        for comp_mask, cells in comps:
            n = len(cells)
            if n not in remaining:
                continue

            is_line, closed = _line_info(cells, board)
            if not is_line:
                continue

            if n == max_remaining or (n >= 2 and closed):
                solved |= comp_mask
                remaining.remove(n)
                changed = True
                break

    return solved, remaining


def _dp_heat(miss_mask, active_mask, solved_mask, unknown_mask, remaining_lengths):
    if not active_mask or not remaining_lengths:
        return None

    cell_to_hbit = {}
    tmp = active_mask
    h = 0
    while tmp:
        b = tmp & -tmp
        idx = b.bit_length() - 1
        cell_to_hbit[idx] = 1 << h
        h += 1
        tmp ^= b

    if h > _MAX_DP_HITS:
        return None

    all_hits = (1 << h) - 1
    blocked = miss_mask | solved_mask

    cache = {}
    for L in set(remaining_lengths):
        options = []
        counts = {}

        for pmask, cells in _PLACEMENTS[L]:
            if pmask & blocked:
                continue

            cover = 0
            for idx in cells:
                cover |= cell_to_hbit.get(idx, 0)

            options.append((cover, cells))
            counts[cover] = counts.get(cover, 0) + 1

        if not options:
            return None

        cache[L] = (options, list(counts.items()))

    lengths = list(remaining_lengths)
    nships = len(lengths)
    ship_options = [cache[L][0] for L in lengths]
    ship_counts = [cache[L][1] for L in lengths]

    fwd = [None] * (nships + 1)
    fwd[0] = {0: 1}

    for i in range(nships):
        cur = fwd[i]
        new = {}
        counts = ship_counts[i]

        for mask, ways in cur.items():
            for cover, num_opts in counts:
                if mask & cover:
                    continue
                nm = mask | cover
                new[nm] = new.get(nm, 0) + ways * num_opts

        if len(new) > _MAX_DP_STATES:
            return None
        fwd[i + 1] = new

    if fwd[nships].get(all_hits, 0) == 0:
        return None

    bwd = [None] * (nships + 1)
    bwd[nships] = {0: 1}

    for i in range(nships - 1, -1, -1):
        cur = bwd[i + 1]
        new = {}
        counts = ship_counts[i]

        for mask, ways in cur.items():
            for cover, num_opts in counts:
                if mask & cover:
                    continue
                nm = mask | cover
                new[nm] = new.get(nm, 0) + ways * num_opts

        if len(new) > _MAX_DP_STATES:
            return None
        bwd[i] = new

    heat = [0] * SIZE

    for i in range(nships):
        ways_by_cover = {}
        prefix = fwd[i]
        suffix = bwd[i + 1]

        for cover, _ in ship_counts[i]:
            total = 0
            for pre_mask, pre_ways in prefix.items():
                if pre_mask & cover:
                    continue
                need = all_hits ^ (pre_mask | cover)
                suf_ways = suffix.get(need, 0)
                if suf_ways:
                    total += pre_ways * suf_ways
            ways_by_cover[cover] = total

        for cover, cells in ship_options[i]:
            w = ways_by_cover.get(cover, 0)
            if not w:
                continue
            for idx in cells:
                if unknown_mask & _BITS[idx]:
                    heat[idx] += w

    return heat


def _hunt_heat(miss_mask, hit_mask, unknown_mask, remaining_lengths):
    lengths = remaining_lengths if remaining_lengths else FLEET
    blocked = miss_mask | hit_mask
    heat = [0.0] * SIZE

    for L in lengths:
        valid = []
        for pmask, cells in _PLACEMENTS[L]:
            if not (pmask & blocked):
                valid.append(cells)

        total = len(valid)
        if total == 0:
            continue

        w = 1.0 / total
        for cells in valid:
            for idx in cells:
                if unknown_mask & _BITS[idx]:
                    heat[idx] += w

    return heat


def _all_zero(heat, unknown_mask):
    tmp = unknown_mask
    while tmp:
        b = tmp & -tmp
        idx = b.bit_length() - 1
        if heat[idx] > 0:
            return False
        tmp ^= b
    return True


def _boost_runs(target, active_mask, unknown_mask, remaining_lengths):
    max_len = max(remaining_lengths) if remaining_lengths else 5

    for _, cells in _components(active_mask):
        n = len(cells)

        if n == 1:
            idx = cells[0]
            for nb in _ADJ[idx]:
                if unknown_mask & _BITS[nb]:
                    target[nb] += 25.0
            continue

        rows = [idx // N for idx in cells]
        cols = [idx % N for idx in cells]

        if all(r == rows[0] for r in rows):
            r = rows[0]
            lo = min(cols)
            hi = max(cols)
            if hi - lo + 1 == n and n < max_len:
                if lo > 0:
                    idx = r * N + lo - 1
                    if unknown_mask & _BITS[idx]:
                        target[idx] += 80.0 * n * n
                if hi < N - 1:
                    idx = r * N + hi + 1
                    if unknown_mask & _BITS[idx]:
                        target[idx] += 80.0 * n * n
            continue

        if all(c == cols[0] for c in cols):
            c = cols[0]
            lo = min(rows)
            hi = max(rows)
            if hi - lo + 1 == n and n < max_len:
                if lo > 0:
                    idx = (lo - 1) * N + c
                    if unknown_mask & _BITS[idx]:
                        target[idx] += 80.0 * n * n
                if hi < N - 1:
                    idx = (hi + 1) * N + c
                    if unknown_mask & _BITS[idx]:
                        target[idx] += 80.0 * n * n
            continue

        for idx in cells:
            for nb in _ADJ[idx]:
                if unknown_mask & _BITS[nb]:
                    target[nb] += 10.0


def _fallback_heat(miss_mask, hit_mask, active_mask, solved_mask, unknown_mask, remaining_lengths):
    lengths = remaining_lengths if remaining_lengths else FLEET
    blocked = miss_mask | solved_mask

    target = [0.0] * SIZE
    hunt = [0.0] * SIZE

    for L in lengths:
        valid = []
        for pmask, cells in _PLACEMENTS[L]:
            if not (pmask & blocked):
                valid.append((pmask, cells))

        total = len(valid)
        if total == 0:
            continue

        hunt_w = 1.0 / total

        for pmask, cells in valid:
            h = (pmask & active_mask).bit_count()

            if h:
                w = (h * h * h) * (1.0 + 0.2 * L)
                for idx in cells:
                    if unknown_mask & _BITS[idx]:
                        target[idx] += w
            else:
                for idx in cells:
                    if unknown_mask & _BITS[idx]:
                        hunt[idx] += hunt_w

    if not _all_zero(target, unknown_mask):
        _boost_runs(target, active_mask, unknown_mask, lengths)
        return [target[i] * 1000.0 + hunt[i] for i in range(SIZE)], True

    return _hunt_heat(miss_mask, hit_mask, unknown_mask, lengths), False


def _best_index(heat, unknown_mask, active_mask=0, k=0, residue=0):
    best = -1
    best_key = None
    tmp = unknown_mask

    while tmp:
        b = tmp & -tmp
        idx = b.bit_length() - 1
        tmp ^= b

        r = idx // N
        c = idx - r * N

        if k and ((r + c) % k) != residue:
            continue

        adj = 0
        if active_mask:
            for nb in _ADJ[idx]:
                if active_mask & _BITS[nb]:
                    adj += 1

        dist = abs(2 * r - (N - 1)) + abs(2 * c - (N - 1))
        key = (heat[idx], adj, -dist, -idx)

        if best_key is None or key > best_key:
            best_key = key
            best = idx

    return best


def _choose_hunt(heat, unknown_mask, remaining_lengths):
    global_idx = _best_index(heat, unknown_mask)
    if global_idx < 0:
        return -1

    global_val = heat[global_idx]

    k = min(remaining_lengths) if remaining_lengths else 2
    if k < 2:
        k = 2
    if k > 5:
        k = 2

    preferred = _best_index(heat, unknown_mask, 0, k, 0)
    if preferred >= 0:
        preferred_val = heat[preferred]
        if global_val <= 0 or preferred_val >= 0.55 * global_val:
            return preferred

    sums = [0.0] * k
    tmp = unknown_mask
    while tmp:
        b = tmp & -tmp
        idx = b.bit_length() - 1
        tmp ^= b
        r = idx // N
        c = idx - r * N
        val = heat[idx]
        if val > 0:
            sums[(r + c) % k] += val

    best_residue = 0
    for res in range(1, k):
        if sums[res] > sums[best_residue]:
            best_residue = res

    residue_idx = _best_index(heat, unknown_mask, 0, k, best_residue)
    if residue_idx >= 0:
        if global_val <= 0 or heat[residue_idx] >= 0.70 * global_val:
            return residue_idx

    return global_idx


def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        _init()

        miss_mask, hit_mask, unknown_mask = _board_masks(board)
        if unknown_mask == 0:
            return _first_unknown(board)

        solved_mask, remaining = _infer_solved(board, hit_mask)
        active_mask = hit_mask & ~solved_mask

        if active_mask:
            heat = _dp_heat(miss_mask, active_mask, solved_mask, unknown_mask, remaining)
            hunt_mode = False

            if heat is None or _all_zero(heat, unknown_mask):
                heat, target_exists = _fallback_heat(
                    miss_mask,
                    hit_mask,
                    active_mask,
                    solved_mask,
                    unknown_mask,
                    remaining,
                )
                hunt_mode = not target_exists
        else:
            heat = _hunt_heat(miss_mask, hit_mask, unknown_mask, remaining)
            hunt_mode = True

        if hunt_mode:
            idx = _choose_hunt(heat, unknown_mask, remaining)
        else:
            idx = _best_index(heat, unknown_mask, active_mask)

        if idx >= 0:
            r, c = divmod(idx, N)
            if board[r][c] == 0:
                return (r, c)

        return _first_unknown(board)

    except Exception:
        return _first_unknown(board)
