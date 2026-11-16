
import math
import random
import time
import heapq

N = 11
CELLS = 121
TOP, BOTTOM, LEFT, RIGHT = 121, 122, 123, 124
START = (0, TOP, LEFT)
GOAL = (0, BOTTOM, RIGHT)


def _build_tables():
    neighbors = []
    directions = ((-1, 0), (-1, 1), (0, -1),
                  (0, 1), (1, -1), (1, 0))

    for r in range(N):
        for c in range(N):
            neighbors.append(tuple(
                (r + dr) * N + c + dc
                for dr, dc in directions
                if 0 <= r + dr < N and 0 <= c + dc < N
            ))

    adj = [None, [list(x) for x in neighbors] + [[], [], [], []],
           [list(x) for x in neighbors] + [[], [], [], []]]
    all_neighbors = [list(x) for x in neighbors]

    for m in range(CELLS):
        r, c = divmod(m, N)
        edges = []
        if r == 0:
            edges.append((1, TOP))
        if r == N - 1:
            edges.append((1, BOTTOM))
        if c == 0:
            edges.append((2, LEFT))
        if c == N - 1:
            edges.append((2, RIGHT))
        for side, edge in edges:
            adj[side][m].append(edge)
            adj[side][edge].append(m)
            all_neighbors[m].append(edge)

    bridges = []
    jumps = ((-2, 1), (-1, -1), (-1, 2),
             (1, -2), (1, 1), (2, -1))
    for a in range(CELLS):
        r, c = divmod(a, N)
        for dr, dc in jumps:
            rr, cc = r + dr, c + dc
            if not (0 <= rr < N and 0 <= cc < N):
                continue
            b = rr * N + cc
            if b <= a:
                continue
            common = [x for x in neighbors[a] if x in neighbors[b]]
            if len(common) == 2:
                bridges.append((a, b, common[0], common[1]))

    virtual = [None, [[] for _ in range(125)],
               [[] for _ in range(125)]]
    repair = [None, [[] for _ in range(CELLS)],
              [[] for _ in range(CELLS)]]

    for side in (1, 2):
        patterns = list(bridges)
        if side == 1:
            for c in range(10):
                patterns.append((11 + c, TOP, c, c + 1))
            for c in range(1, 11):
                patterns.append((99 + c, BOTTOM, 110 + c, 109 + c))
        else:
            for r in range(10):
                patterns.append((11 * r + 1, LEFT, 11 * r, 11 * (r + 1)))
            for r in range(1, 11):
                patterns.append((11 * r + 9, RIGHT,
                                 11 * r + 10, 11 * (r - 1) + 10))

        for a, b, x, y in patterns:
            virtual[side][a].append((b, x, y))
            virtual[side][b].append((a, x, y))
            repair[side][x].append((y, a, b))
            repair[side][y].append((x, a, b))

    for side in (1, 2):
        adj[side] = tuple(tuple(x) for x in adj[side])
        virtual[side] = tuple(tuple(x) for x in virtual[side])
        repair[side] = tuple(tuple(x) for x in repair[side])

    return (tuple(neighbors), adj, virtual, repair,
            tuple(tuple(x) for x in all_neighbors))


NB, ADJ, VIRTUAL, REPAIR, ALL_NEIGHBORS = _build_tables()


def _find(parent, x):
    while parent[x] >= 0:
        if parent[parent[x]] >= 0:
            parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _play(board, parent, flags, move, side):
    """Place a stone, update connectivity, and report an exact win."""
    board[move] = side
    root = move
    for q in ADJ[side][move]:
        if board[q] != side:
            continue
        q = _find(parent, q)
        if root == q:
            continue
        if parent[root] > parent[q]:
            root, q = q, root
        parent[root] += parent[q]
        parent[q] = root
        flags[root] |= flags[q]
    return flags[root] == 3


def _urgent(board, parent, flags, empties, side):
    """Return immediate winning moves or mandatory blocking moves."""
    blocks = []
    for m in empties:
        bits1 = bits2 = 0
        for q in ALL_NEIGHBORS[m]:
            occupant = board[q]
            if occupant == 1:
                bits1 |= flags[_find(parent, q)]
            elif occupant == 2:
                bits2 |= flags[_find(parent, q)]
        own, enemy = (bits1, bits2) if side == 1 else (bits2, bits1)
        if own == 3:
            return [m]
        if enemy == 3:
            blocks.append(m)
    return blocks


def _rescue(board, parent, last, side):
    if last < 0:
        return -1
    for other, a, b in REPAIR[side][last]:
        if (board[other] == 0 and board[a] == side and board[b] == side
                and _find(parent, a) != _find(parent, b)):
            return other
    return -1


def _distances(board, side, source, target=-1):
    """Shortest paths with inexpensive, intact two-carrier bridges."""
    inf = 10000.0
    distance = [inf] * 125
    distance[source] = 0.0
    queue = [(0.0, source)]
    adjacency = ADJ[side]
    virtual = VIRTUAL[side]
    enemy = 3 - side
    push = heapq.heappush
    pop = heapq.heappop

    while queue:
        d, u = pop(queue)
        if d != distance[u]:
            continue
        if u == target:
            return d

        for v in adjacency[u]:
            occupant = board[v]
            if occupant == enemy:
                continue
            nd = d + (1.0 if occupant == 0 else 0.0)
            if nd < distance[v]:
                distance[v] = nd
                push(queue, (nd, v))

        if board[u] == side:
            for v, x, y in virtual[u]:
                if board[v] == side and board[x] == 0 and board[y] == 0:
                    nd = d + 0.4
                    if nd < distance[v]:
                        distance[v] = nd
                        push(queue, (nd, v))

    return distance if target < 0 else inf


def _make_priors(board, parent, empties, started):
    forward = [None, None, None]
    backward = [None, None, None]
    baseline = [0.0, 0.0, 0.0]
    corridor = [None, [0.0] * CELLS, [0.0] * CELLS]
    raw = [None, [0.0] * CELLS, [0.0] * CELLS]

    for side in (1, 2):
        forward[side] = _distances(board, side, START[side])
        backward[side] = _distances(board, side, GOAL[side])
        baseline[side] = forward[side][GOAL[side]]
        for m in empties:
            excess = (forward[side][m] + backward[side][m]
                      - 1.0 - baseline[side])
            corridor[side][m] = math.exp(-0.8 * max(0.0, excess))

    for side in (1, 2):
        enemy = 3 - side
        for m in empties:
            r, c = divmod(m, N)
            central = 1.0 - ((r - 5) ** 2 + (c - 5) ** 2) / 50.0
            raw[side][m] = (0.8 * corridor[side][m]
                            + 0.35 * corridor[enemy][m]
                            + 0.04 * central)

    ordering = sorted(
        empties,
        key=lambda m: max(raw[1][m], raw[2][m]),
        reverse=True
    )

    # Refine strategically relevant moves with explicit placements.
    for m in ordering:
        if time.perf_counter() - started > 0.19:
            break
        r, c = divmod(m, N)
        central = 1.0 - ((r - 5) ** 2 + (c - 5) ** 2) / 50.0
        for side in (1, 2):
            enemy = 3 - side
            board[m] = side
            own_distance = _distances(
                board, side, START[side], GOAL[side])
            enemy_distance = _distances(
                board, enemy, START[enemy], GOAL[enemy])
            raw[side][m] = (
                baseline[side] - own_distance
                + 0.85 * (enemy_distance - baseline[enemy])
                + 0.22 * corridor[side][m]
                + 0.15 * corridor[enemy][m]
                + 0.04 * central
            )
        board[m] = 0

    # Existing broken bridges deserve attention, even when move order
    # is unavailable in the supplied stone lists.
    for side in (1, 2):
        repairs = set()
        for m in range(CELLS):
            if board[m] == 3 - side:
                for other, a, b in REPAIR[side][m]:
                    if (board[other] == 0 and board[a] == side
                            and board[b] == side
                            and _find(parent, a) != _find(parent, b)):
                        repairs.add(other)
        for m in repairs:
            raw[side][m] += 0.18

    priors = [None, [0.5] * CELLS, [0.5] * CELLS]
    for side in (1, 2):
        values = [raw[side][m] for m in empties]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        scale = 0.30 + math.sqrt(variance)
        for m in empties:
            priors[side][m] = (
                0.5 + 0.23 * math.tanh((raw[side][m] - mean) / scale)
            )
    return priors


class _Node:
    __slots__ = (
        "turn", "move", "prior", "children", "pending",
        "n", "w", "rn", "rw", "terminal", "forced"
    )

    def __init__(self, turn, move, prior, board, parent, flags,
                 priors, terminal=0):
        self.turn = turn
        self.move = move
        self.prior = prior
        self.children = []
        self.n = 0
        self.w = 0
        self.rn = [0] * CELLS
        self.rw = [0] * CELLS
        self.terminal = terminal
        self.forced = -1

        if terminal:
            self.pending = []
            return

        empties = [m for m in range(CELLS) if board[m] == 0]
        urgent = _urgent(board, parent, flags, empties, turn)
        if urgent:
            self.forced = urgent[0]
            choices = urgent
        else:
            choices = empties

        rescue = _rescue(board, parent, move, turn)
        base = priors[turn]
        pending = []
        for m in choices:
            friends = enemies = 0
            for q in NB[m]:
                if board[q] == turn:
                    friends += 1
                elif board[q]:
                    enemies += 1
            p = base[m]
            p += 0.012 * min(friends, 2) + 0.006 * min(enemies, 2)
            if friends >= 4:
                p -= 0.025
            if m == rescue:
                p += 0.12
            pending.append((m, min(0.9, max(0.1, p))))
        self.pending = pending


def _rollout(board, parent, flags, turn, last, sequence,
             first, priors, rng):
    empties = [m for m in range(CELLS) if board[m] == 0]
    position = [-1] * CELLS
    for i, m in enumerate(empties):
        position[m] = i

    step = 0
    while empties:
        if first >= 0 and board[first] == 0:
            move = first
        else:
            move = _rescue(board, parent, last, turn)
        first = -1

        if move < 0:
            k = rng.randrange(len(empties))
            move = empties[k]
            # Light guidance early; retain diverse random completions.
            if step < 8 and len(empties) > 1:
                other = empties[rng.randrange(len(empties))]
                if priors[turn][other] > priors[turn][move]:
                    move = other

        k = position[move]
        tail = empties.pop()
        if k < len(empties):
            empties[k] = tail
            position[tail] = k
        position[move] = -1

        sequence.append(move)
        if _play(board, parent, flags, move, turn):
            return turn
        last = move
        turn = 3 - turn
        step += 1

    # A full Hex board always has a winner.
    return 3 - turn


def _search(mine, theirs, started):
    board = [0] * CELLS + [1, 1, 2, 2]
    parent = [-1] * 125
    flags = [0] * CELLS + [1, 2, 1, 2]

    for m in mine:
        _play(board, parent, flags, m, 1)
    for m in theirs:
        _play(board, parent, flags, m, 2)

    empties = [m for m in range(CELLS) if board[m] == 0]
    if len(empties) == 1:
        return empties[0]
    if not mine and not theirs:
        return 60

    urgent = _urgent(board, parent, flags, empties, 1)
    if urgent:
        return urgent[0]

    priors = _make_priors(board, parent, empties, started)
    root = _Node(1, -1, 0.5, board, parent, flags, priors)

    seed = 1234567
    for m in mine:
        seed ^= (m + 1) * 1000003
    for m in theirs:
        seed ^= (m + 1) * 972663749
    rng = random.Random(seed)

    deadline = started + 0.90
    sqrt = math.sqrt
    log = math.log

    while time.perf_counter() < deadline:
        b = board[:]
        p = parent[:]
        f = flags[:]
        node = root
        path = [root]
        sequence = []
        winner = 0

        while True:
            if node.terminal:
                winner = node.terminal
                break

            width = 5 + int(1.6 * sqrt(node.n + 1))
            if node.pending and len(node.children) < width:
                best_index = 0
                best_score = -1e100
                for i, (move, prior) in enumerate(node.pending):
                    count = node.rn[move]
                    score = ((node.rw[move] + 12.0 * prior)
                             / (count + 12.0) + 0.08 * prior)
                    if score > best_score:
                        best_score = score
                        best_index = i

                move, prior = node.pending[best_index]
                node.pending[best_index] = node.pending[-1]
                node.pending.pop()

                side = node.turn
                sequence.append(move)
                won = _play(b, p, f, move, side)
                child = _Node(
                    3 - side, move, prior, b, p, f, priors,
                    terminal=side if won else 0
                )
                node.children.append(child)
                node = child
                path.append(node)

                if won:
                    winner = side
                else:
                    winner = _rollout(
                        b, p, f, node.turn, move, sequence,
                        node.forced, priors, rng
                    )
                break

            if not node.children:
                winner = _rollout(
                    b, p, f, node.turn, node.move, sequence,
                    node.forced, priors, rng
                )
                break

            exploration = log(node.n + 1.0)
            best_child = None
            best_score = -1e100
            for child in node.children:
                visits = child.n
                amaf_n = node.rn[child.move]
                beta = amaf_n / (
                    amaf_n + visits + amaf_n * visits / 250.0 + 1e-9
                )
                direct = (child.w + 2.0 * child.prior) / (visits + 2.0)
                amaf = ((node.rw[child.move] + 8.0 * child.prior)
                        / (amaf_n + 8.0))
                score = (
                    (1.0 - beta) * direct + beta * amaf
                    + 0.48 * sqrt(exploration / (visits + 1.0))
                    + 0.12 * (child.prior - 0.5) / (1.0 + 0.1 * visits)
                )
                if score > best_score:
                    best_score = score
                    best_child = child

            side = node.turn
            sequence.append(best_child.move)
            won = _play(b, p, f, best_child.move, side)
            node = best_child
            path.append(node)
            if won:
                winner = side
                break

        # Direct statistics use the incoming player's perspective.
        # RAVE statistics use the player to move at the current node.
        for depth, visited in enumerate(path):
            visited.n += 1
            visited.w += int(winner != visited.turn)
            success = int(winner == visited.turn)
            rn, rw = visited.rn, visited.rw
            for move in sequence[depth::2]:
                rn[move] += 1
                rw[move] += success

    if root.children:
        return max(
            root.children,
            key=lambda child: (child.n, child.w / max(1, child.n),
                               child.prior)
        ).move
    return max(empties, key=lambda m: priors[1][m])


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[int, int]:
    started = time.perf_counter()
    occupied = set(me) | set(opp)
    legal = [(r, c) for r in range(N) for c in range(N)
             if (r, c) not in occupied]

    # The arena supplies nonterminal positions with an empty cell.
    if not legal:
        return (0, 0)

    fallback = min(
        legal,
        key=lambda rc: (rc[0] - 5) ** 2 + (rc[1] - 5) ** 2
    )

    try:
        transpose = color == "w"
        if transpose:
            mine = [c * N + r for r, c in me]
            theirs = [c * N + r for r, c in opp]
        else:
            mine = [r * N + c for r, c in me]
            theirs = [r * N + c for r, c in opp]

        move = _search(mine, theirs, started)
        r, c = divmod(move, N)
        result = (c, r) if transpose else (r, c)
        if (0 <= result[0] < N and 0 <= result[1] < N
                and result not in occupied):
            return result
    except Exception:
        # Preserve a legal response if an unexpected runtime issue occurs.
        pass

    return fallback
