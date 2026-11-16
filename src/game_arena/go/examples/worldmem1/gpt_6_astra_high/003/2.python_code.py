
import math
import time
import hashlib
from collections import deque

N = 19
SIZE = N * N

NEIGHBORS = []
DIAGONALS = []
EDGE = []
for p in range(SIZE):
    r, c = divmod(p, N)
    NEIGHBORS.append(tuple(
        rr * N + cc
        for rr, cc in ((r - 1, c), (r + 1, c),
                       (r, c - 1), (r, c + 1))
        if 0 <= rr < N and 0 <= cc < N
    ))
    DIAGONALS.append(tuple(
        rr * N + cc
        for rr, cc in ((r - 1, c - 1), (r - 1, c + 1),
                       (r + 1, c - 1), (r + 1, c + 1))
        if 0 <= rr < N and 0 <= cc < N
    ))
    EDGE.append(min(r + 1, c + 1, N - r, N - c))

DECAY = [math.exp(-d / 2.35) if d <= 12 else 0.0
         for d in range(64)]

REACH = []
for p in range(SIZE):
    r, c = divmod(p, N)
    area = []
    for dr in range(-5, 6):
        for dc in range(-5, 6):
            d = abs(dr) + abs(dc)
            rr, cc = r + dr, c + dc
            if d <= 5 and 0 <= rr < N and 0 <= cc < N:
                area.append((rr * N + cc, DECAY[d]))
    REACH.append(tuple(area))


def _fingerprint(board):
    return hashlib.blake2b(bytes(board), digest_size=16).hexdigest()


def _group(board, start, stop=0):
    """With stop > 0, a partial group suffices once stop liberties appear."""
    color = board[start]
    stones = {start}
    liberties = set()
    stack = [start]
    while stack:
        p = stack.pop()
        for q in NEIGHBORS[p]:
            v = board[q]
            if v == 0:
                liberties.add(q)
                if stop and len(liberties) >= stop:
                    return stones, liberties
            elif v == color and q not in stones:
                stones.add(q)
                stack.append(q)
    return stones, liberties


def _play(board, p, color, ko=-1):
    if p == ko or board[p] != 0:
        return None

    result = board.copy()
    result[p] = color
    enemy = 3 - color
    checked = set()
    captured = []

    for q in NEIGHBORS[p]:
        if result[q] != enemy or q in checked:
            continue
        stones, liberties = _group(result, q, 1)
        checked.update(stones)
        if not liberties:
            captured.extend(stones)
            for s in stones:
                result[s] = 0

    _, liberties = _group(result, p, 1)
    if not liberties:
        return None

    next_ko = -1
    if (len(captured) == 1
            and not any(result[q] == color for q in NEIGHBORS[p])
            and sum(result[q] == 0 for q in NEIGHBORS[p]) == 1):
        next_ko = captured[0]

    return result, captured, next_ko


def _analyze(board):
    ids = [-1] * SIZE
    groups = []

    for p, color in enumerate(board):
        if color == 0 or ids[p] != -1:
            continue
        stones, liberties = _group(board, p)
        gid = len(groups)
        for s in stones:
            ids[s] = gid
        groups.append((color, stones, liberties))

    owner = [0] * SIZE
    region_size = [0] * SIZE
    visited = set()
    eyes = [0] * len(groups)

    for p in range(SIZE):
        if board[p] or p in visited:
            continue
        region = [p]
        visited.add(p)
        borders = set()
        stack = [p]
        while stack:
            s = stack.pop()
            for q in NEIGHBORS[s]:
                if board[q]:
                    borders.add(ids[q])
                elif q not in visited:
                    visited.add(q)
                    region.append(q)
                    stack.append(q)

        colors = {groups[g][0] for g in borders}
        color = next(iter(colors)) if len(colors) == 1 else 0
        for s in region:
            owner[s] = color
            region_size[s] = len(region)

        # Two separate vital empty regions certify a safe group.
        if len(borders) == 1 and len(region) <= 10:
            gid = next(iter(borders))
            if all(any(ids[q] == gid for q in NEIGHBORS[s])
                   for s in region):
                eyes[gid] += 1

    alive = [e >= 2 for e in eyes]
    return ids, groups, owner, region_size, alive


def _distances(board, color):
    dist = [50] * SIZE
    queue = deque()
    for p, v in enumerate(board):
        if v == color:
            dist[p] = 0
            queue.append(p)
    while queue:
        p = queue.popleft()
        nd = dist[p] + 1
        for q in NEIGHBORS[p]:
            if board[q] == 0 and nd < dist[q]:
                dist[q] = nd
                queue.append(q)
    return dist


def _value(size):
    return 4.0 + 3.5 * size ** 0.85


class _Reader:
    """Bounded alternating ladder and low-liberty tactical search."""

    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.left = 0
        self.anchor = 0
        self.color = 1
        self.cache = {}

    def check(self, board, anchor, color, attacker_turn,
              ko=-1, budget=220):
        if self.nodes >= 6500 or time.perf_counter() >= self.deadline:
            return None
        self.anchor = anchor
        self.color = color
        self.left = budget
        self.cache = {}
        return self._search(board, attacker_turn, ko, 36)

    def _search(self, board, attacker_turn, ko, depth):
        self.nodes += 1
        self.left -= 1
        if self.left < 0 or self.nodes > 6500:
            return None
        if self.nodes % 24 == 0 and time.perf_counter() >= self.deadline:
            return None

        if board[self.anchor] != self.color:
            return True

        stones, liberties = _group(board, self.anchor, 3)
        if len(liberties) >= 3:
            return False
        if depth <= 0:
            return None

        key = (bytes(board), attacker_turn, ko, depth)
        if key in self.cache:
            return self.cache[key]

        attacker = 3 - self.color
        moves = set(liberties)

        if not attacker_turn:
            checked = set()
            # Extensions, captures, and local counter-atari.
            for s in stones:
                for q in NEIGHBORS[s]:
                    if board[q] != attacker or q in checked:
                        continue
                    es, el = _group(board, q, 3)
                    checked.update(es)
                    if len(el) <= 2:
                        moves.update(el)

        moves = sorted(
            moves,
            key=lambda p: sum(board[q] == 0 for q in NEIGHBORS[p]),
            reverse=True
        )

        unknown = False
        color = attacker if attacker_turn else self.color

        for p in moves:
            played = _play(board, p, color, ko)
            if played is None:
                continue
            new_board, _, next_ko = played
            outcome = self._search(
                new_board, not attacker_turn, next_ko, depth - 1
            )
            if attacker_turn and outcome is True:
                self.cache[key] = True
                return True
            if not attacker_turn and outcome is False:
                self.cache[key] = False
                return False
            if outcome is None:
                unknown = True
            if self.left < 0 or self.nodes > 6500:
                break

        if not attacker_turn and len(liberties) > 1 and self.left >= 0:
            # Doing nothing locally is important for two-eye positions.
            outcome = self._search(board, True, -1, depth - 1)
            if outcome is False:
                self.cache[key] = False
                return False
            if outcome is None:
                unknown = True
        elif not attacker_turn and ko in liberties and self.left >= 0:
            outcome = self._search(board, True, -1, depth - 1)
            if outcome is False:
                self.cache[key] = False
                return False
            if outcome is None:
                unknown = True

        result = None if unknown else (not attacker_turn)
        self.cache[key] = result
        return result


def _policy(me, opponent, memory):
    start = time.perf_counter()
    deadline = start + 0.84

    board = [0] * SIZE
    for r, c in me:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + c - 1] = 1
    for r, c in opponent:
        if 1 <= r <= N and 1 <= c <= N:
            board[(r - 1) * N + c - 1] = 2

    history = list(memory.get("go_history", []))
    seen = set(history)
    current_hash = _fingerprint(board)
    if current_hash not in seen:
        history.append(current_hash)
        seen.add(current_hash)

    def finish(p=None, position_hash=None):
        if position_hash is not None and position_hash not in seen:
            history.append(position_hash)
        updated = {"go_history": history}
        if p is None:
            return (0, 0), updated
        return (p // N + 1, p % N + 1), updated

    ids, groups, owner, region_size, alive = _analyze(board)
    dm = _distances(board, 1)
    de = _distances(board, 2)
    own_influence = [DECAY[d] for d in dm]
    weights = [
        1.0 / (0.65 + own_influence[p] + DECAY[de[p]])
        for p in range(SIZE)
    ]

    stone_count = sum(v != 0 for v in board)
    phase = 0.25 + 0.75 * max(0.0, 1.0 - stone_count / 130.0)
    reader = _Reader(min(deadline, start + 0.14))

    critical = {
        gid for gid, g in enumerate(groups)
        if g[0] == 1 and len(g[2]) == 1
    }
    weak_groups = sorted(
        (gid for gid, g in enumerate(groups)
         if g[0] == 1 and len(g[2]) == 2 and not alive[gid]),
        key=lambda gid: len(groups[gid][1]),
        reverse=True
    )
    for gid in weak_groups[:6]:
        if time.perf_counter() >= start + 0.13:
            break
        g = groups[gid]
        result = reader.check(
            board, next(iter(g[1])), 1, True, budget=130
        )
        if result is True:
            critical.add(gid)
    reader.deadline = deadline

    opening_bonus = {}
    if stone_count < 90:
        for flip_r, flip_c in ((False, False), (False, True),
                               (True, False), (True, True)):
            def orient(r, c):
                if flip_r:
                    r = N - 1 - r
                if flip_c:
                    c = N - 1 - c
                return r * N + c

            corner = orient(3, 3)
            occupied = any(
                board[orient(r, c)] != 0
                for r in range(6) for c in range(6)
            )
            if not occupied:
                opening_bonus[corner] = 5.5
            elif board[corner] == 1:
                for r, c in ((2, 5), (5, 2)):
                    p = orient(r, c)
                    if de[p] >= 4:
                        opening_bonus[p] = max(
                            opening_bonus.get(p, 0.0), 1.1 * phase
                        )
            elif board[corner] == 2:
                for r, c in ((2, 6), (6, 2), (3, 6), (6, 3)):
                    p = orient(r, c)
                    if dm[p] >= 2:
                        opening_bonus[p] = max(
                            opening_bonus.get(p, 0.0), 1.3 * phase
                        )

    records = []
    line_scores = (0.0, -3.8, -0.5, 1.5, 2.0, 0.9, 0.25)

    for p in range(SIZE):
        if board[p]:
            continue

        friends = {ids[q] for q in NEIGHBORS[p] if board[q] == 1}
        enemies = {ids[q] for q in NEIGHBORS[p] if board[q] == 2}
        capture_ids = {g for g in enemies if len(groups[g][2]) == 1}

        captured = []
        for gid in capture_ids:
            captured.extend(groups[gid][1])

        liberties = {q for q in NEIGHBORS[p] if board[q] == 0}
        new_size = 1
        for gid in friends:
            new_size += len(groups[gid][1])
            liberties.update(groups[gid][2])
        liberties.discard(p)

        freed = {}
        for s in captured:
            touches_new = False
            for q in NEIGHBORS[s]:
                if q == p:
                    touches_new = True
                elif board[q] == 1:
                    gid = ids[q]
                    freed.setdefault(gid, set()).add(s)
                    if gid in friends:
                        touches_new = True
            if touches_new:
                liberties.add(s)

        nl = len(liberties)
        if nl == 0:
            continue

        expansion = 0.0
        for q, influence in REACH[p]:
            if board[q] == 0 and influence > own_influence[q]:
                expansion += (
                    influence - own_influence[q]
                ) * weights[q]

        score = 0.105 * expansion
        edge = EDGE[p]
        if edge < len(line_scores):
            score += phase * line_scores[edge]
        score += opening_bonus.get(p, 0.0)

        rescue_connected = 0.0
        rescue_total = 0.0
        affected = friends | set(freed)
        for gid in affected:
            _, stones, old_liberties = groups[gid]
            old_n = len(old_liberties)
            if gid in friends:
                new_n = nl
            else:
                new_n = len(old_liberties | freed.get(gid, set()))

            bonus = 0.0
            if old_n == 1 and new_n >= 2:
                bonus = _value(len(stones)) * (1.08 if new_n >= 3 else 0.86)
            elif old_n == 2 and not alive[gid]:
                if gid in critical and new_n >= 2:
                    bonus = _value(len(stones)) * (
                        0.82 if new_n >= 3 else 0.35
                    )
                elif new_n >= 3:
                    bonus = 2.0 + 0.65 * math.sqrt(len(stones))
            elif old_n == 3 and new_n >= 4 and de[p] <= 2:
                bonus = 0.35 + 0.08 * math.sqrt(len(stones))

            rescue_total += bonus
            if gid in friends:
                rescue_connected += bonus
        score += rescue_total

        for gid in capture_ids:
            score += _value(len(groups[gid][1]))

        for gid in enemies - capture_ids:
            if alive[gid]:
                score -= 0.35
                continue
            size = len(groups[gid][1])
            old_n = len(groups[gid][2])
            if old_n == 2:
                score += 2.5 + 0.7 * math.sqrt(size)
            elif old_n == 3:
                score += 0.85 + 0.25 * math.sqrt(size)
            elif old_n == 4:
                score += 0.15

        if nl == 1:
            score -= 6.0 + 3.2 * new_size ** 0.85
        elif nl == 2:
            score -= 1.6 + 0.2 * math.sqrt(new_size)
        else:
            score += min(0.8, 0.14 * (nl - 3))

        if len(friends) >= 2:
            score += 0.8 * (len(friends) - 1)
            if de[p] <= 2:
                score += 0.8
        if len(enemies) >= 2 and dm[p] <= 2:
            score += 1.2

        friendly_diagonals = sum(board[q] == 1 for q in DIAGONALS[p])
        if dm[p] >= 2:
            score += 0.22 * friendly_diagonals
        if enemies and friendly_diagonals:
            score += 0.7
        if enemies and not friends and not friendly_diagonals:
            score -= 1.8

        if dm[p] == 1 and de[p] >= 3:
            score -= 1.2
        elif dm[p] == 2 and de[p] >= 3:
            score += 0.35

        if dm[p] >= de[p] + 2 and de[p] <= 2:
            score -= (2.6 if de[p] == 1 else 1.5)
            score -= 0.12 * min(6, dm[p] - de[p])

        own_neighbors = [q for q in NEIGHBORS[p] if board[q] == 1]
        if len(own_neighbors) >= 3 and not enemies:
            score -= 1.4
        elif len(own_neighbors) == 2 and de[p] > 2:
            a, b = own_neighbors
            if a // N != b // N and a % N != b % N:
                score -= 0.65

        if owner[p] == 1 and region_size[p] <= 35:
            score -= 6.5 if region_size[p] < 9 else 4.0
        elif owner[p] == 2:
            if region_size[p] <= 6:
                score -= 10.0
            elif region_size[p] <= 12:
                score -= 5.0
            elif region_size[p] <= 22:
                score -= 2.0

        if (all(board[q] == 1 for q in NEIGHBORS[p])
                and not captured and rescue_total < 0.1):
            hostile_diagonals = sum(board[q] == 2 for q in DIAGONALS[p])
            if len(friends) == 1 or hostile_diagonals == 0:
                score -= 7.0

        score += 0.00001 * (SIZE - p)
        records.append((
            score, p, nl, new_size, friends, enemies,
            capture_ids, rescue_connected
        ))

    if not records:
        return finish()

    records.sort(key=lambda rec: rec[0], reverse=True)
    best_score = -float("inf")
    best_p = None
    best_hash = None
    evaluated = 0

    for rec in records:
        if evaluated >= 34:
            break
        if evaluated and time.perf_counter() >= deadline:
            break

        score, p, nl, new_size, friends, enemies, cap_ids, rescue = rec
        played = _play(board, p, 1)
        if played is None:
            continue
        new_board, _, ko = played
        position_hash = _fingerprint(new_board)
        if position_hash in seen:
            continue

        evaluated += 1
        unsafe = False

        if nl <= 2:
            outcome = reader.check(
                new_board, p, 1, True, ko, budget=270
            )
            if outcome is True:
                unsafe = True
                previously_endangered = sum(
                    len(groups[g][1]) for g in friends if g in critical
                )
                newly_lost = max(1, new_size - previously_endangered)
                score -= rescue + 6.0 + 3.3 * newly_lost ** 0.85
            elif outcome is None:
                score -= 1.0 + 0.5 * math.sqrt(new_size)
                score -= 0.2 * rescue

        if not unsafe:
            targets = sorted(
                (g for g in enemies - cap_ids
                 if not alive[g] and len(groups[g][2]) <= 3),
                key=lambda g: len(groups[g][1]),
                reverse=True
            )
            for gid in targets[:2]:
                anchor = next(iter(groups[gid][1]))
                if new_board[anchor] != 2:
                    continue
                outcome = reader.check(
                    new_board, anchor, 2, False, ko, budget=190
                )
                if outcome is True:
                    score += 0.65 * _value(len(groups[gid][1]))

        if score > best_score:
            best_score = score
            best_p = p
            best_hash = position_hash

    if best_p is None:
        # A repetition-heavy position can exhaust the shortlist.
        for rec in records:
            p = rec[1]
            played = _play(board, p, 1)
            if played is None:
                continue
            position_hash = _fingerprint(played[0])
            if position_hash not in seen:
                if rec[0] > 0.15:
                    return finish(p, position_hash)
                break
        return finish()

    if best_score <= 0.15:
        return finish()
    return finish(best_p, best_hash)


def policy(
    me: list[tuple[int, int]],
    opponent: list[tuple[int, int]],
    memory: dict
) -> tuple[tuple[int, int], dict]:
    if not isinstance(memory, dict):
        memory = {}
    try:
        return _policy(me, opponent, memory)
    except Exception:
        # Passing is always a legal fallback.
        return (0, 0), memory
