
import heapq
import math
import time
from collections import deque

N = 11
SIZE = N * N
WIN = 1_000_000
INF = 10**9

DIRECTIONS = (
    (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0),
)

BITS = tuple(1 << i for i in range(SIZE))
COORDS = tuple(divmod(i, N) for i in range(SIZE))

NEIGHBORS = []
for r, c in COORDS:
    ns = []
    for dr, dc in DIRECTIONS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            ns.append(rr * N + cc)
    NEIGHBORS.append(tuple(ns))
NEIGHBORS = tuple(NEIGHBORS)

# A bridge has two nonadjacent endpoints and two common neighbors.
_neighbor_sets = tuple(set(ns) for ns in NEIGHBORS)
BRIDGE_NEIGHBORS = [[] for _ in range(SIZE)]
BRIDGE_PAIRS = []

for i in range(SIZE):
    for j in range(i + 1, SIZE):
        if j in _neighbor_sets[i]:
            continue
        common = _neighbor_sets[i] & _neighbor_sets[j]
        if len(common) == 2:
            a, b = sorted(common)
            BRIDGE_NEIGHBORS[i].append((j, a, b))
            BRIDGE_NEIGHBORS[j].append((i, a, b))
            BRIDGE_PAIRS.append((i, j, a, b))

BRIDGE_NEIGHBORS = tuple(tuple(x) for x in BRIDGE_NEIGHBORS)
BRIDGE_PAIRS = tuple(BRIDGE_PAIRS)

# Internally player 1 connects top to bottom; player 2 connects left to right.
EDGES = (
    (
        tuple(range(N)),
        tuple(range(SIZE - N, SIZE)),
    ),
    (
        tuple(r * N for r in range(N)),
        tuple(r * N + N - 1 for r in range(N)),
    ),
)

EDGE_FLAGS = []
VIRTUAL_EDGES = []

for player_edges in EDGES:
    flags_for_player = []
    virtual_for_player = []
    for edge in player_edges:
        edge_set = set(edge)
        flags_for_player.append(tuple(i in edge_set for i in range(SIZE)))
        virtual = []
        for i in range(SIZE):
            if i in edge_set:
                continue
            common = _neighbor_sets[i] & edge_set
            if len(common) == 2:
                a, b = sorted(common)
                virtual.append((i, a, b))
        virtual_for_player.append(tuple(virtual))
    EDGE_FLAGS.append(tuple(flags_for_player))
    VIRTUAL_EDGES.append(tuple(virtual_for_player))

EDGE_FLAGS = tuple(EDGE_FLAGS)
VIRTUAL_EDGES = tuple(VIRTUAL_EDGES)

# Lookup table for near-shortest-route relevance.
EXP_TABLE = tuple(math.exp(-x / 135.0) for x in range(3001))


class _Deadline(Exception):
    pass


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str,
) -> tuple[int, int]:
    started = time.perf_counter()
    deadline = started + 0.90
    transpose = color == "w"

    board = [0] * SIZE
    my_bits = 0
    opp_bits = 0

    for r, c in me:
        i = c * N + r if transpose else r * N + c
        board[i] = 1
        my_bits |= BITS[i]

    for r, c in opp:
        i = c * N + r if transpose else r * N + c
        board[i] = 2
        opp_bits |= BITS[i]

    legal = [i for i in range(SIZE) if board[i] == 0]

    # A full board is terminal and has no legal action.
    if not legal:
        return (0, 0)

    def decode(i):
        r, c = COORDS[i]
        return (c, r) if transpose else (r, c)

    def centrality(i):
        r, c = COORDS[i]
        dr, dc = r - 5, c - 5
        return max(abs(dr), abs(dc), abs(dr + dc))

    answer = min(legal, key=lambda i: (centrality(i), i))

    if len(legal) == SIZE:
        return (5, 5)

    def winning_cells(player):
        """Empty cells which immediately complete an actual connection."""
        frontiers = []
        for edge in EDGES[player - 1]:
            seen = 0
            frontier = 0
            stack = []
            for i in edge:
                if board[i] == player:
                    if not seen & BITS[i]:
                        seen |= BITS[i]
                        stack.append(i)
                elif board[i] == 0:
                    frontier |= BITS[i]

            while stack:
                i = stack.pop()
                for j in NEIGHBORS[i]:
                    if board[j] == 0:
                        frontier |= BITS[j]
                    elif board[j] == player and not seen & BITS[j]:
                        seen |= BITS[j]
                        stack.append(j)
            frontiers.append(frontier)

        return frontiers[0] & frontiers[1]

    winning = winning_cells(1)
    if winning:
        return decode(min(
            (i for i in legal if winning & BITS[i]),
            key=lambda i: (centrality(i), i),
        ))

    blocking = winning_cells(2)
    if blocking:
        return decode(min(
            (i for i in legal if blocking & BITS[i]),
            key=lambda i: (centrality(i), i),
        ))

    cache = {}

    def actual_distance(player):
        """0-1 shortest path: own stones cost zero, empty cells cost one."""
        enemy = 3 - player
        dist = [10000] * SIZE
        queue = deque()

        for i in EDGES[player - 1][0]:
            if board[i] == player:
                dist[i] = 0
                queue.appendleft(i)
            elif board[i] == 0:
                dist[i] = 1
                queue.append(i)

        target = EDGE_FLAGS[player - 1][1]

        while queue:
            i = queue.popleft()
            di = dist[i]
            if target[i]:
                return di

            for j in NEIGHBORS[i]:
                bj = board[j]
                if bj == enemy:
                    continue
                step = 1 if bj == 0 else 0
                nd = di + step
                if nd < dist[j]:
                    dist[j] = nd
                    if step:
                        queue.append(j)
                    else:
                        queue.appendleft(j)

        return 10000

    def dijkstra(graph, sources):
        dist = [INF] * SIZE
        heap = []
        for i, cost in sources:
            if cost < dist[i]:
                dist[i] = cost
                heap.append((cost, i))
        heapq.heapify(heap)

        pop = heapq.heappop
        push = heapq.heappush

        while heap:
            di, i = pop(heap)
            if di != dist[i]:
                continue
            for j, cost in graph[i]:
                nd = di + cost
                if nd < dist[j]:
                    dist[j] = nd
                    push(heap, (nd, j))
        return dist

    def connection_data(player, actual, weights):
        enemy = 3 - player
        graph = [[] for _ in range(SIZE)]

        for i in range(SIZE):
            if board[i] == enemy:
                continue

            row = graph[i]
            for j in NEIGHBORS[i]:
                if board[j] != enemy:
                    row.append((j, weights[j]))

            bridge_base = 12 + (22 if board[i] == 0 else 0)
            for j, a, b in BRIDGE_NEIGHBORS[i]:
                if board[j] != enemy and board[a] == board[b] == 0:
                    cost = weights[j] + bridge_base
                    if board[j] == 0:
                        cost += 22
                    row.append((j, cost))

        sources = []
        for side in range(2):
            side_sources = []
            for i in EDGES[player - 1][side]:
                if board[i] != enemy:
                    side_sources.append((i, weights[i]))

            for i, a, b in VIRTUAL_EDGES[player - 1][side]:
                if board[i] != enemy and board[a] == board[b] == 0:
                    cost = weights[i] + 12
                    if board[i] == 0:
                        cost += 22
                    side_sources.append((i, cost))

            sources.append(side_sources)

        top = dijkstra(graph, sources[0])
        bottom = dijkstra(graph, sources[1])

        distance = min(
            (top[i] + cost - weights[i] for i, cost in sources[1]),
            default=INF,
        )

        potential = [0.0] * SIZE
        flexibility = 0.0

        for i in range(SIZE):
            if board[i] != 0:
                continue
            slack = top[i] + bottom[i] - 100 - distance
            if slack < 0:
                slack = 0
            if slack < len(EXP_TABLE):
                value = EXP_TABLE[slack]
                potential[i] = value
                flexibility += value

        merit = (
            -distance
            -24.0 * actual
            -75.0 * math.log1p(distance / 100.0)
            +20.0 * math.log1p(flexibility / (1.0 + distance / 100.0))
        )

        return distance, actual, top, bottom, potential, merit

    def analyse(bits1, bits2):
        if time.perf_counter() >= deadline:
            raise _Deadline

        key = (bits1, bits2)
        result = cache.get(key)
        if result is not None:
            return result

        a1 = actual_distance(1)
        a2 = actual_distance(2)

        if a1 == 0 or a2 == 0:
            score = WIN if a1 == 0 else -WIN
            result = (
                score,
                (0, a1, None, None, None, 0),
                (0, a2, None, None, None, 0),
            )
            cache[key] = result
            return result

        weights = [100 if stone == 0 else 0 for stone in board]
        data1 = connection_data(1, a1, weights)
        data2 = connection_data(2, a2, weights)

        positional = 0.0
        occupied = 0
        for i, stone in enumerate(board):
            if not stone:
                continue
            occupied += 1
            r, c = COORDS[i]
            if stone == 1:
                positional += (5 - abs(c - 5)) + 0.3 * (5 - abs(r - 5))
            else:
                positional -= (5 - abs(r - 5)) + 0.3 * (5 - abs(c - 5))

        phase = max(0.0, 1.0 - occupied / 65.0)
        score = data1[5] - data2[5] + 2.5 * phase * positional

        result = (score, data1, data2)
        cache[key] = result
        return result

    def relevance(slack):
        if slack <= 0:
            return 1.0
        if slack >= len(EXP_TABLE):
            return 0.0
        return EXP_TABLE[slack]

    def ranked_moves(info, player, limit):
        ours = info[player]
        theirs = info[3 - player]
        scores = [-INF] * SIZE
        empties = []

        for i in range(SIZE):
            if board[i]:
                continue
            empties.append(i)
            value = 112.0 * ours[4][i] + 108.0 * theirs[4][i]
            value += 0.6 * (10 - centrality(i))

            for j in NEIGHBORS[i]:
                if board[j] == player:
                    value += 2.0
                elif board[j]:
                    value += 2.5

            for j, a, b in BRIDGE_NEIGHBORS[i]:
                if board[j] == player and board[a] == board[b] == 0:
                    value += 5.0

            scores[i] = value

        # Include bridge repairs and attacks even when their carrier cells
        # are not themselves on a shortest virtual route.
        for u, v, a, b in BRIDGE_PAIRS:
            owner = board[u]
            if owner == 0 or board[v] != owner:
                continue

            data = info[owner]
            slack = min(
                data[2][u] + data[3][v],
                data[2][v] + data[3][u],
            ) - data[0]
            rel = relevance(slack)

            if board[a] == board[b] == 0:
                bonus = (7.0 if owner == player else 22.0) * rel
                scores[a] += bonus
                scores[b] += bonus
            elif board[a] == 0 and board[b] == 3 - owner:
                scores[a] += (65.0 if owner == player else 50.0) * rel
            elif board[b] == 0 and board[a] == 3 - owner:
                scores[b] += (65.0 if owner == player else 50.0) * rel

        for owner in (1, 2):
            data = info[owner]
            for side in range(2):
                opposite_distance = data[3] if side == 0 else data[2]
                for i, a, b in VIRTUAL_EDGES[owner - 1][side]:
                    if board[i] != owner:
                        continue

                    rel = relevance(opposite_distance[i] + 12 - data[0])
                    if board[a] == board[b] == 0:
                        bonus = (6.0 if owner == player else 20.0) * rel
                        scores[a] += bonus
                        scores[b] += bonus
                    elif board[a] == 0 and board[b] == 3 - owner:
                        scores[a] += 60.0 * rel
                    elif board[b] == 0 and board[a] == 3 - owner:
                        scores[b] += 60.0 * rel

        empties.sort(key=lambda i: scores[i], reverse=True)
        return empties[:limit]

    def ordering_value(info, mover):
        if info[mover][1] == 0:
            return WIN
        if info[3 - mover][1] <= 1:
            return -WIN
        value = info[0] if mover == 1 else -info[0]
        if info[mover][1] == 1:
            value += 45.0
        return value

    def negamax(bits1, bits2, player, depth, alpha, beta, ply, qleft=4):
        if time.perf_counter() >= deadline:
            raise _Deadline

        info = analyse(bits1, bits2)
        other = 3 - player
        ours = info[player][1]
        theirs = info[other][1]

        if ours == 0:
            return WIN - ply
        if theirs == 0:
            return -WIN + ply
        if ours == 1:
            return WIN - ply - 1

        if theirs == 1:
            forced = winning_cells(other)
            if forced & (forced - 1):
                return -WIN + ply + 2

            if forced:
                if depth <= 0 and qleft <= 0:
                    static = info[0] if player == 1 else -info[0]
                    return static - 80.0

                move = (forced & -forced).bit_length() - 1
                board[move] = player
                try:
                    nb1 = bits1 | BITS[move] if player == 1 else bits1
                    nb2 = bits2 | BITS[move] if player == 2 else bits2
                    return -negamax(
                        nb1, nb2, other, max(0, depth - 1),
                        -beta, -alpha, ply + 1,
                        qleft - (1 if depth <= 0 else 0),
                    )
                finally:
                    board[move] = 0

        if depth <= 0:
            return info[0] if player == 1 else -info[0]

        moves = ranked_moves(info, player, 16 if depth == 1 else 18)
        if not moves:
            return info[0] if player == 1 else -info[0]

        if depth >= 2:
            ordered = []
            for move in moves:
                board[move] = player
                try:
                    nb1 = bits1 | BITS[move] if player == 1 else bits1
                    nb2 = bits2 | BITS[move] if player == 2 else bits2
                    child = analyse(nb1, nb2)
                    ordered.append((ordering_value(child, player), move))
                finally:
                    board[move] = 0

            ordered.sort(reverse=True)
            width = 7 if depth == 2 else 6
            moves = [move for _, move in ordered[:width]]

        best = -2 * WIN
        for move in moves:
            board[move] = player
            try:
                nb1 = bits1 | BITS[move] if player == 1 else bits1
                nb2 = bits2 | BITS[move] if player == 2 else bits2
                value = -negamax(
                    nb1, nb2, other, depth - 1,
                    -beta, -alpha, ply + 1, qleft,
                )
            finally:
                board[move] = 0

            if value > best:
                best = value
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        return best

    try:
        root = analyse(my_bits, opp_bits)
        initial_order = ranked_moves(root, 1, len(legal))

        scored = []
        best_initial = -2 * WIN

        # Evaluate every legal root move before narrowing the search.
        for move in initial_order:
            board[move] = 1
            try:
                child = analyse(my_bits | BITS[move], opp_bits)
                value = ordering_value(child, 1)
            finally:
                board[move] = 0

            scored.append((value, move))
            if value > best_initial:
                best_initial = value
                answer = move

        scored.sort(reverse=True)
        root_order = [move for _, move in scored[:14]]

        for depth in range(2, 7):
            width = 14 if depth == 2 else 10 if depth == 3 else 7
            current_results = []
            current_best = -2 * WIN
            alpha = -2 * WIN

            for move in root_order[:width]:
                board[move] = 1
                try:
                    value = -negamax(
                        my_bits | BITS[move], opp_bits, 2,
                        depth - 1, -2 * WIN, -alpha, 1,
                    )
                finally:
                    board[move] = 0

                current_results.append((value, move))
                if value > current_best:
                    current_best = value
                    answer = move
                if value > alpha:
                    alpha = value

            current_results.sort(reverse=True)
            root_order = [move for _, move in current_results]

            if current_best > WIN / 2:
                break

    except _Deadline:
        pass

    # Every search mutation is restored with finally; retain a final guard.
    if board[answer] != 0:
        answer = legal[0]

    return decode(answer)
