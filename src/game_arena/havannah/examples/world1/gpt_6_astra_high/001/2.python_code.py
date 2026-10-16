
import math
import time
from collections import deque


_INF = 1000
_POWER = [math.exp(-0.62 * k) for k in range(40)] + [0.0]
_PAIRS = [(i, j) for i in range(6) for j in range(i + 1, 6)]
_TRIPLES = [
    (i, j, k)
    for i in range(6)
    for j in range(i + 1, 6)
    for k in range(j + 1, 6)
]
_BOARD_CACHE = {}


def _bits(x):
    while x:
        b = x & -x
        yield b.bit_length() - 1
        x ^= b


def _p(x):
    return _POWER[min(40, max(0, x))]


class _Board:
    pass


def _make_board(coords):
    g = _Board()
    g.coords = coords
    g.n = len(coords)
    g.index = {p: i for i, p in enumerate(coords)}
    g.all = (1 << g.n) - 1

    # Try the usual axial and offset-coordinate representations.
    axial = [(1, 0), (1, -1), (0, -1),
             (-1, 0), (-1, 1), (0, 1)]
    best = None
    for kind in range(6):
        def transform(r, c):
            if kind == 0:
                return r, c
            if kind == 1:
                return r, -c
            if kind == 2:
                return c, r - c // 2
            if kind == 3:
                return c, r - (c + 1) // 2
            if kind == 4:
                return r, c - r // 2
            return r, c - (r + 1) // 2

        transformed = [transform(r, c) for r, c in coords]
        lookup = {p: i for i, p in enumerate(transformed)}
        ordered = [
            [lookup.get((a + da, b + db), -1) for da, db in axial]
            for a, b in transformed
        ]
        degrees = [sum(j >= 0 for j in ns) for ns in ordered]
        score = (
            5 * degrees.count(6)
            - 9 * degrees.count(5)
            - 16 * sum(d < 3 for d in degrees)
            - 3 * abs(degrees.count(3) - 6)
        )
        if best is None or score > best[0]:
            best = score, ordered

    g.ordered = best[1]
    g.neighbors = [[j for j in ns if j >= 0] for ns in g.ordered]
    g.nbmask = [sum(1 << j for j in ns) for ns in g.neighbors]
    boundary = [i for i in range(g.n) if len(g.neighbors[i]) < 6]
    boundary_set = set(boundary)
    g.boundary = sum(1 << i for i in boundary)

    # Walk around the perimeter to label corners and open edges.
    perimeter = []
    if boundary:
        start = min(boundary)
        previous, current = -1, start
        seen = set()
        while current not in seen:
            seen.add(current)
            perimeter.append(current)
            choices = [
                j for j in g.neighbors[current]
                if j in boundary_set and j != previous
            ]
            unvisited = [j for j in choices if j not in seen]
            if not unvisited:
                break
            previous, current = current, min(unvisited)

    if len(perimeter) != len(boundary):
        cr = sum(coords[i][0] for i in boundary) / max(1, len(boundary))
        cc = sum(coords[i][1] for i in boundary) / max(1, len(boundary))
        perimeter = sorted(
            boundary,
            key=lambda i: math.atan2(coords[i][0] - cr, coords[i][1] - cc)
        )

    corners = [i for i in perimeter if len(g.neighbors[i]) == 3]
    if len(corners) != 6 and perimeter:
        corners = [
            perimeter[(k * len(perimeter)) // 6]
            for k in range(6)
        ]

    g.corners = corners
    g.corner_mask = [0] * g.n
    g.edge_mask = [0] * g.n
    g.edges = [[] for _ in range(6)]
    for k, i in enumerate(corners):
        g.corner_mask[i] |= 1 << k

    if len(corners) == 6 and perimeter:
        positions = {i: k for k, i in enumerate(perimeter)}
        for k in range(6):
            a = positions[corners[k]]
            b = positions[corners[(k + 1) % 6]]
            a = (a + 1) % len(perimeter)
            while a != b:
                i = perimeter[a]
                if not g.corner_mask[i]:
                    g.edge_mask[i] |= 1 << k
                    g.edges[k].append(i)
                a = (a + 1) % len(perimeter)

    g.depth = [-1] * g.n
    queue = deque(boundary)
    for i in boundary:
        g.depth[i] = 0
    while queue:
        i = queue.popleft()
        for j in g.neighbors[i]:
            if g.depth[j] < 0:
                g.depth[j] = g.depth[i] + 1
                queue.append(j)

    # Several useful families of genuine enclosing rings.
    rings = {}
    interior = [i for i in range(g.n) if len(g.neighbors[i]) == 6]
    for i in interior:
        rings[g.nbmask[i]] = 0.8

    for i in interior:
        for j in g.neighbors[i]:
            if j > i and len(g.neighbors[j]) == 6:
                mask = (g.nbmask[i] | g.nbmask[j]) & ~((1 << i) | (1 << j))
                if mask.bit_count() == 8:
                    rings[mask] = max(rings.get(mask, 0.0), 0.30)

    for i in interior:
        if g.depth[i] < 2:
            continue
        near = g.nbmask[i] | (1 << i)
        outer = 0
        for j in g.neighbors[i]:
            outer |= g.nbmask[j]
        outer &= ~near
        if outer.bit_count() == 12:
            rings[outer] = max(rings.get(outer, 0.0), 0.12)

    g.rings = [(mask, mask.bit_count(), weight)
               for mask, weight in rings.items()]
    g.ring_membership = [[] for _ in range(g.n)]
    for entry in g.rings:
        for i in _bits(entry[0]):
            g.ring_membership[i].append(entry)

    # A two-carrier virtual connection survives one enemy intrusion.
    g.virtual = []
    g.virtual_endpoints = [[] for _ in range(g.n)]
    for i in range(g.n):
        distance_two = 0
        for j in g.neighbors[i]:
            distance_two |= g.nbmask[j]
        distance_two &= ~g.nbmask[i] & ~(1 << i)
        for j in _bits(distance_two):
            if j <= i:
                continue
            common = g.nbmask[i] & g.nbmask[j]
            if common.bit_count() == 2:
                endpoints = (1 << i) | (1 << j)
                g.virtual.append((endpoints, common))
                g.virtual_endpoints[i].append((j, common))
                g.virtual_endpoints[j].append((i, common))
    return g


class _Search:
    def __init__(self, board, deadline):
        self.g = board
        self.deadline = deadline
        self.win_cache = {}
        self.component_cache = {}
        self.eval_cache = {}

    def components(self, stones):
        cached = self.component_cache.get(stones)
        if cached is not None:
            return cached
        g = self.g
        labels = [-1] * g.n
        edges, corners = [], []
        remaining = stones
        while remaining:
            b = remaining & -remaining
            start = b.bit_length() - 1
            remaining ^= b
            component = len(edges)
            stack = [start]
            labels[start] = component
            em = cm = 0
            while stack:
                i = stack.pop()
                em |= g.edge_mask[i]
                cm |= g.corner_mask[i]
                new = g.nbmask[i] & remaining
                remaining ^= new
                for j in _bits(new):
                    labels[j] = component
                    stack.append(j)
            edges.append(em)
            corners.append(cm)
        result = labels, edges, corners
        self.component_cache[stones] = result
        return result

    def winning_cells(self, stones):
        """Winning placements before filtering out enemy-occupied cells."""
        cached = self.win_cache.get(stones)
        if cached is not None:
            return cached
        g = self.g
        result = 0
        nonown = g.all ^ stones

        for mask, size, weight in g.rings:
            missing = mask & nonown
            if missing and not (missing & (missing - 1)):
                result |= missing

        labels, edge_masks, corner_masks = self.components(stones)
        enough_for_ring = stones.bit_count() >= 5

        for i in _bits(nonown & ~result):
            em = g.edge_mask[i]
            cm = g.corner_mask[i]
            roots = set()
            for j in g.neighbors[i]:
                root = labels[j]
                if root >= 0 and root not in roots:
                    roots.add(root)
                    em |= edge_masks[root]
                    cm |= corner_masks[root]
            if cm.bit_count() >= 2 or em.bit_count() >= 3:
                result |= 1 << i
                continue

            if not enough_for_ring:
                continue

            # A newly enclosed unoccupied region needs two separated
            # contacts with the same existing component.
            cyclic = [labels[j] if j >= 0 else -1 for j in g.ordered[i]]
            runs = []
            for k, root in enumerate(cyclic):
                if root >= 0 and cyclic[k - 1] < 0:
                    runs.append(root)
            if len(runs) < 2 or len(set(runs)) == len(runs):
                continue

            available = nonown & ~(1 << i)
            known_exterior = 0
            enclosed = False
            for start in g.neighbors[i]:
                sb = 1 << start
                if not (available & sb) or known_exterior & sb:
                    continue
                seen = sb
                stack = [start]
                escapes = False
                while stack:
                    v = stack.pop()
                    if (g.boundary >> v) & 1:
                        escapes = True
                        break
                    new = g.nbmask[v] & available & ~seen
                    seen |= new
                    stack.extend(_bits(new))
                if not escapes:
                    enclosed = True
                    break
                known_exterior |= seen
            if enclosed:
                result |= 1 << i

        self.win_cache[stones] = result
        return result

    def side_value(self, own, enemy):
        key = own, enemy
        cached = self.eval_cache.get(key)
        if cached is not None:
            return cached

        g = self.g
        weights = [
            0 if (own >> i) & 1 else
            _INF if (enemy >> i) & 1 else 1
            for i in range(g.n)
        ]
        sources = [[i] for i in g.corners] + g.edges
        while len(sources) < 12:
            sources.append([])

        distances = []
        for seeds in sources:
            dist = [_INF] * g.n
            queue = deque()
            for i in seeds:
                if weights[i] < _INF:
                    dist[i] = weights[i]
                    queue.append(i)
            while queue:
                i = queue.popleft()
                di = dist[i]
                for j in g.neighbors[i]:
                    w = weights[j]
                    nd = di + w
                    if nd < dist[j]:
                        dist[j] = nd
                        if w:
                            queue.append(j)
                        else:
                            queue.appendleft(j)
            distances.append(dist)

        goals = []
        value = 0.0
        for a, b in _PAIRS:
            if b < len(g.corners):
                cost = distances[a][g.corners[b]]
            else:
                cost = _INF
            cost = min(40, cost)
            goals.append(cost)
            value += _p(cost)

        usable = [i for i in range(g.n) if weights[i] < _INF]
        edge_distances = distances[6:12]
        for a, b, c in _TRIPLES:
            da, db, dc = edge_distances[a], edge_distances[b], edge_distances[c]
            cost = 40
            for i in usable:
                candidate = da[i] + db[i] + dc[i] - 2 * weights[i]
                if candidate < cost:
                    cost = candidate
            goals.append(cost)
            value += 0.8 * _p(cost)

        for mask, size, weight in g.rings:
            if not mask & enemy:
                occupied = (mask & own).bit_count()
                if occupied:
                    value += weight * (_p(size - occupied) - _p(size))

        empty = g.all & ~(own | enemy)
        for endpoints, carriers in g.virtual:
            if own & endpoints == endpoints:
                free = (carriers & empty).bit_count()
                if free == 2:
                    value += 0.028
                elif free == 1 and not carriers & own:
                    value += 0.003

        value += 0.0003 * sum(g.depth[i] for i in _bits(own))
        result = value, distances, goals
        self.eval_cache[key] = result
        return result

    def evaluate(self, own, enemy):
        return self.side_value(own, enemy)[0] - self.side_value(enemy, own)[0]

    def rank(self, own, enemy, own_data=None, enemy_data=None):
        g = self.g
        empty = g.all & ~(own | enemy)
        if own_data is None:
            own_data = self.side_value(own, enemy)
        if enemy_data is None:
            enemy_data = self.side_value(enemy, own)
        od, og = own_data[1], own_data[2]
        ed, eg = enemy_data[1], enemy_data[2]
        labels = self.components(own)[0]
        scored = []

        for i in _bits(empty):
            attack = defense = 0.0
            for k, (a, b) in enumerate(_PAIRS):
                cost = od[a][i] + od[b][i] - 2
                if cost < og[k]:
                    attack += _p(cost) - _p(og[k])
                cost = ed[a][i] + ed[b][i] - 2
                if cost < eg[k]:
                    defense += _p(cost) - _p(eg[k])

            for t, (a, b, c) in enumerate(_TRIPLES):
                k = t + 15
                cost = od[a + 6][i] + od[b + 6][i] + od[c + 6][i] - 3
                if cost < og[k]:
                    attack += 0.8 * (_p(cost) - _p(og[k]))
                cost = ed[a + 6][i] + ed[b + 6][i] + ed[c + 6][i] - 3
                if cost < eg[k]:
                    defense += 0.8 * (_p(cost) - _p(eg[k]))

            score = attack + 0.86 * defense
            for mask, size, weight in g.ring_membership[i]:
                if not mask & enemy:
                    count = (mask & own).bit_count()
                    score += weight * (_p(size - count - 1) - _p(size - count))
                if not mask & own:
                    count = (mask & enemy).bit_count()
                    if count:
                        factor = 0.10 if count == 1 else 0.35 if count == 2 else 0.85
                        score += factor * weight * (_p(size - count) - _p(size))

            for j, carriers in g.virtual_endpoints[i]:
                if (own >> j) & 1 and (carriers & empty).bit_count() == 2:
                    score += 0.028

            adjacent = [labels[j] for j in g.neighbors[i] if labels[j] >= 0]
            if adjacent:
                score += 0.004 + 0.010 * (len(set(adjacent)) - 1)
                if len(adjacent) >= 3 and len(set(adjacent)) == 1:
                    score -= 0.010

            score += 0.00012 * g.depth[i]
            score += 0.0000001 * ((i * 37 + own.bit_count() * 17) % 101)
            scored.append((score, i))
        scored.sort(reverse=True)
        return scored


def _choose(g, own, enemy, deadline):
    search = _Search(g, deadline)
    empty = g.all & ~(own | enemy)

    immediate = search.winning_cells(own) & empty
    if immediate:
        return next(_bits(immediate))

    blocks = search.winning_cells(enemy) & empty
    if blocks:
        # With multiple distinct immediate threats, no ordinary defense
        # can stop them all; occupying one is still always legal.
        return max(_bits(blocks), key=lambda i: g.depth[i])

    if not own and not enemy:
        return max(_bits(empty), key=lambda i: g.depth[i])

    own_data = search.side_value(own, enemy)
    enemy_data = search.side_value(enemy, own)
    ranked = search.rank(own, enemy, own_data, enemy_data)
    enemy_ranked = search.rank(enemy, own, enemy_data, own_data)
    fallback = ranked[0][1]

    candidates = [i for _, i in ranked[:14]]
    candidates.extend(i for _, i in enemy_ranked[:4])

    # Locate likely enemy two-threat attacks; include their defenses.
    dangers = []
    for _, i in enemy_ranked[:9]:
        if time.perf_counter() > deadline - 0.35:
            break
        threats = search.winning_cells(enemy | (1 << i)) & (empty ^ (1 << i))
        if threats.bit_count() >= 2:
            dangers.append(i)
            candidates.append(i)
            candidates.extend(_bits(threats))

    candidates = list(dict.fromkeys(candidates))
    root_scores = dict((i, score) for score, i in ranked)
    prepared = []
    for i in candidates:
        if time.perf_counter() > deadline - 0.20:
            break
        bit = 1 << i
        threats = search.winning_cells(own | bit) & (empty ^ bit)
        if threats.bit_count() >= 2:
            return i
        prepared.append((root_scores.get(i, 0.0) + (0.08 if threats else 0.0),
                         i, threats))
    prepared.sort(reverse=True)

    best_move = fallback
    best_value = -float("inf")

    for order_score, move, threats in prepared:
        if time.perf_counter() > deadline - 0.055:
            break
        mb = 1 << move
        mine = own | mb
        available = empty ^ mb

        if threats:
            replies = [next(_bits(threats))]
            my_data = search.side_value(mine, enemy)
            their_data = search.side_value(enemy, mine)
        else:
            # A known double threat makes this candidate immediately bad.
            losing = False
            for d in dangers:
                db = 1 << d
                if available & db:
                    wins = search.winning_cells(enemy | db) & (available ^ db)
                    if wins.bit_count() >= 2:
                        losing = True
                        break
            if losing:
                continue

            my_data = search.side_value(mine, enemy)
            their_data = search.side_value(enemy, mine)
            response_order = search.rank(enemy, mine, their_data, my_data)
            replies = [i for _, i in response_order[:5]]
            replies.extend(d for d in dangers if (available >> d) & 1)
            replies = list(dict.fromkeys(replies))

        worst = float("inf")
        completed = True

        for reply in replies:
            if time.perf_counter() > deadline - 0.015:
                completed = False
                break

            rb = 1 << reply
            theirs = enemy | rb
            remaining = available ^ rb
            counter_threats = search.winning_cells(theirs) & remaining

            if counter_threats.bit_count() >= 2:
                value = -100.0
            elif counter_threats:
                forced = counter_threats & -counter_threats
                defended = mine | forced
                later = remaining ^ forced
                our_threats = search.winning_cells(defended) & later
                if our_threats.bit_count() >= 2:
                    value = 100.0
                else:
                    value = search.evaluate(defended, theirs) - 0.035
                    if our_threats:
                        value += 0.025
            else:
                value = search.evaluate(mine, theirs) + 0.035

                # Extend forcing lines to recognize a second-stage
                # double threat rather than stopping at the first block.
                if threats and time.perf_counter() < deadline - 0.09:
                    next_order = search.rank(mine, theirs, my_data, their_data)
                    for _, nxt in next_order[:5]:
                        nb = 1 << nxt
                        future = search.winning_cells(mine | nb) & (remaining ^ nb)
                        if future.bit_count() >= 2:
                            value = 100.0
                            break

            if value < worst:
                worst = value
            if worst + 0.002 * order_score <= best_value:
                break

        if completed and worst != float("inf"):
            score = worst + 0.002 * order_score
            if score > best_value:
                best_value = score
                best_move = move
            if best_value > 50.0:
                return best_move

    return best_move


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    start = time.perf_counter()
    occupied = {tuple(p) for p in me} | {tuple(p) for p in opp}
    rows = len(valid_mask)
    coords = tuple(
        (r, c)
        for r in range(rows)
        for c in range(len(valid_mask[r]))
        if bool(valid_mask[r][c])
    )
    legal = [p for p in coords if p not in occupied]

    # The game API guarantees a move exists on every nonterminal call.
    if not legal:
        raise ValueError("policy called without any legal placement")

    midpoint = (rows - 1) / 2.0
    fallback = min(
        legal,
        key=lambda p: (p[0] - midpoint) ** 2 + (p[1] - midpoint) ** 2
    )

    try:
        g = _BOARD_CACHE.get(coords)
        if g is None:
            g = _make_board(coords)
            _BOARD_CACHE.clear()
            _BOARD_CACHE[coords] = g

        own = 0
        enemy = 0
        for p in me:
            i = g.index.get(tuple(p))
            if i is not None:
                own |= 1 << i
        for p in opp:
            i = g.index.get(tuple(p))
            if i is not None:
                enemy |= 1 << i

        chosen = _choose(g, own, enemy, start + 0.88)
        result = g.coords[chosen]
        if result not in occupied and bool(valid_mask[result[0]][result[1]]):
            return int(result[0]), int(result[1])
    except Exception:
        # Never let a search failure turn an otherwise legal turn
        # into an invalid action.
        pass

    return int(fallback[0]), int(fallback[1])
