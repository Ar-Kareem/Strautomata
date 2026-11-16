
import math
import random
from collections import deque, defaultdict

N = 15

# Hex neighbors matching prompt:
# (r,c) touches (r-1,c),(r+1,c),(r-1,c-1),(r,c-1),(r,c+1),(r-1,c+1)
# More generally from example: left column: (r-1,c-1),(r,c-1); right: (r,c+1),(r-1,c+1)
DIRS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]


def _inside(r, c, valid_mask):
    return 0 <= r < len(valid_mask) and 0 <= c < len(valid_mask[r]) and bool(valid_mask[r][c])


def _neighbors(cell, valid_mask):
    r, c = cell
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _inside(nr, nc, valid_mask):
            yield (nr, nc)


def _board_cells(valid_mask):
    n = len(valid_mask)
    return [(r, c) for r in range(n) for c in range(len(valid_mask[r])) if bool(valid_mask[r][c])]


def _classify_boundaries(valid_mask):
    """
    Return:
      corners: set of cells with exactly 3 playable neighbors, usually six cells.
      edge_id: dict cell -> bitmask of non-corner board edges touched.
    We infer geometric sides by boundary degrees and chains. This works for standard
    Havannah hex boards embedded in a rectangular/rhombic mask.
    """
    cells = _board_cells(valid_mask)
    cellset = set(cells)

    corners = {x for x in cells if sum(1 for _ in _neighbors(x, valid_mask)) == 3}

    # Fallback for unusual masks: choose six extremes.
    if len(corners) != 6:
        candidates = sorted(cells, key=lambda p: (p[0] + p[1], p[0], p[1]))
        guess = set()
        guess.add(min(cells, key=lambda p: (p[0], p[1])))
        guess.add(max(cells, key=lambda p: (p[0], p[1])))
        guess.add(min(cells, key=lambda p: (p[1], p[0])))
        guess.add(max(cells, key=lambda p: (p[1], p[0])))
        guess.add(min(cells, key=lambda p: (p[0] - p[1], p[0])))
        guess.add(max(cells, key=lambda p: (p[0] - p[1], p[0])))
        corners = set(list(guess)[:6])

    boundary = {x for x in cells if sum(1 for _ in _neighbors(x, valid_mask)) < 6}
    noncorner_boundary = boundary - corners

    # Split boundary non-corners into up to 6 chains. Two boundary cells adjacent
    # on the rim belong together unless crossing through a corner.
    seen = set()
    chains = []
    for b in noncorner_boundary:
        if b in seen:
            continue
        q = deque([b])
        seen.add(b)
        comp = []
        while q:
            x = q.popleft()
            comp.append(x)
            for y in _neighbors(x, valid_mask):
                if y in noncorner_boundary and y not in seen:
                    # Boundary adjacency can jump near concavities, but board is convex.
                    seen.add(y)
                    q.append(y)
        chains.append(comp)

    # If the whole rim was connected as one chain due to adjacent side cells, split
    # by directions/coordinates fallback. For normal masks, there are six sides.
    edge_id = {}
    if len(chains) == 6:
        for i, ch in enumerate(chains):
            bit = 1 << i
            for x in ch:
                edge_id[x] = edge_id.get(x, 0) | bit
    else:
        # Robust geometric fallback: six lines of a parallelogram/hex mask:
        rows = [r for r, c in cells]
        cols = [c for r, c in cells]
        sums = [r + c for r, c in cells]
        diffs = [r - c for r, c in cells]
        vals = [
            ("rmin", min(rows)), ("rmax", max(rows)),
            ("cmin", min(cols)), ("cmax", max(cols)),
            ("smin", min(sums)), ("smax", max(sums)),
        ]
        # Use only actual side-like constraints; assign bits.
        for idx, (typ, val) in enumerate(vals[:6]):
            bit = 1 << idx
            for r, c in noncorner_boundary:
                ok = (
                    (typ == "rmin" and r == val) or
                    (typ == "rmax" and r == val) or
                    (typ == "cmin" and c == val) or
                    (typ == "cmax" and c == val) or
                    (typ == "smin" and r + c == val) or
                    (typ == "smax" and r + c == val)
                )
                if ok:
                    edge_id[(r, c)] = edge_id.get((r, c), 0) | bit

        # Some Havannah embeddings use diagonals r-c.
        if len(set(edge_id.values())) < 3:
            edge_id.clear()
            vals2 = [
                ("rmin", min(rows)), ("rmax", max(rows)),
                ("cmin", min(cols)), ("cmax", max(cols)),
                ("dmin", min(diffs)), ("dmax", max(diffs)),
            ]
            for idx, (typ, val) in enumerate(vals2):
                bit = 1 << idx
                for r, c in noncorner_boundary:
                    ok = (
                        (typ == "rmin" and r == val) or
                        (typ == "rmax" and r == val) or
                        (typ == "cmin" and c == val) or
                        (typ == "cmax" and c == val) or
                        (typ == "dmin" and r - c == val) or
                        (typ == "dmax" and r - c == val)
                    )
                    if ok:
                        edge_id[(r, c)] = edge_id.get((r, c), 0) | bit

    return corners, edge_id


class DSU:
    def __init__(self):
        self.p = {}
        self.sz = {}
        self.corners = {}
        self.edges = {}

    def add(self, x, corner_bit=0, edge_bits=0):
        if x not in self.p:
            self.p[x] = x
            self.sz[x] = 1
            self.corners[x] = corner_bit
            self.edges[x] = edge_bits

    def find(self, x):
        p = self.p[x]
        while p != self.p[p]:
            p = self.p[p]
        while x != p:
            nx = self.p[x]
            self.p[x] = p
            x = nx
        return p

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        if self.sz[ra] < self.sz[rb]:
            ra, rb = rb, ra
        self.p[rb] = ra
        self.sz[ra] += self.sz[rb]
        self.corners[ra] |= self.corners[rb]
        self.edges[ra] |= self.edges[rb]
        return ra


def _popcount(x):
    try:
        return int(x).bit_count()
    except AttributeError:
        return bin(x).count("1")


def _has_ring(stones, valid_mask):
    """
    Detect ring by checking if any non-stone connected empty/opponent region is
    fully enclosed away from the outside of the board.
    In Havannah, a ring of stones creates an interior region not connected to
    the board boundary without crossing stones.
    """
    stone_set = set(stones)
    cells = _board_cells(valid_mask)
    boundary = {x for x in cells if sum(1 for _ in _neighbors(x, valid_mask)) < 6}
    nonstones = [x for x in cells if x not in stone_set]
    seen = set()
    for start in nonstones:
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        touches_boundary = start in boundary
        count = 0
        while q:
            x = q.popleft()
            count += 1
            if x in boundary:
                touches_boundary = True
            for y in _neighbors(x, valid_mask):
                if y not in stone_set and y not in seen:
                    seen.add(y)
                    q.append(y)
        if not touches_boundary and count > 0:
            return True
    return False


def _is_win(stones, valid_mask, corners, edge_id):
    stones = set(stones)
    if not stones:
        return False

    corner_list = list(corners)
    corner_index = {x: i for i, x in enumerate(corner_list[:6])}
    dsu = DSU()

    for x in stones:
        cb = 0
        if x in corner_index:
            cb = 1 << corner_index[x]
        eb = edge_id.get(x, 0)
        dsu.add(x, cb, eb)

    for x in stones:
        for y in _neighbors(x, valid_mask):
            if y in stones:
                dsu.union(x, y)

    roots = set(dsu.find(x) for x in stones)
    for r in roots:
        if _popcount(dsu.corners[r]) >= 2:
            return True
        if _popcount(dsu.edges[r]) >= 3:
            return True

    if _has_ring(stones, valid_mask):
        return True

    return False


def _components(stones, valid_mask, corners, edge_id):
    stones = set(stones)
    corner_list = list(corners)
    corner_index = {x: i for i, x in enumerate(corner_list[:6])}
    dsu = DSU()
    for x in stones:
        cb = 1 << corner_index[x] if x in corner_index else 0
        eb = edge_id.get(x, 0)
        dsu.add(x, cb, eb)
    for x in stones:
        for y in _neighbors(x, valid_mask):
            if y in stones:
                dsu.union(x, y)

    info = {}
    for x in stones:
        r = dsu.find(x)
        if r not in info:
            info[r] = [0, dsu.corners[r], dsu.edges[r]]
        info[r][0] += 1
    return dsu, info


def _local_score(move, me_set, opp_set, valid_mask, corners, edge_id, all_valid):
    r, c = move

    # Center preference: Havannah rings and flexible connections benefit from center.
    cr = sum(x for x, y in all_valid) / float(len(all_valid))
    cc = sum(y for x, y in all_valid) / float(len(all_valid))
    dist = abs(r - cr) + abs(c - cc) + abs((r - c) - (cr - cc)) * 0.45
    score = 35.0 - 2.0 * dist

    neigh = list(_neighbors(move, valid_mask))
    friendly = [x for x in neigh if x in me_set]
    enemy = [x for x in neigh if x in opp_set]
    empty_neigh = [x for x in neigh if x not in me_set and x not in opp_set]

    score += 13.0 * len(friendly)
    score += 3.0 * len(empty_neigh)
    score += 4.5 * len(enemy)  # contact can block/cut

    # Boundary features.
    if move in corners:
        score += 18.0
    eb = edge_id.get(move, 0)
    if eb:
        score += 9.0 * _popcount(eb)

    # Connect multiple friendly components.
    dsu_me, info_me = _components(me_set, valid_mask, corners, edge_id)
    roots = set()
    comp_size_sum = 0
    comp_corner_bits = 0
    comp_edge_bits = eb
    for x in friendly:
        if x in dsu_me.p:
            root = dsu_me.find(x)
            roots.add(root)
    for root in roots:
        comp_size_sum += info_me[root][0]
        comp_corner_bits |= info_me[root][1]
        comp_edge_bits |= info_me[root][2]

    if len(roots) >= 2:
        score += 32.0 * (len(roots) - 1)
    score += 1.5 * min(comp_size_sum, 12)
    score += 18.0 * _popcount(comp_corner_bits)
    score += 15.0 * _popcount(comp_edge_bits)
    if _popcount(comp_corner_bits | (1 if move in corners else 0)) >= 1 and _popcount(comp_edge_bits) >= 1:
        score += 8.0
    if _popcount(comp_corner_bits) >= 1 and move in corners:
        score += 30.0
    if _popcount(comp_edge_bits) >= 2 and eb:
        score += 26.0

    # Ring-building heuristic: stones around common empty cells.
    for e in empty_neigh:
        around = list(_neighbors(e, valid_mask))
        k_me = sum(1 for z in around if z in me_set or z == move)
        k_opp = sum(1 for z in around if z in opp_set)
        if k_me >= 3:
            score += 6.0 * (k_me - 2)
        if k_me >= 4 and k_opp == 0:
            score += 18.0

    # Defensive value against opponent components/threats.
    dsu_op, info_op = _components(opp_set, valid_mask, corners, edge_id)
    oproots = set()
    o_edges = edge_id.get(move, 0)
    o_corners = 1 if move in corners else 0
    for x in enemy:
        if x in dsu_op.p:
            oproots.add(dsu_op.find(x))
    o_size = 0
    o_cb = 0
    o_eb = o_edges
    for root in oproots:
        o_size += info_op[root][0]
        o_cb |= info_op[root][1]
        o_eb |= info_op[root][2]

    score += 10.0 * len(oproots)
    if len(oproots) >= 2:
        score += 22.0 * (len(oproots) - 1)
    score += 8.0 * _popcount(o_cb)
    score += 7.0 * _popcount(o_eb)
    if _popcount(o_cb) >= 1 and move in corners:
        score += 20.0
    if _popcount(o_eb) >= 2 and o_edges:
        score += 18.0

    # Avoid isolated rim moves too early unless meaningful.
    if not friendly and not enemy and (move in corners or eb):
        score -= 10.0

    # Stable deterministic tie breaker.
    score += ((r * 37 + c * 101) % 1000) / 100000.0
    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        all_valid = _board_cells(valid_mask)
        occupied = set(me) | set(opp)
        legal = [x for x in all_valid if x not in occupied]
        if not legal:
            # Should not happen; still return a valid board cell.
            return all_valid[0] if all_valid else (0, 0)

        me_set = set(me)
        opp_set = set(opp)
        corners, edge_id = _classify_boundaries(valid_mask)

        # Opening: play central or near-central strong point.
        if not me and not opp:
            cr = sum(r for r, c in all_valid) / float(len(all_valid))
            cc = sum(c for r, c in all_valid) / float(len(all_valid))
            return min(legal, key=lambda p: abs(p[0] - cr) + abs(p[1] - cc) + abs((p[0]-p[1]) - (cr-cc)) * 0.25)

        # 1. Immediate win.
        for mv in legal:
            if _is_win(me_set | {mv}, valid_mask, corners, edge_id):
                return mv

        # 2. Block immediate opponent win.
        opp_wins = []
        for mv in legal:
            if _is_win(opp_set | {mv}, valid_mask, corners, edge_id):
                opp_wins.append(mv)
        if opp_wins:
            # If multiple blocks, choose the one best for us too.
            return max(opp_wins, key=lambda m: _local_score(m, me_set, opp_set, valid_mask, corners, edge_id, all_valid))

        # Candidate pruning: evaluate all on 15x15 is fine, but focus nearby occupied
        # if game has developed.
        if len(occupied) > 8:
            cand = set()
            for s in occupied:
                cand.add(s)
                for n1 in _neighbors(s, valid_mask):
                    if n1 not in occupied:
                        cand.add(n1)
                    for n2 in _neighbors(n1, valid_mask):
                        if n2 not in occupied:
                            cand.add(n2)
            candidates = [x for x in cand if x in legal]
            if len(candidates) < 12:
                candidates = legal
        else:
            candidates = legal

        # 3. Heuristic best move.
        best = None
        best_score = -1e100
        for mv in candidates:
            sc = _local_score(mv, me_set, opp_set, valid_mask, corners, edge_id, all_valid)

            # Light one-ply threat bonus: moves that create many next-turn wins.
            # Only for topological promising moves to fit time.
            if len(me) >= 4:
                new_me = me_set | {mv}
                threat_count = 0
                for n in _neighbors(mv, valid_mask):
                    if n not in new_me and n not in opp_set:
                        if _is_win(new_me | {n}, valid_mask, corners, edge_id):
                            threat_count += 1
                            if threat_count >= 2:
                                break
                if threat_count >= 2:
                    sc += 80.0
                elif threat_count == 1:
                    sc += 22.0

            if sc > best_score:
                best_score = sc
                best = mv

        if best is None or best in occupied or not _inside(best[0], best[1], valid_mask):
            # Absolute safety fallback.
            return legal[0]
        return best

    except Exception:
        # Never fail to return a legal move. Reconstruct simply.
        try:
            occupied = set(me) | set(opp)
            n = len(valid_mask)
            for r in range(n):
                for c in range(len(valid_mask[r])):
                    if bool(valid_mask[r][c]) and (r, c) not in occupied:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)
