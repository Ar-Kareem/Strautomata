
import math
import time
from collections import deque

_GEOMETRY_CACHE = {}
_RING_WEIGHTS = (0.0, 0.008, 0.10, 0.55, 2.6, 13.0, 10000.0)
_WIN = 100000.0


class _Timeout(Exception):
    pass


def _geometry(cells):
    key = tuple(cells)
    cached = _GEOMETRY_CACHE.get(key)
    if cached is not None:
        return cached

    index = {cell: i for i, cell in enumerate(cells)}
    plus = ((1, 0), (1, 1), (0, 1),
            (-1, 0), (-1, -1), (0, -1))
    minus = ((1, 0), (0, 1), (-1, 1),
             (-1, 0), (0, -1), (1, -1))

    def adjacency_count(directions):
        return sum(
            (r + dr, c + dc) in index
            for r, c in cells for dr, dc in directions
        )

    positive = adjacency_count(plus) >= adjacency_count(minus)
    directions = plus if positive else minus

    neighbors = [
        tuple(index.get((r + dr, c + dc), -1)
              for dr, dc in directions)
        for r, c in cells
    ]

    axes = [
        (r, c, r - c if positive else r + c)
        for r, c in cells
    ]
    lows = [min(a[k] for a in axes) for k in range(3)]
    highs = [max(a[k] for a in axes) for k in range(3)]
    boundary = []
    for a in axes:
        bits = 0
        for k in range(3):
            if a[k] == lows[k]:
                bits |= 1 << (2 * k)
            if a[k] == highs[k]:
                bits |= 1 << (2 * k + 1)
        boundary.append(bits)

    corners = [
        i for i, bits in enumerate(boundary)
        if bits.bit_count() >= 2
    ]
    corner_masks = [0] * len(cells)
    for k, v in enumerate(corners):
        corner_masks[v] = 1 << k

    edge_masks = [
        0 if corner_masks[i] else boundary[i]
        for i in range(len(cells))
    ]
    edge_sources = [
        [i for i, bits in enumerate(edge_masks) if bits & (1 << k)]
        for k in range(6)
    ]
    corner_sources = [[v] for v in corners]

    # A regular Havannah board has six corners. Padding also permits
    # graceful operation on unusual masks.
    while len(corner_sources) < 6:
        corner_sources.append([])
    corner_sources = corner_sources[:6]

    rings = []
    through = [[] for _ in cells]
    for ns in neighbors:
        if -1 not in ns:
            ri = len(rings)
            rings.append(ns)
            for v in ns:
                through[v].append(ri)

    near_two = []
    for v, ns in enumerate(neighbors):
        seen = set()
        for u in ns:
            if u >= 0:
                seen.update(x for x in neighbors[u] if x >= 0)
        seen.discard(v)
        seen.difference_update(ns)
        near_two.append(tuple(seen))

    result = (
        cells, index, neighbors, edge_masks, corner_masks,
        edge_sources + corner_sources, rings, through,
        near_two, positive
    )
    if len(_GEOMETRY_CACHE) > 6:
        _GEOMETRY_CACHE.clear()
    _GEOMETRY_CACHE[key] = result
    return result


def _distances(neighbors, sources, occupancy, player):
    n = len(neighbors)
    costs = [
        0 if x == player + 1 else 1 if x == 0 else 1000
        for x in occupancy
    ]
    all_distances = []
    for source in sources:
        distance = [1000] * n
        queue = deque()
        for v in source:
            if costs[v] < 1000:
                distance[v] = costs[v]
                if costs[v] == 0:
                    queue.appendleft(v)
                else:
                    queue.append(v)

        while queue:
            v = queue.popleft()
            dv = distance[v]
            for u in neighbors[v]:
                if u < 0 or costs[u] >= 1000:
                    continue
                nd = dv + costs[u]
                if nd < distance[u]:
                    distance[u] = nd
                    if costs[u] == 0:
                        queue.appendleft(u)
                    else:
                        queue.append(u)
        all_distances.append(distance)

    return [
        tuple(
            min(40, max(0, all_distances[k][v] -
                        (1 if occupancy[v] == 0 else 0)))
            for k in range(12)
        )
        for v in range(n)
    ]


def _reach_value(reach):
    edges = sorted(reach[:6])
    corners = sorted(reach[6:])
    bridge = corners[0] + corners[1]
    fork = edges[0] + edges[1] + edges[2]
    return (9.0 * math.exp(-0.28 * bridge) +
            11.0 * math.exp(-0.28 * fork))


class _Position:
    def __init__(self, geometry, initial, deadline):
        (self.cells, self.index, self.neighbors,
         self.edge_masks, self.corner_masks, sources,
         self.rings, self.through, self.near_two,
         self.positive) = geometry

        self.n = len(self.cells)
        self.deadline = deadline
        self.board = [0] * self.n
        self.parent = [[-1] * self.n for _ in range(2)]
        self.size = [[0] * self.n for _ in range(2)]
        self.edges = [[0] * self.n for _ in range(2)]
        self.corners = [[0] * self.n for _ in range(2)]
        self.reach = [[None] * self.n for _ in range(2)]
        self.base = [
            _distances(self.neighbors, sources, initial, p)
            for p in range(2)
        ]
        self.ring_counts = [[0] * len(self.rings) for _ in range(2)]
        self.ring_score = [0.0, 0.0]
        self.best_reach = [0.0, 0.0]
        self.links = [0, 0]
        self.nodes = 0
        self.preferred = None
        self.root_answer = None

        for v, owner in enumerate(initial):
            if owner:
                self.play(owner - 1, v)

    def find(self, p, v):
        parent = self.parent[p]
        while parent[v] != v:
            v = parent[v]
        return v

    def play(self, p, v):
        q = 1 - p
        parent = self.parent[p]
        sizes = self.size[p]
        edges = self.edges[p]
        corners = self.corners[p]
        reach = self.reach[p]

        old_best = self.best_reach[p]
        old_scores = (self.ring_score[0], self.ring_score[1])
        changes = []

        self.board[v] = p + 1
        parent[v] = v
        sizes[v] = 1
        edges[v] = self.edge_masks[v]
        corners[v] = self.corner_masks[v]
        reach[v] = self.base[p][v]
        root = v

        for u in self.neighbors[v]:
            if u < 0 or parent[u] < 0:
                continue
            other = self.find(p, u)
            if root == other:
                continue
            if sizes[root] < sizes[other]:
                root, other = other, root

            changes.append((
                other, root, sizes[root], edges[root],
                corners[root], reach[root]
            ))
            parent[other] = root
            sizes[root] += sizes[other]
            edges[root] |= edges[other]
            corners[root] |= corners[other]
            ra, rb = reach[root], reach[other]
            reach[root] = tuple(
                a if a < b else b for a, b in zip(ra, rb)
            )

        self.links[p] += len(changes)
        self.best_reach[p] = max(
            old_best, _reach_value(reach[root])
        )

        counts = self.ring_counts
        weights = _RING_WEIGHTS
        for ri in self.through[v]:
            a, b = counts[p][ri], counts[q][ri]
            if b == 0:
                self.ring_score[p] += weights[a + 1] - weights[a]
            if a == 0:
                self.ring_score[q] -= weights[b]
            counts[p][ri] = a + 1

        return changes, old_best, old_scores

    def undo(self, p, v, record):
        changes, old_best, old_scores = record
        parent = self.parent[p]

        for other, root, size, edges, corners, reach in reversed(changes):
            parent[other] = other
            self.size[p][root] = size
            self.edges[p][root] = edges
            self.corners[p][root] = corners
            self.reach[p][root] = reach

        parent[v] = -1
        self.board[v] = 0
        self.links[p] -= len(changes)
        self.best_reach[p] = old_best
        self.ring_score[0], self.ring_score[1] = old_scores
        for ri in self.through[v]:
            self.ring_counts[p][ri] -= 1

    def wins_at(self, p, v):
        parent = self.parent[p]
        roots = []
        edges = self.edge_masks[v]
        corners = self.corner_masks[v]
        occupied = 0

        for u in self.neighbors[v]:
            if u >= 0 and parent[u] >= 0:
                root = u
                while parent[root] != root:
                    root = parent[root]
                roots.append(root)
                edges |= self.edges[p][root]
                corners |= self.corners[p][root]
                occupied += 1
            else:
                roots.append(-1)

        if corners.bit_count() >= 2 or edges.bit_count() >= 3:
            return True
        if occupied < 2:
            return False

        # Separate arcs belonging to the same connected component
        # close a hole in the union of the player's hexagons.
        seen = set()
        previous = roots[-1]
        for root in roots:
            if root >= 0 and root != previous:
                if root in seen:
                    return True
                seen.add(root)
            previous = root

        # Also recognize rings whose interior is already filled with
        # friendly stones; such rings need not create a new empty hole.
        if occupied >= 3:
            counts = self.ring_counts[p]
            for ri in self.through[v]:
                if counts[ri] == 5:
                    return True
        return False

    def winning_moves(self, p, limit=2):
        result = []
        for v, owner in enumerate(self.board):
            if owner == 0 and self.wins_at(p, v):
                result.append(v)
                if len(result) >= limit:
                    break
        return result

    def evaluate(self, p):
        q = 1 - p
        return (
            self.ring_score[p] - self.ring_score[q]
            + self.best_reach[p] - self.best_reach[q]
            + 0.14 * (self.links[p] - self.links[q])
        )

    def ordered_moves(self, p, preferred=None):
        q = 1 - p
        own, enemy = p + 1, q + 1
        weights = _RING_WEIGHTS
        cp, cq = self.ring_counts[p], self.ring_counts[q]
        board = self.board
        result = []

        for v, owner in enumerate(board):
            if owner:
                continue
            attack = defense = 0.0
            for ri in self.through[v]:
                a, b = cp[ri], cq[ri]
                if b == 0:
                    attack += weights[a + 1] - weights[a]
                if a == 0:
                    defense += (
                        0.70 * (weights[b + 1] - weights[b])
                        + 0.30 * weights[b]
                    )

            roots = set()
            friendly = hostile = 0
            for u in self.neighbors[v]:
                if u < 0:
                    continue
                if board[u] == own:
                    friendly += 1
                    roots.add(self.find(p, u))
                elif board[u] == enemy:
                    hostile += 1

            score = attack + 0.86 * defense
            score += 0.14 * min(friendly, 3)
            score += 0.40 * max(0, len(roots) - 1)
            score += 0.035 * min(hostile, 3)

            if roots:
                reach = self.base[p][v]
                for root in roots:
                    other = self.reach[p][root]
                    reach = tuple(
                        a if a < b else b
                        for a, b in zip(reach, other)
                    )
                score += max(
                    0.0, _reach_value(reach) - self.best_reach[p]
                )
            else:
                nearby = sum(board[u] == own for u in self.near_two[v])
                score += 0.12 * min(nearby, 4)
                if not nearby:
                    score -= 0.7

            score += 0.006 * len(self.through[v])
            if v == preferred:
                score += 1000000.0
            result.append((score, v))

        result.sort(reverse=True)
        return [v for _, v in result]

    def search(self, p, depth, alpha, beta, ply=0, extensions=5):
        self.nodes += 1
        if self.nodes & 7 == 0:
            if time.perf_counter() >= self.deadline:
                raise _Timeout

        winning = self.winning_moves(p, 1)
        if winning:
            if ply == 0:
                self.root_answer = winning[0]
            return _WIN - ply

        threats = self.winning_moves(1 - p, 2)
        if len(threats) >= 2:
            return -_WIN + ply + 1

        forced = bool(threats)
        if depth <= 0 and (not forced or extensions <= 0):
            return self.evaluate(p)

        if forced:
            moves = threats
        else:
            preferred = self.preferred if ply == 0 else None
            moves = self.ordered_moves(p, preferred)
            width = 24 if ply == 0 else 9 if ply == 1 else 7 if ply == 2 else 5
            moves = moves[:width]

        if not moves:
            return self.evaluate(p)

        best = -float("inf")
        for v in moves:
            if ply == 0 and time.perf_counter() >= self.deadline:
                raise _Timeout

            record = self.play(p, v)
            try:
                if depth <= 0:
                    value = -self.search(
                        1 - p, 0, -beta, -alpha,
                        ply + 1, extensions - 1
                    )
                else:
                    value = -self.search(
                        1 - p, depth - 1, -beta, -alpha,
                        ply + 1, extensions
                    )
            finally:
                self.undo(p, v, record)

            if value > best:
                best = value
                if ply == 0:
                    self.root_answer = v
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        return best


def _choose(me, opp, valid_mask, started):
    occupied = set(me) | set(opp)
    rows = len(valid_mask)
    cols = len(valid_mask[0]) if rows else 0

    playable = {
        (r, c)
        for r in range(rows)
        for c in range(cols)
        if bool(valid_mask[r][c])
    }
    legal = sorted(playable - occupied)
    if not legal:
        # No legal action exists in a terminal/full state.
        return (0, 0)
    if len(legal) == 1:
        return legal[0]

    # Include occupied cells even when the supplied mask marks only empties.
    cells = sorted(playable | occupied)
    geometry = _geometry(cells)
    index = geometry[1]
    positive = geometry[-1]

    if not me and len(opp) <= 1:
        cr = sum(r for r, c in cells) / len(cells)
        cc = sum(c for r, c in cells) / len(cells)
        target = (cr - 2.0, cc - 2.0 if positive else cc + 2.0)

        def hex_distance(a, b):
            dr, dc = a[0] - b[0], a[1] - b[1]
            return max(abs(dr), abs(dc),
                       abs(dr - dc if positive else dr + dc))

        def opening_score(v):
            score = -hex_distance(v, target)
            score -= 0.15 * hex_distance(v, (cr, cc))
            if opp:
                d = hex_distance(v, opp[0])
                if d <= 1:
                    score -= 5.0
                elif d == 2:
                    score += 0.25
            return score

        return max(legal, key=opening_score)

    initial = [0] * len(cells)
    for cell in me:
        if cell in index:
            initial[index[cell]] = 1
    for cell in opp:
        if cell in index:
            initial[index[cell]] = 2

    position = _Position(geometry, initial, started + 0.90)

    winning = position.winning_moves(0, 1)
    if winning:
        return cells[winning[0]]
    blocking = position.winning_moves(1, 2)
    if blocking:
        return cells[blocking[0]]

    ordered = position.ordered_moves(0)
    best_move = ordered[0]
    position.preferred = best_move

    for depth in range(1, 7):
        position.root_answer = None
        try:
            value = position.search(
                0, depth, -float("inf"), float("inf")
            )
        except _Timeout:
            break

        if position.root_answer is not None:
            best_move = position.root_answer
            position.preferred = best_move
        if value > _WIN / 2:
            break
        if time.perf_counter() >= position.deadline:
            break

    return cells[best_move]


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           valid_mask) -> tuple[int, int]:
    started = time.perf_counter()
    me = [tuple(map(int, cell)) for cell in me]
    opp = [tuple(map(int, cell)) for cell in opp]
    occupied = set(me) | set(opp)

    legal = [
        (r, c)
        for r in range(len(valid_mask))
        for c in range(len(valid_mask[r]))
        if bool(valid_mask[r][c]) and (r, c) not in occupied
    ]
    if not legal:
        return (0, 0)

    legal_set = set(legal)
    fallback = legal[len(legal) // 2]
    try:
        move = _choose(me, opp, valid_mask, started)
        if move in legal_set:
            return (int(move[0]), int(move[1]))
    except Exception:
        pass
    return fallback
