
from collections import deque
from functools import lru_cache
import math

# Module-level cache for board geometry
_GEOM_CACHE = {}


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    try:
        geom = _get_geometry(valid_mask)
        legal = [p for p in geom["valid_cells"] if p not in set(me) and p not in set(opp)]
        if not legal:
            # Should never happen in a valid game state, but keep it safe.
            for r, c in geom["valid_cells"]:
                return (r, c)

        me_set = set(me)
        opp_set = set(opp)

        # 1) Immediate winning move
        for mv in legal:
            if _is_winning_move(mv, me_set, opp_set, geom):
                return mv

        # 2) Immediate block of opponent winning move
        opp_wins = []
        for mv in legal:
            if _is_winning_move(mv, opp_set, me_set, geom):
                opp_wins.append(mv)
        if opp_wins:
            # If several blocks exist, choose the best-looking one for us.
            best_block = None
            best_score = -10**18
            for mv in opp_wins:
                sc = _heuristic_score(mv, me_set, opp_set, geom) + 50000
                if sc > best_score:
                    best_score = sc
                    best_block = mv
            return best_block

        # 3) Heuristic move selection
        best_move = None
        best_score = -10**18
        for mv in legal:
            sc = _heuristic_score(mv, me_set, opp_set, geom)
            if sc > best_score:
                best_score = sc
                best_move = mv
        if best_move is not None:
            return best_move

        # Final fallback: first legal move
        return legal[0]

    except Exception:
        # Absolute safety fallback: return first legal move we can find.
        n = len(valid_mask)
        occ = set(me) | set(opp)
        for r in range(n):
            for c in range(n):
                if valid_mask[r][c] and (r, c) not in occ:
                    return (r, c)
        return (0, 0)


def _get_geometry(valid_mask):
    key = id(valid_mask)
    cached = _GEOM_CACHE.get(key)
    if cached is not None:
        return cached

    n = len(valid_mask)
    valid_cells = []
    valid_set = set()
    for r in range(n):
        for c in range(n):
            if valid_mask[r][c]:
                valid_cells.append((r, c))
                valid_set.add((r, c))

    def nbrs(cell):
        r, c = cell
        cand = [
            (r - 1, c),
            (r + 1, c),
            (r, c - 1),
            (r, c + 1),
            (r - 1, c + 1),
            (r + 1, c - 1),
        ]
        return [x for x in cand if x in valid_set]

    neighbors = {p: nbrs(p) for p in valid_cells}
    degree = {p: len(neighbors[p]) for p in valid_cells}

    boundary = [p for p in valid_cells if degree[p] < 6]
    boundary_set = set(boundary)

    # Corners on a Havannah hex board are exactly the boundary cells with degree 3.
    corners = [p for p in boundary if degree[p] <= 3]

    # Fallback if board representation is unusual.
    if len(corners) != 6:
        corners = _fallback_find_corners(boundary, neighbors)

    corner_set = set(corners)

    boundary_neighbors = {
        p: [q for q in neighbors[p] if q in boundary_set] for p in boundary
    }

    # Order boundary in a cycle.
    boundary_cycle = _build_boundary_cycle(boundary, boundary_neighbors)

    # Assign each non-corner boundary cell to one of 6 edges between corners.
    edge_of = {}
    if boundary_cycle and len(corners) == 6:
        corner_positions = [i for i, p in enumerate(boundary_cycle) if p in corner_set]
        corner_positions.sort()
        m = len(boundary_cycle)
        for eid in range(len(corner_positions)):
            a = corner_positions[eid]
            b = corner_positions[(eid + 1) % len(corner_positions)]
            i = (a + 1) % m
            while i != b:
                p = boundary_cycle[i]
                if p not in corner_set:
                    edge_of[p] = eid
                i = (i + 1) % m

    # Center estimate: average of valid cells
    cr = sum(r for r, _ in valid_cells) / max(1, len(valid_cells))
    cc = sum(c for _, c in valid_cells) / max(1, len(valid_cells))

    geom = {
        "n": n,
        "valid_cells": valid_cells,
        "valid_set": valid_set,
        "neighbors": neighbors,
        "degree": degree,
        "boundary": boundary,
        "boundary_set": boundary_set,
        "corners": corners,
        "corner_set": corner_set,
        "edge_of": edge_of,
        "center": (cr, cc),
    }
    _GEOM_CACHE[key] = geom
    return geom


def _fallback_find_corners(boundary, neighbors):
    # Robust fallback: pick 6 extreme points in skewed coordinates.
    # Hex-like coordinates induced by neighbors:
    # Use transforms that expose the six "directions".
    if not boundary:
        return []
    scored = []
    for p in boundary:
        r, c = p
        scored.append((
            p,
            r,          # south
            -r,         # north
            c,          # east-ish
            -c,         # west-ish
            r + c,      # diagonal
            -(r + c),
        ))
    picks = set()
    for k in range(1, 7):
        best = max(scored, key=lambda x: x[k])[0]
        picks.add(best)
    corners = list(picks)
    # If still not 6, pad by low-degree boundary cells.
    boundary_sorted = sorted(boundary, key=lambda p: (len(neighbors[p]), p[0], p[1]))
    for p in boundary_sorted:
        if len(corners) >= 6:
            break
        if p not in picks:
            corners.append(p)
    return corners[:6]


def _build_boundary_cycle(boundary, boundary_neighbors):
    if not boundary:
        return []

    start = min(boundary)
    nbrs = boundary_neighbors[start]
    if not nbrs:
        return [start]
    prev = None
    cur = start
    cycle = []

    # Traverse until repeat or dead-end.
    seen_pairs = set()
    while True:
        cycle.append(cur)
        nxts = boundary_neighbors[cur]
        nxt = None
        for x in nxts:
            if x != prev:
                nxt = x
                break
        if nxt is None:
            break
        pair = (cur, nxt)
        if pair in seen_pairs:
            break
        seen_pairs.add(pair)
        prev, cur = cur, nxt
        if cur == start:
            break

    # If not all boundary nodes were visited, try opposite initial choice.
    if len(set(cycle)) < len(boundary):
        start = min(boundary)
        nbrs = boundary_neighbors[start]
        if len(nbrs) >= 2:
            prev = nbrs[0]
            cur = start
            cycle = []
            seen_pairs = set()
            while True:
                cycle.append(cur)
                nxts = boundary_neighbors[cur]
                nxt = None
                for x in nxts:
                    if x != prev:
                        nxt = x
                        break
                if nxt is None:
                    break
                pair = (cur, nxt)
                if pair in seen_pairs:
                    break
                seen_pairs.add(pair)
                prev, cur = cur, nxt
                if cur == start:
                    break

    # Deduplicate while preserving order if needed.
    out = []
    seen = set()
    for p in cycle:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def _is_winning_move(move, stones_set, opp_set, geom):
    new_stones = set(stones_set)
    new_stones.add(move)
    return _has_bridge_or_fork(new_stones, move, geom) or _has_ring(new_stones, geom)


def _has_bridge_or_fork(stones_set, start, geom):
    neighbors = geom["neighbors"]
    corner_set = geom["corner_set"]
    edge_of = geom["edge_of"]

    q = deque([start])
    seen = {start}
    touched_corners = set()
    touched_edges = set()

    while q:
        p = q.popleft()
        if p in corner_set:
            touched_corners.add(p)
        eid = edge_of.get(p)
        if eid is not None:
            touched_edges.add(eid)
        for nb in neighbors[p]:
            if nb in stones_set and nb not in seen:
                seen.add(nb)
                q.append(nb)

    if len(touched_corners) >= 2:
        return True
    if len(touched_edges) >= 3:
        return True
    return False


def _has_ring(stones_set, geom):
    # Exact ring test via complement connectivity:
    # if any connected component of cells not occupied by player
    # does not touch the board boundary, then the player has a ring.
    valid_cells = geom["valid_cells"]
    valid_set = geom["valid_set"]
    neighbors = geom["neighbors"]
    boundary_set = geom["boundary_set"]

    non_player = [p for p in valid_cells if p not in stones_set]
    non_player_set = set(non_player)
    seen = set()

    for p in non_player:
        if p in seen:
            continue
        q = deque([p])
        seen.add(p)
        touches_boundary = (p in boundary_set)
        size = 0
        while q:
            x = q.popleft()
            size += 1
            for nb in neighbors[x]:
                if nb in non_player_set and nb not in seen:
                    seen.add(nb)
                    q.append(nb)
                    if nb in boundary_set:
                        touches_boundary = True
        if not touches_boundary:
            # Enclosed region found
            return True
    return False


def _heuristic_score(move, me_set, opp_set, geom):
    neighbors = geom["neighbors"]
    center_r, center_c = geom["center"]
    corner_set = geom["corner_set"]
    edge_of = geom["edge_of"]

    r, c = move
    nbs = neighbors[move]

    my_adj = sum((nb in me_set) for nb in nbs)
    opp_adj = sum((nb in opp_set) for nb in nbs)
    empty_adj = len(nbs) - my_adj - opp_adj

    # Centrality
    dist_center = abs(r - center_r) + abs(c - center_c)
    score = -1.8 * dist_center

    # Connection preference
    score += 18 * my_adj
    score += 4 * len([nb for nb in nbs if nb in me_set])

    # Prefer extending multiple second-order friendly links
    second = set()
    for nb in nbs:
        if nb in me_set:
            for x in neighbors[nb]:
                if x not in me_set and x != move:
                    second.add(x)
    score += 0.4 * len(second)

    # Light blocking
    score += 9 * opp_adj

    # Tactical shape: avoid isolated edge-clinging in opening unless useful
    if move in corner_set:
        score += 6
    if move in edge_of:
        score += 2

    # Estimate bridge/fork potential from resulting component
    comp = _component_after_move(move, me_set, geom)
    touched_corners = set()
    touched_edges = set()
    for p in comp:
        if p in corner_set:
            touched_corners.add(p)
        eid = edge_of.get(p)
        if eid is not None:
            touched_edges.add(eid)
    score += 24 * len(touched_corners)
    score += 13 * len(touched_edges)
    score += 1.5 * len(comp)

    # Pressure near opponent groups
    opp_comp_sizes = []
    seen = set()
    for nb in nbs:
        if nb in opp_set and nb not in seen:
            comp_opp = _collect_component(nb, opp_set, geom, seen)
            opp_comp_sizes.append(len(comp_opp))
    score += 2.5 * sum(opp_comp_sizes)

    # Ring-ish local patterns: more occupied neighborhood often helps
    occupied_adj = my_adj + opp_adj
    if occupied_adj >= 4:
        score += 5
    if my_adj >= 2 and opp_adj >= 1:
        score += 3

    # Small preference to moves that create immediate threats next turn
    temp_me = set(me_set)
    temp_me.add(move)
    threats = 0
    for nb in nbs:
        if nb not in temp_me and nb not in opp_set:
            if _has_bridge_or_fork(temp_me | {nb}, nb, geom):
                threats += 1
    score += 7 * threats

    # Mild anti-suicidal crowding with no support
    if my_adj == 0 and opp_adj == 0:
        score -= 8
    elif my_adj == 0 and dist_center > 5:
        score -= 6

    return score


def _component_after_move(move, me_set, geom):
    stones = set(me_set)
    stones.add(move)
    return _collect_component(move, stones, geom, set())


def _collect_component(start, stones_set, geom, global_seen):
    q = deque([start])
    comp = []
    global_seen.add(start)
    while q:
        p = q.popleft()
        comp.append(p)
        for nb in geom["neighbors"][p]:
            if nb in stones_set and nb not in global_seen:
                global_seen.add(nb)
                q.append(nb)
    return comp
