
import math
import time
import hashlib
from collections import deque


SIZE = 19
AREA = SIZE * SIZE

NEIGHBORS = []
DIAGONALS = []
EDGE_LINE = []
KERNEL = []

for p in range(AREA):
    r, c = divmod(p, SIZE)
    ns = []
    ds = []
    for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < SIZE and 0 <= cc < SIZE:
            ns.append(rr * SIZE + cc)
    for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
        rr, cc = r + dr, c + dc
        if 0 <= rr < SIZE and 0 <= cc < SIZE:
            ds.append(rr * SIZE + cc)

    NEIGHBORS.append(tuple(ns))
    DIAGONALS.append(tuple(ds))
    EDGE_LINE.append(min(r + 1, c + 1, SIZE - r, SIZE - c))

    kernel = []
    for dr in range(-5, 6):
        for dc in range(-5, 6):
            d = abs(dr) + abs(dc)
            rr, cc = r + dr, c + dc
            if d <= 5 and 0 <= rr < SIZE and 0 <= cc < SIZE:
                kernel.append((rr * SIZE + cc, math.exp(-0.55 * d)))
    z = sum(w for _, w in kernel)
    KERNEL.append(tuple((q, w / z) for q, w in kernel))

NEIGHBORS = tuple(NEIGHBORS)
DIAGONALS = tuple(DIAGONALS)
EDGE_LINE = tuple(EDGE_LINE)
KERNEL = tuple(KERNEL)


def _signature(board):
    return hashlib.blake2b(bytes(board), digest_size=12).hexdigest()


def _analyse(board):
    """Return point-to-group indices and (color, stones, liberties) groups."""
    ids = [-1] * AREA
    groups = []

    for start in range(AREA):
        color = board[start]
        if not color or ids[start] != -1:
            continue

        gid = len(groups)
        ids[start] = gid
        stack = [start]
        stones = []
        liberties = set()

        while stack:
            p = stack.pop()
            stones.append(p)
            for q in NEIGHBORS[p]:
                v = board[q]
                if not v:
                    liberties.add(q)
                elif v == color and ids[q] == -1:
                    ids[q] = gid
                    stack.append(q)

        groups.append((color, tuple(stones), frozenset(liberties)))

    return ids, groups


def _play(board, ids, groups, p, color):
    """Play without suicide. Ko is checked separately."""
    if board[p]:
        return None

    enemy = 3 - color
    captured_groups = set()
    has_liberty = False

    for q in NEIGHBORS[p]:
        value = board[q]
        if value == 0:
            has_liberty = True
        elif value == color:
            if len(groups[ids[q]][2]) > 1:
                has_liberty = True
        elif value == enemy:
            gid = ids[q]
            if len(groups[gid][2]) == 1:
                captured_groups.add(gid)

    if not has_liberty and not captured_groups:
        return None

    result = bytearray(board)
    result[p] = color
    captured = 0
    for gid in captured_groups:
        stones = groups[gid][1]
        captured += len(stones)
        for q in stones:
            result[q] = 0

    return result, captured


def _eye(board, p, color, strict=True):
    if board[p] or any(board[q] != color for q in NEIGHBORS[p]):
        return False

    diagonals = DIAGONALS[p]
    allowance = 1 if len(diagonals) == 4 else 0

    if strict:
        bad = sum(board[q] != color for q in diagonals)
    else:
        bad = sum(board[q] == 3 - color for q in diagonals)

    return bad <= allowance


def _alive(board, group):
    color, _, liberties = group
    if not 2 <= len(liberties) <= 3:
        return False
    eyes = 0
    for p in liberties:
        if _eye(board, p, color, True):
            eyes += 1
            if eyes >= 2:
                return True
    return False


def _cheap_risk(color, size, liberties, alive=False):
    if alive or liberties >= 4:
        return 0.0
    if liberties <= 0:
        return float(size)

    if color == 1:
        probability = (0.0, 1.0, 0.24, 0.045)[liberties]
        return size * probability

    pressure = (0.0, 0.20, 0.07, 0.012)[liberties]
    return math.sqrt(size) * pressure


def _distances(board, color):
    distances = [99] * AREA
    queue = deque()

    for p, value in enumerate(board):
        if value == color:
            distances[p] = 0
            queue.append(p)

    while queue:
        p = queue.popleft()
        nd = distances[p] + 1
        for q in NEIGHBORS[p]:
            if nd < distances[q]:
                distances[q] = nd
                queue.append(q)

    return distances


class _Reader:
    """Small local capture search; -1 means unresolved, 0 escape, 1 capture."""

    def __init__(self, deadline, max_nodes=2300):
        self.deadline = deadline
        self.max_nodes = max_nodes
        self.nodes = 0
        self.memo = {}

    def exhausted(self):
        return self.nodes >= self.max_nodes or time.perf_counter() >= self.deadline

    def solve(self, board, ids, groups, anchor, attacker, turn,
              depth, previous, allowance):
        limit = min(self.max_nodes, self.nodes + allowance)
        return self._search(
            board, ids, groups, anchor, attacker, turn,
            depth, previous, limit
        )

    def _search(self, board, ids, groups, anchor, attacker, turn,
                depth, previous, limit):
        defender = 3 - attacker

        if board[anchor] != defender:
            return 1

        group = groups[ids[anchor]]
        liberties = group[2]
        nl = len(liberties)

        if nl >= 4 or _alive(board, group):
            return 0

        if self.nodes >= limit or time.perf_counter() >= self.deadline:
            return -1

        self.nodes += 1
        state = bytes(board)
        key = (state, anchor, attacker, turn, depth, previous)
        cached = self.memo.get(key)
        if cached is not None:
            return cached

        # An immediate legal capture is conclusive, including at the horizon.
        if turn == attacker and nl == 1:
            p = next(iter(liberties))
            played = _play(board, ids, groups, p, attacker)
            if played is not None:
                nb, _ = played
                if bytes(nb) == previous:
                    return -1
                if nb[anchor] != defender:
                    self.memo[key] = 1
                    return 1
            return -1

        if depth <= 0:
            return -1

        moves = set(liberties)
        adjacent_attackers = set()

        for s in group[1]:
            for q in NEIGHBORS[s]:
                if board[q] == attacker:
                    adjacent_attackers.add(ids[q])

        for gid in adjacent_attackers:
            ag = groups[gid]
            al = len(ag[2])
            if al == 1:
                moves.update(ag[2])
            elif turn == defender and nl <= 2 and al == 2:
                # Counter-atari can be the only effective defense.
                moves.update(ag[2])

        def move_order(p):
            empty = sum(board[q] == 0 for q in NEIGHBORS[p])
            support = sum(board[q] == turn for q in NEIGHBORS[p])
            capture = 0
            seen = set()
            for q in NEIGHBORS[p]:
                if board[q] == 3 - turn:
                    gid = ids[q]
                    if gid not in seen and len(groups[gid][2]) == 1:
                        seen.add(gid)
                        capture += len(groups[gid][1])
            if turn == defender:
                return -(empty + 0.6 * support + 3.0 * capture)
            return empty - 0.5 * support - 3.0 * capture

        ordered = sorted(moves, key=move_order)
        unknown = len(ordered) > 10
        ordered = ordered[:10]
        legal_count = 0

        for p in ordered:
            played = _play(board, ids, groups, p, turn)
            if played is None:
                continue

            nb, _ = played
            if bytes(nb) == previous:
                unknown = True
                continue

            legal_count += 1
            ni, ng = _analyse(nb)
            outcome = self._search(
                nb, ni, ng, anchor, attacker, 3 - turn,
                depth - 1, state, limit
            )

            if turn == attacker and outcome == 1:
                self.memo[key] = 1
                return 1
            if turn == defender and outcome == 0:
                self.memo[key] = 0
                return 0
            if outcome == -1:
                unknown = True

        if unknown:
            return -1

        result = 0 if turn == attacker else 1
        if legal_count == 0:
            result = 0 if turn == attacker else 1

        self.memo[key] = result
        return result


def _policy(me, opponent, memory):
    start = time.perf_counter()
    deadline = start + 0.88

    board = bytearray(AREA)
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + c - 1] = 2

    history = list(memory.get("_go_history", []))
    seen_positions = set(history)
    current_signature = _signature(board)
    if current_signature not in seen_positions:
        history.append(current_signature)
        seen_positions.add(current_signature)

    def finish(p=None, after=None):
        if p is None:
            action = (0, 0)
        else:
            action = (p // SIZE + 1, p % SIZE + 1)
            signature = _signature(after)
            if signature not in seen_positions:
                history.append(signature)
                seen_positions.add(signature)

        memory["_go_history"] = history[-2048:]
        return action, memory

    ids, groups = _analyse(board)
    empty_points = [p for p in range(AREA) if not board[p]]
    if not empty_points:
        return finish()

    occupied = AREA - len(empty_points)
    phase = min(1.0, occupied / 130.0)
    own_distance = _distances(board, 1)
    enemy_distance = _distances(board, 2)

    # Diffuse influence through empty intersections, keeping stones fixed.
    influence = [
        1.0 if v == 1 else -1.0 if v == 2 else 0.0
        for v in board
    ]
    for _ in range(24):
        updated = influence[:]
        for p in empty_points:
            ns = NEIGHBORS[p]
            updated[p] = 0.94 * sum(influence[q] for q in ns) / len(ns)
        influence = updated

    uncertainty = [
        0.0 if board[p] else 1.0 - abs(math.tanh(2.3 * influence[p]))
        for p in range(AREA)
    ]
    expansion = [0.0] * AREA
    for p in empty_points:
        expansion[p] = sum(uncertainty[q] * w for q, w in KERNEL[p])

    alive = [_alive(board, g) for g in groups]
    cheap = [
        _cheap_risk(g[0], len(g[1]), len(g[2]), alive[i])
        for i, g in enumerate(groups)
    ]

    book = [0.0] * AREA
    if occupied < 90:
        opening_scale = max(0.0, 1.0 - occupied / 100.0)
        for rr, cc in ((3, 3), (3, 15), (15, 3), (15, 15)):
            corner = rr * SIZE + cc
            if min(own_distance[corner], enemy_distance[corner]) >= 6:
                book[corner] += 3.7 * opening_scale

            # Low approaches and small enclosures around a 4-4 stone.
            if board[corner]:
                sr = 1 if rr == 3 else -1
                sc = 1 if cc == 3 else -1
                for dr, dc in ((-1, 2), (2, -1)):
                    ar, ac = rr + sr * dr, cc + sc * dc
                    p = ar * SIZE + ac
                    if not board[p]:
                        bonus = 1.1 if board[corner] == 2 else 0.85
                        book[p] += bonus * opening_scale

        for r, c in ((3, 9), (9, 3), (15, 9), (9, 15)):
            p = r * SIZE + c
            if min(own_distance[p], enemy_distance[p]) >= 4:
                book[p] += 0.55 * opening_scale

    line_values = (0.0, -2.8, -1.1, 0.7, 1.1, 0.55,
                   0.15, -0.15, -0.3, -0.4, -0.4)
    proximity = {1: -0.70, 2: 0.10, 3: 0.50, 4: 0.65,
                 5: 0.45, 6: 0.15, 7: 0.0}

    candidates = []

    for p in empty_points:
        friendly = set()
        enemy = set()
        immediate = set()
        own_adj = 0
        enemy_adj = 0

        for q in NEIGHBORS[p]:
            if board[q] == 1:
                friendly.add(ids[q])
                own_adj += 1
            elif board[q] == 2:
                enemy.add(ids[q])
                enemy_adj += 1
            else:
                immediate.add(q)

        captured_groups = {g for g in enemy if len(groups[g][2]) == 1}
        liberties = set(immediate)
        new_size = 1
        for gid in friendly:
            new_size += len(groups[gid][1])
            liberties.update(groups[gid][2])
        liberties.discard(p)

        captured = 0
        extra_liberties = {}
        for gid in captured_groups:
            captured += len(groups[gid][1])
            for s in groups[gid][1]:
                touches_new_group = False
                for q in NEIGHBORS[s]:
                    if q == p:
                        touches_new_group = True
                    elif board[q] == 1:
                        fg = ids[q]
                        if fg in friendly:
                            touches_new_group = True
                        else:
                            extra_liberties.setdefault(fg, set()).add(s)
                if touches_new_group:
                    liberties.add(s)

        if not liberties:
            continue

        preserved_life = (
            any(alive[g] for g in friendly)
            and not _eye(board, p, 1, False)
        )
        own_delta = sum(cheap[g] for g in friendly)
        own_delta -= _cheap_risk(1, new_size, len(liberties), preserved_life)

        for gid, additions in extra_liberties.items():
            group = groups[gid]
            nl = len(group[2] | additions)
            own_delta += cheap[gid] - _cheap_risk(
                1, len(group[1]), nl, alive[gid]
            )

        enemy_delta = 0.0
        for gid in enemy:
            group = groups[gid]
            enemy_delta -= cheap[gid]
            if gid not in captured_groups:
                enemy_delta += _cheap_risk(
                    2, len(group[1]), len(group[2]) - 1, alive[gid]
                )

        d_own = own_distance[p]
        d_enemy = enemy_distance[p]
        field = influence[p]

        positional = 2.8 * expansion[p]
        positional += line_values[EDGE_LINE[p]] * (1.0 - 0.8 * phase)
        positional += proximity.get(d_own, -0.25) * (1.0 - 0.45 * phase)
        positional += book[p]

        if d_enemy == 1:
            positional -= 0.8
            if d_own >= 3:
                positional -= 1.5
        elif d_enemy == 2:
            positional -= 0.05
            if d_own >= 5:
                positional -= 0.6
        elif d_enemy == 3:
            positional += 0.35
        elif d_enemy == 4:
            positional += 0.20

        if field < -0.30 and d_own > 2:
            positional -= 2.8 * (-field - 0.30)
            if d_own >= 5:
                positional -= 0.6
        if field > 0.55:
            positional -= 2.0 * (field - 0.55)

        if own_adj and enemy_adj:
            positional += 1.05 + 0.45 * phase
        elif d_own <= 2 and d_enemy <= 2:
            positional += 0.35 * phase

        if len(friendly) >= 2:
            positional += 0.85 * min(2, len(friendly) - 1)
        elif own_adj >= 2:
            positional -= 0.4 * (own_adj - 1)

        if len(enemy) >= 2:
            positional += 0.8 if d_own <= 2 else -0.7

        if not own_adj:
            positional += 0.1 * min(
                2, sum(board[q] == 1 for q in DIAGONALS[p])
            )

        # Empty triangles generally waste a move unless tactically required.
        r, c = divmod(p, SIZE)
        triangles = 0
        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE:
                if (board[rr * SIZE + c] == 1
                        and board[r * SIZE + cc] == 1
                        and board[rr * SIZE + cc] == 1):
                    triangles += 1
        positional -= 0.35 * triangles

        if own_adj == len(NEIGHBORS[p]) and not captured:
            if _eye(board, p, 1, False):
                positional -= 9.0 if len(friendly) == 1 else 2.5
            else:
                positional -= 1.4

        raw = positional + 5.5 * (captured + own_delta + enemy_delta)
        candidates.append((raw, p, positional))

    if not candidates:
        return finish()

    candidates.sort(reverse=True, key=lambda x: (x[0], -x[1]))

    reader = _Reader(deadline)
    risk_cache = {}
    initial_bytes = bytes(board)

    def assessed_risk(b, gi, gs, group_index):
        group = gs[group_index]
        color, stones, liberties = group
        nl = len(liberties)
        size = len(stones)

        if nl >= 4 or _alive(b, group):
            return 0.0

        basic = _cheap_risk(color, size, nl)
        if nl >= 3:
            return basic

        # Reuse tactical results when the chain and its local surroundings
        # have not changed between candidate moves.
        ring = set(liberties)
        for q in liberties:
            ring.update(NEIGHBORS[q])
        ring_tuple = tuple(sorted(ring))
        key = (
            color,
            tuple(sorted(stones)),
            tuple(sorted(liberties)),
            bytes(b[q] for q in ring_tuple),
        )
        cached = risk_cache.get(key)
        if cached is not None:
            return cached

        if reader.exhausted():
            return basic

        attacker = 2 if color == 1 else 1
        allowance = 170 if color == 1 else 120
        outcome = reader.solve(
            b, gi, gs, stones[0], attacker, 2,
            30 if color == 1 else 24,
            initial_bytes, allowance
        )

        if outcome == 1:
            risk = float(size) if color == 1 else 0.70 * size
        elif outcome == 0:
            if color == 1:
                risk = 0.02 * size
            else:
                risk = (0.08 if nl == 1 else 0.025) * math.sqrt(size)
        else:
            risk = basic

        # Unknown results remain conservative but can also be reused.
        risk_cache[key] = risk
        return risk

    def assess_position(b, gi, gs):
        own_risk = 0.0
        enemy_risk = 0.0

        # Read urgent, large friendly chains first.
        order = sorted(
            range(len(gs)),
            key=lambda g: (
                len(gs[g][2]),
                0 if gs[g][0] == 1 else 1,
                -len(gs[g][1]),
            )
        )
        for gid in order:
            group = gs[gid]
            risk = assessed_risk(b, gi, gs, gid)
            if group[0] == 1:
                own_risk += risk
            else:
                enemy_risk += risk
        return own_risk, enemy_risk

    baseline_own, baseline_enemy = assess_position(board, ids, groups)

    best_score = -float("inf")
    best_point = None
    best_board = None
    evaluated = 0

    for raw, p, positional in candidates:
        if evaluated >= 18:
            break
        if evaluated and time.perf_counter() >= deadline:
            break
        if evaluated >= 6 and reader.nodes >= reader.max_nodes:
            break

        played = _play(board, ids, groups, p, 1)
        if played is None:
            continue

        after, captured = played
        if _signature(after) in seen_positions:
            continue

        ai, ag = _analyse(after)
        own_risk, enemy_risk = assess_position(after, ai, ag)

        score = positional + 5.5 * (
            captured
            + baseline_own - own_risk
            + enemy_risk - baseline_enemy
        )

        # Very small deterministic tie-break, without disturbing tactics.
        score += 0.00001 * raw

        evaluated += 1
        if score > best_score:
            best_score = score
            best_point = p
            best_board = after

    if best_point is None:
        # This also covers a position where all otherwise legal candidates
        # would repeat an earlier board.
        return finish()

    if occupied >= 70 and best_score <= 0.03:
        return finish()

    return finish(best_point, best_board)


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]],
           memory: dict) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}
    try:
        return _policy(me, opponent, memory)
    except Exception:
        # Passing is always a valid fallback action.
        return (0, 0), memory
