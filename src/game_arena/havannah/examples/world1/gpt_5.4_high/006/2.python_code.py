
from collections import deque

INF = 10**9

# Adjacency in the coordinate system described in the prompt.
DIRS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]

# Cyclic neighbor order around a cell, used for local shape heuristics.
RING_DIRS = [(-1, 0), (-1, 1), (0, 1), (1, 0), (0, -1), (-1, -1)]

_INFO_CACHE = {}


def _popcount(x: int) -> int:
    return x.bit_count()


def _mask_key(valid_mask):
    n = len(valid_mask)
    return tuple(tuple(bool(valid_mask[r][c]) for c in range(n)) for r in range(n))


def _get_info(valid_mask):
    key = _mask_key(valid_mask)
    cached = _INFO_CACHE.get(key)
    if cached is not None:
        return cached

    n = len(valid_mask)
    cells = [(r, c) for r in range(n) for c in range(n) if bool(valid_mask[r][c])]
    cell_set = set(cells)

    neighbors = {}
    for r, c in cells:
        lst = []
        for dr, dc in DIRS:
            rr, cc = r + dr, c + dc
            if (rr, cc) in cell_set:
                lst.append((rr, cc))
        neighbors[(r, c)] = lst

    boundary = {cell for cell in cells if len(neighbors[cell]) < 6}
    # On the standard Havannah board in this embedding, corners have degree 2.
    corners = [cell for cell in cells if len(neighbors[cell]) == 2]

    # Boundary graph should be a single cycle.
    bneighbors = {cell: [nb for nb in neighbors[cell] if nb in boundary] for cell in boundary}

    # Traverse the boundary cycle.
    if corners:
        start = min(corners)
    else:
        start = min(boundary)

    cycle = [start]
    prev = None
    cur = start
    seen = {start}
    for _ in range(len(boundary) + 5):
        bns = bneighbors[cur]
        if not bns:
            break
        if prev is None:
            nxt = min(bns)
        else:
            if len(bns) == 1:
                nxt = bns[0]
            else:
                nxt = bns[0] if bns[1] == prev else bns[1]
        if nxt == start:
            break
        if nxt in seen:
            break
        cycle.append(nxt)
        seen.add(nxt)
        prev, cur = cur, nxt

    # Fallback if needed: use all boundary cells in row-major order.
    if len(cycle) < len(boundary) // 2:
        cycle = sorted(boundary)

    corner_set = set(corners)
    ordered_corners = [cell for cell in cycle if cell in corner_set]

    # Fallback: still ensure 6 corners if traversal was odd.
    if len(ordered_corners) != 6:
        ordered_corners = sorted(corners)[:6]
    if len(ordered_corners) != 6:
        # Extremely defensive fallback for malformed masks.
        # Pick 6 boundary cells with minimum degree.
        ordered_corners = sorted(boundary, key=lambda x: (len(neighbors[x]), x))[:6]

    corner_id = {cell: i for i, cell in enumerate(ordered_corners)}
    corner_bits = {cell: (1 << corner_id[cell]) for cell in ordered_corners}

    # Split boundary cycle into 6 edge segments between consecutive corners.
    pos = {cell: i for i, cell in enumerate(cycle)}
    edges = [[] for _ in range(6)]
    edge_id = {}

    if len(cycle) >= 6 and len(ordered_corners) == 6 and all(c in pos for c in ordered_corners):
        L = len(cycle)
        for i in range(6):
            a = ordered_corners[i]
            b = ordered_corners[(i + 1) % 6]
            ia, ib = pos[a], pos[b]
            seg = []
            j = (ia + 1) % L
            while j != ib:
                seg.append(cycle[j])
                j = (j + 1) % L
            edges[i] = seg
            for cell in seg:
                edge_id[cell] = i
    else:
        # Fallback: boundary non-corner cells split by simple order.
        non_corner_boundary = [cell for cell in cycle if cell not in corner_set]
        chunk = max(1, len(non_corner_boundary) // 6)
        for i in range(6):
            seg = non_corner_boundary[i * chunk:(i + 1) * chunk] if i < 5 else non_corner_boundary[i * chunk:]
            edges[i] = seg
            for cell in seg:
                edge_id[cell] = i

    edge_bits = {cell: (1 << edge_id[cell]) for cell in edge_id}

    # Center = valid cell closest to board center.
    mid = n // 2
    center = min(cells, key=lambda x: abs(x[0] - mid) + abs(x[1] - mid))

    # Unweighted graph distance to center for centrality.
    center_dist = {cell: INF for cell in cells}
    dq = deque([center])
    center_dist[center] = 0
    while dq:
        x = dq.popleft()
        dx = center_dist[x]
        for y in neighbors[x]:
            if center_dist[y] == INF:
                center_dist[y] = dx + 1
                dq.append(y)

    info = {
        "n": n,
        "cells": cells,
        "cell_set": cell_set,
        "neighbors": neighbors,
        "boundary": boundary,
        "corners": ordered_corners,
        "edges": edges,
        "corner_bits": corner_bits,
        "edge_bits": edge_bits,
        "center": center,
        "center_dist": center_dist,
    }
    _INFO_CACHE[key] = info
    return info


def _build_components(stones, info):
    neighbors = info["neighbors"]
    corner_bits = info["corner_bits"]
    edge_bits = info["edge_bits"]

    comp_id = {}
    corner_masks = []
    edge_masks = []
    sizes = []

    for s in stones:
        if s in comp_id:
            continue
        cid = len(sizes)
        stack = [s]
        comp_id[s] = cid
        cm = 0
        em = 0
        sz = 0
        while stack:
            x = stack.pop()
            sz += 1
            cm |= corner_bits.get(x, 0)
            em |= edge_bits.get(x, 0)
            for y in neighbors[x]:
                if y in stones and y not in comp_id:
                    comp_id[y] = cid
                    stack.append(y)
        corner_masks.append(cm)
        edge_masks.append(em)
        sizes.append(sz)

    return {
        "comp_id": comp_id,
        "corner_masks": corner_masks,
        "edge_masks": edge_masks,
        "sizes": sizes,
    }


def _contact_after_move(stones, comp, move, info):
    adj_comps = set()
    adj_count = 0
    size_sum = 1

    for nb in info["neighbors"][move]:
        if nb in stones:
            adj_count += 1
            cid = comp["comp_id"][nb]
            if cid not in adj_comps:
                adj_comps.add(cid)
                size_sum += comp["sizes"][cid]

    cm = info["corner_bits"].get(move, 0)
    em = info["edge_bits"].get(move, 0)
    for cid in adj_comps:
        cm |= comp["corner_masks"][cid]
        em |= comp["edge_masks"][cid]

    return cm, em, adj_comps, adj_count, size_sum


def _encloses_non_own(stones, move, info):
    neighbors = info["neighbors"]
    boundary = info["boundary"]

    seen = set()
    for start in neighbors[move]:
        if start == move or start in stones or start in seen:
            continue
        q = deque([start])
        seen.add(start)
        touches_boundary = start in boundary

        while q:
            x = q.popleft()
            for y in neighbors[x]:
                if y == move or y in stones or y in seen:
                    continue
                seen.add(y)
                if y in boundary:
                    touches_boundary = True
                q.append(y)

        if not touches_boundary:
            return True
    return False


def _shortest_own_path_len(stones, start, goal, info):
    if start == goal:
        return 0
    neighbors = info["neighbors"]
    q = deque([(start, 0)])
    seen = {start}
    while q:
        x, d = q.popleft()
        for y in neighbors[x]:
            if y not in stones or y in seen:
                continue
            if y == goal:
                return d + 1
            seen.add(y)
            q.append((y, d + 1))
    return INF


def _forms_ring(stones, comp, move, info):
    # Minimal ring needs at least 6 stones total, so at least 5 already present.
    if len(stones) < 5:
        return False

    # Detector 1: newly enclosed non-own region.
    if _encloses_non_own(stones, move, info):
        return True

    # Detector 2: cycle through the new stone of length >= 6.
    # Approximate but effective for common filled-center ring patterns.
    own_neighbors = [nb for nb in info["neighbors"][move] if nb in stones]
    if len(own_neighbors) < 2:
        return False

    comp_id = comp["comp_id"]
    m = len(own_neighbors)
    for i in range(m):
        a = own_neighbors[i]
        for j in range(i + 1, m):
            b = own_neighbors[j]
            if comp_id.get(a) != comp_id.get(b):
                continue
            d = _shortest_own_path_len(stones, a, b, info)
            if d >= 4:
                return True
    return False


def _is_winning_move(stones, comp, move, info):
    cm, em, _, _, _ = _contact_after_move(stones, comp, move, info)
    if _popcount(cm) >= 2:
        return True  # bridge
    if _popcount(em) >= 3:
        return True  # fork
    if _forms_ring(stones, comp, move, info):
        return True  # ring
    return False


def _zero_one_bfs(my_stones, opp_stones, sources, info):
    neighbors = info["neighbors"]
    cells = info["cells"]

    dist = {cell: INF for cell in cells}
    dq = deque()

    for s in sources:
        if s in opp_stones:
            continue
        w = 0 if s in my_stones else 1
        if w < dist[s]:
            dist[s] = w
            if w == 0:
                dq.appendleft(s)
            else:
                dq.append(s)

    while dq:
        x = dq.popleft()
        dx = dist[x]
        for y in neighbors[x]:
            if y in opp_stones:
                continue
            w = 0 if y in my_stones else 1
            nd = dx + w
            if nd < dist[y]:
                dist[y] = nd
                if w == 0:
                    dq.appendleft(y)
                else:
                    dq.append(y)

    return dist


def _all_connection_dists(my_stones, opp_stones, info):
    corner_dists = [_zero_one_bfs(my_stones, opp_stones, [c], info) for c in info["corners"]]
    edge_dists = [_zero_one_bfs(my_stones, opp_stones, edge, info) for edge in info["edges"]]
    return corner_dists, edge_dists


def _cost_summary(move, corner_dists, edge_dists):
    cv = []
    for d in corner_dists:
        x = d[move]
        if x < INF:
            cv.append(max(0, x - 1))
    cv.sort()

    ev = []
    for d in edge_dists:
        x = d[move]
        if x < INF:
            ev.append(max(0, x - 1))
    ev.sort()

    best_bridge = cv[0] + cv[1] if len(cv) >= 2 else INF
    best_two_edges = ev[0] + ev[1] if len(ev) >= 2 else INF
    best_fork = ev[0] + ev[1] + ev[2] if len(ev) >= 3 else INF
    return best_bridge, best_fork, best_two_edges


def _spoke_bonus(move, stones):
    r, c = move
    vals = [1 if (r + dr, c + dc) in stones else 0 for dr, dc in RING_DIRS]
    ones = sum(vals)
    if ones == 0:
        return 0
    runs = 0
    for i in range(6):
        if vals[i] and not vals[i - 1]:
            runs += 1
    return 2 * ones + 5 * max(0, runs - 1)


def _base_score(
    move,
    me_set,
    opp_set,
    comp_me,
    comp_opp,
    info,
    my_corner_dists,
    my_edge_dists,
    opp_corner_dists,
    opp_edge_dists,
    stage,
):
    neighbors = info["neighbors"][move]

    adj_my = 0
    adj_opp = 0
    adj_my_comps = set()
    adj_opp_comps = set()
    liberties = 0

    for nb in neighbors:
        if nb in me_set:
            adj_my += 1
            adj_my_comps.add(comp_me["comp_id"][nb])
        elif nb in opp_set:
            adj_opp += 1
            adj_opp_comps.add(comp_opp["comp_id"][nb])
        else:
            liberties += 1

    cm, em, _, _, size_sum = _contact_after_move(me_set, comp_me, move, info)
    kc = _popcount(cm)
    ke = _popcount(em)

    score = 0.0

    # Connectivity / growth.
    if len(adj_my_comps) >= 2:
        score += 95 * (len(adj_my_comps) - 1)
    score += 9 * sum(comp_me["sizes"][cid] for cid in adj_my_comps)
    score += 16 * adj_my
    score += 2 * size_sum
    score += 7 * liberties

    # Contesting / cutting.
    score += 12 * adj_opp
    score += 18 * max(0, len(adj_opp_comps) - 1)

    # Border structure progress.
    score += 28 * kc
    score += 20 * ke
    if ke >= 2:
        score += 36 * (ke - 1)
    if kc >= 1 and ke >= 1:
        score += 10

    # Centrality.
    cd = info["center_dist"][move]
    early = max(0.0, (18 - stage) / 18.0)
    score += (14 + 20 * early) * max(0, 5 - cd)
    score -= 5 * max(0, cd - 5) * early

    if move in info["boundary"]:
        score -= 14 * early
        if stage < 8 and adj_my == 0:
            score -= 10

    if adj_my == 0 and adj_opp == 0:
        score -= 8 * early

    # Connection-potential heuristics.
    mb, mf, me2 = _cost_summary(move, my_corner_dists, my_edge_dists)
    ob, of, oe2 = _cost_summary(move, opp_corner_dists, opp_edge_dists)

    if mb < INF:
        score += max(0, 70 - 8 * mb)
    if mf < INF:
        score += max(0, 85 - 6 * mf)
    if me2 < INF:
        score += max(0, 28 - 4 * me2)

    # Defensive value: occupy cells that are cheap for opponent plans.
    if ob < INF:
        score += max(0, 24 - 3 * ob)
    if of < INF:
        score += max(0, 30 - 2 * of)
    if oe2 < INF:
        score += max(0, 12 - 1.5 * oe2)

    # Local ring/connection shape.
    score += _spoke_bonus(move, me_set)

    return score


def _future_win_count(stones, move, legal_moves, info, cap=2):
    new_stones = set(stones)
    new_stones.add(move)
    comp = _build_components(new_stones, info)

    cnt = 0
    for mv in legal_moves:
        if mv == move:
            continue
        if _is_winning_move(new_stones, comp, mv, info):
            cnt += 1
            if cnt >= cap:
                break
    return cnt


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    info = _get_info(valid_mask)

    me_set = {tuple(x) for x in me}
    opp_set = {tuple(x) for x in opp}
    occupied = me_set | opp_set

    legal = [cell for cell in info["cells"] if cell not in occupied]
    if not legal:
        # Should not happen, but always return something valid if possible.
        return info["center"]

    # Opening: take center if available.
    if not me_set and not opp_set and info["center"] in legal:
        return info["center"]

    try:
        comp_me = _build_components(me_set, info)
        comp_opp = _build_components(opp_set, info)

        # 1) Play an immediate win if we have one.
        my_wins = [mv for mv in legal if _is_winning_move(me_set, comp_me, mv, info)]
        if my_wins:
            return min(my_wins, key=lambda mv: (info["center_dist"][mv], mv[0], mv[1]))

        # 2) Block any immediate opponent win.
        opp_wins = [mv for mv in legal if _is_winning_move(opp_set, comp_opp, mv, info)]

        # 3) Positional scoring.
        my_corner_dists, my_edge_dists = _all_connection_dists(me_set, opp_set, info)
        opp_corner_dists, opp_edge_dists = _all_connection_dists(opp_set, me_set, info)

        stage = len(me_set) + len(opp_set)
        base_scores = {}
        for mv in legal:
            base_scores[mv] = _base_score(
                mv,
                me_set,
                opp_set,
                comp_me,
                comp_opp,
                info,
                my_corner_dists,
                my_edge_dists,
                opp_corner_dists,
                opp_edge_dists,
                stage,
            )

        # Candidate set: either mandatory blocks, or best-scoring moves.
        if opp_wins:
            candidates = opp_wins
        else:
            k = min(len(legal), 10 if stage >= 16 else 8)
            candidates = sorted(legal, key=lambda mv: base_scores[mv], reverse=True)[:k]

        best_move = None
        best_key = None

        for mv in candidates:
            total = base_scores[mv]

            # Short lookahead: prefer moves that create immediate threats next turn.
            future_wins = _future_win_count(me_set, mv, legal, info, cap=2)
            if future_wins >= 2:
                total += 260
            elif future_wins == 1:
                total += 90

            key = (total, -info["center_dist"][mv], -mv[0], -mv[1])
            if best_key is None or key > best_key:
                best_key = key
                best_move = mv

        if best_move is not None:
            return best_move

        # Fallback to best base score.
        return max(legal, key=lambda mv: (base_scores[mv], -info["center_dist"][mv], -mv[0], -mv[1]))

    except Exception:
        # Absolute safety fallback: return a legal move.
        return min(legal, key=lambda mv: (info["center_dist"][mv], mv[0], mv[1]))
