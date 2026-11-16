
from collections import deque
from math import sqrt
from time import perf_counter

_GEOMETRY_CACHE = {}

_DIR_OPTIONS = (
    ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)),
    ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1)),
)


def _popcount(value):
    return bin(value).count("1")


def _boundary_components(valid, dirs):
    neighbors = {}
    degrees = {}

    for cell in valid:
        r, c = cell
        ns = []
        for dr, dc in dirs:
            nxt = (r + dr, c + dc)
            if nxt in valid:
                ns.append(nxt)
        neighbors[cell] = tuple(ns)
        degrees[cell] = len(ns)

    corners = {x for x in valid if degrees[x] == 3}
    boundary = {x for x in valid if degrees[x] < 6}
    edge_cells = boundary - corners

    components = []
    unseen = set(edge_cells)
    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        comp = {start}
        stack = [start]

        while stack:
            x = stack.pop()
            for y in neighbors[x]:
                if y in unseen and y in edge_cells:
                    unseen.remove(y)
                    comp.add(y)
                    stack.append(y)

        components.append(comp)

    return neighbors, degrees, corners, boundary, components


def _orientation_score(valid, dirs):
    _, degrees, corners, boundary, edge_components = _boundary_components(
        valid, dirs
    )

    interior_bad = sum(
        1 for x in valid if x not in boundary and degrees[x] != 6
    )

    return (
        abs(len(corners) - 6) * 1000
        + abs(len(edge_components) - 6) * 500
        + interior_bad * 20
        - sum(1 for x in valid if degrees[x] == 6)
    )


def _multi_source_dist(neighbors, sources):
    dist = {}
    q = deque()

    for source in sources:
        if source not in dist:
            dist[source] = 0
            q.append(source)

    while q:
        x = q.popleft()
        nd = dist[x] + 1
        for y in neighbors[x]:
            if y not in dist:
                dist[y] = nd
                q.append(y)

    return dist


def _get_geometry(valid_mask, valid_cells):
    rows = len(valid_mask)
    widths = tuple(len(valid_mask[r]) for r in range(rows))
    key = (rows, widths, tuple(sorted(valid_cells)))

    cached = _GEOMETRY_CACHE.get(key)
    if cached is not None:
        return cached

    valid = set(valid_cells)
    dirs = min(_DIR_OPTIONS, key=lambda d: _orientation_score(valid, d))

    neighbors, degrees, corners, boundary, edge_components = (
        _boundary_components(valid, dirs)
    )

    # Standard boards produce exactly six components. Sorting makes the
    # assignment deterministic; only distinct identities matter.
    edge_components.sort(key=lambda comp: min(comp) if comp else (999, 999))
    if len(edge_components) > 6:
        edge_components = edge_components[:6]

    sorted_corners = sorted(corners)
    if len(sorted_corners) > 6:
        sorted_corners = sorted_corners[:6]

    edge_mask = {x: 0 for x in valid}
    for index, comp in enumerate(edge_components):
        bit = 1 << index
        for x in comp:
            edge_mask[x] |= bit

    corner_mask = {x: 0 for x in valid}
    for index, x in enumerate(sorted_corners):
        corner_mask[x] = 1 << index

    edge_distances = [
        _multi_source_dist(neighbors, comp) for comp in edge_components
    ]
    corner_distances = [
        _multi_source_dist(neighbors, (corner,))
        for corner in sorted_corners
    ]
    depth = _multi_source_dist(neighbors, boundary)

    geometry = {
        "valid": valid,
        "dirs": dirs,
        "neighbors": neighbors,
        "boundary": boundary,
        "corners": set(sorted_corners),
        "edges": edge_components,
        "edge_mask": edge_mask,
        "corner_mask": corner_mask,
        "edge_dist": edge_distances,
        "corner_dist": corner_distances,
        "depth": depth,
    }
    _GEOMETRY_CACHE[key] = geometry
    return geometry


def _build_components(stones, geometry):
    stones = set(stones)
    neighbors = geometry["neighbors"]
    edge_mask = geometry["edge_mask"]
    corner_mask = geometry["corner_mask"]

    labels = {}
    infos = []
    unseen = set(stones)

    while unseen:
        start = unseen.pop()
        stack = [start]
        component = [start]
        emask = edge_mask.get(start, 0)
        cmask = corner_mask.get(start, 0)

        while stack:
            x = stack.pop()
            for y in neighbors.get(x, ()):
                if y in unseen:
                    unseen.remove(y)
                    stack.append(y)
                    component.append(y)
                    emask |= edge_mask.get(y, 0)
                    cmask |= corner_mask.get(y, 0)

        index = len(infos)
        for x in component:
            labels[x] = index

        infos.append({
            "size": len(component),
            "edge_mask": emask,
            "corner_mask": cmask,
        })

    return labels, infos


def _connection_result(move, labels, infos, geometry):
    adjacent_labels = {
        labels[x]
        for x in geometry["neighbors"][move]
        if x in labels
    }

    emask = geometry["edge_mask"].get(move, 0)
    cmask = geometry["corner_mask"].get(move, 0)
    size = 1

    for label in adjacent_labels:
        info = infos[label]
        size += info["size"]
        emask |= info["edge_mask"]
        cmask |= info["corner_mask"]

    return adjacent_labels, size, emask, cmask


def _has_ring_after(stones, move, geometry):
    stones_after = set(stones)
    stones_after.add(move)

    # A newly completed ring must use the new stone with at least two
    # friendly neighboring stones.
    friendly_neighbors = sum(
        1 for x in geometry["neighbors"][move] if x in stones
    )
    if friendly_neighbors < 2:
        return False

    valid = geometry["valid"]
    neighbors = geometry["neighbors"]

    # Treat the player's stones as walls. Any non-player region that cannot
    # reach the boundary is enclosed by a ring.
    reachable = set()
    q = deque()

    for x in geometry["boundary"]:
        if x not in stones_after:
            reachable.add(x)
            q.append(x)

    while q:
        x = q.popleft()
        for y in neighbors[x]:
            if y not in stones_after and y not in reachable:
                reachable.add(y)
                q.append(y)

    if len(reachable) < len(valid) - len(stones_after):
        return True

    # Covers the important case of a six-cell ring whose center is also one
    # of the player's stones and therefore was excluded from flood filling.
    candidates = {move}
    candidates.update(neighbors[move])
    for center in candidates:
        around = neighbors.get(center, ())
        if len(around) == 6 and all(x in stones_after for x in around):
            return True

    return False


def _winning_moves(stones, legal, geometry, deadline=None):
    labels, infos = _build_components(stones, geometry)
    wins = []

    for move in legal:
        if deadline is not None and perf_counter() > deadline:
            break

        _, _, emask, cmask = _connection_result(
            move, labels, infos, geometry
        )

        bridge = _popcount(cmask) >= 2
        fork = _popcount(emask) >= 3

        if bridge or fork:
            wins.append(move)
            continue

        friendly_neighbors = sum(
            1 for x in geometry["neighbors"][move] if x in stones
        )
        if friendly_neighbors >= 2 and _has_ring_after(
            stones, move, geometry
        ):
            wins.append(move)

    return wins


def _ring_shape_value(move, stones, geometry):
    value = 0.0
    hypothetical = set(stones)
    hypothetical.add(move)

    centers = set(geometry["neighbors"][move])
    centers.add(move)

    for center in centers:
        around = geometry["neighbors"].get(center, ())
        if len(around) != 6:
            continue

        count = sum(1 for x in around if x in hypothetical)
        if count >= 3:
            value += 2.5 * (count - 2) * (count - 2)

    return value


def _placement_value(move, stones, labels, infos, geometry):
    neighbors = geometry["neighbors"][move]
    touching = [x for x in neighbors if x in stones]
    adjacent_labels, size, emask, cmask = _connection_result(
        move, labels, infos, geometry
    )

    friendly_count = len(touching)
    distinct_count = len(adjacent_labels)
    edge_count = _popcount(emask)
    corner_count = _popcount(cmask)

    neighbor_values = (-3.0, 6.0, 17.0, 25.0, 31.0, 35.0, 38.0)
    value = neighbor_values[min(friendly_count, 6)]

    value += 7.5 * max(0, distinct_count - 1)
    value += 3.0 * sqrt(max(1, size))

    # Multiple contacts with one old component often indicate a developing
    # loop and are particularly useful in Havannah.
    repeated_contacts = friendly_count - distinct_count
    value += 8.0 * max(0, repeated_contacts)

    if edge_count == 1:
        value += 10.0
    elif edge_count == 2:
        value += 36.0
    elif edge_count >= 3:
        value += 5000.0

    if corner_count == 1:
        value += 16.0
    elif corner_count >= 2:
        value += 5000.0

    # Estimate the remaining geometric effort for a fork.
    remaining_edge_dist = []
    for i, dist_map in enumerate(geometry["edge_dist"]):
        if not (emask & (1 << i)):
            remaining_edge_dist.append(dist_map.get(move, 30))
    remaining_edge_dist.sort()

    needed_edges = max(0, 3 - edge_count)
    for distance in remaining_edge_dist[:needed_edges]:
        value += 13.0 / (1.0 + distance)

    # Estimate the remaining geometric effort for a bridge.
    remaining_corner_dist = []
    for i, dist_map in enumerate(geometry["corner_dist"]):
        if not (cmask & (1 << i)):
            remaining_corner_dist.append(dist_map.get(move, 30))
    remaining_corner_dist.sort()

    needed_corners = max(0, 2 - corner_count)
    for distance in remaining_corner_dist[:needed_corners]:
        value += 10.0 / (1.0 + distance)

    value += _ring_shape_value(move, stones, geometry)
    return value


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    valid_mask
) -> tuple[int, int]:
    start_time = perf_counter()
    deadline = start_time + 0.92

    occupied = set(me)
    occupied.update(opp)

    valid_cells = []
    for r in range(len(valid_mask)):
        for c in range(len(valid_mask[r])):
            if bool(valid_mask[r][c]):
                valid_cells.append((r, c))

    legal = [x for x in valid_cells if x not in occupied]

    # A normal Havannah call always has a legal move.
    if not legal:
        for x in valid_cells:
            return x
        return (0, 0)

    fallback = legal[0]

    try:
        geometry = _get_geometry(valid_mask, valid_cells)
        my_stones = set(me)
        opp_stones = set(opp)

        # On an empty board, occupy the deepest central cell.
        if not occupied:
            return max(
                legal,
                key=lambda x: (
                    geometry["depth"].get(x, 0),
                    -abs(x[0] - 7),
                    -abs(x[1] - 7),
                ),
            )

        my_wins = _winning_moves(
            my_stones, legal, geometry, deadline
        )
        if my_wins:
            return max(
                my_wins,
                key=lambda x: (
                    geometry["depth"].get(x, 0),
                    -x[0],
                    -x[1],
                ),
            )

        opp_wins = _winning_moves(
            opp_stones, legal, geometry, deadline
        )

        # A unique immediate threat has exactly one rational response.
        if len(opp_wins) == 1:
            return opp_wins[0]

        my_labels, my_infos = _build_components(my_stones, geometry)
        opp_labels, opp_infos = _build_components(opp_stones, geometry)

        if opp_wins:
            candidates = list(opp_wins)
        else:
            candidates = list(legal)

        move_count = len(occupied)
        if move_count < 18:
            depth_weight = 1.8
        elif move_count < 55:
            depth_weight = 1.0
        else:
            depth_weight = 0.45

        scores = {}
        for move in candidates:
            own_value = _placement_value(
                move, my_stones, my_labels, my_infos, geometry
            )
            defensive_value = _placement_value(
                move, opp_stones, opp_labels, opp_infos, geometry
            )

            enemy_contacts = sum(
                1 for x in geometry["neighbors"][move]
                if x in opp_stones
            )

            score = own_value + 0.80 * defensive_value
            score += 1.5 * enemy_contacts
            score += depth_weight * geometry["depth"].get(move, 0)

            # Stable, tiny tie-breaker.
            score += (
                (
                    move[0] * 92821
                    + move[1] * 68917
                    + len(me) * 31337
                    + len(opp) * 7919
                ) % 997
            ) * 0.00001

            scores[move] = score

        ranked = sorted(candidates, key=lambda x: scores[x], reverse=True)

        # Detect opponent moves that would create two or more immediate
        # winning continuations. Occupying such a cell is valuable defense.
        dangerous = {}
        if not opp_wins and perf_counter() < deadline:
            opp_ranked = sorted(
                legal,
                key=lambda x: _placement_value(
                    x, opp_stones, opp_labels, opp_infos, geometry
                ),
                reverse=True,
            )

            danger_limit = 12 if len(legal) < 90 else 9
            for move in opp_ranked[:danger_limit]:
                if perf_counter() > deadline:
                    break

                new_opp = set(opp_stones)
                new_opp.add(move)
                next_legal = [x for x in legal if x != move]
                continuations = _winning_moves(
                    new_opp, next_legal, geometry, deadline
                )

                if len(continuations) >= 2:
                    dangerous[move] = len(continuations)

            for move, count in dangerous.items():
                if move in scores:
                    scores[move] += 850.0 + 100.0 * min(count, 4)

        # Search the best-looking moves for our own forcing threats.
        ranked = sorted(candidates, key=lambda x: scores[x], reverse=True)
        search_limit = 24 if len(legal) < 70 else 18

        for move in ranked[:search_limit]:
            if perf_counter() > deadline:
                break

            new_me = set(my_stones)
            new_me.add(move)
            next_legal = [x for x in legal if x != move]
            continuations = _winning_moves(
                new_me, next_legal, geometry, deadline
            )
            count = len(continuations)

            if count >= 2:
                # Two distinct wins cannot both be blocked in one move.
                scores[move] += 10000.0 + 300.0 * min(count, 5)
            elif count == 1:
                scores[move] += 220.0

        best = max(candidates, key=lambda x: scores[x])
        if (
            best in occupied
            or best not in geometry["valid"]
            or not bool(valid_mask[best[0]][best[1]])
        ):
            return fallback

        return best

    except Exception:
        # The fallback was selected directly from currently legal cells.
        return fallback
