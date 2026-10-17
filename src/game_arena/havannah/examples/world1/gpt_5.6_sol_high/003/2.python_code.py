
from collections import deque
from math import sqrt

_GEOMETRY_CACHE = {}


def _make_geometry(valid_mask):
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0
    key = tuple(
        tuple(bool(valid_mask[r][c]) for c in range(cols))
        for r in range(rows)
    )
    cached = _GEOMETRY_CACHE.get(key)
    if cached is not None:
        return cached

    valid = {
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if bool(valid_mask[r][c])
    }

    # A hexagon embedded in a square array can use either diagonal orientation.
    options = [
        ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)),
        ((1, 0), (-1, 0), (0, 1), (0, -1), (1, -1), (-1, 1)),
    ]

    def orientation_score(dirs):
        degrees = []
        for r, c in valid:
            degrees.append(sum((r + dr, c + dc) in valid for dr, dc in dirs))
        n3 = sum(d == 3 for d in degrees)
        malformed = sum(d < 3 for d in degrees)
        n5 = sum(d == 5 for d in degrees)
        return abs(n3 - 6) * 40 + malformed * 200 + n5 * 3

    dirs = min(options, key=orientation_score)
    same_diagonal = (1, 1) in dirs

    neigh = {}
    for p in valid:
        r, c = p
        neigh[p] = tuple(
            (r + dr, c + dc)
            for dr, dc in dirs
            if (r + dr, c + dc) in valid
        )

    boundary = {p for p in valid if len(neigh[p]) < 6}
    corners = [p for p in boundary if len(neigh[p]) == 3]

    # Standard Havannah masks produce exactly six degree-three corners.
    # The fallback chooses low-degree boundary cells spread apart.
    if len(corners) != 6:
        candidates = sorted(boundary, key=lambda p: (len(neigh[p]), p))
        chosen = []
        if candidates:
            chosen.append(candidates[0])
        while candidates and len(chosen) < 6:
            remaining = [p for p in candidates if p not in chosen]
            if not remaining:
                break

            def separation(p):
                return min(
                    abs(p[0] - q[0]) + abs(p[1] - q[1])
                    for q in chosen
                )

            chosen.append(max(remaining, key=separation))
        corners = chosen[:6]

    corner_index = {p: i for i, p in enumerate(corners)}
    corner_set = set(corners)

    # Removing the six corners splits the perimeter into the six edges.
    edge_nodes = boundary - corner_set
    edge_components = []
    unseen = set(edge_nodes)
    while unseen:
        start = unseen.pop()
        comp = {start}
        stack = [start]
        while stack:
            p = stack.pop()
            for q in neigh[p]:
                if q in unseen and q in edge_nodes:
                    unseen.remove(q)
                    comp.add(q)
                    stack.append(q)
        edge_components.append(comp)

    edge_components.sort(key=lambda comp: min(comp) if comp else (rows, cols))

    # On unusual but legal masks, normalize to at most six edge groups.
    if len(edge_components) > 6:
        edge_components.sort(key=len, reverse=True)
        edge_components = edge_components[:6]

    edge_index = {}
    for i, comp in enumerate(edge_components):
        for p in comp:
            edge_index[p] = i

    corner_bit = {p: 1 << i for p, i in corner_index.items()}
    edge_bit = {p: 1 << i for p, i in edge_index.items()}

    # Axial-like coordinates used for polygon-area ring checks.
    axial = {}
    for r, c in valid:
        if same_diagonal:
            axial[(r, c)] = (c, r - c)
        else:
            axial[(r, c)] = (c, r + c)

    if valid:
        avg_q = sum(axial[p][0] for p in valid) / len(valid)
        avg_s = sum(axial[p][1] for p in valid) / len(valid)
        center = min(
            valid,
            key=lambda p: (
                (axial[p][0] - avg_q) ** 2
                + (axial[p][1] - avg_s) ** 2
            ),
        )
    else:
        avg_q = avg_s = 0.0
        center = (0, 0)

    geom = {
        "rows": rows,
        "cols": cols,
        "valid": valid,
        "valid_list": tuple(sorted(valid)),
        "dirs": dirs,
        "neigh": neigh,
        "boundary": boundary,
        "corners": tuple(corners),
        "corner_bit": corner_bit,
        "edge_components": tuple(tuple(comp) for comp in edge_components),
        "edge_bit": edge_bit,
        "axial": axial,
        "avg_q": avg_q,
        "avg_s": avg_s,
        "center": center,
    }
    _GEOMETRY_CACHE[key] = geom
    return geom


def _build_components(stones, geom):
    neigh = geom["neigh"]
    corner_bit = geom["corner_bit"]
    edge_bit = geom["edge_bit"]

    comp_id = {}
    metas = []
    unseen = set(stones)

    while unseen:
        start = unseen.pop()
        stack = [start]
        cells = [start]
        corners = corner_bit.get(start, 0)
        edges = edge_bit.get(start, 0)

        while stack:
            p = stack.pop()
            for q in neigh[p]:
                if q in unseen:
                    unseen.remove(q)
                    stack.append(q)
                    cells.append(q)
                    corners |= corner_bit.get(q, 0)
                    edges |= edge_bit.get(q, 0)

        idx = len(metas)
        for p in cells:
            comp_id[p] = idx
        metas.append((len(cells), corners, edges))

    return comp_id, metas


def _merged_meta(move, stones, comp_data, geom):
    comp_id, metas = comp_data
    ids = {
        comp_id[q]
        for q in geom["neigh"][move]
        if q in stones
    }

    size = 1
    corners = geom["corner_bit"].get(move, 0)
    edges = geom["edge_bit"].get(move, 0)

    for idx in ids:
        msize, mcorners, medges = metas[idx]
        size += msize
        corners |= mcorners
        edges |= medges

    return size, corners, edges, len(ids)


def _structure_win(move, stones, comp_data, geom):
    _, corners, edges, _ = _merged_meta(move, stones, comp_data, geom)
    return corners.bit_count() >= 2 or edges.bit_count() >= 3


def _cycle_ring_through_move(move, stones, geom):
    """Detect a cycle through move that geometrically encloses a board point."""
    own_neighbors = [q for q in geom["neigh"][move] if q in stones]
    if len(own_neighbors) < 2:
        return False

    neigh = geom["neigh"]
    axial = geom["axial"]

    for i in range(len(own_neighbors)):
        start = own_neighbors[i]
        for j in range(i + 1, len(own_neighbors)):
            target = own_neighbors[j]

            parent = {start: None}
            queue = deque([start])
            found = False

            while queue and not found:
                p = queue.popleft()
                for q in neigh[p]:
                    if q not in stones or q in parent:
                        continue
                    parent[q] = p
                    if q == target:
                        found = True
                        break
                    queue.append(q)

            if target not in parent:
                continue

            path = []
            p = target
            while p is not None:
                path.append(p)
                p = parent[p]
            path.reverse()

            vertices = [move] + path
            area2 = 0
            for k in range(len(vertices)):
                q1, s1 = axial[vertices[k]]
                q2, s2 = axial[vertices[(k + 1) % len(vertices)]]
                area2 += q1 * s2 - q2 * s1

            # All cycle edges are primitive lattice edges, so Pick's theorem
            # gives I = (abs(area2) - boundary_edges + 2) / 2.
            boundary_edges = len(vertices)
            if abs(area2) - boundary_edges + 2 >= 2:
                return True

    return False


def _ring_after(move, stones, geom):
    barriers = set(stones)
    barriers.add(move)
    valid = geom["valid"]
    neigh = geom["neigh"]

    # A ring separates at least one non-ring cell from the perimeter.
    seen = set()
    queue = deque()

    for p in geom["boundary"]:
        if p not in barriers:
            seen.add(p)
            queue.append(p)

    while queue:
        p = queue.popleft()
        for q in neigh[p]:
            if q not in barriers and q not in seen:
                seen.add(q)
                queue.append(q)

    for p in valid:
        if p not in barriers and p not in seen:
            return True

    # This additionally catches common cases where an enclosed cell is itself
    # occupied by the ring player's stone.
    return _cycle_ring_through_move(move, stones, geom)


def _winning_moves(stones, occupied, geom, limit=None):
    comp_data = _build_components(stones, geom)
    wins = []

    for move in geom["valid_list"]:
        if move in occupied:
            continue

        if _structure_win(move, stones, comp_data, geom):
            wins.append(move)
        else:
            adjacent = sum(q in stones for q in geom["neigh"][move])
            if adjacent >= 2 and _ring_after(move, stones, geom):
                wins.append(move)

        if limit is not None and len(wins) >= limit:
            break

    return wins


def _distance_maps(stones, enemy, goals, geom):
    valid = geom["valid"]
    neigh = geom["neigh"]
    inf = 10 ** 6
    result = []

    for sources in goals:
        dist = {p: inf for p in valid}
        queue = deque()

        for p in sources:
            if p not in valid or p in enemy:
                continue
            cost = 0 if p in stones else 1
            if cost < dist[p]:
                dist[p] = cost
                if cost == 0:
                    queue.appendleft(p)
                else:
                    queue.append(p)

        while queue:
            p = queue.popleft()
            base = dist[p]
            for q in neigh[p]:
                if q in enemy:
                    continue
                weight = 0 if q in stones else 1
                nd = base + weight
                if nd < dist[q]:
                    dist[q] = nd
                    if weight == 0:
                        queue.appendleft(q)
                    else:
                        queue.append(q)

        result.append(dist)

    return result


def _goal_cost(move, maps, count, cap):
    vals = sorted(min(cap, d.get(move, cap)) for d in maps)
    if len(vals) < count:
        vals.extend([cap] * (count - len(vals)))
    # The candidate cell is included in every path and should only be paid once.
    return sum(vals[:count]) - max(0, count - 1)


def _virtual_bridge_count(move, stones, occupied, geom):
    count = 0
    move_neighbors = set(geom["neigh"][move])

    for stone in stones:
        if stone in move_neighbors:
            continue
        common = move_neighbors.intersection(geom["neigh"][stone])
        carriers = [p for p in common if p not in occupied]
        if len(carriers) >= 2:
            count += 1

    return count


def _offense_value(move, stones, occupied, comp_data,
                   corner_maps, edge_maps, geom):
    neigh = geom["neigh"]
    size, corner_bits, edge_bits, merged_components = _merged_meta(
        move, stones, comp_data, geom
    )

    adjacent = sum(q in stones for q in neigh[move])
    corner_count = corner_bits.bit_count()
    edge_count = edge_bits.bit_count()

    cap = geom["rows"] + geom["cols"] + 8
    bridge_cost = _goal_cost(move, corner_maps, 2, cap)
    fork_cost = _goal_cost(move, edge_maps, 3, cap)
    virtuals = _virtual_bridge_count(move, stones, occupied, geom)

    value = 0.0
    value += 16.0 * adjacent
    value += 35.0 * max(0, merged_components - 1)
    value += 8.0 * sqrt(size)
    value += 34.0 * corner_count * corner_count
    value += 22.0 * edge_count * edge_count
    value += 18.0 * virtuals
    value -= 7.5 * bridge_cost
    value -= 6.0 * fork_cost

    return value


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    geom = _make_geometry(valid_mask)
    valid = geom["valid"]
    my_stones = set(me)
    opp_stones = set(opp)
    occupied = my_stones | opp_stones
    legal = [p for p in geom["valid_list"] if p not in occupied]

    # The game API promises that a move exists, but retain a defensive fallback.
    if not legal:
        for r in range(len(valid_mask)):
            for c in range(len(valid_mask[r])):
                if bool(valid_mask[r][c]) and (r, c) not in occupied:
                    return (r, c)
        return (0, 0)

    if not occupied and geom["center"] in legal:
        return geom["center"]

    # Exact one-move tactics have absolute priority.
    my_wins = _winning_moves(my_stones, occupied, geom)
    if my_wins:
        center = geom["center"]
        return min(
            my_wins,
            key=lambda p: abs(p[0] - center[0]) + abs(p[1] - center[1]),
        )

    opp_wins = _winning_moves(opp_stones, occupied, geom)
    if len(opp_wins) == 1:
        return opp_wins[0]

    my_components = _build_components(my_stones, geom)
    opp_components = _build_components(opp_stones, geom)

    corner_goals = [(p,) for p in geom["corners"]]
    edge_goals = list(geom["edge_components"])

    my_corner_maps = _distance_maps(
        my_stones, opp_stones, corner_goals, geom
    )
    my_edge_maps = _distance_maps(
        my_stones, opp_stones, edge_goals, geom
    )
    opp_corner_maps = _distance_maps(
        opp_stones, my_stones, corner_goals, geom
    )
    opp_edge_maps = _distance_maps(
        opp_stones, my_stones, edge_goals, geom
    )

    scores = {}
    opp_values = {}
    avg_q = geom["avg_q"]
    avg_s = geom["avg_s"]

    for move in legal:
        my_value = _offense_value(
            move, my_stones, occupied, my_components,
            my_corner_maps, my_edge_maps, geom
        )
        opp_value = _offense_value(
            move, opp_stones, occupied, opp_components,
            opp_corner_maps, opp_edge_maps, geom
        )
        opp_values[move] = opp_value

        q, s = geom["axial"][move]
        center_penalty = 0.38 * (
            (q - avg_q) ** 2 + (s - avg_s) ** 2
        )

        # Occupying a strong opponent point is valuable, but development of
        # our own connected threats remains slightly more important.
        score = my_value + 0.72 * opp_value - center_penalty

        # Reward occupying one carrier of an opponent's virtual connection.
        opp_adjacent = [p for p in geom["neigh"][move] if p in opp_stones]
        for i in range(len(opp_adjacent)):
            for j in range(i + 1, len(opp_adjacent)):
                a = opp_adjacent[i]
                b = opp_adjacent[j]
                common = set(geom["neigh"][a]).intersection(geom["neigh"][b])
                if any(
                    p != move and p not in occupied
                    for p in common
                ):
                    score += 20.0

        # Stable deterministic tie-breaking.
        score += (
            (move[0] * 37 + move[1] * 17 + len(me) * 13 + len(opp) * 7)
            % 23
        ) * 0.0001
        scores[move] = score

    # If several immediate losses exist, at least occupy the most useful one.
    if len(opp_wins) > 1:
        return max(opp_wins, key=lambda p: scores.get(p, -10 ** 9))

    # Search likely opponent threat-creation moves. A point that would give the
    # opponent two different wins next turn is a critical defensive target.
    if len(opp_stones) >= 2:
        opponent_candidates = sorted(
            legal, key=lambda p: opp_values[p], reverse=True
        )[:14]

        for creator in opponent_candidates:
            hypothetical_opp = set(opp_stones)
            hypothetical_opp.add(creator)
            hypothetical_occupied = set(occupied)
            hypothetical_occupied.add(creator)

            replies = _winning_moves(
                hypothetical_opp, hypothetical_occupied, geom, limit=3
            )

            if len(replies) >= 2:
                scores[creator] += 8500.0
                for reply in replies:
                    if reply in scores:
                        scores[reply] += 2100.0
            elif len(replies) == 1:
                scores[creator] += 150.0

    # Examine the strongest candidates for forcing threats of our own.
    shortlist = sorted(legal, key=lambda p: scores[p], reverse=True)[:16]

    for move in shortlist:
        hypothetical_me = set(my_stones)
        hypothetical_me.add(move)
        hypothetical_occupied = set(occupied)
        hypothetical_occupied.add(move)

        replies = _winning_moves(
            hypothetical_me, hypothetical_occupied, geom, limit=3
        )

        if len(replies) >= 3:
            scores[move] += 13000.0
        elif len(replies) == 2:
            scores[move] += 10000.0
        elif len(replies) == 1:
            scores[move] += 280.0

    chosen = max(legal, key=lambda p: scores[p])

    if chosen in valid and chosen not in occupied:
        return (int(chosen[0]), int(chosen[1]))

    # Guaranteed legal fallback.
    fallback = legal[0]
    return (int(fallback[0]), int(fallback[1]))
