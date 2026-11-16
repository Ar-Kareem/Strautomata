
from collections import deque, defaultdict
from functools import lru_cache
import math

# Hex neighbors for the board embedding described in the prompt.
# For (r, c), neighbors are:
# (r-1, c), (r+1, c), (r-1, c-1), (r, c-1), (r, c+1), (r-1, c+1)
DIRS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    n = len(valid_mask)
    valid_cells = []
    occupied = set(me) | set(opp)

    for r in range(n):
        row = valid_mask[r]
        for c in range(n):
            if row[c]:
                valid_cells.append((r, c))

    legal = [cell for cell in valid_cells if cell not in occupied]
    if not legal:
        # Should never happen in a valid game, but always return something legal-looking.
        return 0, 0

    # Board geometry
    corners, edge_map, center = _board_info(valid_mask)

    me_set = set(me)
    opp_set = set(opp)

    # Opening: if no stones at all, take the cell closest to board center.
    if not me and not opp:
        return min(legal, key=lambda x: _dist2(x, center))

    # Immediate win for us?
    winning_moves = [m for m in legal if _wins_bridge_or_fork(me_set, m, valid_mask, corners, edge_map)]
    if winning_moves:
        return _best_tactical_choice(
            winning_moves, me_set, opp_set, valid_mask, corners, edge_map, center
        )

    # Immediate opponent win to block?
    opp_winning_moves = [m for m in legal if _wins_bridge_or_fork(opp_set, m, valid_mask, corners, edge_map)]
    if opp_winning_moves:
        # If there are multiple blocks, choose the one that also helps us most.
        return _best_tactical_choice(
            opp_winning_moves, me_set, opp_set, valid_mask, corners, edge_map, center
        )

    # Build component information once for heuristic scoring.
    me_comp_id, me_comp_data = _components_info(me_set, valid_mask, corners, edge_map)
    opp_comp_id, opp_comp_data = _components_info(opp_set, valid_mask, corners, edge_map)

    # Score all legal moves.
    best_move = legal[0]
    best_score = -10**18

    total_stones = len(me) + len(opp)
    opening_weight = 1.6 if total_stones < 12 else 0.7

    for m in legal:
        score = 0.0
        r, c = m

        nbrs = _neighbors(m, valid_mask)

        own_adj = [x for x in nbrs if x in me_set]
        opp_adj = [x for x in nbrs if x in opp_set]

        own_adj_count = len(own_adj)
        opp_adj_count = len(opp_adj)

        own_adj_comps = set(me_comp_id[x] for x in own_adj)
        opp_adj_comps = set(opp_comp_id[x] for x in opp_adj)

        # Central influence, especially in opening.
        score -= opening_weight * 0.22 * _dist2(m, center)

        # Prefer adjacency to our stones.
        score += 4.5 * own_adj_count

        # Prefer connecting multiple own groups.
        if own_adj_comps:
            score += 8.0 * (len(own_adj_comps) - 1)

        # Mildly reward contesting opponent stones.
        score += 1.8 * opp_adj_count
        if opp_adj_comps:
            score += 2.0 * min(2, len(opp_adj_comps))

        # Component growth / anchor potential for our side.
        own_corners, own_edges, own_size = _merged_component_features(
            m, me_set, me_comp_id, me_comp_data, corners, edge_map, valid_mask
        )
        score += 3.0 * min(6, own_size)
        score += 9.0 * len(own_corners)
        score += 4.5 * len(own_edges)
        score += 10.0 * max(0, len(own_corners) - 1)
        score += 6.0 * max(0, len(own_edges) - 1)
        if len(own_corners) >= 1 and len(own_edges) >= 1:
            score += 3.0
        if len(own_edges) >= 2:
            score += 5.0
        if len(own_edges) >= 3:
            score += 12.0
        if len(own_corners) >= 2:
            score += 20.0

        # Defensive denial: if opponent played here, how strong would it be?
        opp_corners, opp_edges, opp_size = _merged_component_features(
            m, opp_set, opp_comp_id, opp_comp_data, corners, edge_map, valid_mask
        )
        danger = (
            7.0 * len(opp_corners)
            + 4.0 * len(opp_edges)
            + 6.0 * max(0, len(opp_corners) - 1)
            + 5.0 * max(0, len(opp_edges) - 1)
            + 2.0 * min(6, opp_size)
        )
        score += 0.75 * danger

        # Slight preference for edge/corner contacts, but not too early.
        if m in corners:
            score += 3.0 if total_stones > 10 else 1.0
        elif m in edge_map:
            score += 1.5 if total_stones > 8 else 0.4

        # Small tie-breakers: nearer to our stones / nearer to opponents.
        if me_set:
            d_me = min(_hex_like_distance(m, s) for s in me_set)
            score -= 0.25 * d_me
        if opp_set:
            d_opp = min(_hex_like_distance(m, s) for s in opp_set)
            score -= 0.08 * d_opp

        # Last-resort tie-break toward center.
        score -= 1e-4 * _dist2(m, center)

        if score > best_score:
            best_score = score
            best_move = m

    # Safety: ensure legal
    if best_move in occupied or not valid_mask[best_move[0]][best_move[1]]:
        return legal[0]
    return best_move


def _dist2(a, center):
    return (a[0] - center[0]) ** 2 + (a[1] - center[1]) ** 2


def _hex_like_distance(a, b):
    # Works reasonably for this embedded hex grid.
    dr = a[0] - b[0]
    dc = a[1] - b[1]
    return max(abs(dr), abs(dc), abs(dr - dc))


def _neighbors(cell, valid_mask):
    n = len(valid_mask)
    r, c = cell
    out = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < n and 0 <= cc < n and valid_mask[rr][cc]:
            out.append((rr, cc))
    return out


def _mask_key(valid_mask):
    return tuple(tuple(bool(x) for x in row) for row in valid_mask)


@lru_cache(maxsize=8)
def _board_info_cached(mask_key):
    n = len(mask_key)
    valid = [(r, c) for r in range(n) for c in range(n) if mask_key[r][c]]

    # Degree among valid cells
    deg = {}
    for cell in valid:
        r, c = cell
        d = 0
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < n and 0 <= cc < n and mask_key[rr][cc]:
                d += 1
        deg[cell] = d

    boundary = [x for x in valid if deg[x] < 6]
    corners = [x for x in boundary if deg[x] == 3]

    # Fallback if corner detection ever fails on an unusual mask:
    if len(corners) != 6:
        # Use extreme points in six directions.
        scored = []
        for r, c in valid:
            scored.append(((r, c), (r, c, r + c, r - c)))
        candidates = set()
        candidates.add(min(valid, key=lambda x: (x[0], x[1])))
        candidates.add(max(valid, key=lambda x: (x[0], x[1])))
        candidates.add(min(valid, key=lambda x: (x[1], x[0])))
        candidates.add(max(valid, key=lambda x: (x[1], x[0])))
        candidates.add(min(valid, key=lambda x: (x[0] + x[1], x[0])))
        candidates.add(max(valid, key=lambda x: (x[0] - x[1], x[0])))
        corners = list(candidates)[:6]

    corner_set = set(corners)

    # Boundary graph: boundary cells adjacent on the hex grid.
    b_adj = {x: [] for x in boundary}
    boundary_set = set(boundary)
    for x in boundary:
        for y in _neighbors_maskkey(x, mask_key):
            if y in boundary_set:
                b_adj[x].append(y)

    # Traverse perimeter cycle starting at a corner.
    start = min(corners)
    order = [start]
    prev = None
    cur = start
    while True:
        nxts = [z for z in b_adj[cur] if z != prev]
        if not nxts:
            break
        if prev is None:
            # Deterministic first step.
            nxt = min(nxts)
        else:
            # On a simple cycle there should be exactly one forward choice.
            if len(nxts) == 1:
                nxt = nxts[0]
            else:
                # Prefer the one not already just visited.
                unseen = [z for z in nxts if z not in order]
                nxt = unseen[0] if unseen else nxts[0]
        if nxt == start:
            break
        if nxt in order:
            break
        order.append(nxt)
        prev, cur = cur, nxt

    # If traversal missed some boundary cells, try to complete by sorting around center.
    if len(order) < len(boundary):
        cr = sum(r for r, c in boundary) / len(boundary)
        cc = sum(c for r, c in boundary) / len(boundary)

        def ang(x):
            r, c = x
            return math.atan2(r - cr, c - cc)

        order = sorted(boundary, key=ang)

    # Find corners in cyclic order.
    ordered_corners = [x for x in order if x in corner_set]
    if len(ordered_corners) != 6:
        # Fallback deterministic order around center.
        cr = sum(r for r, c in corners) / len(corners)
        cc = sum(c for r, c in corners) / len(corners)
        ordered_corners = sorted(corners, key=lambda x: math.atan2(x[0] - cr, x[1] - cc))

    # Label edge segments between consecutive corners, excluding corners themselves.
    idx_in_order = {cell: i for i, cell in enumerate(order)}
    corner_indices = sorted(idx_in_order[c] for c in ordered_corners if c in idx_in_order)

    edge_map = {}
    if len(corner_indices) == 6 and len(order) >= 6:
        L = len(order)
        for edge_id in range(6):
            a = corner_indices[edge_id]
            b = corner_indices[(edge_id + 1) % 6]
            i = (a + 1) % L
            while i != b:
                edge_map[order[i]] = edge_id
                i = (i + 1) % L

    center = (
        sum(r for r, c in valid) / len(valid),
        sum(c for r, c in valid) / len(valid),
    )
    return tuple(corners), tuple(sorted(edge_map.items())), center


def _neighbors_maskkey(cell, mask_key):
    n = len(mask_key)
    r, c = cell
    out = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < n and 0 <= cc < n and mask_key[rr][cc]:
            out.append((rr, cc))
    return out


def _board_info(valid_mask):
    corners_t, edge_items_t, center = _board_info_cached(_mask_key(valid_mask))
    return set(corners_t), dict(edge_items_t), center


def _components_info(stones_set, valid_mask, corners, edge_map):
    comp_id = {}
    comp_data = []
    seen = set()
    cid = 0

    for s in stones_set:
        if s in seen:
            continue
        q = deque([s])
        seen.add(s)
        comp_id[s] = cid
        cells = []
        touched_corners = set()
        touched_edges = set()

        while q:
            x = q.popleft()
            cells.append(x)
            if x in corners:
                touched_corners.add(x)
            if x in edge_map:
                touched_edges.add(edge_map[x])

            for y in _neighbors(x, valid_mask):
                if y in stones_set and y not in seen:
                    seen.add(y)
                    comp_id[y] = cid
                    q.append(y)

        comp_data.append({
            "cells": cells,
            "size": len(cells),
            "corners": touched_corners,
            "edges": touched_edges,
        })
        cid += 1

    return comp_id, comp_data


def _wins_bridge_or_fork(stones_set, move, valid_mask, corners, edge_map):
    # Evaluate connected component formed by placing move.
    touched_corners = set()
    touched_edges = set()

    if move in corners:
        touched_corners.add(move)
    if move in edge_map:
        touched_edges.add(edge_map[move])

    seen_comp_ids = set()
    comp_id, comp_data = _components_info(stones_set, valid_mask, corners, edge_map)

    for nb in _neighbors(move, valid_mask):
        if nb in stones_set:
            cid = comp_id[nb]
            if cid not in seen_comp_ids:
                seen_comp_ids.add(cid)
                touched_corners |= comp_data[cid]["corners"]
                touched_edges |= comp_data[cid]["edges"]

    # Bridge: two corners
    if len(touched_corners) >= 2:
        return True
    # Fork: three edges (corners do not count as edges, already enforced by edge_map)
    if len(touched_edges) >= 3:
        return True

    return False


def _merged_component_features(move, stones_set, comp_id, comp_data, corners, edge_map, valid_mask):
    touched_corners = set()
    touched_edges = set()
    size = 1

    if move in corners:
        touched_corners.add(move)
    if move in edge_map:
        touched_edges.add(edge_map[move])

    used = set()
    for nb in _neighbors(move, valid_mask):
        if nb in stones_set:
            cid = comp_id[nb]
            if cid not in used:
                used.add(cid)
                data = comp_data[cid]
                touched_corners |= data["corners"]
                touched_edges |= data["edges"]
                size += data["size"]

    return touched_corners, touched_edges, size


def _best_tactical_choice(moves, me_set, opp_set, valid_mask, corners, edge_map, center):
    # Among tactical candidates, prefer ones that also improve our shape.
    me_comp_id, me_comp_data = _components_info(me_set, valid_mask, corners, edge_map)
    opp_comp_id, opp_comp_data = _components_info(opp_set, valid_mask, corners, edge_map)

    best = moves[0]
    best_score = -10**18
    for m in moves:
        score = 0.0
        own_corners, own_edges, own_size = _merged_component_features(
            m, me_set, me_comp_id, me_comp_data, corners, edge_map, valid_mask
        )
        opp_corners, opp_edges, opp_size = _merged_component_features(
            m, opp_set, opp_comp_id, opp_comp_data, corners, edge_map, valid_mask
        )
        score += 20.0 * len(own_corners) + 12.0 * len(own_edges) + 2.0 * own_size
        score += 8.0 * len(opp_corners) + 6.0 * len(opp_edges) + 1.0 * opp_size
        score -= 0.15 * _dist2(m, center)
        if score > best_score:
            best_score = score
            best = m
    return best
