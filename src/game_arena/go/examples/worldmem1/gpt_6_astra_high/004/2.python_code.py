
from collections import deque
from math import sqrt
from time import perf_counter

SIZE = 19
POINTS = SIZE * SIZE


def _make_tables():
    neighbors = []
    diagonals = []
    edges = []
    nearby = []
    weights = (1.0, 0.65, 0.38, 0.22, 0.12, 0.065, 0.03)

    for p in range(POINTS):
        r, c = divmod(p, SIZE)
        ns = []
        ds = []
        near = []

        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE:
                ns.append(rr * SIZE + cc)

        for dr, dc in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
            rr, cc = r + dr, c + dc
            if 0 <= rr < SIZE and 0 <= cc < SIZE:
                ds.append(rr * SIZE + cc)

        for dr in range(-6, 7):
            rr = r + dr
            if not 0 <= rr < SIZE:
                continue
            for dc in range(-6, 7):
                d = abs(dr) + abs(dc)
                cc = c + dc
                if d <= 6 and 0 <= cc < SIZE:
                    near.append((rr * SIZE + cc, weights[d]))

        neighbors.append(tuple(ns))
        diagonals.append(tuple(ds))
        edges.append(min(r, c, SIZE - 1 - r, SIZE - 1 - c))
        nearby.append(tuple(near))

    return neighbors, diagonals, edges, nearby


_NB, _DIAG, _EDGE, _NEAR = _make_tables()
_STARS = (3 * SIZE + 3, 3 * SIZE + 15,
          15 * SIZE + 3, 15 * SIZE + 15)


class _Board:
    __slots__ = ("b", "gid", "groups", "key", "prev", "taken", "captures")

    def __init__(self, board, previous=None):
        self.b = board
        self.key = bytes(board)
        self.prev = previous
        self.taken = 0
        self.captures = ()
        ids = [-1] * POINTS
        groups = []

        for start in range(POINTS):
            color = board[start]
            if not color or ids[start] != -1:
                continue

            number = len(groups)
            stones = []
            liberties = set()
            stack = [start]
            ids[start] = number

            while stack:
                p = stack.pop()
                stones.append(p)
                for q in _NB[p]:
                    v = board[q]
                    if v == 0:
                        liberties.add(q)
                    elif v == color and ids[q] == -1:
                        ids[q] = number
                        stack.append(q)

            groups.append((color, stones, liberties))

        self.gid = ids
        self.groups = groups

    def possible(self, p, color):
        if self.b[p]:
            return False
        for q in _NB[p]:
            v = self.b[q]
            if not v:
                return True
            count = len(self.groups[self.gid[q]][2])
            if v == color and count > 1:
                return True
            if v != color and count == 1:
                return True
        return False

    def play(self, p, color):
        if self.b[p]:
            return None

        captured = set()
        legal = False
        for q in _NB[p]:
            v = self.b[q]
            if not v:
                legal = True
            else:
                g = self.gid[q]
                libs = self.groups[g][2]
                if v == color:
                    if len(libs) > 1:
                        legal = True
                elif len(libs) == 1:
                    captured.add(g)

        if not legal and not captured:
            return None

        board = self.b[:]
        board[p] = color
        count = 0
        for g in captured:
            stones = self.groups[g][1]
            count += len(stones)
            for q in stones:
                board[q] = 0

        if self.prev is not None and bytes(board) == self.prev:
            return None

        result = _Board(board, self.key)
        result.taken = count
        result.captures = tuple(captured)
        return result


def _two_eyes(state, g):
    liberties = state.groups[g][2]
    if len(liberties) < 2:
        return False

    count = 0
    for p in liberties:
        if all(state.gid[q] == g for q in _NB[p]):
            count += 1
            if count >= 2:
                return True
    return False


def _full_risk(n):
    return 3.0 + 7.5 * n


def _base_risk(libs, n):
    if libs == 1:
        return _full_risk(n)
    if libs == 2:
        return 1.0 + 0.7 * sqrt(n)
    if libs == 3:
        return 0.3 + 0.25 * sqrt(n)
    if libs == 4:
        return 0.12 * sqrt(n)
    return 0.0


def _metrics(state, hunted):
    endangered_ids = {
        state.gid[p] for p in hunted if state.b[p] == 1
    }
    risk = 0.0
    threat = 0.0
    own_low = []
    enemy_low = []

    for g, (color, stones, liberties) in enumerate(state.groups):
        count = len(liberties)
        if count >= 5:
            continue
        if count >= 2 and _two_eyes(state, g):
            continue

        n = len(stones)
        if color == 1:
            value = _base_risk(count, n)
            if count == 2 and g in endangered_ids:
                value = _full_risk(n)
            risk += value
            if count <= 2:
                own_low.append((g, value))
        else:
            if count == 1:
                threat += 2.0 + 0.7 * sqrt(n)
            elif count == 2:
                threat += 0.4 + 0.2 * sqrt(n)
            elif count == 3:
                threat += 0.1
            if count <= 2:
                enemy_low.append(g)

    return risk, threat, own_low, enemy_low


class _Reader:
    """Bounded, three-valued local capture reader."""

    __slots__ = ("deadline", "limit", "nodes", "cache")

    def __init__(self, deadline, limit):
        self.deadline = deadline
        self.limit = limit
        self.nodes = 0
        self.cache = {}

    def available(self):
        return self.nodes < self.limit and perf_counter() < self.deadline

    def win(self, state, target, victim, turn, depth=36):
        if state.b[target] != victim:
            return True

        g = state.gid[target]
        liberties = state.groups[g][2]
        if len(liberties) >= 3 or _two_eyes(state, g):
            return False
        if depth <= 0:
            return None

        self.nodes += 1
        if self.nodes >= self.limit:
            return None
        if (self.nodes & 7) == 0 and perf_counter() >= self.deadline:
            return None

        key = (state.key, state.prev, target, victim, turn, depth)
        if key in self.cache:
            return self.cache[key]

        attacker = 3 - victim
        unknown = False

        if turn == attacker:
            for p in liberties:
                child = state.play(p, attacker)
                if child is None:
                    continue
                answer = self.win(child, target, victim, victim, depth - 1)
                if answer is True:
                    self.cache[key] = True
                    return True
                if answer is None:
                    unknown = True

            result = None if unknown else False
        else:
            moves = set(liberties)
            adjacent_attackers = set()

            for p in state.groups[g][1]:
                for q in _NB[p]:
                    if state.b[q] == attacker:
                        adjacent_attackers.add(state.gid[q])

            for enemy_g in adjacent_attackers:
                enemy_libs = state.groups[enemy_g][2]
                if len(enemy_libs) == 1:
                    moves.update(enemy_libs)
                elif len(liberties) == 2 and len(enemy_libs) == 2:
                    moves.update(enemy_libs)

            def freedom(p):
                value = sum(state.b[q] == 0 for q in _NB[p])
                for q in _NB[p]:
                    if state.b[q] == victim:
                        value += min(4, len(state.groups[state.gid[q]][2]))
                    elif state.b[q] == attacker:
                        if len(state.groups[state.gid[q]][2]) == 1:
                            value += 5
                return value

            for p in sorted(moves, key=freedom, reverse=True):
                child = state.play(p, victim)
                if child is None:
                    continue
                answer = self.win(child, target, victim, attacker, depth - 1)
                if answer is False:
                    self.cache[key] = False
                    return False
                if answer is None:
                    unknown = True

            result = None if unknown else True

        if result is not None:
            self.cache[key] = result
        return result


def _distances(board, color):
    distances = [40] * POINTS
    queue = deque()
    for p, v in enumerate(board):
        if v == color:
            distances[p] = 0
            queue.append(p)

    while queue:
        p = queue.popleft()
        d = distances[p] + 1
        for q in _NB[p]:
            if d < distances[q]:
                distances[q] = d
                queue.append(q)
    return distances


def _small_regions(board):
    marks = [0] * POINTS
    visited = bytearray(POINTS)

    for start in range(POINTS):
        if board[start] or visited[start]:
            continue

        visited[start] = 1
        stack = [start]
        region = []
        boundary = set()

        while stack:
            p = stack.pop()
            region.append(p)
            for q in _NB[p]:
                if board[q]:
                    boundary.add(board[q])
                elif not visited[q]:
                    visited[q] = 1
                    stack.append(q)

        if len(region) <= 22 and len(boundary) == 1:
            owner = next(iter(boundary))
            for p in region:
                marks[p] = owner

    return marks


def _positional_scores(state):
    board = state.b
    mine = [0.0] * POINTS
    theirs = [0.0] * POINTS
    occupied = 0
    own_count = 0

    for p, color in enumerate(board):
        if not color:
            continue
        occupied += 1
        if color == 1:
            own_count += 1
        influence = mine if color == 1 else theirs
        for q, weight in _NEAR[p]:
            influence[q] += weight

    dm = _distances(board, 1)
    de = _distances(board, 2)
    regions = _small_regions(board)
    opening = max(0.0, 1.0 - occupied / 110.0)
    tempo = 1.0 + 1.8 * opening
    denominator = [mine[p] + theirs[p] + 0.65 for p in range(POINTS)]
    numerator = [2.0 * theirs[p] + 0.65 for p in range(POINTS)]
    line_bonus = (-2.2, -0.7, 1.0, 1.8, 0.8, 0.2, 0.0, 0.0, 0.0, 0.0)

    available_corners = []
    for star in _STARS:
        nearest = min(dm[star], de[star])
        availability = min(1.0, max(0.0, (nearest - 3.0) / 3.0))
        if availability:
            available_corners.append((divmod(star, SIZE), availability))

    scores = [-1e9] * POINTS
    for p, v in enumerate(board):
        if v:
            continue

        gain = 0.0
        for q, weight in _NEAR[p]:
            if board[q] == 0:
                d = denominator[q]
                gain += weight * numerator[q] / (d * (d + weight))

        score = 0.70 * gain - tempo
        edge = _EDGE[p]
        score += opening * line_bonus[edge]
        if edge == 0:
            score -= 0.45
        elif edge in (2, 3):
            score += 0.15

        r, c = divmod(p, SIZE)
        corner_bonus = 0.0
        for (sr, sc), availability in available_corners:
            distance = abs(r - sr) + abs(c - sc)
            corner_bonus = max(
                corner_bonus,
                availability * max(0.0, 3.5 - 1.1 * distance)
            )
        score += opening * corner_bonus

        if own_count:
            if dm[p] == 2:
                score += 1.05
            elif dm[p] == 3:
                score += 0.8
            elif dm[p] == 4:
                score += 0.25
            if dm[p] > 5 and de[p] <= 3:
                score -= min(4.0, 0.6 * (dm[p] - 4))

        imbalance = max(0.0, theirs[p] - mine[p] - 0.45)
        score -= 1.7 * imbalance

        friendly = sum(board[q] == 1 for q in _NB[p])
        enemy = sum(board[q] == 2 for q in _NB[p])
        empty = len(_NB[p]) - friendly - enemy

        if enemy and not friendly:
            score -= 1.2
            if empty <= 2:
                score -= 1.0
        if de[p] == 1 and dm[p] >= 3:
            score -= 1.4
        if not friendly and any(board[q] == 1 for q in _DIAG[p]):
            score += 0.45
        if friendly and empty >= 2:
            score += 0.2

        if regions[p] == 1:
            score -= 7.0
        elif regions[p] == 2:
            score -= 3.5

        score += ((p * 73 + occupied * 23) % 101) * 0.00001
        scores[p] = score

    return scores


def _fork_penalty(state, own_low):
    shared = {}
    for g, unused in own_low:
        color, stones, liberties = state.groups[g]
        if len(liberties) != 2:
            continue
        for p in liberties:
            shared.setdefault(p, []).append(len(stones))

    penalty = 0.0
    for p, sizes in shared.items():
        if len(sizes) < 2:
            continue
        if not state.possible(p, 2):
            continue

        free = sum(state.b[q] == 0 for q in _NB[p])
        supported = any(
            state.b[q] == 2
            and len(state.groups[state.gid[q]][2]) >= 3
            for q in _NB[p]
        )
        if free >= 2 or supported:
            sizes.sort(reverse=True)
            penalty = max(penalty, min(24.0, 2.5 * sizes[1]))
    return penalty


def _finish(root, selected, point, history, seen):
    current = root.key.hex()
    if current not in seen:
        history.append(current)
        seen.add(current)

    after = selected.key.hex()
    if after not in seen:
        history.append(after)

    new_memory = {
        "positions": history,
        "last_after": after,
    }
    if point is None:
        return (0, 0), new_memory
    return (point // SIZE + 1, point % SIZE + 1), new_memory


def _policy(me, opponent, memory):
    start = perf_counter()
    finish_time = start + 0.90

    board = [0] * POINTS
    for r, c in me:
        board[(r - 1) * SIZE + c - 1] = 1
    for r, c in opponent:
        board[(r - 1) * SIZE + c - 1] = 2

    if not isinstance(memory, dict):
        memory = {}

    previous = None
    try:
        previous = bytes.fromhex(memory.get("last_after", ""))
        if len(previous) != POINTS:
            previous = None
    except (ValueError, TypeError):
        previous = None

    history = memory.get("positions", [])
    if not isinstance(history, list):
        history = []
    history = [
        x for x in history
        if isinstance(x, str) and len(x) == 2 * POINTS
    ]
    if not history:
        history = [bytes(POINTS).hex()]
    seen = set(history)

    root = _Board(board, previous)
    positions = _positional_scores(root)
    reader = _Reader(start + 0.17, 450)

    hunted = set()
    known_dead = set()

    own_candidates = []
    enemy_candidates = []
    for g, (color, stones, liberties) in enumerate(root.groups):
        if len(liberties) > 2 or _two_eyes(root, g):
            continue
        if color == 1 and len(liberties) == 2:
            own_candidates.append(g)
        elif color == 2:
            enemy_candidates.append(g)

    own_candidates.sort(key=lambda g: len(root.groups[g][1]), reverse=True)
    enemy_candidates.sort(
        key=lambda g: (len(root.groups[g][2]), -len(root.groups[g][1]))
    )

    for g in own_candidates[:10]:
        if not reader.available():
            break
        anchor = root.groups[g][1][0]
        if reader.win(root, anchor, 1, 2) is True:
            hunted.add(anchor)

    for g in enemy_candidates[:10]:
        if not reader.available():
            break
        anchor = root.groups[g][1][0]
        if reader.win(root, anchor, 2, 2) is True:
            known_dead.add(g)

    old_risk, old_threat, _, _ = _metrics(root, hunted)

    urgency = [0.0] * POINTS
    urgent_points = set()
    for g, (color, stones, liberties) in enumerate(root.groups):
        count = len(liberties)
        if count > 2 or _two_eyes(root, g):
            continue

        urgent_points.update(liberties)
        n = len(stones)
        if color == 1:
            value = _full_risk(n) if count == 1 else 2.0 + sqrt(n)
            if stones[0] in hunted:
                value = _full_risk(n)
        else:
            value = 8.0 * n if count == 1 else 2.0 + sqrt(n)

        for p in liberties:
            urgency[p] += value

    empties = [p for p in range(POINTS) if not board[p]]
    empties.sort(key=lambda p: positions[p] + urgency[p], reverse=True)
    records = []

    for index, p in enumerate(empties):
        if index and (index & 15) == 0 and perf_counter() > start + 0.60:
            break

        friendly_ids = {
            root.gid[q] for q in _NB[p] if board[q] == 1
        }

        # Filling a one-chain eye cannot improve the position.
        if (len(friendly_ids) == 1
                and all(board[q] == 1 for q in _NB[p])):
            continue

        child = root.play(p, 1)
        if child is None or child.key.hex() in seen:
            continue

        risk, threat, own_low, enemy_low = _metrics(child, hunted)
        score = positions[p]
        score += old_risk - risk + threat - old_threat
        score += 8.0 * child.taken + 2.0 * len(child.captures)

        for g in child.captures:
            if g in known_dead:
                score -= 4.0 * len(root.groups[g][1])

        if len(friendly_ids) > 1:
            score += min(1.8, 0.7 * (len(friendly_ids) - 1))

        for q in _NB[p]:
            if child.b[q] != 0:
                continue
            ids = {child.gid[t] for t in _NB[q]}
            if len(ids) == 1 and -1 not in ids:
                eye_g = next(iter(ids))
                if child.groups[eye_g][0] == 1:
                    if not all(board[t] == 1 for t in _NB[q]):
                        score += 0.7

        records.append((score, p, child, own_low, enemy_low))

    if not records:
        return _finish(root, root, None, history, seen)

    records.sort(key=lambda record: record[0], reverse=True)
    shortlist = records[:24]
    included = {record[1] for record in shortlist}
    extras = 0
    for record in records:
        if record[1] in urgent_points and record[1] not in included:
            shortlist.append(record)
            included.add(record[1])
            extras += 1
            if extras >= 12:
                break

    reader.deadline = start + 0.88
    reader.limit = reader.nodes + 2200

    best_score = -float("inf")
    best_point = None
    best_state = root

    for initial_score, p, child, own_low, enemy_low in shortlist:
        if best_point is not None and perf_counter() >= finish_time:
            break

        score = initial_score

        for g, approximate_risk in own_low:
            color, stones, liberties = child.groups[g]
            n = len(stones)

            if len(liberties) == 1:
                liberty = next(iter(liberties))
                capture = child.play(liberty, 2)
                actual_risk = (
                    _full_risk(n) if capture is not None
                    else 2.0 + 0.6 * sqrt(n)
                )
            elif reader.available():
                answer = reader.win(child, stones[0], 1, 2)
                if answer is True:
                    actual_risk = _full_risk(n)
                elif answer is False:
                    actual_risk = _base_risk(2, n)
                else:
                    actual_risk = max(
                        approximate_risk, _base_risk(2, n) + 1.0
                    )
            else:
                actual_risk = approximate_risk

            score += approximate_risk - actual_risk

        score -= _fork_penalty(child, own_low)

        adjacent_enemies = {
            child.gid[q] for q in _NB[p] if child.b[q] == 2
        }

        for g in enemy_low:
            if g not in adjacent_enemies or not reader.available():
                continue

            color, stones, liberties = child.groups[g]
            old_g = root.gid[stones[0]]
            if old_g in known_dead:
                continue

            # Only newly changed tactical situations need extra reading.
            old_liberties = root.groups[old_g][2]
            if liberties == old_liberties:
                continue

            if reader.win(child, stones[0], 2, 2) is True:
                score += 4.0 * len(stones)

        if score > best_score:
            best_score = score
            best_point = p
            best_state = child

    if best_point is None or best_score <= 0.05:
        return _finish(root, root, None, history, seen)
    return _finish(root, best_state, best_point, history, seen)


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]],
           memory: dict) -> tuple[tuple[int, int], dict]:
    try:
        return _policy(me, opponent, memory)
    except Exception:
        # Passing remains legal even if unexpected input or resource issues
        # prevent normal evaluation. Preserve the current position for ko.
        board = [0] * POINTS
        for r, c in me:
            if 1 <= r <= SIZE and 1 <= c <= SIZE:
                board[(r - 1) * SIZE + c - 1] = 1
        for r, c in opponent:
            if 1 <= r <= SIZE and 1 <= c <= SIZE:
                board[(r - 1) * SIZE + c - 1] = 2

        result_memory = dict(memory) if isinstance(memory, dict) else {}
        key = bytes(board).hex()
        history = result_memory.get("positions", [])
        history = list(history) if isinstance(history, list) else []
        if key not in history:
            history.append(key)
        result_memory["positions"] = history
        result_memory["last_after"] = key
        return (0, 0), result_memory
