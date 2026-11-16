
from __future__ import annotations

# Havannah policy for a 15x15 hex-shaped board embedded in a square mask.
# The function required by the arena is:
#     policy(me, opp, valid_mask) -> (row, col)

_GEOM_CACHE = {}

# Axial-style neighbourhood for the common Havannah square-array encoding:
# valid cells are usually abs(row-col) < side_length.
_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]


class DSU:
    def __init__(self):
        self.parent = {}
        self.rank = {}
        self.cbits = {}
        self.ebits = {}

    def add(self, x, cb=0, eb=0):
        self.parent[x] = x
        self.rank[x] = 0
        self.cbits[x] = cb
        self.ebits[x] = eb

    def find(self, x):
        p = self.parent[x]
        if p != x:
            self.parent[x] = self.find(p)
        return self.parent[x]

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return ra
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.cbits[ra] |= self.cbits[rb]
        self.ebits[ra] |= self.ebits[rb]
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return ra


def _mask_key(valid_mask):
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0
    packed = []
    for r in range(rows):
        bits = 0
        for c in range(cols):
            if bool(valid_mask[r][c]):
                bits |= 1 << c
        packed.append(bits)
    return rows, cols, tuple(packed)


def _get_geometry(valid_mask):
    key = _mask_key(valid_mask)
    if key in _GEOM_CACHE:
        return _GEOM_CACHE[key]

    rows, cols, _ = key
    valid = []
    valid_set = set()

    for r in range(rows):
        for c in range(cols):
            if bool(valid_mask[r][c]):
                cell = (r, c)
                valid.append(cell)
                valid_set.add(cell)

    # Extremely defensive fallback for malformed masks.
    if not valid:
        geom = {
            "valid": [],
            "valid_set": set(),
            "corner_bits": {},
            "edge_bits": {},
            "center": (0.0, 0.0, 0.0),
        }
        _GEOM_CACHE[key] = geom
        return geom

    rmin = min(r for r, c in valid)
    rmax = max(r for r, c in valid)
    cmin = min(c for r, c in valid)
    cmax = max(c for r, c in valid)
    dmin = min(r - c for r, c in valid)
    dmax = max(r - c for r, c in valid)

    # Six sides in axial coordinates:
    # 0: top row       r == rmin
    # 1: upper-right   r-c == dmin
    # 2: right column  c == cmax
    # 3: bottom row    r == rmax
    # 4: lower-left    r-c == dmax
    # 5: left column   c == cmin
    def side_flags(cell):
        r, c = cell
        d = r - c
        flags = []
        if r == rmin:
            flags.append(0)
        if d == dmin:
            flags.append(1)
        if c == cmax:
            flags.append(2)
        if r == rmax:
            flags.append(3)
        if d == dmax:
            flags.append(4)
        if c == cmin:
            flags.append(5)
        return flags

    # Corner order follows intersections of consecutive sides.
    corner_specs = [
        (0, 5),  # top-left
        (0, 1),  # top-right
        (1, 2),  # upper-right / right
        (2, 3),  # bottom-right
        (3, 4),  # bottom-left
        (4, 5),  # lower-left / left
    ]

    corner_cells = []
    for a, b in corner_specs:
        found = None
        for cell in valid:
            fl = side_flags(cell)
            if a in fl and b in fl:
                found = cell
                break
        if found is not None:
            corner_cells.append(found)

    # If a strange board orientation prevents detecting all corners,
    # supplement with low-degree boundary cells.
    if len(set(corner_cells)) < 6:
        degs = []
        for cell in valid:
            r, c = cell
            deg = 0
            for dr, dc in _DIRS:
                if (r + dr, c + dc) in valid_set:
                    deg += 1
            degs.append((deg, cell))
        degs.sort()
        for _, cell in degs:
            if cell not in corner_cells:
                corner_cells.append(cell)
            if len(set(corner_cells)) >= 6:
                break

    corner_cells = list(dict.fromkeys(corner_cells))[:6]
    corner_index = {cell: i for i, cell in enumerate(corner_cells)}

    corner_bits = {}
    edge_bits = {}

    for cell in valid:
        if cell in corner_index:
            corner_bits[cell] = 1 << corner_index[cell]
            edge_bits[cell] = 0          # Corners are not fork edges.
            continue

        corner_bits[cell] = 0
        eb = 0
        for s in side_flags(cell):
            eb |= 1 << s
        edge_bits[cell] = eb

    ar = sum(r for r, c in valid) / float(len(valid))
    ac = sum(c for r, c in valid) / float(len(valid))
    ad = sum((r - c) for r, c in valid) / float(len(valid))

    geom = {
        "valid": valid,
        "valid_set": valid_set,
        "corner_bits": corner_bits,
        "edge_bits": edge_bits,
        "center": (ar, ac, ad),
    }
    _GEOM_CACHE[key] = geom
    return geom


def _build_dsu(stones, geom):
    stones_set = set(stones)
    dsu = DSU()
    cbits = geom["corner_bits"]
    ebits = geom["edge_bits"]

    for cell in stones_set:
        dsu.add(cell, cbits.get(cell, 0), ebits.get(cell, 0))

    for r, c in stones_set:
        for dr, dc in _DIRS:
            nb = (r + dr, c + dc)
            if nb in stones_set:
                dsu.union((r, c), nb)

    return dsu, stones_set


def _bitcount(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")


def _potential(move, stones_set, dsu, geom):
    """Return tactical information if 'stones_set' player placed at move."""
    r, c = move
    cb = geom["corner_bits"].get(move, 0)
    eb = geom["edge_bits"].get(move, 0)

    seen_roots = set()
    duplicate_root = False
    adj = 0

    for dr, dc in _DIRS:
        nb = (r + dr, c + dc)
        if nb in stones_set:
            adj += 1
            root = dsu.find(nb)
            if root in seen_roots:
                duplicate_root = True
            else:
                seen_roots.add(root)
                cb |= dsu.cbits[root]
                eb |= dsu.ebits[root]

    ccount = _bitcount(cb)
    ecount = _bitcount(eb)

    # In a hex grid, connecting two neighbouring stones from the same existing
    # component usually completes a cycle, which is the local signature of a ring.
    ring = duplicate_root

    return {
        "corner_count": ccount,
        "edge_count": ecount,
        "adj": adj,
        "roots": len(seen_roots),
        "ring": ring,
        "corner_bits": cb,
        "edge_bits": eb,
    }


def _is_win_potential(pot):
    return pot["ring"] or pot["corner_count"] >= 2 or pot["edge_count"] >= 3


def _hex_dist_to_center(move, geom):
    r, c = move
    cr, cc, cd = geom["center"]
    return max(abs(r - cr), abs(c - cc), abs((r - c) - cd))


def _best_central_legal(legal, geom):
    if not legal:
        return None
    return min(legal, key=lambda x: (_hex_dist_to_center(x, geom), x[0], x[1]))


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    geom = _get_geometry(valid_mask)
    valid = geom["valid"]

    occupied = set(me) | set(opp)
    legal = [cell for cell in valid if cell not in occupied]

    # Absolute safety fallback: always return some legal move if one exists.
    if not legal:
        # This should never happen in a normal game, but keeps the API total.
        for r in range(len(valid_mask)):
            for c in range(len(valid_mask[0])):
                if bool(valid_mask[r][c]) and (r, c) not in occupied:
                    return (r, c)
        return (0, 0)

    if not me and not opp:
        mv = _best_central_legal(legal, geom)
        if mv is not None:
            return mv

    my_dsu, my_set = _build_dsu(me, geom)
    op_dsu, op_set = _build_dsu(opp, geom)

    # 1. Win immediately if possible.
    winning_moves = []
    for mv in legal:
        if _is_win_potential(_potential(mv, my_set, my_dsu, geom)):
            winning_moves.append(mv)

    if winning_moves:
        # Prefer central among winning moves for deterministic stability.
        return _best_central_legal(winning_moves, geom)

    # 2. Identify opponent immediate wins and block one.
    opponent_wins = []
    for mv in legal:
        if _is_win_potential(_potential(mv, op_set, op_dsu, geom)):
            opponent_wins.append(mv)

    phase = len(me) + len(opp)

    def score_move(mv):
        myp = _potential(mv, my_set, my_dsu, geom)
        oppp = _potential(mv, op_set, op_dsu, geom)

        dist = _hex_dist_to_center(mv, geom)
        center_weight = 8.0 if phase < 8 else 3.0

        score = -center_weight * dist

        r, c = mv
        empty_neigh = 0
        opp_adj_direct = 0
        for dr, dc in _DIRS:
            nb = (r + dr, c + dc)
            if nb in geom["valid_set"] and nb not in occupied:
                empty_neigh += 1
            if nb in op_set:
                opp_adj_direct += 1

        # Flexibility and local relevance.
        score += 3.0 * empty_neigh
        score += 10.0 * opp_adj_direct

        # Friendly connection value.
        score += 24.0 * myp["adj"]
        score += 45.0 * myp["roots"]
        score += 70.0 * max(0, myp["roots"] - 1)

        # Ring-building pressure.
        if myp["adj"] >= 2:
            score += 70.0
        if myp["roots"] >= 2:
            score += 110.0

        # Bridge / fork development.
        # Boundary moves are de-emphasized in the opening unless connected.
        boundary_factor = 1.0
        if phase < 8 and myp["adj"] == 0:
            boundary_factor = 0.18

        if myp["corner_count"] == 1:
            score += 160.0 * boundary_factor
        if myp["edge_count"] == 1:
            score += 35.0 * boundary_factor
        elif myp["edge_count"] == 2:
            score += 650.0
        elif myp["edge_count"] >= 3:
            score += 50000.0

        if myp["corner_count"] >= 2:
            score += 50000.0
        if myp["ring"]:
            score += 50000.0

        # Defensive value: occupy points that would be very good for opponent.
        if _is_win_potential(oppp):
            score += 100000.0
        else:
            score += 14.0 * oppp["adj"]
            score += 25.0 * oppp["roots"]
            if oppp["corner_count"] == 1:
                score += 130.0
            if oppp["edge_count"] == 2:
                score += 560.0
            elif oppp["edge_count"] == 1:
                score += 45.0
            if oppp["adj"] >= 2:
                score += 55.0
            if oppp["roots"] >= 2:
                score += 80.0

        # Deterministic tiny tie-breaker, state-dependent but legal-safe.
        h = (
            (mv[0] + 1) * 1009
            + (mv[1] + 1) * 9176
            + len(me) * 37
            + len(opp) * 101
        ) % 997
        score += h * 1e-5

        return score

    if opponent_wins:
        # If several losses are threatened, choose the block that is otherwise
        # strongest. If only one, this is the mandatory move.
        return max(opponent_wins, key=score_move)

    # 3. Otherwise play the highest scoring strategic/tactical move.
    best = max(legal, key=score_move)

    # Final legality assertion by construction; fallback anyway for arena safety.
    if best in occupied or not bool(valid_mask[best[0]][best[1]]):
        fallback = _best_central_legal(legal, geom)
        if fallback is not None:
            return fallback

    return best
