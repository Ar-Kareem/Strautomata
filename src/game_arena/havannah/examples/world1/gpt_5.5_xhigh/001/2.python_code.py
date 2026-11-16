
from __future__ import annotations

import math
import heapq
from collections import deque

_INF = 10 ** 8
_SQRT3_OVER_2 = 0.8660254037844386
_META_CACHE = {}


class _Meta:
    __slots__ = (
        "rows", "cols", "M", "scheme", "cells", "index",
        "neighbors", "nbr_order", "degree",
        "boundary", "boundary_set",
        "corners", "corner_bit", "corner_cells",
        "edge_id", "edge_bit", "edge_cells",
        "xy", "center_xy", "max_center_dist",
    )


def _bit_count(x: int) -> int:
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")


def _ordered_deltas(c: int, scheme: int):
    # scheme 0 is the layout matching the prompt example:
    # odd columns are shifted upward.
    if scheme == 0:
        if c & 1:
            return ((-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1))
        return ((-1, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))

    # Mirrored fallback layout.
    if c & 1:
        return ((-1, 0), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1))
    return ((-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1))


def _make_neighbor_data(cells, index, rows, cols, scheme):
    nbr_order = []
    neighbors = []
    degree = []
    for r, c in cells:
        order = []
        for dr, dc in _ordered_deltas(c, scheme):
            rr, cc = r + dr, c + dc
            if 0 <= rr < rows and 0 <= cc < cols:
                j = index[rr][cc]
            else:
                j = -1
            order.append(j)
        nbr_order.append(order)
        ns = [j for j in order if j >= 0]
        neighbors.append(ns)
        degree.append(len(ns))
    return nbr_order, neighbors, degree


def _scheme_metric(degree):
    if not degree:
        return 0.0
    cnt3 = sum(1 for d in degree if d == 3)
    cnt6 = sum(1 for d in degree if d == 6)
    bad = sum(1 for d in degree if d not in (3, 4, 6))
    low = sum(1 for d in degree if d < 3)
    return low * 1000.0 + bad * 100.0 + abs(cnt3 - 6) * 50.0 - cnt6 * 0.01


def _edge_assignment_by_boundary(neighbors, boundary, corners, M):
    if len(corners) != 6:
        return None

    bset = set(boundary)
    cset = set(corners)
    bneis = {i: [j for j in neighbors[i] if j in bset] for i in boundary}
    start = corners[0]
    if start not in bneis or not bneis[start]:
        return None

    best = None
    for first in bneis[start]:
        cycle = [start]
        seen = {start}
        prev, cur = start, first
        ok = False

        for _ in range(len(boundary) + 6):
            if cur == start:
                ok = True
                break
            if cur in seen:
                break
            cycle.append(cur)
            seen.add(cur)

            choices = [x for x in bneis.get(cur, []) if x != prev]
            if not choices:
                break
            unvisited = [x for x in choices if x == start or x not in seen]
            nxt = unvisited[0] if unvisited else choices[0]
            prev, cur = cur, nxt

        if ok and all(c in seen for c in corners):
            if best is None or len(cycle) > len(best):
                best = cycle

    if best is None:
        return None

    pos = {cell: p for p, cell in enumerate(best)}
    if not all(c in pos for c in corners):
        return None

    corner_positions = sorted(pos[c] for c in corners)
    L = len(best)
    edge_id = [-1] * M

    for k in range(6):
        a = corner_positions[k]
        b = corner_positions[(k + 1) % 6]
        p = (a + 1) % L
        while p != b:
            cell = best[p]
            if cell not in cset:
                edge_id[cell] = k
            p = (p + 1) % L

    return edge_id


def _get_meta(valid_mask):
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0

    bits = []
    for r in range(rows):
        for c in range(cols):
            bits.append(bool(valid_mask[r][c]))

    key = (rows, cols, tuple(bits))
    cached = _META_CACHE.get(key)
    if cached is not None:
        return cached

    cells = []
    index = [[-1] * cols for _ in range(rows)]
    for r in range(rows):
        base = r * cols
        for c in range(cols):
            if bits[base + c]:
                index[r][c] = len(cells)
                cells.append((r, c))

    M = len(cells)

    best_scheme = 0
    best_data = None
    best_metric = None
    for scheme in (0, 1):
        data = _make_neighbor_data(cells, index, rows, cols, scheme)
        metric = _scheme_metric(data[2])
        if best_metric is None or metric < best_metric:
            best_metric = metric
            best_scheme = scheme
            best_data = data

    nbr_order, neighbors, degree = best_data if best_data else ([], [], [])
    boundary = [i for i, d in enumerate(degree) if d < 6]
    boundary_set = set(boundary)

    if M:
        odd_shift = -0.5 if best_scheme == 0 else 0.5
        xy = [(c * _SQRT3_OVER_2, r + odd_shift * (c & 1)) for r, c in cells]
        cx = sum(x for x, _ in xy) / M
        cy = sum(y for _, y in xy) / M
        maxd = max(math.hypot(x - cx, y - cy) for x, y in xy)
        if maxd <= 0:
            maxd = 1.0
    else:
        xy = []
        cx = cy = 0.0
        maxd = 1.0

    ax = []
    if M:
        for r, c in cells:
            if best_scheme == 0:
                ar = r - ((c + (c & 1)) // 2)
            else:
                ar = r - (c // 2)
            q = c
            s = -q - ar
            ax.append((q, ar, s))

        minq = min(q for q, _, _ in ax)
        maxq = max(q for q, _, _ in ax)
        mina = min(a for _, a, _ in ax)
        maxa = max(a for _, a, _ in ax)
        mins = min(s for _, _, s in ax)
        maxs = max(s for _, _, s in ax)

        corners = []
        for i, (q, a, s) in enumerate(ax):
            ext = (
                q == minq, q == maxq,
                a == mina, a == maxa,
                s == mins, s == maxs,
            )
            if sum(ext) >= 2:
                corners.append(i)
    else:
        minq = maxq = mina = maxa = mins = maxs = 0
        corners = []

    if len(corners) != 6:
        deg_corners = [i for i, d in enumerate(degree) if d <= 3]
        if len(deg_corners) == 6:
            corners = deg_corners
        else:
            def radial(i):
                x, y = xy[i]
                return (x - cx) * (x - cx) + (y - cy) * (y - cy)

            candidates = []
            for seq in (corners, deg_corners, boundary):
                for i in seq:
                    if i not in candidates:
                        candidates.append(i)

            candidates.sort(key=radial, reverse=True)
            corners = []
            for i in candidates:
                if i not in corners:
                    corners.append(i)
                    if len(corners) == 6:
                        break
            if len(corners) < 6:
                all_cells = sorted(range(M), key=radial, reverse=True)
                for i in all_cells:
                    if i not in corners:
                        corners.append(i)
                        if len(corners) == 6:
                            break

    if M:
        corners = sorted(corners[:6], key=lambda i: math.atan2(xy[i][1] - cy, xy[i][0] - cx))
    else:
        corners = []

    corner_set = set(corners)

    edge_id = [-1] * M
    if M:
        for i, (q, a, s) in enumerate(ax):
            if i in corner_set:
                continue
            tests = (
                q == minq,
                a == maxa,
                s == mins,
                q == maxq,
                a == mina,
                s == maxs,
            )
            for k, t in enumerate(tests):
                if t:
                    edge_id[i] = k
                    break

    edge_cells = [[] for _ in range(6)]
    for i, e in enumerate(edge_id):
        if 0 <= e < 6 and i not in corner_set:
            edge_cells[e].append(i)

    if M and (
        any(len(edge_cells[k]) == 0 for k in range(6)) or
        any(i not in corner_set and edge_id[i] < 0 for i in boundary)
    ):
        alt = _edge_assignment_by_boundary(neighbors, boundary, corners, M)
        if alt is not None:
            alt_cells = [[] for _ in range(6)]
            for i, e in enumerate(alt):
                if 0 <= e < 6 and i not in corner_set:
                    alt_cells[e].append(i)
            if all(len(alt_cells[k]) > 0 for k in range(6)):
                edge_id = alt
                edge_cells = alt_cells

    corner_bit = [0] * M
    for k, i in enumerate(corners[:6]):
        corner_bit[i] = 1 << k

    edge_bit = [0] * M
    for i, e in enumerate(edge_id):
        if 0 <= e < 6 and i not in corner_set:
            edge_bit[i] = 1 << e

    corner_cells = [[i] for i in corners[:6]]
    while len(corner_cells) < 6:
        corner_cells.append([])

    meta = _Meta()
    meta.rows = rows
    meta.cols = cols
    meta.M = M
    meta.scheme = best_scheme
    meta.cells = cells
    meta.index = index
    meta.neighbors = neighbors
    meta.nbr_order = nbr_order
    meta.degree = degree
    meta.boundary = boundary
    meta.boundary_set = boundary_set
    meta.corners = corners
    meta.corner_bit = corner_bit
    meta.corner_cells = corner_cells
    meta.edge_id = edge_id
    meta.edge_bit = edge_bit
    meta.edge_cells = edge_cells
    meta.xy = xy
    meta.center_xy = (cx, cy)
    meta.max_center_dist = maxd

    if len(_META_CACHE) > 8:
        _META_CACHE.clear()
    _META_CACHE[key] = meta
    return meta


def _to_indices(stones, meta):
    out = set()
    for rc in stones:
        try:
            r, c = int(rc[0]), int(rc[1])
        except Exception:
            continue
        if 0 <= r < meta.rows and 0 <= c < meta.cols:
            i = meta.index[r][c]
            if i >= 0:
                out.add(i)
    return out


def _fallback_move(me, opp, valid_mask):
    occ = set()
    for seq in (me, opp):
        for rc in seq:
            try:
                occ.add((int(rc[0]), int(rc[1])))
            except Exception:
                pass

    try:
        rows = len(valid_mask)
        cols = len(valid_mask[0]) if rows else 0
        legal = []
        for r in range(rows):
            for c in range(cols):
                if bool(valid_mask[r][c]) and (r, c) not in occ:
                    legal.append((r, c))

        if legal:
            cr = sum(r for r, _ in legal) / len(legal)
            cc = sum(c for _, c in legal) / len(legal)
            return min(legal, key=lambda rc: (rc[0] - cr) ** 2 + (rc[1] - cc) ** 2)
    except Exception:
        pass

    return (0, 0)


def _best_center(meta, legal):
    cx, cy = meta.center_xy
    return min(
        legal,
        key=lambda i: (
            (meta.xy[i][0] - cx) ** 2 + (meta.xy[i][1] - cy) ** 2,
            meta.cells[i][0],
            meta.cells[i][1],
        ),
    )


def _has_connection_win(stones, meta):
    visited = set()
    for start in stones:
        if start in visited:
            continue

        stack = [start]
        visited.add(start)
        cb = 0
        eb = 0

        while stack:
            i = stack.pop()
            cb |= meta.corner_bit[i]
            eb |= meta.edge_bit[i]

            for nb in meta.neighbors[i]:
                if nb in stones and nb not in visited:
                    visited.add(nb)
                    stack.append(nb)

        if _bit_count(cb) >= 2 or _bit_count(eb) >= 3:
            return True

    return False


def _ring_exists(stones, meta):
    if len(stones) < 6:
        return False

    # Empty/opponent-filled enclosed regions.
    visited = set()
    q = deque()

    for i in meta.boundary:
        if i not in stones:
            visited.add(i)
            q.append(i)

    while q:
        i = q.popleft()
        for nb in meta.neighbors[i]:
            if nb not in stones and nb not in visited:
                visited.add(nb)
                q.append(nb)

    if len(visited) < meta.M - len(stones):
        return True

    # Own-stone-only interior: a friendly stone fully surrounded by friendly
    # stones means the six surrounding stones form a valid ring around it.
    for i in stones:
        if meta.degree[i] == 6:
            surrounded = True
            for nb in meta.neighbors[i]:
                if nb not in stones:
                    surrounded = False
                    break
            if surrounded:
                return True

    return False


def _is_win(stones, meta):
    return _has_connection_win(stones, meta) or _ring_exists(stones, meta)


def _build_components(stones, meta):
    comp = [-1] * meta.M
    comps = []

    for start in stones:
        if comp[start] != -1:
            continue

        cid = len(comps)
        stack = [start]
        comp[start] = cid
        size = 0
        eb = 0
        cb = 0

        while stack:
            i = stack.pop()
            size += 1
            eb |= meta.edge_bit[i]
            cb |= meta.corner_bit[i]

            for nb in meta.neighbors[i]:
                if nb in stones and comp[nb] == -1:
                    comp[nb] = cid
                    stack.append(nb)

        comps.append((size, eb, cb))

    return comp, comps


def _new_stats(idx, comp_arr, comps, meta):
    seen = set()
    size = 1
    eb = meta.edge_bit[idx]
    cb = meta.corner_bit[idx]

    for nb in meta.neighbors[idx]:
        cid = comp_arr[nb]
        if cid >= 0 and cid not in seen:
            seen.add(cid)
            s, e, c = comps[cid]
            size += s
            eb |= e
            cb |= c

    return size, eb, cb, len(seen)


def _distances_from_sources(meta, player, opponent, sources):
    all_dists = []
    blocked = opponent

    for srcs in sources:
        dist = [_INF] * meta.M
        heap = []

        for s in srcs:
            if s in blocked:
                continue
            d0 = 0 if s in player else 1
            if d0 < dist[s]:
                dist[s] = d0
                heapq.heappush(heap, (d0, s))

        while heap:
            d, i = heapq.heappop(heap)
            if d != dist[i]:
                continue

            for nb in meta.neighbors[i]:
                if nb in blocked:
                    continue
                nd = d + (0 if nb in player else 1)
                if nd < dist[nb]:
                    dist[nb] = nd
                    heapq.heappush(heap, (nd, nb))

        all_dists.append(dist)

    return all_dists


def _potential_sums(idx, d_edges, d_corners):
    ed = []
    for dist in d_edges:
        v = dist[idx]
        if v < _INF:
            ed.append(max(0, v - 1))
    ed.sort()
    fork = ed[0] + ed[1] + ed[2] if len(ed) >= 3 else _INF

    cr = []
    for dist in d_corners:
        v = dist[idx]
        if v < _INF:
            cr.append(max(0, v - 1))
    cr.sort()
    bridge = cr[0] + cr[1] if len(cr) >= 2 else _INF

    return fork, bridge


def _potential_score(fork, bridge):
    s = 0.0

    if fork < _INF:
        s += 230.0 / (fork + 1.0)
        if fork <= 2:
            s += 85.0 * (3 - fork)
        elif fork <= 5:
            s += 15.0 * (6 - fork)

    if bridge < _INF:
        s += 150.0 / (bridge + 1.0)
        if bridge <= 1:
            s += 80.0 * (2 - bridge)
        elif bridge <= 4:
            s += 12.0 * (5 - bridge)

    return s


def _shape_features(idx, stones, comp_arr, meta):
    order = meta.nbr_order[idx]
    occ = [(j >= 0 and j in stones) for j in order]
    cnt = sum(1 for x in occ if x)
    if cnt == 0:
        return 0, 0, False

    groups = 0
    for k in range(6):
        if occ[k] and not occ[(k - 1) % 6]:
            groups += 1

    by_comp = {}
    for k, j in enumerate(order):
        if occ[k]:
            cid = comp_arr[j]
            by_comp.setdefault(cid, []).append(k)

    separated_same_component = False
    for positions in by_comp.values():
        if len(positions) < 2:
            continue
        flags = [False] * 6
        for p in positions:
            flags[p] = True
        g = 0
        for k in range(6):
            if flags[k] and not flags[(k - 1) % 6]:
                g += 1
        if g >= 2:
            separated_same_component = True
            break

    return cnt, groups, separated_same_component


def _ring_potential(idx, stones, meta):
    best = 0

    # A move completing or nearly completing the six neighbors around an
    # interior cell is a strong local ring pattern.
    for center in meta.neighbors[idx]:
        if meta.degree[center] < 6:
            continue
        cnt = 0
        for nb in meta.neighbors[center]:
            if nb == idx or nb in stones:
                cnt += 1
        if cnt > best:
            best = cnt

    return best


def _score_move(
    idx, meta, me_set, opp_set,
    me_comp, me_comps, opp_comp, opp_comps,
    my_d_edges, my_d_corners, op_d_edges, op_d_corners,
    total_stones,
):
    score = 0.0

    x, y = meta.xy[idx]
    cx, cy = meta.center_xy
    central = 1.0 - min(1.0, math.hypot(x - cx, y - cy) / meta.max_center_dist)
    if total_stones < 10:
        score += central * (82.0 - 4.0 * total_stones)
    else:
        score += central * 25.0

    own_nei = 0
    opp_nei = 0
    empty_nei = 0
    for nb in meta.neighbors[idx]:
        if nb in me_set:
            own_nei += 1
        elif nb in opp_set:
            opp_nei += 1
        else:
            empty_nei += 1

    score += own_nei * 10.0 + opp_nei * 6.0 + empty_nei * 1.4
    if own_nei == 0 and len(me_set) > 0:
        score -= 12.0 if total_stones > 8 else 4.0
    if own_nei >= 2:
        score += 10.0
    if opp_nei >= 2:
        score += 5.0 * opp_nei

    osize, oeb, ocb, oncomp = _new_stats(idx, me_comp, me_comps, meta)
    oe = _bit_count(oeb)
    oc = _bit_count(ocb)

    score += max(0, oncomp - 1) * 30.0
    score += min(osize, 16) * 2.25 + max(0, osize - 16) * 0.7
    score += oe * 18.0 + oc * 30.0
    if oe == 1:
        score += 10.0
    elif oe == 2:
        score += 125.0
    elif oe >= 3:
        score += 10000.0
    if oc == 1:
        score += 46.0
    elif oc >= 2:
        score += 10000.0

    dsize, deb, dcb, dncomp = _new_stats(idx, opp_comp, opp_comps, meta)
    de = _bit_count(deb)
    dc = _bit_count(dcb)

    score += max(0, dncomp - 1) * 26.0
    score += min(dsize, 18) * 1.75 + max(0, dsize - 18) * 0.55
    score += de * 16.0 + dc * 29.0
    if de == 2:
        score += 118.0
    elif de >= 3:
        score += 9000.0
    if dc == 1:
        score += 56.0
    elif dc >= 2:
        score += 9000.0

    my_fork, my_bridge = _potential_sums(idx, my_d_edges, my_d_corners)
    op_fork, op_bridge = _potential_sums(idx, op_d_edges, op_d_corners)
    score += _potential_score(my_fork, my_bridge)
    score += 0.88 * _potential_score(op_fork, op_bridge)

    cnt, groups, sep_same = _shape_features(idx, me_set, me_comp, meta)
    if sep_same:
        score += 82.0
    score += max(0, groups - 1) * 14.0 + max(0, cnt - 1) * 6.0

    ocnt, ogroups, osep_same = _shape_features(idx, opp_set, opp_comp, meta)
    if osep_same:
        score += 70.0
    score += 0.85 * (max(0, ogroups - 1) * 14.0 + max(0, ocnt - 1) * 6.0)

    rp = _ring_potential(idx, me_set, meta)
    if rp >= 6:
        score += 260.0
    elif rp == 5:
        score += 150.0
    elif rp == 4:
        score += 45.0
    elif rp == 3:
        score += 12.0

    orp = _ring_potential(idx, opp_set, meta)
    if orp >= 6:
        score += 230.0
    elif orp == 5:
        score += 132.0
    elif orp == 4:
        score += 40.0
    elif orp == 3:
        score += 10.0

    if meta.edge_bit[idx]:
        score += 6.0
        if total_stones < 8 and own_nei == 0:
            score -= 8.0
    if meta.corner_bit[idx]:
        score += 12.0
        if total_stones < 10 and own_nei == 0:
            score -= 10.0

    r, c = meta.cells[idx]
    score += ((r * 31 + c * 17) % 11) * 0.001
    return score


def _count_winning_moves(player_set, legal, forbidden, meta, limit=3):
    cnt = 0

    for j in legal:
        if j == forbidden:
            continue

        # A winning placement must attach to existing stones on this board.
        adjacent = False
        for nb in meta.neighbors[j]:
            if nb in player_set:
                adjacent = True
                break
        if not adjacent:
            continue

        player_set.add(j)
        if _is_win(player_set, meta):
            cnt += 1
        player_set.remove(j)

        if cnt >= limit:
            return cnt

    return cnt


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        meta = _get_meta(valid_mask)
        me_set = _to_indices(me, meta)
        opp_set = _to_indices(opp, meta)
        occupied = me_set | opp_set
        legal = [i for i in range(meta.M) if i not in occupied]

        if not legal:
            return _fallback_move(me, opp, valid_mask)

        if len(legal) == 1:
            r, c = meta.cells[legal[0]]
            return (int(r), int(c))

        total_stones = len(me_set) + len(opp_set)

        if total_stones == 0:
            idx = _best_center(meta, legal)
            r, c = meta.cells[idx]
            return (int(r), int(c))

        # 1. Win immediately if possible.
        winning = []
        for i in legal:
            me_set.add(i)
            if _is_win(me_set, meta):
                winning.append(i)
            me_set.remove(i)

        if winning:
            idx = _best_center(meta, winning)
            r, c = meta.cells[idx]
            return (int(r), int(c))

        # 2. Block opponent's immediate wins.
        opp_winning = []
        for i in legal:
            opp_set.add(i)
            if _is_win(opp_set, meta):
                opp_winning.append(i)
            opp_set.remove(i)

        if len(opp_winning) == 1:
            r, c = meta.cells[opp_winning[0]]
            return (int(r), int(c))

        # 3. Positional scoring.
        me_comp, me_comps = _build_components(me_set, meta)
        opp_comp, opp_comps = _build_components(opp_set, meta)

        my_d_edges = _distances_from_sources(meta, me_set, opp_set, meta.edge_cells)
        my_d_corners = _distances_from_sources(meta, me_set, opp_set, meta.corner_cells)
        op_d_edges = _distances_from_sources(meta, opp_set, me_set, meta.edge_cells)
        op_d_corners = _distances_from_sources(meta, opp_set, me_set, meta.corner_cells)

        candidates = opp_winning if opp_winning else legal
        scored = []
        for i in candidates:
            sc = _score_move(
                i, meta, me_set, opp_set,
                me_comp, me_comps, opp_comp, opp_comps,
                my_d_edges, my_d_corners, op_d_edges, op_d_corners,
                total_stones,
            )
            if opp_winning:
                sc += 5000.0
            scored.append((sc, i))

        scored.sort(reverse=True)

        # If there were multiple immediate opponent wins, choose the best block.
        # The position may be losing, but this remains the most resilient legal move.
        if opp_winning:
            idx = scored[0][1]
            r, c = meta.cells[idx]
            return (int(r), int(c))

        best_score, best_idx = scored[0]

        # 4. Among the best static moves, prefer moves creating double threats.
        if len(me_set) >= 4 and len(legal) > 3:
            top_n = min(10, len(scored))
            for base_score, i in scored[:top_n]:
                me_set.add(i)
                threats = _count_winning_moves(me_set, legal, i, meta, limit=3)
                me_set.remove(i)

                bonus = 0.0
                if threats >= 2:
                    bonus = 1000.0 + 200.0 * threats
                elif threats == 1:
                    bonus = 80.0

                final_score = base_score + bonus
                if final_score > best_score:
                    best_score = final_score
                    best_idx = i

        r, c = meta.cells[best_idx]
        return (int(r), int(c))

    except Exception:
        return _fallback_move(me, opp, valid_mask)
