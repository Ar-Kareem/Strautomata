
from collections import deque
from typing import List, Tuple, Dict, Set

# Hex-neighbor offsets for the board embedding described in the prompt.
NEI = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]

_META_CACHE = {}


def _in_bounds(r: int, c: int, n: int) -> bool:
    return 0 <= r < n and 0 <= c < n


def _neighbors(cell, valid_set, n):
    r, c = cell
    out = []
    for dr, dc in NEI:
        nr, nc = r + dr, c + dc
        if _in_bounds(nr, nc, n) and (nr, nc) in valid_set:
            out.append((nr, nc))
    return out


def _compute_meta(valid_mask):
    # Cache by shape + contents.
    key = (tuple(valid_mask.shape), valid_mask.tobytes())
    if key in _META_CACHE:
        return _META_CACHE[key]

    n = valid_mask.shape[0]
    valid_set = set()
    for r in range(n):
        for c in range(n):
            if bool(valid_mask[r][c]):
                valid_set.add((r, c))

    neigh = {}
    deg = {}
    for cell in valid_set:
        ns = _neighbors(cell, valid_set, n)
        neigh[cell] = ns
        deg[cell] = len(ns)

    boundary = {cell for cell in valid_set if deg[cell] < 6}
    corners = [cell for cell in boundary if deg[cell] == 3]

    # Fallback if degree-based corner detection ever fails.
    if len(corners) != 6:
        # Pick 6 extreme boundary points by simple geometric proxies.
        # This should almost never be needed on a standard Havannah mask.
        b = list(boundary)
        if not b:
            corners = []
        else:
            # Axial-like embedding for angle sorting.
            pts = []
            cr = sum(r for r, c in b) / len(b)
            cc = sum(c + 0.5 * r for r, c in b) / len(b)
            import math
            for cell in b:
                r, c = cell
                x = c + 0.5 * r
                y = r
                ang = math.atan2(y - cr, x - cc)
                pts.append((ang, cell))
            pts.sort()
            # take six roughly evenly spaced boundary points
            corners = [pts[(i * len(pts)) // 6][1] for i in range(6)]

    b_adj = {cell: [x for x in neigh[cell] if x in boundary] for cell in boundary}

    # Traverse the boundary cycle.
    boundary_order = []
    if corners:
        start = min(corners)
        if b_adj[start]:
            prev = None
            cur = start
            seen = set()
            while True:
                boundary_order.append(cur)
                seen.add(cur)
                nxts = b_adj[cur]
                if prev is None:
                    nxt = min(nxts)
                else:
                    # On a simple cycle, choose the neighbor that's not prev.
                    if len(nxts) == 1:
                        nxt = nxts[0]
                    else:
                        nxt = nxts[0] if nxts[1] == prev else nxts[1]
                prev, cur = cur, nxt
                if cur == start:
                    break
                if cur in seen:
                    break

    # Order corners by appearance on boundary cycle.
    corner_index = {}
    if boundary_order:
        pos = {cell: i for i, cell in enumerate(boundary_order)}
        corners = sorted(corners, key=lambda x: pos.get(x, 10**9))
    corner_id = {cell: i for i, cell in enumerate(corners)}

    edge_id = {}
    if boundary_order and len(corners) == 6:
        pos = {cell: i for i, cell in enumerate(boundary_order)}
        m = len(boundary_order)
        corner_positions = [pos[c] for c in corners]
        for i in range(6):
            a = corner_positions[i]
            b = corner_positions[(i + 1) % 6]
            j = (a + 1) % m
            while j != b:
                edge_id[boundary_order[j]] = i
                j = (j + 1) % m

    meta = {
        "n": n,
        "valid_set": valid_set,
        "neigh": neigh,
        "deg": deg,
        "boundary": boundary,
        "corners": corners,
        "corner_id": corner_id,
        "edge_id": edge_id,
        "center_r": sum(r for r, c in valid_set) / max(1, len(valid_set)),
        "center_c": sum(c for r, c in valid_set) / max(1, len(valid_set)),
    }
    _META_CACHE[key] = meta
    return meta


def _component_info(stones: Set[Tuple[int, int]], meta):
    neigh = meta["neigh"]
    corner_id = meta["corner_id"]
    edge_id = meta["edge_id"]

    comp_id = {}
    comp_touches = []
    cid = 0

    for s in stones:
        if s in comp_id:
            continue
        q = deque([s])
        comp_id[s] = cid
        corners = set()
        edges = set()
        cells = []
        while q:
            x = q.popleft()
            cells.append(x)
            if x in corner_id:
                corners.add(corner_id[x])
            if x in edge_id:
                edges.add(edge_id[x])
            for y in neigh[x]:
                if y in stones and y not in comp_id:
                    comp_id[y] = cid
                    q.append(y)
        comp_touches.append((corners, edges, cells))
        cid += 1

    return comp_id, comp_touches


def _touches_after_move(stones: Set[Tuple[int, int]], move, meta):
    # BFS only through the component containing move.
    neigh = meta["neigh"]
    corner_id = meta["corner_id"]
    edge_id = meta["edge_id"]

    q = deque([move])
    seen = {move}
    corners = set()
    edges = set()

    while q:
        x = q.popleft()
        if x in corner_id:
            corners.add(corner_id[x])
        if x in edge_id:
            edges.add(edge_id[x])
        for y in neigh[x]:
            if y in stones and y not in seen:
                seen.add(y)
                q.append(y)
    return corners, edges


def _has_ring(stones: Set[Tuple[int, int]], meta) -> bool:
    # Ring test via enclosed non-stone component:
    # if any connected component of valid cells not occupied by this player
    # fails to reach the boundary, then a ring exists.
    valid_set = meta["valid_set"]
    neigh = meta["neigh"]
    boundary = meta["boundary"]

    nonstones = valid_set - stones
    seen = set()
    for cell in nonstones:
        if cell in seen:
            continue
        q = deque([cell])
        seen.add(cell)
        reaches_boundary = cell in boundary
        while q:
            x = q.popleft()
            for y in neigh[x]:
                if y in nonstones and y not in seen:
                    seen.add(y)
                    if y in boundary:
                        reaches_boundary = True
                    q.append(y)
        if not reaches_boundary:
            return True
    return False


def _is_winning_move(stones: Set[Tuple[int, int]], move, meta) -> bool:
    if move in stones:
        return False
    stones2 = set(stones)
    stones2.add(move)

    corners, edges = _touches_after_move(stones2, move, meta)
    if len(corners) >= 2:
        return True  # bridge
    if len(edges) >= 3:
        return True  # fork
    if _has_ring(stones2, meta):
        return True  # ring
    return False


def _score_move(
    move,
    me_set: Set[Tuple[int, int]],
    opp_set: Set[Tuple[int, int]],
    me_comp_id,
    me_comp_info,
    opp_comp_id,
    opp_comp_info,
    meta,
):
    neigh = meta["neigh"]
    r, c = move
    score = 0.0

    # Mild center preference.
    dr = r - meta["center_r"]
    dc = c - meta["center_c"]
    score -= 0.12 * (dr * dr + dc * dc)

    my_n = 0
    opp_n = 0
    my_comps = set()
    opp_comps = set()

    for nb in neigh[move]:
        if nb in me_set:
            my_n += 1
            my_comps.add(me_comp_id[nb])
        elif nb in opp_set:
            opp_n += 1
            opp_comps.add(opp_comp_id[nb])

    # Connectivity and shape.
    score += 2.8 * my_n
    score += 1.4 * opp_n
    if len(my_comps) >= 2:
        score += 4.5 * (len(my_comps) - 1)
    if len(opp_comps) >= 2:
        score += 1.8 * (len(opp_comps) - 1)

    # Estimate side/corner reach after this move by merging adjacent friendly comps.
    merged_corners = set()
    merged_edges = set()
    if move in meta["corner_id"]:
        merged_corners.add(meta["corner_id"][move])
    if move in meta["edge_id"]:
        merged_edges.add(meta["edge_id"][move])

    for cid in my_comps:
        cs, es, _ = me_comp_info[cid]
        merged_corners |= cs
        merged_edges |= es

    score += 2.2 * len(merged_edges)
    score += 3.0 * len(merged_corners)

    # Tactical local pattern bonuses.
    if my_n >= 2:
        score += 1.5
    if my_n >= 3:
        score += 2.5
    if opp_n >= 2:
        score += 0.8

    # Empty-neighborhood flexibility.
    empties = 0
    for nb in neigh[move]:
        if nb not in me_set and nb not in opp_set:
            empties += 1
    score += 0.15 * empties

    return score


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    meta = _compute_meta(valid_mask)
    valid_set = meta["valid_set"]

    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set

    legal = [cell for cell in valid_set if cell not in occupied]
    if not legal:
        # Should not happen in a valid game state, but never crash.
        for r in range(valid_mask.shape[0]):
            for c in range(valid_mask.shape[1]):
                if bool(valid_mask[r][c]) and (r, c) not in occupied:
                    return (r, c)
        return (0, 0)

    # Opening: center-ish if available.
    if not me and not opp:
        best = min(
            legal,
            key=lambda x: (x[0] - meta["center_r"]) ** 2 + (x[1] - meta["center_c"]) ** 2,
        )
        return best

    # 1) Immediate winning move.
    winning_moves = []
    for mv in legal:
        if _is_winning_move(me_set, mv, meta):
            winning_moves.append(mv)
    if winning_moves:
        me_comp_id, me_comp_info = _component_info(me_set, meta)
        opp_comp_id, opp_comp_info = _component_info(opp_set, meta)
        return max(
            winning_moves,
            key=lambda mv: _score_move(
                mv, me_set, opp_set,
                me_comp_id, me_comp_info,
                opp_comp_id, opp_comp_info,
                meta
            )
        )

    # 2) Block opponent immediate wins.
    opp_wins = []
    for mv in legal:
        if _is_winning_move(opp_set, mv, meta):
            opp_wins.append(mv)
    if opp_wins:
        me_comp_id, me_comp_info = _component_info(me_set, meta)
        opp_comp_id, opp_comp_info = _component_info(opp_set, meta)
        return max(
            opp_wins,
            key=lambda mv: _score_move(
                mv, me_set, opp_set,
                me_comp_id, me_comp_info,
                opp_comp_id, opp_comp_info,
                meta
            )
        )

    # 3) Heuristic move selection.
    me_comp_id, me_comp_info = _component_info(me_set, meta)
    opp_comp_id, opp_comp_info = _component_info(opp_set, meta)

    best_move = None
    best_score = None
    for mv in legal:
        s = _score_move(
            mv, me_set, opp_set,
            me_comp_id, me_comp_info,
            opp_comp_id, opp_comp_info,
            meta
        )
        if best_score is None or s > best_score:
            best_score = s
            best_move = mv

    if best_move is not None:
        return best_move

    # 4) Absolute fallback: first legal move.
    return legal[0]
