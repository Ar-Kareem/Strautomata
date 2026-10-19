
from collections import deque, defaultdict
import math
import random

# Hex directions for the coordinate system described in the prompt.
_DIRS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (-1, 1), (0, 1)]

_GEOM_CACHE = {}


def _mask_key(valid_mask):
    try:
        return (len(valid_mask), len(valid_mask[0]), tuple(tuple(bool(x) for x in row) for row in valid_mask))
    except Exception:
        return None


def _is_valid(valid_mask, r, c):
    try:
        return bool(valid_mask[r][c])
    except Exception:
        return False


def _compute_geometry(valid_mask):
    key = _mask_key(valid_mask)
    if key in _GEOM_CACHE:
        return _GEOM_CACHE[key]

    n = len(valid_mask)
    m = len(valid_mask[0])

    cells = []
    valid_set = set()
    for r in range(n):
        for c in range(m):
            if _is_valid(valid_mask, r, c):
                cells.append((r, c))
                valid_set.add((r, c))

    neigh = {}
    for r, c in cells:
        ns = []
        for dr, dc in _DIRS:
            nr, nc = r + dr, c + dc
            if (nr, nc) in valid_set:
                ns.append((nr, nc))
        neigh[(r, c)] = ns

    boundary = {p for p in cells if len(neigh[p]) < 6}

    # On a normal Havannah hex board, corners are boundary cells with the fewest valid neighbours.
    if boundary:
        min_deg = min(len(neigh[p]) for p in boundary)
        corners = {p for p in boundary if len(neigh[p]) == min_deg}
    else:
        corners = set()

    # If something unusual happens, fall back to six angularly extreme boundary cells.
    if len(corners) != 6 and boundary:
        cr = sum(r for r, c in cells) / float(len(cells))
        cc = sum(c for r, c in cells) / float(len(cells))
        ordered = sorted(boundary, key=lambda p: math.atan2(p[0] - cr, p[1] - cc))
        corners = set()
        step = max(1, len(ordered) // 6)
        for i in range(6):
            corners.add(ordered[(i * step) % len(ordered)])
        # Trim if needed
        if len(corners) > 6:
            corners = set(list(corners)[:6])

    # Boundary graph.
    b_adj = {p: [q for q in neigh[p] if q in boundary] for p in boundary}

    # Assign the six edge IDs to boundary non-corner cells by walking between corners.
    edge_id = {}
    if len(corners) >= 2:
        cid = 0
        visited_edges = set()

        # Boundary cells usually form a cycle. Start walks from each corner along boundary.
        for corner in list(corners):
            for nxt in b_adj.get(corner, []):
                ekey = tuple(sorted([corner, nxt]))
                if ekey in visited_edges:
                    continue

                path = []
                prev, cur = corner, nxt
                visited_edges.add(ekey)

                while cur not in corners:
                    path.append(cur)
                    candidates = [x for x in b_adj.get(cur, []) if x != prev]
                    if not candidates:
                        break
                    # Prefer staying on boundary.
                    nxt2 = candidates[0]
                    ekey2 = tuple(sorted([cur, nxt2]))
                    if ekey2 in visited_edges:
                        break
                    visited_edges.add(ekey2)
                    prev, cur = cur, nxt2

                if path:
                    for p in path:
                        if p not in edge_id:
                            edge_id[p] = cid % 6
                    cid += 1

    # Fallback edge assignment by angle if traversal did not cover all boundary non-corners.
    missing = [p for p in boundary if p not in corners and p not in edge_id]
    if missing:
        cr = sum(r for r, c in cells) / float(len(cells))
        cc = sum(c for r, c in cells) / float(len(cells))
        for p in missing:
            ang = math.atan2(p[0] - cr, p[1] - cc)
            if ang < 0:
                ang += 2 * math.pi
            edge_id[p] = int((ang / (2 * math.pi)) * 6) % 6

    center = (
        sum(r for r, c in cells) / float(len(cells)),
        sum(c for r, c in cells) / float(len(cells)),
    )

    geom = {
        "cells": cells,
        "valid_set": valid_set,
        "neigh": neigh,
        "boundary": boundary,
        "corners": corners,
        "edge_id": edge_id,
        "center": center,
        "n": n,
        "m": m,
    }

    if key is not None:
        _GEOM_CACHE[key] = geom
    return geom


def _component_info(stones, geom):
    stones = set(stones)
    neigh = geom["neigh"]
    corners = geom["corners"]
    edge_id = geom["edge_id"]

    seen = set()
    infos = []

    for p in stones:
        if p in seen:
            continue

        q = deque([p])
        seen.add(p)
        comp = []
        comp_corners = set()
        comp_edges = set()

        while q:
            x = q.popleft()
            comp.append(x)
            if x in corners:
                comp_corners.add(x)
            if x in edge_id:
                comp_edges.add(edge_id[x])

            for y in neigh.get(x, []):
                if y in stones and y not in seen:
                    seen.add(y)
                    q.append(y)

        infos.append((comp, comp_corners, comp_edges))

    return infos


def _has_bridge_or_fork(stones, geom):
    for comp, comp_corners, comp_edges in _component_info(stones, geom):
        if len(comp_corners) >= 2:
            return True
        if len(comp_edges) >= 3:
            return True
    return False


def _has_ring(stones, occupied_other, geom):
    """
    A ring exists if there is a connected region of non-player cells that does
    not touch the board boundary. This detects the standard Havannah enclosure.
    """
    mine = set(stones)
    valid_set = geom["valid_set"]
    boundary = geom["boundary"]
    neigh = geom["neigh"]

    non_mine = valid_set - mine
    seen = set()

    for p in non_mine:
        if p in seen:
            continue

        touches_boundary = False
        q = deque([p])
        seen.add(p)

        while q:
            x = q.popleft()
            if x in boundary:
                touches_boundary = True

            for y in neigh.get(x, []):
                if y in non_mine and y not in seen:
                    seen.add(y)
                    q.append(y)

        if not touches_boundary:
            return True

    return False


def _is_win_after(move, stones, other, geom):
    new_stones = set(stones)
    new_stones.add(move)
    if _has_bridge_or_fork(new_stones, geom):
        return True
    if _has_ring(new_stones, set(other), geom):
        return True
    return False


def _legal_moves(me, opp, geom):
    occupied = set(me) | set(opp)
    return [p for p in geom["cells"] if p not in occupied]


def _candidate_moves(me, opp, legal, geom):
    if not me and not opp:
        cr, cc = geom["center"]
        return sorted(legal, key=lambda p: (p[0] - cr) ** 2 + (p[1] - cc) ** 2)[:12]

    occupied = set(me) | set(opp)
    cand = set()

    for p in occupied:
        for q in geom["neigh"].get(p, []):
            if q in legal:
                cand.add(q)
            for q in geom["neigh"].get(p, []):
                for z in geom["neigh"].get(q, []):
                    if z in legal:
                        cand.add(z)

    if not cand:
        cand = set(legal)

    # Cap candidates for speed, keeping central/local moves.
    cr, cc = geom["center"]
    scored = sorted(cand, key=lambda p: (p[0] - cr) ** 2 + (p[1] - cc) ** 2)
    return scored[:80]


def _score_move(move, me, opp, geom):
    neigh = geom["neigh"]
    corners = geom["corners"]
    edge_id = geom["edge_id"]
    cr, cc = geom["center"]

    me_set = set(me)
    opp_set = set(opp)

    score = 0.0

    # Central preference.
    dist2 = (move[0] - cr) ** 2 + (move[1] - cc) ** 2
    score -= 0.20 * dist2

    # Contact and shape.
    friendly_adj = 0
    enemy_adj = 0
    empty_adj = 0
    friendly_second = 0

    for nb in neigh.get(move, []):
        if nb in me_set:
            friendly_adj += 1
        elif nb in opp_set:
            enemy_adj += 1
        else:
            empty_adj += 1

        for nb2 in neigh.get(nb, []):
            if nb2 in me_set:
                friendly_second += 1

    score += 9.0 * friendly_adj
    score += 3.2 * enemy_adj
    score += 0.8 * empty_adj
    score += 0.9 * friendly_second

    # Boundary objectives.
    if move in corners:
        score += 16.0
    if move in edge_id:
        score += 8.0

    # Evaluate resulting components for our strategic potential.
    new_me = set(me)
    new_me.add(move)
    infos = _component_info(new_me, geom)

    for comp, comp_corners, comp_edges in infos:
        if move in comp:
            score += 8.0 * len(comp_corners)
            score += 5.5 * len(comp_edges)
            score += 1.1 * len(comp)

            if len(comp_corners) == 1:
                score += 6.0
            if len(comp_edges) == 2:
                score += 12.0
            if len(comp_corners) >= 1 and len(comp_edges) >= 1:
                score += 4.0
            break

    # Defensive value: playing adjacent to opponent components that already
    # have multiple edge/corner contacts.
    opp_infos = _component_info(opp_set, geom)
    for comp, comp_corners, comp_edges in opp_infos:
        adjacent = False
        for x in comp:
            if move in neigh.get(x, []):
                adjacent = True
                break
        if adjacent:
            score += 5.0 * len(comp_corners)
            score += 4.0 * len(comp_edges)
            if len(comp_corners) >= 1:
                score += 3.0
            if len(comp_edges) >= 2:
                score += 10.0

    # Prefer moves with several mutually connected neighbour groups.
    friend_neighbours = [nb for nb in neigh.get(move, []) if nb in me_set]
    if len(friend_neighbours) >= 2:
        score += 8.0 * len(friend_neighbours)

    # Slight penalty for cramped placements fully surrounded by stones.
    if empty_adj == 0:
        score -= 10.0

    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    geom = _compute_geometry(valid_mask)
    legal = _legal_moves(me, opp, geom)

    # Absolute safety: return any valid legal move if something odd happens.
    if not legal:
        # Should never happen in normal play.
        for r in range(len(valid_mask)):
            for c in range(len(valid_mask[0])):
                if _is_valid(valid_mask, r, c):
                    return (r, c)
        return (0, 0)

    legal_set = set(legal)

    # Opening: take the most central point.
    if not me and not opp:
        cr, cc = geom["center"]
        return min(legal, key=lambda p: (p[0] - cr) ** 2 + (p[1] - cc) ** 2)

    candidates = _candidate_moves(me, opp, legal_set, geom)

    # 1. Immediate win.
    for mv in candidates:
        if _is_win_after(mv, me, opp, geom):
            return mv

    # In case winning move is far away, scan all legal moves too.
    if len(candidates) < len(legal):
        for mv in legal:
            if mv not in candidates and _is_win_after(mv, me, opp, geom):
                return mv

    # 2. Immediate block.
    opponent_wins = []
    for mv in legal:
        if _is_win_after(mv, opp, me, geom):
            opponent_wins.append(mv)

    if opponent_wins:
        # If multiple threats exist, choose the block that is also best for us.
        return max(opponent_wins, key=lambda p: _score_move(p, me, opp, geom))

    # 3. Heuristic strategic move.
    best = None
    best_score = -10**18

    for mv in candidates:
        s = _score_move(mv, me, opp, geom)

        # Add a tiny deterministic tie-breaker.
        s += ((mv[0] * 31 + mv[1] * 17) % 97) * 1e-5

        if s > best_score:
            best_score = s
            best = mv

    if best is not None and best in legal_set:
        return best

    # Final fallback: legal central move.
    cr, cc = geom["center"]
    return min(legal, key=lambda p: (p[0] - cr) ** 2 + (p[1] - cc) ** 2)
