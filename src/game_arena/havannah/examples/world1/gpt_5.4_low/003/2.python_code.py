
from collections import deque
from functools import lru_cache

# Symmetric hex-neighbor model on skewed coordinates.
# This is a common embedding for Havannah-like hex boards.
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    n = len(valid_mask)
    me_set = set(map(tuple, me))
    opp_set = set(map(tuple, opp))
    occupied = me_set | opp_set

    info = _board_info(valid_mask)
    valid_cells = info["valid_cells"]

    empties = [p for p in valid_cells if p not in occupied]
    if not empties:
        # Should never happen in a normal game, but return something legal-looking if possible.
        for r in range(n):
            for c in range(n):
                if valid_mask[r][c]:
                    return (r, c)
        return (0, 0)

    # 1) Immediate winning move for us (bridge/fork)
    for mv in empties:
        if _is_winning_bridge_or_fork(me_set, mv, info):
            return mv

    # 2) Immediate opponent threats: block if possible
    opp_wins = []
    for mv in empties:
        if _is_winning_bridge_or_fork(opp_set, mv, info):
            opp_wins.append(mv)

    if opp_wins:
        # If multiple threats exist, pick the best blocking move among them.
        best_mv = None
        best_score = -10**18
        my_comps = _components(me_set, info)
        opp_comps = _components(opp_set, info)
        for mv in opp_wins:
            score = _heuristic_score(mv, me_set, opp_set, my_comps, opp_comps, info, block_bonus=True)
            if score > best_score:
                best_score = score
                best_mv = mv
        if best_mv is not None:
            return best_mv

    # 3) General heuristic search
    my_comps = _components(me_set, info)
    opp_comps = _components(opp_set, info)

    best_mv = None
    best_score = -10**18
    for mv in empties:
        score = _heuristic_score(mv, me_set, opp_set, my_comps, opp_comps, info, block_bonus=False)
        if score > best_score:
            best_score = score
            best_mv = mv

    if best_mv is not None:
        return best_mv

    # 4) Guaranteed legal fallback
    return empties[0]


def _neighbors(cell, valid_mask):
    n = len(valid_mask)
    r, c = cell
    out = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < n and 0 <= cc < n and valid_mask[rr][cc]:
            out.append((rr, cc))
    return out


def _board_info(valid_mask):
    key = _mask_key(valid_mask)
    return _board_info_cached(key, len(valid_mask))


def _mask_key(valid_mask):
    # Works for python lists or numpy arrays
    return tuple(tuple(bool(x) for x in row) for row in valid_mask)


@lru_cache(maxsize=8)
def _board_info_cached(mask_key, n):
    valid_cells = []
    for r in range(n):
        row = mask_key[r]
        for c in range(n):
            if row[c]:
                valid_cells.append((r, c))

    valid_set = set(valid_cells)

    neigh = {}
    deg = {}
    for p in valid_cells:
        r, c = p
        ns = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n and mask_key[rr][cc]:
                ns.append((rr, cc))
        neigh[p] = ns
        deg[p] = len(ns)

    boundary = {p for p in valid_cells if deg[p] < 6}

    # Havannah corners are typically the 6 boundary cells with minimum degree.
    # Usually they have degree 3 in this embedding.
    min_deg = min(deg[p] for p in boundary) if boundary else 0
    corners = [p for p in boundary if deg[p] == min_deg]

    # If for some reason we do not get exactly 6, fall back to geometric extremes.
    if len(corners) != 6:
        corners = _fallback_corners(valid_cells)

    corner_set = set(corners)

    # Boundary graph
    bneigh = {p: [q for q in neigh[p] if q in boundary] for p in boundary}

    # Order boundary cycle
    cycle = _boundary_cycle(boundary, bneigh, corners)

    # Map corners in cycle order
    corner_pos = []
    corner_in_cycle = set(corners)
    for i, p in enumerate(cycle):
        if p in corner_in_cycle:
            corner_pos.append(i)

    # Deduplicate if cycle includes start corner again
    ordered_corners = []
    seen = set()
    for i in corner_pos:
        p = cycle[i]
        if p not in seen:
            ordered_corners.append(p)
            seen.add(p)

    if len(ordered_corners) != 6:
        ordered_corners = corners[:6]

    corner_id = {p: i for i, p in enumerate(ordered_corners)}

    edge_id = {}
    if cycle and len(ordered_corners) == 6:
        idxs = [i for i, p in enumerate(cycle) if p in corner_id]
        # keep unique corner positions in traversal order
        tmp = []
        used = set()
        for i in idxs:
            p = cycle[i]
            if p not in used:
                tmp.append(i)
                used.add(p)
        idxs = tmp

        m = len(cycle)
        for k in range(6):
            a = idxs[k]
            b = idxs[(k + 1) % 6]
            i = (a + 1) % m
            while i != b:
                p = cycle[i]
                if p not in corner_id:
                    edge_id[p] = k
                i = (i + 1) % m

    # Center estimate for heuristics
    cr = sum(r for r, c in valid_cells) / len(valid_cells)
    cc = sum(c for r, c in valid_cells) / len(valid_cells)

    return {
        "n": n,
        "valid_cells": valid_cells,
        "valid_set": valid_set,
        "neighbors": neigh,
        "boundary": boundary,
        "corners": ordered_corners,
        "corner_id": corner_id,
        "edge_id": edge_id,
        "center": (cr, cc),
        "mask_key": mask_key,
    }


def _fallback_corners(valid_cells):
    # Pick 6 extreme cells in different directions.
    # This is only a fallback.
    candidates = []
    funcs = [
        lambda p: (p[0], p[1]),
        lambda p: (p[1], p[0]),
        lambda p: (p[0] + p[1], p[0]),
        lambda p: (p[0] - p[1], p[0]),
        lambda p: (-p[0], p[1]),
        lambda p: (-p[1], p[0]),
    ]
    picked = set()
    for f in funcs:
        best = min(valid_cells, key=f)
        picked.add(best)
    if len(picked) < 6:
        # fill from more extremes
        extras = sorted(valid_cells, key=lambda p: (p[0] + p[1], p[0], p[1]))
        for p in extras:
            picked.add(p)
            if len(picked) == 6:
                break
    return list(picked)[:6]


def _boundary_cycle(boundary, bneigh, corners):
    if not boundary:
        return []
    start = corners[0] if corners else next(iter(boundary))

    # Try walking around boundary using local continuation.
    ns = bneigh[start]
    if not ns:
        return [start]
    prev = None
    cur = start
    cycle = []
    seen_steps = set()

    for _ in range(len(boundary) + 5):
        cycle.append(cur)
        nxts = bneigh[cur]
        if prev is None:
            nxt = nxts[0]
        else:
            if len(nxts) == 1:
                nxt = nxts[0]
            else:
                nxt = nxts[0] if nxts[1] == prev else nxts[1]
        prev, cur = cur, nxt
        if cur == start:
            break
        state = (prev, cur)
        if state in seen_steps:
            break
        seen_steps.add(state)

    return cycle


def _components(stones, info):
    neigh = info["neighbors"]
    corner_id = info["corner_id"]
    edge_id = info["edge_id"]

    comp_index = {}
    comps = []
    seen = set()

    for s in stones:
        if s in seen:
            continue
        q = deque([s])
        seen.add(s)
        cells = []
        touched_corners = set()
        touched_edges = set()

        while q:
            x = q.popleft()
            comp_index[x] = len(comps)
            cells.append(x)

            if x in corner_id:
                touched_corners.add(corner_id[x])
            if x in edge_id:
                touched_edges.add(edge_id[x])

            for y in neigh[x]:
                if y in stones and y not in seen:
                    seen.add(y)
                    q.append(y)

        comps.append({
            "cells": cells,
            "size": len(cells),
            "corners": touched_corners,
            "edges": touched_edges,
        })

    return {"index": comp_index, "comps": comps}


def _is_winning_bridge_or_fork(stones, move, info):
    neigh = info["neighbors"]
    corner_id = info["corner_id"]
    edge_id = info["edge_id"]

    seen_comp_ids = set()
    touched_corners = set()
    touched_edges = set()

    if move in corner_id:
        touched_corners.add(corner_id[move])
    if move in edge_id:
        touched_edges.add(edge_id[move])

    # Explore only merged neighborhood through adjacent components
    visited = {move}
    q = deque()

    for nb in neigh[move]:
        if nb in stones and nb not in visited:
            visited.add(nb)
            q.append(nb)

    while q:
        x = q.popleft()
        if x in corner_id:
            touched_corners.add(corner_id[x])
        if x in edge_id:
            touched_edges.add(edge_id[x])

        for y in neigh[x]:
            if y in stones and y not in visited:
                visited.add(y)
                q.append(y)

    return len(touched_corners) >= 2 or len(touched_edges) >= 3


def _heuristic_score(move, me_set, opp_set, my_comps, opp_comps, info, block_bonus=False):
    neigh = info["neighbors"]
    corner_id = info["corner_id"]
    edge_id = info["edge_id"]
    center_r, center_c = info["center"]

    adj_me = 0
    adj_opp = 0
    my_ids = set()
    opp_ids = set()

    for nb in neigh[move]:
        if nb in me_set:
            adj_me += 1
            cid = my_comps["index"].get(nb)
            if cid is not None:
                my_ids.add(cid)
        elif nb in opp_set:
            adj_opp += 1
            cid = opp_comps["index"].get(nb)
            if cid is not None:
                opp_ids.add(cid)

    merged_size = 1
    merged_corners = set()
    merged_edges = set()

    if move in corner_id:
        merged_corners.add(corner_id[move])
    if move in edge_id:
        merged_edges.add(edge_id[move])

    for cid in my_ids:
        comp = my_comps["comps"][cid]
        merged_size += comp["size"]
        merged_corners |= comp["corners"]
        merged_edges |= comp["edges"]

    # Structural potential
    score = 0
    score += 18 * adj_me
    score += 10 * len(my_ids)
    score += 2 * merged_size
    score += 30 * len(merged_corners)
    score += 20 * len(merged_edges)

    # Blocking / interference
    score += 8 * adj_opp
    score += 6 * len(opp_ids)
    if block_bonus:
        score += 200

    # Immediate next-step potential: if this move puts us close to bridge/fork, reward it
    if len(merged_corners) >= 2:
        score += 5000
    if len(merged_edges) >= 3:
        score += 5000
    if len(merged_corners) == 1 and len(merged_edges) >= 2:
        score += 40
    if len(merged_edges) == 2:
        score += 30

    # Centrality
    # A simple Euclidean-like bias toward center.
    dr = move[0] - center_r
    dc = move[1] - center_c
    score -= 0.8 * (dr * dr + dc * dc)

    # Slight preference for boundary strategic points, but not too much
    if move in corner_id:
        score += 15
    elif move in edge_id:
        score += 6

    # Mild anti-isolation penalty
    if adj_me == 0 and adj_opp == 0:
        score -= 8

    return score
