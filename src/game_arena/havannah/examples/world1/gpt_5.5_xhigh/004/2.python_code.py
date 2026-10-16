
from collections import deque
import math

_GEOM_CACHE = {}

try:
    (1).bit_count
    def _popcount(x):
        return x.bit_count()
except AttributeError:
    def _popcount(x):
        return bin(x).count("1")


class _Geom:
    __slots__ = (
        "rows", "cols", "cells", "valid_set",
        "dir_neighbors", "neighbors", "degree", "cube",
        "corner_bit", "edge_bit", "boundary",
        "center", "center_dist", "corner_dist", "edge_dist", "near2"
    )


def policy(me, opp, valid_mask):
    """
    Return a legal (row, col) move for the current player.
    """
    try:
        geom = _get_geom(valid_mask)

        me_set = set()
        for p in me:
            cell = (int(p[0]), int(p[1]))
            if cell in geom.valid_set:
                me_set.add(cell)

        opp_set = set()
        for p in opp:
            cell = (int(p[0]), int(p[1]))
            if cell in geom.valid_set:
                opp_set.add(cell)

        occupied = me_set | opp_set
        legal = [cell for cell in geom.cells if cell not in occupied]

        if not legal:
            return _emergency_fallback(me, opp, valid_mask)
        if len(legal) == 1:
            return legal[0]

        phase = len(occupied)

        # Opening: take the most central legal point.
        if phase == 0:
            return _best_center(legal, geom, phase)

        # 1. Win immediately if possible.
        for m in legal:
            if _is_win_after(me_set, m, geom):
                return m

        # 2. Block opponent's immediate wins.
        opp_wins = []
        for m in legal:
            if _is_win_after(opp_set, m, geom):
                opp_wins.append(m)

        comps_me, cid_me = _build_components(me_set, occupied, geom)
        comps_opp, cid_opp = _build_components(opp_set, occupied, geom)

        if opp_wins:
            best = None
            best_score = -1.0e30
            for m in opp_wins:
                s = _candidate_score(
                    me_set, opp_set, comps_me, cid_me, comps_opp, cid_opp,
                    m, occupied, geom, phase
                )
                # All listed moves block one immediate win; choose the most useful one.
                s += 10000.0
                if s > best_score:
                    best_score = s
                    best = m
            if best in geom.valid_set and best not in occupied:
                return best
            return legal[0]

        # 3. Heuristic scoring.
        seed = phase * 131 + len(me_set) * 17 + len(opp_set) * 29
        scored = []
        for m in legal:
            s = _candidate_score(
                me_set, opp_set, comps_me, cid_me, comps_opp, cid_opp,
                m, occupied, geom, phase
            )
            s += _tiny_noise(m, seed)
            scored.append((s, m))
        scored.sort(key=lambda x: x[0], reverse=True)

        # 4. Shallow threat extension for the most promising moves.
        top_threat = min(len(scored), 28 if phase < 60 else 22)
        reply_top = min(top_threat, 12 if phase < 70 else 8)

        best_score = -1.0e30
        best_move = scored[0][1]

        for rank, (base, m) in enumerate(scored):
            s = base

            if rank < top_threat:
                new_me = set(me_set)
                new_me.add(m)
                occ2 = occupied | {m}
                legal2 = [x for x in legal if x != m]

                # Count immediate winning threats we create for our next turn.
                threat_moves = []
                for x in legal2:
                    if _is_win_after(new_me, x, geom):
                        threat_moves.append(x)
                        if len(threat_moves) >= 4:
                            break

                tc = len(threat_moves)
                if tc == 1:
                    s += 220.0
                elif tc == 2:
                    s += 2200.0
                elif tc >= 3:
                    s += 3200.0

                # Estimate the opponent's best reply for top-ranked moves.
                if rank < reply_top and legal2:
                    comps_me2, cid_me2 = _build_components(new_me, occ2, geom)
                    comps_opp2, cid_opp2 = _build_components(opp_set, occ2, geom)

                    threat_set = set(threat_moves)
                    opp_best = -1.0e30
                    my_best = 0.0

                    for x in legal2:
                        op = _move_potential(
                            opp_set, new_me, comps_opp2, cid_opp2,
                            x, occ2, geom, phase + 1
                        )
                        mp = _move_potential(
                            new_me, opp_set, comps_me2, cid_me2,
                            x, occ2, geom, phase + 1
                        )

                        # Opponent likes blocking our direct winning point.
                        if x in threat_set:
                            op += 1100.0

                        mp_cap = min(max(mp, 0.0), 2000.0)
                        op += 0.18 * mp_cap

                        if op > opp_best:
                            opp_best = op
                        if mp > my_best:
                            my_best = mp

                    s += 0.08 * min(max(my_best, 0.0), 2600.0)
                    s -= 0.16 * min(max(opp_best, 0.0), 3400.0)

            if s > best_score:
                best_score = s
                best_move = m

        if best_move in geom.valid_set and best_move not in occupied:
            return best_move
        return legal[0]

    except Exception:
        # Absolute safety net: never fail to return a legal move if one exists.
        return _emergency_fallback(me, opp, valid_mask)


# ---------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------

def _get_geom(valid_mask):
    tuple_index = False
    try:
        rows = int(valid_mask.shape[0])
        cols = int(valid_mask.shape[1])
        tuple_index = True
    except Exception:
        rows = len(valid_mask)
        cols = len(valid_mask[0]) if rows else 0

    bits = []
    cells = []
    for r in range(rows):
        row_bits = []
        for c in range(cols):
            if tuple_index:
                try:
                    v = bool(valid_mask[r, c])
                except Exception:
                    v = bool(valid_mask[r][c])
            else:
                v = bool(valid_mask[r][c])
            row_bits.append(v)
            if v:
                cells.append((r, c))
        bits.append(tuple(row_bits))

    key = (rows, cols, tuple(bits))
    geom = _GEOM_CACHE.get(key)
    if geom is not None:
        return geom

    geom = _make_geom(rows, cols, tuple(bits), cells)
    if len(_GEOM_CACHE) > 8:
        _GEOM_CACHE.clear()
    _GEOM_CACHE[key] = geom
    return geom


def _make_geom(rows, cols, bits, cells):
    geom = _Geom()
    geom.rows = rows
    geom.cols = cols
    geom.cells = list(cells)
    geom.valid_set = set(cells)

    geom.dir_neighbors = {}
    geom.neighbors = {}
    geom.degree = {}
    geom.cube = {}
    geom.corner_bit = {}
    geom.edge_bit = {}
    geom.boundary = set()
    geom.center = (0, 0)
    geom.center_dist = {}
    geom.corner_dist = []
    geom.edge_dist = []
    geom.near2 = {}

    if not cells:
        return geom

    valid_set = geom.valid_set

    for cell in cells:
        r, c = cell
        dirs = []
        ns = []
        for pos in _six_positions(r, c):
            if pos in valid_set:
                dirs.append(pos)
                ns.append(pos)
            else:
                dirs.append(None)
        geom.dir_neighbors[cell] = tuple(dirs)
        geom.neighbors[cell] = tuple(ns)
        geom.degree[cell] = len(ns)

    # Odd-column offset coordinates -> cube coordinates.
    # This matches the prompt example:
    # (4,1) touches (3,0), (4,0), (3,2), (4,2), (3,1), (5,1).
    for r, c in cells:
        z = r - ((c + (c & 1)) // 2)
        x = c
        y = -x - z
        geom.cube[(r, c)] = (x, y, z)

    xs = [geom.cube[cell][0] for cell in cells]
    ys = [geom.cube[cell][1] for cell in cells]
    zs = [geom.cube[cell][2] for cell in cells]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minz, maxz = min(zs), max(zs)

    side_list = {}
    for cell in cells:
        x, y, z = geom.cube[cell]
        sides = []
        if x == minx:
            sides.append(0)
        if y == miny:
            sides.append(1)
        if z == minz:
            sides.append(2)
        if x == maxx:
            sides.append(3)
        if y == maxy:
            sides.append(4)
        if z == maxz:
            sides.append(5)
        side_list[cell] = tuple(sides)

    corners_ext = [cell for cell in cells if len(side_list[cell]) >= 2]

    if len(corners_ext) == 6:
        corners = _sort_cells_around(corners_ext, cells)
    else:
        deg_corners = [cell for cell in cells if geom.degree[cell] <= 3]
        if len(deg_corners) == 6:
            corners = _sort_cells_around(deg_corners, cells)
        else:
            boundary_candidates = [
                cell for cell in cells
                if geom.degree[cell] < 6 or len(side_list[cell]) > 0
            ]
            corners = _choose_six_corners(boundary_candidates, geom.cube, cells)

    for i, cell in enumerate(corners[:6]):
        geom.corner_bit[cell] = 1 << i

    for cell in cells:
        if side_list[cell] or geom.degree[cell] < 6:
            geom.boundary.add(cell)

        # Corners are not edge cells for fork purposes.
        if cell in geom.corner_bit:
            continue

        sides = side_list[cell]
        if len(sides) == 1:
            geom.edge_bit[cell] = 1 << sides[0]

    # Fallback edge labelling if cube-extreme labelling did not find six sides.
    edge_groups = set(geom.edge_bit.values())
    if len(edge_groups) < 6:
        mask_to_side = {}
        next_side = 0
        fallback_edge_bit = {}
        for cell in cells:
            if cell in geom.corner_bit:
                continue
            miss = 0
            for i, nb in enumerate(geom.dir_neighbors[cell]):
                if nb is None:
                    miss |= 1 << i
            if miss:
                if miss not in mask_to_side and next_side < 6:
                    mask_to_side[miss] = next_side
                    next_side += 1
                if miss in mask_to_side:
                    fallback_edge_bit[cell] = 1 << mask_to_side[miss]
        if len(set(fallback_edge_bit.values())) >= len(edge_groups):
            geom.edge_bit = fallback_edge_bit

    # Center by cube-coordinate average.
    n = float(len(cells))
    avgx = sum(geom.cube[cell][0] for cell in cells) / n
    avgy = sum(geom.cube[cell][1] for cell in cells) / n
    avgz = sum(geom.cube[cell][2] for cell in cells) / n
    avgr = sum(cell[0] for cell in cells) / n
    avgc = sum(cell[1] for cell in cells) / n

    def center_key(cell):
        x, y, z = geom.cube[cell]
        d_cube = max(abs(x - avgx), abs(y - avgy), abs(z - avgz))
        d_rc = (cell[0] - avgr) * (cell[0] - avgr) + (cell[1] - avgc) * (cell[1] - avgc)
        return (d_cube, d_rc, cell[0], cell[1])

    geom.center = min(cells, key=center_key)
    geom.center_dist = _bfs_dist([geom.center], geom.neighbors)

    geom.corner_dist = []
    for corner in corners[:6]:
        geom.corner_dist.append(_bfs_dist([corner], geom.neighbors))

    geom.edge_dist = []
    for i in range(6):
        starts = [cell for cell, b in geom.edge_bit.items() if b & (1 << i)]
        if not starts:
            starts = [cell for cell, sides in side_list.items() if i in sides]
        geom.edge_dist.append(_bfs_dist(starts, geom.neighbors) if starts else {})

    for cell in cells:
        s = set(geom.neighbors[cell])
        for nb in geom.neighbors[cell]:
            s.update(geom.neighbors[nb])
        s.discard(cell)
        geom.near2[cell] = tuple(s)

    return geom


def _six_positions(r, c):
    # Direction order: N, NE, SE, S, SW, NW.
    if c & 1:
        return (
            (r - 1, c),
            (r - 1, c + 1),
            (r,     c + 1),
            (r + 1, c),
            (r,     c - 1),
            (r - 1, c - 1),
        )
    else:
        return (
            (r - 1, c),
            (r,     c + 1),
            (r + 1, c + 1),
            (r + 1, c),
            (r + 1, c - 1),
            (r,     c - 1),
        )


def _bfs_dist(starts, neighbors):
    dist = {}
    q = deque()
    for s in starts:
        if s in neighbors and s not in dist:
            dist[s] = 0
            q.append(s)
    while q:
        x = q.popleft()
        nd = dist[x] + 1
        for nb in neighbors[x]:
            if nb not in dist:
                dist[nb] = nd
                q.append(nb)
    return dist


def _sort_cells_around(cells_to_sort, all_cells):
    if not cells_to_sort:
        return []
    n = float(len(all_cells) or 1)
    avg_r = sum(r for r, c in all_cells) / n
    avg_c = sum(c for r, c in all_cells) / n

    def ang(cell):
        r, c = cell
        # Odd columns are vertically shifted; this is only for stable ordering.
        pr = r + 0.5 * (c & 1)
        pc = c
        return math.atan2(pr - avg_r, pc - avg_c)

    return sorted(cells_to_sort, key=lambda cell: (ang(cell), cell[0], cell[1]))


def _choose_six_corners(candidates, cube, all_cells):
    candidates = list(dict.fromkeys(candidates))
    if len(candidates) <= 6:
        return _sort_cells_around(candidates, all_cells)

    n = float(len(all_cells) or 1)
    avgx = sum(cube[cell][0] for cell in all_cells) / n
    avgy = sum(cube[cell][1] for cell in all_cells) / n
    avgz = sum(cube[cell][2] for cell in all_cells) / n

    def far_center(cell):
        x, y, z = cube[cell]
        return max(abs(x - avgx), abs(y - avgy), abs(z - avgz))

    selected = []
    remaining = set(candidates)

    first = max(remaining, key=lambda c: (far_center(c), c[0], c[1]))
    selected.append(first)
    remaining.remove(first)

    while len(selected) < 6 and remaining:
        best = max(
            remaining,
            key=lambda c: (
                min(_cube_dist(cube[c], cube[s]) for s in selected),
                far_center(c),
                c[0],
                c[1],
            )
        )
        selected.append(best)
        remaining.remove(best)

    return _sort_cells_around(selected, all_cells)


def _cube_dist(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


# ---------------------------------------------------------------------
# Win detection
# ---------------------------------------------------------------------

def _is_win_after(stones, move, geom):
    if move in stones:
        return False
    if _connection_win_after(stones, move, geom):
        return True
    if _completes_ring(stones, move, geom):
        return True
    return False


def _connection_win_after(stones, move, geom):
    seen = {move}
    stack = [move]
    corner_mask = 0
    edge_mask = 0

    while stack:
        x = stack.pop()
        corner_mask |= geom.corner_bit.get(x, 0)
        edge_mask |= geom.edge_bit.get(x, 0)

        for nb in geom.neighbors[x]:
            if nb in stones and nb not in seen:
                seen.add(nb)
                stack.append(nb)

    # Bridge: two corners. Fork: three edges, with corners excluded from edges.
    return _popcount(corner_mask) >= 2 or _popcount(edge_mask) >= 3


def _completes_ring(stones, move, geom):
    own_adj = 0
    for nb in geom.neighbors[move]:
        if nb in stones:
            own_adj += 1
    if own_adj < 2:
        return False

    # Detect a one-cell ring even if the surrounded cell is also ours.
    for x in geom.neighbors[move]:
        if x in geom.boundary or len(geom.neighbors[x]) < 6:
            continue
        ok = True
        for y in geom.neighbors[x]:
            if y != move and y not in stones:
                ok = False
                break
        if ok:
            return True

    # Flood-fill non-player cells adjacent to the move. If any such region
    # cannot reach the board boundary, the move closed a ring.
    seen = set()
    for start in geom.neighbors[move]:
        if start in stones or start in seen:
            continue

        touches_boundary = False
        stack = [start]
        seen.add(start)

        while stack:
            x = stack.pop()

            if x in geom.boundary:
                touches_boundary = True
                break

            for nb in geom.neighbors[x]:
                if nb == move or nb in stones or nb in seen:
                    continue
                seen.add(nb)
                stack.append(nb)

        if not touches_boundary:
            return True

    return False


# ---------------------------------------------------------------------
# Components and move evaluation
# ---------------------------------------------------------------------

def _build_components(stones, occupied, geom):
    comps = []
    comp_id = {}
    visited = set()

    for start in stones:
        if start in visited or start not in geom.valid_set:
            continue

        idx = len(comps)
        stack = [start]
        visited.add(start)

        size = 0
        corner_mask = 0
        edge_mask = 0
        libs = set()

        while stack:
            x = stack.pop()
            comp_id[x] = idx
            size += 1
            corner_mask |= geom.corner_bit.get(x, 0)
            edge_mask |= geom.edge_bit.get(x, 0)

            for nb in geom.neighbors[x]:
                if nb in stones:
                    if nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
                elif nb not in occupied:
                    libs.add(nb)

        comps.append((size, corner_mask, edge_mask, libs))

    return comps, comp_id


def _candidate_score(me_set, opp_set, comps_me, cid_me, comps_opp, cid_opp,
                     move, occupied, geom, phase):
    near_own = 0
    near_opp = 0
    for x in geom.near2[move]:
        if x in me_set:
            near_own += 1
        elif x in opp_set:
            near_opp += 1

    adj_opp = 0
    for nb in geom.neighbors[move]:
        if nb in opp_set:
            adj_opp += 1

    own = _move_potential(
        me_set, opp_set, comps_me, cid_me, move, occupied, geom, phase
    )
    block = _move_potential(
        opp_set, me_set, comps_opp, cid_opp, move, occupied, geom, phase
    )

    if opp_set:
        block_weight = 0.30 + 0.07 * min(6, near_opp)
        if adj_opp:
            block_weight += 0.14
        if near_opp >= 4:
            block_weight += 0.08
        if block_weight > 0.90:
            block_weight = 0.90
    else:
        block_weight = 0.15

    score = 1.05 * own + block_weight * block
    score += min(85.0, 9.0 * near_own)
    score += min(65.0, 6.5 * near_opp)

    # Avoid aimless scattering, unless it is clearly a defensive contest.
    if me_set and near_own == 0:
        if near_opp == 0:
            score -= 125.0 if phase > 4 else 40.0
        elif phase > 12:
            score -= 30.0

    if near_own > 0 and near_opp > 0:
        score += 28.0
    if adj_opp >= 2 and near_own == 0:
        score += 25.0

    return score


def _move_potential(player, enemy, comps, comp_id, move, occupied, geom, phase):
    neigh = geom.neighbors[move]

    own_n = 0
    enemy_n = 0
    empty_n = 0
    adj_counts = {}
    libset = set()

    for nb in neigh:
        if nb in player:
            own_n += 1
            cid = comp_id.get(nb)
            if cid is not None:
                adj_counts[cid] = adj_counts.get(cid, 0) + 1
        elif nb in enemy:
            enemy_n += 1
        else:
            empty_n += 1
            libset.add(nb)

    corner_mask = geom.corner_bit.get(move, 0)
    edge_mask = geom.edge_bit.get(move, 0)
    size = 1
    sum_adj_size = 0

    adj_ids = list(adj_counts.keys())
    for cid in adj_ids:
        comp = comps[cid]
        size += comp[0]
        sum_adj_size += comp[0]
        corner_mask |= comp[1]
        edge_mask |= comp[2]
        libset.update(comp[3])

    libset.discard(move)
    lib_count = len(libset)

    cc = _popcount(corner_mask)
    ec = _popcount(edge_mask)

    score = 0.0

    # Actual bridge/fork completion is decisive.
    if cc >= 2:
        score += 120000.0
    if ec >= 3:
        score += 120000.0

    # Central influence is strongest in the opening.
    d_center = geom.center_dist.get(move, 8)
    if phase < 10:
        score += max(0.0, 105.0 - 14.0 * d_center)
    elif phase < 35:
        score += max(0.0, 62.0 - 6.0 * d_center)
    else:
        score += max(0.0, 34.0 - 2.7 * d_center)

    # Connectivity and liberties.
    if own_n:
        score += 32.0 * own_n + 8.0 * own_n * own_n
    elif player:
        score -= 36.0 if phase > 5 else 12.0

    score += min(95.0, 5.8 * lib_count)
    if lib_count <= 1:
        score -= 70.0
    elif lib_count == 2:
        score -= 20.0

    # Contact can be useful for blocking/cutting.
    score += 6.0 * enemy_n
    if enemy_n >= 2:
        score += 8.0 * enemy_n
        if own_n:
            score += 20.0

    # Merging components is valuable, especially with different edge/corner masks.
    k = len(adj_ids)
    if k >= 2:
        score += 135.0 * (k - 1) + min(160.0, 9.0 * sum_adj_size)

        max_edge_before = 0
        max_corner_before = 0
        for cid in adj_ids:
            comp = comps[cid]
            max_edge_before = max(max_edge_before, _popcount(comp[2]))
            max_corner_before = max(max_corner_before, _popcount(comp[1]))
        if ec > max_edge_before:
            score += 90.0 * (ec - max_edge_before)
        if cc > max_corner_before:
            score += 140.0 * (cc - max_corner_before)

    elif k == 1:
        score += min(90.0, 4.0 * sum_adj_size)

    # Bridge potential.
    if cc == 1:
        score += 155.0 + min(140.0, 6.0 * size)
        if geom.corner_dist:
            md = 99
            for i, distmap in enumerate(geom.corner_dist):
                if not ((corner_mask >> i) & 1):
                    di = distmap.get(move, 99)
                    if di < md:
                        md = di
            score += max(0.0, 115.0 - 8.0 * md)
    elif cc >= 2:
        score += 8000.0
    else:
        if geom.corner_dist:
            md = min(distmap.get(move, 99) for distmap in geom.corner_dist)
            if md <= 2:
                score += (3 - md) * 18.0

    # Fork potential.
    if ec == 1:
        score += 65.0 + min(70.0, 3.0 * size)
    elif ec == 2:
        score += 620.0 + min(260.0, 11.0 * size)
        if geom.edge_dist:
            md = 99
            for i, distmap in enumerate(geom.edge_dist):
                if not ((edge_mask >> i) & 1):
                    di = distmap.get(move, 99)
                    if di < md:
                        md = di
            score += max(0.0, 210.0 - 11.0 * md)
    elif ec >= 3:
        score += 8000.0

    if geom.corner_bit.get(move, 0):
        score += 80.0
        if phase < 8:
            score -= 20.0

    if geom.edge_bit.get(move, 0):
        score += 25.0

    # Ring/cycle potential.
    if own_n >= 2:
        for cid, cnt in adj_counts.items():
            if cnt >= 2:
                score += 240.0 + 85.0 * (cnt - 2)
                score += min(180.0, 5.0 * comps[cid][0])
        if k >= 2:
            score += 80.0 * k

    # Local surrounding patterns: strong ring threats.
    ringish = 0.0
    for x in neigh:
        if x in geom.boundary or len(geom.neighbors[x]) < 6:
            continue
        cnt = 0
        for y in geom.neighbors[x]:
            if y == move or y in player:
                cnt += 1
        if cnt >= 5:
            ringish += 1500.0
        elif cnt == 4:
            ringish += 430.0
        elif cnt == 3:
            ringish += 115.0
        elif cnt == 2:
            ringish += 24.0
    score += ringish

    # Interior points are flexible; early boundary moves are slightly less flexible.
    degree = len(neigh)
    if degree == 6:
        score += 12.0
    elif move in geom.boundary and phase < 12:
        score -= 8.0

    return score


# ---------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------

def _best_center(legal, geom, seed):
    return min(
        legal,
        key=lambda m: (
            geom.center_dist.get(m, 999),
            _tiny_noise(m, seed),
            m[0],
            m[1],
        )
    )


def _tiny_noise(cell, seed):
    r, c = cell
    x = ((r + 1) * 73856093) ^ ((c + 1) * 19349663) ^ ((seed + 1) * 83492791)
    x &= 0xffffffff
    x ^= (x >> 16)
    return (x & 1023) / 4096.0


def _emergency_fallback(me, opp, valid_mask):
    occ = set()
    try:
        for p in me:
            occ.add((int(p[0]), int(p[1])))
        for p in opp:
            occ.add((int(p[0]), int(p[1])))
    except Exception:
        pass

    tuple_index = False
    try:
        rows = int(valid_mask.shape[0])
        cols = int(valid_mask.shape[1])
        tuple_index = True
    except Exception:
        try:
            rows = len(valid_mask)
            cols = len(valid_mask[0]) if rows else 0
        except Exception:
            return (0, 0)

    cr = (rows - 1) / 2.0
    cc = (cols - 1) / 2.0

    best = None
    best_d = 1.0e30

    for r in range(rows):
        for c in range(cols):
            try:
                if tuple_index:
                    try:
                        v = bool(valid_mask[r, c])
                    except Exception:
                        v = bool(valid_mask[r][c])
                else:
                    v = bool(valid_mask[r][c])
            except Exception:
                v = False

            if v and (r, c) not in occ:
                d = (r - cr) * (r - cr) + (c - cc) * (c - cc)
                if d < best_d:
                    best_d = d
                    best = (r, c)

    if best is not None:
        return best
    return (0, 0)
