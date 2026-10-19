
from collections import deque

# Hex-neighbor order arranged cyclically around a cell.
DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1)]
INF = 10**9

_GEOM = None


class Geometry:
    def __init__(self, valid_mask):
        self.N = len(valid_mask)
        self.valid = [(r, c) for r in range(self.N) for c in range(self.N) if bool(valid_mask[r][c])]
        self.valid_set = set(self.valid)

        self.neigh = {}
        self.neigh_cycle = {}
        for cell in self.valid:
            r, c = cell
            cyc = []
            ns = []
            for dr, dc in DIRS:
                nr, nc = r + dr, c + dc
                ncell = (nr, nc)
                if 0 <= nr < self.N and 0 <= nc < self.N and ncell in self.valid_set:
                    cyc.append(ncell)
                    ns.append(ncell)
                else:
                    cyc.append(None)
            self.neigh[cell] = tuple(ns)
            self.neigh_cycle[cell] = tuple(cyc)

        self.boundary = [cell for cell in self.valid if len(self.neigh[cell]) < 6]
        self.boundary_set = set(self.boundary)

        corners = [cell for cell in self.boundary if len(self.neigh[cell]) == 3]
        if len(corners) != 6:
            corners = self._fallback_corners()

        bneigh = {
            cell: sorted([n for n in self.neigh[cell] if n in self.boundary_set])
            for cell in self.boundary
        }
        order = self._order_boundary(bneigh, corners)

        corner_set = set(corners)
        corner_positions = [(i, cell) for i, cell in enumerate(order) if cell in corner_set]
        if len(corner_positions) != 6:
            pos = {cell: i for i, cell in enumerate(order)}
            corner_positions = sorted((pos.get(cell, INF), cell) for cell in corners)[:6]

        corner_positions.sort()
        self.corners = [cell for _, cell in corner_positions]
        self.corner_of = {cell: i for i, cell in enumerate(self.corners)}

        m = len(order)
        edge_sets = [set() for _ in range(6)]
        if m > 0 and len(corner_positions) == 6:
            for k in range(6):
                a = corner_positions[k][0]
                b = corner_positions[(k + 1) % 6][0]
                i = (a + 1) % m
                while i != b:
                    cell = order[i]
                    if cell not in self.corner_of:
                        edge_sets[k].add(cell)
                    i = (i + 1) % m
        self.edge_cells = [tuple(sorted(s)) for s in edge_sets]
        self.edge_of = {}
        for i, cells in enumerate(self.edge_cells):
            for cell in cells:
                self.edge_of[cell] = i

        mid = (self.N - 1) / 2.0
        self.center = min(self.valid, key=lambda x: (x[0] - mid) ** 2 + (x[1] - mid) ** 2)
        self.center_dist = self._bfs_dist(self.center)
        maxd = max(self.center_dist.values()) if self.center_dist else 0
        self.center_score = {cell: maxd - self.center_dist[cell] for cell in self.valid}
        self.center_order = tuple(sorted(self.valid, key=lambda cell: (self.center_dist[cell], cell[0], cell[1])))

    def _bfs_dist(self, start):
        dist = {start: 0}
        dq = deque([start])
        while dq:
            u = dq.popleft()
            du = dist[u]
            for v in self.neigh[u]:
                if v not in dist:
                    dist[v] = du + 1
                    dq.append(v)
        # board is connected, but be safe
        for cell in self.valid:
            if cell not in dist:
                dist[cell] = INF
        return dist

    def _fallback_corners(self):
        b = self.boundary
        if not b:
            return []
        cand = {
            min(b, key=lambda x: (x[0], x[1])),
            max(b, key=lambda x: (x[0], x[1])),
            min(b, key=lambda x: (x[1], x[0])),
            max(b, key=lambda x: (x[1], x[0])),
            min(b, key=lambda x: (x[0] - x[1], x[0], x[1])),
            max(b, key=lambda x: (x[0] - x[1], x[0], x[1])),
        }
        if len(cand) < 6:
            extras = sorted(b, key=lambda x: (len(self.neigh[x]), x[0], x[1]))
            for cell in extras:
                cand.add(cell)
                if len(cand) == 6:
                    break
        return list(cand)

    def _order_boundary(self, bneigh, corners):
        if not self.boundary:
            return []
        start = min(corners) if corners else min(self.boundary)
        starts = bneigh.get(start, [])
        if not starts:
            return sorted(self.boundary)

        for first in starts:
            order = [start]
            used = {start}
            prev = start
            cur = first
            ok = True
            while cur != start and len(order) <= len(self.boundary):
                if cur in used:
                    ok = False
                    break
                order.append(cur)
                used.add(cur)
                nxts = bneigh.get(cur, [])
                if not nxts:
                    ok = False
                    break
                if len(nxts) == 1:
                    nxt = nxts[0]
                else:
                    if nxts[0] == prev:
                        nxt = nxts[1]
                    elif nxts[1] == prev:
                        nxt = nxts[0]
                    else:
                        nxt = nxts[0] if nxts[0] not in used else nxts[1]
                prev, cur = cur, nxt
            if ok and cur == start and len(order) == len(self.boundary):
                return order

        return sorted(self.boundary)


def get_geometry(valid_mask):
    global _GEOM
    if _GEOM is None or _GEOM.N != len(valid_mask):
        _GEOM = Geometry(valid_mask)
    return _GEOM


def build_components(occ, geom):
    comp_id = {}
    comps = []
    for cell in occ:
        if cell in comp_id:
            continue
        idx = len(comps)
        q = deque([cell])
        comp_id[cell] = idx
        size = 0
        corners = set()
        edges = set()
        while q:
            u = q.popleft()
            size += 1
            if u in geom.corner_of:
                corners.add(geom.corner_of[u])
            if u in geom.edge_of:
                edges.add(geom.edge_of[u])
            for v in geom.neigh[u]:
                if v in occ and v not in comp_id:
                    comp_id[v] = idx
                    q.append(v)
        comps.append((size, frozenset(corners), frozenset(edges)))
    return comp_id, comps


def has_ring(player_occ, geom):
    visited = set()
    dq = deque()

    for cell in geom.boundary:
        if cell not in player_occ and cell not in visited:
            visited.add(cell)
            dq.append(cell)

    while dq:
        u = dq.popleft()
        for v in geom.neigh[u]:
            if v not in player_occ and v not in visited:
                visited.add(v)
                dq.append(v)

    for cell in geom.valid:
        if cell not in player_occ and cell not in visited:
            return True
    return False


def is_winning_move(move, occ, geom):
    if move in occ:
        return False

    occ2 = set(occ)
    occ2.add(move)

    q = deque([move])
    seen = {move}
    corners = set()
    edges = set()

    friendly_neighbors = 0
    for n in geom.neigh[move]:
        if n in occ:
            friendly_neighbors += 1

    while q:
        u = q.popleft()
        if u in geom.corner_of:
            corners.add(geom.corner_of[u])
        if u in geom.edge_of:
            edges.add(geom.edge_of[u])
        for v in geom.neigh[u]:
            if v in occ2 and v not in seen:
                seen.add(v)
                q.append(v)

    if len(corners) >= 2:
        return True
    if len(edges) >= 3:
        return True

    # Ring needs a cycle, so < 2 adjacent friendly stones cannot create one.
    if friendly_neighbors >= 2 and len(occ) >= 5:
        if has_ring(occ2, geom):
            return True

    return False


def build_entry_costs(own, enemy, geom):
    cost = {}
    for cell in geom.valid:
        if cell in enemy:
            cost[cell] = INF
        elif cell in own:
            cost[cell] = 0
        else:
            cost[cell] = 1
    return cost


def zero_one_bfs(sources, entry_cost, geom):
    dist = {cell: INF for cell in geom.valid}
    dq = deque()

    for s in sources:
        w = entry_cost[s]
        if w >= INF:
            continue
        if w < dist[s]:
            dist[s] = w
            if w == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        u = dq.popleft()
        du = dist[u]
        for v in geom.neigh[u]:
            w = entry_cost[v]
            if w >= INF:
                continue
            nd = du + w
            if nd < dist[v]:
                dist[v] = nd
                if w == 0:
                    dq.appendleft(v)
                else:
                    dq.append(v)
    return dist


def pattern_score(move, own_set, geom):
    bits = [1 if (n is not None and n in own_set) else 0 for n in geom.neigh_cycle[move]]
    same_n = sum(bits)
    if same_n < 2:
        return 0.0

    clusters = 0
    for i in range(6):
        if bits[i] and not bits[i - 1]:
            clusters += 1

    opposites = 0
    for a, b in ((0, 3), (1, 4), (2, 5)):
        if bits[a] and bits[b]:
            opposites += 1

    return 1.5 * same_n + 3.0 * max(0, clusters - 1) + 2.0 * opposites


def local_value(move, own_set, enemy_set, comp_id, comps, geom, total_stones):
    adj_ids = set()
    same_n = 0
    enemy_n = 0
    merged_size = 1
    corners = set()
    edges = set()

    for n in geom.neigh[move]:
        if n in own_set:
            same_n += 1
            cid = comp_id[n]
            if cid not in adj_ids:
                adj_ids.add(cid)
                size, cc, ee = comps[cid]
                merged_size += size
                corners.update(cc)
                edges.update(ee)
        elif n in enemy_set:
            enemy_n += 1

    if move in geom.corner_of:
        corners.add(geom.corner_of[move])
    elif move in geom.edge_of:
        edges.add(geom.edge_of[move])

    liberties = 0
    for n in geom.neigh[move]:
        if n not in own_set and n not in enemy_set:
            liberties += 1

    if total_stones < 18:
        center_w = 6.0
    elif total_stones < 70:
        center_w = 3.0
    else:
        center_w = 1.5

    s = 0.0
    s += center_w * geom.center_score[move]
    s += 7.0 * same_n
    s += 2.5 * enemy_n
    s += 20.0 * max(0, len(adj_ids) - 1)
    s += 1.6 * merged_size
    s += 1.5 * liberties
    s += pattern_score(move, own_set, geom)

    # Strategic target pressure.
    s += 5.0 * len(corners)
    s += 3.0 * len(edges)
    if len(edges) >= 2:
        s += 10.0
    if len(corners) >= 1:
        s += 2.0 * len(edges)

    # Avoid pointless isolated plays once the game has started.
    occupied_n = same_n + enemy_n
    if total_stones >= 2 and occupied_n == 0:
        s -= 5.0 + 0.6 * geom.center_dist[move]

    # Opening bias away from the boundary unless justified.
    if total_stones < 10 and (move in geom.edge_of or move in geom.corner_of):
        s -= 3.0

    return s


def path_bonus(move, corner_maps, edge_maps):
    corner_costs = []
    for d in corner_maps:
        val = d[move]
        corner_costs.append(99 if val >= INF else max(0, val - 1))
    edge_costs = []
    for d in edge_maps:
        val = d[move]
        edge_costs.append(99 if val >= INF else max(0, val - 1))

    corner_costs.sort()
    edge_costs.sort()

    s = 0.0
    if len(corner_costs) >= 2 and corner_costs[1] < 99:
        pair = corner_costs[0] + corner_costs[1]
        s += 8.0 / (1.0 + pair)
        if pair <= 2:
            s += 10.0 - 3.0 * pair

    if len(edge_costs) >= 3 and edge_costs[2] < 99:
        trip = edge_costs[0] + edge_costs[1] + edge_costs[2]
        s += 10.0 / (1.0 + trip)
        if trip <= 4:
            s += 12.0 - 2.0 * trip

    return s


def policy(me, opp, valid_mask):
    geom = get_geometry(valid_mask)

    me_set = set(map(tuple, me))
    opp_set = set(map(tuple, opp))
    occupied = me_set | opp_set

    legal = [cell for cell in geom.center_order if cell not in occupied]
    if not legal:
        # Should not happen in a legal game, but still return something valid.
        return geom.center

    if len(legal) == 1:
        return legal[0]

    try:
        # 1) Immediate win.
        for m in legal:
            if is_winning_move(m, me_set, geom):
                return m

        # 2) Immediate block.
        opp_wins = [m for m in legal if is_winning_move(m, opp_set, geom)]
        if len(opp_wins) == 1:
            return opp_wins[0]

        total_stones = len(occupied)

        # 3) Opening: take the center or closest available center cell.
        if total_stones <= 1 and not opp_wins:
            return legal[0]

        candidate_moves = opp_wins if opp_wins else legal
        if len(candidate_moves) == 1:
            return candidate_moves[0]

        my_comp_id, my_comps = build_components(me_set, geom)
        opp_comp_id, opp_comps = build_components(opp_set, geom)

        my_entry = build_entry_costs(me_set, opp_set, geom)
        opp_entry = build_entry_costs(opp_set, me_set, geom)

        my_corner_maps = [zero_one_bfs((corner,), my_entry, geom) for corner in geom.corners]
        my_edge_maps = [zero_one_bfs(edge_cells, my_entry, geom) for edge_cells in geom.edge_cells]

        opp_corner_maps = [zero_one_bfs((corner,), opp_entry, geom) for corner in geom.corners]
        opp_edge_maps = [zero_one_bfs(edge_cells, opp_entry, geom) for edge_cells in geom.edge_cells]

        if total_stones < 18:
            block_factor = 0.65
        elif total_stones < 70:
            block_factor = 0.85
        else:
            block_factor = 0.95

        best_move = candidate_moves[0]
        best_key = None

        for m in candidate_moves:
            my_score = local_value(m, me_set, opp_set, my_comp_id, my_comps, geom, total_stones)
            my_score += path_bonus(m, my_corner_maps, my_edge_maps)

            opp_score = local_value(m, opp_set, me_set, opp_comp_id, opp_comps, geom, total_stones)
            opp_score += path_bonus(m, opp_corner_maps, opp_edge_maps)

            score = my_score + block_factor * opp_score
            tie_neighbors = sum(1 for n in geom.neigh[m] if n in occupied)

            key = (score, tie_neighbors, geom.center_score[m], -m[0], -m[1])
            if best_key is None or key > best_key:
                best_key = key
                best_move = m

        return best_move

    except Exception:
        # Deterministic legal fallback.
        return legal[0]
