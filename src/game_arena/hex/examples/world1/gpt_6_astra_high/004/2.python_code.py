
import heapq
import math
import time

N = 11
SIZE = N * N
ALL = (1 << SIZE) - 1
INF = 10**7
WIN = 10**6

DIRECTIONS = (
    (-1, 0), (-1, 1),
    (0, -1), (0, 1),
    (1, -1), (1, 0),
)

NEIGHBORS = []
for r in range(N):
    for c in range(N):
        NEIGHBORS.append(tuple(
            (r + dr) * N + c + dc
            for dr, dc in DIRECTIONS
            if 0 <= r + dr < N and 0 <= c + dc < N
        ))
NEIGHBORS = tuple(NEIGHBORS)

LEFT = sum(1 << (r * N) for r in range(N))
RIGHT = sum(1 << (r * N + N - 1) for r in range(N))
TOP = (1 << N) - 1
BOTTOM = TOP << (N * (N - 1))
NOT_LEFT = ALL ^ LEFT
NOT_RIGHT = ALL ^ RIGHT

EDGE_CELLS = (
    (
        tuple(range(N)),
        tuple(range(N * (N - 1), SIZE)),
    ),
    (
        tuple(r * N for r in range(N)),
        tuple(r * N + N - 1 for r in range(N)),
    ),
)
EDGE_MASKS = ((TOP, BOTTOM), (LEFT, RIGHT))

# A template consists of an endpoint and its two edge carriers.
EDGE_TEMPLATES = (
    (
        tuple((N + c, c, c + 1) for c in range(N - 1)),
        tuple(
            ((N - 2) * N + c, (N - 1) * N + c,
             (N - 1) * N + c - 1)
            for c in range(1, N)
        ),
    ),
    (
        tuple((r * N + 1, r * N, (r + 1) * N)
              for r in range(N - 1)),
        tuple(
            (r * N + N - 2, r * N + N - 1,
             (r - 1) * N + N - 1)
            for r in range(1, N)
        ),
    ),
)

BRIDGE_OFFSETS = (
    (1, 1), (-1, -1),
    (2, -1), (-2, 1),
    (1, -2), (-1, 2),
)

_neighbor_sets = tuple(set(ns) for ns in NEIGHBORS)
_bridges = []
for u in range(SIZE):
    r, c = divmod(u, N)
    for dr, dc in BRIDGE_OFFSETS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            v = rr * N + cc
            if v > u:
                carriers = sorted(_neighbor_sets[u] & _neighbor_sets[v])
                if len(carriers) == 2:
                    _bridges.append((u, v, carriers[0], carriers[1]))
BRIDGES = tuple(_bridges)
del _bridges, _neighbor_sets

SOFT = tuple(math.exp(-x / 6.0) for x in range(401))
HOT = tuple(math.exp(-x / 10.0) for x in range(401))

CENTER = tuple(
    0.065 * (
        1.0 - max(abs(r - 5), abs(c - 5), abs(r + c - 10)) / 10.0
    )
    for r in range(N)
    for c in range(N)
)


class _SearchTimeout(Exception):
    pass


def _spread(bits):
    return (
        ((bits & NOT_RIGHT) << 1)
        | ((bits & NOT_LEFT) >> 1)
        | (bits << N)
        | (bits >> N)
        | ((bits & NOT_LEFT) << (N - 1))
        | ((bits & NOT_RIGHT) >> (N - 1))
    ) & ALL


def _flood(stones, edge):
    reached = stones & edge
    while True:
        enlarged = reached | (_spread(reached) & stones)
        if enlarged == reached:
            return reached
        reached = enlarged


def _winning_cells(stones, other, axis):
    start, finish = EDGE_MASKS[axis]
    empty = ALL & ~(stones | other)
    a = _flood(stones, start)

    # This also provides a legal answer for an already-won input.
    if a & finish:
        return empty

    b = _flood(stones, finish)
    return (
        (_spread(a) | start)
        & (_spread(b) | finish)
        & empty
    )


def _distances(cost, virtual, edge, templates, board):
    distance = [INF] * SIZE
    heap = []
    push = heapq.heappush
    pop = heapq.heappop

    for u in edge:
        d = cost[u]
        if d < distance[u]:
            distance[u] = d
            push(heap, (d, u))

    for u, a, b in templates:
        if board[a] == 0 and board[b] == 0:
            d = cost[u] + 1 + 2 * (board[u] == 0)
            if d < distance[u]:
                distance[u] = d
                push(heap, (d, u))

    neighbors = NEIGHBORS
    while heap:
        du, u = pop(heap)
        if du != distance[u]:
            continue

        for v in neighbors[u]:
            dv = du + cost[v]
            if dv < distance[v]:
                distance[v] = dv
                push(heap, (dv, v))

        for v, penalty in virtual[u]:
            dv = du + cost[v] + penalty
            if dv < distance[v]:
                distance[v] = dv
                push(heap, (dv, v))

    return distance


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[int, int]:
    deadline = time.perf_counter() + 0.86

    # Transposition preserves Hex adjacency and makes us top-to-bottom.
    transpose = color == "w"

    def encode(cell):
        r, c = cell
        return c * N + r if transpose else r * N + c

    def decode(index):
        r, c = divmod(index, N)
        return (c, r) if transpose else (r, c)

    board = [0] * SIZE
    mine = 0
    theirs = 0

    for cell in me:
        i = encode(cell)
        board[i] = 1
        mine |= 1 << i

    for cell in opp:
        i = encode(cell)
        board[i] = -1
        theirs |= 1 << i

    occupied = mine | theirs
    empties = [i for i in range(SIZE) if not (occupied >> i) & 1]

    # No legal move exists on a full board; normal arena states exclude it.
    if not empties:
        return (0, 0)

    fallback = max(empties, key=lambda i: CENTER[i])
    best_move = fallback

    if len(empties) == 1:
        return decode(empties[0])
    if occupied == 0:
        return (5, 5)

    def select_bit(mask):
        candidates = []
        while mask:
            bit = mask & -mask
            candidates.append(bit.bit_length() - 1)
            mask ^= bit
        return max(candidates, key=lambda i: CENTER[i])

    own_wins = _winning_cells(mine, theirs, 0)
    if own_wins:
        return decode(select_bit(own_wins))

    enemy_wins = _winning_cells(theirs, mine, 1)
    if enemy_wins:
        # One threat must be blocked. With multiple immediate threats,
        # no non-winning move can prevent the opponent from winning.
        return decode(select_bit(enemy_wins))

    static_cache = {}
    tactical_cache = {(mine, theirs): (own_wins, enemy_wins)}
    transpositions = {}

    def check_time():
        if time.perf_counter() >= deadline:
            raise _SearchTimeout

    def tactics(mb, ob):
        key = (mb, ob)
        cached = tactical_cache.get(key)
        if cached is None:
            cached = (
                _winning_cells(mb, ob, 0),
                _winning_cells(ob, mb, 1),
            )
            tactical_cache[key] = cached
        return cached

    def analyze(mb, ob):
        key = (mb, ob)
        cached = static_cache.get(key)
        if cached is not None:
            return cached
        check_time()

        virtual = [[] for _ in range(SIZE)]
        bonus_me = [0.0] * SIZE
        bonus_opp = [0.0] * SIZE

        for u, v, a, b in BRIDGES:
            su, sv = board[u], board[v]
            sa, sb = board[a], board[b]

            if sa == 0 and sb == 0:
                if su * sv != -1:
                    penalty = 1 + 2 * (su == 0) + 2 * (sv == 0)
                    virtual[u].append((v, penalty))
                    virtual[v].append((u, penalty))

                if su == 0:
                    if sv == 1:
                        bonus_me[u] += 0.055
                    elif sv == -1:
                        bonus_opp[u] += 0.055

                if sv == 0:
                    if su == 1:
                        bonus_me[v] += 0.055
                    elif su == -1:
                        bonus_opp[v] += 0.055

            elif su != 0 and su == sv:
                repair = -1
                if sa == -su and sb == 0:
                    repair = b
                elif sb == -su and sa == 0:
                    repair = a

                if repair >= 0:
                    if su == 1:
                        bonus_me[repair] += 0.55
                    else:
                        bonus_opp[repair] += 0.55

        for axis, stone, bonuses in (
            (0, 1, bonus_me), (1, -1, bonus_opp)
        ):
            for templates in EDGE_TEMPLATES[axis]:
                for u, a, b in templates:
                    if board[u] == stone:
                        if board[a] == -stone and board[b] == 0:
                            bonuses[b] += 0.50
                        elif board[b] == -stone and board[a] == 0:
                            bonuses[a] += 0.50

        cost_me = [
            0 if x == 1 else 10 if x == 0 else INF
            for x in board
        ]
        cost_opp = [
            0 if x == -1 else 10 if x == 0 else INF
            for x in board
        ]

        mt = _distances(
            cost_me, virtual, EDGE_CELLS[0][0],
            EDGE_TEMPLATES[0][0], board
        )
        mbot = _distances(
            cost_me, virtual, EDGE_CELLS[0][1],
            EDGE_TEMPLATES[0][1], board
        )
        ol = _distances(
            cost_opp, virtual, EDGE_CELLS[1][0],
            EDGE_TEMPLATES[1][0], board
        )
        ore = _distances(
            cost_opp, virtual, EDGE_CELLS[1][1],
            EDGE_TEMPLATES[1][1], board
        )

        through_me = [
            mt[i] + mbot[i] - cost_me[i]
            if mt[i] < INF and mbot[i] < INF else INF
            for i in range(SIZE)
        ]
        through_opp = [
            ol[i] + ore[i] - cost_opp[i]
            if ol[i] < INF and ore[i] < INF else INF
            for i in range(SIZE)
        ]

        dm = min(through_me)
        do = min(through_opp)

        mass_me = 1.0
        mass_opp = 1.0
        ranked_me = []
        ranked_opp = []

        for i in range(SIZE):
            if board[i] != 0:
                continue

            gm = min(400, max(0, through_me[i] - dm))
            go = min(400, max(0, through_opp[i] - do))
            mass_me += SOFT[gm]
            mass_opp += SOFT[go]

            a = HOT[gm]
            b = HOT[go]
            shared = 0.35 * a * b + CENTER[i]

            ranked_me.append((
                1.12 * a + b + shared
                + bonus_me[i] + 0.35 * bonus_opp[i],
                i,
            ))
            ranked_opp.append((
                1.12 * b + a + shared
                + bonus_opp[i] + 0.35 * bonus_me[i],
                i,
            ))

        value = (
            do - dm
            + 1.7 * math.log(mass_me / mass_opp)
            + 180.0 / (dm + 8.0)
            - 180.0 / (do + 8.0)
        )

        ranked_me.sort(reverse=True)
        ranked_opp.sort(reverse=True)

        result = (
            value,
            tuple(i for _, i in ranked_me),
            tuple(i for _, i in ranked_opp),
        )
        static_cache[key] = result
        return result

    widths = (18, 9, 6, 4, 4, 3)

    def search(depth, alpha, beta, side, mb, ob, ply, extensions):
        check_time()

        wm, wo = tactics(mb, ob)
        current_wins, opposing_wins = (wm, wo) if side == 1 else (wo, wm)

        if current_wins:
            return WIN - ply

        if opposing_wins and opposing_wins & (opposing_wins - 1):
            return -WIN + ply + 1

        forced = (
            (opposing_wins & -opposing_wins).bit_length() - 1
            if opposing_wins else -1
        )

        if depth <= 0 and (forced < 0 or extensions <= 0):
            return side * analyze(mb, ob)[0]

        key = (mb, ob, side)
        entry = transpositions.get(key)
        original_alpha = alpha
        original_beta = beta
        hint = -1

        if entry is not None:
            old_depth, old_value, flag, hint = entry
            if depth > 0 and old_depth >= depth:
                if flag == 0:
                    return old_value
                if flag == 1:
                    alpha = max(alpha, old_value)
                else:
                    beta = min(beta, old_value)
                if alpha >= beta:
                    return old_value

        if forced >= 0:
            moves = [forced]
        else:
            info = analyze(mb, ob)
            ordering = info[1] if side == 1 else info[2]
            width = widths[min(ply, len(widths) - 1)]
            moves = list(ordering[:width])
            if hint in moves:
                moves.remove(hint)
                moves.insert(0, hint)

        if not moves:
            return side * analyze(mb, ob)[0]

        best_value = -2 * WIN
        chosen = moves[0]
        next_depth = max(0, depth - 1)
        next_extensions = extensions - (depth <= 0)

        for move in moves:
            bit = 1 << move
            board[move] = side
            try:
                if side == 1:
                    value = -search(
                        next_depth, -beta, -alpha, -side,
                        mb | bit, ob, ply + 1, next_extensions
                    )
                else:
                    value = -search(
                        next_depth, -beta, -alpha, -side,
                        mb, ob | bit, ply + 1, next_extensions
                    )
            finally:
                board[move] = 0

            if value > best_value:
                best_value = value
                chosen = move

            if value > alpha:
                alpha = value
            if alpha >= beta:
                break

        if depth > 0:
            if best_value <= original_alpha:
                flag = -1
            elif best_value >= original_beta:
                flag = 1
            else:
                flag = 0
            transpositions[key] = (depth, best_value, flag, chosen)

        return best_value

    def root_child(move, depth, alpha):
        board[move] = 1
        try:
            return -search(
                depth - 1, -2 * WIN, -alpha, -1,
                mine | (1 << move), theirs, 1, 5
            )
        finally:
            board[move] = 0

    try:
        info = analyze(mine, theirs)
        ordering = list(info[1][:22])
        best_move = ordering[0]

        # Establish a useful completed shallow result first.
        shallow_values = {}
        shallow_best = -2 * WIN
        for move in ordering:
            value = root_child(move, 1, -2 * WIN)
            shallow_values[move] = value
            if value > shallow_best:
                shallow_best = value
                best_move = move

        ordering.sort(key=lambda m: shallow_values[m], reverse=True)

        # Commit only completed deeper iterations.
        for depth, root_width in ((2, 18), (3, 14), (4, 10), (5, 8)):
            check_time()
            candidates = ordering[:root_width]
            values = {}
            iteration_best = candidates[0]
            iteration_value = -2 * WIN
            alpha = -2 * WIN

            for move in candidates:
                value = root_child(move, depth, alpha)
                values[move] = value

                if value > iteration_value:
                    iteration_value = value
                    iteration_best = move
                if value > alpha:
                    alpha = value

            best_move = iteration_best
            candidates.sort(key=lambda m: values[m], reverse=True)
            considered = set(candidates)
            ordering = candidates + [
                m for m in ordering if m not in considered
            ]

            if iteration_value > WIN // 2:
                break

    except _SearchTimeout:
        pass

    if not (0 <= best_move < SIZE) or ((occupied >> best_move) & 1):
        best_move = fallback

    return decode(best_move)
