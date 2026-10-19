
from collections import deque
import math
import random

# Hex-neighbour directions matching the prompt's coordinate system.
_DIRS = ((1, 0), (-1, 0), (0, -1), (-1, -1), (0, 1), (-1, 1))

_CACHE = {}


def _mask_key(valid_mask):
    n = len(valid_mask)
    rows = []
    for r in range(n):
        row = valid_mask[r]
        rows.append(tuple(bool(row[c]) for c in range(len(row))))
    return (n, tuple(rows))


def _build_info(valid_mask):
    key = _mask_key(valid_mask)
    if key in _CACHE:
        return _CACHE[key]

    n = len(valid_mask)
    cells = []
    valid = set()
    for r in range(n):
        for c in range(len(valid_mask[r])):
            if bool(valid_mask[r][c]):
                valid.add((r, c))
                cells.append((r, c))

    neigh = {}
    for p in cells:
        r, c = p
        ns = []
        for dr, dc in _DIRS:
            q = (r + dr, c + dc)
            if q in valid:
                ns.append(q)
        neigh[p] = ns

    # A side is represented by a missing neighbour in one of the six directions.
    # Corners have two or more missing directions; edge cells have one missing dir.
    corner_id = {}
    edge_bits = {}
    corners = []

    for p in cells:
        r, c = p
        missing = []
        for i, (dr, dc) in enumerate(_DIRS):
            if (r + dr, c + dc) not in valid:
                missing.append(i)

        if len(missing) >= 2:
            corner_id[p] = len(corners)
            corners.append(p)
            edge_bits[p] = 0       # Corners do not count as edges for fork.
        elif len(missing) == 1:
            corner_id[p] = -1
            edge_bits[p] = 1 << missing[0]
        else:
            corner_id[p] = -1
            edge_bits[p] = 0

    # Geometric centre for soft positional scoring.
    cr = sum(r for r, c in cells) / max(1, len(cells))
    cc = sum(c for r, c in cells) / max(1, len(cells))

    info = {
        "n": n,
        "valid": valid,
        "cells": cells,
        "neigh": neigh,
        "corner_id": corner_id,
        "edge_bits": edge_bits,
        "centre": (cr, cc),
    }
    _CACHE[key] = info
    return info


class _DSU:
    __slots__ = ("parent", "size", "corners", "edges")

    def __init__(self):
        self.parent = {}
        self.size = {}
        self.corners = {}
        self.edges = {}

    def add(self, x, corner_mask=0, edge_mask=0):
        self.parent[x] = x
        self.size[x] = 1
        self.corners[x] = corner_mask
        self.edges[x] = edge_mask

    def find(self, x):
        parent = self.parent
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(self, a, b):
        ra = self.find(a)
        rb = self.find(b)
        if ra == rb:
            return ra
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        self.size[ra] += self.size[rb]
        self.corners[ra] |= self.corners[rb]
        self.edges[ra] |= self.edges[rb]
        return ra


def _bitcount(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")


def _stone_masks(p, info):
    cid = info["corner_id"].get(p, -1)
    cm = 0 if cid < 0 else (1 << cid)
    em = info["edge_bits"].get(p, 0)
    return cm, em


def _component_after_move(stones, move, info):
    sset = set(stones)
    dsu = _DSU()

    for p in sset:
        cm, em = _stone_masks(p, info)
        dsu.add(p, cm, em)

    if move not in dsu.parent:
        cm, em = _stone_masks(move, info)
        dsu.add(move, cm, em)
        sset.add(move)

    for p in sset:
        for q in info["neigh"][p]:
            if q in sset and q in dsu.parent:
                dsu.union(p, q)

    root = dsu.find(move)
    return dsu, root


def _creates_graph_cycle(stones, move, info):
    """
    Practical ring proxy:
    if the placed stone touches two neighbours already connected through
    the player's stones without using the move, then a cycle is formed.
    Havannah rings are cycles enclosing at least one cell; this catches many
    tactical ring wins and threats cheaply.
    """
    sset = set(stones)
    ns = [q for q in info["neigh"][move] if q in sset]
    if len(ns) < 2:
        return False

    start_targets = set(ns)
    for i in range(len(ns)):
        start = ns[i]
        targets = set(ns[i + 1:])
        if not targets:
            continue
        seen = {start}
        dq = deque([start])
        while dq:
            p = dq.popleft()
            if p in targets:
                return True
            for q in info["neigh"][p]:
                if q in sset and q not in seen:
                    seen.add(q)
                    dq.append(q)
    return False


def _is_win_move(stones, move, info):
    dsu, root = _component_after_move(stones, move, info)
    if _bitcount(dsu.corners[root]) >= 2:
        return True
    if _bitcount(dsu.edges[root]) >= 3:
        return True
    if _creates_graph_cycle(stones, move, info):
        return True
    return False


def _threat_value(stones, move, info):
    dsu, root = _component_after_move(stones, move, info)
    corners = _bitcount(dsu.corners[root])
    edges = _bitcount(dsu.edges[root])
    size = dsu.size[root]
    val = 0.0
    val += 8.0 * corners
    val += 5.0 * edges
    val += 0.8 * size

    if corners >= 1:
        val += 5.0
    if edges >= 2:
        val += 10.0
    if corners >= 2:
        val += 10000.0
    if edges >= 3:
        val += 10000.0
    if _creates_graph_cycle(stones, move, info):
        val += 10000.0
    return val


def _score_move(move, me_set, opp_set, info, ply):
    r, c = move
    cr, cc = info["centre"]

    score = 0.0

    # Centrality is valuable early, but less decisive later.
    dist = abs(r - cr) + abs(c - cc)
    score += max(0.0, 18.0 - dist) * (1.4 if ply < 10 else 0.7)

    own_adj = 0
    opp_adj = 0
    empty_adj = 0

    for q in info["neigh"][move]:
        if q in me_set:
            own_adj += 1
        elif q in opp_set:
            opp_adj += 1
        else:
            empty_adj += 1

    # Local contact.
    score += 7.0 * own_adj
    score += 3.5 * opp_adj
    score += 0.6 * empty_adj

    # Prefer moves that merge multiple own groups.
    own_roots_seen = set()
    if own_adj:
        dsu = _DSU()
        for p in me_set:
            cm, em = _stone_masks(p, info)
            dsu.add(p, cm, em)
        for p in me_set:
            for q in info["neigh"][p]:
                if q in me_set:
                    dsu.union(p, q)
        for q in info["neigh"][move]:
            if q in me_set:
                own_roots_seen.add(dsu.find(q))
        score += 9.0 * max(0, len(own_roots_seen) - 1)

    # Own strategic structure value.
    score += _threat_value(me_set, move, info) * 0.9

    # Defensive value: occupy points useful to opponent.
    score += _threat_value(opp_set, move, info) * 0.65

    # Cells that are themselves boundary-relevant.
    cid = info["corner_id"].get(move, -1)
    if cid >= 0:
        score += 9.0
    eb = info["edge_bits"].get(move, 0)
    if eb:
        score += 3.0

    # Avoid completely isolated moves after opening.
    if ply > 5 and own_adj == 0 and opp_adj == 0:
        score -= 8.0

    # Tiny deterministic jitter to avoid repeated ties.
    score += ((r * 37 + c * 17) % 13) * 0.001
    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    info = _build_info(valid_mask)
    valid = info["valid"]

    me_set = set(tuple(x) for x in me)
    opp_set = set(tuple(x) for x in opp)
    occupied = me_set | opp_set

    legal = [p for p in valid if p not in occupied]

    # Absolute safety fallback.
    if not legal:
        # This should not happen in normal play, but return some valid cell.
        for p in valid:
            return p
        return (0, 0)

    ply = len(me_set) + len(opp_set)

    # Opening: play near the centre.
    if ply == 0:
        cr, cc = info["centre"]
        return min(legal, key=lambda p: (p[0] - cr) ** 2 + (p[1] - cc) ** 2)

    # 1. Win immediately if possible.
    winning = []
    for m in legal:
        if _is_win_move(me_set, m, info):
            winning.append(m)
    if winning:
        return max(winning, key=lambda m: _score_move(m, me_set, opp_set, info, ply))

    # 2. Block opponent immediate wins.
    blocks = []
    for m in legal:
        if _is_win_move(opp_set, m, info):
            blocks.append(m)
    if blocks:
        return max(blocks, key=lambda m: _score_move(m, me_set, opp_set, info, ply) + 1000.0)

    # 3. Tactical/strategic heuristic.
    best = None
    best_score = -10**100
    for m in legal:
        s = _score_move(m, me_set, opp_set, info, ply)
        if s > best_score:
            best_score = s
            best = m

    if best is not None:
        return best

    # Final legal fallback.
    return legal[0]
