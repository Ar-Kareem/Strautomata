
from collections import deque
from math import log, sqrt
from time import perf_counter
import random


SIZE = 11
CELLS = SIZE * SIZE
FULL = (1 << CELLS) - 1
INF = 10 ** 9

TOP = sum(1 << c for c in range(SIZE))
BOTTOM = sum(1 << ((SIZE - 1) * SIZE + c) for c in range(SIZE))
LEFT = sum(1 << (r * SIZE) for r in range(SIZE))
RIGHT = sum(1 << (r * SIZE + SIZE - 1) for r in range(SIZE))

NEIGH = [0] * CELLS
NEIGH_LIST = [[] for _ in range(CELLS)]

for r in range(SIZE):
    for c in range(SIZE):
        i = r * SIZE + c
        for dr, dc in (
            (0, -1), (0, 1),
            (-1, 0), (-1, 1),
            (1, 0), (1, -1)
        ):
            nr, nc = r + dr, c + dc
            if 0 <= nr < SIZE and 0 <= nc < SIZE:
                j = nr * SIZE + nc
                NEIGH[i] |= 1 << j
                NEIGH_LIST[i].append(j)


def _bits_from_moves(moves):
    bits = 0
    for r, c in moves:
        if 0 <= r < SIZE and 0 <= c < SIZE:
            bits |= 1 << (r * SIZE + c)
    return bits


def _has_win(stones, vertical):
    if vertical:
        reached = stones & TOP
        target = BOTTOM
    else:
        reached = stones & LEFT
        target = RIGHT

    if not reached:
        return False

    while True:
        expanded = (
            ((reached << 1) & FULL & ~LEFT)
            | ((reached >> 1) & ~RIGHT)
            | ((reached << SIZE) & FULL)
            | (reached >> SIZE)
            | ((reached >> (SIZE - 1)) & ~LEFT)
            | ((reached << (SIZE - 1)) & FULL & ~RIGHT)
        )
        new_reached = reached | (expanded & stones)
        if new_reached == reached:
            break
        reached = new_reached

    return bool(reached & target)


def _iter_empty_indices(occupied):
    mask = FULL & ~occupied
    result = []
    while mask:
        b = mask & -mask
        result.append(b.bit_length() - 1)
        mask ^= b
    return result


def _goal_cells(vertical, first):
    if vertical:
        row = 0 if first else SIZE - 1
        return [row * SIZE + c for c in range(SIZE)]
    col = 0 if first else SIZE - 1
    return [r * SIZE + col for r in range(SIZE)]


def _distance_from_goal(own, enemy, vertical, first):
    dist = [INF] * CELLS
    q = deque()

    for i in _goal_cells(vertical, first):
        bit = 1 << i
        if enemy & bit:
            continue
        cost = 0 if own & bit else 1
        if cost < dist[i]:
            dist[i] = cost
            if cost == 0:
                q.appendleft(i)
            else:
                q.append(i)

    while q:
        u = q.popleft()
        du = dist[u]
        for v in NEIGH_LIST[u]:
            bit = 1 << v
            if enemy & bit:
                continue
            cost = 0 if own & bit else 1
            nd = du + cost
            if nd < dist[v]:
                dist[v] = nd
                if cost == 0:
                    q.appendleft(v)
                else:
                    q.append(v)

    return dist


def _path_information(own, enemy, vertical):
    da = _distance_from_goal(own, enemy, vertical, True)
    db = _distance_from_goal(own, enemy, vertical, False)
    goal = _goal_cells(vertical, False)
    best = min((da[i] for i in goal), default=INF)
    return da, db, best


def _broken_bridges(own, enemy):
    stones = []
    mask = own
    while mask:
        b = mask & -mask
        stones.append(b.bit_length() - 1)
        mask ^= b

    responses = set()
    potentials = set()

    for a_pos in range(len(stones)):
        a = stones[a_pos]
        for b_pos in range(a_pos + 1, len(stones)):
            b = stones[b_pos]

            if NEIGH[a] & (1 << b):
                continue

            common = NEIGH[a] & NEIGH[b]
            if common.bit_count() != 2:
                continue

            enemy_common = common & enemy
            empty_common = common & ~(own | enemy)

            if enemy_common.bit_count() == 1 and empty_common.bit_count() == 1:
                responses.add((empty_common & -empty_common).bit_length() - 1)
            elif empty_common.bit_count() == 2:
                t = empty_common
                while t:
                    x = t & -t
                    potentials.add(x.bit_length() - 1)
                    t ^= x

    return responses, potentials


def _edge_bridge_responses(own, enemy, vertical):
    responses = set()
    mask = own

    while mask:
        b = mask & -mask
        i = b.bit_length() - 1
        mask ^= b
        r, c = divmod(i, SIZE)

        pairs = []

        if vertical:
            if r == 1:
                pairs.append((c, c + 1))
            if r == SIZE - 2:
                pairs.append(((SIZE - 1) * SIZE + c,
                              (SIZE - 1) * SIZE + c - 1))
        else:
            if c == 1:
                pairs.append((r * SIZE, (r + 1) * SIZE))
            if c == SIZE - 2:
                pairs.append((r * SIZE + SIZE - 1,
                              (r - 1) * SIZE + SIZE - 1))

        for a, d in pairs:
            if not (0 <= a < CELLS and 0 <= d < CELLS):
                continue
            pair_bits = (1 << a) | (1 << d)
            enemy_part = pair_bits & enemy
            empty_part = pair_bits & ~(own | enemy)
            if enemy_part.bit_count() == 1 and empty_part.bit_count() == 1:
                responses.add((empty_part & -empty_part).bit_length() - 1)

    return responses


def _make_priorities(me_bits, opp_bits, my_vertical):
    occupied = me_bits | opp_bits
    empties = _iter_empty_indices(occupied)

    my_a, my_b, my_best = _path_information(
        me_bits, opp_bits, my_vertical
    )
    op_a, op_b, op_best = _path_information(
        opp_bits, me_bits, not my_vertical
    )

    my_broken, my_bridge_cells = _broken_bridges(me_bits, opp_bits)
    op_broken, op_bridge_cells = _broken_bridges(opp_bits, me_bits)

    my_edge = _edge_bridge_responses(me_bits, opp_bits, my_vertical)
    op_edge = _edge_bridge_responses(opp_bits, me_bits, not my_vertical)

    my_prior = [-1000.0] * CELLS
    op_prior = [-1000.0] * CELLS

    for i in empties:
        bit = 1 << i
        r, c = divmod(i, SIZE)

        my_through = INF
        if my_a[i] < INF and my_b[i] < INF:
            my_through = my_a[i] + my_b[i] - 1

        op_through = INF
        if op_a[i] < INF and op_b[i] < INF:
            op_through = op_a[i] + op_b[i] - 1

        if my_through < INF and my_best < INF:
            my_attack = 8.0 / (1.0 + max(0, my_through - my_best))
        else:
            my_attack = 0.0

        if op_through < INF and op_best < INF:
            my_defense = 7.0 / (1.0 + max(0, op_through - op_best))
        else:
            my_defense = 0.0

        my_adj = (NEIGH[i] & me_bits).bit_count()
        op_adj = (NEIGH[i] & opp_bits).bit_count()

        center = 1.0 - (abs(r - 5) + abs(c - 5)) / 10.0

        score = (
            my_attack
            + 0.88 * my_defense
            + 0.58 * my_adj
            + 0.20 * op_adj
            + 0.40 * center
        )

        if i in my_broken:
            score += 10.0
        if i in my_edge:
            score += 8.0
        if i in my_bridge_cells:
            score += 1.4
        if i in op_broken or i in op_edge:
            score += 1.2

        # Reward moves which form new two-cell bridges.
        bridge_count = 0
        m = me_bits
        while m and bridge_count < 3:
            x = m & -m
            j = x.bit_length() - 1
            m ^= x
            if not (NEIGH[i] & bit & (1 << j)) and not (NEIGH[i] & (1 << j)):
                if (NEIGH[i] & NEIGH[j]).bit_count() == 2:
                    bridge_count += 1
        score += 0.62 * bridge_count

        my_prior[i] = score

        # Same calculation from the opponent's point of view.
        op_attack = my_defense
        op_defense = my_attack
        score2 = (
            op_attack
            + 0.88 * op_defense
            + 0.58 * op_adj
            + 0.20 * my_adj
            + 0.40 * center
        )

        if i in op_broken:
            score2 += 10.0
        if i in op_edge:
            score2 += 8.0
        if i in op_bridge_cells:
            score2 += 1.4
        if i in my_broken or i in my_edge:
            score2 += 1.2

        bridge_count = 0
        m = opp_bits
        while m and bridge_count < 3:
            x = m & -m
            j = x.bit_length() - 1
            m ^= x
            if not (NEIGH[i] & (1 << j)):
                if (NEIGH[i] & NEIGH[j]).bit_count() == 2:
                    bridge_count += 1
        score2 += 0.62 * bridge_count

        op_prior[i] = score2

    return my_prior, op_prior


class _Node:
    __slots__ = (
        "me_bits", "opp_bits", "turn", "move",
        "children", "untried", "n", "w",
        "amaf_n", "amaf_w", "terminal"
    )

    def __init__(self, me_bits, opp_bits, turn, move=-1):
        self.me_bits = me_bits
        self.opp_bits = opp_bits
        self.turn = turn       # 0: root player, 1: opponent
        self.move = move
        self.children = []
        self.untried = None
        self.n = 0
        self.w = 0.0           # Root-player wins
        self.amaf_n = {}
        self.amaf_w = {}
        self.terminal = -1     # -1 unknown, 0 root loss, 1 root win


def _initialize_untried(node, root_prior, opp_prior, rng):
    occupied = node.me_bits | node.opp_bits
    candidates = _iter_empty_indices(occupied)
    prior = root_prior if node.turn == 0 else opp_prior
    candidates.sort(key=lambda x: prior[x] + 0.30 * rng.random())
    node.untried = candidates


def _select_child(node, rng):
    log_parent = log(node.n + 1.0)
    mover_is_root = node.turn == 0
    best_child = None
    best_score = -1e100

    for child in node.children:
        if child.n == 0:
            return child

        q = child.w / child.n
        if not mover_is_root:
            q = 1.0 - q

        rn = node.amaf_n.get(child.move, 0)
        if rn:
            rq = node.amaf_w.get(child.move, 0.0) / rn
            if not mover_is_root:
                rq = 1.0 - rq

            beta = rn / (
                rn + child.n
                + (4.0 * rn * child.n) / 400.0
            )
            value = (1.0 - beta) * q + beta * rq
        else:
            value = q

        exploration = 0.54 * sqrt(log_parent / child.n)
        score = value + exploration + rng.random() * 1e-8

        if score > best_score:
            best_score = score
            best_child = child

    return best_child


def _run_mcts(me_bits, opp_bits, my_vertical,
              root_prior, opp_prior, deadline, rng):
    root = _Node(me_bits, opp_bits, 0)

    while perf_counter() < deadline:
        node = root
        path = [root]
        offsets = [0]
        sequence = []

        # Tree selection and progressive widening.
        while node.terminal < 0:
            if node.untried is None:
                _initialize_untried(node, root_prior, opp_prior, rng)

            widening_limit = 4 + int(1.65 * sqrt(node.n + 1))

            if node.untried and len(node.children) < widening_limit:
                move = node.untried.pop()
                bit = 1 << move
                actor = node.turn
                sequence.append((move, actor))

                if actor == 0:
                    new_me = node.me_bits | bit
                    new_opp = node.opp_bits
                else:
                    new_me = node.me_bits
                    new_opp = node.opp_bits | bit

                child = _Node(new_me, new_opp, 1 - actor, move)

                if actor == 0 and _has_win(new_me, my_vertical):
                    child.terminal = 1
                elif actor == 1 and _has_win(new_opp, not my_vertical):
                    child.terminal = 0

                node.children.append(child)
                node = child
                path.append(node)
                offsets.append(len(sequence))
                break

            if node.children:
                child = _select_child(node, rng)
                if child is None:
                    break
                sequence.append((child.move, node.turn))
                node = child
                path.append(node)
                offsets.append(len(sequence))
                continue

            # No legal moves remain.
            node.terminal = 1 if _has_win(node.me_bits, my_vertical) else 0
            break

        if node.terminal >= 0:
            result = float(node.terminal)
        else:
            # Uniform random completion. On a full Hex board exactly one
            # player has a connection, so intermediate terminal checks are
            # unnecessary.
            p = node.me_bits
            o = node.opp_bits
            rollout = _iter_empty_indices(p | o)
            rng.shuffle(rollout)
            actor = node.turn

            for move in rollout:
                sequence.append((move, actor))
                if actor == 0:
                    p |= 1 << move
                else:
                    o |= 1 << move
                actor ^= 1

            result = 1.0 if _has_win(p, my_vertical) else 0.0

        # Standard and all-moves-as-first (RAVE/AMAF) backup.
        for nd, offset in zip(path, offsets):
            nd.n += 1
            nd.w += result

            actor = nd.turn
            amaf_n = nd.amaf_n
            amaf_w = nd.amaf_w

            for move, move_actor in sequence[offset:]:
                if move_actor == actor:
                    amaf_n[move] = amaf_n.get(move, 0) + 1
                    amaf_w[move] = amaf_w.get(move, 0.0) + result

    if not root.children:
        return None

    # Robust-child selection, with value as a tie breaker.
    best = max(
        root.children,
        key=lambda child: (
            child.n,
            child.w / child.n if child.n else 0.0,
            root_prior[child.move]
        )
    )
    return best.move


def policy(me: list[tuple[int, int]],
           opp: list[tuple[int, int]],
           color: str) -> tuple[int, int]:
    start = perf_counter()

    me_bits = _bits_from_moves(me)
    opp_bits = _bits_from_moves(opp)
    occupied = me_bits | opp_bits
    empties = _iter_empty_indices(occupied)

    # A legal game state presented to a player always has an empty cell.
    # This fallback also protects against malformed input.
    if not empties:
        return (0, 0)

    fallback = empties[0]
    my_vertical = color == "b"

    # Strong central opening.
    if occupied == 0:
        return (5, 5)

    # Always take an immediate win.
    winning_moves = []
    for i in empties:
        if _has_win(me_bits | (1 << i), my_vertical):
            winning_moves.append(i)

    if winning_moves:
        i = min(
            winning_moves,
            key=lambda x: abs(x // SIZE - 5) + abs(x % SIZE - 5)
        )
        return divmod(i, SIZE)

    # Always stop an immediate opponent win.
    opponent_wins = []
    for i in empties:
        if _has_win(opp_bits | (1 << i), not my_vertical):
            opponent_wins.append(i)

    if opponent_wins:
        i = min(
            opponent_wins,
            key=lambda x: abs(x // SIZE - 5) + abs(x % SIZE - 5)
        )
        return divmod(i, SIZE)

    try:
        root_prior, opp_prior = _make_priorities(
            me_bits, opp_bits, my_vertical
        )

        seed = 1469598103934665603
        seed ^= me_bits + 0x9E3779B97F4A7C15
        seed *= 1099511628211
        seed ^= (opp_bits << 1)
        seed *= 1099511628211
        seed ^= 1 if my_vertical else 2
        rng = random.Random(seed & ((1 << 64) - 1))

        # Leave margin beneath the one-second arena limit.
        deadline = start + 0.88
        move = _run_mcts(
            me_bits,
            opp_bits,
            my_vertical,
            root_prior,
            opp_prior,
            deadline,
            rng
        )

        if move is None or (occupied & (1 << move)):
            move = max(empties, key=lambda x: root_prior[x])

        if 0 <= move < CELLS and not (occupied & (1 << move)):
            return divmod(move, SIZE)

    except Exception:
        # The policy must never lose legality because of a search failure.
        pass

    return divmod(fallback, SIZE)
