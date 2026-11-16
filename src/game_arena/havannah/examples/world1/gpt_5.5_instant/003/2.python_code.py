
import math
from collections import deque, defaultdict

N = 15

# Hex neighbors for the coordinate system described in the prompt:
# vertical: (r-1,c),(r+1,c); left column: (r-1,c-1),(r,c-1); right column: (r,c+1),(r-1,c+1)
DIRS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    valid = _valid_set(valid_mask)
    occupied = set(me) | set(opp)
    legal = [p for p in valid if p not in occupied]
    if not legal:
        # Should never happen in normal play, but return a syntactically valid tuple.
        return (0, 0)

    meta = _board_meta(valid)

    me_set = set(me)
    opp_set = set(opp)

    # 1. Win immediately if possible.
    best_win = None
    for m in legal:
        if _is_win(me_set | {m}, valid, meta):
            if best_win is None or _move_static_score(m, meta, me_set, opp_set) > _move_static_score(best_win, meta, me_set, opp_set):
                best_win = m
    if best_win is not None:
        return best_win

    # 2. Block opponent's immediate win.
    opp_wins = []
    for m in legal:
        if _is_win(opp_set | {m}, valid, meta):
            opp_wins.append(m)
    if opp_wins:
        # If multiple blocks are needed, choose the one that is also best for us.
        return max(opp_wins, key=lambda x: _evaluate_move(x, me_set, opp_set, valid, meta))

    # 3. Prefer moves that create immediate threats next turn, while avoiding opponent threats.
    # Evaluate every legal move; board is small enough.
    best = None
    best_score = -10**18

    # If opening, play center-ish.
    if not me and not opp:
        center = _closest_to_center(legal, meta)
        return center

    for m in legal:
        score = _evaluate_move(m, me_set, opp_set, valid, meta)

        # One-ply threat creation: count our winning moves after this placement.
        new_me = me_set | {m}
        threat_count = 0
        # Only inspect nearby and strategically important cells first for speed.
        cand = set()
        for s in new_me:
            for nb in _neighbors(s, valid):
                if nb not in occupied and nb != m:
                    cand.add(nb)
        for corner in meta["corners"]:
            if corner not in occupied and corner != m:
                cand.add(corner)
        for cm in list(cand)[:80]:
            if cm in valid and cm not in occupied and cm != m:
                if _is_win(new_me | {cm}, valid, meta):
                    threat_count += 1
                    if threat_count >= 2:
                        break
        if threat_count >= 2:
            score += 9000
        elif threat_count == 1:
            score += 1800

        # Slight penalty if the move allows opponent an immediate win elsewhere.
        # Sample likely opponent replies around the move and opponent stones to stay fast.
        new_occ = occupied | {m}
        danger = 0
        ocand = set()
        for s in opp_set:
            for nb in _neighbors(s, valid):
                if nb not in new_occ:
                    ocand.add(nb)
        for nb in _neighbors(m, valid):
            if nb not in new_occ:
                ocand.add(nb)
        for cm in list(ocand)[:90]:
            if _is_win(opp_set | {cm}, valid, meta):
                danger += 1
                if danger >= 2:
                    break
        if danger:
            score -= 2200 * danger

        if score > best_score:
            best_score = score
            best = m

    if best is not None and best in valid and best not in occupied:
        return best

    return legal[0]


def _valid_set(valid_mask):
    valid = set()
    rows = len(valid_mask)
    for r in range(rows):
        row = valid_mask[r]
        cols = len(row)
        for c in range(cols):
            try:
                if bool(row[c]):
                    valid.add((r, c))
            except Exception:
                pass
    return valid


def _neighbors(p, valid):
    r, c = p
    for dr, dc in DIRS:
        q = (r + dr, c + dc)
        if q in valid:
            yield q


def _board_meta(valid):
    # Derive six board edges by taking boundary cells and grouping them into connected boundary arcs.
    boundary = set()
    for p in valid:
        if sum(1 for _ in _neighbors(p, valid)) < 6:
            boundary.add(p)

    # Corners are boundary cells with exactly 3 valid neighbors on a standard Havannah hex.
    corners = [p for p in boundary if sum(1 for _ in _neighbors(p, valid)) == 3]
    if len(corners) != 6:
        # Robust fallback: select six extreme cells by projections.
        dirs = [(1, 0), (0, 1), (1, 1), (-1, 0), (0, -1), (-1, -1)]
        cs = []
        for a, b in dirs:
            p = max(valid, key=lambda x: a * x[0] + b * x[1])
            if p not in cs:
                cs.append(p)
        # Fill if duplicates occurred.
        for p in sorted(boundary):
            if p not in cs:
                cs.append(p)
            if len(cs) == 6:
                break
        corners = cs[:6]

    corners_set = set(corners)

    # Boundary non-corners split into six edge components if corners removed.
    edge_id = {}
    edge_components = []
    unvisited = set(boundary - corners_set)
    while unvisited:
        start = next(iter(unvisited))
        comp = []
        dq = deque([start])
        unvisited.remove(start)
        while dq:
            x = dq.popleft()
            comp.append(x)
            for nb in _neighbors(x, valid):
                if nb in unvisited:
                    unvisited.remove(nb)
                    dq.append(nb)
        edge_components.append(comp)

    # In case components not exactly six due to mask quirks, assign boundary cells to nearest side by angle around center.
    if len(edge_components) != 6:
        edge_components = [[] for _ in range(6)]
        cr = sum(r for r, c in valid) / len(valid)
        cc = sum(c for r, c in valid) / len(valid)
        for p in boundary - corners_set:
            ang = math.atan2(p[0] - cr, p[1] - cc)
            k = int(((ang + math.pi) / (2 * math.pi)) * 6) % 6
            edge_components[k].append(p)

    for i, comp in enumerate(edge_components):
        for p in comp:
            edge_id[p] = i

    center_r = sum(r for r, c in valid) / len(valid)
    center_c = sum(c for r, c in valid) / len(valid)

    return {
        "boundary": boundary,
        "corners": corners_set,
        "edge_id": edge_id,
        "edges": edge_components,
        "center": (center_r, center_c),
        "valid_list": list(valid),
    }


def _components(stones, valid, meta):
    unseen = set(stones)
    comps = []
    while unseen:
        st = next(iter(unseen))
        dq = deque([st])
        unseen.remove(st)
        cells = []
        corners = set()
        edges = set()
        while dq:
            x = dq.popleft()
            cells.append(x)
            if x in meta["corners"]:
                corners.add(x)
            if x in meta["edge_id"]:
                edges.add(meta["edge_id"][x])
            for nb in _neighbors(x, valid):
                if nb in unseen:
                    unseen.remove(nb)
                    dq.append(nb)
        comps.append((cells, corners, edges))
    return comps


def _is_win(stones, valid, meta):
    if not stones:
        return False

    for cells, corners, edges in _components(stones, valid, meta):
        if len(corners) >= 2:
            return True
        if len(edges) >= 3:
            return True

    if _has_ring(stones, valid):
        return True

    return False


def _has_ring(stones, valid):
    # Flood-fill all non-stone cells from the outside of the valid board.
    # If any non-stone region inside valid is not reachable from outside, stones enclose it.
    blocked = set(stones)

    minr = min(r for r, c in valid) - 1
    maxr = max(r for r, c in valid) + 1
    minc = min(c for r, c in valid) - 1
    maxc = max(c for r, c in valid) + 1

    def box_neighbors(p):
        r, c = p
        for dr, dc in DIRS:
            q = (r + dr, c + dc)
            if minr <= q[0] <= maxr and minc <= q[1] <= maxc:
                yield q

    outside = (minr, minc)
    seen = {outside}
    dq = deque([outside])

    while dq:
        x = dq.popleft()
        for nb in box_neighbors(x):
            if nb in seen:
                continue
            if nb in valid and nb in blocked:
                continue
            seen.add(nb)
            dq.append(nb)

    for p in valid:
        if p not in blocked and p not in seen:
            return True
    return False


def _evaluate_move(m, me, opp, valid, meta):
    score = 0.0
    occ = me | opp

    # Local friendly/enemy contacts.
    friendly = 0
    enemy = 0
    empty = 0
    friend_neighbor_groups = set()
    enemy_neighbor_groups = set()

    # Group labels for local merge value.
    me_labels = _local_group_labels(me, valid, around=m)
    opp_labels = _local_group_labels(opp, valid, around=m)

    for nb in _neighbors(m, valid):
        if nb in me:
            friendly += 1
            friend_neighbor_groups.add(me_labels.get(nb, nb))
        elif nb in opp:
            enemy += 1
            enemy_neighbor_groups.add(opp_labels.get(nb, nb))
        else:
            empty += 1

    score += friendly * 55
    score += enemy * 28
    score += len(friend_neighbor_groups) * 140
    score += max(0, len(friend_neighbor_groups) - 1) * 180
    score += len(enemy_neighbor_groups) * 55

    # Avoid totally isolated edge/corner moves early unless tactically useful.
    if friendly == 0 and enemy == 0:
        score -= 90

    # Centrality.
    cr, cc = meta["center"]
    dist2 = (m[0] - cr) ** 2 + (m[1] - cc) ** 2
    score -= 5.0 * math.sqrt(dist2)

    # Edge/corner strategic values.
    if m in meta["corners"]:
        score += 260
    elif m in meta["edge_id"]:
        score += 90

    # Evaluate resulting component containing m.
    new_me = set(me)
    new_me.add(m)
    comp = _component_from(m, new_me, valid)
    comp_corners = {x for x in comp if x in meta["corners"]}
    comp_edges = {meta["edge_id"][x] for x in comp if x in meta["edge_id"]}

    score += len(comp) * 8
    score += len(comp_corners) * 430
    score += len(comp_edges) * 280
    if len(comp_corners) == 1:
        score += 160
    if len(comp_edges) == 2:
        score += 420
    if len(comp_edges) >= 3 or len(comp_corners) >= 2:
        score += 100000

    # Distance/progress toward missing corners and edges.
    if comp:
        if len(comp_corners) < 2:
            dcorn = sorted(_hex_distance_to_set_cell(x, meta["corners"]) for x in comp)
            if dcorn:
                score += max(0, 80 - 12 * dcorn[0])
        if len(comp_edges) < 3:
            edge_cells = set(meta["edge_id"].keys())
            dedge = min((_hex_distance_to_set_cell(x, edge_cells) for x in comp), default=9)
            score += max(0, 70 - 10 * dedge)

    # Block opponent component ambitions.
    opp_adj_comp = set()
    for nb in _neighbors(m, valid):
        if nb in opp:
            opp_adj_comp |= _component_from(nb, opp, valid)
    if opp_adj_comp:
        ocorners = {x for x in opp_adj_comp if x in meta["corners"]}
        oedges = {meta["edge_id"][x] for x in opp_adj_comp if x in meta["edge_id"]}
        score += len(ocorners) * 250 + len(oedges) * 170 + len(opp_adj_comp) * 4
        if len(ocorners) >= 1:
            score += 120
        if len(oedges) >= 2:
            score += 260

    # Ring-shape heuristic: occupying cells with multiple friendly neighbors and adjacent empties.
    if friendly >= 2 and empty >= 2:
        score += 180
    if friendly >= 3:
        score += 260
    # Cutting opponent ring-ish clusters.
    if enemy >= 3:
        score += 220

    # Liberty / shape penalty for over-crowding without purpose.
    if empty <= 1 and friendly < 2:
        score -= 120

    return score


def _component_from(start, stones, valid):
    if start not in stones:
        return set()
    seen = {start}
    dq = deque([start])
    while dq:
        x = dq.popleft()
        for nb in _neighbors(x, valid):
            if nb in stones and nb not in seen:
                seen.add(nb)
                dq.append(nb)
    return seen


def _local_group_labels(stones, valid, around):
    labels = {}
    targets = [nb for nb in _neighbors(around, valid) if nb in stones]
    remaining = set(targets)
    while remaining:
        start = next(iter(remaining))
        comp = _component_from(start, stones, valid)
        root = min(comp)
        for x in comp:
            labels[x] = root
        remaining -= comp
    return labels


def _hex_distance_to_set_cell(a, targets):
    # Fast approximate graph distance in this skew hex coordinate system.
    if not targets:
        return 99
    ar, ac = a
    best = 99
    for br, bc in targets:
        # Convert to cube-like axial approximation. Neighbor deltas are compatible enough for heuristics.
        dr = br - ar
        dc = bc - ac
        d = max(abs(dr), abs(dc), abs(dr + dc))
        if d < best:
            best = d
    return best


def _move_static_score(m, meta, me, opp):
    cr, cc = meta["center"]
    s = -math.sqrt((m[0] - cr) ** 2 + (m[1] - cc) ** 2)
    if m in meta["corners"]:
        s += 4
    if m in meta["edge_id"]:
        s += 2
    for dr, dc in DIRS:
        nb = (m[0] + dr, m[1] + dc)
        if nb in me:
            s += 3
        if nb in opp:
            s += 1
    return s


def _closest_to_center(legal, meta):
    cr, cc = meta["center"]
    return min(legal, key=lambda p: (p[0] - cr) ** 2 + (p[1] - cc) ** 2)
