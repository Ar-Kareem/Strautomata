
import math
import time
import heapq
from collections import deque

_CACHE = {}
_TRIANGLES = [
    (m & (((m << 1) | (m >> 5)) & 63)).bit_count()
    for m in range(64)
]
_RING_WEIGHTS = (0.0, 0.015, 0.15, 0.8, 3.7, 28.0, 10000.0)


def _indices(bits):
    while bits:
        b = bits & -bits
        yield b.bit_length() - 1
        bits ^= b


class _Geometry:
    def __init__(self, rows, cols, board):
        self.rows = rows
        self.cols = cols
        self.L = rows * cols
        self.board = board
        self.cells = list(_indices(board))
        self.bit = [1 << i for i in range(self.L)]

        # Try axial coordinates and the common offset-coordinate layouts.
        best_score = -10**20
        best = None

        for kind in range(6):
            all_six = [[] for _ in range(self.L)]
            all_neighbors = [[] for _ in range(self.L)]

            for i in self.cells:
                r, c = divmod(i, cols)
                if kind == 0:
                    directions = (
                        (1, 0), (1, 1), (0, 1),
                        (-1, 0), (-1, -1), (0, -1)
                    )
                elif kind == 1:
                    directions = (
                        (1, 0), (0, 1), (-1, 1),
                        (-1, 0), (0, -1), (1, -1)
                    )
                elif kind in (2, 3):
                    a = -((c + kind - 2) & 1)
                    directions = (
                        (1, 0), (a + 1, 1), (a, 1),
                        (-1, 0), (a, -1), (a + 1, -1)
                    )
                else:
                    a = -((r + kind - 4) & 1)
                    directions = (
                        (0, 1), (1, a + 1), (1, a),
                        (0, -1), (-1, a), (-1, a + 1)
                    )

                six = []
                for dr, dc in directions:
                    rr, cc = r + dr, c + dc
                    j = rr * cols + cc
                    if (0 <= rr < rows and 0 <= cc < cols
                            and board & (1 << j)):
                        six.append(j)
                        all_neighbors[i].append(j)
                    else:
                        six.append(-1)
                all_six[i] = six

            degrees = [len(all_neighbors[i]) for i in self.cells]
            score = (
                20 * sum(degrees)
                - 3 * abs(sum(d == 3 for d in degrees) - 6)
                - 12 * sum(d < 3 for d in degrees)
            )
            if score > best_score:
                best_score = score
                best = all_six, all_neighbors

        self.six, self.nb = best
        self.nb_bits = [0] * self.L
        self.entries = [[] for _ in range(self.L)]
        self.interior = []

        for i in self.cells:
            mask = 0
            entries = []
            for direction, j in enumerate(self.six[i]):
                if j >= 0:
                    mask |= self.bit[j]
                    entries.append((j, self.bit[j], 1 << direction))
            self.nb_bits[i] = mask
            self.entries[i] = entries
            if len(self.nb[i]) == 6:
                self.interior.append(i)

        boundary = [i for i in self.cells if len(self.nb[i]) < 6]
        corners = [i for i in boundary if len(self.nb[i]) <= 3]

        # A regular Havannah board has precisely six such vertices.
        if len(corners) > 6:
            corners = sorted(
                corners,
                key=lambda i: (
                    len(self.nb[i]),
                    -abs(i // cols - (rows - 1) / 2)
                    - abs(i % cols - (cols - 1) / 2)
                )
            )[:6]

        self.corner = [0] * self.L
        for k, i in enumerate(corners):
            self.corner[i] = 1 << k

        corner_set = set(corners)
        remaining = set(boundary) - corner_set
        edge_groups = []
        while remaining:
            seed = remaining.pop()
            group = [seed]
            stack = [seed]
            while stack:
                u = stack.pop()
                for v in self.nb[u]:
                    if v in remaining:
                        remaining.remove(v)
                        stack.append(v)
                        group.append(v)
            edge_groups.append(group)

        edge_groups.sort(key=lambda group: (-len(group), min(group)))
        edge_groups = edge_groups[:6]
        self.edge = [0] * self.L
        for k, group in enumerate(edge_groups):
            for i in group:
                self.edge[i] = 1 << k

        edge_sources = [
            sum(self.bit[i] for i in group) for group in edge_groups
        ]
        corner_sources = [self.bit[i] for i in corners]
        edge_sources += [0] * (6 - len(edge_sources))
        corner_sources += [0] * (6 - len(corner_sources))
        self.sources = edge_sources[:6] + corner_sources[:6]

        # Geometric centrality, independent of coordinate convention.
        edge_distances = []
        for source in edge_sources[:6]:
            dist = [50] * self.L
            queue = deque()
            for i in _indices(source):
                dist[i] = 0
                queue.append(i)
            while queue:
                u = queue.popleft()
                nd = dist[u] + 1
                for v in self.nb[u]:
                    if nd < dist[v]:
                        dist[v] = nd
                        queue.append(v)
            edge_distances.append(dist)

        self.central = [0] * self.L
        for i in self.cells:
            self.central[i] = min(d[i] for d in edge_distances)

        # Two-step virtual connections with two alternative carriers.
        self.virtual = [[] for _ in range(self.L)]
        for i in self.cells:
            near = 0
            for j in self.nb[i]:
                near |= self.nb_bits[j]
            near &= board & ~self.nb_bits[i] & ~self.bit[i]
            for j in _indices(near):
                common = self.nb_bits[i] & self.nb_bits[j]
                if common.bit_count() == 2:
                    self.virtual[i].append((j, common))


def _components(stones, g):
    labels = [-1] * g.L
    edges = []
    corners = []
    members = []
    frontier = 0
    unseen = stones

    while unseen:
        seed_bit = unseen & -unseen
        seed = seed_bit.bit_length() - 1
        unseen ^= seed_bit
        cid = len(edges)
        stack = [seed]
        labels[seed] = cid
        group = []
        em = cm = 0

        while stack:
            u = stack.pop()
            group.append(u)
            em |= g.edge[u]
            cm |= g.corner[u]
            frontier |= g.nb_bits[u]
            fresh = g.nb_bits[u] & unseen
            unseen &= ~fresh
            for v in _indices(fresh):
                labels[v] = cid
                stack.append(v)

        edges.append(em)
        corners.append(cm)
        members.append(group)

    return labels, edges, corners, members, frontier


def _winning_moves(stones, free, info, g, wheels=True):
    labels, component_edges, component_corners, _, frontier = info
    result = 0

    # Rings surrounding an occupied friendly cell require this additional
    # check: their induced graph can consist entirely of triangular faces.
    if wheels:
        for center in g.interior:
            missing = g.nb_bits[center] & ~stones
            if missing and not (missing & (missing - 1)):
                result |= missing & free

    candidates = free & frontier & ~result
    for x in _indices(candidates):
        em = g.edge[x]
        cm = g.corner[x]
        roots = set()
        local = 0

        for j, bj, direction_bit in g.entries[x]:
            if stones & bj:
                local |= direction_bit
                root = labels[j]
                if root not in roots:
                    roots.add(root)
                    em |= component_edges[root]
                    cm |= component_corners[root]

        if cm.bit_count() >= 2 or em.bit_count() >= 3:
            result |= g.bit[x]
            continue

        # In the triangular adjacency graph, a newly formed non-triangular
        # bounded face encloses at least one board cell. Existing terminal
        # positions are never passed to this routine.
        cycles_added = local.bit_count() - len(roots)
        if cycles_added > _TRIANGLES[local]:
            result |= g.bit[x]

    return result


def _pair_graph(stones, enemy, free, info, g, deadline):
    """links[x] contains y when placing both x and y wins."""
    links = [0] * g.L

    # Seed all elementary ring pairs; also covers friendly-filled rings.
    for center in g.interior:
        missing = g.nb_bits[center] & ~stones
        if missing.bit_count() == 2 and not (missing & ~free):
            a = missing & -missing
            b = missing ^ a
            ia = a.bit_length() - 1
            ib = b.bit_length() - 1
            links[ia] |= b
            links[ib] |= a

    frontier = info[4]
    near = frontier
    for i in _indices(frontier):
        near |= g.nb_bits[i]

    candidates = list(_indices(near & free))
    candidates.sort(
        key=lambda x: (
            -(g.nb_bits[x] & stones).bit_count(),
            -g.central[x],
            x
        )
    )

    for count, x in enumerate(candidates):
        if count % 4 == 0 and time.perf_counter() >= deadline:
            return links, False
        bx = g.bit[x]

        # Each unordered pair needs testing only once.
        higher = free & ~((bx << 1) - 1)
        if not higher:
            continue
        updated = stones | bx
        updated_info = _components(updated, g)
        wins = _winning_moves(
            updated, higher, updated_info, g, wheels=False
        )
        links[x] |= wins
        for y in _indices(wins):
            links[y] |= bx

    return links, True


def _distance_maps(stones, enemy, free, g):
    cost = [50.0] * g.L
    occupied = stones | enemy
    virtual_edges = [[] for _ in range(g.L)]

    for i in g.cells:
        bi = g.bit[i]
        if enemy & bi:
            continue
        if stones & bi:
            cost[i] = 0.0
            for j, common in g.virtual[i]:
                if stones & g.bit[j] and not (common & occupied):
                    virtual_edges[i].append(j)
        else:
            cost[i] = 1.0 + 0.10 * (
                g.nb_bits[i] & enemy
            ).bit_count()

    maps = []
    for source in g.sources:
        dist = [50.0] * g.L
        heap = []
        for i in _indices(source & ~enemy):
            dist[i] = cost[i]
            heapq.heappush(heap, (dist[i], i))

        while heap:
            d, u = heapq.heappop(heap)
            if d != dist[u]:
                continue
            for v in g.nb[u]:
                if enemy & g.bit[v]:
                    continue
                nd = d + cost[v]
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))
            for v in virtual_edges[u]:
                nd = d + 0.30
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))

        maps.append(dist)

    return maps, cost


def _group_value(distances, size):
    edge_distances = sorted(distances[:6])
    corner_distances = sorted(distances[6:])
    fork_cost = sum(edge_distances[:3])
    bridge_cost = sum(corner_distances[:2]) + 2.0
    return (
        70.0 / (4.0 + fork_cost)
        + 55.0 / (4.0 + bridge_cost)
        + 0.25 * math.sqrt(size)
        + 0.08 * sum(1.0 / (1.0 + d) for d in edge_distances)
    )


def _positional_scores(stones, enemy, free, info, g):
    labels, _, _, actual_groups, _ = info
    maps, costs = _distance_maps(stones, enemy, free, g)
    count = len(actual_groups)
    parent = list(range(count))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    occupied = stones | enemy
    for i in _indices(stones):
        for j, common in g.virtual[i]:
            if (j > i and stones & g.bit[j]
                    and not (common & occupied)):
                a, b = find(labels[i]), find(labels[j])
                if a != b:
                    parent[b] = a

    grouped = {}
    for k, members in enumerate(actual_groups):
        grouped.setdefault(find(k), []).extend(members)

    group_ids = [-1] * g.L
    group_distances = []
    group_sizes = []
    group_values = []

    for members in grouped.values():
        gid = len(group_sizes)
        ds = [min(m[i] for i in members) for m in maps]
        group_distances.append(ds)
        group_sizes.append(len(members))
        group_values.append(_group_value(ds, len(members)))
        for i in members:
            group_ids[i] = gid

    best = max(group_values, default=0.0)
    scores = [0.0] * g.L
    opening = max(0.0, (12 - stones.bit_count()) / 12.0)

    for x in _indices(free):
        joined = set()
        actual_joined = set()
        adjacent = 0
        virtual_count = 0

        for j in g.nb[x]:
            if stones & g.bit[j]:
                joined.add(group_ids[j])
                actual_joined.add(labels[j])
                adjacent += 1
        for j, common in g.virtual[x]:
            if stones & g.bit[j] and not (common & occupied):
                joined.add(group_ids[j])
                virtual_count += 1

        if not joined:
            scores[x] = -0.7 + 0.025 * opening * g.central[x]
            continue

        ds = [max(0.0, maps[k][x] - costs[x]) for k in range(12)]
        size = 1
        previous = 0.0
        for gid in joined:
            size += group_sizes[gid]
            previous = max(previous, group_values[gid])
            old_ds = group_distances[gid]
            for k in range(12):
                if old_ds[k] < ds[k]:
                    ds[k] = old_ds[k]

        value = _group_value(ds, size)
        scores[x] = (
            3.2 * max(0.0, value - best)
            + 0.35 * (value - previous)
            + 0.10 * min(adjacent, 2)
            - 0.14 * max(0, adjacent - 3)
            + 0.18 * min(virtual_count, 2)
            + 0.35 * max(0, len(actual_joined) - 1)
            + 0.025 * opening * g.central[x]
        )

    return scores


def _ring_features(stones, enemy, free, g):
    gains = [0.0] * g.L
    denial = [0.0] * g.L
    potential = 0.0

    for center in g.interior:
        perimeter = g.nb_bits[center]
        if perimeter & enemy:
            continue
        k = (perimeter & stones).bit_count()
        base = _RING_WEIGHTS[k]
        potential += base
        if k == 6:
            continue
        gain = _RING_WEIGHTS[k + 1] - base
        for x in _indices(perimeter & free):
            gains[x] += gain
            denial[x] += base

    return gains, denial, potential


def _ring_potential(stones, enemy, g):
    total = 0.0
    for center in g.interior:
        perimeter = g.nb_bits[center]
        if not (perimeter & enemy):
            total += _RING_WEIGHTS[(perimeter & stones).bit_count()]
    return total


def _forcing_search(stones, enemy, free, g, deadline,
                    root_links=None, root_scores=None):
    nodes = [0]
    failed = set()

    def solve(mine, theirs, empty, depth, supplied=None, ordering=None):
        if time.perf_counter() >= deadline or nodes[0] >= 20:
            return -1
        nodes[0] += 1
        key = (mine, theirs, depth)
        if key in failed:
            return -1

        mine_info = _components(mine, g)
        wins = _winning_moves(mine, empty, mine_info, g)
        if wins:
            return (wins & -wins).bit_length() - 1
        if depth <= 0:
            return -1

        their_info = _components(theirs, g)
        threats = _winning_moves(theirs, empty, their_info, g)
        if threats.bit_count() >= 2:
            failed.add(key)
            return -1
        allowed = threats if threats else empty

        if supplied is None:
            links, _ = _pair_graph(
                mine, theirs, empty, mine_info, g, deadline
            )
        else:
            links = supplied

        for x in _indices(allowed):
            if links[x].bit_count() >= 2:
                return x

        choices = [
            x for x in _indices(allowed)
            if links[x].bit_count() == 1
        ]
        if ordering is None:
            choices.sort(
                key=lambda x: (
                    (g.nb_bits[x] & mine).bit_count()
                    + 0.05 * g.central[x]
                ),
                reverse=True
            )
        else:
            choices.sort(key=lambda x: ordering[x], reverse=True)

        for x in choices[:6]:
            if time.perf_counter() >= deadline:
                break
            bx = g.bit[x]
            by = links[x]
            # The opponent must occupy the sole immediate winning point.
            answer = solve(
                mine | bx,
                theirs | by,
                empty & ~(bx | by),
                depth - 1
            )
            if answer >= 0:
                return x

        failed.add(key)
        return -1

    return solve(
        stones, enemy, free, 3,
        supplied=root_links, ordering=root_scores
    )


def _quiet_win_certificate(links, opponent_links, free, first, g):
    """Certify a quiet setup against every opponent reply."""
    bx = g.bit[first]
    empty = free & ~bx
    centers = [
        x for x in _indices(empty) if links[x].bit_count() >= 2
    ]
    if not centers:
        return False

    for reply in _indices(empty):
        br = g.bit[reply]
        counter = opponent_links[reply] & ~bx
        number = counter.bit_count()

        if number >= 2:
            return False
        if number == 1:
            forced = counter.bit_length() - 1
            if (links[forced] & ~br).bit_count() < 2:
                return False
        else:
            if not any(
                center != reply
                and (links[center] & ~br).bit_count() >= 2
                for center in centers
            ):
                return False

    return True


def _choose(mine, theirs, free, g, started):
    legal = list(_indices(free))

    if not mine:
        # Start centrally, but do not immediately crowd an enemy opening.
        return max(
            legal,
            key=lambda x: (
                3.0 * g.central[x]
                - 4.5 * (g.nb_bits[x] & theirs).bit_count()
                - 0.002 * (
                    (x // g.cols - (g.rows - 1) / 2.0) ** 2
                    + (x % g.cols - (g.cols - 1) / 2.0) ** 2
                ),
                -x
            )
        )

    my_info = _components(mine, g)
    their_info = _components(theirs, g)

    wins = _winning_moves(mine, free, my_info, g)
    if wins:
        return max(
            _indices(wins),
            key=lambda x: ((g.nb_bits[x] & mine).bit_count(), -x)
        )

    threats = _winning_moves(theirs, free, their_info, g)
    if threats:
        # Multiple immediate threats cannot all be blocked, but the move
        # remains legal and blocks the most locally useful one.
        return max(
            _indices(threats),
            key=lambda x: (
                (g.nb_bits[x] & mine).bit_count(),
                g.central[x],
                -x
            )
        )

    my_links, _ = _pair_graph(
        mine, theirs, free, my_info, g, started + 0.26
    )
    double_moves = [
        x for x in legal if my_links[x].bit_count() >= 2
    ]
    if double_moves:
        return max(
            double_moves,
            key=lambda x: (
                my_links[x].bit_count(),
                g.central[x],
                -x
            )
        )

    their_links, opponent_graph_complete = _pair_graph(
        theirs, mine, free, their_info, g, started + 0.43
    )

    my_position = _positional_scores(
        mine, theirs, free, my_info, g
    )
    their_position = _positional_scores(
        theirs, mine, free, their_info, g
    )
    my_ring_gain, _, my_ring_base = _ring_features(
        mine, theirs, free, g
    )
    _, their_ring_denial, their_ring_base = _ring_features(
        theirs, mine, free, g
    )

    opponent_forks = [
        x for x in legal if their_links[x].bit_count() >= 2
    ]
    scores = [-10**12] * g.L

    for x in legal:
        bx = g.bit[x]
        own_threat_count = my_links[x].bit_count()
        losing = False

        if own_threat_count == 1:
            by = my_links[x]
            y = by.bit_length() - 1

            if (their_links[y] & ~bx).bit_count() >= 2:
                losing = True

            after_mine = mine | bx
            after_theirs = theirs | by
            ring_change = (
                _ring_potential(after_mine, after_theirs, g)
                - my_ring_base
                - 0.90 * (
                    _ring_potential(after_theirs, after_mine, g)
                    - their_ring_base
                )
            )
            value = (
                my_position[x]
                + 0.80 * max(0.0, their_position[x])
                - 0.82 * max(0.0, their_position[y])
                - 0.50 * max(0.0, my_position[y])
                + ring_change
                + 0.15
            )
        else:
            for center in opponent_forks:
                if center != x:
                    if (their_links[center] & ~bx).bit_count() >= 2:
                        losing = True
                        break
            value = (
                my_position[x]
                + 0.85 * max(0.0, their_position[x])
                + my_ring_gain[x]
                + 0.85 * their_ring_denial[x]
            )

        if losing:
            value -= 1000000.0

        value += 0.003 * g.central[x]
        value += 0.000001 * (
            (x * 1103515245 + mine.bit_count() * 12345) & 1023
        )
        scores[x] = value

    if time.perf_counter() < started + 0.70:
        forced_win = _forcing_search(
            mine, theirs, free, g, started + 0.72,
            root_links=my_links, root_scores=scores
        )
        if forced_win >= 0:
            return forced_win

    # Examine promising non-forcing setups. In particular, look for
    # multiple overlapping threats that no single reply can neutralize.
    ranked = sorted(legal, key=lambda x: scores[x], reverse=True)
    best_base = scores[ranked[0]]
    old_pairs = sum(v.bit_count() for v in my_links) // 2
    examined = 0

    for x in ranked:
        if examined >= 6 or time.perf_counter() >= started + 0.87:
            break
        if my_links[x] or scores[x] < best_base - 4.0:
            continue
        if scores[x] < -100000.0:
            continue

        examined += 1
        bx = g.bit[x]
        updated = mine | bx
        updated_info = _components(updated, g)
        links, _ = _pair_graph(
            updated, theirs, free & ~bx, updated_info,
            g, started + 0.89
        )

        if opponent_graph_complete and _quiet_win_certificate(
                links, their_links, free, x, g):
            return x

        centers = sum(v.bit_count() >= 2 for v in links)
        pairs = sum(v.bit_count() for v in links) // 2
        scores[x] += (
            0.55 * min(centers, 4)
            + 0.12 * max(0, pairs - old_pairs)
        )

    return max(legal, key=lambda x: scores[x])


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    started = time.perf_counter()
    rows = len(valid_mask)
    cols = len(valid_mask[0])

    mine = 0
    theirs = 0
    for r, c in me:
        r, c = int(r), int(c)
        if 0 <= r < rows and 0 <= c < cols:
            mine |= 1 << (r * cols + c)
    for r, c in opp:
        r, c = int(r), int(c)
        if 0 <= r < rows and 0 <= c < cols:
            theirs |= 1 << (r * cols + c)

    occupied = mine | theirs
    board = occupied
    free = 0
    fallback = None

    for r in range(rows):
        for c in range(cols):
            if bool(valid_mask[r][c]):
                b = 1 << (r * cols + c)
                board |= b
                if not (occupied & b):
                    free |= b
                    if fallback is None:
                        fallback = (r, c)

    # A nonterminal Havannah position always has a legal placement.
    if fallback is None:
        # Defensive handling of an out-of-contract terminal invocation.
        return (0, 0)

    try:
        key = (rows, cols, board)
        geometry = _CACHE.get(key)
        if geometry is None:
            geometry = _Geometry(rows, cols, board)
            if len(_CACHE) >= 4:
                _CACHE.clear()
            _CACHE[key] = geometry

        move = _choose(mine, theirs, free, geometry, started)
        if isinstance(move, int) and move >= 0 and free & (1 << move):
            r, c = divmod(move, cols)
            return (int(r), int(c))
    except Exception:
        # Never sacrifice move legality to an evaluation failure.
        pass

    return fallback
