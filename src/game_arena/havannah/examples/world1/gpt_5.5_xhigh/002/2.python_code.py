
from __future__ import annotations

import math
import heapq
import time
from collections import deque

_INF = 10 ** 8
_SQRT3_OVER_2 = 0.8660254037844386
_INFO_CACHE = {}


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Havannah policy for a 15x15 odd-q offset hex board.

    Always returns a legal empty playable (row, col) if one exists.
    """
    try:
        mv = _policy_impl(me, opp, valid_mask)
        if _is_legal_move(mv, me, opp, valid_mask):
            return (int(mv[0]), int(mv[1]))
    except Exception:
        pass
    return _fallback_move(me, opp, valid_mask)


def _policy_impl(me, opp, valid_mask):
    start_time = time.perf_counter()
    deadline = start_time + 0.86

    info = _get_info(valid_mask)
    if info.M <= 0:
        return _fallback_move(me, opp, valid_mask)

    state = _make_state(info, me, opp)
    empties = [i for i, s in enumerate(state) if s == 0]
    if not empties:
        return _fallback_move(me, opp, valid_mask)

    my_count = sum(1 for s in state if s == 1)
    opp_count = sum(1 for s in state if s == 2)
    phase = my_count + opp_count

    # Strong, flexible opening: take the centre, or play adjacent to it.
    if my_count == 0 and opp_count <= 1:
        idx = _choose_opening(info, state, empties)
        return info.cells[idx]

    my_comp = _build_components(info, state, 1)
    my_wins = _winning_moves_from_components(info, state, 1, my_comp)
    if my_wins:
        best = max(my_wins, key=lambda i: _quick_win_score(i, info, state, 1, my_comp))
        return info.cells[best]

    opp_comp = _build_components(info, state, 2)
    opp_wins = _winning_moves_from_components(info, state, 2, opp_comp)
    if opp_wins:
        if len(opp_wins) == 1:
            return info.cells[opp_wins[0]]
        best = max(opp_wins, key=lambda i: _quick_block_score(i, info, state, my_comp, opp_comp))
        return info.cells[best]

    fields_me = _compute_connection_fields(info, state, 1)
    fields_opp = _compute_connection_fields(info, state, 2)

    scores = {}
    for idx in empties:
        scores[idx] = _evaluate_move(
            idx, info, state,
            my_comp, opp_comp,
            fields_me, fields_opp,
            my_count, opp_count, phase,
        )

    # Limited forward check: prefer moves that create multiple immediate wins next turn.
    if len(empties) > 1 and time.perf_counter() < deadline:
        if len(empties) > 100:
            top_k = 16
        elif len(empties) > 60:
            top_k = 22
        else:
            top_k = min(32, len(empties))

        top = sorted(empties, key=lambda i: scores[i], reverse=True)[:top_k]
        for idx in top:
            if time.perf_counter() > deadline:
                break

            state[idx] = 1
            try:
                future_my = _winning_moves(info, state, 1, limit=3)
                t = len(future_my)
                if t >= 2:
                    scores[idx] += 300000.0 + 50000.0 * t
                elif t == 1:
                    scores[idx] += 4500.0

                # Normally our stone cannot create opponent wins, but this protects
                # against unusual masks and tactical detection edge cases.
                if time.perf_counter() < deadline:
                    future_opp = _winning_moves(info, state, 2, limit=2)
                    ot = len(future_opp)
                    if ot:
                        scores[idx] -= 240000.0 * ot
            finally:
                state[idx] = 0

    best = max(
        empties,
        key=lambda i: (
            scores.get(i, -1e100),
            info.center_weight[i],
            -info.cells[i][0],
            -info.cells[i][1],
        ),
    )
    return info.cells[best]


class _BoardInfo:
    __slots__ = (
        "h", "w", "valid", "cells", "index", "M", "neigh",
        "boundary", "corner_bit", "edge_bit", "corner_cells", "edge_cells",
        "xy", "boundary_dist", "center_idx", "center_weight",
    )

    def __init__(self, valid):
        self.valid = valid
        self.h = len(valid)
        self.w = len(valid[0]) if self.h else 0

        self.cells = []
        self.index = [[-1 for _ in range(self.w)] for _ in range(self.h)]
        for r in range(self.h):
            for c in range(self.w):
                if valid[r][c]:
                    self.index[r][c] = len(self.cells)
                    self.cells.append((r, c))

        self.M = len(self.cells)
        self.neigh = [[] for _ in range(self.M)]

        for idx, (r, c) in enumerate(self.cells):
            if c & 1:
                offsets = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]
            else:
                offsets = [(-1, 0), (1, 0), (0, -1), (1, -1), (0, 1), (1, 1)]

            ns = []
            for dr, dc in offsets:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.h and 0 <= nc < self.w:
                    j = self.index[nr][nc]
                    if j >= 0:
                        ns.append(j)
            self.neigh[idx] = ns

        self.xy = [
            (c * _SQRT3_OVER_2, r - 0.5 * (c & 1))
            for r, c in self.cells
        ]

        self.boundary = [i for i in range(self.M) if len(self.neigh[i]) < 6]
        if self.M and not self.boundary:
            self.boundary = list(range(self.M))

        self.corner_bit = [0] * self.M
        self.edge_bit = [0] * self.M
        self.corner_cells = []
        self.edge_cells = [[] for _ in range(6)]

        self._assign_corners_and_edges()
        self._compute_center_data()

    def _assign_corners_and_edges(self):
        if self.M == 0:
            return

        boundary = self.boundary
        order = self._trace_boundary(boundary)

        if order:
            min_deg = min(len(self.neigh[i]) for i in boundary)
            candidate_lists = [
                [i for i in boundary if len(self.neigh[i]) <= 3],
                [i for i in boundary if len(self.neigh[i]) == min_deg],
            ]

            for cand in candidate_lists:
                if len(cand) == 6:
                    cset = set(cand)
                    positions = [(p, i) for p, i in enumerate(order) if i in cset]
                    if len(positions) == 6:
                        self._assign_from_boundary_order(order, positions)
                        return

        self._assign_fallback_sides(boundary)

    def _trace_boundary(self, boundary):
        if not boundary:
            return None
        if len(boundary) == 1:
            return [boundary[0]]

        bset = set(boundary)
        bneigh = {i: [j for j in self.neigh[i] if j in bset] for i in boundary}
        start = min(boundary, key=lambda i: (len(self.neigh[i]), self.cells[i]))

        for first in bneigh.get(start, []):
            order = [start]
            seen = {start}
            prev, cur = start, first
            ok = True

            while cur != start:
                if cur in seen:
                    ok = False
                    break
                order.append(cur)
                seen.add(cur)
                if len(order) > len(boundary) + 1:
                    ok = False
                    break

                ns = [n for n in bneigh.get(cur, []) if n != prev]
                if not ns:
                    ok = False
                    break

                if start in ns and len(seen) == len(boundary):
                    nxt = start
                else:
                    unvisited = [n for n in ns if n not in seen]
                    if unvisited:
                        nxt = unvisited[0]
                    else:
                        nxt = ns[0]

                prev, cur = cur, nxt

            if ok and cur == start and len(seen) == len(boundary):
                return order

        return None

    def _assign_from_boundary_order(self, order, positions):
        positions.sort()
        self.corner_cells = [idx for _, idx in positions]

        for bit, idx in enumerate(self.corner_cells):
            self.corner_bit[idx] = 1 << bit

        L = len(order)
        for bit in range(6):
            p1 = positions[bit][0]
            p2 = positions[(bit + 1) % 6][0]
            k = (p1 + 1) % L
            while k != p2:
                cell = order[k]
                self.edge_bit[cell] |= 1 << bit
                self.edge_cells[bit].append(cell)
                k = (k + 1) % L

    def _assign_fallback_sides(self, boundary):
        if not boundary:
            return

        cx = sum(x for x, _ in self.xy) / max(1, self.M)
        cy = sum(y for _, y in self.xy) / max(1, self.M)

        def ang(i):
            x, y = self.xy[i]
            a = math.atan2(y - cy, x - cx)
            if a < 0:
                a += 2 * math.pi
            return a

        def rad2(i):
            x, y = self.xy[i]
            return (x - cx) * (x - cx) + (y - cy) * (y - cy)

        deg3 = [i for i in boundary if len(self.neigh[i]) <= 3]
        if len(deg3) == 6:
            selected = deg3[:]
        else:
            first = max(boundary, key=rad2)
            a0 = ang(first)
            selected = []
            for k in range(6):
                target = (a0 + k * math.pi / 3.0) % (2 * math.pi)
                best = None
                best_score = -1e100
                for i in boundary:
                    if i in selected:
                        continue
                    d = abs((ang(i) - target + math.pi) % (2 * math.pi) - math.pi)
                    score = -1000.0 * d + 0.001 * rad2(i) - len(self.neigh[i])
                    if score > best_score:
                        best_score = score
                        best = i
                if best is not None:
                    selected.append(best)

            for i in sorted(boundary, key=rad2, reverse=True):
                if len(selected) >= 6:
                    break
                if i not in selected:
                    selected.append(i)

        selected = sorted(selected[:6], key=ang)
        self.corner_cells = selected

        for bit, idx in enumerate(selected):
            self.corner_bit[idx] = 1 << bit

        if len(selected) < 2:
            return

        cset = set(selected)
        cangs = [ang(i) for i in selected]

        for i in boundary:
            if i in cset:
                continue
            a = ang(i)
            side = 0
            for e in range(len(cangs)):
                a1 = cangs[e]
                a2 = cangs[(e + 1) % len(cangs)]
                if e == len(cangs) - 1:
                    inside = (a >= a1 or a < a2)
                else:
                    inside = (a1 <= a < a2)
                if inside:
                    side = e
                    break
            if side < 6:
                self.edge_bit[i] |= 1 << side
                self.edge_cells[side].append(i)

    def _compute_center_data(self):
        if self.M == 0:
            self.boundary_dist = []
            self.center_idx = -1
            self.center_weight = []
            return

        dist = [_INF] * self.M
        q = deque()
        for b in self.boundary:
            dist[b] = 0
            q.append(b)

        while q:
            v = q.popleft()
            nd = dist[v] + 1
            for nb in self.neigh[v]:
                if dist[nb] > nd:
                    dist[nb] = nd
                    q.append(nb)

        self.boundary_dist = dist
        max_bd = max(d for d in dist if d < _INF)
        if max_bd <= 0:
            max_bd = 1

        cx = sum(x for x, _ in self.xy) / self.M
        cy = sum(y for _, y in self.xy) / self.M
        r2s = []
        for x, y in self.xy:
            r2s.append((x - cx) * (x - cx) + (y - cy) * (y - cy))
        max_r2 = max(r2s) if r2s else 1.0
        if max_r2 <= 0:
            max_r2 = 1.0

        self.center_weight = []
        for i in range(self.M):
            bd_part = max(0.0, min(1.0, dist[i] / max_bd))
            radial_part = max(0.0, 1.0 - r2s[i] / max_r2)
            self.center_weight.append(0.80 * bd_part + 0.20 * radial_part)

        cr = sum(r for r, _ in self.cells) / self.M
        cc = sum(c for _, c in self.cells) / self.M

        self.center_idx = max(
            range(self.M),
            key=lambda i: (
                dist[i],
                self.center_weight[i],
                -((self.cells[i][0] - cr) ** 2 + (self.cells[i][1] - cc) ** 2),
            ),
        )


class _DSU:
    __slots__ = ("p", "sz")

    def __init__(self, n):
        self.p = list(range(n))
        self.sz = [1] * n

    def find(self, x):
        p = self.p
        while p[x] != x:
            p[x] = p[p[x]]
            x = p[x]
        return x

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return ra
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        self.sz[ra] += self.sz[rb]
        return ra


def _get_info(valid_mask):
    h = len(valid_mask)
    w = len(valid_mask[0]) if h else 0

    rows = []
    flat = []
    for r in range(h):
        row = []
        for c in range(w):
            try:
                v = bool(valid_mask[r][c])
            except Exception:
                v = False
            row.append(v)
            flat.append(v)
        rows.append(row)

    key = (h, w, tuple(flat))
    info = _INFO_CACHE.get(key)
    if info is None:
        if len(_INFO_CACHE) > 4:
            _INFO_CACHE.clear()
        info = _BoardInfo(rows)
        _INFO_CACHE[key] = info
    return info


def _make_state(info, me, opp):
    state = [0] * info.M

    for p in me:
        idx = _point_to_index(info, p)
        if idx >= 0:
            state[idx] = 1

    for p in opp:
        idx = _point_to_index(info, p)
        if idx >= 0 and state[idx] == 0:
            state[idx] = 2

    return state


def _point_to_index(info, p):
    try:
        r, c = int(p[0]), int(p[1])
    except Exception:
        return -1
    if 0 <= r < info.h and 0 <= c < info.w:
        return info.index[r][c]
    return -1


def _choose_opening(info, state, empties):
    c = info.center_idx
    if c >= 0 and state[c] == 0:
        return c

    center_neighbors = set(info.neigh[c]) if c >= 0 else set()
    best = empties[0]
    best_score = -1e100

    for idx in empties:
        opp_adj = sum(1 for nb in info.neigh[idx] if state[nb] == 2)
        emp_adj = sum(1 for nb in info.neigh[idx] if state[nb] == 0)
        score = (
            120.0 * info.center_weight[idx]
            + (30.0 if idx in center_neighbors else 0.0)
            + 8.0 * opp_adj
            + 2.0 * emp_adj
            + _noise(idx)
        )
        if score > best_score:
            best_score = score
            best = idx

    return best


def _build_components(info, state, player):
    dsu = _DSU(info.M)

    for i in range(info.M):
        if state[i] != player:
            continue
        for j in info.neigh[i]:
            if j > i and state[j] == player:
                dsu.union(i, j)

    comp_corner = [0] * info.M
    comp_edge = [0] * info.M
    comp_size = [0] * info.M

    for i in range(info.M):
        if state[i] == player:
            r = dsu.find(i)
            comp_size[r] += 1
            comp_corner[r] |= info.corner_bit[i]
            comp_edge[r] |= info.edge_bit[i]

    return dsu, comp_corner, comp_edge, comp_size


def _merged_info(idx, player, state, info, dsu, comp_corner, comp_edge, comp_size):
    cm = info.corner_bit[idx]
    em = info.edge_bit[idx]
    sz = 1
    roots = []

    for nb in info.neigh[idx]:
        if state[nb] == player:
            r = dsu.find(nb)
            if r not in roots:
                roots.append(r)
                cm |= comp_corner[r]
                em |= comp_edge[r]
                sz += comp_size[r]

    return cm, em, sz, roots


def _winning_moves(info, state, player, limit=None):
    comp = _build_components(info, state, player)
    return _winning_moves_from_components(info, state, player, comp, limit=limit)


def _winning_moves_from_components(info, state, player, comp, limit=None):
    dsu, comp_corner, comp_edge, comp_size = comp
    out = []

    for idx in range(info.M):
        if state[idx] != 0:
            continue
        if _is_winning_move(idx, player, state, info, dsu, comp_corner, comp_edge, comp_size):
            out.append(idx)
            if limit is not None and len(out) >= limit:
                break

    return out


def _is_winning_move(idx, player, state, info, dsu, comp_corner, comp_edge, comp_size):
    cm, em, _, _ = _merged_info(idx, player, state, info, dsu, comp_corner, comp_edge, comp_size)

    # Bridge: connected component touches at least two corners.
    if _bit_count(cm) >= 2:
        return True

    # Fork: connected component touches at least three non-corner edges.
    if _bit_count(em) >= 3:
        return True

    # Ring.
    own_adj = 0
    for nb in info.neigh[idx]:
        if state[nb] == player:
            own_adj += 1
            if own_adj >= 2:
                return _ring_after_move(info, state, idx, player)

    return False


def _ring_after_move(info, state, idx, player):
    owned_neighbors = [nb for nb in info.neigh[idx] if state[nb] == player]
    if len(owned_neighbors) < 2:
        return False

    # Flood fill through all non-player cells from the board boundary.
    # Any non-player cell not reached is enclosed by player stones.
    visited = [False] * info.M
    q = deque()

    for b in info.boundary:
        if b != idx and state[b] != player:
            visited[b] = True
            q.append(b)

    while q:
        v = q.popleft()
        for nb in info.neigh[v]:
            if not visited[nb] and nb != idx and state[nb] != player:
                visited[nb] = True
                q.append(nb)

    for i in range(info.M):
        if i != idx and state[i] != player and not visited[i]:
            return True

    # If the only enclosed cells are also player stones, flood-fill cannot see them.
    # Detect a real geometric cycle around at least one valid cell centre.
    return _cycle_encloses_valid_cell(info, state, idx, player, owned_neighbors)


def _cycle_encloses_valid_cell(info, state, idx, player, owned_neighbors):
    if len(owned_neighbors) < 2:
        return False

    nset = set(owned_neighbors)
    n = len(owned_neighbors)

    for ai in range(n):
        a = owned_neighbors[ai]
        for bi in range(ai + 1, n):
            b = owned_neighbors[bi]
            forbidden = set(nset)
            forbidden.discard(a)
            forbidden.discard(b)

            path = _bfs_player_path(info, state, player, a, b, forbidden, idx)
            # path vertices include a and b.  A true Havannah ring needs cycle length >= 6,
            # so the path between two neighbours of the new stone needs at least 4 edges.
            if path is not None and len(path) >= 5:
                cycle = [idx] + path
                if _cycle_has_inside_cell(info, cycle):
                    return True

    return False


def _bfs_player_path(info, state, player, start, goal, forbidden, move_idx):
    prev = [-2] * info.M
    prev[start] = -1
    q = deque([start])

    while q:
        v = q.popleft()
        if v == goal:
            break
        for nb in info.neigh[v]:
            if nb == move_idx or nb in forbidden or prev[nb] != -2:
                continue
            if state[nb] != player:
                continue
            prev[nb] = v
            q.append(nb)

    if prev[goal] == -2:
        return None

    path = []
    cur = goal
    while cur != -1:
        path.append(cur)
        cur = prev[cur]
    path.reverse()
    return path


def _cycle_has_inside_cell(info, cycle):
    if len(cycle) < 6:
        return False

    cset = set(cycle)
    poly = [info.xy[i] for i in cycle]

    minx = min(x for x, _ in poly)
    maxx = max(x for x, _ in poly)
    miny = min(y for _, y in poly)
    maxy = max(y for _, y in poly)

    eps = 1e-9
    for i, (x, y) in enumerate(info.xy):
        if i in cset:
            continue
        if x < minx - eps or x > maxx + eps or y < miny - eps or y > maxy + eps:
            continue
        if _point_in_poly(x, y, poly):
            return True

    return False


def _point_in_poly(x, y, poly):
    inside = False
    j = len(poly) - 1

    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]

        if (yi > y) != (yj > y):
            x_intersect = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_intersect:
                inside = not inside

        j = i

    return inside


def _compute_connection_fields(info, state, player):
    cost = [_INF] * info.M
    for i, s in enumerate(state):
        if s == player:
            cost[i] = 0
        elif s == 0:
            cost[i] = 1

    edge_fields = []
    for e in range(6):
        edge_fields.append(_dijkstra_node_cost(info, cost, info.edge_cells[e]))

    corner_fields = []
    for k in range(6):
        if k < len(info.corner_cells):
            corner_fields.append(_dijkstra_node_cost(info, cost, [info.corner_cells[k]]))
        else:
            corner_fields.append([_INF] * info.M)

    return edge_fields, corner_fields


def _dijkstra_node_cost(info, cost, sources):
    dist = [_INF] * info.M
    heap = []

    for s in sources:
        if 0 <= s < info.M and cost[s] < _INF:
            if cost[s] < dist[s]:
                dist[s] = cost[s]
                heapq.heappush(heap, (dist[s], s))

    while heap:
        d, v = heapq.heappop(heap)
        if d != dist[v]:
            continue
        for nb in info.neigh[v]:
            nd = d + cost[nb]
            if nd < dist[nb]:
                dist[nb] = nd
                heapq.heappush(heap, (nd, nb))

    return dist


def _connection_value(idx, edge_fields, corner_fields):
    val = 0.0

    ed = []
    for f in edge_fields:
        d = f[idx]
        if d < _INF // 2:
            v = d - 1
            if v < 0:
                v = 0
            ed.append(v)

    ed.sort()
    if len(ed) >= 3:
        s3 = ed[0] + ed[1] + ed[2]
        val += 950.0 / (s3 + 1.0)
        val += 120.0 / (ed[2] + 1.0)
        if s3 <= 2:
            val += (3 - s3) * 180.0

    cd = []
    for f in corner_fields:
        d = f[idx]
        if d < _INF // 2:
            v = d - 1
            if v < 0:
                v = 0
            cd.append(v)

    cd.sort()
    if len(cd) >= 2:
        s2 = cd[0] + cd[1]
        val += 700.0 / (s2 + 1.0)
        val += 100.0 / (cd[1] + 1.0)
        if s2 <= 1:
            val += (2 - s2) * 200.0

    return val


def _evaluate_move(idx, info, state, my_comp, opp_comp, fields_me, fields_opp,
                   my_count, opp_count, phase):
    my_dsu, my_cc, my_ee, my_ss = my_comp
    op_dsu, op_cc, op_ee, op_ss = opp_comp

    if phase < 10:
        center_factor = 95.0
    elif phase < 45:
        center_factor = 55.0
    else:
        center_factor = 25.0

    score = center_factor * info.center_weight[idx]

    own_adj = 0
    opp_adj = 0
    empty_adj = 0
    own_neighbor_roots = []
    opp_neighbor_roots = []

    for nb in info.neigh[idx]:
        s = state[nb]
        if s == 1:
            own_adj += 1
            own_neighbor_roots.append(my_dsu.find(nb))
        elif s == 2:
            opp_adj += 1
            opp_neighbor_roots.append(op_dsu.find(nb))
        else:
            empty_adj += 1

    cm, em, msize, roots = _merged_info(idx, 1, state, info, my_dsu, my_cc, my_ee, my_ss)

    score += own_adj * 34.0 + own_adj * own_adj * 7.0
    score += empty_adj * 3.0
    score += min(msize, 30) * 6.0 + max(0, msize - 30) * 2.0
    score += max(0, len(roots) - 1) * 85.0

    if my_count > 0 and own_adj == 0:
        score -= 30.0 if phase < 50 else 15.0

    edge_n = _bit_count(em)
    corner_n = _bit_count(cm)

    if edge_n == 1:
        score += 70.0
    elif edge_n == 2:
        score += 520.0

    if corner_n == 1:
        score += 170.0

    if my_count < 3:
        if info.corner_bit[idx]:
            score -= 55.0
        elif info.edge_bit[idx]:
            score -= 18.0

    if own_adj >= 2 and len(set(own_neighbor_roots)) < len(own_neighbor_roots):
        score += 130.0
    if own_adj >= 3:
        score += 80.0

    score += min(_local_liberties(idx, 1, state, info), 14) * 4.0

    # Defensive value: occupy cells the opponent wants.
    ocm, oem, osize, oroots = _merged_info(idx, 2, state, info, op_dsu, op_cc, op_ee, op_ss)
    oe = _bit_count(oem)
    oc = _bit_count(ocm)

    score += opp_adj * 18.0 + opp_adj * opp_adj * 6.0
    score += min(osize, 30) * 3.8
    score += max(0, len(oroots) - 1) * 65.0

    if oe == 1:
        score += 45.0
    elif oe == 2:
        score += 480.0

    if oc == 1:
        score += 150.0

    if opp_adj >= 2 and len(set(opp_neighbor_roots)) < len(opp_neighbor_roots):
        score += 120.0

    me_edges, me_corners = fields_me
    op_edges, op_corners = fields_opp
    score += 1.05 * _connection_value(idx, me_edges, me_corners)
    score += 0.72 * _connection_value(idx, op_edges, op_corners)

    score += _noise(idx)
    return score


def _local_liberties(idx, player, state, info):
    libs = set()

    for nb in info.neigh[idx]:
        if state[nb] == 0:
            libs.add(nb)

    for nb in info.neigh[idx]:
        if state[nb] == player:
            for nn in info.neigh[nb]:
                if nn != idx and state[nn] == 0:
                    libs.add(nn)

    return len(libs)


def _quick_win_score(idx, info, state, player, comp):
    dsu, cc, ee, ss = comp
    cm, em, size, roots = _merged_info(idx, player, state, info, dsu, cc, ee, ss)
    adj = sum(1 for nb in info.neigh[idx] if state[nb] == player)

    return (
        10000.0 * _bit_count(cm)
        + 7000.0 * _bit_count(em)
        + 40.0 * size
        + 25.0 * adj
        + 50.0 * len(roots)
        + info.center_weight[idx]
        + _noise(idx)
    )


def _quick_block_score(idx, info, state, my_comp, opp_comp):
    my_dsu, my_cc, my_ee, my_ss = my_comp
    op_dsu, op_cc, op_ee, op_ss = opp_comp

    mcm, mem, msize, mroots = _merged_info(idx, 1, state, info, my_dsu, my_cc, my_ee, my_ss)
    ocm, oem, osize, oroots = _merged_info(idx, 2, state, info, op_dsu, op_cc, op_ee, op_ss)

    own_adj = sum(1 for nb in info.neigh[idx] if state[nb] == 1)
    opp_adj = sum(1 for nb in info.neigh[idx] if state[nb] == 2)

    return (
        30.0 * info.center_weight[idx]
        + 16.0 * own_adj
        + 28.0 * opp_adj
        + 8.0 * msize
        + 12.0 * osize
        + 80.0 * len(mroots)
        + 110.0 * len(oroots)
        + 260.0 * _bit_count(oem)
        + 320.0 * _bit_count(ocm)
        + 120.0 * _bit_count(mem)
        + 130.0 * _bit_count(mcm)
        + _noise(idx)
    )


def _bit_count(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")


def _noise(idx):
    return ((((idx + 1) * 2654435761) & 0xFFFF) / 65535.0) * 0.01


def _is_legal_move(mv, me, opp, valid_mask):
    try:
        r, c = int(mv[0]), int(mv[1])
        if r < 0 or c < 0:
            return False
        if r >= len(valid_mask) or c >= len(valid_mask[0]):
            return False
        if not bool(valid_mask[r][c]):
            return False
    except Exception:
        return False

    occ = set()
    for p in me:
        try:
            occ.add((int(p[0]), int(p[1])))
        except Exception:
            pass
    for p in opp:
        try:
            occ.add((int(p[0]), int(p[1])))
        except Exception:
            pass

    return (r, c) not in occ


def _fallback_move(me, opp, valid_mask):
    occ = set()
    for p in me:
        try:
            occ.add((int(p[0]), int(p[1])))
        except Exception:
            pass
    for p in opp:
        try:
            occ.add((int(p[0]), int(p[1])))
        except Exception:
            pass

    try:
        h = len(valid_mask)
        w = len(valid_mask[0]) if h else 0
    except Exception:
        return (0, 0)

    legal = []
    for r in range(h):
        for c in range(w):
            try:
                if bool(valid_mask[r][c]) and (r, c) not in occ:
                    legal.append((r, c))
            except Exception:
                pass

    if not legal:
        return (0, 0)

    cr = (h - 1) / 2.0
    cc = (w - 1) / 2.0
    return min(legal, key=lambda p: ((p[0] - cr) ** 2 + (p[1] - cc) ** 2, p[0], p[1]))
