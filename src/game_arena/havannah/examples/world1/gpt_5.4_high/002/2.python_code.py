
from collections import deque

_INF = 10**9
_BITCOUNT = int.bit_count if hasattr(int, "bit_count") else (lambda x: bin(x).count("1"))
_CACHE = {}


def _dims(mask):
    return (len(mask), len(mask[0]))


def _ordered_deltas(col, shift_down_odd=True):
    """
    Vertical-offset hex coordinates.
    If shift_down_odd is True, odd columns are shifted "down", which matches the prompt example.
    """
    shifted_down = (col & 1) == 1 if shift_down_odd else (col & 1) == 0
    if shifted_down:
        # cyclic order
        return [(-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1)]
    else:
        return [(-1, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1)]


def _build_topology(valid_mask, shift_down_odd=True, relaxed=False):
    rows, cols = _dims(valid_mask)
    coords = []
    idx_of = {}
    for r in range(rows):
        for c in range(cols):
            if bool(valid_mask[r][c]):
                idx_of[(r, c)] = len(coords)
                coords.append((r, c))

    m = len(coords)
    nbrs = [[] for _ in range(m)]
    ordered_nbrs = [[-1] * 6 for _ in range(m)]

    for i, (r, c) in enumerate(coords):
        deltas = _ordered_deltas(c, shift_down_odd)
        for k, (dr, dc) in enumerate(deltas):
            rr, cc = r + dr, c + dc
            j = idx_of.get((rr, cc), -1)
            ordered_nbrs[i][k] = j
            if j != -1:
                nbrs[i].append(j)

    deg = [len(n) for n in nbrs]
    boundary = [i for i in range(m) if deg[i] < 6]
    boundary_set = set(boundary)
    corners = [i for i in boundary if deg[i] == 3]

    # Precompute centrality even for relaxed mode.
    depth = [_INF] * m
    dq = deque()
    for b in boundary:
        depth[b] = 0
        dq.append(b)
    while dq:
        x = dq.popleft()
        dx = depth[x] + 1
        for y in nbrs[x]:
            if dx < depth[y]:
                depth[y] = dx
                dq.append(y)

    r_mean = sum(r for r, _ in coords) / max(1, m)
    c_mean = sum(c for _, c in coords) / max(1, m)
    sqdist = [((r - r_mean) ** 2 + (c - c_mean) ** 2) for (r, c) in coords]

    # If relaxed, don't insist on perfect edge labeling.
    if relaxed:
        corner_of = [-1] * m
        for k, x in enumerate(sorted(corners)[:6]):
            corner_of[x] = k
        edge_of = [-1] * m
        corner_targets = [[i] for i in sorted(corners)[:6]]
        edge_targets = [[] for _ in range(6)]
        opening = min(range(m), key=lambda i: (-depth[i], sqdist[i], coords[i][0], coords[i][1]))
        return {
            "coords": coords,
            "idx_of": idx_of,
            "nbrs": nbrs,
            "ordered_nbrs": ordered_nbrs,
            "boundary": boundary,
            "corner_of": corner_of,
            "edge_of": edge_of,
            "corner_targets": corner_targets,
            "edge_targets": edge_targets,
            "depth": depth,
            "sqdist": sqdist,
            "opening": opening,
        }

    if len(corners) != 6:
        return None

    boundary_adj = {i: [j for j in nbrs[i] if j in boundary_set] for i in boundary}
    if any(len(boundary_adj[i]) != 2 for i in boundary):
        return None

    # Trace the boundary cycle.
    start = min(corners)
    first = min(boundary_adj[start])
    cycle = [start]
    prev = start
    curr = first
    seen = {start}

    while curr != start:
        if curr in seen:
            return None
        seen.add(curr)
        cycle.append(curr)
        a, b = boundary_adj[curr]
        nxt = b if a == prev else a
        prev, curr = curr, nxt

    if len(cycle) != len(boundary):
        return None

    pos = {x: i for i, x in enumerate(cycle)}
    corners_cycle = sorted(corners, key=lambda x: pos[x])

    corner_of = [-1] * m
    for k, x in enumerate(corners_cycle):
        corner_of[x] = k

    edge_of = [-1] * m
    edge_targets = [[] for _ in range(6)]
    L = len(cycle)
    for k in range(6):
        a = pos[corners_cycle[k]]
        b = pos[corners_cycle[(k + 1) % 6]]
        i = (a + 1) % L
        while i != b:
            x = cycle[i]
            edge_of[x] = k
            edge_targets[k].append(x)
            i = (i + 1) % L

    corner_targets = [[x] for x in corners_cycle]
    opening = min(range(m), key=lambda i: (-depth[i], sqdist[i], coords[i][0], coords[i][1]))

    return {
        "coords": coords,
        "idx_of": idx_of,
        "nbrs": nbrs,
        "ordered_nbrs": ordered_nbrs,
        "boundary": boundary,
        "corner_of": corner_of,
        "edge_of": edge_of,
        "corner_targets": corner_targets,
        "edge_targets": edge_targets,
        "depth": depth,
        "sqdist": sqdist,
        "opening": opening,
    }


def _init(valid_mask):
    top = _build_topology(valid_mask, shift_down_odd=True, relaxed=False)
    alt = _build_topology(valid_mask, shift_down_odd=False, relaxed=False)

    # Prefer the prompt-compatible interpretation if it validates.
    if top is not None:
        state = top
    elif alt is not None:
        state = alt
    else:
        state = _build_topology(valid_mask, shift_down_odd=True, relaxed=True)

    state["dims"] = _dims(valid_mask)
    return state


def _build_components(occ_bool, occ_indices, nbrs, corner_of, edge_of):
    m = len(nbrs)
    comp_of = [-1] * m
    sizes = []
    corner_masks = []
    edge_masks = []

    for s in occ_indices:
        if comp_of[s] != -1:
            continue
        cid = len(sizes)
        stack = [s]
        comp_of[s] = cid
        size = 0
        cmask = 0
        emask = 0

        while stack:
            x = stack.pop()
            size += 1
            co = corner_of[x]
            eo = edge_of[x]
            if co >= 0:
                cmask |= (1 << co)
            if eo >= 0:
                emask |= (1 << eo)
            for y in nbrs[x]:
                if occ_bool[y] and comp_of[y] == -1:
                    comp_of[y] = cid
                    stack.append(y)

        sizes.append(size)
        corner_masks.append(cmask)
        edge_masks.append(emask)

    return comp_of, sizes, corner_masks, edge_masks


def _dist_maps(own_bool, opp_bool, nbrs, targets):
    m = len(nbrs)
    cost = [_INF] * m
    for i in range(m):
        if opp_bool[i]:
            cost[i] = _INF
        elif own_bool[i]:
            cost[i] = 0
        else:
            cost[i] = 1

    all_maps = []
    for target in targets:
        dist = [_INF] * m
        dq = deque()
        for t in target:
            w = cost[t]
            if w >= _INF:
                continue
            if w < dist[t]:
                dist[t] = w
                if w == 0:
                    dq.appendleft(t)
                else:
                    dq.append(t)

        while dq:
            x = dq.popleft()
            dx = dist[x]
            for y in nbrs[x]:
                w = cost[y]
                if w >= _INF:
                    continue
                nd = dx + w
                if nd < dist[y]:
                    dist[y] = nd
                    if w == 0:
                        dq.appendleft(y)
                    else:
                        dq.append(y)

        all_maps.append(dist)

    return all_maps


def _connection_costs(dist_maps, need, m):
    if len(dist_maps) < need:
        return [_INF] * m
    out = [_INF] * m
    for i in range(m):
        vals = []
        for dist in dist_maps:
            d = dist[i]
            if d < _INF:
                vals.append(max(0, d - 1))  # if we play here, this cell's empty-cost disappears
        if len(vals) >= need:
            vals.sort()
            out[i] = sum(vals[:need])
    return out


def _has_ring_after_move(move, occ_bool, nbrs, boundary):
    """
    Exact ring test via complement connectivity:
    if some non-player cell region is not connected to the boundary, there is a ring.
    """
    m = len(nbrs)
    seen = [False] * m
    dq = deque()

    for b in boundary:
        if b != move and not occ_bool[b]:
            seen[b] = True
            dq.append(b)

    while dq:
        x = dq.popleft()
        for y in nbrs[x]:
            if y != move and (not occ_bool[y]) and (not seen[y]):
                seen[y] = True
                dq.append(y)

    for i in range(m):
        if i != move and (not occ_bool[i]) and (not seen[i]):
            return True
    return False


def _is_winning_move(move, occ_bool, nbrs, corner_of, edge_of, boundary):
    """
    Exact immediate-win check for bridge / fork / ring.
    """
    # Connected component after adding move.
    stack = [move]
    seen = {move}
    cmask = 0
    emask = 0
    comp_size = 0

    occ_nbrs = 0
    for y in nbrs[move]:
        if occ_bool[y]:
            occ_nbrs += 1

    while stack:
        x = stack.pop()
        comp_size += 1
        co = corner_of[x]
        eo = edge_of[x]
        if co >= 0:
            cmask |= (1 << co)
        if eo >= 0:
            emask |= (1 << eo)
        for y in nbrs[x]:
            if occ_bool[y] and y not in seen:
                seen.add(y)
                stack.append(y)

    if _BITCOUNT(cmask) >= 2:
        return True
    if _BITCOUNT(emask) >= 3:
        return True

    # Ring is impossible below 6 stones in a component, and unlikely with <2 adjacent friends.
    if comp_size < 6 or occ_nbrs < 2:
        return False

    return _has_ring_after_move(move, occ_bool, nbrs, boundary)


def _groups6(bits):
    g = 0
    for i, v in enumerate(bits):
        if v and not bits[i - 1]:
            g += 1
    return g


def _count_future_wins_after(move, me_bool, legal, nbrs, corner_of, edge_of, boundary, limit=2):
    occ2 = me_bool[:]
    occ2[move] = True
    cnt = 0
    for x in legal:
        if x == move:
            continue
        if _is_winning_move(x, occ2, nbrs, corner_of, edge_of, boundary):
            cnt += 1
            if cnt >= limit:
                return cnt
    return cnt


def policy(me, opp, valid_mask):
    try:
        dims = _dims(valid_mask)
        state = _CACHE.get("state")
        if state is None or state.get("dims") != dims:
            state = _init(valid_mask)
            _CACHE["state"] = state

        coords = state["coords"]
        idx_of = state["idx_of"]
        nbrs = state["nbrs"]
        ordered_nbrs = state["ordered_nbrs"]
        boundary = state["boundary"]
        corner_of = state["corner_of"]
        edge_of = state["edge_of"]
        corner_targets = state["corner_targets"]
        edge_targets = state["edge_targets"]
        depth = state["depth"]
        sqdist = state["sqdist"]
        opening = state["opening"]

        m = len(coords)

        me_idx = [idx_of[p] for p in me]
        opp_idx = [idx_of[p] for p in opp]

        me_bool = [False] * m
        opp_bool = [False] * m
        for i in me_idx:
            me_bool[i] = True
        for i in opp_idx:
            opp_bool[i] = True

        legal = [i for i in range(m) if not me_bool[i] and not opp_bool[i]]
        if not legal:
            # Should not happen in a normal game, but still return something valid-ish.
            return coords[0]

        total = len(me_idx) + len(opp_idx)
        if total == 0:
            return coords[opening]
        if len(legal) == 1:
            return coords[legal[0]]

        # 1) Immediate tactical wins.
        my_wins = [x for x in legal if _is_winning_move(x, me_bool, nbrs, corner_of, edge_of, boundary)]
        if my_wins:
            # Any immediate win is fine.
            my_wins.sort(key=lambda x: (sqdist[x], coords[x][0], coords[x][1]))
            return coords[my_wins[0]]

        # 2) Immediate opponent threats.
        opp_wins = [x for x in legal if _is_winning_move(x, opp_bool, nbrs, corner_of, edge_of, boundary)]
        if len(opp_wins) == 1:
            return coords[opp_wins[0]]

        # 3) Positional analysis.
        me_comp_of, me_sizes, me_cmask, me_emask = _build_components(
            me_bool, me_idx, nbrs, corner_of, edge_of
        )
        opp_comp_of, opp_sizes, opp_cmask, opp_emask = _build_components(
            opp_bool, opp_idx, nbrs, corner_of, edge_of
        )

        me_corner_maps = _dist_maps(me_bool, opp_bool, nbrs, corner_targets)
        me_edge_maps = _dist_maps(me_bool, opp_bool, nbrs, edge_targets)
        opp_corner_maps = _dist_maps(opp_bool, me_bool, nbrs, corner_targets)
        opp_edge_maps = _dist_maps(opp_bool, me_bool, nbrs, edge_targets)

        me_bridge_cost = _connection_costs(me_corner_maps, 2, m)
        me_fork_cost = _connection_costs(me_edge_maps, 3, m)
        opp_bridge_cost = _connection_costs(opp_corner_maps, 2, m)
        opp_fork_cost = _connection_costs(opp_edge_maps, 3, m)

        opening_factor = max(0.0, 24.0 - total) / 24.0

        raw = [-10**18] * m

        candidates = opp_wins if opp_wins else legal

        for x in candidates:
            my_ids = set()
            opp_ids = set()
            my_n = 0
            opp_n = 0

            for y in nbrs[x]:
                if me_bool[y]:
                    my_n += 1
                    cid = me_comp_of[y]
                    if cid != -1:
                        my_ids.add(cid)
                elif opp_bool[y]:
                    opp_n += 1
                    cid = opp_comp_of[y]
                    if cid != -1:
                        opp_ids.add(cid)

            score = 0.0

            # Opening / centrality.
            score += opening_factor * (10.0 * depth[x] - 0.60 * sqdist[x])

            # Stay active; avoid dead isolated moves unless very early.
            if total > 2 and my_n == 0 and opp_n == 0:
                score -= 8.0

            # Local contact.
            score += 11.0 * my_n
            score += 4.5 * opp_n
            score += 16.0 * max(0, len(my_ids) - 1)
            score += 5.0 * len(opp_ids)

            # Component size / merging.
            new_size = 1 + sum(me_sizes[cid] for cid in my_ids)
            score += 2.5 * (new_size ** 0.70)

            # Targets already touched by the merged component.
            cmask = 0
            emask = 0
            co = corner_of[x]
            eo = edge_of[x]
            if co >= 0:
                cmask |= (1 << co)
            if eo >= 0:
                emask |= (1 << eo)
            for cid in my_ids:
                cmask |= me_cmask[cid]
                emask |= me_emask[cid]

            nc = _BITCOUNT(cmask)
            ne = _BITCOUNT(emask)

            score += 24.0 * nc
            score += 16.0 * ne
            if ne == 2:
                score += 24.0
            if nc >= 1 and ne >= 1:
                score += 10.0

            # Global bridge/fork potential for us.
            bc = me_bridge_cost[x]
            if bc < _INF:
                score += 70.0 / (1.0 + bc)
                if bc <= 2:
                    score += 20.0 - 5.0 * bc

            fc = me_fork_cost[x]
            if fc < _INF:
                score += 90.0 / (1.0 + fc)
                if fc <= 3:
                    score += 26.0 - 4.0 * fc

            # Block cells that are globally valuable to the opponent.
            obc = opp_bridge_cost[x]
            if obc < _INF:
                score += 30.0 / (1.0 + obc)
                if obc <= 2:
                    score += 10.0

            ofc = opp_fork_cost[x]
            if ofc < _INF:
                score += 40.0 / (1.0 + ofc)
                if ofc <= 3:
                    score += 13.0

            # If we touch strategically advanced opponent components, that's useful.
            for cid in opp_ids:
                score += 4.0 * _BITCOUNT(opp_cmask[cid])
                score += 3.0 * _BITCOUNT(opp_emask[cid])
                score += 0.5 * (opp_sizes[cid] ** 0.5)

            # Small local ring-shape bias.
            mine_bits = [1 if (y != -1 and me_bool[y]) else 0 for y in ordered_nbrs[x]]
            opp_bits2 = [1 if (y != -1 and opp_bool[y]) else 0 for y in ordered_nbrs[x]]

            fm = sum(mine_bits)
            fo = sum(opp_bits2)
            if fm >= 2:
                score += 2.5 * fm + 4.0 * max(0, _groups6(mine_bits) - 1)
            if fo >= 2:
                score += 1.5 * fo + 3.0 * max(0, _groups6(opp_bits2) - 1)

            raw[x] = score

        ranked = sorted(
            candidates,
            key=lambda x: (-raw[x], -depth[x], sqdist[x], coords[x][0], coords[x][1]),
        )

        # If opponent already has multiple winning moves, we're lost tactically;
        # pick the best blocking point we can.
        if opp_wins:
            return coords[ranked[0]]

        # 4) Search for forcing moves: create 2 distinct immediate wins next turn.
        force_limit = min(len(ranked), 14 if len(legal) > 100 else 18 if len(legal) > 70 else 24)

        best_move = ranked[0]
        best_val = raw[best_move]
        best_key = (-best_val, -depth[best_move], sqdist[best_move], coords[best_move][0], coords[best_move][1])

        for x in ranked[:force_limit]:
            wins_next = _count_future_wins_after(
                x, me_bool, legal, nbrs, corner_of, edge_of, boundary, limit=2
            )
            if wins_next >= 2:
                return coords[x]
            val = raw[x] + 55.0 * wins_next
            key = (-val, -depth[x], sqdist[x], coords[x][0], coords[x][1])
            if key < best_key:
                best_key = key
                best_move = x

        choice = coords[best_move]

        # Final legality guard.
        if choice in set(me) or choice in set(opp) or not bool(valid_mask[choice[0]][choice[1]]):
            occ = set(me) | set(opp)
            for r in range(len(valid_mask)):
                for c in range(len(valid_mask[0])):
                    if bool(valid_mask[r][c]) and (r, c) not in occ:
                        return (r, c)

        return choice

    except Exception:
        # Absolute fallback: always return a legal move.
        occ = set(me) | set(opp)
        rows = len(valid_mask)
        cols = len(valid_mask[0])
        for r in range(rows):
            for c in range(cols):
                if bool(valid_mask[r][c]) and (r, c) not in occ:
                    return (r, c)
        return (0, 0)
