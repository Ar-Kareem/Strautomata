
import math
import time
from collections import deque

SIZE = 19
POINTS = SIZE * SIZE
BITS = [1 << p for p in range(POINTS)]

NEIGHBORS = []
DIAGONALS = []
NEIGHBOR_MASKS = []
LINES = []

for p in range(POINTS):
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
    NEIGHBOR_MASKS.append(sum(BITS[q] for q in ns))
    LINES.append(min(r + 1, c + 1, SIZE - r, SIZE - c))

# A compact, smoothly decaying territorial influence kernel.
KERNELS = []
for p in range(POINTS):
    r, c = divmod(p, SIZE)
    entries = []
    for dr in range(-7, 8):
        rr = r + dr
        if not 0 <= rr < SIZE:
            continue
        for dc in range(-7, 8):
            cc = c + dc
            d2 = dr * dr + dc * dc
            if 0 <= cc < SIZE and d2 <= 49:
                entries.append((rr * SIZE + cc, 1.0 / (1.0 + d2)))
    KERNELS.append(tuple(entries))


def bit_points(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def group_value(n):
    return 6.0 + 7.0 * min(n, 8) + 3.0 * max(0, n - 8)


def signature(a, b):
    return "%x:%x" % (a, b)


class Position:
    __slots__ = ("board", "at", "groups", "a", "b", "ko")

    def __init__(self, board):
        self.board = board
        self.at = [-1] * POINTS
        self.groups = {}
        self.a = sum(BITS[p] for p, v in enumerate(board) if v == 1)
        self.b = sum(BITS[p] for p, v in enumerate(board) if v == 2)
        self.ko = -1
        occupied = self.a | self.b

        for p, color in enumerate(board):
            if not color or self.at[p] != -1:
                continue
            stack = [p]
            self.at[p] = p
            stones = 0
            border = 0
            while stack:
                q = stack.pop()
                stones |= BITS[q]
                border |= NEIGHBOR_MASKS[q]
                for z in NEIGHBORS[q]:
                    if board[z] == color and self.at[z] == -1:
                        self.at[z] = p
                        stack.append(z)
            self.groups[p] = (color, stones, border & ~occupied, border)

    def without_ko(self):
        if self.ko == -1:
            return self
        result = Position.__new__(Position)
        result.board = self.board
        result.at = self.at
        result.groups = self.groups
        result.a, result.b, result.ko = self.a, self.b, -1
        return result

    def describe(self, p, color):
        if self.board[p] or p == self.ko:
            return None

        friends = set()
        enemies = set()
        for q in NEIGHBORS[p]:
            value = self.board[q]
            if value == color:
                friends.add(self.at[q])
            elif value:
                enemies.add(self.at[q])

        bit = BITS[p]
        stones = bit
        border = NEIGHBOR_MASKS[p]
        liberties = border & ~(self.a | self.b)
        captures = 0

        for gid in friends:
            g = self.groups[gid]
            stones |= g[1]
            liberties |= g[2]
            border |= g[3]

        for gid in enemies:
            g = self.groups[gid]
            if g[2] == bit:
                captures |= g[1]

        liberties = (liberties | (captures & border)) & ~stones
        if not liberties:
            return None

        return friends, enemies, captures, stones, liberties, border

    def play(self, p, color, info=None):
        if info is None:
            info = self.describe(p, color)
        if info is None:
            return None

        friends, enemies, captures, stones, liberties, border = info
        bit = BITS[p]
        result = Position.__new__(Position)
        result.board = self.board.copy()
        result.at = self.at.copy()
        result.groups = self.groups.copy()
        result.ko = -1

        for gid in friends:
            del result.groups[gid]

        for gid in enemies:
            g = self.groups[gid]
            if g[1] & captures:
                del result.groups[gid]
            else:
                result.groups[gid] = (g[0], g[1], g[2] & ~bit, g[3])

        affected = set()
        for q in bit_points(captures):
            result.board[q] = 0
            result.at[q] = -1
            for z in NEIGHBORS[q]:
                gid = self.at[z]
                if self.board[z] == color and gid not in friends:
                    affected.add(gid)

        for gid in affected:
            g = result.groups[gid]
            result.groups[gid] = (
                g[0], g[1], g[2] | (g[3] & captures), g[3]
            )

        result.board[p] = color
        for q in bit_points(stones):
            result.at[q] = p
        result.groups[p] = (color, stones, liberties, border)

        if color == 1:
            result.a = self.a | bit
            result.b = self.b & ~captures
        else:
            result.a = self.a & ~captures
            result.b = self.b | bit

        if (captures and captures.bit_count() == 1
                and stones.bit_count() == 1
                and liberties.bit_count() == 1):
            result.ko = captures.bit_length() - 1
        return result


class TacticalReader:
    """Bounded local capture search: 1=caught, 0=escapes, -1=unresolved."""

    def __init__(self, deadline):
        self.deadline = deadline
        self.remaining = 0
        self.cache = {}

    def read(self, state, anchor, color, attacker=True, quota=250):
        self.remaining = quota
        return self._search(state, anchor, color, attacker, 40, True)

    def _search(self, state, anchor, color, attacker, depth, wide=False):
        if state.board[anchor] != color:
            return 1

        g = state.groups[state.at[anchor]]
        liberties = g[2]
        count = liberties.bit_count()

        if count >= 3:
            if not (attacker and wide and count == 3):
                return 0
            outside = 0
            for p in bit_points(liberties):
                outside |= NEIGHBOR_MASKS[p]
            outside &= ~(state.a | state.b | liberties)
            if outside.bit_count() > 5:
                return 0

        if depth <= 0 or self.remaining <= 0:
            return -1
        self.remaining -= 1
        if (self.remaining & 15) == 0 and time.perf_counter() >= self.deadline:
            self.remaining = 0
            return -1

        key = (state.a, state.b, state.ko, anchor, color, attacker, wide)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        moves = set(bit_points(liberties))
        moving_color = 3 - color if attacker else color

        if not attacker:
            # Capturing an adjacent attacker can be better than extending.
            enemy_mask = state.b if color == 1 else state.a
            checked = set()
            for q in bit_points(g[3] & enemy_mask):
                gid = state.at[q]
                if gid in checked:
                    continue
                checked.add(gid)
                enemy = state.groups[gid]
                if enemy[2].bit_count() == 1:
                    moves.add(enemy[2].bit_length() - 1)

        occupied = state.a | state.b
        moves = sorted(
            moves,
            key=lambda p: -(NEIGHBOR_MASKS[p] & ~occupied).bit_count()
        )

        unknown = False
        for p in moves:
            child = state.play(p, moving_color)
            if child is None:
                continue

            value = self._search(
                child, anchor, color, not attacker, depth - 1
            )
            if attacker and value == 1:
                self.cache[key] = 1
                return 1
            if not attacker and value == 0:
                self.cache[key] = 0
                return 0
            if value == -1:
                unknown = True

        if not attacker and count >= 2:
            # Standing pat is essential: never force a living group
            # to fill one of its own eyes in the tactical search.
            value = self._search(
                state.without_ko(), anchor, color, True, depth - 1
            )
            if value == 0:
                self.cache[key] = 0
                return 0
            if value == -1:
                unknown = True

        result = -1 if unknown else (0 if attacker else 1)
        if result != -1:
            self.cache[key] = result
        return result


def distances(board, color):
    result = [99] * POINTS
    queue = deque()
    for p, value in enumerate(board):
        if value == color:
            result[p] = 0
            queue.append(p)
    while queue:
        p = queue.popleft()
        d = result[p] + 1
        for q in NEIGHBORS[p]:
            if result[q] > d:
                result[q] = d
                queue.append(q)
    return result


def empty_regions(board):
    owner = [0] * POINTS
    sizes = [0] * POINTS
    visited = [False] * POINTS
    for p in range(POINTS):
        if board[p] or visited[p]:
            continue
        visited[p] = True
        stack = [p]
        region = []
        borders = 0
        while stack:
            q = stack.pop()
            region.append(q)
            for z in NEIGHBORS[q]:
                value = board[z]
                if value:
                    borders |= 1 << value
                elif not visited[z]:
                    visited[z] = True
                    stack.append(z)
        color = 1 if borders == 2 else 2 if borders == 4 else 0
        for q in region:
            owner[q] = color
            sizes[q] = len(region)
    return owner, sizes


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]],
           memory: dict) -> tuple[tuple[int, int], dict]:
    start = time.perf_counter()
    deadline = start + 0.86

    board = [0] * POINTS
    for r, c in me:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= SIZE and 1 <= c <= SIZE:
            board[(r - 1) * SIZE + c - 1] = 2

    state = Position(board)
    if not isinstance(memory, dict):
        memory = {}

    old_history = memory.get("history", [])
    if not isinstance(old_history, list):
        old_history = []
    history = [x for x in old_history if isinstance(x, str)]
    seen = set(history)
    current_key = signature(state.a, state.b)

    # Infer the immediate ko from the board after our previous move.
    try:
        old_a, old_b = (
            int(x, 16) for x in memory.get("last", "").split(":")
        )
        lost = old_a & ~state.a
        added = state.b & ~old_b
        if (lost.bit_count() == 1 and added.bit_count() == 1
                and not (state.a & ~old_a)
                and not (old_b & ~state.b)):
            q = added.bit_length() - 1
            g = state.groups[state.at[q]]
            if g[1] == added and g[2] == lost:
                state.ko = lost.bit_length() - 1
    except (ValueError, TypeError, AttributeError):
        pass

    if current_key not in seen:
        history.append(current_key)
        seen.add(current_key)

    def finish(p, info=None):
        if p is None:
            key = current_key
            action = (0, 0)
        else:
            key = signature(state.a | BITS[p], state.b & ~info[2])
            action = (p // SIZE + 1, p % SIZE + 1)
        if key not in seen:
            history.append(key)
        return action, {"history": history, "last": key}

    empties = [p for p, value in enumerate(board) if not value]
    if not empties:
        return finish(None)

    total = POINTS - len(empties)
    own_distance = distances(board, 1)
    enemy_distance = distances(board, 2)
    region_owner, region_size = empty_regions(board)

    own_field = [0.0] * POINTS
    enemy_field = [0.0] * POINTS
    for p, color in enumerate(board):
        if color:
            field = own_field if color == 1 else enemy_field
            for q, weight in KERNELS[p]:
                field[q] += weight

    denominator = [
        own_field[p] + enemy_field[p] + 0.6 for p in range(POINTS)
    ]
    numerator = [2.0 * enemy_field[p] + 0.6 for p in range(POINTS)]
    coefficient = [
        numerator[p] / denominator[p] for p in range(POINTS)
    ]

    opening = max(0.0, 1.0 - total / 100.0)
    corner_bonus = {}
    if total < 50:
        for rr, cc in ((3, 3), (3, 15), (15, 3), (15, 15)):
            rows = range(6) if rr == 3 else range(13, 19)
            cols = range(6) if cc == 3 else range(13, 19)
            if not any(board[r * SIZE + c] for r in rows for c in cols):
                corner_bonus[rr * SIZE + cc] = 8.0
    side_stars = {3 * SIZE + 9, 15 * SIZE + 9,
                  9 * SIZE + 3, 9 * SIZE + 15}

    reader = TacticalReader(min(deadline, start + 0.18))
    risks = {}
    hypothetical = state.without_ko()
    own_groups = sorted(
        ((gid, g) for gid, g in state.groups.items() if g[0] == 1),
        key=lambda item: (
            item[1][2].bit_count(), -item[1][1].bit_count()
        )
    )
    for gid, g in own_groups:
        liberties = g[2].bit_count()
        n = g[1].bit_count()
        if liberties > 3:
            break
        if liberties == 1:
            risks[gid] = (gid, group_value(n))
        elif time.perf_counter() < reader.deadline:
            if liberties == 2 or n >= 3:
                if reader.read(hypothetical, gid, 1, True, 220) == 1:
                    risks[gid] = (gid, group_value(n))
    reader.deadline = deadline

    records = []
    for p in empties:
        info = state.describe(p, 1)
        if info is None:
            continue
        friends, enemies, captures, stones, liberties, border = info
        next_key = signature(state.a | BITS[p], state.b & ~captures)
        if next_key in seen:
            continue

        nlib = liberties.bit_count()
        nstones = stones.bit_count()
        ncaptured = captures.bit_count()

        gain = numerator[p] / (denominator[p] + 1.0)
        for q, weight in KERNELS[p]:
            if not board[q]:
                gain += weight * coefficient[q] / (denominator[q] + weight)
        score = 0.55 * gain - 0.5

        if ncaptured:
            score += group_value(ncaptured)

        # Estimate which existing threats this move answers.
        rescues = []
        for gid, (anchor, value) in risks.items():
            g = state.groups[gid]
            if gid in friends:
                new_count = nlib
            elif g[3] & captures:
                new_count = (g[2] | (g[3] & captures)).bit_count()
            else:
                continue
            probability = 1.0 if new_count >= 3 else (
                0.65 if new_count == 2 else 0.0
            )
            if probability:
                score += value * probability
                rescues.append((anchor, value, probability))

        self_penalty = 0.0
        if nlib == 1:
            if ncaptured == 1 and nstones == 1:
                self_penalty = 1.5       # A protected ko capture.
            else:
                self_penalty = group_value(nstones) + 5.0
        elif nlib == 2:
            self_penalty = 2.5 + 0.2 * min(nstones, 10)
        elif nlib == 3 and nstones > 2:
            self_penalty = 1.0
        score -= self_penalty

        for gid in enemies:
            g = state.groups[gid]
            if g[1] & captures:
                continue
            count = g[2].bit_count()
            size = g[1].bit_count()
            if count == 2:
                score += 2.3 + min(2.0, 0.28 * math.sqrt(size))
            elif count == 3:
                score += 0.7 + 0.15 * math.sqrt(size)
            elif count == 4:
                score += 0.25

        if friends and enemy_distance[p] <= 3:
            old_liberties = max(
                state.groups[gid][2].bit_count() for gid in friends
            )
            if old_liberties <= 4:
                score += max(0, min(3, nlib - old_liberties)) * (
                    0.7 + 0.15 * min(nstones, 8)
                )

        if len(friends) >= 2:
            fs = list(friends)
            common = min(
                (state.groups[fs[i]][2] & state.groups[fs[j]][2]
                 & ~BITS[p]).bit_count()
                for i in range(len(fs)) for j in range(i)
            )
            connection = 1.5 * (len(fs) - 1)
            connection += 2.5 if common == 0 else 1.0 if common == 1 else 0.0
            score += connection * (1.0 if enemy_distance[p] <= 3 else 0.5)

        if len(enemies) >= 2:
            score += (len(enemies) - 1) * (
                2.0 if own_distance[p] <= 2 else 0.5
            )

        own_adjacent = sum(board[q] == 1 for q in NEIGHBORS[p])
        enemy_adjacent = sum(board[q] == 2 for q in NEIGHBORS[p])
        own_diagonal = sum(board[q] == 1 for q in DIAGONALS[p])

        if not own_adjacent:
            score += 0.25 * own_diagonal
            if own_distance[p] == 2:
                score += 0.7
            elif own_distance[p] == 3:
                score += 0.4
        elif own_adjacent >= 2 and len(friends) == 1:
            r, c = divmod(p, SIZE)
            vertical = ((r > 0 and board[p - SIZE] == 1)
                        or (r < SIZE - 1 and board[p + SIZE] == 1))
            horizontal = ((c > 0 and board[p - 1] == 1)
                          or (c < SIZE - 1 and board[p + 1] == 1))
            if vertical and horizontal:
                score -= 1.6

        if own_adjacent and enemy_adjacent and nlib >= 2:
            score += 0.75

        hostile = enemy_field[p] - 0.8 * own_field[p]
        if hostile > 0:
            score -= 6.0 * hostile / (
                0.5 + own_field[p] + enemy_field[p]
            )
        if enemy_distance[p] == 1 and own_distance[p] > 2 and not ncaptured:
            score -= 4.0
        elif enemy_distance[p] == 2 and own_distance[p] > 3:
            score -= 2.0

        if own_distance[p] == 1 and enemy_distance[p] >= 4:
            if own_field[p] > 3.0 * enemy_field[p]:
                score -= 1.5 if enemy_distance[p] == 4 else 3.0

        line = LINES[p]
        if line == 1:
            score -= 5.0 * opening * (0.6 if enemy_adjacent else 1.0)
        elif line == 2:
            score -= 1.5 * opening
        elif line == 3:
            score += 1.8 * opening
        elif line == 4:
            score += 2.5 * opening
        elif line == 5:
            score += 0.8 * opening
        elif total < 28:
            score -= 0.5 * opening

        score += corner_bonus.get(p, 0.0)
        if (total < 45 and p in side_stars
                and min(own_distance[p], enemy_distance[p]) >= 4):
            score += 1.8

        owner, area = region_owner[p], region_size[p]
        if owner == 1:
            if area <= 8:
                score -= 16.0
            elif area <= 36:
                score -= 8.0
            elif area <= 60:
                score -= 3.0
        elif owner == 2 and not ncaptured:
            if area <= 16:
                score -= 8.0
            elif area <= 40:
                score -= 3.0

        # Do not voluntarily fill a genuine single-point eye.
        if own_adjacent == len(NEIGHBORS[p]):
            bad_diagonals = sum(board[q] == 2 for q in DIAGONALS[p])
            allowed = 1 if len(DIAGONALS[p]) == 4 else 0
            if bad_diagonals <= allowed:
                score -= 47.0

        records.append((score, p, info, self_penalty, rescues))

    if not records:
        return finish(None)

    records.sort(key=lambda item: (-item[0], item[1]))
    selected = records[:32]
    selected_points = {record[1] for record in selected}
    # Include unusually shaped tactical moves even if their static
    # self-atari penalty initially puts them below positional moves.
    extra = 0
    for record in records[32:]:
        if extra >= 10:
            break
        if record[2][2] or record[4]:
            if record[1] not in selected_points:
                selected.append(record)
                selected_points.add(record[1])
                extra += 1

    best_score = -float("inf")
    best_record = None

    for record in selected:
        if best_record is not None and time.perf_counter() >= deadline:
            break

        score, p, info, self_penalty, rescues = record
        child = state.play(p, 1, info)
        friends, enemies, captures, stones, liberties, border = info
        nlib = liberties.bit_count()
        danger = 0

        if nlib <= 3 and time.perf_counter() < deadline:
            danger = reader.read(child, p, 1, True, 420)
            if danger == 1:
                score -= max(
                    0.0, group_value(stones.bit_count()) + 7.0 - self_penalty
                )
            elif danger == 0 and nlib <= 2:
                score += 0.8 * self_penalty
            elif danger == -1 and nlib <= 2:
                score -= 2.0

        for anchor, value, probability in rescues:
            if child.at[anchor] == p:
                verdict = danger
            else:
                g = child.groups[child.at[anchor]]
                if g[2].bit_count() >= 3:
                    verdict = 0
                elif time.perf_counter() < deadline:
                    verdict = reader.read(child, anchor, 1, True, 220)
                else:
                    verdict = -1
            actual = 0.0 if verdict == 1 else (
                1.0 if verdict == 0 else probability
            )
            score += (actual - probability) * value

        if danger != 1:
            targets = sorted(
                (gid for gid in enemies
                 if not state.groups[gid][1] & captures),
                key=lambda gid: -state.groups[gid][1].bit_count()
            )
            for gid in targets[:3]:
                g = child.groups[child.at[gid]]
                if g[2].bit_count() > 2:
                    continue
                if time.perf_counter() >= deadline:
                    break
                verdict = reader.read(child, gid, 2, False, 320)
                if verdict == 1:
                    score += 0.8 * group_value(g[1].bit_count())
                elif verdict == 0 and g[2].bit_count() == 1:
                    escape = g[2].bit_length() - 1
                    escape_info = child.describe(escape, 2)
                    if escape_info and escape_info[4].bit_count() >= 4:
                        score -= 1.4

        if score > best_score:
            best_score = score
            best_record = record

    # A fully validated fallback remains available even if reading
    # exhausted the allotted time.
    if best_record is None:
        best_record = records[0]
        best_score = best_record[0]

    if best_score <= 0.05 and not (total < 50 and best_score > -8.0):
        return finish(None)

    return finish(best_record[1], best_record[2])
