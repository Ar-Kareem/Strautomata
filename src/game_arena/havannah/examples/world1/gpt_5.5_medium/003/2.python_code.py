
# Havannah 15x15 policy
# Implements:
#   policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]

from collections import deque
import math

_TOPO_CACHE = {}


def _mask_key(valid_mask):
    n = len(valid_mask)
    return tuple(tuple(bool(valid_mask[r][c]) for c in range(len(valid_mask[r]))) for r in range(n))


def _offset(c):
    # Coordinate system matching the prompt example:
    # odd columns touch rows r and r-1 in adjacent columns;
    # even columns touch rows r and r+1 in adjacent columns.
    return (c + 1) // 2


def _cube(row, col):
    # Convert odd-column vertical offset coordinates to axial/cube-like coordinates.
    x = col
    z = row - _offset(col)
    y = -x - z
    return x, y, z


def _raw_neighbors(r, c):
    if c & 1:
        return (
            (r - 1, c),
            (r + 1, c),
            (r - 1, c - 1),
            (r,     c - 1),
            (r - 1, c + 1),
            (r,     c + 1),
        )
    else:
        return (
            (r - 1, c),
            (r + 1, c),
            (r,     c - 1),
            (r + 1, c - 1),
            (r,     c + 1),
            (r + 1, c + 1),
        )


def _build_topology(valid_mask):
    key = _mask_key(valid_mask)
    if key in _TOPO_CACHE:
        return _TOPO_CACHE[key]

    rows = len(valid_mask)
    cols = max(len(valid_mask[r]) for r in range(rows)) if rows else 0

    valid = set()
    for r in range(rows):
        for c in range(len(valid_mask[r])):
            if bool(valid_mask[r][c]):
                valid.add((r, c))

    neigh = {}
    for cell in valid:
        r, c = cell
        neigh[cell] = [p for p in _raw_neighbors(r, c) if p in valid]

    cubes = {cell: _cube(cell[0], cell[1]) for cell in valid}
    xs = [v[0] for v in cubes.values()]
    ys = [v[1] for v in cubes.values()]
    zs = [v[2] for v in cubes.values()]

    minx, maxx = min(xs), max(xs)
    miny, maxy = min(ys), max(ys)
    minz, maxz = min(zs), max(zs)

    # Six side conditions. Opposite sides are paired by min/max of cube coordinates.
    side_values = (
        ("minx", minx),
        ("maxx", maxx),
        ("miny", miny),
        ("maxy", maxy),
        ("minz", minz),
        ("maxz", maxz),
    )

    def side_hits(cell):
        x, y, z = cubes[cell]
        hits = []
        if x == minx:
            hits.append(0)
        if x == maxx:
            hits.append(1)
        if y == miny:
            hits.append(2)
        if y == maxy:
            hits.append(3)
        if z == minz:
            hits.append(4)
        if z == maxz:
            hits.append(5)
        return hits

    corner_cells = [cell for cell in valid if len(side_hits(cell)) >= 2]

    # Robust fallback for unusual masks.
    if len(corner_cells) != 6:
        low_degree = [cell for cell in valid if len(neigh[cell]) <= 3]
        if len(low_degree) >= 6:
            # Keep the six most corner-like cells, ordered around the center.
            cx = sum(r for r, c in valid) / float(len(valid))
            cy = sum(c for r, c in valid) / float(len(valid))
            low_degree.sort(key=lambda p: -((p[0] - cx) ** 2 + (p[1] - cy) ** 2))
            corner_cells = low_degree[:6]

    corner_index = {cell: i for i, cell in enumerate(corner_cells)}

    corner_mask = {}
    edge_mask = {}
    boundary = []

    for cell in valid:
        cm = 0
        if cell in corner_index:
            cm = 1 << corner_index[cell]
        corner_mask[cell] = cm

        # Corners are not considered part of an edge for fork purposes.
        em = 0
        if cm == 0:
            for sid in side_hits(cell):
                em |= 1 << sid
        edge_mask[cell] = em

        if len(neigh[cell]) < 6:
            boundary.append(cell)

    # Center distance for positional scoring.
    avgx = sum(cubes[p][0] for p in valid) / float(len(valid))
    avgy = sum(cubes[p][1] for p in valid) / float(len(valid))
    avgz = sum(cubes[p][2] for p in valid) / float(len(valid))

    center_dist = {}
    maxdist = 1.0
    for p in valid:
        x, y, z = cubes[p]
        d = max(abs(x - avgx), abs(y - avgy), abs(z - avgz))
        center_dist[p] = d
        if d > maxdist:
            maxdist = d

    topo = {
        "valid": valid,
        "neighbors": neigh,
        "corner_mask": corner_mask,
        "edge_mask": edge_mask,
        "boundary": boundary,
        "center_dist": center_dist,
        "max_center_dist": maxdist,
        "rows": rows,
        "cols": cols,
    }

    _TOPO_CACHE[key] = topo
    return topo


class _DSU:
    __slots__ = ("parent", "size")

    def __init__(self, items):
        self.parent = {x: x for x in items}
        self.size = {x: 1 for x in items}

    def find(self, x):
        p = self.parent[x]
        while p != self.parent[p]:
            p = self.parent[p]
        while x != p:
            q = self.parent[x]
            self.parent[x] = p
            x = q
        return p

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return ra
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        return ra


def _components(stones, topo):
    if not stones:
        return {}, {}, {}, {}

    dsu = _DSU(stones)
    neigh = topo["neighbors"]

    for p in stones:
        for q in neigh[p]:
            if q in stones:
                dsu.union(p, q)

    comp_corner = {}
    comp_edge = {}
    comp_size = {}

    for p in stones:
        r = dsu.find(p)
        comp_corner[r] = comp_corner.get(r, 0) | topo["corner_mask"][p]
        comp_edge[r] = comp_edge.get(r, 0) | topo["edge_mask"][p]
        comp_size[r] = comp_size.get(r, 0) + 1

    cell_root = {p: dsu.find(p) for p in stones}
    return cell_root, comp_corner, comp_edge, comp_size


def _after_masks(move, stones, topo, comp):
    cell_root, comp_corner, comp_edge, comp_size = comp

    roots = set()
    for nb in topo["neighbors"][move]:
        if nb in stones:
            roots.add(cell_root[nb])

    cm = topo["corner_mask"][move]
    em = topo["edge_mask"][move]
    sz = 1

    for r in roots:
        cm |= comp_corner.get(r, 0)
        em |= comp_edge.get(r, 0)
        sz += comp_size.get(r, 1)

    return cm, em, sz, roots


def _ring_after(move, stones, topo):
    # Exact practical test: after adding the move, if any non-player cell is
    # disconnected from the board exterior, the player's stones enclose it.
    blocked = set(stones)
    blocked.add(move)

    valid = topo["valid"]
    neigh = topo["neighbors"]

    seen = set()
    dq = deque()

    for p in topo["boundary"]:
        if p not in blocked and p not in seen:
            seen.add(p)
            dq.append(p)

    while dq:
        p = dq.popleft()
        for q in neigh[p]:
            if q not in blocked and q not in seen:
                seen.add(q)
                dq.append(q)

    for p in valid:
        if p not in blocked and p not in seen:
            return True
    return False


def _is_win_move(move, stones, topo, comp):
    cm, em, _sz, _roots = _after_masks(move, stones, topo, comp)

    # Bridge: connect any two corners.
    if cm.bit_count() >= 2:
        return True

    # Fork: connect any three edges; corners are excluded from edge masks.
    if em.bit_count() >= 3:
        return True

    # Ring.
    friendly_adj = 0
    for nb in topo["neighbors"][move]:
        if nb in stones:
            friendly_adj += 1
    if friendly_adj >= 2 and _ring_after(move, stones, topo):
        return True

    return False


def _legal_moves(topo, me_set, opp_set):
    occ = me_set | opp_set
    return [p for p in topo["valid"] if p not in occ]


def _nearest_center_move(moves, topo):
    return min(moves, key=lambda p: topo["center_dist"].get(p, 999.0))


def _score_move(move, me_set, opp_set, topo, my_comp, opp_comp):
    neigh = topo["neighbors"][move]
    maxcd = topo["max_center_dist"]

    my_cm, my_em, my_sz, my_roots = _after_masks(move, me_set, topo, my_comp)
    op_cm, op_em, op_sz, op_roots = _after_masks(move, opp_set, topo, opp_comp)

    my_edges = my_em.bit_count()
    my_corners = my_cm.bit_count()
    op_edges = op_em.bit_count()
    op_corners = op_cm.bit_count()

    friendly_adj = sum(1 for q in neigh if q in me_set)
    enemy_adj = sum(1 for q in neigh if q in opp_set)
    empty_adj = sum(1 for q in neigh if q not in me_set and q not in opp_set)

    center_score = (maxcd - topo["center_dist"].get(move, maxcd))

    score = 0.0

    # Positional influence.
    score += 20.0 * center_score

    # Build strong connected groups.
    score += 28.0 * friendly_adj
    score += 45.0 * max(0, len(my_roots) - 1)
    score += 7.0 * math.sqrt(max(1, my_sz))

    # Havannah-specific progress.
    score += 75.0 * (my_edges ** 2)
    score += 95.0 * (my_corners ** 2)
    score += 30.0 * my_edges * my_corners

    # Defensive value: occupy cells that would be good for the opponent.
    score += 0.85 * (
        70.0 * (op_edges ** 2)
        + 90.0 * (op_corners ** 2)
        + 28.0 * op_edges * op_corners
        + 40.0 * max(0, len(op_roots) - 1)
        + 20.0 * enemy_adj
        + 5.0 * math.sqrt(max(1, op_sz))
    )

    # Local shape and flexibility.
    score += 5.0 * empty_adj
    score += 8.0 * enemy_adj

    # A totally isolated move is usually poor after the opening.
    if len(me_set) >= 2 and friendly_adj == 0 and enemy_adj == 0:
        score -= 28.0

    # Slight preference for actual edge/corner occupation when useful.
    if topo["corner_mask"][move]:
        score += 25.0
    elif topo["edge_mask"][move]:
        score += 8.0

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        topo = _build_topology(valid_mask)

        me_set = set(tuple(p) for p in me)
        opp_set = set(tuple(p) for p in opp)

        legal = _legal_moves(topo, me_set, opp_set)
        if not legal:
            # Should never happen in a normal game, but keep API total.
            return (0, 0)

        # Opening: take the center or closest available point.
        if not me_set and not opp_set:
            return _nearest_center_move(legal, topo)

        my_comp = _components(me_set, topo)
        opp_comp = _components(opp_set, topo)

        # 1. Immediate win.
        winning = [m for m in legal if _is_win_move(m, me_set, topo, my_comp)]
        if winning:
            return max(
                winning,
                key=lambda m: _score_move(m, me_set, opp_set, topo, my_comp, opp_comp),
            )

        # 2. Immediate block.
        opp_winning = [m for m in legal if _is_win_move(m, opp_set, topo, opp_comp)]
        if opp_winning:
            return max(
                opp_winning,
                key=lambda m: _score_move(m, me_set, opp_set, topo, my_comp, opp_comp),
            )

        # 3. Heuristic strategic move.
        return max(
            legal,
            key=lambda m: _score_move(m, me_set, opp_set, topo, my_comp, opp_comp),
        )

    except Exception:
        # Absolute safety fallback: always return a legal unoccupied cell if one exists.
        occupied = set(tuple(p) for p in me) | set(tuple(p) for p in opp)
        try:
            for r in range(len(valid_mask)):
                for c in range(len(valid_mask[r])):
                    if bool(valid_mask[r][c]) and (r, c) not in occupied:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
