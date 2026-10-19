
import math
import time
from heapq import heappush, heappop

_GEOMETRY_CACHE = {}
_WIN = 1000000.0


class _Geometry:
    pass


def _bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def _geometry(cells):
    cached = _GEOMETRY_CACHE.get(cells)
    if cached is not None:
        return cached

    g = _Geometry()
    g.cells = cells
    g.n = len(cells)
    g.index = {p: i for i, p in enumerate(cells)}
    g.full = (1 << g.n) - 1

    orientations = [
        ((1, 0), (1, 1), (0, 1), (-1, 0), (-1, -1), (0, -1)),
        ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1)),
    ]
    choices = []
    for orientation, directions in enumerate(orientations):
        cyclic = []
        neighbors = []
        for r, c in cells:
            row = [g.index.get((r + dr, c + dc), -1)
                   for dr, dc in directions]
            cyclic.append(row)
            neighbors.append([x for x in row if x >= 0])
        degrees = [len(x) for x in neighbors]
        penalty = (10 * sum(d not in (3, 4, 6) for d in degrees)
                   + abs(degrees.count(3) - 6))
        choices.append(((penalty, -degrees.count(6)),
                        orientation, cyclic, neighbors))

    _, g.orientation, g.cyclic, g.neighbors = min(
        choices, key=lambda x: x[0]
    )
    g.nb = [sum(1 << j for j in row) for row in g.neighbors]
    boundary = {i for i in range(g.n) if len(g.neighbors[i]) < 6}
    corners = [i for i in boundary if len(g.neighbors[i]) == 3]

    # The usual hexagonal mask has exactly six degree-three corners.
    if len(corners) != 6:
        sign = 1 if g.orientation == 0 else -1
        chosen = set()
        for k in range(6):
            angle = math.pi * k / 3
            ux, uy = math.cos(angle), math.sin(angle)
            pool = boundary or set(range(g.n))
            ranked = sorted(
                pool,
                key=lambda i: (
                    ux * (cells[i][1] - sign * cells[i][0] * 0.5)
                    + uy * cells[i][0] * 0.866025403784
                ),
                reverse=True,
            )
            for i in ranked:
                if i not in chosen:
                    chosen.add(i)
                    break
        corners = sorted(chosen)

    g.corner = [0] * g.n
    g.corner_sources = []
    for k, i in enumerate(sorted(corners)[:6]):
        g.corner[i] = 1 << k
        g.corner_sources.append([i])

    remaining = boundary - set(corners)
    edge_groups = []
    while remaining:
        first = remaining.pop()
        group = [first]
        stack = [first]
        while stack:
            v = stack.pop()
            for w in g.neighbors[v]:
                if w in remaining:
                    remaining.remove(w)
                    stack.append(w)
                    group.append(w)
        edge_groups.append(group)

    edge_groups.sort(key=lambda x: (-len(x), min(x)))
    g.edge_sources = edge_groups[:6]
    g.edge = [0] * g.n
    for k, group in enumerate(g.edge_sources):
        for i in group:
            g.edge[i] = 1 << k

    # Virtual connections: nonadjacent cells sharing two neighbors.
    g.virtual = []
    for i in range(g.n):
        nearby = 0
        for j in g.neighbors[i]:
            nearby |= g.nb[j]
        nearby &= ~g.nb[i]
        nearby &= ~((1 << (i + 1)) - 1)
        for j in _bits(nearby):
            common = g.nb[i] & g.nb[j]
            if common.bit_count() == 2:
                g.virtual.append((i, j, common))

    g.virtual_at = [[] for _ in range(g.n)]
    for i, j, common in g.virtual:
        g.virtual_at[i].append((j, common))
        g.virtual_at[j].append((i, common))

    # Boundaries surrounding one, two, or three connected interior cells.
    interior = {i for i in range(g.n) if len(g.neighbors[i]) == 6}
    rings = set()
    for i in interior:
        rings.add(g.nb[i])
        for j in g.neighbors[i]:
            if j <= i or j not in interior:
                continue
            region = (1 << i) | (1 << j)
            rings.add((g.nb[i] | g.nb[j]) & ~region)
            for k in g.neighbors[j]:
                if (k > j and k in interior
                        and (g.nb[i] & (1 << k))):
                    region3 = region | (1 << k)
                    rings.add(
                        (g.nb[i] | g.nb[j] | g.nb[k]) & ~region3
                    )
    g.rings = tuple(rings)

    cr = sum(r for r, c in cells) / max(1, g.n)
    cc = sum(c for r, c in cells) / max(1, g.n)
    sign = 1 if g.orientation == 0 else -1
    g.central = [
        -((r - cr) ** 2 + (c - cc) ** 2
          - sign * (r - cr) * (c - cc)) / 100.0
        for r, c in cells
    ]

    if len(_GEOMETRY_CACHE) >= 4:
        _GEOMETRY_CACHE.clear()
    _GEOMETRY_CACHE[cells] = g
    return g


def _play(me, opp, valid_mask, legal_coordinates, started):
    occupied_coordinates = set(me) | set(opp)
    rows = len(valid_mask)
    cells = tuple(
        (r, c)
        for r in range(rows)
        for c in range(len(valid_mask[r]))
        if bool(valid_mask[r][c]) or (r, c) in occupied_coordinates
    )
    g = _geometry(cells)
    n = g.n
    deadline = started + 0.92

    a = sum(1 << g.index[p] for p in set(me) if p in g.index)
    b = sum(1 << g.index[p] for p in set(opp) if p in g.index)
    empty = g.full & ~(a | b)
    legal = [g.index[p] for p in legal_coordinates]
    legal_set = set(legal)

    fallback = max(legal, key=lambda i: g.central[i])

    if not a and b.bit_count() <= 2:
        move = max(
            legal,
            key=lambda i: (
                g.central[i] - 0.20 * (g.nb[i] & b).bit_count()
            ),
        )
        return g.cells[move]

    component_cache = {}
    win_cache = {}
    evaluation_cache = {}

    def components(stones):
        cached = component_cache.get(stones)
        if cached is not None:
            return cached
        labels = [-1] * n
        edges = []
        corners = []
        frontier = 0
        remaining = stones
        while remaining:
            first_bit = remaining & -remaining
            first = first_bit.bit_length() - 1
            remaining ^= first_bit
            label = len(edges)
            labels[first] = label
            stack = [first]
            em = cm = 0
            while stack:
                v = stack.pop()
                em |= g.edge[v]
                cm |= g.corner[v]
                frontier |= g.nb[v]
                new = g.nb[v] & remaining
                remaining &= ~new
                for w in _bits(new):
                    labels[w] = label
                    stack.append(w)
            edges.append(em)
            corners.append(cm)
        result = (labels, edges, corners, frontier)
        component_cache[stones] = result
        return result

    def winning_moves(stones, vacancies):
        key = (stones, vacancies)
        cached = win_cache.get(key)
        if cached is not None:
            return cached

        labels, edges, corners, frontier = components(stones)
        wins = []
        for v in _bits(vacancies & frontier):
            cyclic = g.cyclic[v]
            labs = [labels[w] if w >= 0 else -1 for w in cyclic]
            joined = {x for x in labs if x >= 0}
            em = g.edge[v]
            cm = g.corner[v]
            for label in joined:
                em |= edges[label]
                cm |= corners[label]
            if em.bit_count() >= 3 or cm.bit_count() >= 2:
                wins.append(v)
                continue

            count = sum(x >= 0 for x in labs)
            if count < 2:
                continue

            # Separate occupied neighbor runs joined through an existing
            # component close a nontrivial loop around a lattice cell.
            seen = set()
            ring = False
            for k in range(6):
                if labs[k] >= 0 and labs[k - 1] < 0:
                    if labs[k] in seen:
                        ring = True
                        break
                    seen.add(labs[k])

            # This also recognizes closing a ring whose interior is filled
            # with friendly stones, rather than empty or hostile cells.
            if not ring and count >= 3:
                after = stones | (1 << v)
                for w in g.neighbors[v]:
                    if ((stones & (1 << w))
                            and len(g.neighbors[w]) == 6
                            and (g.nb[w] & after) == g.nb[w]):
                        ring = True
                        break

            if ring:
                wins.append(v)

        result = tuple(wins)
        win_cache[key] = result
        return result

    my_wins = winning_moves(a, empty)
    if my_wins:
        return g.cells[max(my_wins, key=lambda i: g.central[i])]

    their_wins = winning_moves(b, empty)
    if their_wins:
        # If there are several independent immediate wins, the position
        # is already lost; still return a legal blocking move.
        return g.cells[max(their_wins, key=lambda i: g.central[i])]

    urgency_weights = (
        0.0, 100000.0, 100.0, 12.0, 2.0,
        0.25, 0.025, 0.002, 0.0002, 0.00002, 0.0,
    )

    def urgency(own, enemy):
        scores = [0.0] * n
        for ring in g.rings:
            if ring & enemy:
                continue
            missing = ring & ~own
            count = missing.bit_count()
            if 0 < count < len(urgency_weights):
                weight = urgency_weights[count]
                if weight:
                    for v in _bits(missing):
                        scores[v] += weight
        return scores

    def quick_scores(own, enemy, own_surface=None, enemy_surface=None):
        us = urgency(own, enemy)
        them = urgency(enemy, own)
        occupied = own | enemy
        result = [0.0] * n
        for v in legal:
            friendly = (g.nb[v] & own).bit_count()
            hostile = (g.nb[v] & enemy).bit_count()
            triangles = 0
            cyc = g.cyclic[v]
            for k in range(6):
                x, y = cyc[k], cyc[k - 1]
                if (x >= 0 and y >= 0
                        and own & (1 << x) and own & (1 << y)):
                    triangles += 1
            virtuals = sum(
                bool(own & (1 << w)) and not (common & occupied)
                for w, common in g.virtual_at[v]
            )
            value = (
                us[v] + 1.02 * them[v]
                + 0.28 * friendly + 0.10 * hostile
                - 0.29 * triangles + 0.55 * virtuals
                + 0.08 * g.central[v]
            )
            if own_surface is not None:
                value += own_surface[v] + 0.95 * enemy_surface[v]
            result[v] = value
        return result

    initial_quick = quick_scores(a, b)
    ordered = sorted(legal, key=lambda i: initial_quick[i], reverse=True)
    fallback = ordered[0]

    # Map every placement to its winning continuations.
    my_threats = {}
    their_threats = {}
    for k, v in enumerate(ordered):
        if k % 16 == 0 and time.perf_counter() > started + 0.30:
            break
        following = winning_moves(a | (1 << v), empty & ~(1 << v))
        my_threats[v] = following
        if len(following) >= 2:
            return g.cells[v]

    for k, v in enumerate(ordered):
        if k % 16 == 0 and time.perf_counter() > started + 0.42:
            break
        their_threats[v] = winning_moves(
            b | (1 << v), empty & ~(1 << v)
        )

    their_forks = [
        (v, ws) for v, ws in their_threats.items() if len(ws) >= 2
    ]
    safe = []
    for v in ordered:
        threats = my_threats.get(v, ())
        losing = False
        if len(threats) == 1:
            reply = threats[0]
            continuation = their_threats.get(reply, ())
            losing = sum(w != v for w in continuation) >= 2
        elif not threats:
            losing = any(
                fork != v and sum(w != v for w in ws) >= 2
                for fork, ws in their_forks
            )
        if not losing:
            safe.append(v)

    if not safe:
        return g.cells[max(
            legal,
            key=lambda v: (
                1000 * bool(my_threats.get(v))
                + 100 * len(their_threats.get(v, ()))
                + initial_quick[v]
            ),
        )]

    ring_values = (
        1000.0, 100.0, 5.0, 0.85, 0.13,
        0.017, 0.002, 0.0002, 0.00002, 0.000002, 0.0,
    )

    def strategic(own, enemy):
        key = (own, enemy)
        cached = evaluation_cache.get(key)
        if cached is not None:
            return cached

        occupied = own | enemy
        costs = [2] * n
        for v in _bits(own):
            costs[v] = 0
        for v in _bits(enemy):
            costs[v] = 10000

        virtual_links = [[] for _ in range(n)]
        virtual_count = 0
        for i, j, common in g.virtual:
            if ((own & (1 << i)) and (own & (1 << j))
                    and not (occupied & common)):
                virtual_links[i].append(j)
                virtual_links[j].append(i)
                virtual_count += 1

        def distances(sources):
            dist = [10000] * n
            heap = []
            for v in sources:
                if costs[v] < 10000:
                    dist[v] = costs[v]
                    heappush(heap, (costs[v], v))
            while heap:
                d, v = heappop(heap)
                if d != dist[v]:
                    continue
                for w in g.neighbors[v]:
                    nd = d + costs[w]
                    if nd < dist[w]:
                        dist[w] = nd
                        heappush(heap, (nd, w))
                for w in virtual_links[v]:
                    nd = d + 1
                    if nd < dist[w]:
                        dist[w] = nd
                        heappush(heap, (nd, w))
            return dist

        c1 = [10000] * n
        c2 = [10000] * n
        for sources in g.corner_sources:
            dist = distances(sources)
            for v, d in enumerate(dist):
                if d < c1[v]:
                    c2[v] = c1[v]
                    c1[v] = d
                elif d < c2[v]:
                    c2[v] = d

        e1 = [10000] * n
        e2 = [10000] * n
        e3 = [10000] * n
        for sources in g.edge_sources:
            dist = distances(sources)
            for v, d in enumerate(dist):
                if d < e1[v]:
                    e3[v], e2[v], e1[v] = e2[v], e1[v], d
                elif d < e2[v]:
                    e3[v], e2[v] = e2[v], d
                elif d < e3[v]:
                    e3[v] = d

        best_bridge = best_fork = 10000
        surface = [0.0] * n
        for v in range(n):
            if costs[v] >= 10000:
                continue
            bridge = c1[v] + c2[v] - costs[v]
            fork = e1[v] + e2[v] + e3[v] - 2 * costs[v]
            best_bridge = min(best_bridge, bridge)
            best_fork = min(best_fork, fork)
            surface[v] = (
                7.0 * math.exp(-0.18 * min(bridge, 200))
                + 8.0 * math.exp(-0.18 * min(fork, 200))
            )

        connection_value = (
            7.0 * math.exp(-0.18 * min(best_bridge, 200))
            + 8.0 * math.exp(-0.18 * min(best_fork, 200))
        )

        ring_sum = ring_best = 0.0
        for ring in g.rings:
            if ring & enemy:
                continue
            missing = (ring & ~own).bit_count()
            value = ring_values[min(missing, len(ring_values) - 1)]
            ring_sum += value
            ring_best = max(ring_best, value)

        contacts = triangle_count = 0
        central = 0.0
        for v in _bits(own):
            contacts += (g.nb[v] & own).bit_count()
            central += g.central[v]
            cyc = g.cyclic[v]
            for k in range(6):
                x, y = cyc[k], cyc[k - 1]
                if (x >= 0 and y >= 0
                        and own & (1 << x) and own & (1 << y)):
                    triangle_count += 1

        early = max(0.0, (16 - occupied.bit_count()) / 16.0)
        value = (
            connection_value + 0.78 * ring_best + 0.22 * ring_sum
            + 0.0175 * contacts - (0.055 / 3.0) * triangle_count
            + 0.06 * virtual_count + 0.08 * early * central
        )
        result = (value, surface)
        evaluation_cache[key] = result
        return result

    def evaluate(aa, bb):
        return strategic(aa, bb)[0] - 1.04 * strategic(bb, aa)[0]

    def resolve(aa, bb, turn):
        """Follow mandatory blocks; report a proven tactical result."""
        for _ in range(10):
            vacancies = g.full & ~(aa | bb)
            wa = winning_moves(aa, vacancies)
            wb = winning_moves(bb, vacancies)
            current = wa if turn == 0 else wb
            incoming = wb if turn == 0 else wa
            if current:
                return aa, bb, turn, (_WIN if turn == 0 else -_WIN)
            if len(incoming) >= 2:
                return aa, bb, turn, (-_WIN if turn == 0 else _WIN)
            if not incoming:
                return aa, bb, turn, None
            bit = 1 << incoming[0]
            if turn == 0:
                aa |= bit
            else:
                bb |= bit
            turn ^= 1
        return aa, bb, turn, None

    if time.perf_counter() > deadline - 0.05:
        return g.cells[safe[0]]

    _, own_surface = strategic(a, b)
    _, enemy_surface = strategic(b, a)
    quick = quick_scores(a, b, own_surface, enemy_surface)
    for v in safe:
        if my_threats.get(v):
            quick[v] += 20.0
        if their_threats.get(v):
            quick[v] += 7.0

    safe.sort(key=lambda v: quick[v], reverse=True)
    fallback = safe[0]
    records = []
    root_stop = min(started + 0.57, deadline - 0.10)

    for v in safe[:24]:
        if records and time.perf_counter() > root_stop:
            break
        aa, bb, turn, outcome = resolve(a | (1 << v), b, 1)
        if outcome == _WIN:
            return g.cells[v]
        if outcome == -_WIN:
            value = -_WIN
        elif time.perf_counter() < deadline - 0.025:
            value = evaluate(aa, bb)
        else:
            break
        records.append((value, v, aa, bb, turn, outcome))

    if not records:
        return g.cells[fallback]

    records.sort(reverse=True, key=lambda item: item[0])
    best_move = records[0][1]
    shortlist = records[:5]

    # Iterative, small-beam opponent reply search. Only completed rounds
    # replace the previous selection, avoiding time-cutoff bias.
    reply_lists = {}
    scores = {}
    fixed = set()
    for value, v, aa, bb, turn, outcome in shortlist:
        scores[v] = value
        if outcome is not None or turn == 0:
            fixed.add(v)
            reply_lists[v] = []
            continue

        reply_quick = quick_scores(bb, aa, enemy_surface, own_surface)
        replies = list(_bits(g.full & ~(aa | bb)))
        for w in replies:
            threats = their_threats.get(w, ())
            if any(z != v for z in threats):
                reply_quick[w] += 20.0
        replies.sort(key=lambda w: reply_quick[w], reverse=True)
        reply_lists[v] = replies[:3]

    running = {v: (_WIN if v not in fixed else scores[v])
               for _, v, *_ in shortlist}

    for depth in range(3):
        completed = True
        for value, v, aa, bb, turn, outcome in shortlist:
            if v in fixed or depth >= len(reply_lists[v]):
                continue
            if time.perf_counter() > deadline - 0.025:
                completed = False
                break

            reply = reply_lists[v][depth]
            ra, rb, rt, result = resolve(aa, bb | (1 << reply), 0)
            if result is None:
                if time.perf_counter() > deadline - 0.020:
                    completed = False
                    break
                result = evaluate(ra, rb)
            running[v] = min(running[v], result)

        if not completed:
            break

        scores = dict(running)
        best_move = max(
            scores,
            key=lambda v: (scores[v], quick[v], g.central[v]),
        )

    if best_move not in legal_set:
        best_move = fallback
    return g.cells[best_move]


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    started = time.perf_counter()
    occupied = set(map(tuple, me)) | set(map(tuple, opp))
    legal = [
        (r, c)
        for r in range(len(valid_mask))
        for c in range(len(valid_mask[r]))
        if bool(valid_mask[r][c]) and (r, c) not in occupied
    ]

    # A nonterminal Havannah position necessarily has a legal placement.
    if not legal:
        return (0, 0)

    center_r = (len(valid_mask) - 1) / 2.0
    center_c = (len(valid_mask[0]) - 1) / 2.0
    fallback = min(
        legal,
        key=lambda p: (p[0] - center_r) ** 2 + (p[1] - center_c) ** 2,
    )

    try:
        move = _play(
            list(map(tuple, me)), list(map(tuple, opp)),
            valid_mask, legal, started
        )
        if move in set(legal):
            return (int(move[0]), int(move[1]))
    except Exception:
        # Keep the action legal even if an unusual board representation
        # prevents the strategic search from completing.
        pass

    return (int(fallback[0]), int(fallback[1]))
