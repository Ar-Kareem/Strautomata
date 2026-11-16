
from __future__ import annotations

import heapq
import math
import time
from itertools import combinations

_INF = 10**6

# Odd-column vertical offset, matching the prompt's example.
# Internally we use (q=col, t=row+col//2) with neighbor deltas below.
_DIRS_QT = ((0, -1), (1, 0), (1, 1), (0, 1), (-1, 0), (-1, -1))

_CACHE = {}
_HAS_BITCOUNT = hasattr(int, "bit_count")


def _popcount(x: int) -> int:
    return x.bit_count() if _HAS_BITCOUNT else bin(x).count("1")


class BoardInfo:
    __slots__ = (
        "H", "W", "total", "valid", "valid_indices",
        "neighbors", "neighbor_dirs", "boundary",
        "corner_indices", "corner_bits", "edge_bits", "edge_cells",
        "corner_pairs", "edge_triples",
        "center_dist", "center_order",
    )

    def __init__(self, H: int, W: int, flat):
        self.H = H
        self.W = W
        self.total = H * W

        valid = list(flat)
        if len(valid) < self.total:
            valid += [False] * (self.total - len(valid))
        elif len(valid) > self.total:
            valid = valid[:self.total]
        self.valid = valid

        valid_indices = [i for i, ok in enumerate(valid) if ok]
        self.valid_indices = valid_indices

        qs = [0] * self.total
        ts = [0] * self.total
        ds = [0] * self.total

        qvals, tvals, dvals = [], [], []
        for idx in valid_indices:
            r, c = divmod(idx, W)
            q = c
            t = r + (c // 2)
            d = t - q
            qs[idx], ts[idx], ds[idx] = q, t, d
            qvals.append(q)
            tvals.append(t)
            dvals.append(d)

        if valid_indices:
            qmin, qmax = min(qvals), max(qvals)
            tmin, tmax = min(tvals), max(tvals)
            dmin, dmax = min(dvals), max(dvals)
            cq = (qmin + qmax) / 2.0
            ct = (tmin + tmax) / 2.0
            cd = (dmin + dmax) / 2.0
        else:
            qmin = qmax = tmin = tmax = dmin = dmax = 0
            cq = ct = cd = 0.0

        neighbors = [() for _ in range(self.total)]
        neighbor_dirs = [(-1, -1, -1, -1, -1, -1) for _ in range(self.total)]

        for idx in valid_indices:
            r, c = divmod(idx, W)
            q = c
            t = r + (c // 2)
            ordered = []
            compact = []
            for dq, dt in _DIRS_QT:
                nq = q + dq
                nt = t + dt
                nr = nt - (nq // 2)
                nc = nq
                nidx = -1
                if 0 <= nr < H and 0 <= nc < W:
                    cand = nr * W + nc
                    if valid[cand]:
                        nidx = cand
                        compact.append(cand)
                ordered.append(nidx)
            neighbor_dirs[idx] = tuple(ordered)
            neighbors[idx] = tuple(compact)

        self.neighbors = neighbors
        self.neighbor_dirs = neighbor_dirs
        self.boundary = [i for i in valid_indices if len(neighbors[i]) < 6]

        center_dist = [99.0] * self.total
        for idx in valid_indices:
            dist = max(abs(qs[idx] - cq), abs(ts[idx] - ct), abs(ds[idx] - cd))
            center_dist[idx] = float(dist)
        self.center_dist = center_dist

        # In the (q,t,d=t-q) coordinates, the six sides are coordinate extremes.
        corner_candidates = []
        for idx in valid_indices:
            flags = (
                qs[idx] == qmin, qs[idx] == qmax,
                ts[idx] == tmin, ts[idx] == tmax,
                ds[idx] == dmin, ds[idx] == dmax,
            )
            if sum(1 for f in flags if f) >= 2:
                corner_candidates.append(idx)

        # Robust fallback for unusual masks.
        if len(corner_candidates) != 6:
            degree_corners = [i for i in valid_indices if len(neighbors[i]) <= 3]
            if len(degree_corners) >= 6:
                corner_candidates = sorted(
                    degree_corners, key=lambda i: (-center_dist[i], i)
                )[:6]
            elif len(corner_candidates) > 6:
                corner_candidates = sorted(
                    corner_candidates, key=lambda i: (-center_dist[i], i)
                )[:6]
            elif len(corner_candidates) == 0:
                pool = self.boundary or valid_indices
                corner_candidates = sorted(
                    pool, key=lambda i: (-center_dist[i], i)
                )[:6]

        corner_candidates = sorted(
            set(corner_candidates),
            key=lambda i: (math.atan2(ts[i] - ct, qs[i] - cq), i),
        )

        self.corner_indices = corner_candidates
        corner_bits = [0] * self.total
        for k, idx in enumerate(corner_candidates):
            corner_bits[idx] = 1 << k
        self.corner_bits = corner_bits

        edge_bits = [0] * self.total
        edge_cells = [[] for _ in range(6)]
        corner_set = set(corner_candidates)

        for idx in valid_indices:
            if idx in corner_set:
                continue
            flags = (
                qs[idx] == qmin, qs[idx] == qmax,
                ts[idx] == tmin, ts[idx] == tmax,
                ds[idx] == dmin, ds[idx] == dmax,
            )
            bit = 0
            for side, flag in enumerate(flags):
                if flag:
                    bit |= 1 << side
                    edge_cells[side].append(idx)
            edge_bits[idx] = bit

        self.edge_bits = edge_bits
        self.edge_cells = edge_cells
        self.corner_pairs = list(combinations(range(len(corner_candidates)), 2))
        self.edge_triples = list(combinations(range(6), 3))
        self.center_order = sorted(
            valid_indices,
            key=lambda i: (center_dist[i], -len(neighbors[i]), i),
        )


class DSU:
    __slots__ = ("parent", "rank", "corner", "edge")

    def __init__(self, n: int):
        self.parent = [-1] * n
        self.rank = [0] * n
        self.corner = [0] * n
        self.edge = [0] * n

    def find(self, x: int) -> int:
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(self, a: int, b: int) -> int:
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return ra
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.corner[ra] |= self.corner[rb]
        self.edge[ra] |= self.edge[rb]
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return ra


def _get_info(valid_mask) -> BoardInfo:
    H = len(valid_mask)
    W = len(valid_mask[0]) if H else 0
    flat = []
    for r in range(H):
        row = valid_mask[r]
        for c in range(W):
            flat.append(bool(row[c]))
    key = (H, W, tuple(flat))
    info = _CACHE.get(key)
    if info is None:
        info = BoardInfo(H, W, flat)
        if len(_CACHE) > 8:
            _CACHE.clear()
        _CACHE[key] = info
    return info


def _build_dsu(info: BoardInfo, occ) -> DSU:
    dsu = DSU(info.total)
    parent = dsu.parent
    for idx in info.valid_indices:
        if occ[idx]:
            parent[idx] = idx
            dsu.corner[idx] = info.corner_bits[idx]
            dsu.edge[idx] = info.edge_bits[idx]

    for idx in info.valid_indices:
        if occ[idx]:
            for nb in info.neighbors[idx]:
                if nb > idx and occ[nb]:
                    dsu.union(idx, nb)
    return dsu


def _merged_features(info: BoardInfo, move: int, occ, dsu: DSU):
    cbits = info.corner_bits[move]
    ebits = info.edge_bits[move]
    roots = []
    neigh = 0
    duplicate = False

    for nb in info.neighbors[move]:
        if occ[nb]:
            neigh += 1
            rt = dsu.find(nb)
            if rt in roots:
                duplicate = True
            else:
                roots.append(rt)
                cbits |= dsu.corner[rt]
                ebits |= dsu.edge[rt]

    return cbits, ebits, len(roots), neigh, duplicate


def _simple_cell_ring(info: BoardInfo, occ, move: int) -> bool:
    # Detect the common six-stones-around-one-cell ring, including if the
    # surrounded cell is already occupied by the same player.
    for center in info.neighbors[move]:
        ring = info.neighbors[center]
        if len(ring) != 6:
            continue
        ok = True
        for p in ring:
            if p != move and not occ[p]:
                ok = False
                break
        if ok:
            return True
    return False


def _creates_ring_by_flood(info: BoardInfo, occ, move: int) -> bool:
    # Treat current player's stones plus move as walls. If any non-player cell
    # cannot reach the board boundary, the move formed a ring.
    visited = [False] * info.total
    queue = []

    for s in info.boundary:
        if s != move and not occ[s] and not visited[s]:
            visited[s] = True
            queue.append(s)

    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        for v in info.neighbors[u]:
            if not visited[v] and v != move and not occ[v]:
                visited[v] = True
                queue.append(v)

    for idx in info.valid_indices:
        if idx != move and not occ[idx] and not visited[idx]:
            return True
    return False


def _move_wins_fast(info: BoardInfo, move: int, occ, dsu: DSU) -> bool:
    cbits, ebits, _roots, _neigh, duplicate = _merged_features(info, move, occ, dsu)

    # Bridge: connected component touches at least two corners.
    if _popcount(cbits) >= 2:
        return True

    # Fork: connected component touches at least three non-corner edges.
    if _popcount(ebits) >= 3:
        return True

    # Ring: adding a stone can only create a new cycle if it contacts the same
    # component through at least two neighboring stones.
    if duplicate:
        if _simple_cell_ring(info, occ, move):
            return True
        if _creates_ring_by_flood(info, occ, move):
            return True

    return False


def _bridge_fork_win(info: BoardInfo, move: int, occ, dsu: DSU) -> bool:
    cbits, ebits, _r, _n, _d = _merged_features(info, move, occ, dsu)
    return _popcount(cbits) >= 2 or _popcount(ebits) >= 3


def _dijkstra_multi(info: BoardInfo, sources, own_occ, block_occ):
    dist = [_INF] * info.total
    heap = []

    for s in sources:
        if 0 <= s < info.total and info.valid[s] and not block_occ[s]:
            c = 0 if own_occ[s] else 1
            if c < dist[s]:
                dist[s] = c
                heapq.heappush(heap, (c, s))

    while heap:
        d, u = heapq.heappop(heap)
        if d != dist[u]:
            continue
        for v in info.neighbors[u]:
            if block_occ[v]:
                continue
            nd = d + (0 if own_occ[v] else 1)
            if nd < dist[v]:
                dist[v] = nd
                heapq.heappush(heap, (nd, v))

    return dist


def _compute_maps(info: BoardInfo, own_occ, block_occ):
    corner_dists = [
        _dijkstra_multi(info, (corner,), own_occ, block_occ)
        for corner in info.corner_indices
    ]
    edge_dists = [
        _dijkstra_multi(info, info.edge_cells[side], own_occ, block_occ)
        for side in range(6)
    ]

    best_bridge = _INF
    for i, j in info.corner_pairs:
        target = info.corner_indices[j]
        val = corner_dists[i][target]
        if val < best_bridge:
            best_bridge = val

    best_fork = _INF
    for x in info.valid_indices:
        if block_occ[x]:
            continue
        cx = 0 if own_occ[x] else 1
        for a, b, c in info.edge_triples:
            da = edge_dists[a][x]
            db = edge_dists[b][x]
            dc = edge_dists[c][x]
            if da < _INF and db < _INF and dc < _INF:
                val = da + db + dc - 2 * cx
                if val < best_fork:
                    best_fork = val

    return corner_dists, edge_dists, min(best_bridge, best_fork)


def _bridge_need_at(info: BoardInfo, maps, move: int) -> int:
    corner_dists = maps[0]
    best = _INF
    for i, j in info.corner_pairs:
        a = corner_dists[i][move]
        b = corner_dists[j][move]
        if a < _INF and b < _INF:
            val = a + b - 2  # move is empty now; after playing it, remove its cost twice
            if val < best:
                best = val
    return 0 if best < 0 else best


def _fork_need_at(info: BoardInfo, maps, move: int) -> int:
    edge_dists = maps[1]
    best = _INF
    for a, b, c in info.edge_triples:
        da = edge_dists[a][move]
        db = edge_dists[b][move]
        dc = edge_dists[c][move]
        if da < _INF and db < _INF and dc < _INF:
            val = da + db + dc - 3  # candidate counted once in each branch
            if val < best:
                best = val
    return 0 if best < 0 else best


def _need_score(need: int, scale: float) -> float:
    if need >= _INF // 2:
        return 0.0
    n = max(0.0, float(need))
    s = scale / (n + 1.0)
    if n <= 1:
        s += 0.75 * scale
    elif n <= 2:
        s += 0.30 * scale
    elif n <= 3:
        s += 0.12 * scale
    return s


def _connection_score(cbits: int, ebits: int, roots: int, neigh: int, duplicate: bool) -> float:
    cc = _popcount(cbits)
    ec = _popcount(ebits)

    if cc >= 2 or ec >= 3:
        return 100000.0

    s = 0.0
    if cc == 1:
        s += 85.0
    if ec == 1:
        s += 35.0
    elif ec == 2:
        s += 260.0

    s += 28.0 * roots + 7.5 * neigh
    if roots >= 2:
        s += 55.0 * (roots - 1)
    if duplicate:
        s += 75.0 + 8.0 * neigh
    if cc == 1 and ec >= 1:
        s += 35.0

    return s


def _ring_shape_score(info: BoardInfo, move: int, own_occ, block_occ) -> float:
    # Score one-cell-ring templates around neighboring centers.
    score = 0.0
    for center in info.neighbors[move]:
        ring = info.neighbors[center]
        if len(ring) != 6:
            continue

        own_count = 1  # include the candidate move
        blockers = 0
        for p in ring:
            if p == move:
                continue
            if own_occ[p]:
                own_count += 1
            elif block_occ[p]:
                blockers += 1

        if blockers == 0:
            if own_count >= 6:
                score += 100000.0
            elif own_count == 5:
                score += 480.0
            elif own_count == 4:
                score += 150.0
            elif own_count == 3:
                score += 45.0
        elif blockers == 1 and own_count >= 4:
            score += 24.0

    return score


def _score_move(
    info: BoardInfo,
    move: int,
    my_occ,
    opp_occ,
    my_dsu: DSU,
    opp_dsu: DSU,
    my_maps,
    opp_maps,
    phase: int,
    defense_weight: float,
):
    my_cb, my_eb, my_roots, my_neigh, my_dup = _merged_features(info, move, my_occ, my_dsu)
    op_cb, op_eb, op_roots, op_neigh, op_dup = _merged_features(info, move, opp_occ, opp_dsu)

    attack_conn = _connection_score(my_cb, my_eb, my_roots, my_neigh, my_dup)
    defend_conn = _connection_score(op_cb, op_eb, op_roots, op_neigh, op_dup)

    my_bridge = _bridge_need_at(info, my_maps, move)
    my_fork = _fork_need_at(info, my_maps, move)
    op_bridge = _bridge_need_at(info, opp_maps, move)
    op_fork = _fork_need_at(info, opp_maps, move)

    attack_path = _need_score(my_bridge, 360.0) + _need_score(my_fork, 430.0)
    defend_path = _need_score(op_bridge, 330.0) + _need_score(op_fork, 400.0)

    attack_ring = _ring_shape_score(info, move, my_occ, opp_occ)
    defend_ring = _ring_shape_score(info, move, opp_occ, my_occ)

    empty_neigh = 0
    for nb in info.neighbors[move]:
        if not my_occ[nb] and not opp_occ[nb]:
            empty_neigh += 1

    center_weight = max(0.55, 3.0 - 0.025 * float(phase))
    center_score = center_weight * (16.0 - 2.8 * info.center_dist[move])

    local = (
        7.5 * my_neigh
        + 4.0 * op_neigh
        + 1.5 * empty_neigh
        + 1.0 * len(info.neighbors[move])
    )

    if phase > 5 and my_neigh + op_neigh == 0:
        local -= min(70.0, 14.0 + 1.4 * phase)
    if phase > 12 and my_neigh == 0:
        local -= 5.0

    score = (
        attack_conn
        + attack_path
        + attack_ring
        + center_score
        + local
        + defense_weight * (0.85 * defend_conn + defend_path + defend_ring)
    )

    danger = defend_conn + defend_path + defend_ring + 3.0 * op_neigh

    # Deterministic tiny tie-breaker.
    score += ((move * 2654435761) & 1023) * 0.0001
    return score, danger


def _quick_score(info: BoardInfo, move: int, my_occ, opp_occ, my_dsu: DSU, opp_dsu: DSU, phase: int) -> float:
    my_cb, my_eb, my_roots, my_neigh, my_dup = _merged_features(info, move, my_occ, my_dsu)
    op_cb, op_eb, op_roots, op_neigh, op_dup = _merged_features(info, move, opp_occ, opp_dsu)

    return (
        1.15 * _connection_score(my_cb, my_eb, my_roots, my_neigh, my_dup)
        + 0.95 * _connection_score(op_cb, op_eb, op_roots, op_neigh, op_dup)
        + _ring_shape_score(info, move, my_occ, opp_occ)
        + 0.85 * _ring_shape_score(info, move, opp_occ, my_occ)
        + (14.0 - 2.0 * info.center_dist[move])
        + 4.0 * my_neigh
        + 2.5 * op_neigh
        + ((move * 1103515245 + phase) & 255) * 0.0001
    )


def _count_winning_replies_after(info: BoardInfo, occ, first_move: int, legal, limit: int = 3) -> int:
    if occ[first_move]:
        return 0

    occ[first_move] = True
    try:
        dsu = _build_dsu(info, occ)
        count = 0
        for m in legal:
            if m == first_move or occ[m]:
                continue
            if _move_wins_fast(info, m, occ, dsu):
                count += 1
                if count >= limit:
                    break
        return count
    finally:
        occ[first_move] = False


def _policy(me, opp, valid_mask):
    start = time.perf_counter()
    info = _get_info(valid_mask)

    my_occ = [False] * info.total
    opp_occ = [False] * info.total
    my_count = 0
    opp_count = 0

    for p in me:
        try:
            r, c = int(p[0]), int(p[1])
        except Exception:
            continue
        if 0 <= r < info.H and 0 <= c < info.W:
            idx = r * info.W + c
            if info.valid[idx] and not my_occ[idx]:
                my_occ[idx] = True
                my_count += 1

    for p in opp:
        try:
            r, c = int(p[0]), int(p[1])
        except Exception:
            continue
        if 0 <= r < info.H and 0 <= c < info.W:
            idx = r * info.W + c
            if info.valid[idx] and not opp_occ[idx]:
                opp_occ[idx] = True
                opp_count += 1

    legal = [idx for idx in info.valid_indices if not my_occ[idx] and not opp_occ[idx]]
    if not legal:
        return (0, 0)

    phase = my_count + opp_count

    # Strong opening: take the most central legal cell.
    if phase <= 1:
        for idx in info.center_order:
            if not my_occ[idx] and not opp_occ[idx]:
                return (idx // info.W, idx % info.W)

    my_dsu = _build_dsu(info, my_occ)
    opp_dsu = _build_dsu(info, opp_occ)

    # 1. Immediate win.
    my_wins = [m for m in legal if _move_wins_fast(info, m, my_occ, my_dsu)]
    if my_wins:
        best = max(
            my_wins,
            key=lambda m: (
                1 if _bridge_fork_win(info, m, my_occ, my_dsu) else 0,
                _quick_score(info, m, my_occ, opp_occ, my_dsu, opp_dsu, phase),
            ),
        )
        return (best // info.W, best % info.W)

    # 2. Immediate block.
    opp_wins = [m for m in legal if _move_wins_fast(info, m, opp_occ, opp_dsu)]
    if opp_wins:
        if len(opp_wins) == 1:
            best = opp_wins[0]
        else:
            best = max(
                opp_wins,
                key=lambda m: (
                    1 if _bridge_fork_win(info, m, opp_occ, opp_dsu) else 0,
                    _quick_score(info, m, my_occ, opp_occ, my_dsu, opp_dsu, phase),
                ),
            )
        return (best // info.W, best % info.W)

    # 3. Positional scoring.
    my_maps = _compute_maps(info, my_occ, opp_occ)
    opp_maps = _compute_maps(info, opp_occ, my_occ)

    my_dist = my_maps[2]
    opp_dist = opp_maps[2]
    defense_weight = 0.82
    if my_dist < _INF // 2 and opp_dist < _INF // 2:
        if opp_dist + 1 < my_dist:
            defense_weight += 0.25
        if my_dist + 1 < opp_dist:
            defense_weight -= 0.08
    if opp_dist <= 3:
        defense_weight += 0.18
    if my_dist <= 2:
        defense_weight -= 0.08
    if opp_count > my_count:
        defense_weight += 0.04
    defense_weight = max(0.65, min(1.25, defense_weight))

    scores = []
    score_by = {}
    danger_by = {}

    for m in legal:
        s, danger = _score_move(
            info, m,
            my_occ, opp_occ,
            my_dsu, opp_dsu,
            my_maps, opp_maps,
            phase, defense_weight,
        )
        scores.append((s, m))
        score_by[m] = s
        danger_by[m] = danger

    scores.sort(reverse=True)
    adjusted = dict(score_by)

    # 4. Exact double-threat creation for our best-looking moves.
    if my_count >= 4:
        lim = 32 if len(legal) <= 120 else 24
        for _s, m in scores[:lim]:
            if time.perf_counter() - start > 0.70:
                break
            cnt = _count_winning_replies_after(info, my_occ, m, legal, limit=3)
            if cnt >= 2:
                adjusted[m] += 65000.0 + 2500.0 * cnt
            elif cnt == 1:
                adjusted[m] += 1050.0

    # 5. Exact opponent double-threat prevention for dangerous cells.
    if opp_count >= 4:
        danger_sorted = sorted(((danger_by[m], m) for m in legal), reverse=True)
        lim = 32 if len(legal) <= 120 else 24
        for _d, m in danger_sorted[:lim]:
            if time.perf_counter() - start > 0.88:
                break
            cnt = _count_winning_replies_after(info, opp_occ, m, legal, limit=3)
            if cnt >= 2:
                adjusted[m] += 54000.0 + 2000.0 * cnt
            elif cnt == 1:
                adjusted[m] += 850.0

    best = max(legal, key=lambda m: adjusted.get(m, score_by[m]))
    return (best // info.W, best % info.W)


def _occupied_coord_set(me, opp):
    occupied = set()
    for seq in (me, opp):
        for p in seq:
            try:
                occupied.add((int(p[0]), int(p[1])))
            except Exception:
                pass
    return occupied


def _fallback_move(me, opp, valid_mask) -> tuple[int, int]:
    try:
        H = len(valid_mask)
        W = len(valid_mask[0]) if H else 0
        occupied = _occupied_coord_set(me, opp)
        cr = (H - 1) / 2.0
        cc = (W - 1) / 2.0

        best = None
        bestd = 10**18
        for r in range(H):
            row = valid_mask[r]
            for c in range(W):
                if bool(row[c]) and (r, c) not in occupied:
                    d = (r - cr) * (r - cr) + (c - cc) * (c - cc)
                    if d < bestd:
                        bestd = d
                        best = (r, c)
        if best is not None:
            return best
    except Exception:
        pass
    return (0, 0)


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        move = _policy(me, opp, valid_mask)
        r, c = int(move[0]), int(move[1])

        H = len(valid_mask)
        W = len(valid_mask[0]) if H else 0
        occupied = _occupied_coord_set(me, opp)

        if 0 <= r < H and 0 <= c < W and bool(valid_mask[r][c]) and (r, c) not in occupied:
            return (r, c)
    except Exception:
        pass

    return _fallback_move(me, opp, valid_mask)
