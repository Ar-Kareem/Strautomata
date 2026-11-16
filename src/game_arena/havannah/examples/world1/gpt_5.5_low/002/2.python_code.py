
import math
from collections import deque

# Havannah neighbour relation matching the prompt's coordinate system.
_DIRS = [(-1, 0), (1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1)]

_GEOM_CACHE = {}


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    n = len(valid_mask)
    geom = _geometry(valid_mask)

    occupied = set(me) | set(opp)
    legal = [
        (r, c)
        for r in range(n)
        for c in range(len(valid_mask[r]))
        if bool(valid_mask[r][c]) and (r, c) not in occupied
    ]

    if not legal:
        # Should never happen, but keep API safe.
        return (0, 0)

    me_set = set(me)
    opp_set = set(opp)

    # 1. Win immediately if possible.
    best_win = None
    for mv in legal:
        if _is_win_after(me_set, mv, geom):
            if best_win is None or _static_tiebreak(mv, geom) > _static_tiebreak(best_win, geom):
                best_win = mv
    if best_win is not None:
        return best_win

    # 2. Block opponent's immediate win.
    blocks = []
    for mv in legal:
        if _is_win_after(opp_set, mv, geom):
            blocks.append(mv)
    if blocks:
        return max(blocks, key=lambda m: _move_score(m, me_set, opp_set, geom, urgent_block=True))

    # 3. Positional heuristic.
    return max(legal, key=lambda m: _move_score(m, me_set, opp_set, geom, urgent_block=False))


def _geometry(valid_mask):
    n = len(valid_mask)

    try:
        key = (n, tuple(tuple(bool(x) for x in row) for row in valid_mask))
    except TypeError:
        key = id(valid_mask)

    if key in _GEOM_CACHE:
        return _GEOM_CACHE[key]

    valid = set()
    for r in range(n):
        for c in range(len(valid_mask[r])):
            if bool(valid_mask[r][c]):
                valid.add((r, c))

    def neigh(cell):
        r, c = cell
        out = []
        for dr, dc in _DIRS:
            nb = (r + dr, c + dc)
            if nb in valid:
                out.append(nb)
        return out

    neighs = {cell: neigh(cell) for cell in valid}

    boundary = {cell for cell in valid if len(neighs[cell]) < 6}

    # Corners are boundary cells with minimum boundary degree / board-neighbour degree.
    # On a normal Havannah board this gives the six degree-3 cells.
    min_deg = min((len(neighs[x]) for x in boundary), default=0)
    corners = {x for x in boundary if len(neighs[x]) == min_deg}

    # If mask is unusual and this over/under-selects, keep the six most corner-like cells:
    # farthest from the board centre among low-degree boundary cells.
    if len(corners) != 6 and boundary:
        cr = sum(r for r, _ in valid) / float(len(valid))
        cc = sum(c for _, c in valid) / float(len(valid))
        ordered = sorted(
            boundary,
            key=lambda x: (len(neighs[x]), -((x[0] - cr) ** 2 + (x[1] - cc) ** 2))
        )
        corners = set(ordered[:6])

    # Edge labels: connected boundary arcs after removing corners.
    noncorner_boundary = boundary - corners
    edge_label = {}
    label = 0
    seen = set()

    for start in noncorner_boundary:
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        while q:
            x = q.popleft()
            edge_label[x] = label
            for y in neighs[x]:
                if y in noncorner_boundary and y not in seen:
                    seen.add(y)
                    q.append(y)
        label += 1

    # Normal board should produce six edge components. If not, still usable.
    center_r = sum(r for r, _ in valid) / float(len(valid))
    center_c = sum(c for _, c in valid) / float(len(valid))

    geom = {
        "n": n,
        "valid": valid,
        "neighs": neighs,
        "boundary": boundary,
        "corners": corners,
        "edge_label": edge_label,
        "center": (center_r, center_c),
    }
    _GEOM_CACHE[key] = geom
    return geom


def _neighbors(cell, geom):
    return geom["neighs"].get(cell, [])


def _tags(cell, geom):
    corners = geom["corners"]
    edge_label = geom["edge_label"]

    corner_count = 1 if cell in corners else 0
    edges = set()
    if cell in edge_label:
        edges.add(edge_label[cell])

    return corner_count, edges


def _component_info(stones, geom):
    stones = set(stones)
    seen = set()
    comps = []

    for s in stones:
        if s in seen:
            continue

        q = deque([s])
        seen.add(s)
        comp = []
        corner_count = 0
        edges = set()

        while q:
            x = q.popleft()
            comp.append(x)

            cc, ee = _tags(x, geom)
            corner_count += cc
            edges |= ee

            for y in _neighbors(x, geom):
                if y in stones and y not in seen:
                    seen.add(y)
                    q.append(y)

        comps.append((set(comp), corner_count, edges))

    return comps


def _is_win_after(stones, move, geom):
    stones2 = set(stones)
    stones2.add(move)

    # Bridge / fork detection.
    seen = set()
    q = deque([move])
    seen.add(move)
    corner_count = 0
    edges = set()

    while q:
        x = q.popleft()
        cc, ee = _tags(x, geom)
        corner_count += cc
        edges |= ee

        for y in _neighbors(x, geom):
            if y in stones2 and y not in seen:
                seen.add(y)
                q.append(y)

    if corner_count >= 2:
        return True
    if len(edges) >= 3:
        return True

    # Ring approximation: adding move creates a cycle in own-stone graph.
    # In Havannah, a newly completed ring necessarily creates such a cycle.
    if _creates_cycle(stones, move, geom):
        return True

    return False


def _creates_cycle(stones, move, geom):
    stones = set(stones)
    nbrs = [x for x in _neighbors(move, geom) if x in stones]

    if len(nbrs) < 2:
        return False

    blocked = move

    # If any two neighbouring friendly groups are already connected without move,
    # placing move closes a loop.
    for i in range(len(nbrs)):
        start = nbrs[i]
        targets = set(nbrs[i + 1:])
        if not targets:
            continue

        q = deque([start])
        seen = {start, blocked}

        while q:
            x = q.popleft()
            if x in targets:
                return True
            for y in _neighbors(x, geom):
                if y in stones and y not in seen:
                    seen.add(y)
                    q.append(y)

    return False


def _move_score(move, me_set, opp_set, geom, urgent_block=False):
    r, c = move
    cr, cc = geom["center"]

    score = 0.0

    # Central flexibility.
    dist2 = (r - cr) ** 2 + (c - cc) ** 2
    score += 25.0 / (1.0 + math.sqrt(dist2))

    my_nei = 0
    op_nei = 0
    empty_nei = 0

    for nb in _neighbors(move, geom):
        if nb in me_set:
            my_nei += 1
        elif nb in opp_set:
            op_nei += 1
        else:
            empty_nei += 1

    score += 7.5 * my_nei
    score += 4.2 * op_nei
    score += 0.7 * empty_nei

    # Local shape: two or more friendly neighbours often builds rings/strong groups.
    if my_nei >= 2:
        score += 8.0 * (my_nei - 1)
    if op_nei >= 2:
        score += 5.5 * (op_nei - 1)

    # Boundary/corner value for Havannah bridge/fork goals.
    ccnt, edges = _tags(move, geom)
    if ccnt:
        score += 10.0
    if edges:
        score += 5.0

    # Friendly component merge potential.
    my_adj_comps = _adjacent_component_summaries(move, me_set, geom)
    if my_adj_comps:
        merged_corners = ccnt + sum(x[0] for x in my_adj_comps)
        merged_edges = set(edges)
        merged_size = 1
        for co, ed, sz in my_adj_comps:
            merged_edges |= ed
            merged_size += sz

        score += 1.2 * merged_size
        score += 18.0 * min(merged_corners, 2)
        score += 13.0 * min(len(merged_edges), 3)

        if merged_corners >= 2:
            score += 80.0
        if len(merged_edges) >= 3:
            score += 80.0

        if len(my_adj_comps) >= 2:
            score += 12.0 * (len(my_adj_comps) - 1)

    # Opponent disruption / block potential.
    op_adj_comps = _adjacent_component_summaries(move, opp_set, geom)
    if op_adj_comps:
        opp_corners = ccnt + sum(x[0] for x in op_adj_comps)
        opp_edges = set(edges)
        opp_size = 1
        for co, ed, sz in op_adj_comps:
            opp_edges |= ed
            opp_size += sz

        score += 0.9 * opp_size
        score += 13.0 * min(opp_corners, 2)
        score += 10.0 * min(len(opp_edges), 3)

        if opp_corners >= 2:
            score += 50.0
        if len(opp_edges) >= 3:
            score += 50.0

    if urgent_block:
        score += 1000.0

    # Small deterministic tiebreak to avoid random/legal instability.
    score += _static_tiebreak(move, geom) * 1e-4

    return score


def _adjacent_component_summaries(move, stones, geom):
    stones = set(stones)
    summaries = []
    used = set()

    for nb in _neighbors(move, geom):
        if nb not in stones or nb in used:
            continue

        q = deque([nb])
        used.add(nb)
        size = 0
        corners = 0
        edges = set()

        while q:
            x = q.popleft()
            size += 1
            cc, ee = _tags(x, geom)
            corners += cc
            edges |= ee

            for y in _neighbors(x, geom):
                if y in stones and y not in used:
                    used.add(y)
                    q.append(y)

        summaries.append((corners, edges, size))

    return summaries


def _static_tiebreak(move, geom):
    r, c = move
    cr, cc = geom["center"]
    return -((r - cr) ** 2 + (c - cc) ** 2) + ((r * 37 + c * 17) % 11) * 0.01
