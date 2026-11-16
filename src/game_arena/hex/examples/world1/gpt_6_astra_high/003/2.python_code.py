
import heapq
import math
import random
import time

_N = 11
_V = _N * _N
_TOTAL = _V + 4
_BITS = tuple(1 << i for i in range(_V))
_INF = 10 ** 9


def _make_tables():
    directions = ((-1, 0), (-1, 1), (0, -1),
                  (0, 1), (1, -1), (1, 0))
    real = []
    for r in range(_N):
        for c in range(_N):
            real.append(tuple(
                rr * _N + cc
                for dr, dc in directions
                for rr, cc in ((r + dr, c + dc),)
                if 0 <= rr < _N and 0 <= cc < _N
            ))

    sides = (
        tuple(range(_N)),
        tuple(range(_V - _N, _V)),
        tuple(r * _N for r in range(_N)),
        tuple(r * _N + _N - 1 for r in range(_N)),
    )

    adj = [list(x) for x in real] + [list(x) for x in sides]
    for k, side in enumerate(sides):
        terminal = _V + k
        for cell in side:
            adj[cell].append(terminal)

    bridges = [[] for _ in range(_TOTAL)]
    edges = []

    def add_bridge(u, v, a, b):
        bridges[u].append((v, a, b))
        bridges[v].append((u, a, b))
        edges.append((u, v, a, b))

    # The three positive orientations of a two-carrier Hex bridge.
    for u in range(_V):
        r, c = divmod(u, _N)
        for dr, dc in ((1, 1), (2, -1), (1, -2)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < _N and 0 <= cc < _N:
                v = rr * _N + cc
                common = [x for x in real[u] if x in real[v]]
                if len(common) == 2:
                    add_bridge(u, v, common[0], common[1])

    # Bridges from a stone to a goal edge.
    for k, side in enumerate(sides):
        side_set = set(side)
        terminal = _V + k
        for u in range(_V):
            if u not in side_set:
                common = [x for x in real[u] if x in side_set]
                if len(common) == 2:
                    add_bridge(u, terminal, common[0], common[1])

    replies = [
        None,
        [[] for _ in range(_V)],
        [[] for _ in range(_V)],
    ]
    for u, v, a, b in edges:
        for player in (1, 2):
            valid = True
            for endpoint in (u, v):
                if endpoint >= _V:
                    owner = 1 if endpoint < _V + 2 else 2
                    if owner != player:
                        valid = False
            if valid:
                replies[player][a].append((u, v, b))
                replies[player][b].append((u, v, a))

    liberties = [
        sum(_BITS[x] for x in real[u])
        for u in range(_V)
    ]
    liberties.extend(sum(_BITS[x] for x in side) for side in sides)

    return (
        tuple(real),
        tuple(tuple(x) for x in adj),
        tuple(tuple(x) for x in bridges),
        tuple(None if x is None else tuple(tuple(y) for y in x)
              for x in replies),
        tuple(liberties),
    )


_REAL, _ADJ, _BRIDGES, _REPLIES, _INITIAL_LIBERTIES = _make_tables()


def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


def _put(board, parent, size, liberties, move, player):
    """Place a stone and update connectivity and component liberties."""
    board[move] = player
    root = move

    for neighbor in _ADJ[move]:
        if board[neighbor] != player:
            continue
        other = _find(parent, neighbor)
        if root == other:
            continue
        if size[root] < size[other]:
            root, other = other, root
        parent[other] = root
        size[root] += size[other]
        liberties[root] |= liberties[other]


def _winning_moves(parent, liberties, player, empty_mask):
    start = _V if player == 1 else _V + 2
    a = _find(parent, start)
    b = _find(parent, start + 1)
    return liberties[a] & liberties[b] & empty_mask


def _repair_bridge(board, parent, player, last):
    if last < 0:
        return -1
    for a, b, repair in _REPLIES[player][last]:
        if (board[repair] == 0 and
                board[a] == player and board[b] == player and
                _find(parent, a) != _find(parent, b)):
            return repair
    return -1


def _distance(board, player, source, target=None):
    """
    Dijkstra distance with ordinary adjacency and discounted virtual bridges.
    Distances are in tenths of a stone.
    """
    enemy = 3 - player
    dist = [_INF] * _TOTAL
    dist[source] = 0
    heap = [(0, source)]
    pop = heapq.heappop
    push = heapq.heappush

    while heap:
        value, u = pop(heap)
        if value != dist[u]:
            continue
        if u == target:
            return value

        for v in _ADJ[u]:
            owner = board[v]
            if owner == enemy:
                continue
            candidate = value + (10 if owner == 0 else 0)
            if candidate < dist[v]:
                dist[v] = candidate
                push(heap, (candidate, v))

        own_u = board[u] == player
        for v, a, b in _BRIDGES[u]:
            if board[a] or board[b]:
                continue
            owner = board[v]
            if owner == enemy:
                continue

            own_v = owner == player
            if own_u and own_v:
                bridge_cost = 1
            elif own_u or own_v:
                bridge_cost = 3
            else:
                bridge_cost = 6

            candidate = value + bridge_cost + (10 if owner == 0 else 0)
            if candidate < dist[v]:
                dist[v] = candidate
                push(heap, (candidate, v))

    return dist if target is None else dist[target]


class _Node:
    __slots__ = ("player", "n", "w", "moves", "children", "rn", "rw")

    def __init__(self, player, moves):
        self.player = player
        self.n = 0
        self.w = 0
        self.moves = moves
        self.children = [None] * _V
        self.rn = [0] * _V
        self.rw = [0] * _V


def _select(node, prior, repair):
    # Progressive widening concentrates early work without permanently
    # excluding lower-ranked legal moves.
    width = min(len(node.moves), 12 + int(2.2 * math.sqrt(node.n + 1)))
    candidates = node.moves[:width]
    if repair >= 0 and repair not in candidates:
        candidates.append(repair)

    exploration = 0.27 * math.sqrt(math.log(node.n + 2))
    best_move = candidates[0]
    best_score = -1e100

    for move in candidates:
        child = node.children[move]
        if child is None:
            visits = 0
            direct = 0.5
        else:
            visits = child.n
            direct = 1.0 - child.w / visits if visits else 0.5

        rave_n = node.rn[move] + 18.0
        rave = (node.rw[move] + 18.0 * prior[move]) / rave_n
        beta = rave_n / (
            rave_n + visits + rave_n * visits / 160.0
        )
        value = (1.0 - beta) * direct + beta * rave
        value += exploration / math.sqrt(visits + 1)
        value += 0.30 * (prior[move] - 0.5) / (1.0 + 0.1 * visits)
        if move == repair:
            value += 0.025 / (1.0 + 0.05 * visits)

        if value > best_score:
            best_score = value
            best_move = move

    return best_move


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[int, int]:
    started = time.perf_counter()
    deadline = started + 0.90
    transpose = color == "w"

    def output(move):
        r, c = divmod(move, _N)
        return (c, r) if transpose else (r, c)

    def index(cell):
        r, c = cell
        if transpose:
            r, c = c, r
        return r * _N + c

    if not me and not opp:
        return (5, 5)

    # Normalize our direction to top-bottom.
    board = [0] * _V + [1, 1, 2, 2]
    parent = list(range(_TOTAL))
    size = [1] * _TOTAL
    liberties = list(_INITIAL_LIBERTIES)

    for cell in me:
        _put(board, parent, size, liberties, index(cell), 1)
    for cell in opp:
        _put(board, parent, size, liberties, index(cell), 2)

    empty = [i for i in range(_V) if board[i] == 0]
    if not empty:
        # A full board is terminal; this branch is outside normal arena calls.
        return (0, 0)
    if len(empty) == 1:
        return output(empty[0])

    empty_mask = sum(_BITS[i] for i in empty)

    winning = _winning_moves(parent, liberties, 1, empty_mask)
    if winning:
        return output((winning & -winning).bit_length() - 1)

    blocking = _winning_moves(parent, liberties, 2, empty_mask)
    if blocking:
        return output((blocking & -blocking).bit_length() - 1)

    # Initial strategic evaluations for both players.
    d1a = _distance(board, 1, _V)
    d1b = _distance(board, 1, _V + 1)
    d2a = _distance(board, 2, _V + 2)
    d2b = _distance(board, 2, _V + 3)
    base1 = d1a[_V + 1]
    base2 = d2a[_V + 3]

    raw = [None, [0.0] * _V, [0.0] * _V]
    roots = [_find(parent, i) for i in range(_TOTAL)]

    for move in empty:
        gap1 = max(0, d1a[move] + d1b[move] - 10 - base1)
        gap2 = max(0, d2a[move] + d2b[move] - 10 - base2)
        heat1 = math.exp(-gap1 / 12.0)
        heat2 = math.exp(-gap2 / 12.0)

        adjacent = [None, set(), set()]
        linked = [None, set(), set()]
        for v in _REAL[move]:
            owner = board[v]
            if owner:
                adjacent[owner].add(roots[v])
        for v, a, b in _BRIDGES[move]:
            owner = board[v]
            if owner and board[a] == 0 and board[b] == 0:
                linked[owner].add(roots[v])

        r, c = divmod(move, _N)
        rr, cc = r - 5, c - 5
        central = math.exp(
            -(rr * rr + cc * cc + 0.5 * (rr + cc) ** 2) / 40.0
        )

        for player, own_heat, other_heat in (
                (1, heat1, heat2), (2, heat2, heat1)):
            linked[player].difference_update(adjacent[player])
            raw[player][move] = (
                1.30 * own_heat
                + 1.05 * other_heat
                + 0.22 * min(2, len(linked[player]))
                + 0.05 * min(2, len(adjacent[player]))
                + 0.13 * central
            )

    # Encourage repairs without assuming the input lists are chronological.
    for attacker in range(_V):
        owner = board[attacker]
        if not owner:
            continue
        defender = 3 - owner
        for a, b, repair in _REPLIES[defender][attacker]:
            if (board[repair] == 0 and
                    board[a] == defender and board[b] == defender and
                    roots[a] != roots[b]):
                raw[defender][repair] += 0.35

    # Refine our prior by actually placing each candidate stone.
    # If the whole pass cannot finish promptly, retain the consistent
    # inexpensive evaluation for every move.
    refined = raw[1][:]
    complete = True
    for move in empty:
        if time.perf_counter() > started + 0.24:
            complete = False
            break
        board[move] = 1
        after1 = _distance(board, 1, _V, _V + 1)
        after2 = _distance(board, 2, _V + 2, _V + 3)
        board[move] = 0
        refined[move] = (
            3.0 * raw[1][move]
            + 0.68 * (base1 - after1)
            + 0.62 * (after2 - base2)
        )
    if complete:
        raw[1] = refined

    priors = [None, [0.5] * _V, [0.5] * _V]
    orders = [None, None, None]
    for player in (1, 2):
        values = [raw[player][i] for i in empty]
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        scale = max(0.10, math.sqrt(variance))
        for move in empty:
            q = 0.5 + 0.105 * (raw[player][move] - mean) / scale
            priors[player][move] = min(0.74, max(0.28, q))
        orders[player] = sorted(
            empty, key=lambda i: raw[player][i], reverse=True
        )

    fallback = orders[1][0]
    root = _Node(1, orders[1])

    seed = 0x9E3779B9
    for i in range(_V):
        if board[i]:
            seed = (seed * 1664525 + (i + 17) * board[i] + 1013904223)
            seed &= 0xFFFFFFFF
    rng = random.Random(seed)

    while time.perf_counter() < deadline:
        b = board[:]
        par = parent[:]
        sz = size[:]
        libs = liberties[:]
        remaining = empty_mask

        permutation = empty[:]
        rng.shuffle(permutation)
        cursor = 0

        turn = 1
        last = -1
        node = root
        trace = [root]
        tree_moves = []
        in_tree = True
        played1 = 0
        played2 = 0

        while True:
            if not remaining:
                winner = (
                    1 if _find(par, _V) == _find(par, _V + 1) else 2
                )
                break

            wins = _winning_moves(par, libs, turn, remaining)
            if wins:
                bit = wins & -wins
                if turn == 1:
                    played1 |= bit
                else:
                    played2 |= bit
                winner = turn
                break

            threats = _winning_moves(par, libs, 3 - turn, remaining)
            if threats and (threats & (threats - 1)):
                # Two distinct immediate winning cells cannot both be blocked.
                winner = 3 - turn
                break

            forced = (
                (threats & -threats).bit_length() - 1
                if threats else -1
            )
            repair = -1
            if forced < 0 and last >= 0:
                repair = _repair_bridge(b, par, turn, last)

            if in_tree:
                move = (
                    forced if forced >= 0
                    else _select(node, priors[turn], repair)
                )
            elif forced >= 0:
                move = forced
            elif repair >= 0:
                move = repair
            else:
                while b[permutation[cursor]] != 0:
                    cursor += 1
                move = permutation[cursor]
                cursor += 1

            bit = _BITS[move]
            remaining ^= bit
            if turn == 1:
                played1 |= bit
            else:
                played2 |= bit

            _put(b, par, sz, libs, move, turn)

            if in_tree:
                child = node.children[move]
                if child is None:
                    next_player = 3 - turn
                    child = _Node(
                        next_player,
                        [i for i in orders[next_player] if b[i] == 0],
                    )
                    node.children[move] = child
                    in_tree = False
                tree_moves.append(move)
                trace.append(child)
                node = child

            last = move
            turn = 3 - turn

        # RAVE updates use only moves occurring after the respective node.
        mask1, mask2 = played1, played2
        for depth, visited in enumerate(trace):
            won = int(winner == visited.player)
            visited.n += 1
            visited.w += won

            mask = mask1 if visited.player == 1 else mask2
            counts = visited.rn
            successes = visited.rw
            if won:
                while mask:
                    bit = mask & -mask
                    move = bit.bit_length() - 1
                    counts[move] += 1
                    successes[move] += 1
                    mask ^= bit
            else:
                while mask:
                    bit = mask & -mask
                    counts[bit.bit_length() - 1] += 1
                    mask ^= bit

            if depth < len(tree_moves):
                bit = _BITS[tree_moves[depth]]
                if visited.player == 1:
                    mask1 ^= bit
                else:
                    mask2 ^= bit

    chosen = fallback
    best_key = (-1, -1.0, -1.0)
    for move in empty:
        child = root.children[move]
        if child is not None and child.n:
            key = (
                child.n,
                1.0 - child.w / child.n,
                priors[1][move],
            )
            if key > best_key:
                best_key = key
                chosen = move

    # All root candidates were generated from the original empty cells.
    if board[chosen] != 0:
        chosen = empty[0]
    return output(chosen)
