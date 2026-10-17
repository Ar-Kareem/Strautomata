
from collections import deque, defaultdict
from typing import List, Tuple, Dict, Set

# ---------- Board analysis cache ----------

_CACHE = {}

def _valid_cells(valid_mask):
    n = len(valid_mask)
    cells = []
    for r in range(n):
        row = valid_mask[r]
        for c in range(n):
            if row[c]:
                cells.append((r, c))
    return cells

def _neighbors_of(cell, valid_set):
    r, c = cell
    cand = [
        (r - 1, c), (r + 1, c),
        (r, c - 1), (r, c + 1),
        (r - 1, c - 1), (r + 1, c + 1),
    ]
    return [x for x in cand if x in valid_set]

def _analyze_board(valid_mask):
    key = id(valid_mask)
    if key in _CACHE:
        return _CACHE[key]

    cells = _valid_cells(valid_mask)
    valid_set = set(cells)
    neighbors = {cell: _neighbors_of(cell, valid_set) for cell in cells}
    degree = {cell: len(neighbors[cell]) for cell in cells}

    boundary = [cell for cell in cells if degree[cell] < 6]
    boundary_set = set(boundary)
    corners = [cell for cell in boundary if degree[cell] == 3]
    corner_set = set(corners)

    # Build boundary graph
    bneigh = {cell: [x for x in neighbors[cell] if x in boundary_set] for cell in boundary}

    # Order corners and identify 6 edges by walking boundary cycle
    edge_id = {}
    ordered_corners = []

    if len(corners) == 6:
        start = min(corners)
        ordered_corners.append(start)
        prev = None
        curr = start

        # Choose one boundary direction arbitrarily
        nxt = min(bneigh[start])
        visited_corner_pairs = 0

        while visited_corner_pairs < 6:
            path = []
            p = curr
            q = nxt

            while q not in corner_set:
                path.append(q)
                q_nexts = [x for x in bneigh[q] if x != p]
                if not q_nexts:
                    break
                p, q = q, q_nexts[0]

            eid = visited_corner_pairs
            for cell in path:
                edge_id[cell] = eid

            curr = q
            ordered_corners.append(curr)
            visited_corner_pairs += 1
            if curr == start:
                break
            q_nexts = [x for x in bneigh[curr] if x != p]
            if not q_nexts:
                break
            nxt = q_nexts[0]

    # Fallback if ordering failed somehow: partition corners by position only not needed;
    # edge_id may remain partial, which is acceptable.
    info = {
        "cells": cells,
        "valid_set": valid_set,
        "neighbors": neighbors,
        "degree": degree,
        "boundary": boundary,
        "boundary_set": boundary_set,
        "corners": corners,
        "corner_set": corner_set,
        "edge_id": edge_id,
    }
    _CACHE[key] = info
    return info


# ---------- Geometry / utility ----------

def _hex_dist(a, b):
    # Works for this axial-like embedding:
    # map (r,c) -> cube-like (x=c, z=r, y=-x-z) up to linear transform.
    # For this board embedding, max of coordinate differences below is a good hex distance.
    r1, c1 = a
    r2, c2 = b
    dr = r1 - r2
    dc = c1 - c2
    return max(abs(dr), abs(dc), abs(dr - dc))

def _center_cell(info):
    target = (7, 7)
    cells = info["cells"]
    return min(cells, key=lambda x: (_hex_dist(x, target), abs(x[0] - 7) + abs(x[1] - 7), x))

def _occupied_set(me, opp):
    return set(me) | set(opp)

def _legal_moves(info, occ):
    return [cell for cell in info["cells"] if cell not in occ]

def _neighbor_count(cell, stone_set, neighbors):
    return sum((n in stone_set) for n in neighbors[cell])


# ---------- Component analysis ----------

def _components(stones: Set[Tuple[int, int]], info):
    neighbors = info["neighbors"]
    comp_id = {}
    comp_meta = []
    cid = 0
    for s in stones:
        if s in comp_id:
            continue
        q = deque([s])
        comp_id[s] = cid
        cells = []
        edges = set()
        corners = set()
        while q:
            x = q.popleft()
            cells.append(x)
            if x in info["corner_set"]:
                corners.add(x)
            eid = info["edge_id"].get(x)
            if eid is not None:
                edges.add(eid)
            for y in neighbors[x]:
                if y in stones and y not in comp_id:
                    comp_id[y] = cid
                    q.append(y)
        comp_meta.append({
            "cells": cells,
            "size": len(cells),
            "edges": edges,
            "corners": corners,
        })
        cid += 1
    return comp_id, comp_meta

def _component_from_move(stones: Set[Tuple[int, int]], move, info):
    # stones already includes move
    neighbors = info["neighbors"]
    q = deque([move])
    seen = {move}
    edges = set()
    corners = set()
    size = 0
    while q:
        x = q.popleft()
        size += 1
        if x in info["corner_set"]:
            corners.add(x)
        eid = info["edge_id"].get(x)
        if eid is not None:
            edges.add(eid)
        for y in neighbors[x]:
            if y in stones and y not in seen:
                seen.add(y)
                q.append(y)
    return size, edges, corners


# ---------- Win detection ----------

def _has_bridge_or_fork_after(stones: Set[Tuple[int, int]], move, info):
    _, edges, corners = _component_from_move(stones, move, info)
    if len(corners) >= 2:
        return True
    if len(edges) >= 3:
        return True
    return False

def _has_ring(stones: Set[Tuple[int, int]], info):
    # Ring exists iff some connected component of non-stone valid cells
    # does not touch boundary.
    valid_set = info["valid_set"]
    boundary = info["boundary"]
    neighbors = info["neighbors"]

    nonstones = valid_set - stones
    if not nonstones:
        return False

    seen = set()
    q = deque()

    for b in boundary:
        if b in nonstones and b not in seen:
            seen.add(b)
            q.append(b)

    while q:
        x = q.popleft()
        for y in neighbors[x]:
            if y in nonstones and y not in seen:
                seen.add(y)
                q.append(y)

    # Any non-stone cell unreachable from boundary is enclosed.
    return len(seen) < len(nonstones)

def _is_winning_move(player_stones: Set[Tuple[int, int]], move, info):
    if move in player_stones:
        return False
    stones = set(player_stones)
    stones.add(move)
    if _has_bridge_or_fork_after(stones, move, info):
        return True
    if _has_ring(stones, info):
        return True
    return False


# ---------- Tactical search ----------

def _find_immediate_wins(player_stones: Set[Tuple[int, int]], occ: Set[Tuple[int, int]], info):
    wins = []
    for mv in _legal_moves(info, occ):
        if _is_winning_move(player_stones, mv, info):
            wins.append(mv)
    return wins

def _frontier_moves(info, occ, radius_source):
    neighbors = info["neighbors"]
    cand = set()
    for s in radius_source:
        for n in neighbors.get(s, []):
            if n not in occ:
                cand.add(n)
    return cand

def _second_ring_moves(info, occ, source):
    neighbors = info["neighbors"]
    cand = set()
    for s in source:
        for n in neighbors.get(s, []):
            for m in neighbors.get(n, []):
                if m not in occ:
                    cand.add(m)
    return cand


# ---------- Heuristic evaluation ----------

def _score_move(move, me_set, opp_set, occ, info, my_comp_id, my_comp_meta, opp_comp_id, opp_comp_meta, opp_wins):
    neighbors = info["neighbors"]

    my_adj = [n for n in neighbors[move] if n in me_set]
    opp_adj = [n for n in neighbors[move] if n in opp_set]
    empty_adj = [n for n in neighbors[move] if n not in occ]

    score = 0.0

    # Immediate block
    if move in opp_wins:
        score += 50000.0

    # Local shape
    score += 18.0 * len(my_adj)
    score += 7.0 * len(opp_adj)
    score += 2.0 * len(empty_adj)

    # Merge own components
    touched_my = set(my_comp_id[n] for n in my_adj if n in my_comp_id)
    if touched_my:
        score += 12.0 * len(touched_my)
        score += sum(0.6 * my_comp_meta[cid]["size"] for cid in touched_my)
        union_edges = set()
        union_corners = set()
        for cid in touched_my:
            union_edges |= my_comp_meta[cid]["edges"]
            union_corners |= my_comp_meta[cid]["corners"]
        if move in info["corner_set"]:
            union_corners.add(move)
        eid = info["edge_id"].get(move)
        if eid is not None:
            union_edges.add(eid)
        score += 16.0 * len(union_edges)
        score += 20.0 * len(union_corners)
        if len(union_corners) >= 2:
            score += 500.0
        if len(union_edges) >= 3:
            score += 500.0
    else:
        # Starting/extending a new chain
        if move in info["corner_set"]:
            score += 25.0
        eid = info["edge_id"].get(move)
        if eid is not None:
            score += 14.0

    # Interfere with opponent connectivity
    touched_opp = set(opp_comp_id[n] for n in opp_adj if n in opp_comp_id)
    if touched_opp:
        score += 8.0 * len(touched_opp)
        for cid in touched_opp:
            score += 0.4 * opp_comp_meta[cid]["size"]
            score += 8.0 * len(opp_comp_meta[cid]["edges"])
            score += 10.0 * len(opp_comp_meta[cid]["corners"])

    # Centrality
    score -= 1.5 * _hex_dist(move, (7, 7))

    # Slight preference for cells with more mobility / connectivity
    score += 0.7 * info["degree"][move]

    return score


# ---------- Main policy ----------

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    info = _analyze_board(valid_mask)
    occ = _occupied_set(me, opp)
    legal = _legal_moves(info, occ)

    # Absolute safety: always return a legal move
    if not legal:
        # Should never happen in a valid game state, but return something valid if possible.
        for cell in info["cells"]:
            if valid_mask[cell[0]][cell[1]]:
                return cell
        return (0, 0)

    me_set = set(me)
    opp_set = set(opp)

    # Opening
    if not me and not opp:
        center = _center_cell(info)
        if center not in occ:
            return center
        return legal[0]

    # 1) Immediate winning move
    my_wins = _find_immediate_wins(me_set, occ, info)
    if my_wins:
        center = (7, 7)
        return min(my_wins, key=lambda x: (_hex_dist(x, center), -info["degree"][x], x))

    # 2) Immediate block of opponent winning move
    opp_wins = set(_find_immediate_wins(opp_set, occ, info))
    if opp_wins:
        # If multiple winning threats exist, pick the block that also gives best shape.
        my_comp_id, my_comp_meta = _components(me_set, info)
        opp_comp_id, opp_comp_meta = _components(opp_set, info)
        best = None
        best_score = float("-inf")
        for mv in opp_wins:
            if mv not in occ:
                sc = _score_move(mv, me_set, opp_set, occ, info,
                                 my_comp_id, my_comp_meta, opp_comp_id, opp_comp_meta, opp_wins)
                # Prefer also being adjacent to our stones
                if _is_winning_move(me_set, mv, info):
                    sc += 100000.0
                if sc > best_score:
                    best_score = sc
                    best = mv
        if best is not None:
            return best

    # 3) Heuristic candidate set
    frontier = _frontier_moves(info, occ, me_set | opp_set)
    if not frontier:
        frontier = set()

    if len(frontier) < 12:
        frontier |= _second_ring_moves(info, occ, me_set | opp_set)

    center = _center_cell(info)
    if center not in occ:
        frontier.add(center)

    # Always include neighbors of our stones and opponent stones
    frontier |= _frontier_moves(info, occ, me_set)
    frontier |= _frontier_moves(info, occ, opp_set)

    # Include all tactical blocks if any existed
    frontier |= opp_wins

    # Fallback if too small
    if not frontier:
        frontier = set(legal)

    # Build component info once
    my_comp_id, my_comp_meta = _components(me_set, info)
    opp_comp_id, opp_comp_meta = _components(opp_set, info)

    best = None
    best_score = float("-inf")

    # First pass over candidate frontier
    for mv in frontier:
        if mv in occ:
            continue
        sc = _score_move(mv, me_set, opp_set, occ, info,
                         my_comp_id, my_comp_meta, opp_comp_id, opp_comp_meta, opp_wins)

        # Bonus if this move creates a direct tactical threat / progress
        tmp_me = set(me_set)
        tmp_me.add(mv)
        _, e, c = _component_from_move(tmp_me, mv, info)
        if len(c) == 1:
            sc += 20.0
        if len(e) == 2:
            sc += 25.0
        if len(c) >= 2 or len(e) >= 3:
            sc += 1000.0

        # Small anti-ring defense: occupy cells with many opponent adjacencies
        opp_adj = _neighbor_count(mv, opp_set, info["neighbors"])
        if opp_adj >= 3:
            sc += 8.0 * opp_adj

        if sc > best_score:
            best_score = sc
            best = mv

    # Safety fallback
    if best is None or best in occ or best not in info["valid_set"]:
        # Prefer legal move nearest center
        return min(legal, key=lambda x: (_hex_dist(x, center), -info["degree"][x], x))

    return best
