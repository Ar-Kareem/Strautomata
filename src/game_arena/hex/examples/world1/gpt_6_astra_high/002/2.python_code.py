
import heapq
import math
import time

N = 11
SIZE = N * N
INF = 10 ** 6
WIN = 20000.0

DIRECTIONS = ((-1, 0), (-1, 1), (0, -1),
              (0, 1), (1, -1), (1, 0))

NEIGHBORS = []
for r in range(N):
    for c in range(N):
        NEIGHBORS.append(tuple(
            (r + dr) * N + c + dc
            for dr, dc in DIRECTIONS
            if 0 <= r + dr < N and 0 <= c + dc < N
        ))

# A bridge has two endpoints and two alternative connecting cells.
BRIDGES = []
BRIDGES_FROM = [[] for _ in range(SIZE)]
neighbor_sets = [set(ns) for ns in NEIGHBORS]
for v in range(SIZE):
    r, c = divmod(v, N)
    for dr, dc in ((-2, 1), (-1, -1), (-1, 2),
                   (1, -2), (1, 1), (2, -1)):
        rr, cc = r + dr, c + dc
        if not (0 <= rr < N and 0 <= cc < N):
            continue
        u = rr * N + cc
        if u <= v:
            continue
        common = sorted(neighbor_sets[v] & neighbor_sets[u])
        if len(common) == 2:
            x, y = common
            BRIDGES.append((v, u, x, y))
            BRIDGES_FROM[v].append((u, x, y))
            BRIDGES_FROM[u].append((v, x, y))

# Player 1 connects top-bottom; player 2 connects left-right.
EDGES = (
    (tuple(range(N)), tuple(range(SIZE - N, SIZE))),
    (tuple(r * N for r in range(N)),
     tuple(r * N + N - 1 for r in range(N))),
)

TEMPLATES = (
    (
        tuple((N + c, c, c + 1) for c in range(N - 1)),
        tuple(((N - 2) * N + c,
               (N - 1) * N + c - 1,
               (N - 1) * N + c) for c in range(1, N)),
    ),
    (
        tuple((r * N + 1, r * N, (r + 1) * N)
              for r in range(N - 1)),
        tuple((r * N + N - 2,
               (r - 1) * N + N - 1,
               r * N + N - 1) for r in range(1, N)),
    ),
)

NEAR_EDGE = [[[] for _ in range(SIZE)] for _ in range(2)]
for p in range(2):
    for end in range(2):
        for v, x, y in TEMPLATES[p][end]:
            NEAR_EDGE[p][v].append((end, x, y))

EXP = tuple(math.exp(-i / 12.0) for i in range(601))
CENTER = []
for v in range(SIZE):
    r, c = divmod(v, N)
    CENTER.append(-0.015 * (
        abs(r - 5) + abs(c - 5) + abs(r + c - 10)
    ))


def _influence(gap):
    if gap <= 0:
        return 1.0
    if gap >= len(EXP):
        return 0.0
    return EXP[gap]


def _dijkstra(graph, seeds):
    dist = [INF] * SIZE
    heap = []
    push = heapq.heappush
    pop = heapq.heappop

    for v, cost in seeds:
        if cost < dist[v]:
            dist[v] = cost
            push(heap, (cost, v))

    while heap:
        d, v = pop(heap)
        if d != dist[v]:
            continue
        for u, cost in graph[v]:
            nd = d + cost
            if nd < dist[u]:
                dist[u] = nd
                push(heap, (nd, u))
    return dist


class _TimeUp(Exception):
    pass


class _Position:
    __slots__ = ("value", "distance", "a", "b", "wins")

    def __init__(self, value, distance, a, b, wins):
        self.value = value
        self.distance = distance
        self.a = a
        self.b = b
        self.wins = wins


class _Engine:
    def __init__(self, board, started):
        self.board = board
        self.cells = [v for v in range(SIZE) if board[v] == 0]
        self.best = max(self.cells, key=lambda v: CENTER[v])
        self.deadline = started + 0.90
        self.ordering_deadline = started + 0.23
        self.cache = {}

    def check_time(self):
        if time.perf_counter() >= self.deadline:
            raise _TimeUp

    def connection(self, player):
        board = self.board
        enemy = 3 - player
        weights = [10 if stone == 0 else 0 for stone in board]
        graph = [[] for _ in range(SIZE)]

        for v in range(SIZE):
            if board[v] == enemy:
                continue
            graph[v] = [
                (u, weights[u])
                for u in NEIGHBORS[v]
                if board[u] != enemy
            ]

        for v, u, x, y in BRIDGES:
            if board[x] or board[y]:
                continue
            sv, su = board[v], board[u]
            if sv == enemy or su == enemy:
                continue
            if sv != player and su != player:
                continue
            # Positive bridge costs distinguish virtual from actual wins.
            penalty = 1 if sv == player and su == player else 5
            graph[v].append((u, weights[u] + penalty))
            graph[u].append((v, weights[v] + penalty))

        seeds = [[], []]
        p = player - 1
        for end in range(2):
            seeds[end].extend(
                (v, weights[v])
                for v in EDGES[p][end]
                if board[v] != enemy
            )
            for v, x, y in TEMPLATES[p][end]:
                if board[v] != enemy and board[x] == board[y] == 0:
                    penalty = 1 if board[v] == player else 5
                    seeds[end].append((v, weights[v] + penalty))

        a = _dijkstra(graph, seeds[0])
        b = _dijkstra(graph, seeds[1])
        distance = min(
            (a[v] + cost - weights[v] for v, cost in seeds[1]),
            default=INF,
        )
        return a, b, distance

    def evaluate(self):
        self.check_time()
        key = tuple(self.board)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        a1, b1, d1 = self.connection(1)
        a2, b2, d2 = self.connection(2)
        wins1, wins2 = [], []
        mass1 = mass2 = 0.0

        for v in self.cells:
            if self.board[v]:
                continue
            if a1[v] == 10 and b1[v] == 10:
                wins1.append(v)
            if a2[v] == 10 and b2[v] == 10:
                wins2.append(v)
            mass1 += _influence(a1[v] + b1[v] - 10 - d1)
            mass2 += _influence(a2[v] + b2[v] - 10 - d2)

        if d1 == 0:
            value = WIN
        elif d2 == 0:
            value = -WIN
        else:
            x, y = min(d1, 600), min(d2, 600)
            value = (
                y - x
                + 24.0 * math.log((y + 12.0) / (x + 12.0))
                + 3.0 * math.log((mass1 + 1.0) / (mass2 + 1.0))
            )

        result = _Position(
            value, (d1, d2), (a1, a2), (b1, b2),
            (wins1, wins2),
        )
        self.cache[key] = result
        return result

    @staticmethod
    def tactical_value(pos, player, ply):
        if pos.distance[0] == 0:
            return WIN - ply
        if pos.distance[1] == 0:
            return -WIN + ply

        sign = 1 if player == 1 else -1
        if pos.wins[player - 1]:
            return sign * (WIN - ply - 1)
        if len(pos.wins[2 - player]) > 1:
            return -sign * (WIN - ply - 2)
        return None

    def ordered_moves(self, player, pos):
        board = self.board
        p, e = player - 1, 2 - player
        enemy = 3 - player
        a, b = pos.a[p], pos.b[p]
        ea, eb = pos.a[e], pos.b[e]
        d, ed = pos.distance[p], pos.distance[e]
        own_scale = 1.0 + 24.0 / (d + 12.0)
        enemy_scale = 1.0 + 24.0 / (ed + 12.0)
        attack = [0.0] * SIZE

        # Include attacks on important virtual connections in the beam.
        for v, u, x, y in BRIDGES:
            if board[x] or board[y]:
                continue
            sv, su = board[v], board[u]
            if sv == player or su == player:
                continue
            if sv != enemy and su != enemy:
                continue
            complete = sv == enemy and su == enemy
            penalty = 1 if complete else 5
            gap = min(ea[v] + penalty + eb[u],
                      ea[u] + penalty + eb[v]) - ed
            importance = (
                (7.0 if complete else 2.5)
                * enemy_scale * _influence(gap)
            )
            attack[x] += importance
            attack[y] += importance

        for end in range(2):
            for v, x, y in TEMPLATES[e][end]:
                if board[v] == enemy and board[x] == board[y] == 0:
                    gap = (eb[v] if end == 0 else ea[v]) + 1 - ed
                    importance = 6.0 * enemy_scale * _influence(gap)
                    attack[x] += importance
                    attack[y] += importance

        scored = []
        for v in self.cells:
            if board[v]:
                continue

            # Estimate the connection improvement from occupying v.
            left, right = a[v] - 10, b[v] - 10
            for u, x, y in BRIDGES_FROM[v]:
                if board[u] == player and board[x] == board[y] == 0:
                    left = min(left, a[u] + 1)
                    right = min(right, b[u] + 1)

            for end, x, y in NEAR_EDGE[p][v]:
                if board[x] == board[y] == 0:
                    if end == 0:
                        left = min(left, 1)
                    else:
                        right = min(right, 1)

            gain = max(0, d - left - right)
            own_gap = a[v] + b[v] - 10 - d
            enemy_gap = ea[v] + eb[v] - 10 - ed
            score = (
                own_scale * gain
                + 2.0 * _influence(own_gap)
                + 5.0 * enemy_scale * _influence(enemy_gap)
                + attack[v]
                + CENTER[v]
            )
            scored.append((score, v))

        scored.sort(reverse=True)
        return [v for _, v in scored]

    def search(self, player, depth, alpha, beta, ply, qleft=3):
        self.check_time()
        pos = self.evaluate()
        tactical = self.tactical_value(pos, player, ply)
        if tactical is not None:
            return tactical

        forced = pos.wins[2 - player]
        if depth <= 0:
            if not forced or qleft <= 0:
                return pos.value
            moves = forced
            next_depth = 0
            next_q = qleft - 1
        else:
            next_depth = depth - 1
            next_q = qleft
            if forced:
                moves = forced
            else:
                width = 12 if ply == 1 else (8 if ply == 2 else 6)
                moves = self.ordered_moves(player, pos)[:width]

        if not moves:
            return pos.value

        if player == 1:
            value = -2 * WIN
            for move in moves:
                self.board[move] = 1
                try:
                    child = self.search(
                        2, next_depth, alpha, beta, ply + 1, next_q
                    )
                finally:
                    self.board[move] = 0
                value = max(value, child)
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value

        value = 2 * WIN
        for move in moves:
            self.board[move] = 2
            try:
                child = self.search(
                    1, next_depth, alpha, beta, ply + 1, next_q
                )
            finally:
                self.board[move] = 0
            value = min(value, child)
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    def run(self):
        root = self.evaluate()
        if root.wins[0]:
            return max(root.wins[0], key=lambda v: CENTER[v])
        if root.wins[1]:
            return max(root.wins[1], key=lambda v: CENTER[v])

        ordered = self.ordered_moves(1, root)
        self.best = ordered[0]
        static_scores = {}
        candidates = []

        # Evaluate a broad root pool before narrowing the search.
        for move in ordered[:56]:
            if (len(candidates) >= 16
                    and time.perf_counter() >= self.ordering_deadline):
                break
            self.board[move] = 1
            try:
                value = self.search(2, 0, -2 * WIN, 2 * WIN, 1)
            finally:
                self.board[move] = 0

            static_scores[move] = value
            candidates.append((value, move))
            if value > static_scores.get(self.best, -3 * WIN):
                self.best = move
            if value > WIN - 100:
                self.best = move
                return move

        candidates.sort(
            key=lambda item: (item[0], CENTER[item[1]]),
            reverse=True,
        )
        roots = [move for _, move in candidates[:16]]
        if not roots:
            return self.best
        self.best = roots[0]

        for depth in range(2, 7):
            results = []
            alpha = -2 * WIN
            iteration_best = roots[0]
            interrupted = False

            try:
                for move in roots:
                    self.check_time()
                    self.board[move] = 1
                    try:
                        value = self.search(
                            2, depth - 1, alpha, 2 * WIN, 1
                        )
                    finally:
                        self.board[move] = 0

                    results.append((value, move))
                    if value > alpha:
                        alpha = value
                        iteration_best = move

                    if value > WIN - 100:
                        self.best = move
                        return move
            except _TimeUp:
                interrupted = True

            # The previous principal variation is searched first.
            if results and (
                not interrupted or len(results) >= 2 or depth == 2
            ):
                self.best = iteration_best

            if interrupted:
                break

            results.sort(
                key=lambda item: (
                    item[0], static_scores[item[1]], CENTER[item[1]]
                ),
                reverse=True,
            )
            roots = [move for _, move in results]

        return self.best


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[int, int]:
    started = time.perf_counter()
    transpose = color == "w"
    board = [0] * SIZE

    for r, c in me:
        if transpose:
            r, c = c, r
        board[r * N + c] = 1

    for r, c in opp:
        if transpose:
            r, c = c, r
        board[r * N + c] = 2

    legal = [v for v in range(SIZE) if board[v] == 0]
    if not legal:
        # A full board cannot occur in a valid nonterminal Hex position.
        return (0, 0)

    if len(legal) == SIZE:
        return (5, 5)
    if len(legal) == 1:
        r, c = divmod(legal[0], N)
        return (c, r) if transpose else (r, c)

    engine = _Engine(board, started)
    try:
        move = engine.run()
    except Exception:
        # In particular, preserve the best completed result on timeout.
        move = engine.best

    if move not in legal:
        move = legal[0]

    r, c = divmod(move, N)
    return (c, r) if transpose else (r, c)
