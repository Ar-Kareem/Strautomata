
from collections import deque, defaultdict
import math

# Hex neighbors for the board embedding described in the prompt:
# (r-1,c), (r+1,c), (r,c-1), (r,c+1), (r-1,c-1), (r+1,c+1)
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)]

_CACHED = {}

def _in_bounds(n, r, c):
    return 0 <= r < n and 0 <= c < n

def _neighbors(cell, valid_mask):
    n = len(valid_mask)
    r, c = cell
    out = []
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if _in_bounds(n, nr, nc) and valid_mask[nr][nc]:
            out.append((nr, nc))
    return out

def _all_valid(valid_mask):
    n = len(valid_mask)
    return [(r, c) for r in range(n) for c in range(n) if valid_mask[r][c]]

def _board_key(valid_mask):
    try:
        return tuple(tuple(bool(x) for x in row) for row in valid_mask)
    except Exception:
        return tuple(tuple(bool(valid_mask[r][c]) for c in range(len(valid_mask[r]))) for r in range(len(valid_mask)))

def _compute_board_features(valid_mask):
    key = _board_key(valid_mask)
    if key in _CACHED:
        return _CACHED[key]

    cells = _all_valid(valid_mask)
    deg = {}
    for cell in cells:
        deg[cell] = len(_neighbors(cell, valid_mask))

    # In Havannah board, corners are the valid cells with degree 3.
    corners = [cell for cell in cells if deg[cell] == 3]

    # Sort corners cyclically by angle around board center for stable edge construction.
    rs = [r for r, c in cells]
    cs = [c for r, c in cells]
    cr = sum(rs) / len(rs)
    cc = sum(cs) / len(cs)
    corners_sorted = sorted(corners, key=lambda x: math.atan2(x[0] - cr, x[1] - cc))

    # Boundary cells are degree < 6; edge cells exclude corners.
    boundary = [cell for cell in cells if deg[cell] < 6]
    boundary_set = set(boundary)
    corner_set = set(corners_sorted)

    # Build graph on boundary excluding corners; connected components are the 6 edges.
    edge_cells = [cell for cell in boundary if cell not in corner_set]
    edge_set = set(edge_cells)
    seen = set()
    edges = []
    for start in edge_cells:
        if start in seen:
            continue
        comp = []
        dq = [start]
        seen.add(start)
        while dq:
            u = dq.pop()
            comp.append(u)
            for v in _neighbors(u, valid_mask):
                if v in edge_set and v not in seen:
                    seen.add(v)
                    dq.append(v)
        edges.append(comp)

    # Usually 6 edges. If not, fallback by grouping with nearest corner-pair separators later.
    edge_id = {}
    if len(edges) == 6:
        for i, comp in enumerate(edges):
            for cell in comp:
                edge_id[cell] = i
    else:
        # Fallback: classify boundary non-corners by rough direction from center into 6 sectors.
        for cell in edge_cells:
            ang = math.atan2(cell[0] - cr, cell[1] - cc)
            sector = int(((ang + math.pi) / (2 * math.pi)) * 6) % 6
            edge_id[cell] = sector
        edges = [[] for _ in range(6)]
        for cell, i in edge_id.items():
            edges[i].append(cell)

    corner_id = {cell: i for i, cell in enumerate(corners_sorted)}

    info = {
        "cells": cells,
        "cell_set": set(cells),
        "corners": corners_sorted,
        "corner_set": corner_set,
        "corner_id": corner_id,
        "edges": edges,
        "edge_id": edge_id,
        "center": min(cells, key=lambda x: (x[0]-cr)**2 + (x[1]-cc)**2),
        "center_float": (cr, cc),
    }
    _CACHED[key] = info
    return info

class DSU:
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def add(self, x):
        if x not in self.parent:
            self.parent[x] = x
            self.rank[x] = 0

    def find(self, x):
        p = self.parent[x]
        while p != self.parent[p]:
            self.parent[p] = self.parent[self.parent[p]]
            p = self.parent[p]
        self.parent[x] = p
        return p

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return ra
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1
        return ra

def _build_groups(stones, valid_mask, info):
    stone_set = set(stones)
    dsu = DSU()
    for s in stones:
        dsu.add(s)
    for s in stones:
        for t in _neighbors(s, valid_mask):
            if t in stone_set:
                dsu.union(s, t)

    groups = {}
    for s in stones:
        r = dsu.find(s)
        groups.setdefault(r, []).append(s)

    feats = {}
    for root, members in groups.items():
        cset = set()
        eset = set()
        for m in members:
            if m in info["corner_id"]:
                cset.add(info["corner_id"][m])
            eid = info["edge_id"].get(m, None)
            if eid is not None:
                eset.add(eid)
        feats[root] = (cset, eset)
    return dsu, stone_set, groups, feats

def _features_after_move(move, stones, valid_mask, info):
    # Compute corners/edges touched by the connected component containing move after placing it.
    myset = set(stones)
    myset.add(move)
    visited = {move}
    dq = deque([move])
    corners = set()
    edges = set()
    while dq:
        u = dq.popleft()
        if u in info["corner_id"]:
            corners.add(info["corner_id"][u])
        eid = info["edge_id"].get(u, None)
        if eid is not None:
            edges.add(eid)
        for v in _neighbors(u, valid_mask):
            if v in myset and v not in visited:
                visited.add(v)
                dq.append(v)
    return corners, edges, visited

def _is_immediate_bridge_or_fork(move, stones, valid_mask, info):
    corners, edges, _ = _features_after_move(move, stones, valid_mask, info)
    return (len(corners) >= 2) or (len(edges) >= 3)

def _occupied_set(me, opp):
    return set(me) | set(opp)

def _legal_moves(me, opp, valid_mask, info):
    occ = _occupied_set(me, opp)
    return [cell for cell in info["cells"] if cell not in occ]

def _dist2(a, b):
    return (a[0]-b[0])*(a[0]-b[0]) + (a[1]-b[1])*(a[1]-b[1])

def _score_move(move, me, opp, valid_mask, info, my_groups_data=None, opp_groups_data=None):
    occ = _occupied_set(me, opp)
    myset = set(me)
    oppset = set(opp)

    score = 0.0

    # Strong local connectivity
    nbrs = _neighbors(move, valid_mask)
    friendly = 0
    enemy = 0
    friend_roots = set()

    if my_groups_data is not None:
        my_dsu, _, _, my_feats = my_groups_data
    else:
        my_dsu, _, _, my_feats = _build_groups(me, valid_mask, info)

    for n in nbrs:
        if n in myset:
            friendly += 1
            if n in my_dsu.parent:
                friend_roots.add(my_dsu.find(n))
        elif n in oppset:
            enemy += 1

    score += 18.0 * friendly
    score += 22.0 * max(0, len(friend_roots) - 1)   # joining groups is valuable
    score += 3.0 * enemy  # contested cells matter

    # Features after move
    corners, edges, comp = _features_after_move(move, me, valid_mask, info)
    score += 45.0 * len(corners)
    score += 20.0 * len(edges)
    if len(corners) >= 2:
        score += 1000000.0
    if len(edges) >= 3:
        score += 1000000.0

    # Proximity to center, especially early
    center = info["center"]
    d2c = _dist2(move, center)
    total_stones = len(me) + len(opp)
    if total_stones < 10:
        score += max(0.0, 40.0 - 2.0 * d2c)
    elif total_stones < 30:
        score += max(0.0, 20.0 - 1.0 * d2c)
    else:
        score += max(0.0, 8.0 - 0.4 * d2c)

    # Slight preference for boundary progress later
    if total_stones >= 12:
        if move in info["corner_set"]:
            score += 8.0
        elif move in info["edge_id"]:
            score += 5.0

    # Two-step expansion potential
    second_ring = set()
    for n in nbrs:
        for m in _neighbors(n, valid_mask):
            if m not in occ and m != move:
                second_ring.add(m)
    score += 0.15 * len(second_ring)

    # Blocking value: if this move occupies a cell the opponent would use for immediate bridge/fork
    if _is_immediate_bridge_or_fork(move, opp, valid_mask, info):
        score += 200000.0

    # Tactical adjacency to opponent groups with many edge/corner claims
    if opp_groups_data is not None:
        opp_dsu, _, _, opp_feats = opp_groups_data
        touched_opp_roots = set()
        for n in nbrs:
            if n in oppset and n in opp_dsu.parent:
                touched_opp_roots.add(opp_dsu.find(n))
        for r in touched_opp_roots:
            cset, eset = opp_feats[r]
            score += 10.0 * len(cset) + 6.0 * len(eset)

    # Mild anti-isolation penalty
    if friendly == 0 and total_stones > 2:
        score -= 12.0

    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    info = _compute_board_features(valid_mask)
    legal = _legal_moves(me, opp, valid_mask, info)

    # Absolute safety fallback
    if not legal:
        # Should never happen in a legal game state, but return something valid-shaped.
        for r in range(len(valid_mask)):
            for c in range(len(valid_mask)):
                if valid_mask[r][c]:
                    return (r, c)
        return (0, 0)

    # Opening: center if available
    if len(me) + len(opp) == 0 and info["center"] in legal:
        return info["center"]

    # Immediate win
    for mv in legal:
        if _is_immediate_bridge_or_fork(mv, me, valid_mask, info):
            return mv

    # Immediate block of opponent win
    opp_wins = [mv for mv in legal if _is_immediate_bridge_or_fork(mv, opp, valid_mask, info)]
    if opp_wins:
        # Prefer one that also helps us most.
        my_groups_data = _build_groups(me, valid_mask, info)
        opp_groups_data = _build_groups(opp, valid_mask, info)
        best = max(opp_wins, key=lambda mv: _score_move(mv, me, opp, valid_mask, info, my_groups_data, opp_groups_data))
        return best

    my_groups_data = _build_groups(me, valid_mask, info)
    opp_groups_data = _build_groups(opp, valid_mask, info)

    # Evaluate all legal moves
    best_move = None
    best_score = -1e100
    center = info["center"]

    for mv in legal:
        sc = _score_move(mv, me, opp, valid_mask, info, my_groups_data, opp_groups_data)

        # Tiebreakers: closer to center, then lexicographic stability
        sc -= 0.001 * _dist2(mv, center)
        sc -= 0.000001 * (mv[0] * 100 + mv[1])

        if sc > best_score:
            best_score = sc
            best_move = mv

    if best_move is not None:
        return best_move

    # Fallback: nearest legal to center
    legal_sorted = sorted(legal, key=lambda x: (_dist2(x, center), x[0], x[1]))
    return legal_sorted[0]
