
from collections import deque

INF = 10**9
_GEOM_CACHE = {}


class CompData:
    __slots__ = ("comp_id", "sizes", "corner_masks", "edge_masks")

    def __init__(self, comp_id, sizes, corner_masks, edge_masks):
        self.comp_id = comp_id
        self.sizes = sizes
        self.corner_masks = corner_masks
        self.edge_masks = edge_masks


def _fallback_move(me, opp, valid_mask):
    occ = set((int(r), int(c)) for r, c in me) | set((int(r), int(c)) for r, c in opp)
    n = len(valid_mask)
    mid = (n - 1) / 2.0
    best = None
    best_key = None
    for r, row in enumerate(valid_mask):
        for c, v in enumerate(row):
            if bool(v) and (r, c) not in occ:
                key = ((r - mid) * (r - mid) + (c - mid) * (c - mid), r, c)
                if best_key is None or key < best_key:
                    best_key = key
                    best = (r, c)
    return best if best is not None else (0, 0)


def _mask_key(valid_mask):
    return tuple(tuple(bool(x) for x in row) for row in valid_mask)


def _neighbor_coords(r, c):
    # Column-offset hex coordinates matching the prompt example.
    # For odd columns (0-based), upper diagonals are used.
    if c & 1:
        return (
            (r - 1, c),
            (r + 1, c),
            (r - 1, c - 1),
            (r, c - 1),
            (r - 1, c + 1),
            (r, c + 1),
        )
    else:
        return (
            (r - 1, c),
            (r + 1, c),
            (r, c - 1),
            (r + 1, c - 1),
            (r, c + 1),
            (r + 1, c + 1),
        )


def _order_boundary_cycle(start, boundary_set, neighbors):
    bneigh = {i: [j for j in neighbors[i] if j in boundary_set] for i in boundary_set}
    starts = bneigh[start]
    for first in starts:
        order = [start]
        seen = {start}
        prev = start
        cur = first
        while True:
            if cur == start:
                if len(order) == len(boundary_set):
                    return order
                break
            if cur in seen:
                break
            order.append(cur)
            seen.add(cur)
            nxts = bneigh[cur]
            if not nxts:
                break
            if len(nxts) == 1:
                nxt = nxts[0]
            else:
                nxt = nxts[0] if nxts[0] != prev else nxts[1]
            prev, cur = cur, nxt
    raise ValueError("Could not order boundary cycle")


def _get_geom(valid_mask):
    key = _mask_key(valid_mask)
    geom = _GEOM_CACHE.get(key)
    if geom is not None:
        return geom

    n = len(valid_mask)
    coords = []
    coord_to_idx = {}
    for r in range(n):
        row = valid_mask[r]
        for c in range(len(row)):
            if bool(row[c]):
                coord_to_idx[(r, c)] = len(coords)
                coords.append((r, c))

    m = len(coords)
    neighbors = [[] for _ in range(m)]
    for i, (r, c) in enumerate(coords):
        lst = neighbors[i]
        for rr, cc in _neighbor_coords(r, c):
            j = coord_to_idx.get((rr, cc))
            if j is not None:
                lst.append(j)

    boundary = [i for i in range(m) if len(neighbors[i]) < 6]
    min_deg = min(len(neighbors[i]) for i in boundary)
    corners = [i for i in boundary if len(neighbors[i]) == min_deg]
    if len(corners) != 6:
        # Standard Havannah board should have exactly 6 degree-min boundary corners.
        # If not, fall back to degree<=3 boundary cells.
        corners = [i for i in boundary if len(neighbors[i]) <= 3]
        if len(corners) != 6:
            raise ValueError("Could not identify 6 corners")

    boundary_set = set(boundary)
    order = _order_boundary_cycle(corners[0], boundary_set, neighbors)
    corner_set = set(corners)
    corner_positions = [i for i, v in enumerate(order) if v in corner_set]
    if len(corner_positions) != 6:
        raise ValueError("Boundary ordering did not expose 6 corners")

    corner_cells = [order[p] for p in corner_positions]
    corner_id = [-1] * m
    for k, idx in enumerate(corner_cells):
        corner_id[idx] = k

    edge_id = [-1] * m
    edge_cells = [[] for _ in range(6)]
    L = len(order)
    for e in range(6):
        a = corner_positions[e]
        b = corner_positions[(e + 1) % 6]
        i = (a + 1) % L
        while i != b:
            idx = order[i]
            edge_id[idx] = e
            edge_cells[e].append(idx)
            i = (i + 1) % L

    corner_bit = [0] * m
    edge_bit = [0] * m
    for i in range(m):
        if corner_id[i] != -1:
            corner_bit[i] = 1 << corner_id[i]
        if edge_id[i] != -1:
            edge_bit[i] = 1 << edge_id[i]

    mid = (n - 1) / 2.0
    center_idx = min(
        range(m),
        key=lambda i: (
            (coords[i][0] - mid) * (coords[i][0] - mid)
            + (coords[i][1] - mid) * (coords[i][1] - mid),
            -len(neighbors[i]),
        ),
    )

    center_dist = [-1] * m
    dq = deque([center_idx])
    center_dist[center_idx] = 0
    while dq:
        u = dq.popleft()
        du = center_dist[u] + 1
        for v in neighbors[u]:
            if center_dist[v] == -1:
                center_dist[v] = du
                dq.append(v)
    max_cd = max(center_dist)
    center_score = [max_cd - d for d in center_dist]
    central_order = sorted(
        range(m),
        key=lambda i: (center_dist[i], -len(neighbors[i]), coords[i][0], coords[i][1]),
    )

    geom = {
        "N": n,
        "M": m,
        "coords": coords,
        "coord_to_idx": coord_to_idx,
        "neighbors": neighbors,
        "boundary": boundary,
        "corner_cells": corner_cells,
        "edge_cells": edge_cells,
        "corner_id": corner_id,
        "edge_id": edge_id,
        "corner_bit": corner_bit,
        "edge_bit": edge_bit,
        "center_idx": center_idx,
        "center_score": center_score,
        "central_order": central_order,
    }
    _GEOM_CACHE[key] = geom
    return geom


def _build_components(occ, geom):
    m = geom["M"]
    neighbors = geom["neighbors"]
    corner_bit = geom["corner_bit"]
    edge_bit = geom["edge_bit"]

    comp_id = [-1] * m
    sizes = []
    corner_masks = []
    edge_masks = []

    for i in range(m):
        if occ[i] and comp_id[i] == -1:
            cid = len(sizes)
            dq = deque([i])
            comp_id[i] = cid
            size = 0
            cm = 0
            em = 0
            while dq:
                u = dq.popleft()
                size += 1
                cm |= corner_bit[u]
                em |= edge_bit[u]
                for v in neighbors[u]:
                    if occ[v] and comp_id[v] == -1:
                        comp_id[v] = cid
                        dq.append(v)
            sizes.append(size)
            corner_masks.append(cm)
            edge_masks.append(em)

    return CompData(comp_id, sizes, corner_masks, edge_masks)


def _forms_ring_after_move(move, occ, geom):
    m = geom["M"]
    neighbors = geom["neighbors"]
    boundary = geom["boundary"]

    visited = [False] * m
    dq = deque()

    for b in boundary:
        if b != move and not occ[b]:
            visited[b] = True
            dq.append(b)

    while dq:
        u = dq.popleft()
        for v in neighbors[u]:
            if v == move or occ[v] or visited[v]:
                continue
            visited[v] = True
            dq.append(v)

    for i in range(m):
        if i != move and not occ[i] and not visited[i]:
            return True
    return False


def _is_winning_move(move, occ, comp, geom):
    neigh = geom["neighbors"][move]
    corner_mask = geom["corner_bit"][move]
    edge_mask = geom["edge_bit"][move]
    merged_size = 1
    friendly_neighbors = 0
    seen = set()

    for nb in neigh:
        if occ[nb]:
            friendly_neighbors += 1
            cid = comp.comp_id[nb]
            if cid not in seen:
                seen.add(cid)
                merged_size += comp.sizes[cid]
                corner_mask |= comp.corner_masks[cid]
                edge_mask |= comp.edge_masks[cid]

    if corner_mask.bit_count() >= 2:
        return True
    if edge_mask.bit_count() >= 3:
        return True
    if friendly_neighbors >= 2 and merged_size >= 6:
        return _forms_ring_after_move(move, occ, geom)
    return False


def _adjacent_empty_from_indices(indices, empty_mask, geom):
    out = set()
    neighbors = geom["neighbors"]
    for i in indices:
        for nb in neighbors[i]:
            if empty_mask[nb]:
                out.add(nb)
    return out


def _adjacent_empty_from_occ(occ, empty_mask, geom):
    out = set()
    neighbors = geom["neighbors"]
    for i, flag in enumerate(occ):
        if flag:
            for nb in neighbors[i]:
                if empty_mask[nb]:
                    out.add(nb)
    return out


def _two_step_empty_from_indices(indices, empty_mask, geom):
    out = set()
    neighbors = geom["neighbors"]
    for i in indices:
        for nb in neighbors[i]:
            for nb2 in neighbors[nb]:
                if empty_mask[nb2]:
                    out.add(nb2)
    return out


def _zero_one_dist(sources, own_occ, enemy_occ, geom):
    m = geom["M"]
    neighbors = geom["neighbors"]
    dist = [INF] * m
    dq = deque()

    for s in sources:
        if enemy_occ[s]:
            continue
        d0 = 0 if own_occ[s] else 1
        if d0 < dist[s]:
            dist[s] = d0
            if d0 == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in neighbors[u]:
            if enemy_occ[v]:
                continue
            w = 0 if own_occ[v] else 1
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)

    return dist


def _compute_dist_maps(own_occ, enemy_occ, geom):
    corner_dists = [
        _zero_one_dist([geom["corner_cells"][k]], own_occ, enemy_occ, geom)
        for k in range(6)
    ]
    edge_dists = [
        _zero_one_dist(geom["edge_cells"][k], own_occ, enemy_occ, geom)
        for k in range(6)
    ]
    return corner_dists, edge_dists


def _raw_move_value(
    mv,
    own_occ,
    enemy_occ,
    own_comp,
    enemy_comp,
    corner_dists,
    edge_dists,
    geom,
    phase,
):
    neighbors = geom["neighbors"][mv]

    own_adj = set()
    enemy_adj = set()
    own_nb = 0
    enemy_nb = 0
    merged_size = 1

    base_corner_mask = 0
    base_edge_mask = 0

    for nb in neighbors:
        if own_occ[nb]:
            own_nb += 1
            cid = own_comp.comp_id[nb]
            if cid not in own_adj:
                own_adj.add(cid)
                merged_size += own_comp.sizes[cid]
                base_corner_mask |= own_comp.corner_masks[cid]
                base_edge_mask |= own_comp.edge_masks[cid]
        elif enemy_occ[nb]:
            enemy_nb += 1
            cid = enemy_comp.comp_id[nb]
            if cid != -1:
                enemy_adj.add(cid)

    result_corner_mask = base_corner_mask | geom["corner_bit"][mv]
    result_edge_mask = base_edge_mask | geom["edge_bit"][mv]
    total_c = result_corner_mask.bit_count()
    total_e = result_edge_mask.bit_count()

    score = 0

    # Local connectivity and merging.
    score += 72 * own_nb
    score += 18 * merged_size
    k = len(own_adj)
    if k:
        score += 24
    score += 90 * k * k
    if own_nb >= 2:
        score += 18 * own_nb * own_nb

    # Strategic targets already present in the resulting connected component.
    score += 60 * total_c + 40 * total_e
    if k >= 2:
        score += 55 * total_c + 35 * total_e
    if geom["corner_bit"][mv]:
        score += 90
    if geom["edge_bit"][mv]:
        score += 55

    # Distance to still-unreached corners/edges.
    db = 0
    vals = []
    for i in range(6):
        if not ((result_corner_mask >> i) & 1):
            d = corner_dists[i][mv]
            if d < INF:
                vals.append(max(0, d - 1))
    vals.sort()
    if vals:
        db += 100 // (1 + vals[0])
    if len(vals) > 1:
        db += 75 // (1 + vals[1])

    vals = []
    for i in range(6):
        if not ((result_edge_mask >> i) & 1):
            d = edge_dists[i][mv]
            if d < INF:
                vals.append(max(0, d - 1))
    vals.sort()
    if vals:
        db += 95 // (1 + vals[0])
    if len(vals) > 1:
        db += 70 // (1 + vals[1])
    if len(vals) > 2:
        db += 50 // (1 + vals[2])

    support = min(3, own_nb + k)
    score += db * (2 + support) // 5

    # Contesting opponent space.
    score += 26 * enemy_nb
    if enemy_adj:
        score += 7 * sum(enemy_comp.sizes[c] for c in enemy_adj)

    # Shape preferences.
    if own_nb == 0 and enemy_nb == 0:
        score -= 60 if phase < 0.7 else 20

    score += int(max(0.0, 1.15 - phase) * 10 * geom["center_score"][mv])

    # Early isolated boundary moves are usually too loose.
    if phase < 0.18 and (geom["corner_id"][mv] != -1 or geom["edge_id"][mv] != -1) and own_nb == 0:
        score -= 70

    return score


def _count_future_wins_after_move(mv, own_occ, empty_mask, geom, limit=2):
    new_occ = own_occ[:]
    new_occ[mv] = True
    new_comp = _build_components(new_occ, geom)
    cands = _adjacent_empty_from_occ(new_occ, empty_mask, geom)
    if mv in cands:
        cands.remove(mv)

    count = 0
    for m2 in cands:
        if _is_winning_move(m2, new_occ, new_comp, geom):
            count += 1
            if count >= limit:
                return count
    return count


def _pick_centerish(moves, geom):
    return max(
        moves,
        key=lambda m: (
            geom["center_score"][m],
            -geom["coords"][m][0],
            -geom["coords"][m][1],
        ),
    )


def _pick_scored(moves, scores, geom):
    return max(
        moves,
        key=lambda m: (
            scores.get(m, -INF),
            geom["center_score"][m],
            -geom["coords"][m][0],
            -geom["coords"][m][1],
        ),
    )


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        geom = _get_geom(valid_mask)
        m = geom["M"]
        coords = geom["coords"]
        coord_to_idx = geom["coord_to_idx"]

        my_occ = [False] * m
        opp_occ = [False] * m
        my_indices = []
        opp_indices = []

        for r, c in me:
            idx = coord_to_idx.get((int(r), int(c)))
            if idx is not None and not my_occ[idx]:
                my_occ[idx] = True
                my_indices.append(idx)

        for r, c in opp:
            idx = coord_to_idx.get((int(r), int(c)))
            if idx is not None and not opp_occ[idx]:
                opp_occ[idx] = True
                opp_indices.append(idx)

        empty_mask = [not my_occ[i] and not opp_occ[i] for i in range(m)]
        legal = [i for i in range(m) if empty_mask[i]]
        if not legal:
            return _fallback_move(me, opp, valid_mask)

        total_stones = len(my_indices) + len(opp_indices)
        center_idx = geom["center_idx"]

        # Strong simple opening rule.
        if total_stones < 4 and empty_mask[center_idx]:
            return coords[center_idx]

        my_comp = _build_components(my_occ, geom)
        opp_comp = _build_components(opp_occ, geom)

        my_adj = _adjacent_empty_from_indices(my_indices, empty_mask, geom)
        opp_adj = _adjacent_empty_from_indices(opp_indices, empty_mask, geom)

        # 1) Immediate win.
        if my_adj:
            my_adj_order = sorted(
                my_adj,
                key=lambda mv: (
                    geom["center_score"][mv],
                    -coords[mv][0],
                    -coords[mv][1],
                ),
                reverse=True,
            )
            winning_now = [mv for mv in my_adj_order if _is_winning_move(mv, my_occ, my_comp, geom)]
            if winning_now:
                return coords[_pick_centerish(winning_now, geom)]

        # 2) Immediate block.
        if opp_adj:
            opp_adj_order = sorted(
                opp_adj,
                key=lambda mv: (
                    geom["center_score"][mv],
                    -coords[mv][0],
                    -coords[mv][1],
                ),
                reverse=True,
            )
            opp_winning_now = [mv for mv in opp_adj_order if _is_winning_move(mv, opp_occ, opp_comp, geom)]
            if opp_winning_now:
                # If there are multiple opponent immediate wins, this is usually lost anyway.
                # Still occupy one of them deterministically.
                return coords[_pick_centerish(opp_winning_now, geom)]

        # Build a frontier of plausible moves.
        frontier = set(my_adj) | set(opp_adj)
        all_stones = my_indices + opp_indices
        if len(frontier) < min(28, len(legal)) and all_stones:
            frontier |= _two_step_empty_from_indices(all_stones, empty_mask, geom)

        if empty_mask[center_idx]:
            frontier.add(center_idx)
        for c in geom["corner_cells"]:
            if empty_mask[c]:
                frontier.add(c)

        if not frontier:
            frontier = set(legal)

        need = min(24, len(legal))
        if len(frontier) < need:
            for mv in geom["central_order"]:
                if empty_mask[mv]:
                    frontier.add(mv)
                    if len(frontier) >= need:
                        break

        frontier = list(frontier)
        phase = total_stones / float(max(1, m))

        my_corner_dists, my_edge_dists = _compute_dist_maps(my_occ, opp_occ, geom)
        opp_corner_dists, opp_edge_dists = _compute_dist_maps(opp_occ, my_occ, geom)

        my_raw_scores = {}
        opp_raw_scores = {}
        scores = {}

        for mv in frontier:
            my_raw = _raw_move_value(
                mv,
                my_occ,
                opp_occ,
                my_comp,
                opp_comp,
                my_corner_dists,
                my_edge_dists,
                geom,
                phase,
            )
            opp_raw = _raw_move_value(
                mv,
                opp_occ,
                my_occ,
                opp_comp,
                my_comp,
                opp_corner_dists,
                opp_edge_dists,
                geom,
                phase,
            )
            my_raw_scores[mv] = my_raw
            opp_raw_scores[mv] = opp_raw
            scores[mv] = my_raw + (7 * opp_raw) // 10

        ordered = sorted(
            frontier,
            key=lambda mv: (
                scores[mv],
                geom["center_score"][mv],
                -coords[mv][0],
                -coords[mv][1],
            ),
            reverse=True,
        )

        future_counts = {}

        # 3) Look for our 2-ply forced win: create >=2 immediate wins next turn.
        my_force_pool = [mv for mv in ordered if mv in my_adj]
        force_limit = min(len(my_force_pool), 40)
        for mv in my_force_pool[:force_limit]:
            cnt = _count_future_wins_after_move(mv, my_occ, empty_mask, geom, limit=2)
            future_counts[mv] = cnt
            if cnt >= 2:
                return coords[mv]

        # 4) Prevent opponent's analogous forcing move if possible.
        if opp_adj:
            opp_order = sorted(
                frontier,
                key=lambda mv: (
                    opp_raw_scores[mv],
                    scores[mv],
                    geom["center_score"][mv],
                    -coords[mv][0],
                    -coords[mv][1],
                ),
                reverse=True,
            )
            opp_force_pool = [mv for mv in opp_order if mv in opp_adj]
            danger = []
            danger_limit = min(len(opp_force_pool), 40)
            for mv in opp_force_pool[:danger_limit]:
                cnt = _count_future_wins_after_move(mv, opp_occ, empty_mask, geom, limit=2)
                if cnt >= 2:
                    danger.append(mv)
            if danger:
                best_danger = max(
                    danger,
                    key=lambda mv: (
                        opp_raw_scores[mv],
                        scores[mv],
                        geom["center_score"][mv],
                        -coords[mv][0],
                        -coords[mv][1],
                    ),
                )
                return coords[best_danger]

        # 5) Bonus for moves that create at least one immediate threat next turn.
        for mv in ordered[: min(10, len(ordered))]:
            cnt = future_counts.get(mv)
            if cnt is None:
                cnt = _count_future_wins_after_move(mv, my_occ, empty_mask, geom, limit=2)
                future_counts[mv] = cnt
            scores[mv] += 240 * cnt

        best = _pick_scored(ordered, scores, geom)
        return coords[best]

    except Exception:
        return _fallback_move(me, opp, valid_mask)
