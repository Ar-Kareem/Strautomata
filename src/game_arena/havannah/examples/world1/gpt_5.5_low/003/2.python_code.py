
from collections import deque, defaultdict
import math

# Hex-neighbour directions matching the coordinate description in the prompt.
_DIRS = ((1, 0), (-1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1))

_GEOM_CACHE = {}


def _popcount(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")


def _mask_key(valid_mask):
    n = len(valid_mask)
    rows = []
    for r in range(n):
        row = []
        for c in range(len(valid_mask[r])):
            row.append(1 if bool(valid_mask[r][c]) else 0)
        rows.append(tuple(row))
    return (n, tuple(rows))


def _build_geom(valid_mask):
    key = _mask_key(valid_mask)
    if key in _GEOM_CACHE:
        return _GEOM_CACHE[key]

    n = len(valid_mask)
    cells = []
    valid = set()
    for r in range(n):
        for c in range(len(valid_mask[r])):
            if bool(valid_mask[r][c]):
                valid.add((r, c))
                cells.append((r, c))

    neigh = {}
    for cell in cells:
        r, c = cell
        ns = []
        for dr, dc in _DIRS:
            nb = (r + dr, c + dc)
            if nb in valid:
                ns.append(nb)
        neigh[cell] = ns

    boundary = {x for x in cells if len(neigh[x]) < 6}
    corners = {x for x in boundary if len(neigh[x]) <= 3}

    # Fallback corner detection if the mask geometry is unusual.
    if len(corners) != 6 and boundary:
        # Pick six boundary cells that are extremal in axial-like directions.
        dirs = [
            lambda p: p[0],
            lambda p: -p[0],
            lambda p: p[1],
            lambda p: -p[1],
            lambda p: p[0] - p[1],
            lambda p: p[1] - p[0],
        ]
        corners = set()
        for f in dirs:
            best = min(boundary, key=f)
            corners.add(best)
        if len(corners) < 6:
            # Add farthest boundary cells from center until six are obtained.
            cr = sum(r for r, c in cells) / float(len(cells))
            cc = sum(c for r, c in cells) / float(len(cells))
            extra = sorted(boundary, key=lambda p: -((p[0] - cr) ** 2 + (p[1] - cc) ** 2))
            for p in extra:
                corners.add(p)
                if len(corners) >= 6:
                    break

    corner_list = list(corners)[:6]
    corner_id = {p: i for i, p in enumerate(corner_list)}

    # Boundary components after removing corners are the six edges.
    edge_id = {}
    edge_index = 0
    seen = set()
    noncorner_boundary = boundary - set(corner_list)

    for start in list(noncorner_boundary):
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        comp = []
        while q:
            x = q.popleft()
            comp.append(x)
            for y in neigh[x]:
                if y in noncorner_boundary and y not in seen:
                    seen.add(y)
                    q.append(y)
        for x in comp:
            edge_id[x] = edge_index
        edge_index += 1

    # If the boundary component method did not produce enough edges, assign
    # boundary non-corners to nearest side-like group by angle around center.
    if edge_index < 6 and noncorner_boundary:
        cr = sum(r for r, c in cells) / float(len(cells))
        cc = sum(c for r, c in cells) / float(len(cells))
        for x in noncorner_boundary:
            ang = math.atan2(x[0] - cr, x[1] - cc)
            k = int(((ang + math.pi) / (2 * math.pi)) * 6.0) % 6
            edge_id[x] = k

    center = (
        sum(r for r, c in cells) / float(len(cells)),
        sum(c for r, c in cells) / float(len(cells)),
    )

    geom = {
        "n": n,
        "cells": cells,
        "valid": valid,
        "neigh": neigh,
        "boundary": boundary,
        "corners": set(corner_list),
        "corner_id": corner_id,
        "edge_id": edge_id,
        "center": center,
    }
    _GEOM_CACHE[key] = geom
    return geom


class _DSU:
    def __init__(self):
        self.parent = {}
        self.size = {}
        self.corner_bits = {}
        self.edge_bits = {}

    def add(self, x, cb=0, eb=0):
        self.parent[x] = x
        self.size[x] = 1
        self.corner_bits[x] = cb
        self.edge_bits[x] = eb

    def find(self, x):
        p = self.parent[x]
        while p != self.parent[p]:
            p = self.parent[p]
        while x != p:
            nxt = self.parent[x]
            self.parent[x] = p
            x = nxt
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
        self.corner_bits[ra] |= self.corner_bits[rb]
        self.edge_bits[ra] |= self.edge_bits[rb]
        return ra


def _bits_for_cell(cell, geom):
    cb = 0
    eb = 0
    if cell in geom["corner_id"]:
        cb |= 1 << geom["corner_id"][cell]
    if cell in geom["edge_id"]:
        eb |= 1 << geom["edge_id"][cell]
    return cb, eb


def _has_ring(stones, geom):
    stones = set(stones)
    valid = geom["valid"]
    neigh = geom["neigh"]
    boundary = geom["boundary"]

    # Flood-fill all non-player cells reachable from the board boundary.
    q = deque()
    seen = set()

    for b in boundary:
        if b not in stones:
            seen.add(b)
            q.append(b)

    while q:
        x = q.popleft()
        for y in neigh[x]:
            if y not in stones and y not in seen:
                seen.add(y)
                q.append(y)

    # Any non-player cell not reachable from boundary is enclosed by stones.
    for x in valid:
        if x not in stones and x not in seen:
            return True
    return False


def _is_win(stones, geom):
    stones = set(stones)
    if not stones:
        return False

    dsu = _DSU()
    for s in stones:
        cb, eb = _bits_for_cell(s, geom)
        dsu.add(s, cb, eb)

    for s in stones:
        for nb in geom["neigh"][s]:
            if nb in stones:
                dsu.union(s, nb)

    roots = set()
    for s in stones:
        roots.add(dsu.find(s))

    for r in roots:
        if _popcount(dsu.corner_bits[r]) >= 2:
            return True
        if _popcount(dsu.edge_bits[r]) >= 3:
            return True

    if _has_ring(stones, geom):
        return True

    return False


def _component_maps(stones, geom):
    stones = set(stones)
    dsu = _DSU()
    for s in stones:
        cb, eb = _bits_for_cell(s, geom)
        dsu.add(s, cb, eb)

    for s in stones:
        for nb in geom["neigh"][s]:
            if nb in stones:
                dsu.union(s, nb)

    comp = {}
    for s in stones:
        root = dsu.find(s)
        comp[s] = root

    return dsu, comp


def _legal_moves(me, opp, geom):
    occupied = set(me) | set(opp)
    return [x for x in geom["cells"] if x not in occupied]


def _score_move(move, me_set, opp_set, geom, my_dsu, my_comp, op_dsu, op_comp, turn):
    r, c = move
    cr, cc = geom["center"]
    neigh = geom["neigh"][move]

    score = 0.0

    # Prefer central influence early, but not blindly.
    dist2 = (r - cr) ** 2 + (c - cc) ** 2
    score += 16.0 / (1.0 + dist2)

    my_roots = set()
    op_roots = set()
    my_adj = 0
    op_adj = 0
    empty_adj = 0

    for nb in neigh:
        if nb in me_set:
            my_adj += 1
            my_roots.add(my_comp[nb])
        elif nb in opp_set:
            op_adj += 1
            op_roots.add(op_comp[nb])
        else:
            empty_adj += 1

    # Friendly connection value.
    score += 4.5 * my_adj
    score += 7.0 * max(0, len(my_roots) - 1)

    # Defensive contact value.
    score += 3.5 * op_adj
    score += 4.0 * max(0, len(op_roots) - 1)

    # Avoid totally isolated moves except first move.
    if my_adj == 0 and op_adj == 0 and turn > 1:
        score -= 3.0

    # Reward creating/expanding bridge/fork-relevant metadata.
    cb, eb = _bits_for_cell(move, geom)
    my_corner_bits = cb
    my_edge_bits = eb
    my_size = 1
    for root in my_roots:
        my_corner_bits |= my_dsu.corner_bits[root]
        my_edge_bits |= my_dsu.edge_bits[root]
        my_size += my_dsu.size[root]

    score += 8.0 * _popcount(my_corner_bits)
    score += 5.5 * _popcount(my_edge_bits)
    score += 0.45 * my_size

    # Block opponent's bridge/fork development.
    op_corner_bits = cb
    op_edge_bits = eb
    op_size = 1
    for root in op_roots:
        op_corner_bits |= op_dsu.corner_bits[root]
        op_edge_bits |= op_dsu.edge_bits[root]
        op_size += op_dsu.size[root]

    score += 6.0 * _popcount(op_corner_bits)
    score += 4.0 * _popcount(op_edge_bits)
    score += 0.30 * op_size

    # Strong local shapes: having multiple friendly neighbours with liberties.
    if my_adj >= 2:
        score += 5.0
    if op_adj >= 2:
        score += 4.0

    # Corners are tactically important for bridges, but occupying too many
    # isolated edge cells early can be slow.
    if move in geom["corners"]:
        score += 9.0
    elif move in geom["edge_id"]:
        score += 2.0

    # Prefer moves with continuation space.
    score += 0.7 * empty_adj

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    geom = _build_geom(valid_mask)

    me_set = set(tuple(x) for x in me)
    opp_set = set(tuple(x) for x in opp)
    legal = _legal_moves(me_set, opp_set, geom)

    # Absolute safety fallback. Should only happen on malformed/full boards.
    if not legal:
        for r in range(len(valid_mask)):
            for c in range(len(valid_mask[r])):
                if bool(valid_mask[r][c]) and (r, c) not in me_set and (r, c) not in opp_set:
                    return (r, c)
        return (0, 0)

    # First move: take the cell nearest the board center.
    if not me_set and not opp_set:
        cr, cc = geom["center"]
        return min(legal, key=lambda p: (p[0] - cr) ** 2 + (p[1] - cc) ** 2)

    # 1. Immediate win.
    for mv in legal:
        if _is_win(me_set | {mv}, geom):
            return mv

    # 2. Immediate block of opponent win.
    blocking_moves = []
    for mv in legal:
        if _is_win(opp_set | {mv}, geom):
            blocking_moves.append(mv)

    if blocking_moves:
        if len(blocking_moves) == 1:
            return blocking_moves[0]
        # If multiple blocks, choose the one best for us too.
        my_dsu, my_comp = _component_maps(me_set, geom)
        op_dsu, op_comp = _component_maps(opp_set, geom)
        turn = len(me_set) + len(opp_set)
        return max(
            blocking_moves,
            key=lambda m: _score_move(m, me_set, opp_set, geom, my_dsu, my_comp, op_dsu, op_comp, turn),
        )

    # 3. General heuristic.
    my_dsu, my_comp = _component_maps(me_set, geom)
    op_dsu, op_comp = _component_maps(opp_set, geom)
    turn = len(me_set) + len(opp_set)

    # Consider all legal moves. On a 15x15 Havannah board this is small enough.
    best = None
    best_score = -10**18

    for mv in legal:
        sc = _score_move(mv, me_set, opp_set, geom, my_dsu, my_comp, op_dsu, op_comp, turn)

        # Small deterministic tie-breaker favoring center.
        cr, cc = geom["center"]
        sc -= 0.001 * ((mv[0] - cr) ** 2 + (mv[1] - cc) ** 2)

        if sc > best_score:
            best_score = sc
            best = mv

    if best is not None:
        return best

    # Final guaranteed legal fallback.
    return legal[0]
