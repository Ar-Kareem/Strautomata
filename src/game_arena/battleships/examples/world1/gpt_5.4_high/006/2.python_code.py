
import time

# Ship lengths: one each of 5, 4, 2 and two of 3.
LEN_ORDER = (5, 4, 3, 2)
LEN_TO_IDX = {5: 0, 4: 1, 3: 2, 2: 3}
CAPACITY = (1, 1, 2, 1)
ZERO_STATE = (0, 0, 0, 0)
ONEHOT = (
    (1, 0, 0, 0),
    (0, 1, 0, 0),
    (0, 0, 1, 0),
    (0, 0, 0, 1),
)

COMP_RESULT_CAP = 2000
COMP_NODE_CAP = 50000


def _make_placements(length: int):
    out = []
    # Horizontal
    for r in range(10):
        for c in range(11 - length):
            cells = tuple(r * 10 + (c + k) for k in range(length))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            out.append((mask, cells))
    # Vertical
    for r in range(11 - length):
        for c in range(10):
            cells = tuple((r + k) * 10 + c for k in range(length))
            mask = 0
            for idx in cells:
                mask |= 1 << idx
            out.append((mask, cells))
    return out


PLACEMENTS_BY_LEN = {L: _make_placements(L) for L in LEN_ORDER}

ORTH_NEIGHBORS = []
CENTER_SCORE = []
for idx in range(100):
    r, c = divmod(idx, 10)
    neigh = []
    if r > 0:
        neigh.append((r - 1) * 10 + c)
    if r < 9:
        neigh.append((r + 1) * 10 + c)
    if c > 0:
        neigh.append(r * 10 + (c - 1))
    if c < 9:
        neigh.append(r * 10 + (c + 1))
    ORTH_NEIGHBORS.append(tuple(neigh))
    # Larger is better; central cells get higher score.
    CENTER_SCORE.append(-((2 * r - 9) ** 2 + (2 * c - 9) ** 2))


class _SearchAbort(Exception):
    pass


def _state_add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3])


def _state_ok(s):
    return s[0] <= 1 and s[1] <= 1 and s[2] <= 2 and s[3] <= 1


def _choose_count(n: int, k: int) -> int:
    if k <= 0:
        return 1
    if k == 1:
        return n if n >= 1 else 0
    if k == 2:
        return (n * (n - 1)) // 2 if n >= 2 else 0
    return 0


def _enumerate_component(comp_hit_bits, comp_raw_cands, deadline):
    """
    Enumerate legal explanations for one interacting hit component.
    Each explanation records:
      - used ship counts
      - union of unknown cells occupied by the explanatory ships
      - multiplicity (number of distinct local explanations with same outcome)
    """
    local_map = {gbit: i for i, gbit in enumerate(comp_hit_bits)}
    k = len(comp_hit_bits)

    # Candidate tuple:
    # (mask, hitmask_local, unknown_mask, len_idx, hit_count, unknown_count)
    cands = []
    for len_idx, mask, hitmask_global, unknown_mask in comp_raw_cands:
        hm_local = 0
        bits = hitmask_global
        while bits:
            b = bits & -bits
            gbit = b.bit_length() - 1
            hm_local |= 1 << local_map[gbit]
            bits ^= b
        cands.append(
            (
                mask,
                hm_local,
                unknown_mask,
                len_idx,
                hm_local.bit_count(),
                unknown_mask.bit_count(),
            )
        )

    cover_lists = [[] for _ in range(k)]
    for ci, cand in enumerate(cands):
        bits = cand[1]
        while bits:
            b = bits & -bits
            j = b.bit_length() - 1
            cover_lists[j].append(ci)
            bits ^= b

    for lst in cover_lists:
        lst.sort(
            key=lambda ci: (
                -cands[ci][4],                 # more hits covered first
                cands[ci][5],                  # fewer new unknown cells first
                LEN_ORDER[cands[ci][3]],       # shorter ship first as a tie-break
            )
        )

    results = {}
    node_count = 0

    def rec(uncovered, used, occupied, target_mask):
        nonlocal node_count
        node_count += 1

        if node_count >= COMP_NODE_CAP or len(results) >= COMP_RESULT_CAP:
            raise _SearchAbort
        if (node_count & 255) == 0 and time.perf_counter() > deadline:
            raise _SearchAbort

        if uncovered == 0:
            key = (used, target_mask)
            results[key] = results.get(key, 0) + 1
            return

        # Choose the uncovered hit with the fewest feasible candidate placements.
        best_options = None
        best_list = None

        bits = uncovered
        while bits:
            b = bits & -bits
            j = b.bit_length() - 1
            bits ^= b

            feasible = []
            for ci in cover_lists[j]:
                mask, hm_local, unknown_mask, len_idx, _, _ = cands[ci]
                if occupied & mask:
                    continue
                if used[len_idx] >= CAPACITY[len_idx]:
                    continue
                feasible.append(ci)

            if not feasible:
                return

            if best_options is None or len(feasible) < best_options:
                best_options = len(feasible)
                best_list = feasible
                if best_options == 1:
                    break

        for ci in best_list:
            mask, hm_local, unknown_mask, len_idx, _, _ = cands[ci]
            new_used = _state_add(used, ONEHOT[len_idx])
            rec(uncovered & ~hm_local, new_used, occupied | mask, target_mask | unknown_mask)

    try:
        rec((1 << k) - 1, ZERO_STATE, 0, 0)
    except _SearchAbort:
        pass

    return [{"used": used, "target": target, "mult": mult} for (used, target), mult in results.items()]


def _select_target(unknowns, target_heat, base_heat, mobility):
    best_idx = unknowns[0]
    best_key = None
    for idx in unknowns:
        key = (
            target_heat[idx],
            base_heat[idx],
            CENTER_SCORE[idx],
            mobility[idx],
            -idx,
        )
        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx
    return best_idx


def _select_hunt(unknowns, hunt_heat, base_heat, mobility):
    parity_score = [0.0, 0.0]
    parity_count = [0, 0]
    for idx in unknowns:
        r, c = divmod(idx, 10)
        p = (r + c) & 1
        parity_score[p] += hunt_heat[idx]
        parity_count[p] += 1

    if parity_score[0] > parity_score[1]:
        best_parity = 0
    elif parity_score[1] > parity_score[0]:
        best_parity = 1
    else:
        best_parity = 0 if parity_count[0] >= parity_count[1] else 1

    best_idx = unknowns[0]
    best_key = None
    for idx in unknowns:
        r, c = divmod(idx, 10)
        key = (
            1 if ((r + c) & 1) == best_parity else 0,
            hunt_heat[idx],
            base_heat[idx],
            CENTER_SCORE[idx],
            mobility[idx],
            -idx,
        )
        if best_key is None or key > best_key:
            best_key = key
            best_idx = idx
    return best_idx


def _heuristic_target_scores(flat, miss_mask):
    """
    Fallback target heuristic: placements covering more known hits get
    exponentially more weight.
    """
    heat = [0.0] * 100
    for L in LEN_ORDER:
        mult = CAPACITY[LEN_TO_IDX[L]]
        for mask, cells in PLACEMENTS_BY_LEN[L]:
            if mask & miss_mask:
                continue
            hit_count = 0
            for idx in cells:
                if flat[idx] == 1:
                    hit_count += 1
            if hit_count == 0:
                continue
            weight = mult * (7 ** hit_count)
            for idx in cells:
                if flat[idx] == 0:
                    heat[idx] += weight
    return heat


def policy(board: list[list[int]]) -> tuple[int, int]:
    flat = []
    for row in board:
        flat.extend(row)

    unknowns = []
    hits = []
    hit_pos_to_bit = {}
    miss_mask = 0
    hit_mask = 0
    unknown_mask = 0

    for idx, v in enumerate(flat):
        if v == 0:
            unknowns.append(idx)
            unknown_mask |= 1 << idx
        elif v == -1:
            miss_mask |= 1 << idx
        elif v == 1:
            hit_pos_to_bit[idx] = len(hits)
            hits.append(idx)
            hit_mask |= 1 << idx

    # Ultra-safe fallback: if somehow nothing is unknown.
    if not unknowns:
        return (0, 0)

    mobility = [0] * 100
    for idx in unknowns:
        cnt = 0
        for n in ORTH_NEIGHBORS[idx]:
            if flat[n] == 0:
                cnt += 1
        mobility[idx] = cnt

    # Hunt-mode placement statistics on cells not already known occupied/water.
    blocked_hunt = miss_mask | hit_mask
    avail_count = {}
    norm_heat_by_len = {}
    base_heat = [0.0] * 100

    for L in LEN_ORDER:
        raw = [0] * 100
        cnt = 0
        for mask, cells in PLACEMENTS_BY_LEN[L]:
            if mask & blocked_hunt:
                continue
            cnt += 1
            for idx in cells:
                raw[idx] += 1
        avail_count[L] = cnt

        arr = [0.0] * 100
        if cnt > 0:
            inv = 1.0 / cnt
            for idx in unknowns:
                if raw[idx]:
                    arr[idx] = raw[idx] * inv
                    base_heat[idx] += CAPACITY[LEN_TO_IDX[L]] * raw[idx]
        norm_heat_by_len[L] = arr

    # Pure hunt mode: no current hits to explain.
    if not hits:
        hunt_heat = [0.0] * 100
        for L in LEN_ORDER:
            rem = CAPACITY[LEN_TO_IDX[L]]
            arr = norm_heat_by_len[L]
            if rem:
                for idx in unknowns:
                    val = arr[idx]
                    if val:
                        hunt_heat[idx] += rem * val
        best = _select_hunt(unknowns, hunt_heat, base_heat, mobility)
        return divmod(best, 10)

    # Exact local inference around hits, with safe fallback if anything goes wrong.
    try:
        deadline = time.perf_counter() + 0.85

        # Raw hit-touching candidate placements:
        # (len_idx, mask, hitmask_global, unknown_mask)
        raw_candidates = []
        cands_by_hit = [[] for _ in range(len(hits))]

        for L in LEN_ORDER:
            len_idx = LEN_TO_IDX[L]
            for mask, cells in PLACEMENTS_BY_LEN[L]:
                if mask & miss_mask:
                    continue
                hitmask_global = 0
                for idx in cells:
                    bit = hit_pos_to_bit.get(idx)
                    if bit is not None:
                        hitmask_global |= 1 << bit
                if hitmask_global == 0:
                    continue
                umask = mask & unknown_mask
                cid = len(raw_candidates)
                raw_candidates.append((len_idx, mask, hitmask_global, umask))
                bits = hitmask_global
                while bits:
                    b = bits & -bits
                    hbit = b.bit_length() - 1
                    cands_by_hit[hbit].append(cid)
                    bits ^= b

        # If any hit has no legal explanation, jump to fallback.
        for lst in cands_by_hit:
            if not lst:
                raise RuntimeError("unexplainable hit pattern")

        # Build interacting hit components conservatively:
        # two hits are linked if the union of cells reachable by their candidate
        # placements overlaps, meaning explanations can interact by overlap.
        parent = list(range(len(hits)))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        region_masks = [0] * len(hits)
        for hbit in range(len(hits)):
            reg = 0
            for cid in cands_by_hit[hbit]:
                reg |= raw_candidates[cid][1]
            region_masks[hbit] = reg

        for i in range(len(hits)):
            for j in range(i + 1, len(hits)):
                if region_masks[i] & region_masks[j]:
                    union(i, j)

        comp_map = {}
        for hbit in range(len(hits)):
            root = find(hbit)
            comp_map.setdefault(root, []).append(hbit)
        components = [sorted(v) for _, v in sorted(comp_map.items())]

        component_explanations = []
        for comp_hits in components:
            cand_ids = set()
            for hbit in comp_hits:
                cand_ids.update(cands_by_hit[hbit])
            comp_raw_cands = [raw_candidates[cid] for cid in sorted(cand_ids)]
            exps = _enumerate_component(comp_hits, comp_raw_cands, deadline)
            if not exps:
                raise RuntimeError("component search produced no explanation")
            component_explanations.append(exps)

        # DP over components by used ship counts.
        prefix = [{ZERO_STATE: 1}]
        for exps in component_explanations:
            prev = prefix[-1]
            cur = {}
            for s, ways in prev.items():
                for e in exps:
                    ns = _state_add(s, e["used"])
                    if _state_ok(ns):
                        cur[ns] = cur.get(ns, 0) + ways * e["mult"]
            if not cur:
                raise RuntimeError("no compatible global explanations")
            prefix.append(cur)

        suffix = [None] * (len(component_explanations) + 1)
        suffix[len(component_explanations)] = {ZERO_STATE: 1}
        for i in range(len(component_explanations) - 1, -1, -1):
            cur = {}
            for e in component_explanations[i]:
                for s, ways in suffix[i + 1].items():
                    ns = _state_add(e["used"], s)
                    if _state_ok(ns):
                        cur[ns] = cur.get(ns, 0) + ways * e["mult"]
            suffix[i] = cur

        completion_cache = {}

        def completion_weight(used_state):
            if used_state in completion_cache:
                return completion_cache[used_state]
            rem5 = 1 - used_state[0]
            rem4 = 1 - used_state[1]
            rem3 = 2 - used_state[2]
            rem2 = 1 - used_state[3]
            w = (
                _choose_count(avail_count[5], rem5)
                * _choose_count(avail_count[4], rem4)
                * _choose_count(avail_count[3], rem3)
                * _choose_count(avail_count[2], rem2)
            )
            completion_cache[used_state] = w
            return w

        # Target heat from exact explanations.
        target_heat = [0] * 100
        has_target = False

        for i, exps in enumerate(component_explanations):
            left = prefix[i]
            right = suffix[i + 1]
            for e in exps:
                if e["target"] == 0:
                    continue
                u = e["used"]
                mult = e["mult"]
                weight = 0
                for sl, w1 in left.items():
                    sm = _state_add(sl, u)
                    if not _state_ok(sm):
                        continue
                    for sr, w2 in right.items():
                        st = _state_add(sm, sr)
                        if _state_ok(st):
                            cw = completion_weight(st)
                            if cw:
                                weight += w1 * mult * w2 * cw
                if weight:
                    has_target = True
                    tm = e["target"]
                    while tm:
                        b = tm & -tm
                        idx = b.bit_length() - 1
                        target_heat[idx] += weight
                        tm ^= b

        if has_target:
            best = _select_target(unknowns, target_heat, base_heat, mobility)
            return divmod(best, 10)

        # If all current hits are fully explained as sunk/closed, revert to hunt
        # but account for which ship lengths are still likely unused.
        hunt_heat = [0.0] * 100
        final_counts = prefix[-1]

        for used_state, ways in final_counts.items():
            cw = completion_weight(used_state)
            if not cw:
                continue
            mass = ways * cw
            rem5 = 1 - used_state[0]
            rem4 = 1 - used_state[1]
            rem3 = 2 - used_state[2]
            rem2 = 1 - used_state[3]

            if rem5:
                arr = norm_heat_by_len[5]
                factor = mass * rem5
                for idx in unknowns:
                    val = arr[idx]
                    if val:
                        hunt_heat[idx] += factor * val
            if rem4:
                arr = norm_heat_by_len[4]
                factor = mass * rem4
                for idx in unknowns:
                    val = arr[idx]
                    if val:
                        hunt_heat[idx] += factor * val
            if rem3:
                arr = norm_heat_by_len[3]
                factor = mass * rem3
                for idx in unknowns:
                    val = arr[idx]
                    if val:
                        hunt_heat[idx] += factor * val
            if rem2:
                arr = norm_heat_by_len[2]
                factor = mass * rem2
                for idx in unknowns:
                    val = arr[idx]
                    if val:
                        hunt_heat[idx] += factor * val

        best = _select_hunt(unknowns, hunt_heat, base_heat, mobility)
        return divmod(best, 10)

    except Exception:
        # Strong fallback that still handles both target and hunt modes.
        target_fallback = _heuristic_target_scores(flat, miss_mask)
        if any(target_fallback[idx] > 0 for idx in unknowns):
            best = _select_target(unknowns, target_fallback, base_heat, mobility)
            return divmod(best, 10)

        hunt_heat = [0.0] * 100
        for L in LEN_ORDER:
            rem = CAPACITY[LEN_TO_IDX[L]]
            arr = norm_heat_by_len[L]
            if rem:
                for idx in unknowns:
                    val = arr[idx]
                    if val:
                        hunt_heat[idx] += rem * val

        best = _select_hunt(unknowns, hunt_heat, base_heat, mobility)
        return divmod(best, 10)
