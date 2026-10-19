
from collections import deque

INF = 10 ** 9
_GEOM_CACHE = None


def _hex_dist(a, b):
    r1, c1 = a
    r2, c2 = b
    dq = c1 - c2
    dp = (r1 - c1) - (r2 - c2)
    return max(abs(dq), abs(dp), abs(dq + dp))


def _build_geom(valid_mask, sig):
    n = len(valid_mask)
    cells = []
    idx = {}

    for r in range(n):
        for c in range(n):
            if bool(valid_mask[r][c]):
                idx[(r, c)] = len(cells)
                cells.append((r, c))

    m = len(cells)
    neigh = [[] for _ in range(m)]
    deltas = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)]

    for i, (r, c) in enumerate(cells):
        for dr, dc in deltas:
            j = idx.get((r + dr, c + dc))
            if j is not None:
                neigh[i].append(j)

    rs = [r for r, _ in cells]
    cs = [c for _, c in cells]
    ds = [r - c for r, c in cells]

    min_r, max_r = min(rs), max(rs)
    min_c, max_c = min(cs), max(cs)
    min_d, max_d = min(ds), max(ds)

    # Standard Havannah-on-skew-grid corners.
    corner_coords = [
        (min_r, min_c),
        (min_r, min_r - min_d),
        (max_c + min_d, max_c),
        (max_r, max_c),
        (max_r, max_r - max_d),
        (min_c + max_d, min_c),
    ]
    corners = [idx[c] for c in corner_coords if c in idx]

    # Fallback for unusual but still valid masks.
    if len(corners) != 6:
        corners = [i for i in range(m) if len(neigh[i]) == 3]

    corner_set = set(corners)
    corner_bit = [0] * m
    for k, i in enumerate(corners):
        corner_bit[i] = 1 << k

    # Edge ids in clockwise order:
    # 0 top(r=min), 1 upper-right(d=min), 2 lower-right(c=max),
    # 3 bottom(r=max), 4 lower-left(d=max), 5 upper-left(c=min)
    edge_bit = [0] * m
    edges = [[] for _ in range(6)]
    boundary = []

    for i, (r, c) in enumerate(cells):
        d = r - c
        on = []
        if r == min_r:
            on.append(0)
        if d == min_d:
            on.append(1)
        if c == max_c:
            on.append(2)
        if r == max_r:
            on.append(3)
        if d == max_d:
            on.append(4)
        if c == min_c:
            on.append(5)

        if on or len(neigh[i]) < 6:
            boundary.append(i)

        if i in corner_set:
            continue

        if on:
            for e in on:
                edges[e].append(i)
            # On a standard board, a non-corner boundary cell belongs to exactly one edge.
            edge_bit[i] = 1 << on[0]

    if corners:
        best = None
        best_key = None
        for i in range(m):
            dlist = [_hex_dist(cells[i], cells[c]) for c in corners]
            key = (max(dlist), sum(dlist))
            if best_key is None or key < best_key:
                best_key = key
                best = i
        center = best
    else:
        # Very defensive fallback.
        center = min(
            range(m),
            key=lambda i: abs(cells[i][0] - n // 2) + abs(cells[i][1] - n // 2),
        )

    center_dist = [_hex_dist(cells[i], cells[center]) for i in range(m)]

    return {
        "sig": sig,
        "N": n,
        "M": m,
        "cells": cells,
        "idx": idx,
        "neigh": neigh,
        "corners": corners,
        "corner_bit": corner_bit,
        "edge_bit": edge_bit,
        "edges": edges,
        "boundary": boundary,
        "center": center,
        "center_dist": center_dist,
    }


def _get_geom(valid_mask):
    global _GEOM_CACHE
    try:
        sig = (tuple(valid_mask.shape), valid_mask.tobytes())
    except Exception:
        sig = tuple(tuple(bool(x) for x in row) for row in valid_mask)

    if _GEOM_CACHE is None or _GEOM_CACHE["sig"] != sig:
        _GEOM_CACHE = _build_geom(valid_mask, sig)
    return _GEOM_CACHE


def _analyze_player(stones, geom):
    m = geom["M"]
    comp_id = [-1] * m
    sizes = []
    cmasks = []
    emasks = []

    for s in stones:
        if comp_id[s] != -1:
            continue
        cid = len(sizes)
        stack = [s]
        comp_id[s] = cid
        sz = 0
        cm = 0
        em = 0

        while stack:
            u = stack.pop()
            sz += 1
            cm |= geom["corner_bit"][u]
            em |= geom["edge_bit"][u]
            for v in geom["neigh"][u]:
                if v in stones and comp_id[v] == -1:
                    comp_id[v] = cid
                    stack.append(v)

        sizes.append(sz)
        cmasks.append(cm)
        emasks.append(em)

    return {
        "comp_id": comp_id,
        "sizes": sizes,
        "cmasks": cmasks,
        "emasks": emasks,
    }


def _move_merge_info(move, analysis, geom):
    used = set()
    own_neighbors = 0
    merged_size = 1
    cmask = geom["corner_bit"][move]
    emask = geom["edge_bit"][move]

    for v in geom["neigh"][move]:
        cid = analysis["comp_id"][v]
        if cid != -1:
            own_neighbors += 1
            if cid not in used:
                used.add(cid)
                merged_size += analysis["sizes"][cid]
                cmask |= analysis["cmasks"][cid]
                emask |= analysis["emasks"][cid]

    return merged_size, cmask, emask, own_neighbors, len(used)


def _has_ring_floodfill(stones, geom):
    # Conservative enclosure test: if some non-stone cell is cut off from the boundary,
    # then a ring exists.
    m = geom["M"]
    blocked = [False] * m
    for s in stones:
        blocked[s] = True

    seen = [False] * m
    q = deque()

    for b in geom["boundary"]:
        if not blocked[b] and not seen[b]:
            seen[b] = True
            q.append(b)

    while q:
        u = q.popleft()
        for v in geom["neigh"][u]:
            if not blocked[v] and not seen[v]:
                seen[v] = True
                q.append(v)

    for i in range(m):
        if not blocked[i] and not seen[i]:
            return True
    return False


def _has_long_cycle_with_move(stones, move, geom):
    # Ring approximation via cycle length: a genuine Havannah ring needs at least 6 stones.
    # So if the new move joins two neighboring stones that already have a path of length >= 4,
    # then move + path gives a cycle of length >= 6.
    nbrs = [v for v in geom["neigh"][move] if v in stones]
    if len(nbrs) < 2:
        return False

    m = geom["M"]
    target_set = set(nbrs)

    for s in nbrs:
        dist = [-1] * m
        dist[s] = 0
        q = deque([s])

        while q:
            u = q.popleft()
            du = dist[u]
            for v in geom["neigh"][u]:
                if v in stones and dist[v] == -1:
                    dist[v] = du + 1
                    q.append(v)

        for t in target_set:
            if t != s and dist[t] >= 4:
                return True

    return False


def _is_winning_move(stones, move, analysis, geom):
    merged_size, cmask, emask, own_neighbors, _ = _move_merge_info(move, analysis, geom)

    # Bridge or fork
    if cmask.bit_count() >= 2 or emask.bit_count() >= 3:
        return True

    # Ring
    if own_neighbors < 2 or merged_size < 6:
        return False

    # Fast cycle-based ring check
    if _has_long_cycle_with_move(stones, move, geom):
        return True

    # More conservative enclosure test
    stones.add(move)
    try:
        return _has_ring_floodfill(stones, geom)
    finally:
        stones.remove(move)


def _multi_source_dist(targets, own_bool, blocked_bool, geom):
    m = geom["M"]
    dist = [INF] * m
    q = deque()

    for t in targets:
        if blocked_bool[t]:
            continue
        d = 0 if own_bool[t] else 1
        if d < dist[t]:
            dist[t] = d
            if d == 0:
                q.appendleft(t)
            else:
                q.append(t)

    while q:
        u = q.popleft()
        du = dist[u]
        for v in geom["neigh"][u]:
            if blocked_bool[v]:
                continue
            nd = du if own_bool[v] else du + 1
            if nd < dist[v]:
                dist[v] = nd
                if own_bool[v]:
                    q.appendleft(v)
                else:
                    q.append(v)

    return dist


def _distance_maps(own_set, opp_set, geom):
    m = geom["M"]
    own_bool = [False] * m
    opp_bool = [False] * m

    for s in own_set:
        own_bool[s] = True
    for s in opp_set:
        opp_bool[s] = True

    corner_dists = [_multi_source_dist([c], own_bool, opp_bool, geom) for c in geom["corners"]]
    edge_dists = [_multi_source_dist(edge, own_bool, opp_bool, geom) for edge in geom["edges"]]
    return corner_dists, edge_dists


def _best_need(dist_maps, move, k):
    vals = []
    for dist in dist_maps:
        d = dist[move]
        if d < INF:
            vals.append(max(0, d - 1))
    if len(vals) < k:
        return 99
    vals.sort()
    return sum(vals[:k])


def _base_score(
    move,
    my_set,
    opp_set,
    my_an,
    opp_an,
    my_corner_d,
    my_edge_d,
    opp_corner_d,
    opp_edge_d,
    geom,
    phase,
):
    merged_size, cmask, emask, own_neighbors, own_comp_cnt = _move_merge_info(move, my_an, geom)

    enemy_neighbors = 0
    enemy_comps = set()
    for v in geom["neigh"][move]:
        cid = opp_an["comp_id"][v]
        if cid != -1:
            enemy_neighbors += 1
            enemy_comps.add(cid)

    local_empty = len(geom["neigh"][move]) - own_neighbors - enemy_neighbors

    my_bridge_need = _best_need(my_corner_d, move, 2)
    my_fork_need = _best_need(my_edge_d, move, 3)
    opp_bridge_need = _best_need(opp_corner_d, move, 2)
    opp_fork_need = _best_need(opp_edge_d, move, 3)

    if phase < 8:
        center_w = 3.5
        bridge_w = 3.0
        fork_w = 2.5
    elif phase < 24:
        center_w = 2.2
        bridge_w = 3.8
        fork_w = 3.0
    else:
        center_w = 1.2
        bridge_w = 4.4
        fork_w = 3.6

    score = 0.0
    score += 5.0 * merged_size
    score += 18.0 * max(0, own_comp_cnt - 1)
    score += 6.0 * own_neighbors
    score += 2.0 * enemy_neighbors
    score += 4.0 * len(enemy_comps)
    score += 8.0 * cmask.bit_count()
    score += 5.0 * emask.bit_count()
    score += max(0, 12 - geom["center_dist"][move]) * center_w
    score += max(0, 8 - my_bridge_need) * bridge_w
    score += max(0, 10 - my_fork_need) * fork_w
    score += max(0, 7 - opp_bridge_need) * 2.5
    score += max(0, 9 - opp_fork_need) * 2.0
    score += 0.8 * local_empty

    if my_set and own_neighbors == 0 and enemy_neighbors == 0:
        score -= 10.0
    elif my_set and own_neighbors == 0:
        score -= 4.0

    return score


def _policy_impl(me, opp, valid_mask):
    geom = _get_geom(valid_mask)

    raw0 = set()
    raw1 = set()
    for p in me:
        q = tuple(p)
        i = geom["idx"].get(q)
        if i is not None:
            raw0.add(i)
    for p in opp:
        q = tuple(p)
        i = geom["idx"].get(q)
        if i is not None:
            raw1.add(i)

    # The prompt text is a little ambiguous about whether "me/opp" are fixed player-0/player-1
    # or current-player/opponent. To be robust, infer side-to-move as the side with fewer stones,
    # with player-0-to-move on equal counts.
    if len(raw0) <= len(raw1):
        my_set = raw0
        opp_set = raw1
    else:
        my_set = raw1
        opp_set = raw0

    occupied = my_set | opp_set
    legal = [i for i in range(geom["M"]) if i not in occupied]

    if not legal:
        return geom["cells"][geom["center"]]

    if not occupied and geom["center"] in legal:
        return geom["cells"][geom["center"]]

    my_an = _analyze_player(my_set, geom)
    opp_an = _analyze_player(opp_set, geom)

    my_corner_d, my_edge_d = _distance_maps(my_set, opp_set, geom)
    opp_corner_d, opp_edge_d = _distance_maps(opp_set, my_set, geom)

    phase = len(occupied)
    base_scores = {}
    for m in legal:
        base_scores[m] = _base_score(
            m,
            my_set,
            opp_set,
            my_an,
            opp_an,
            my_corner_d,
            my_edge_d,
            opp_corner_d,
            opp_edge_d,
            geom,
            phase,
        )

    ordered = sorted(
        legal,
        key=lambda i: (base_scores[i], -geom["center_dist"][i]),
        reverse=True,
    )

    # 1) Win now if possible.
    for m in ordered:
        if _is_winning_move(my_set, m, my_an, geom):
            return geom["cells"][m]

    # 2) Otherwise block any opponent immediate win.
    opp_wins = [m for m in legal if _is_winning_move(opp_set, m, opp_an, geom)]
    if opp_wins:
        best_block = max(
            opp_wins,
            key=lambda i: (base_scores.get(i, -10**18), -geom["center_dist"][i]),
        )
        return geom["cells"][best_block]

    # 3) Prefer moves that create multiple immediate winning threats next turn.
    best_move = ordered[0]
    best_score = -10**18

    for m in ordered:
        new_my = set(my_set)
        new_my.add(m)
        new_an = _analyze_player(new_my, geom)

        threats = 0
        for n in ordered:
            if n == m:
                continue
            if _is_winning_move(new_my, n, new_an, geom):
                threats += 1
                if threats >= 2:
                    break

        score = base_scores[m] + 6000.0 * threats
        if threats >= 2:
            score += 40000.0

        if score > best_score:
            best_score = score
            best_move = m

    return geom["cells"][best_move]


def policy(me, opp, valid_mask):
    try:
        return _policy_impl(me, opp, valid_mask)
    except Exception:
        # Must always return a legal move.
        occupied = {tuple(x) for x in me} | {tuple(x) for x in opp}
        n = len(valid_mask)
        for r in range(n):
            for c in range(n):
                if bool(valid_mask[r][c]) and (r, c) not in occupied:
                    return (r, c)
        # Last-ditch fallback for impossible/terminal positions.
        for r in range(n):
            for c in range(n):
                if bool(valid_mask[r][c]):
                    return (r, c)
        return (0, 0)
