
from collections import deque

NEIGHBORS = ((1, 0), (-1, 0), (-1, -1), (0, -1), (0, 1), (-1, 1))
_TOPO_CACHE = {}


def _mask_key(valid_mask):
    n = len(valid_mask)
    rows = []
    for r in range(n):
        rows.append(tuple(bool(valid_mask[r][c]) for c in range(n)))
    return n, tuple(rows)


def _build_topology(valid_mask):
    key = _mask_key(valid_mask)
    if key in _TOPO_CACHE:
        return _TOPO_CACHE[key]

    n, grid = key
    valid = []
    valid_set = set()
    for r in range(n):
        for c in range(n):
            if grid[r][c]:
                valid.append((r, c))
                valid_set.add((r, c))

    neigh = {}
    degree = {}
    for cell in valid:
        r, c = cell
        ns = []
        for dr, dc in NEIGHBORS:
            nb = (r + dr, c + dc)
            if nb in valid_set:
                ns.append(nb)
        neigh[cell] = ns
        degree[cell] = len(ns)

    boundary = {x for x in valid if degree[x] < 6}

    corners = {x for x in boundary if degree[x] <= 3}
    if len(corners) != 6:
        ordered = sorted(boundary, key=lambda x: (degree[x], x[0], x[1]))
        corners = set(ordered[:6])

    corner_bits = {}
    for i, cell in enumerate(sorted(corners)):
        corner_bits[cell] = 1 << i

    edge_bits = {cell: 0 for cell in valid}
    unassigned = set(boundary) - corners
    comps = []

    while unassigned:
        start = next(iter(unassigned))
        unassigned.remove(start)
        q = deque([start])
        comp = [start]
        while q:
            x = q.popleft()
            for y in neigh[x]:
                if y in unassigned:
                    unassigned.remove(y)
                    q.append(y)
                    comp.append(y)
        comps.append(comp)

    if len(comps) == 6:
        for i, comp in enumerate(comps):
            bit = 1 << i
            for cell in comp:
                edge_bits[cell] = bit
    else:
        # Robust fallback: classify boundary cells by which neighbor directions are missing.
        patterns = {}
        next_id = 0
        for cell in boundary:
            if cell in corners:
                continue
            r, c = cell
            missing = []
            for i, (dr, dc) in enumerate(NEIGHBORS):
                if (r + dr, c + dc) not in valid_set:
                    missing.append(i)
            pat = tuple(missing)
            if pat not in patterns:
                patterns[pat] = next_id % 6
                next_id += 1
            edge_bits[cell] = 1 << patterns[pat]

    topo = {
        "n": n,
        "valid": valid,
        "valid_set": valid_set,
        "neigh": neigh,
        "degree": degree,
        "boundary": boundary,
        "corner_bits": corner_bits,
        "edge_bits": edge_bits,
        "center": ((n - 1) / 2.0, (n - 1) / 2.0),
    }
    _TOPO_CACHE[key] = topo
    return topo


def _bitcount(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")


def _build_components(stones, topo):
    neigh = topo["neigh"]
    corner_bits = topo["corner_bits"]
    edge_bits = topo["edge_bits"]

    stones = set(stones)
    comp_of = {}
    comp_corner = []
    comp_edge = []
    comp_size = []

    seen = set()
    cid = 0
    for start in stones:
        if start in seen:
            continue
        q = deque([start])
        seen.add(start)
        comp_of[start] = cid
        cb = 0
        eb = 0
        sz = 0

        while q:
            x = q.popleft()
            sz += 1
            cb |= corner_bits.get(x, 0)
            eb |= edge_bits.get(x, 0)
            for y in neigh[x]:
                if y in stones and y not in seen:
                    seen.add(y)
                    comp_of[y] = cid
                    q.append(y)

        comp_corner.append(cb)
        comp_edge.append(eb)
        comp_size.append(sz)
        cid += 1

    return {
        "stones": stones,
        "comp_of": comp_of,
        "corner": comp_corner,
        "edge": comp_edge,
        "size": comp_size,
    }


def _has_ring(stones, topo):
    if len(stones) < 6:
        return False

    valid = topo["valid"]
    neigh = topo["neigh"]
    boundary = topo["boundary"]
    stones = set(stones)

    seen = set()
    for start in valid:
        if start in stones or start in seen:
            continue

        q = deque([start])
        seen.add(start)
        touches_boundary = start in boundary

        while q:
            x = q.popleft()
            if x in boundary:
                touches_boundary = True
            for y in neigh[x]:
                if y not in stones and y not in seen:
                    seen.add(y)
                    q.append(y)

        if not touches_boundary:
            return True

    return False


def _is_win(stones, topo):
    if not stones:
        return False

    state = _build_components(stones, topo)
    for cb, eb in zip(state["corner"], state["edge"]):
        if _bitcount(cb) >= 2:
            return True
        if _bitcount(eb) >= 3:
            return True

    return _has_ring(stones, topo)


def _hypothetical_meta(move, state, topo):
    neigh = topo["neigh"]
    cb = topo["corner_bits"].get(move, 0)
    eb = topo["edge_bits"].get(move, 0)
    size = 1
    ids = set()

    for nb in neigh[move]:
        cid = state["comp_of"].get(nb)
        if cid is not None and cid not in ids:
            ids.add(cid)
            cb |= state["corner"][cid]
            eb |= state["edge"][cid]
            size += state["size"][cid]

    return cb, eb, size, len(ids)


def _static_score(move, my_state, opp_state, me_set, opp_set, topo):
    r, c = move
    cr, cc = topo["center"]
    neigh = topo["neigh"]

    cb, eb, my_size, my_links = _hypothetical_meta(move, my_state, topo)
    ocb, oeb, opp_size, opp_links = _hypothetical_meta(move, opp_state, topo)

    my_edges = _bitcount(eb)
    my_corners = _bitcount(cb)
    opp_edges = _bitcount(oeb)
    opp_corners = _bitcount(ocb)

    own_adj = 0
    opp_adj = 0
    empty_adj = 0
    for nb in neigh[move]:
        if nb in me_set:
            own_adj += 1
        elif nb in opp_set:
            opp_adj += 1
        else:
            empty_adj += 1

    dist2 = (r - cr) * (r - cr) + (c - cc) * (c - cc)
    score = 55.0 - 2.0 * dist2

    # Build our own connected structure.
    score += own_adj * 9.0
    score += opp_adj * 4.5
    score += empty_adj * 2.0
    score += my_links * 20.0
    score += my_size * 1.15

    if my_edges == 1:
        score += 22.0
    elif my_edges == 2:
        score += 135.0
    elif my_edges >= 3:
        score += 100000.0

    if my_corners == 1:
        score += 70.0
    elif my_corners >= 2:
        score += 100000.0

    # Defensive value: occupying strong opponent extension points.
    score += opp_adj * 5.0
    score += opp_links * 18.0
    score += opp_size * 0.9

    if opp_edges == 1:
        score += 28.0
    elif opp_edges == 2:
        score += 175.0
    elif opp_edges >= 3:
        score += 100000.0

    if opp_corners == 1:
        score += 85.0
    elif opp_corners >= 2:
        score += 100000.0

    # Slight deterministic tie-breaker.
    score += (r * 0.001 + c * 0.0001)
    return score


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    topo = _build_topology(valid_mask)
    valid = topo["valid"]

    me_set = set(tuple(x) for x in me)
    opp_set = set(tuple(x) for x in opp)
    occupied = me_set | opp_set

    empties = [cell for cell in valid if cell not in occupied]
    if not empties:
        # Should never happen in a legal game, but keep a total fallback.
        return valid[0] if valid else (0, 0)

    # Opening: take the most central legal point.
    if not me_set and not opp_set:
        cr, cc = topo["center"]
        return min(empties, key=lambda x: ((x[0] - cr) ** 2 + (x[1] - cc) ** 2, x[0], x[1]))

    # 1. Immediate win.
    for mv in empties:
        if _is_win(me_set | {mv}, topo):
            return mv

    # 2. Immediate block.
    opponent_wins = []
    for mv in empties:
        if _is_win(opp_set | {mv}, topo):
            opponent_wins.append(mv)

    my_state = _build_components(me_set, topo)
    opp_state = _build_components(opp_set, topo)

    if opponent_wins:
        # If multiple blocks exist, choose the one that also helps us most.
        return max(
            opponent_wins,
            key=lambda m: _static_score(m, my_state, opp_state, me_set, opp_set, topo),
        )

    # 3. Static Havannah structure evaluation.
    scored = []
    for mv in empties:
        scored.append((_static_score(mv, my_state, opp_state, me_set, opp_set, topo), mv))

    scored.sort(reverse=True, key=lambda x: x[0])

    # 4. Look for moves that create multiple immediate winning threats next turn.
    # Limited to the best static candidates to stay comfortably under time.
    best_score, best_move = scored[0]
    top_k = min(14, len(scored))

    for base_score, mv in scored[:top_k]:
        after_me = me_set | {mv}
        remaining = [x for x in empties if x != mv]

        winning_replies = 0
        for nxt in remaining:
            if _is_win(after_me | {nxt}, topo):
                winning_replies += 1
                if winning_replies >= 3:
                    break

        enhanced = base_score
        if winning_replies >= 2:
            enhanced += 520.0 + 80.0 * winning_replies
        elif winning_replies == 1:
            enhanced += 115.0

        if enhanced > best_score:
            best_score = enhanced
            best_move = mv

    # Final legality guard.
    if best_move in occupied or best_move not in topo["valid_set"]:
        for mv in empties:
            return mv

    return best_move
