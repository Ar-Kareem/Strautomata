
from collections import deque
from heapq import heappush, heappop

_CACHE = {}


class _Info:
    __slots__ = (
        "h", "w", "cells", "cell_set", "neighbors", "boundary",
        "corner_id", "edge_id", "edge_cells", "corner_cells",
        "mode", "cube", "dist_center", "max_center_dist"
    )


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    info = _get_info(valid_mask)

    me_set = set(tuple(x) for x in me)
    opp_set = set(tuple(x) for x in opp)
    occupied = me_set | opp_set

    legal = [c for c in info.cells if c not in occupied]
    if not legal:
        # Should never be called on a full board, but keep a deterministic fallback.
        return info.cells[0] if info.cells else (0, 0)

    # Opening: take the most central legal point.
    if not me_set and not opp_set:
        return min(legal, key=lambda x: (info.dist_center.get(x, 0), x[0], x[1]))

    # 1. Win immediately if possible.
    my_wins = []
    for m in legal:
        if _is_win_after(me_set, m, info):
            my_wins.append(m)
    if my_wins:
        return max(my_wins, key=lambda x: (_positional_value(x, info, len(occupied)), -info.dist_center.get(x, 0)))

    # 2. Block an immediate opponent win.
    opp_wins = []
    for m in legal:
        if _is_win_after(opp_set, m, info):
            opp_wins.append(m)

    scores = _base_scores(me_set, opp_set, occupied, legal, info)

    if opp_wins:
        # If there are multiple immediate threats we cannot solve all of them,
        # but occupying one of those cells is still almost always best.
        return max(opp_wins, key=lambda x: (scores.get(x, -10**9), -info.dist_center.get(x, 0)))

    # 3. Refine promising moves by looking for double threats and defensive blocks.
    k = 30 if len(legal) > 50 else min(len(legal), 42)
    top = sorted(legal, key=lambda x: scores.get(x, -10**9), reverse=True)[:k]
    next_legal_cache = {m: [x for x in legal if x != m] for m in top}

    for m in top:
        # Our double-threat creation.
        new_me = set(me_set)
        new_me.add(m)
        tw = _count_winning_moves(new_me, next_legal_cache[m], info, stop=4)
        if tw >= 2:
            scores[m] += 3200 + 700 * tw
        elif tw == 1:
            scores[m] += 450

        # Defensive: if opponent playing here would make strong threats,
        # occupying this point has extra value.
        new_opp = set(opp_set)
        new_opp.add(m)
        otw = _count_winning_moves(new_opp, next_legal_cache[m], info, stop=3)
        if otw >= 2:
            scores[m] += 1450 + 350 * otw
        elif otw == 1:
            scores[m] += 260

    best = max(
        legal,
        key=lambda x: (
            scores.get(x, -10**9),
            -info.dist_center.get(x, 0),
            -x[0],
            -x[1],
        ),
    )
    return best


# ----------------------------------------------------------------------
# Board geometry
# ----------------------------------------------------------------------

def _make_grid(valid_mask):
    h = len(valid_mask)
    rows = []
    for r in range(h):
        row = valid_mask[r]
        rows.append(tuple(bool(row[c]) for c in range(len(row))))
    return tuple(rows)


def _get_info(valid_mask):
    grid = _make_grid(valid_mask)
    if grid in _CACHE:
        return _CACHE[grid]
    info = _build_info(grid)
    _CACHE[grid] = info
    return info


def _raw_neighbors(r, c, mode):
    # mode 0: skew layout with diagonals (-1,-1), (+1,+1)
    if mode == 0:
        ds = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]
    # mode 1: skew layout with diagonals (-1,+1), (+1,-1)
    elif mode == 1:
        ds = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]
    # mode 2: vertical offset; odd columns have upward diagonals.
    elif mode == 2:
        ds = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if c & 1:
            ds += [(-1, -1), (-1, 1)]
        else:
            ds += [(1, -1), (1, 1)]
    # mode 3: opposite vertical offset.
    else:
        ds = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        if c & 1:
            ds += [(1, -1), (1, 1)]
        else:
            ds += [(-1, -1), (-1, 1)]
    return [(r + dr, c + dc) for dr, dc in ds]


def _cube_coord(r, c, mode):
    # Return cube-like coordinates. Only relative extrema/distances matter.
    if mode == 0:
        x = c
        z = r - c
        y = -x - z
    elif mode == 1:
        x = c
        z = r
        y = -x - z
    elif mode == 2:
        x = c
        z = r - ((c + (c & 1)) // 2)
        y = -x - z
    else:
        x = c
        z = r - ((c - (c & 1)) // 2)
        y = -x - z
    return (x, y, z)


def _build_neighbors(grid, cells, mode):
    h = len(grid)
    w = len(grid[0]) if h else 0
    cell_set = set(cells)
    neighbors = {}
    for r, c in cells:
        ns = []
        for nr, nc in _raw_neighbors(r, c, mode):
            if 0 <= nr < h and 0 <= nc < w and (nr, nc) in cell_set:
                ns.append((nr, nc))
        neighbors[(r, c)] = ns
    return neighbors


def _boundary_components(boundary, corners, neighbors):
    usable = set(boundary) - set(corners)
    seen = set()
    comps = []
    for start in usable:
        if start in seen:
            continue
        comp = set()
        stack = [start]
        seen.add(start)
        while stack:
            v = stack.pop()
            comp.add(v)
            for nb in neighbors[v]:
                if nb in usable and nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        if comp:
            comps.append(comp)
    return comps


def _mode_score(grid, cells, mode):
    neighbors = _build_neighbors(grid, cells, mode)
    degs = [len(neighbors[c]) for c in cells]
    boundary = {c for c in cells if len(neighbors[c]) < 6}
    corners = {c for c in cells if len(neighbors[c]) == 3}
    comps = _boundary_components(boundary, corners, neighbors) if corners else []

    interior = sum(1 for d in degs if d == 6)
    low = sum(1 for d in degs if d < 3)
    corner_bad = abs(len(corners) - 6)
    comp_bad = abs(len(comps) - 6) if len(corners) == 6 else 3

    # The correct geometry should have many degree-6 interior cells,
    # six degree-3 corners, and six boundary chains after removing corners.
    score = interior * 60
    score -= corner_bad * 5000
    score -= comp_bad * 3000
    score -= low * 2000
    score -= sum(max(0, 3 - d) * 500 for d in degs)
    if mode == 2:
        score += 5  # tiny preference for the layout described in the prompt
    return score


def _build_info(grid):
    info = _Info()
    info.h = len(grid)
    info.w = len(grid[0]) if info.h else 0
    cells = [(r, c) for r in range(info.h) for c in range(info.w) if grid[r][c]]
    info.cells = cells
    info.cell_set = set(cells)

    if not cells:
        info.neighbors = {}
        info.boundary = set()
        info.corner_id = {}
        info.edge_id = {}
        info.edge_cells = []
        info.corner_cells = []
        info.mode = 0
        info.cube = {}
        info.dist_center = {}
        info.max_center_dist = 0
        return info

    mode = max(range(4), key=lambda m: _mode_score(grid, cells, m))
    info.mode = mode
    neighbors = _build_neighbors(grid, cells, mode)
    info.neighbors = neighbors

    degrees = {c: len(neighbors[c]) for c in cells}
    boundary = {c for c in cells if degrees[c] < 6}
    info.boundary = boundary

    cube = {c: _cube_coord(c[0], c[1], mode) for c in cells}
    info.cube = cube
    xs = [cube[c][0] for c in cells]
    ys = [cube[c][1] for c in cells]
    zs = [cube[c][2] for c in cells]
    mins = (min(xs), min(ys), min(zs))
    maxs = (max(xs), max(ys), max(zs))

    corners = [c for c in cells if degrees[c] == 3]
    if len(corners) != 6:
        cand = []
        for c in cells:
            cc = cube[c]
            k = 0
            for i in range(3):
                if cc[i] == mins[i] or cc[i] == maxs[i]:
                    k += 1
            if k >= 2:
                cand.append(c)
        if len(cand) >= 6:
            corners = cand[:]
        else:
            # Last-resort fallback: lowest degree boundary cells.
            corners = sorted(boundary, key=lambda x: (degrees[x], x[0], x[1]))[:6]

    corners = sorted(corners)[:6]
    info.corner_cells = corners
    info.corner_id = {c: i for i, c in enumerate(corners)}

    comps = _boundary_components(boundary, set(corners), neighbors)
    edge_id = {}
    edge_cells = []

    if len(comps) == 6:
        for i, comp in enumerate(comps):
            edge_cells.append(set(comp))
            for c in comp:
                edge_id[c] = i
    else:
        # Cube-extrema fallback edge classification.
        forms = [
            (0, mins[0]), (0, maxs[0]),
            (1, mins[1]), (1, maxs[1]),
            (2, mins[2]), (2, maxs[2]),
        ]
        edge_cells = [set() for _ in range(6)]
        corner_set = set(corners)
        for c in cells:
            if c in corner_set:
                continue
            cc = cube[c]
            for i, (axis, val) in enumerate(forms):
                if cc[axis] == val:
                    edge_id[c] = i
                    edge_cells[i].add(c)
                    break

    info.edge_id = edge_id
    info.edge_cells = edge_cells

    # Center distance in cube coordinates.
    ax = sum(xs) / len(xs)
    ay = sum(ys) / len(ys)
    az = sum(zs) / len(zs)
    dist_center = {}
    for c in cells:
        x, y, z = cube[c]
        dist_center[c] = max(abs(x - ax), abs(y - ay), abs(z - az))
    info.dist_center = dist_center
    info.max_center_dist = max(dist_center.values()) if dist_center else 1

    return info


# ----------------------------------------------------------------------
# Win detection
# ----------------------------------------------------------------------

def _is_win_after(stones, move, info):
    if move in stones:
        return False

    new_stones = set(stones)
    new_stones.add(move)

    # Bridge/fork: only the newly changed connected component matters.
    stack = [move]
    seen = {move}
    corners = set()
    edges = set()

    while stack:
        v = stack.pop()

        cid = info.corner_id.get(v)
        if cid is not None:
            corners.add(cid)
            if len(corners) >= 2:
                return True

        eid = info.edge_id.get(v)
        if eid is not None:
            edges.add(eid)
            if len(edges) >= 3:
                return True

        for nb in info.neighbors.get(v, ()):
            if nb in new_stones and nb not in seen:
                seen.add(nb)
                stack.append(nb)

    # A newly completed ring must give the new stone degree at least 2
    # in the player's local graph, so skip expensive checks otherwise.
    local_own = 0
    for nb in info.neighbors.get(move, ()):
        if nb in stones:
            local_own += 1
            if local_own >= 2:
                break

    if local_own >= 2 and _has_ring(new_stones, info):
        return True

    return False


def _has_ring(stones, info):
    visited = set()

    for start in info.cells:
        if start in stones or start in visited:
            continue

        touches_boundary = start in info.boundary
        q = [start]
        visited.add(start)

        while q:
            v = q.pop()
            if v in info.boundary:
                touches_boundary = True
            for nb in info.neighbors.get(v, ()):
                if nb not in stones and nb not in visited:
                    visited.add(nb)
                    q.append(nb)

        if not touches_boundary:
            return True

    return False


def _count_winning_moves(stones, legal, info, stop=3):
    cnt = 0
    for m in legal:
        if _is_win_after(stones, m, info):
            cnt += 1
            if cnt >= stop:
                return cnt
    return cnt


# ----------------------------------------------------------------------
# Evaluation
# ----------------------------------------------------------------------

def _components(stones, occupied, info):
    comp = {}
    metas = []
    seen = set()

    for start in stones:
        if start in seen or start not in info.cell_set:
            continue

        idx = len(metas)
        stack = [start]
        seen.add(start)
        comp[start] = idx

        size = 0
        edges = set()
        corners = set()
        libs = set()

        while stack:
            v = stack.pop()
            size += 1

            eid = info.edge_id.get(v)
            if eid is not None:
                edges.add(eid)
            cid = info.corner_id.get(v)
            if cid is not None:
                corners.add(cid)

            for nb in info.neighbors.get(v, ()):
                if nb in stones:
                    if nb not in seen:
                        seen.add(nb)
                        comp[nb] = idx
                        stack.append(nb)
                elif nb not in occupied:
                    libs.add(nb)

        metas.append({
            "size": size,
            "edges": edges,
            "corners": corners,
            "libs": libs,
        })

    return comp, metas


def _merged_meta(move, player, comp, metas, occupied, info):
    gids = set()
    own_nb = 0

    for nb in info.neighbors.get(move, ()):
        if nb in player:
            own_nb += 1
            g = comp.get(nb)
            if g is not None:
                gids.add(g)

    edges = set()
    corners = set()
    libs = set()
    size = 1

    eid = info.edge_id.get(move)
    if eid is not None:
        edges.add(eid)
    cid = info.corner_id.get(move)
    if cid is not None:
        corners.add(cid)

    for nb in info.neighbors.get(move, ()):
        if nb not in occupied:
            libs.add(nb)

    for g in gids:
        meta = metas[g]
        size += meta["size"]
        edges |= meta["edges"]
        corners |= meta["corners"]
        libs |= meta["libs"]

    libs.discard(move)

    return {
        "size": size,
        "edges_n": len(edges),
        "corners_n": len(corners),
        "libs_n": len(libs),
        "groups_n": len(gids),
        "own_nb": own_nb,
    }


def _shape_value(meta):
    e = meta["edges_n"]
    c = meta["corners_n"]
    size = meta["size"]
    libs = meta["libs_n"]
    groups = meta["groups_n"]
    own_nb = meta["own_nb"]

    val = 0.0
    val += 7.0 * min(size, 55)
    val += 120.0 * max(0, groups - 1)
    val += 10.0 * libs
    val += 25.0 * own_nb

    if own_nb >= 2:
        val += 20.0 * own_nb * own_nb

    if e == 1:
        val += 95.0
    elif e == 2:
        val += 460.0 + 18.0 * libs
    elif e >= 3:
        val += 5000.0

    if c == 1:
        val += 265.0 + 8.0 * size
    elif c >= 2:
        val += 5000.0

    return val


def _dijkstra(sources, player, blockers, info):
    inf = 10**9
    dist = {}
    heap = []

    for s in sources:
        if s in blockers:
            continue
        cost = 0 if s in player else 1
        if cost < dist.get(s, inf):
            dist[s] = cost
            heappush(heap, (cost, s))

    while heap:
        d, v = heappop(heap)
        if d != dist.get(v):
            continue
        for nb in info.neighbors.get(v, ()):
            if nb in blockers:
                continue
            nd = d + (0 if nb in player else 1)
            if nd < dist.get(nb, inf):
                dist[nb] = nd
                heappush(heap, (nd, nb))

    return dist


def _connection_distances(player, blockers, info):
    edge_dists = [_dijkstra(edge, player, blockers, info) for edge in info.edge_cells if edge]
    corner_dists = [_dijkstra([c], player, blockers, info) for c in info.corner_cells]
    return edge_dists, corner_dists


def _path_value(move, edge_dists, corner_dists):
    val = 0.0

    if len(edge_dists) >= 3:
        ds = sorted(max(0, d.get(move, 99) - 1) for d in edge_dists)
        val += 370.0 / (1.0 + ds[0] + ds[1] + ds[2])
        val += 60.0 / (1.0 + ds[0])

    if len(corner_dists) >= 2:
        ds = sorted(max(0, d.get(move, 99) - 1) for d in corner_dists)
        val += 430.0 / (1.0 + ds[0] + ds[1])
        val += 45.0 / (1.0 + ds[0])

    return val


def _positional_value(move, info, total_stones):
    md = info.max_center_dist or 1
    center_factor = 1.0 - (info.dist_center.get(move, 0) / md)
    val = 70.0 * center_factor

    if total_stones < 8:
        val += 80.0 * center_factor
        if move in info.edge_id:
            val -= 12.0
        if move in info.corner_id:
            val -= 18.0
    else:
        if move in info.corner_id:
            val += 38.0
        elif move in info.edge_id:
            val += 12.0

    return val


def _base_scores(me, opp, occupied, legal, info):
    me_comp, me_metas = _components(me, occupied, info)
    opp_comp, opp_metas = _components(opp, occupied, info)

    me_edge_d, me_corner_d = _connection_distances(me, opp, info)
    opp_edge_d, opp_corner_d = _connection_distances(opp, me, info)

    total = len(occupied)
    scores = {}

    for m in legal:
        my_meta = _merged_meta(m, me, me_comp, me_metas, occupied, info)
        op_meta = _merged_meta(m, opp, opp_comp, opp_metas, occupied, info)

        score = 0.0
        score += _shape_value(my_meta)
        score += 0.86 * _shape_value(op_meta)

        score += _path_value(m, me_edge_d, me_corner_d)
        score += 0.68 * _path_value(m, opp_edge_d, opp_corner_d)

        score += _positional_value(m, info, total)

        # Prefer relevant local moves once the game is underway.
        adjacent_opp = any(nb in opp for nb in info.neighbors.get(m, ()))
        if my_meta["own_nb"] == 0 and total > 10:
            if adjacent_opp:
                score += 8.0
            else:
                score -= 30.0

        # Contested contact points are often valuable in Havannah.
        if my_meta["own_nb"] > 0 and adjacent_opp:
            score += 28.0

        scores[m] = score

    return scores
