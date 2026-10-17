
FLEET = [5, 4, 3, 3, 2]
FLEET_COUNTS = {5: 1, 4: 1, 3: 2, 2: 1}


def _build_placements():
    placements = {2: [], 3: [], 4: [], 5: []}
    for L in placements:
        for r in range(10):
            for c in range(11 - L):
                cells = tuple((r, c + i) for i in range(L))
                placements[L].append((cells, frozenset(cells), "H"))
        for r in range(11 - L):
            for c in range(10):
                cells = tuple((r + i, c) for i in range(L))
                placements[L].append((cells, frozenset(cells), "V"))
    return placements


def _build_subset_sums():
    out = {}
    n = len(FLEET)
    for mask in range(1, 1 << n):
        s = 0
        for i in range(n):
            if (mask >> i) & 1:
                s += FLEET[i]
        out.setdefault(s, []).append(mask)
    return out


PLACEMENTS = _build_placements()
SUBSETS_BY_SUM = _build_subset_sums()


def _hit_components(board):
    seen = [[False] * 10 for _ in range(10)]
    comps = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1 and not seen[r][c]:
                stack = [(r, c)]
                seen[r][c] = True
                cells = []
                while stack:
                    cr, cc = stack.pop()
                    cells.append((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 1 and not seen[nr][nc]:
                            seen[nr][nc] = True
                            stack.append((nr, nc))
                comps.append(cells)
    return comps


def _component_info(cells):
    rows = {r for r, _ in cells}
    cols = {c for _, c in cells}

    if len(cells) == 1:
        ori = "S"
        ordered = tuple(cells)
    elif len(rows) == 1:
        ori = "H"
        ordered = tuple(sorted(cells, key=lambda x: x[1]))
    elif len(cols) == 1:
        ori = "V"
        ordered = tuple(sorted(cells, key=lambda x: x[0]))
    else:
        ori = "M"
        ordered = tuple(sorted(cells))

    return {
        "cells": ordered,
        "set": set(ordered),
        "size": len(ordered),
        "ori": ori,
    }


def _component_end_cells(comp):
    if comp["ori"] == "H":
        r = comp["cells"][0][0]
        c0 = comp["cells"][0][1]
        c1 = comp["cells"][-1][1]
        left = (r, c0 - 1) if c0 > 0 else None
        right = (r, c1 + 1) if c1 < 9 else None
        return left, right
    if comp["ori"] == "V":
        c = comp["cells"][0][1]
        r0 = comp["cells"][0][0]
        r1 = comp["cells"][-1][0]
        up = (r0 - 1, c) if r0 > 0 else None
        down = (r1 + 1, c) if r1 < 9 else None
        return up, down
    return None, None


def _end_blocked(board, cell):
    if cell is None:
        return True
    r, c = cell
    return board[r][c] == -1


def _classify_components(board, comp_infos):
    sealed_idx = set()
    sealed_lengths = []
    long_open_idx = set()

    for i, comp in enumerate(comp_infos):
        if comp["ori"] in ("H", "V") and comp["size"] >= 2:
            end1, end2 = _component_end_cells(comp)
            b1 = _end_blocked(board, end1)
            b2 = _end_blocked(board, end2)

            if b1 and b2:
                sealed_idx.add(i)
                sealed_lengths.append(comp["size"])
            elif comp["size"] >= 5:
                # Large open runs can be multiple touching ships.
                long_open_idx.add(i)

    return sealed_idx, sealed_lengths, long_open_idx


def _definite_consumed_from_sealed(sealed_lengths):
    if not sealed_lengths:
        return {5: 0, 4: 0, 3: 0, 2: 0}

    lengths = sorted(sealed_lengths, reverse=True)
    memo = {}

    def rec(i, used_mask):
        key = (i, used_mask)
        if key in memo:
            return memo[key]
        if i == len(lengths):
            return {used_mask}

        total = lengths[i]
        res = set()
        for mask in SUBSETS_BY_SUM.get(total, ()):
            if mask & used_mask:
                continue
            res.update(rec(i + 1, used_mask | mask))

        memo[key] = res
        return res

    feasible_masks = rec(0, 0)
    if not feasible_masks:
        return {5: 0, 4: 0, 3: 0, 2: 0}

    definite = {}
    for L in (5, 4, 3, 2):
        cnts = []
        for mask in feasible_masks:
            cnt = 0
            for i, ship_len in enumerate(FLEET):
                if ship_len == L and ((mask >> i) & 1):
                    cnt += 1
            cnts.append(cnt)
        definite[L] = min(cnts) if cnts else 0

    return definite


def _remaining_lengths_from_definite(definite):
    counts = dict(FLEET_COUNTS)
    for L in (5, 4, 3, 2):
        counts[L] = max(0, counts[L] - definite.get(L, 0))

    remaining = []
    for L in (5, 4, 3, 2):
        remaining.extend([L] * counts[L])
    return remaining


def _build_active_groups(comp_infos, sealed_idx, long_open_idx):
    groups = []
    hit_to_group = {}

    for i, comp in enumerate(comp_infos):
        if i in sealed_idx or i in long_open_idx:
            continue

        # Mixed shapes are safest to treat as individual hits.
        if comp["ori"] == "M" or comp["size"] == 1:
            for cell in comp["cells"]:
                gid = len(groups)
                groups.append({
                    "cells": (cell,),
                    "set": {cell},
                    "size": 1,
                    "ori": "S",
                })
                hit_to_group[cell] = gid
        else:
            gid = len(groups)
            groups.append({
                "cells": comp["cells"],
                "set": set(comp["cells"]),
                "size": comp["size"],
                "ori": comp["ori"],
            })
            for cell in comp["cells"]:
                hit_to_group[cell] = gid

    return groups, hit_to_group


def _score_placements(board, remaining, groups, hit_to_group, blocked_cells):
    hunt = [[0.0] * 10 for _ in range(10)]
    target = [[0.0] * 10 for _ in range(10)]

    for L in remaining:
        for cells, cellset, ori in PLACEMENTS[L]:
            valid = True
            hit_indices = []
            group_ids = set()

            for idx, (r, c) in enumerate(cells):
                if board[r][c] == -1 or (r, c) in blocked_cells:
                    valid = False
                    break
                if board[r][c] == 1:
                    gid = hit_to_group.get((r, c))
                    if gid is not None:
                        hit_indices.append(idx)
                        group_ids.add(gid)

            if not valid:
                continue

            # If a placement touches a known aligned run, require it to explain the whole run.
            for gid in group_ids:
                g = groups[gid]
                if g["size"] > 1:
                    if g["ori"] != ori or not g["set"].issubset(cellset):
                        valid = False
                        break

            if not valid:
                continue

            if not hit_indices:
                for r, c in cells:
                    if board[r][c] == 0:
                        hunt[r][c] += 1.0
            else:
                t = len(hit_indices)
                weight = 50.0 * (4.0 ** (t - 1))
                for idx, (r, c) in enumerate(cells):
                    if board[r][c] != 0:
                        continue
                    dist = min(abs(idx - h) for h in hit_indices)
                    if dist > 0:
                        target[r][c] += weight / dist

    return hunt, target


def _run_space(board, start_cell, step, blocked_cells):
    r, c = start_cell
    dr, dc = step
    n = 0
    while 0 <= r < 10 and 0 <= c < 10 and board[r][c] != -1 and (r, c) not in blocked_cells:
        n += 1
        r += dr
        c += dc
    return n


def _add_end_bonuses(board, comp, remaining, blocked_cells, target):
    if comp["ori"] not in ("H", "V") or comp["size"] < 2:
        return

    end1, end2 = _component_end_cells(comp)

    if comp["ori"] == "H":
        steps = ((0, -1), (0, 1))
    else:
        steps = ((-1, 0), (1, 0))

    for end_cell, step in zip((end1, end2), steps):
        if end_cell is None:
            continue
        er, ec = end_cell
        if board[er][ec] != 0:
            continue

        outward = _run_space(board, end_cell, step, blocked_cells)
        if outward <= 0:
            continue

        # A long run can represent multiple touching ships, so estimate how many
        # hit cells near this end could belong to an unfinished ship.
        bonus = 0.0
        max_k = min(4, comp["size"])
        for k in range(1, max_k + 1):
            for L in remaining:
                if L > k and (L - k) <= outward:
                    bonus += 45.0 * k

        target[er][ec] += bonus


def _apply_hunt_bias(board, hunt, remaining):
    if not remaining:
        return

    sum0 = 0.0
    sum1 = 0.0
    for r in range(10):
        for c in range(10):
            if board[r][c] != 0:
                continue
            if ((r + c) & 1) == 0:
                sum0 += hunt[r][c]
            else:
                sum1 += hunt[r][c]

    preferred = 0 if sum0 >= sum1 else 1
    if min(remaining) == 2:
        good, bad = 1.35, 0.75
    else:
        good, bad = 1.15, 0.90

    for r in range(10):
        for c in range(10):
            if board[r][c] != 0:
                continue
            if ((r + c) & 1) == preferred:
                hunt[r][c] *= good
            else:
                hunt[r][c] *= bad


def _unknown_neighbor_count(board, r, c):
    cnt = 0
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nr, nc = r + dr, c + dc
        if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
            cnt += 1
    return cnt


def policy(board):
    unknowns = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 0]
    if not unknowns:
        return (0, 0)

    comp_infos = [_component_info(cells) for cells in _hit_components(board)]
    sealed_idx, sealed_lengths, long_open_idx = _classify_components(board, comp_infos)

    definite = _definite_consumed_from_sealed(sealed_lengths)
    remaining = _remaining_lengths_from_definite(definite)
    if not remaining:
        # Robust fallback for inconsistent late-game states.
        remaining = [5, 4, 3, 3, 2]

    blocked_cells = set()
    for i in sealed_idx:
        blocked_cells.update(comp_infos[i]["cells"])
    for i in long_open_idx:
        blocked_cells.update(comp_infos[i]["cells"])

    groups, hit_to_group = _build_active_groups(comp_infos, sealed_idx, long_open_idx)
    hunt, target = _score_placements(board, remaining, groups, hit_to_group, blocked_cells)

    # Add direct end bonuses for every open aligned run.
    for i, comp in enumerate(comp_infos):
        if i in sealed_idx:
            continue
        _add_end_bonuses(board, comp, remaining, blocked_cells, target)

    _apply_hunt_bias(board, hunt, remaining)

    target_exists = any(target[r][c] > 0.0 for r, c in unknowns)

    best = unknowns[0]
    best_score = float("-inf")

    for r, c in unknowns:
        if target_exists:
            score = target[r][c] + 0.05 * hunt[r][c]
        else:
            score = hunt[r][c]

        # Small deterministic tie-breakers.
        score += 0.005 * _unknown_neighbor_count(board, r, c)
        score += 0.001 * (9.0 - abs(2 * r - 9) - abs(2 * c - 9))

        if score > best_score:
            best_score = score
            best = (r, c)

    return best
