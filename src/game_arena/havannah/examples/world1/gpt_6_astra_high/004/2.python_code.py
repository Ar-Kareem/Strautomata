
import math
import random
import time
from collections import deque


_GEOMETRY_CACHE = {}


class _Geometry:
    def __init__(self, n, cells):
        self.n = n
        self.size = n * n
        self.cells = tuple(cells)
        self.full = sum(1 << v for v in cells)
        cellset = set(cells)

        # Infer the axial-coordinate orientation from the board's shape.
        orientations = (
            ((-1, -1), (-1, 0), (0, 1),
             (1, 1), (1, 0), (0, -1)),
            ((-1, 0), (-1, 1), (0, 1),
             (1, 0), (1, -1), (0, -1)),
        )

        def geometry_score(dirs):
            total = 0
            for v in cells:
                r, c = divmod(v, n)
                for dr, dc in dirs:
                    rr, cc = r + dr, c + dc
                    if 0 <= rr < n and 0 <= cc < n:
                        total += (rr * n + cc in cellset)
            return total

        self.dirs = max(orientations, key=geometry_score)
        self.neighbors = [[] for _ in range(self.size)]
        self.around = [()] * self.size
        self.nmask = [0] * self.size

        for v in cells:
            r, c = divmod(v, n)
            around = []
            for dr, dc in self.dirs:
                rr, cc = r + dr, c + dc
                u = rr * n + cc
                if (0 <= rr < n and 0 <= cc < n and u in cellset):
                    around.append(u)
                    self.neighbors[v].append(u)
                    self.nmask[v] |= 1 << u
                else:
                    around.append(-1)
            self.around[v] = tuple(around)

        self.centers = tuple(
            v for v in cells if len(self.neighbors[v]) == 6
        )
        self.is_center = [False] * self.size
        for v in self.centers:
            self.is_center[v] = True

        boundary = {
            v for v in cells if len(self.neighbors[v]) < 6
        }
        corners = [
            v for v in boundary if len(self.neighbors[v]) == 3
        ]

        # The supplied board is normally a regular hexagon. This fallback
        # also keeps the policy usable on unusual masks.
        if len(corners) != 6:
            corners = sorted(
                boundary,
                key=lambda v: (len(self.neighbors[v]), v)
            )[:6]

        self.corner = [0] * self.size
        self.edge = [0] * self.size
        self.corner_groups = []
        for i, v in enumerate(sorted(corners)):
            self.corner[v] = 1 << i
            self.corner_groups.append((v,))

        remaining = boundary - set(corners)
        self.edge_groups = []
        while remaining:
            start = min(remaining)
            remaining.remove(start)
            group = [start]
            stack = [start]
            while stack:
                v = stack.pop()
                for u in self.neighbors[v]:
                    if u in remaining:
                        remaining.remove(u)
                        group.append(u)
                        stack.append(u)
            self.edge_groups.append(tuple(group))

        for i, group in enumerate(self.edge_groups):
            for v in group:
                self.edge[v] = 1 << i

        self.virtual = [[] for _ in range(self.size)]
        for v in cells:
            candidates = set()
            for u in self.neighbors[v]:
                candidates.update(self.neighbors[u])
            candidates.discard(v)
            candidates.difference_update(self.neighbors[v])
            for u in candidates:
                common = self.nmask[v] & self.nmask[u]
                if common.bit_count() == 2:
                    self.virtual[v].append((u, common))


class _Board:
    __slots__ = (
        "g", "occ", "parent", "sz", "edges", "corners", "bits"
    )

    def __init__(self, g):
        self.g = g
        self.occ = [-1] * g.size
        self.parent = list(range(g.size))
        self.sz = [1] * g.size
        self.edges = g.edge[:]
        self.corners = g.corner[:]
        self.bits = [0, 0]

    def copy(self):
        b = object.__new__(_Board)
        b.g = self.g
        b.occ = self.occ[:]
        b.parent = self.parent[:]
        b.sz = self.sz[:]
        b.edges = self.edges[:]
        b.corners = self.corners[:]
        b.bits = self.bits[:]
        return b

    def find(self, v):
        parent = self.parent
        while parent[v] != v:
            parent[v] = parent[parent[v]]
            v = parent[v]
        return v

    def place(self, v, p):
        g = self.g
        roots = []
        for u in g.around[v]:
            roots.append(
                self.find(u) if u >= 0 and self.occ[u] == p else -1
            )

        # Separate occupied neighbor arcs already belonging to the same
        # component close a nontrivial hex-grid cycle.
        ring = False
        seen = set()
        previous = roots[-1]
        for root in roots:
            if root >= 0 and previous < 0:
                if root in seen:
                    ring = True
                seen.add(root)
            previous = root

        self.occ[v] = p
        self.bits[p] |= 1 << v
        self.parent[v] = v
        self.sz[v] = 1
        self.edges[v] = g.edge[v]
        self.corners[v] = g.corner[v]

        root = v
        for other in set(roots):
            if other < 0:
                continue
            root = self.find(root)
            other = self.find(other)
            if root == other:
                continue
            if self.sz[root] < self.sz[other]:
                root, other = other, root
            self.parent[other] = root
            self.sz[root] += self.sz[other]
            self.edges[root] |= self.edges[other]
            self.corners[root] |= self.corners[other]

        if (self.corners[root].bit_count() >= 2 or
                self.edges[root].bit_count() >= 3):
            return True

        if ring:
            return True

        # This also recognizes a ring whose enclosed cell is friendly:
        # ordinary neighbor-arc tests alone can miss a filled six-ring.
        own = self.bits[p]
        for center in g.neighbors[v]:
            if (g.is_center[center] and
                    (g.nmask[center] & own) == g.nmask[center]):
                return True
        return False


def _winning_moves(b, p):
    g = b.g
    own = b.bits[p]
    free = g.full & ~(own | b.bits[1 - p])
    if not own or not free:
        return []

    wins = 0
    for center in g.centers:
        missing = g.nmask[center] & ~own
        if missing and not (missing & (missing - 1)) and missing & free:
            wins |= missing

    labels = [-1] * g.size
    stones = own
    while stones:
        bit = stones & -stones
        v = bit.bit_length() - 1
        labels[v] = b.find(v)
        stones ^= bit

    todo = free & ~wins
    while todo:
        bit = todo & -todo
        todo ^= bit
        v = bit.bit_length() - 1
        adjacent = g.nmask[v] & own
        if not adjacent:
            continue
        if (adjacent.bit_count() < 2 and
                not g.edge[v] and not g.corner[v]):
            continue

        em = g.edge[v]
        cm = g.corner[v]
        roots = []
        for u in g.around[v]:
            root = labels[u] if u >= 0 else -1
            roots.append(root)
            if root >= 0:
                em |= b.edges[root]
                cm |= b.corners[root]

        if cm.bit_count() >= 2 or em.bit_count() >= 3:
            wins |= bit
            continue

        previous = roots[-1]
        seen = set()
        for root in roots:
            if root >= 0 and previous < 0:
                if root in seen:
                    wins |= bit
                    break
                seen.add(root)
            previous = root

    result = []
    while wins:
        bit = wins & -wins
        result.append(bit.bit_length() - 1)
        wins ^= bit
    return result


def _goal_distances(b, p, groups):
    g = b.g
    costs = [
        0 if x == p else (1000 if x == 1 - p else 1)
        for x in b.occ
    ]
    answers = []
    for group in groups:
        dist = [1000] * g.size
        queue = deque()
        for v in group:
            if costs[v] >= 1000:
                continue
            dist[v] = costs[v]
            if costs[v] == 0:
                queue.appendleft(v)
            else:
                queue.append(v)

        while queue:
            v = queue.popleft()
            dv = dist[v]
            for u in g.neighbors[v]:
                cost = costs[u]
                nd = dv + cost
                if nd < dist[u]:
                    dist[u] = nd
                    if cost:
                        queue.append(u)
                    else:
                        queue.appendleft(u)
        answers.append(dist)
    return answers


def _offensive_scores(b, p, legal):
    g = b.g
    own, enemy = b.bits[p], b.bits[1 - p]
    cd = _goal_distances(b, p, g.corner_groups)
    ed = _goal_distances(b, p, g.edge_groups)

    bridge = [1000] * g.size
    fork = [1000] * g.size
    frontier = []

    for v in legal:
        if g.nmask[v] & own:
            frontier.append(v)
        ds = sorted(d[v] for d in cd)
        if len(ds) >= 2:
            bridge[v] = ds[0] + ds[1] - 1
        ds = sorted(d[v] for d in ed)
        if len(ds) >= 3:
            fork[v] = ds[0] + ds[1] + ds[2] - 2

    relevant = frontier or legal
    mb = min(bridge[v] for v in relevant)
    mf = min(fork[v] for v in relevant)

    values = [0.0] * g.size
    ring_weights = (0.0, 0.035, 0.19, 0.72, 2.9, 15.0, 1000.0)
    adjacency_values = (0.0, 1.25, 2.0, 1.55, 0.45, 0.15, -3.0)
    center = (g.n - 1) * 0.5

    for v in legal:
        adjacent = (g.nmask[v] & own).bit_count()
        score = adjacency_values[adjacent]

        score += 1.30 * math.exp(
            -0.55 * max(0, bridge[v] - mb)
        )
        score += 1.85 * math.exp(
            -0.43 * max(0, fork[v] - mf)
        )

        roots = {
            b.find(u) for u in g.neighbors[v] if b.occ[u] == p
        }
        if len(roots) > 1:
            score += 0.85 * (len(roots) - 1)

        for u, common in g.virtual[v]:
            if b.occ[u] == p and not common & enemy:
                score += 0.42 if not common & own else 0.10

        for c in g.neighbors[v]:
            if not g.is_center[c]:
                continue
            mask = g.nmask[c]
            if not mask & enemy:
                count = (mask & own).bit_count()
                score += ring_weights[count + 1] - ring_weights[count]

        r, c = divmod(v, g.n)
        score -= 0.022 * ((r - center) ** 2 + (c - center) ** 2)
        values[v] = score
    return values


def _forcing_search(b, attacker, depth, scores, deadline):
    """Prove wins in which every intervening reply is forced."""
    if time.perf_counter() >= deadline:
        return None

    wins = _winning_moves(b, attacker)
    if wins:
        return wins[0]
    if depth <= 0:
        return None

    enemy_wins = _winning_moves(b, 1 - attacker)
    if len(enemy_wins) >= 2:
        return None

    if enemy_wins:
        candidates = enemy_wins
    else:
        free = b.g.full & ~(b.bits[0] | b.bits[1])
        candidates = [
            v for v in b.g.cells
            if free & (1 << v) and
            ((b.g.nmask[v] & b.bits[attacker]).bit_count() >= 2 or
             b.g.edge[v] or b.g.corner[v])
        ]
        candidates.sort(key=lambda v: scores[v], reverse=True)
        candidates = candidates[:16]

    for v in candidates:
        if time.perf_counter() >= deadline:
            return None
        child = b.copy()
        if child.place(v, attacker):
            return v

        threats = _winning_moves(child, attacker)
        if not threats:
            continue

        if enemy_wins and _winning_moves(child, 1 - attacker):
            continue

        if len(threats) >= 2:
            return v
        if depth == 1:
            continue

        if child.place(threats[0], 1 - attacker):
            continue
        continuation = _forcing_search(
            child, attacker, depth - 1, scores, deadline
        )
        if continuation is not None:
            return v
    return None


class _Node:
    __slots__ = (
        "move", "player", "prior", "n", "w",
        "an", "aw", "children", "untried"
    )

    def __init__(self, move, player, prior=1.0):
        self.move = move
        self.player = player
        self.prior = prior
        self.n = 0
        self.w = 0.0
        self.an = 0
        self.aw = 0.0
        self.children = []
        self.untried = None


def _ring_threat_bits(b, p, centers):
    g = b.g
    own = b.bits[p]
    free = g.full & ~(b.bits[0] | b.bits[1])
    threats = 0
    for c in centers:
        if g.is_center[c]:
            missing = g.nmask[c] & ~own
            if (missing and not missing & (missing - 1)
                    and missing & free):
                threats |= missing
    return threats


def _rollout(b, turn, rng, played, ply, deadline):
    g = b.g
    free = g.full & ~(b.bits[0] | b.bits[1])
    bag = [v for v in g.cells if free & (1 << v)]
    positions = [-1] * g.size
    for i, v in enumerate(bag):
        positions[v] = i

    pending = [
        _ring_threat_bits(b, 0, g.centers),
        _ring_threat_bits(b, 1, g.centers),
    ]
    attachment = (0.0, 0.90, 1.75, 1.10, 0.35, 0.1, -1.0)

    while bag:
        if ply % 24 == 0 and time.perf_counter() >= deadline:
            return -1

        urgent = pending[turn] & free
        if not urgent:
            urgent = pending[1 - turn] & free

        if urgent:
            bit = urgent & -urgent
            v = bit.bit_length() - 1
            index = positions[v]
        else:
            count = len(bag)
            index = rng.randrange(count)
            v = bag[index]
            score = (
                attachment[(g.nmask[v] & b.bits[turn]).bit_count()]
                + 1.8 * rng.random()
            )
            for _ in range(2):
                j = rng.randrange(count)
                u = bag[j]
                s = (
                    attachment[(g.nmask[u] & b.bits[turn]).bit_count()]
                    + 0.08 * (g.nmask[u] & b.bits[1 - turn]).bit_count()
                    + 1.8 * rng.random()
                )
                if s > score:
                    index, v, score = j, u, s

        last = bag.pop()
        if index < len(bag):
            bag[index] = last
            positions[last] = index
        positions[v] = -1
        free &= ~(1 << v)

        if ply < 44:
            played[turn] |= 1 << v
        if b.place(v, turn):
            return turn

        pending[turn] |= _ring_threat_bits(
            b, turn, g.neighbors[v]
        )
        pending[0] &= free
        pending[1] &= free
        turn = 1 - turn
        ply += 1

    return -1


def _monte_carlo(board, candidates, base, rng, deadline):
    g = board.g
    root = _Node(-1, 1)
    best_base = max(base[0][v] for v in candidates)
    ordered = sorted(
        candidates, key=lambda v: base[0][v], reverse=True
    )
    root.untried = [
        (v, math.exp(max(-12.0, (base[0][v] - best_base) / 3.0)))
        for v in reversed(ordered)
    ]

    initial_adj = [
        [(g.nmask[v] & board.bits[p]).bit_count()
         for v in range(g.size)]
        for p in (0, 1)
    ]

    while time.perf_counter() < deadline:
        b = board.copy()
        node = root
        path = [root]
        turn = 0
        played = [0, 0]
        winner = -1
        ply = 0

        while True:
            if node.untried is None:
                free = g.full & ~(b.bits[0] | b.bits[1])
                ranked = []
                for v in g.cells:
                    if not free & (1 << v):
                        continue
                    ours = (g.nmask[v] & b.bits[turn]).bit_count()
                    theirs = (g.nmask[v] & b.bits[1 - turn]).bit_count()
                    value = (
                        base[turn][v]
                        + 0.65 * (ours - initial_adj[turn][v])
                        + 0.25 * (theirs - initial_adj[1 - turn][v])
                        + rng.random() * 0.12
                    )
                    ranked.append((value, v))
                ranked.sort(reverse=True)
                ranked = ranked[:20]
                if ranked:
                    top = ranked[0][0]
                    node.untried = [
                        (v, math.exp(max(-12.0, (s - top) / 3.0)))
                        for s, v in reversed(ranked)
                    ]
                else:
                    node.untried = []

            limit = 2 + int(1.55 * math.sqrt(node.n + 1))
            if node.untried and len(node.children) < limit:
                move, prior = node.untried.pop()
                child = _Node(move, turn, prior)
                node.children.append(child)
                played[turn] |= 1 << move
                won = b.place(move, turn)
                node = child
                path.append(node)
                ply += 1
                if won:
                    winner = turn
                turn = 1 - turn
                break

            if not node.children:
                break

            logn = math.log(node.n + 2.0)
            best = None
            best_value = -1e30
            for child in node.children:
                q = child.w / child.n if child.n else 0.5
                if child.an:
                    beta = child.an / (
                        child.an + child.n
                        + 0.025 * child.an * child.n
                    )
                    q = (
                        (1.0 - beta) * q
                        + beta * child.aw / child.an
                    )
                value = (
                    q
                    + 0.52 * math.sqrt(logn / (child.n + 1.0))
                    + 0.14 * child.prior / (1.0 + 0.10 * child.n)
                )
                if value > best_value:
                    best_value = value
                    best = child

            played[turn] |= 1 << best.move
            won = b.place(best.move, turn)
            node = best
            path.append(node)
            ply += 1
            if won:
                winner = turn
                break
            turn = 1 - turn

        if winner < 0:
            winner = _rollout(
                b, turn, rng, played, ply, deadline
            )

        if winner < 0 and time.perf_counter() >= deadline:
            break

        for visited in path:
            visited.n += 1
            visited.w += (
                0.5 if winner < 0 else float(visited.player == winner)
            )
            for child in visited.children:
                if played[child.player] & (1 << child.move):
                    child.an += 1
                    child.aw += (
                        0.5 if winner < 0
                        else float(child.player == winner)
                    )

    if not root.children:
        return ordered[0]

    # Visits are more stable than a raw maximum of noisy win estimates.
    best = max(
        root.children,
        key=lambda child: (
            child.n,
            child.w / max(1, child.n),
            base[0][child.move],
        ),
    )
    return best.move


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    start = time.perf_counter()
    deadline = start + 0.91
    n = len(valid_mask)
    occupied = set(map(tuple, me)) | set(map(tuple, opp))

    legal_coords = []
    cells = []
    for r in range(n):
        for c in range(n):
            valid = bool(valid_mask[r][c])
            if valid or (r, c) in occupied:
                cells.append(r * n + c)
            if valid and (r, c) not in occupied:
                legal_coords.append((r, c))

    # A legal action exists in every nonterminal arena position.
    if not legal_coords:
        # No legal return is mathematically possible in this case.
        return (0, 0)
    if len(legal_coords) == 1:
        return legal_coords[0]

    fallback = legal_coords[0]
    key = (n, tuple(cells))
    g = _GEOMETRY_CACHE.get(key)
    if g is None:
        g = _Geometry(n, cells)
        if len(_GEOMETRY_CACHE) >= 4:
            _GEOMETRY_CACHE.clear()
        _GEOMETRY_CACHE[key] = g

    b = _Board(g)
    for r, c in me:
        b.place(r * n + c, 0)
    for r, c in opp:
        b.place(r * n + c, 1)

    legal = [r * n + c for r, c in legal_coords]
    legal_set = set(legal)

    wins = _winning_moves(b, 0)
    if wins:
        return divmod(wins[0], n)

    enemy_wins = _winning_moves(b, 1)
    if enemy_wins:
        # If several exist the position is already tactically lost,
        # but blocking one still returns a legal move.
        return divmod(enemy_wins[0], n)

    if not me and not opp:
        center = (n - 1) / 2
        target = center - max(1, n // 7)
        move = min(
            legal,
            key=lambda v: (
                (v // n - target) ** 2 + (v % n - target) ** 2,
                v,
            ),
        )
        return divmod(move, n)

    offense = [
        _offensive_scores(b, 0, legal),
        _offensive_scores(b, 1, legal),
    ]
    base = [
        [offense[p][v] + 0.72 * offense[1 - p][v]
         for v in range(g.size)]
        for p in (0, 1)
    ]

    ranked = sorted(legal, key=lambda v: base[0][v], reverse=True)
    fallback_move = ranked[0]
    tactical_deadline = min(start + 0.28, deadline - 0.20)

    forcing = {}
    offensive_order = sorted(
        legal, key=lambda v: offense[0][v], reverse=True
    )

    for v in offensive_order[:44]:
        if time.perf_counter() >= tactical_deadline:
            break
        child = b.copy()
        if child.place(v, 0):
            return divmod(v, n)
        threats = _winning_moves(child, 0)
        if len(threats) >= 2:
            return divmod(v, n)
        if threats:
            forcing[v] = threats[0]
            base[0][v] += 1.6

    defenses = None
    defensive_order = sorted(
        legal, key=lambda v: offense[1][v], reverse=True
    )
    for v in defensive_order[:40]:
        if time.perf_counter() >= tactical_deadline:
            break
        child = b.copy()
        child.place(v, 1)
        threats = _winning_moves(child, 1)
        if len(threats) >= 2:
            answers = {v}
            if len(threats) == 2:
                answers.update(threats)
            defenses = answers if defenses is None else defenses & answers
            for answer in answers:
                base[0][answer] += 2.0

    # Search forcing continuations before spending the rest on sampling.
    for v in sorted(forcing, key=lambda x: base[0][x], reverse=True):
        if time.perf_counter() >= tactical_deadline:
            break
        child = b.copy()
        child.place(v, 0)
        if child.place(forcing[v], 1):
            continue
        if _forcing_search(
            child, 0, 2, offense[0], tactical_deadline
        ) is not None:
            return divmod(v, n)

    if defenses is not None:
        allowed = (defenses | set(forcing)) & legal_set
        if allowed:
            ranked = sorted(
                allowed, key=lambda v: base[0][v], reverse=True
            )
        else:
            ranked = sorted(
                legal, key=lambda v: base[0][v], reverse=True
            )
    else:
        ranked = sorted(
            legal, key=lambda v: base[0][v], reverse=True
        )

    candidates = ranked[:24]
    if not candidates:
        return divmod(fallback_move, n)
    if len(candidates) == 1:
        return divmod(candidates[0], n)

    seed = (
        b.bits[0] * 6364136223846793005
        ^ b.bits[1] * 1442695040888963407
        ^ (len(me) + len(opp)) * 104729
    )
    rng = random.Random(seed)

    if time.perf_counter() < deadline - 0.025:
        move = _monte_carlo(b, candidates, base, rng, deadline)
    else:
        move = candidates[0]

    result = divmod(move, n)
    if result in occupied or not bool(valid_mask[result[0]][result[1]]):
        return fallback
    return result
