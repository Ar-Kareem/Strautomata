
# Havannah policy for a 15x15 masked hex board.
# The policy is deterministic, tactical, and always falls back to a legal move.

_GEOM_CACHE = {}


def _bit_count(x):
    return x.bit_count()


def _dir_offsets(col):
    # Odd-q vertical offset layout. This matches the example:
    # (4,1) touches (3,0), (4,0), (3,1), (5,1), (3,2), (4,2).
    if col & 1:
        return (
            (-1, 0),   # N
            (-1, 1),   # NE
            (0, 1),    # SE
            (1, 0),    # S
            (0, -1),   # SW
            (-1, -1),  # NW
        )
    return (
        (-1, 0),   # N
        (0, 1),    # NE
        (1, 1),    # SE
        (1, 0),    # S
        (1, -1),   # SW
        (0, -1),   # NW
    )


def _cube_coord(r, c):
    # Axial/cube coordinates for the odd-q offset system.
    x = c
    z = r - ((c + (c & 1)) // 2)
    y = -x - z
    return x, y, z


def _fallback_legal(valid_mask, me, opp):
    occupied = set(tuple(p) for p in me) | set(tuple(p) for p in opp)
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0
    cr = (rows - 1) / 2.0
    cc = (cols - 1) / 2.0

    best = None
    best_d = 10 ** 18
    for r in range(rows):
        for c in range(cols):
            try:
                ok = bool(valid_mask[r][c])
            except Exception:
                ok = False
            if ok and (r, c) not in occupied:
                d = (r - cr) * (r - cr) + (c - cc) * (c - cc)
                if d < best_d:
                    best_d = d
                    best = (r, c)

    if best is not None:
        return best

    # A full board should not be queried, but return something shaped correctly.
    return (0, 0)


def _make_geom(valid_mask):
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0

    cells = []
    index = {}
    bits = []

    for r in range(rows):
        for c in range(cols):
            v = bool(valid_mask[r][c])
            bits.append(1 if v else 0)
            if v:
                index[(r, c)] = len(cells)
                cells.append((r, c))

    n = len(cells)
    neighbors = [[] for _ in range(n)]

    for i, (r, c) in enumerate(cells):
        for dr, dc in _dir_offsets(c):
            rr, cc = r + dr, c + dc
            j = index.get((rr, cc))
            if j is not None:
                neighbors[i].append(j)

    cubes = [_cube_coord(r, c) for r, c in cells]
    if n:
        xs = [p[0] for p in cubes]
        ys = [p[1] for p in cubes]
        zs = [p[2] for p in cubes]
        minx, maxx = min(xs), max(xs)
        miny, maxy = min(ys), max(ys)
        minz, maxz = min(zs), max(zs)
    else:
        minx = maxx = miny = maxy = minz = maxz = 0

    # Six side bits: x-min, x-max, y-min, y-max, z-min, z-max.
    extreme_bits = [0] * n
    corner_candidates = []
    for i, (x, y, z) in enumerate(cubes):
        b = 0
        if x == minx:
            b |= 1 << 0
        if x == maxx:
            b |= 1 << 1
        if y == miny:
            b |= 1 << 2
        if y == maxy:
            b |= 1 << 3
        if z == minz:
            b |= 1 << 4
        if z == maxz:
            b |= 1 << 5
        extreme_bits[i] = b
        if _bit_count(b) >= 2:
            corner_candidates.append(i)

    if len(corner_candidates) == 6:
        corners = corner_candidates
    else:
        deg3 = [i for i in range(n) if len(neighbors[i]) == 3]
        if len(deg3) == 6:
            corners = deg3
        else:
            # Robust fallback: choose six low-degree, far-from-center boundary cells.
            avg_r = sum(r for r, c in cells) / float(max(1, n))
            avg_c = sum(c for r, c in cells) / float(max(1, n))
            boundary = [i for i in range(n) if len(neighbors[i]) < 6]
            boundary.sort(
                key=lambda i: (
                    len(neighbors[i]),
                    -((cells[i][0] - avg_r) ** 2 + (cells[i][1] - avg_c) ** 2),
                )
            )
            corners = boundary[:6]

    corner_set = set(corners)
    corner_bit = [0] * n
    for k, i in enumerate(corners[:6]):
        corner_bit[i] = 1 << k

    edge_bit = [0] * n
    for i in range(n):
        if i not in corner_set:
            edge_bit[i] = extreme_bits[i] & 63

    # Center ordering / center scores.
    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    cz = (minz + maxz) / 2.0
    dists = []
    for i, (x, y, z) in enumerate(cubes):
        d = max(abs(x - cx), abs(y - cy), abs(z - cz))
        dists.append(d)
    maxd = max(dists) if dists else 1.0
    if maxd <= 0:
        maxd = 1.0

    center_score = [(maxd - d) / maxd for d in dists]
    center_order = sorted(range(n), key=lambda i: (-center_score[i], cells[i]))

    noise = [((cells[i][0] * 37 + cells[i][1] * 91 + 17) % 100) / 10000.0 for i in range(n)]

    return {
        "rows": rows,
        "cols": cols,
        "cells": cells,
        "index": index,
        "neighbors": neighbors,
        "n": n,
        "corner_bit": corner_bit,
        "edge_bit": edge_bit,
        "center_score": center_score,
        "center_order": center_order,
        "noise": noise,
        "mask_key_bits": tuple(bits),
    }


def _get_geom(valid_mask):
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0
    bits = []
    for r in range(rows):
        for c in range(cols):
            bits.append(1 if bool(valid_mask[r][c]) else 0)
    key = (rows, cols, tuple(bits))

    geom = _GEOM_CACHE.get(key)
    if geom is None:
        geom = _make_geom(valid_mask)
        _GEOM_CACHE[key] = geom
    return geom


def _build_info(stones, geom):
    n = geom["n"]
    neighbors = geom["neighbors"]
    corner_bit = geom["corner_bit"]
    edge_bit = geom["edge_bit"]

    comp_of = [-1] * n
    comps = []

    for s in stones:
        if comp_of[s] != -1:
            continue

        cid = len(comps)
        comp_of[s] = cid
        stack = [s]
        size = 0
        edge_twice = 0
        cm = 0
        em = 0

        while stack:
            v = stack.pop()
            size += 1
            cm |= corner_bit[v]
            em |= edge_bit[v]

            for nb in neighbors[v]:
                if nb in stones:
                    edge_twice += 1
                    if comp_of[nb] == -1:
                        comp_of[nb] = cid
                        stack.append(nb)

        comps.append((size, edge_twice // 2, cm, em))

    return comp_of, comps


def _move_meta(move, info, geom):
    comp_of, comps = info
    neighbors = geom["neighbors"]
    cm = geom["corner_bit"][move]
    em = geom["edge_bit"][move]

    seen = set()
    ids = []
    neigh_count = 0

    for nb in neighbors[move]:
        cid = comp_of[nb]
        if cid >= 0:
            neigh_count += 1
            if cid not in seen:
                seen.add(cid)
                ids.append(cid)

    nodes = 1
    graph_edges = neigh_count

    for cid in ids:
        comp = comps[cid]
        nodes += comp[0]
        graph_edges += comp[1]
        cm |= comp[2]
        em |= comp[3]

    duplicate_touches = neigh_count - len(ids)
    return nodes, graph_edges, cm, em, ids, neigh_count, duplicate_touches


def _move_wins(move, info, geom):
    nodes, graph_edges, cm, em, ids, neigh_count, dup = _move_meta(move, info, geom)

    # Bridge: connected component touches at least two corners.
    if _bit_count(cm) >= 2:
        return True

    # Fork: connected component touches at least three non-corner edges.
    if _bit_count(em) >= 3:
        return True

    # Ring: in the hex adjacency graph, a cycle is a ring.
    if graph_edges >= nodes:
        return True

    return False


def _score_move(move, my_info, opp_info, geom, total_moves):
    my_comp_of, my_comps = my_info
    opp_comp_of, opp_comps = opp_info

    mnodes, medges, mcm, mem, mids, mncnt, mdup = _move_meta(move, my_info, geom)
    onodes, oedges, ocm, oem, oids, oncnt, odup = _move_meta(move, opp_info, geom)

    score = 0.0

    # Center control is most important in the opening, but remains useful.
    center_weight = max(8.0, 38.0 - 0.18 * total_moves)
    score += center_weight * geom["center_score"][move]

    # Prefer flexible cells with empty neighboring space.
    empty_neighbors = 0
    for nb in geom["neighbors"][move]:
        if my_comp_of[nb] < 0 and opp_comp_of[nb] < 0:
            empty_neighbors += 1
    score += 2.0 * empty_neighbors

    # Own structure growth.
    own_join_size = sum(min(my_comps[cid][0], 12) for cid in mids)
    own_edges = _bit_count(mem)
    own_corners = _bit_count(mcm)

    score += 14.0 * mncnt
    score += 18.0 * len(mids)
    score += 2.0 * min(mnodes, 35)
    score += 3.0 * own_join_size

    if len(mids) >= 2:
        score += 42.0 * (len(mids) - 1)
        score += 5.0 * own_join_size

    if mncnt >= 2:
        score += 14.0

    if mdup > 0:
        score += 130.0 * mdup

    if own_edges == 1:
        score += 18.0
    elif own_edges == 2:
        score += 230.0
    elif own_edges >= 3:
        score += 1400.0

    if own_corners == 1:
        score += 35.0
    elif own_corners >= 2:
        score += 1100.0

    if own_edges >= 1 and own_corners >= 1:
        score += 22.0

    # Avoid isolated non-blocking moves after the opening.
    if mncnt == 0 and total_moves > 5:
        score -= 16.0

    # Do not rush low-flexibility edge/corner cells too early unless useful.
    if total_moves < 12:
        if geom["corner_bit"][move]:
            score -= 10.0
        elif geom["edge_bit"][move]:
            score -= 5.0

    # Defensive value: occupying points the opponent would like.
    opp_join_size = sum(min(opp_comps[cid][0], 12) for cid in oids)
    opp_edges = _bit_count(oem)
    opp_corners = _bit_count(ocm)

    defensive = 0.0
    defensive += 11.0 * oncnt
    defensive += 16.0 * len(oids)
    defensive += 1.6 * min(onodes, 35)
    defensive += 2.7 * opp_join_size

    if len(oids) >= 2:
        defensive += 38.0 * (len(oids) - 1)
        defensive += 4.0 * opp_join_size

    if oncnt >= 2:
        defensive += 12.0

    if odup > 0:
        defensive += 160.0 * odup

    if opp_edges == 1:
        defensive += 12.0
    elif opp_edges == 2:
        defensive += 215.0
    elif opp_edges >= 3:
        defensive += 1200.0

    if opp_corners == 1:
        defensive += 28.0
    elif opp_corners >= 2:
        defensive += 950.0

    score += 0.92 * defensive

    # Tiny deterministic tie-breaker.
    score += geom["noise"][move]

    return score


def _policy_core(me, opp, valid_mask):
    geom = _get_geom(valid_mask)
    idx = geom["index"]
    coords = geom["cells"]

    me_set = set()
    for p in me:
        t = tuple(p)
        if t in idx:
            me_set.add(idx[t])

    opp_set = set()
    for p in opp:
        t = tuple(p)
        if t in idx:
            opp_set.add(idx[t])

    occupied = me_set | opp_set
    empties = [i for i in range(geom["n"]) if i not in occupied]

    if not empties:
        return _fallback_legal(valid_mask, me, opp)

    total_moves = len(me_set) + len(opp_set)

    # Opening: take the most central legal point.
    if total_moves == 0:
        return coords[geom["center_order"][0]]

    my_info = _build_info(me_set, geom)
    opp_info = _build_info(opp_set, geom)

    # 1. Win immediately if possible.
    for m in empties:
        if _move_wins(m, my_info, geom):
            return coords[m]

    # 2. Block opponent immediate wins.
    opp_wins = [m for m in empties if _move_wins(m, opp_info, geom)]
    if opp_wins:
        best = max(
            opp_wins,
            key=lambda m: _score_move(m, my_info, opp_info, geom, total_moves),
        )
        return coords[best]

    # 3. Heuristic scoring of all legal moves.
    scored = [
        (_score_move(m, my_info, opp_info, geom, total_moves), m)
        for m in empties
    ]

    # 4. Limited double-threat search among the best heuristic candidates.
    # If a move creates two or more next-turn winning points, it is very strong.
    if total_moves >= 4 and len(empties) > 4:
        scored.sort(key=lambda x: x[0], reverse=True)
        top_n = min(12, len(scored))
        top_moves = set(m for _, m in scored[:top_n])

        adjusted = []
        for s, m in scored:
            if m in top_moves:
                new_stones = set(me_set)
                new_stones.add(m)
                new_info = _build_info(new_stones, geom)

                threats = 0
                for e in empties:
                    if e == m:
                        continue
                    if _move_wins(e, new_info, geom):
                        threats += 1
                        if threats >= 3:
                            break

                if threats >= 2:
                    s += 1000.0 + 300.0 * threats
                elif threats == 1:
                    s += 85.0

            adjusted.append((s, m))

        scored = adjusted

    best_move = max(scored, key=lambda x: x[0])[1]
    return coords[best_move]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        move = _policy_core(me, opp, valid_mask)

        # Final legality guard.
        r, c = move
        occupied = set(tuple(p) for p in me) | set(tuple(p) for p in opp)
        if bool(valid_mask[r][c]) and (r, c) not in occupied:
            return (r, c)

        return _fallback_legal(valid_mask, me, opp)

    except Exception:
        return _fallback_legal(valid_mask, me, opp)
