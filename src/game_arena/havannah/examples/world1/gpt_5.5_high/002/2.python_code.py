
import math
import heapq
from collections import deque

_INF = 10 ** 7
_GEOM_CACHE = {}


class _Geom:
    pass


def _popcount(x):
    return int(x).bit_count()


def _deltas_for_col(c):
    # Odd-q vertical offset coordinates, matching the prompt example:
    # for (4,1), neighbours include (3,0),(4,0),(3,2),(4,2).
    if c & 1:
        return ((-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1))
    return ((-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1))


def _axial_of(cell):
    r, c = cell
    x = c
    z = r - ((c + (c & 1)) // 2)
    y = -x - z
    return x, y, z


def _hex_dist_ax(a, b):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2]))


def _mask_key(valid_mask):
    n = len(valid_mask)
    m = len(valid_mask[0]) if n else 0
    rows = []
    for r in range(n):
        bits = 0
        for c in range(m):
            if bool(valid_mask[r][c]):
                bits |= 1 << c
        rows.append(bits)
    return n, m, tuple(rows)


def _get_geom(valid_mask):
    key = _mask_key(valid_mask)
    g = _GEOM_CACHE.get(key)
    if g is not None:
        return g

    n, m, rows = key
    g = _Geom()
    g.N = n
    g.M = m

    valid_cells = []
    valid_set = set()
    for r in range(n):
        for c in range(m):
            if rows[r] & (1 << c):
                cell = (r, c)
                valid_cells.append(cell)
                valid_set.add(cell)

    g.valid_cells = tuple(valid_cells)
    g.valid_set = valid_set

    neighbors = {}
    for r, c in valid_cells:
        ns = []
        for dr, dc in _deltas_for_col(c):
            nr, nc = r + dr, c + dc
            if (nr, nc) in valid_set:
                ns.append((nr, nc))
        neighbors[(r, c)] = tuple(ns)
    g.neighbors = neighbors

    boundary = [cell for cell in valid_cells if len(neighbors[cell]) < 6]
    if not boundary:
        boundary = list(valid_cells)
    g.boundary_cells = tuple(boundary)

    axial = {cell: _axial_of(cell) for cell in valid_cells}
    g.axial = axial

    xs = [axial[cell][0] for cell in valid_cells]
    ys = [axial[cell][1] for cell in valid_cells]
    zs = [axial[cell][2] for cell in valid_cells]
    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minz, maxz = min(zs), max(zs)

    extreme_bits = {}
    corner_candidates = []
    for cell in valid_cells:
        x, y, z = axial[cell]
        bits = 0
        if x == minx:
            bits |= 1 << 0
        if z == minz:
            bits |= 1 << 1
        if y == miny:
            bits |= 1 << 2
        if x == maxx:
            bits |= 1 << 3
        if z == maxz:
            bits |= 1 << 4
        if y == maxy:
            bits |= 1 << 5
        extreme_bits[cell] = bits
        if _popcount(bits) >= 2:
            corner_candidates.append(cell)

    # Normal Havannah hex masks give exactly six candidates.  The fallback keeps
    # the policy robust if a host uses a slightly different mask alignment.
    if len(corner_candidates) == 6:
        corners = sorted(corner_candidates)
    else:
        pool = list(boundary)
        if len(pool) < 6:
            pool = list(valid_cells)

        def corner_rank(cell):
            return (_popcount(extreme_bits.get(cell, 0)), -len(neighbors[cell]), -abs(cell[0] - n / 2.0) - abs(cell[1] - m / 2.0))

        selected = []
        while len(selected) < 6 and pool:
            if not selected:
                best = max(pool, key=corner_rank)
            else:
                best = max(
                    pool,
                    key=lambda p: (
                        min(_hex_dist_ax(axial[p], axial[q]) for q in selected),
                        corner_rank(p),
                    ),
                )
            selected.append(best)
            pool.remove(best)
        corners = sorted(selected)

    g.corners = tuple(corners)

    corner_mask = {}
    for i, cell in enumerate(corners):
        corner_mask[cell] = 1 << i
    g.corner_mask = corner_mask

    edge_mask = {}
    edge_cells = [[] for _ in range(6)]
    corner_set = set(corners)
    for cell in valid_cells:
        if cell in corner_set:
            edge_mask[cell] = 0
            continue
        bits = extreme_bits.get(cell, 0)
        edge_mask[cell] = bits
        for i in range(6):
            if bits & (1 << i):
                edge_cells[i].append(cell)

    g.edge_mask = edge_mask
    g.edge_cells = tuple(tuple(x) for x in edge_cells)

    cx = (minx + maxx) / 2.0
    cy = (miny + maxy) / 2.0
    cz = (minz + maxz) / 2.0
    maxd = 1.0
    rawd = {}
    for cell in valid_cells:
        x, y, z = axial[cell]
        d = max(abs(x - cx), abs(y - cy), abs(z - cz))
        rawd[cell] = d
        if d > maxd:
            maxd = d
    g.center_score = {cell: 1.0 - rawd[cell] / maxd for cell in valid_cells}

    _GEOM_CACHE[key] = g
    return g


def _has_ring_by_flood(stones, geom):
    # Exact for rings enclosing at least one non-player cell.
    if len(stones) < 6:
        return False

    visited = set()
    q = deque()

    for b in geom.boundary_cells:
        if b not in stones:
            visited.add(b)
            q.append(b)

    while q:
        cell = q.popleft()
        for nb in geom.neighbors[cell]:
            if nb not in stones and nb not in visited:
                visited.add(nb)
                q.append(nb)

    for cell in geom.valid_cells:
        if cell not in stones and cell not in visited:
            return True
    return False


def _has_cycle_ring_after(stones, move, geom):
    # Supplemental detector for rare rings enclosing only own stones.
    own_nbs = [nb for nb in geom.neighbors[move] if nb in stones]
    if len(own_nbs) < 2:
        return False

    own_nb_set = set(own_nbs)
    for i in range(len(own_nbs)):
        a = own_nbs[i]
        for j in range(i + 1, len(own_nbs)):
            b = own_nbs[j]
            blocked = set(own_nb_set)
            blocked.discard(a)
            blocked.discard(b)
            blocked.add(move)

            q = deque([(a, 0)])
            seen = {a}
            while q:
                cur, dist = q.popleft()
                if cur == b:
                    # Path a..b plus the new move forms a cycle.
                    # Require at least 6 stones in the cycle to avoid tiny
                    # triangular/lozenge cycles that do not surround a cell.
                    if dist >= 4:
                        return True
                    break
                for nb in geom.neighbors[cur]:
                    if nb in stones and nb not in blocked and nb not in seen:
                        seen.add(nb)
                        q.append((nb, dist + 1))
    return False


def _is_win_after(stones, move, geom):
    new_stones = set(stones)
    new_stones.add(move)

    # Bridge/fork: only the component containing the new stone can newly win.
    stack = [move]
    seen = {move}
    corners = 0
    edges = 0

    while stack:
        cell = stack.pop()
        corners |= geom.corner_mask.get(cell, 0)
        edges |= geom.edge_mask.get(cell, 0)

        if _popcount(corners) >= 2:
            return True
        if _popcount(edges) >= 3:
            return True

        for nb in geom.neighbors[cell]:
            if nb in new_stones and nb not in seen:
                seen.add(nb)
                stack.append(nb)

    adj_count = sum(1 for nb in geom.neighbors[move] if nb in stones)
    if adj_count >= 2:
        if _has_ring_by_flood(new_stones, geom):
            return True
        if _has_cycle_ring_after(new_stones, move, geom):
            return True

    return False


def _winning_moves(stones, geom, legal, limit=None):
    wins = []
    for mv in legal:
        if _is_win_after(stones, mv, geom):
            wins.append(mv)
            if limit is not None and len(wins) >= limit:
                break
    return wins


def _count_winning_moves(stones, geom, legal, limit=3):
    count = 0
    for mv in legal:
        if _is_win_after(stones, mv, geom):
            count += 1
            if count >= limit:
                return count
    return count


def _build_components(stones, geom):
    comp_id = {}
    comps = []
    unseen = set(stones)

    while unseen:
        start = unseen.pop()
        idx = len(comps)
        comp_id[start] = idx

        stack = [start]
        size = 0
        corners = 0
        edges = 0
        liberties = set()

        while stack:
            cell = stack.pop()
            size += 1
            corners |= geom.corner_mask.get(cell, 0)
            edges |= geom.edge_mask.get(cell, 0)

            for nb in geom.neighbors.get(cell, ()):
                if nb in stones:
                    if nb not in comp_id:
                        comp_id[nb] = idx
                        unseen.discard(nb)
                        stack.append(nb)
                else:
                    liberties.add(nb)

        comps.append((size, corners, edges, len(liberties)))

    return comp_id, comps


def _dijkstra_feature(sources, player, enemy, geom):
    dist = {}
    heap = []

    for s in sources:
        if s not in geom.valid_set or s in enemy:
            continue
        cost = 0 if s in player else 1
        if cost < dist.get(s, _INF):
            dist[s] = cost
            heapq.heappush(heap, (cost, s))

    while heap:
        d, cell = heapq.heappop(heap)
        if d != dist.get(cell):
            continue

        for nb in geom.neighbors[cell]:
            if nb in enemy:
                continue
            nd = d + (0 if nb in player else 1)
            if nd < dist.get(nb, _INF):
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))

    return dist


def _feature_distances(player, enemy, geom):
    corner_dists = []
    for c in geom.corners:
        corner_dists.append(_dijkstra_feature((c,), player, enemy, geom))

    while len(corner_dists) < 6:
        corner_dists.append({})

    edge_dists = []
    for cells in geom.edge_cells:
        edge_dists.append(_dijkstra_feature(cells, player, enemy, geom))

    while len(edge_dists) < 6:
        edge_dists.append({})

    return corner_dists, edge_dists


def _feature_distance_score(move, dists):
    corner_dists, edge_dists = dists

    cvals = []
    for d in corner_dists:
        v = d.get(move, _INF)
        cvals.append(max(0, v - 1) if v < _INF else _INF)
    cvals.sort()

    evals = []
    for d in edge_dists:
        v = d.get(move, _INF)
        evals.append(max(0, v - 1) if v < _INF else _INF)
    evals.sort()

    score = 0.0

    if len(cvals) >= 2 and cvals[1] < _INF // 2:
        bridge_cost = cvals[0] + cvals[1]
        score += 260.0 / ((bridge_cost + 1.0) ** 1.25)
        if bridge_cost <= 2:
            score += 70.0 * (3 - bridge_cost)

    if len(evals) >= 3 and evals[2] < _INF // 2:
        fork_cost = evals[0] + evals[1] + evals[2]
        score += 330.0 / ((fork_cost + 1.5) ** 1.22)
        if fork_cost <= 3:
            score += 55.0 * (4 - fork_cost)

    # A single nearby feature is useful, but less decisive.
    if cvals and cvals[0] < _INF // 2:
        score += 25.0 / (cvals[0] + 1.0)
    if evals and evals[0] < _INF // 2:
        score += 20.0 / (evals[0] + 1.0)

    return score


def _local_potential(move, comp_id, comps, stones, occupied, geom):
    ids = set()
    touch_count = {}
    own_adj = 0

    for nb in geom.neighbors[move]:
        cid = comp_id.get(nb)
        if cid is not None:
            ids.add(cid)
            touch_count[cid] = touch_count.get(cid, 0) + 1
            own_adj += 1

    corners = geom.corner_mask.get(move, 0)
    edges = geom.edge_mask.get(move, 0)
    merged_size = 1
    liberties = 0

    for cid in ids:
        sz, cm, em, lib = comps[cid]
        merged_size += sz
        corners |= cm
        edges |= em
        liberties += lib

    corner_count = _popcount(corners)
    edge_count = _popcount(edges)
    empty_adj = sum(1 for nb in geom.neighbors[move] if nb not in occupied)

    score = 0.0

    # Connectivity and growth.
    score += 6.0 * math.sqrt(max(1, merged_size))
    score += 12.0 * own_adj
    score += 18.0 * len(ids)
    if len(ids) >= 2:
        score += 18.0 * len(ids) * (len(ids) - 1)

    # Bridge and fork feature potential.
    if corner_count == 1:
        score += 38.0
    elif corner_count >= 2:
        score += 180.0

    if edge_count == 1:
        score += 24.0
    elif edge_count == 2:
        score += 125.0
    elif edge_count >= 3:
        score += 360.0

    score += 9.0 * corner_count * edge_count

    # Ring/cycle shape potential: touching the same component from multiple
    # sides is often a ring-making move.
    duplicate_touches = sum(max(0, v - 1) for v in touch_count.values())
    if duplicate_touches:
        score += 48.0 * duplicate_touches + 8.0 * own_adj

    if own_adj >= 2:
        score += 7.0 * own_adj * own_adj

    score += 4.0 * empty_adj
    score += min(20.0, 0.30 * liberties)

    return score


def _tiny_tiebreak(move, salt):
    r, c = move
    x = ((r + 17) * 73856093) ^ ((c + 31) * 19349663) ^ ((salt + 7) * 83492791)
    return (x & 0xFFFF) / 100000000.0


def _score_move(move, me_set, opp_set, geom,
                my_comp_id, my_comps, opp_comp_id, opp_comps,
                my_dists, opp_dists):
    occupied = me_set | opp_set
    move_no = len(occupied)

    own_local = _local_potential(move, my_comp_id, my_comps, me_set, occupied, geom)
    opp_local = _local_potential(move, opp_comp_id, opp_comps, opp_set, occupied, geom)

    score = 1.08 * own_local + 0.92 * opp_local
    score += 1.05 * _feature_distance_score(move, my_dists)
    score += 0.86 * _feature_distance_score(move, opp_dists)

    own_adj = sum(1 for nb in geom.neighbors[move] if nb in me_set)
    opp_adj = sum(1 for nb in geom.neighbors[move] if nb in opp_set)

    # Early central development, gradually less important than concrete threats.
    center_weight = max(4.0, 24.0 - 0.13 * move_no)
    score += center_weight * geom.center_score.get(move, 0.0)

    # Avoid totally isolated stones after the opening; reward contested points.
    if me_set and own_adj == 0:
        score -= 10.0
    if move_no > 4 and own_adj == 0 and opp_adj == 0:
        score -= 8.0

    score += 4.0 * opp_adj + 2.5 * own_adj

    # Corners/edges are useful, but isolated early corner grabs are not too much.
    if geom.corner_mask.get(move, 0):
        score += 8.0
    elif geom.edge_mask.get(move, 0):
        score += 4.0

    score += _tiny_tiebreak(move, move_no)
    return score


def _select_move(candidates, legal, me_set, opp_set, geom, use_threats=True):
    my_comp_id, my_comps = _build_components(me_set, geom)
    opp_comp_id, opp_comps = _build_components(opp_set, geom)

    my_dists = _feature_distances(me_set, opp_set, geom)
    opp_dists = _feature_distances(opp_set, me_set, geom)

    scores = {}
    for mv in candidates:
        scores[mv] = _score_move(
            mv, me_set, opp_set, geom,
            my_comp_id, my_comps, opp_comp_id, opp_comps,
            my_dists, opp_dists
        )

    total_stones = len(me_set) + len(opp_set)

    if use_threats and total_stones >= 8:
        # Reward moves that create two or more immediate wins next turn.
        top_own = sorted(candidates, key=lambda x: scores[x], reverse=True)[:20]
        for mv in top_own:
            next_legal = [x for x in legal if x != mv]
            cnt = _count_winning_moves(me_set | {mv}, geom, next_legal, limit=3)
            if cnt >= 2:
                scores[mv] += 520.0 + 170.0 * cnt
            elif cnt == 1:
                scores[mv] += 70.0

        # Also occupy opponent moves that would create a double threat.
        opp_interest = sorted(
            legal,
            key=lambda x: _score_move(
                x, opp_set, me_set, geom,
                opp_comp_id, opp_comps, my_comp_id, my_comps,
                opp_dists, my_dists
            ),
            reverse=True
        )[:14]

        danger = {}
        for mv in opp_interest:
            next_legal = [x for x in legal if x != mv]
            cnt = _count_winning_moves(opp_set | {mv}, geom, next_legal, limit=3)
            if cnt >= 2:
                danger[mv] = 430.0 + 150.0 * cnt
            elif cnt == 1:
                danger[mv] = 45.0

        for mv, val in danger.items():
            if mv in scores:
                scores[mv] += val

    return max(candidates, key=lambda x: scores.get(x, -1e100))


def _opening_move(legal, opp_set, geom):
    def val(mv):
        opp_adj = sum(1 for nb in geom.neighbors[mv] if nb in opp_set)
        return geom.center_score.get(mv, 0.0) + 0.035 * opp_adj + _tiny_tiebreak(mv, len(opp_set))

    return max(legal, key=val)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    geom = _get_geom(valid_mask)

    me_set = set()
    for r, c in me:
        cell = (int(r), int(c))
        if cell in geom.valid_set:
            me_set.add(cell)

    opp_set = set()
    for r, c in opp:
        cell = (int(r), int(c))
        if cell in geom.valid_set:
            opp_set.add(cell)

    occupied = me_set | opp_set
    legal = [cell for cell in geom.valid_cells if cell not in occupied]

    # A full board should not occur because Havannah ends earlier, but always
    # return a tuple.
    if not legal:
        cell = geom.valid_cells[0] if geom.valid_cells else (0, 0)
        return (int(cell[0]), int(cell[1]))

    # Opening: take the most central available point.
    if len(me_set) == 0 and len(opp_set) <= 1:
        mv = _opening_move(legal, opp_set, geom)
        return (int(mv[0]), int(mv[1]))

    # 1. Win immediately if possible.
    my_wins = _winning_moves(me_set, geom, legal, limit=None)
    if my_wins:
        mv = _select_move(my_wins, legal, me_set, opp_set, geom, use_threats=False)
        if mv not in legal:
            mv = my_wins[0]
        return (int(mv[0]), int(mv[1]))

    # 2. Block opponent's immediate win.
    opp_wins = _winning_moves(opp_set, geom, legal, limit=None)
    if opp_wins:
        if len(opp_wins) == 1:
            mv = opp_wins[0]
        else:
            mv = _select_move(opp_wins, legal, me_set, opp_set, geom, use_threats=False)
        if mv not in legal:
            mv = opp_wins[0]
        return (int(mv[0]), int(mv[1]))

    # 3. Otherwise choose the best strategic/tactical move.
    mv = _select_move(legal, legal, me_set, opp_set, geom, use_threats=True)

    if mv not in legal:
        mv = legal[0]

    return (int(mv[0]), int(mv[1]))
