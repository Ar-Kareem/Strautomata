
import time
from collections import deque


def _popcount(x):
    return bin(x).count("1")


def _candidate_directions(mode, r, c):
    if mode == "odd":
        if c & 1:
            return [
                (-1, 0), (-1, 1), (0, 1),
                (1, 0), (0, -1), (-1, -1)
            ]
        return [
            (-1, 0), (0, 1), (1, 1),
            (1, 0), (1, -1), (0, -1)
        ]

    if mode == "ax1":
        return [
            (-1, 0), (-1, 1), (0, 1),
            (1, 0), (1, -1), (0, -1)
        ]

    return [
        (-1, 0), (0, 1), (1, 1),
        (1, 0), (0, -1), (-1, -1)
    ]


def _choose_topology(valid):
    modes = ("odd", "ax1", "ax2")
    best_mode = "odd"
    best_quality = -10**18

    for mode in modes:
        counts = [0] * 7
        for r, c in valid:
            degree = 0
            for dr, dc in _candidate_directions(mode, r, c):
                if (r + dr, c + dc) in valid:
                    degree += 1
            counts[degree] += 1

        # A regular Havannah board has six degree-3 corners,
        # degree-4 edge cells, and degree-6 interior cells.
        quality = (
            counts[6]
            + 3 * counts[4]
            + 6 * counts[3]
            - 55 * abs(counts[3] - 6)
            - 45 * (counts[0] + counts[1] + counts[2])
            - 10 * counts[5]
        )
        if mode == "odd":
            quality += 0.01  # Prefer the representation described in the prompt.

        if quality > best_quality:
            best_quality = quality
            best_mode = mode

    return best_mode


def _multi_source_dist(sources, neighbors, valid):
    inf = len(valid) + 5
    dist = {p: inf for p in valid}
    q = deque()

    for p in sources:
        if p in valid and dist[p] != 0:
            dist[p] = 0
            q.append(p)

    while q:
        p = q.popleft()
        nd = dist[p] + 1
        for z in neighbors[p]:
            if dist[z] > nd:
                dist[z] = nd
                q.append(z)
    return dist


def _build_geometry(valid):
    mode = _choose_topology(valid)
    neighbors = {}
    around = {}

    for r, c in valid:
        raw = []
        good = []
        for dr, dc in _candidate_directions(mode, r, c):
            z = (r + dr, c + dc)
            raw.append(z if z in valid else None)
            if z in valid:
                good.append(z)
        neighbors[(r, c)] = tuple(good)
        around[(r, c)] = tuple(raw)

    degree = {p: len(neighbors[p]) for p in valid}
    boundary = {p for p in valid if degree[p] < 6}

    min_degree = min((degree[p] for p in boundary), default=0)
    corners = {p for p in boundary if degree[p] == 3}

    if len(corners) != 6:
        corner_candidates = sorted(
            boundary,
            key=lambda p: (degree[p], p[0], p[1])
        )

        # Greedy spreading is only a fallback for unusual masks.
        chosen = []
        if corner_candidates:
            chosen.append(corner_candidates[0])

        while len(chosen) < min(6, len(corner_candidates)):
            best = None
            best_value = -1
            for p in corner_candidates:
                if p in chosen:
                    continue
                # Graph distance is not needed exactly here; coordinate
                # separation is enough for this rare fallback.
                sep = min(
                    abs(p[0] - q[0]) + abs(p[1] - q[1])
                    for q in chosen
                )
                value = sep * 20 - degree[p]
                if value > best_value:
                    best_value = value
                    best = p
            if best is None:
                break
            chosen.append(best)
        corners = set(chosen)

    corner_list = sorted(corners)
    corner_bit = {p: (1 << i) for i, p in enumerate(corner_list)}

    # Removing the corners separates the boundary into its six edges.
    remaining = boundary - corners
    edge_components = []
    unseen = set(remaining)

    while unseen:
        start = next(iter(unseen))
        unseen.remove(start)
        comp = {start}
        q = [start]

        while q:
            p = q.pop()
            for z in neighbors[p]:
                if z in unseen and z in boundary and z not in corners:
                    unseen.remove(z)
                    comp.add(z)
                    q.append(z)
        edge_components.append(comp)

    edge_components.sort(key=lambda comp: min(comp) if comp else (10**9, 10**9))
    edge_bit = {}
    for i, comp in enumerate(edge_components):
        bit = 1 << i
        for p in comp:
            edge_bit[p] = bit

    edge_dists = [
        _multi_source_dist(comp, neighbors, valid)
        for comp in edge_components
    ]
    corner_dists = [
        _multi_source_dist({p}, neighbors, valid)
        for p in corner_list
    ]
    boundary_dist = _multi_source_dist(boundary, neighbors, valid)

    return {
        "valid": valid,
        "mode": mode,
        "neighbors": neighbors,
        "around": around,
        "degree": degree,
        "boundary": boundary,
        "corners": corner_list,
        "corner_bit": corner_bit,
        "edges": edge_components,
        "edge_bit": edge_bit,
        "edge_dists": edge_dists,
        "corner_dists": corner_dists,
        "boundary_dist": boundary_dist,
    }


def _build_components(stones, geom):
    neighbors = geom["neighbors"]
    labels = {}
    infos = []

    edge_count = len(geom["edges"])
    corner_count = len(geom["corners"])
    inf = len(geom["valid"]) + 5

    for start in stones:
        if start in labels or start not in geom["valid"]:
            continue

        idx = len(infos)
        stack = [start]
        labels[start] = idx

        cells = []
        edge_mask = 0
        corner_mask = 0
        min_edges = [inf] * edge_count
        min_corners = [inf] * corner_count

        while stack:
            p = stack.pop()
            cells.append(p)
            edge_mask |= geom["edge_bit"].get(p, 0)
            corner_mask |= geom["corner_bit"].get(p, 0)

            for i, dmap in enumerate(geom["edge_dists"]):
                d = dmap[p]
                if d < min_edges[i]:
                    min_edges[i] = d

            for i, dmap in enumerate(geom["corner_dists"]):
                d = dmap[p]
                if d < min_corners[i]:
                    min_corners[i] = d

            for z in neighbors[p]:
                if z in stones and z not in labels:
                    labels[z] = idx
                    stack.append(z)

        infos.append({
            "size": len(cells),
            "edge_mask": edge_mask,
            "corner_mask": corner_mask,
            "min_edges": min_edges,
            "min_corners": min_corners,
        })

    return labels, infos


def _profile_after(move, labels, infos, geom):
    adjacent_ids = {
        labels[z] for z in geom["neighbors"][move] if z in labels
    }

    edge_mask = geom["edge_bit"].get(move, 0)
    corner_mask = geom["corner_bit"].get(move, 0)
    size = 1

    min_edges = [d[move] for d in geom["edge_dists"]]
    min_corners = [d[move] for d in geom["corner_dists"]]

    for idx in adjacent_ids:
        info = infos[idx]
        edge_mask |= info["edge_mask"]
        corner_mask |= info["corner_mask"]
        size += info["size"]

        for i, d in enumerate(info["min_edges"]):
            if d < min_edges[i]:
                min_edges[i] = d

        for i, d in enumerate(info["min_corners"]):
            if d < min_corners[i]:
                min_corners[i] = d

    return {
        "ids": adjacent_ids,
        "size": size,
        "edge_mask": edge_mask,
        "corner_mask": corner_mask,
        "min_edges": min_edges,
        "min_corners": min_corners,
    }


def _ring_after(stones, move, geom):
    neighbors = geom["neighbors"]

    # A newly completed ring must touch the new stone in at least two places.
    friendly_neighbors = 0
    for z in neighbors[move]:
        if z in stones:
            friendly_neighbors += 1
    if friendly_neighbors < 2:
        return False

    def occupied(p):
        return p == move or p in stones

    # Detect the common compact ring, including one around an occupied center.
    centers = [move]
    centers.extend(neighbors[move])
    for center in centers:
        ns = neighbors[center]
        if len(ns) == 6 and all(occupied(z) for z in ns):
            return True

    # Flood all cells not occupied by this player from the exterior boundary.
    target = len(geom["valid"]) - len(stones) - (0 if move in stones else 1)
    if target <= 0:
        return False

    seen = set()
    q = deque()
    for p in geom["boundary"]:
        if not occupied(p):
            seen.add(p)
            q.append(p)

    while q:
        p = q.popleft()
        for z in neighbors[p]:
            if z not in seen and not occupied(z):
                seen.add(z)
                q.append(z)

    return len(seen) < target


def _winning_moves(stones, legal, geom, stop=None, deadline=None):
    labels, infos = _build_components(stones, geom)
    result = []

    for move in legal:
        if deadline is not None and time.perf_counter() >= deadline:
            break

        profile = _profile_after(move, labels, infos, geom)

        bridge = _popcount(profile["corner_mask"]) >= 2
        fork = _popcount(profile["edge_mask"]) >= 3

        if bridge or fork or _ring_after(stones, move, geom):
            result.append(move)
            if stop is not None and len(result) >= stop:
                break

    return result


def _cyclic_connection_bonus(move, stones, labels, geom, defensive=False):
    raw = geom["around"][move]
    occupied_indices = []

    for i, z in enumerate(raw):
        if z is not None and z in stones:
            occupied_indices.append(i)

    bonus = 0.0
    for a in range(len(occupied_indices)):
        ia = occupied_indices[a]
        pa = raw[ia]
        for b in range(a + 1, len(occupied_indices)):
            ib = occupied_indices[b]
            pb = raw[ib]
            gap = (ib - ia) % 6
            adjacent = gap == 1 or gap == 5

            if not adjacent:
                bonus += 4.0 if defensive else 7.0
                if labels.get(pa) == labels.get(pb):
                    bonus += 20.0 if defensive else 42.0

    return bonus


def _virtual_connection_bonus(move, stones, occupied, geom, weight):
    nset = set(geom["neighbors"][move])
    second_ring = set()

    for x in nset:
        for y in geom["neighbors"][x]:
            if y != move and y not in nset and y in stones:
                second_ring.add(y)

    bonus = 0.0
    for y in second_ring:
        common = nset.intersection(geom["neighbors"][y])
        open_common = sum(1 for z in common if z not in occupied)
        if open_common >= 2:
            bonus += weight

    return bonus


def _score_move(move, me, opp, occupied, geom,
                my_labels, my_infos, op_labels, op_infos, phase, signature):
    my_profile = _profile_after(move, my_labels, my_infos, geom)
    op_profile = _profile_after(move, op_labels, op_infos, geom)

    my_neighbors = sum(1 for z in geom["neighbors"][move] if z in me)
    op_neighbors = sum(1 for z in geom["neighbors"][move] if z in opp)
    free_neighbors = sum(1 for z in geom["neighbors"][move] if z not in occupied)

    score = 0.0

    # Local shape and connectivity.
    score += 7.0 * my_neighbors
    score += 4.5 * op_neighbors
    score += 0.55 * free_neighbors
    score += 17.0 * max(0, len(my_profile["ids"]) - 1)
    score += 9.0 * max(0, len(op_profile["ids"]) - 1)
    score += 1.5 * (my_profile["size"] ** 0.5)

    my_edges = _popcount(my_profile["edge_mask"])
    my_corners = _popcount(my_profile["corner_mask"])
    op_edges = _popcount(op_profile["edge_mask"])
    op_corners = _popcount(op_profile["corner_mask"])

    if my_edges == 1:
        score += 7.0
    elif my_edges == 2:
        score += 34.0

    if my_corners == 1:
        score += 22.0

    if op_edges == 1:
        score += 4.0
    elif op_edges == 2:
        score += 24.0

    if op_corners == 1:
        score += 10.0

    # Estimate remaining distance for the component's best fork or bridge.
    fork_cost = 10**6
    if len(my_profile["min_edges"]) >= 3:
        fork_cost = sum(sorted(my_profile["min_edges"])[:3])

    bridge_cost = 10**6
    if len(my_profile["min_corners"]) >= 2:
        bridge_cost = sum(sorted(my_profile["min_corners"])[:2]) * 1.25

    score -= 0.75 * min(fork_cost, bridge_cost)

    # Ring-like connections: separated neighbors, especially from one component.
    score += _cyclic_connection_bonus(
        move, me, my_labels, geom, defensive=False
    )
    score += _cyclic_connection_bonus(
        move, opp, op_labels, geom, defensive=True
    )

    # Two-common-neighbor virtual connections.
    score += _virtual_connection_bonus(
        move, me, occupied, geom, 6.0
    )
    score += _virtual_connection_bonus(
        move, opp, occupied, geom, 3.0
    )

    # Early central influence; this gradually matters less as the board fills.
    score += (1.0 - phase) * 2.6 * geom["boundary_dist"][move]

    # Tiny deterministic tie breaker.
    r, c = move
    score += ((r * 73 + c * 151 + signature * 19) % 997) / 100000.0
    return score


def _choose_move(me, opp, valid, legal, start_time):
    geom = _build_geometry(valid)
    me_set = set(me).intersection(valid)
    opp_set = set(opp).intersection(valid)
    occupied = me_set | opp_set

    my_labels, my_infos = _build_components(me_set, geom)
    op_labels, op_infos = _build_components(opp_set, geom)

    phase = len(occupied) / max(1, len(valid))
    signature = 0
    for r, c in me_set:
        signature += (r + 1) * 131 + (c + 1) * 17
    for r, c in opp_set:
        signature += (r + 1) * 47 + (c + 1) * 193

    scores = {}
    for move in legal:
        scores[move] = _score_move(
            move, me_set, opp_set, occupied, geom,
            my_labels, my_infos, op_labels, op_infos,
            phase, signature
        )

    # Exact immediate tactical win.
    my_wins = _winning_moves(me_set, legal, geom)
    if my_wins:
        return max(my_wins, key=lambda p: scores[p])

    # Exact immediate defense.
    opp_wins = _winning_moves(opp_set, legal, geom)
    if opp_wins:
        return max(opp_wins, key=lambda p: scores[p])

    # On an empty board, start as centrally as possible.
    if not occupied:
        return max(
            legal,
            key=lambda p: (
                geom["boundary_dist"][p],
                scores[p]
            )
        )

    ordered = sorted(legal, key=lambda p: scores[p], reverse=True)
    deadline = start_time + 0.88

    own_threats = {}
    if len(me_set) >= 4:
        for move in ordered[:18]:
            if time.perf_counter() >= deadline:
                break

            new_stones = set(me_set)
            new_stones.add(move)
            remaining = [p for p in legal if p != move]
            threats = _winning_moves(
                new_stones, remaining, geom,
                stop=2, deadline=deadline
            )
            own_threats[move] = threats

            # Two distinct winning continuations form a double threat.
            if len(threats) >= 2:
                return move

    # Find opponent moves that would create double threats and occupy them.
    opponent_threat_counts = {}
    dangerous = []

    if len(opp_set) >= 4 and time.perf_counter() < deadline:
        opponent_order = sorted(
            legal,
            key=lambda p: (
                _score_move(
                    p, opp_set, me_set, occupied, geom,
                    op_labels, op_infos, my_labels, my_infos,
                    phase, signature + 31
                )
            ),
            reverse=True
        )

        for move in opponent_order[:16]:
            if time.perf_counter() >= deadline:
                break

            new_stones = set(opp_set)
            new_stones.add(move)
            remaining = [p for p in legal if p != move]
            threats = _winning_moves(
                new_stones, remaining, geom,
                stop=2, deadline=deadline
            )
            opponent_threat_counts[move] = len(threats)

            if len(threats) >= 2:
                dangerous.append(move)

        if dangerous:
            return max(dangerous, key=lambda p: scores[p])

    # Reward forcing moves and prophylactic occupation of single-threat makers.
    final_scores = dict(scores)

    for move, threats in own_threats.items():
        if len(threats) == 1:
            final_scores[move] += 85.0

    for move, count in opponent_threat_counts.items():
        if count == 1:
            final_scores[move] += 32.0

    return max(legal, key=lambda p: final_scores[p])


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    start_time = time.perf_counter()

    rows = len(valid_mask)
    valid = set()

    for r in range(rows):
        cols = len(valid_mask[r])
        for c in range(cols):
            try:
                playable = bool(valid_mask[r][c])
            except Exception:
                playable = False
            if playable:
                valid.add((r, c))

    occupied = set(me) | set(opp)
    legal = sorted(p for p in valid if p not in occupied)

    # A normal game state always has at least one legal move.
    if not legal:
        # Defensive API fallback for malformed/full states.
        return (0, 0)

    fallback = legal[0]

    try:
        move = _choose_move(me, opp, valid, legal, start_time)
        if move in valid and move not in occupied:
            return (int(move[0]), int(move[1]))
    except Exception:
        pass

    return (int(fallback[0]), int(fallback[1]))
