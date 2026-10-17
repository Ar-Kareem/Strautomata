
import math
import time
from collections import deque

SIZE = 19
N = SIZE * SIZE

NEIGHBORS = []
DIAGONALS = []
LINES = []

for p in range(N):
    r, c = divmod(p, SIZE)
    NEIGHBORS.append(tuple(
        rr * SIZE + cc
        for rr, cc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1))
        if 0 <= rr < SIZE and 0 <= cc < SIZE
    ))
    DIAGONALS.append(tuple(
        rr * SIZE + cc
        for rr, cc in (
            (r - 1, c - 1), (r - 1, c + 1),
            (r + 1, c - 1), (r + 1, c + 1)
        )
        if 0 <= rr < SIZE and 0 <= cc < SIZE
    ))
    LINES.append(min(r, c, 18 - r, 18 - c) + 1)

KERNEL = []
KERNEL_SUM = []
for p in range(N):
    r, c = divmod(p, SIZE)
    entries = []
    for dr in range(-4, 5):
        for dc in range(-4, 5):
            d = abs(dr) + abs(dc)
            rr, cc = r + dr, c + dc
            if d <= 6 and 0 <= rr < SIZE and 0 <= cc < SIZE:
                entries.append((rr * SIZE + cc, math.exp(-0.48 * d)))
    KERNEL.append(entries)
    KERNEL_SUM.append(sum(w for _, w in entries))

ENCODING = bytes.maketrans(b"\x00\x01\x02", b"012")
CORNERS = (3 * 19 + 3, 3 * 19 + 15, 15 * 19 + 3, 15 * 19 + 15)
SIDES = (3 * 19 + 9, 9 * 19 + 3, 9 * 19 + 15, 15 * 19 + 9)


def _key(board):
    return bytes(board).translate(ENCODING).decode("ascii")


def _group(board, start):
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
            elif v == color and q not in stones:
                stones.add(q)
                stack.append(q)
    return stones, liberties


def _groups(board):
    ids = [-1] * N
    groups = []
    for start, color in enumerate(board):
        if color == 0 or ids[start] != -1:
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
                if v == 0:
                    liberties.add(q)
                elif v == color and ids[q] == -1:
                    ids[q] = gid
                    stack.append(q)
        groups.append((color, stones, liberties))
    return ids, groups


def _play(board, p, color, previous=None):
    if board[p]:
        return None

    result = board[:]
    result[p] = color
    enemy = 3 - color
    checked = set()

    for q in NEIGHBORS[p]:
        if result[q] == enemy and q not in checked:
            stones, liberties = _group(result, q)
            checked.update(stones)
            if not liberties:
                for s in stones:
                    result[s] = 0

    if not any(result[q] == 0 for q in NEIGHBORS[p]):
        _, liberties = _group(result, p)
        if not liberties:
            return None

    if previous is not None and result == previous:
        return None
    return result


def _distances(board, color):
    distances = [40] * N
    queue = deque()
    for p, v in enumerate(board):
        if v == color:
            distances[p] = 0
            queue.append(p)
    while queue:
        p = queue.popleft()
        nd = distances[p] + 1
        for q in NEIGHBORS[p]:
            if distances[q] > nd:
                distances[q] = nd
                queue.append(q)
    return distances


def _eye(board, p, color):
    if not NEIGHBORS[p] or any(board[q] != color for q in NEIGHBORS[p]):
        return False
    allowance = 1 if len(DIAGONALS[p]) == 4 else 0
    return sum(board[q] != color for q in DIAGONALS[p]) <= allowance


def _small_regions(board):
    """Mark small enclosed regions; large open areas are not called territory."""
    owner = [0] * N
    seen = set()
    for start in range(N):
        if board[start] or start in seen:
            continue
        region = [start]
        seen.add(start)
        stack = [start]
        colors = set()
        while stack:
            p = stack.pop()
            for q in NEIGHBORS[p]:
                if board[q]:
                    colors.add(board[q])
                elif q not in seen:
                    seen.add(q)
                    region.append(q)
                    stack.append(q)
        if len(colors) == 1 and len(region) <= 14:
            color = next(iter(colors))
            for p in region:
                owner[p] = color
    return owner


class _Reader:
    """Conservative, three-valued local capture search."""

    def __init__(self, deadline):
        self.deadline = deadline
        self.nodes = 0
        self.stop = 0

    def query(self, board, target, attacker, turn,
              previous=None, budget=180, depth=28):
        if self.nodes >= 5500 or time.perf_counter() >= self.deadline:
            return None
        self.stop = min(5500, self.nodes + budget)
        return self._search(board, target, attacker, turn, previous, depth)

    def _search(self, board, target, attacker, turn, previous, depth):
        self.nodes += 1
        if self.nodes >= self.stop:
            return None
        if (self.nodes & 15) == 0 and time.perf_counter() >= self.deadline:
            return None

        defender = 3 - attacker
        if board[target] != defender:
            return True

        stones, liberties = _group(board, target)
        if len(liberties) >= 3:
            return False
        if depth <= 0:
            return None

        options = set(liberties)
        if turn == defender:
            checked = set()
            for s in stones:
                for q in NEIGHBORS[s]:
                    if board[q] == attacker and q not in checked:
                        es, el = _group(board, q)
                        checked.update(es)
                        if len(el) == 1:
                            options.update(el)

        # On defense, try the most open escape first.
        moves = sorted(
            options,
            key=lambda p: (
                sum(board[q] == 0 for q in NEIGHBORS[p]),
                len(NEIGHBORS[p])
            ),
            reverse=(turn == defender)
        )

        unknown = False
        legal_count = 0
        for p in moves:
            after = _play(board, p, turn, previous)
            if after is None:
                continue
            legal_count += 1
            answer = self._search(
                after, target, attacker, 3 - turn, board, depth - 1
            )
            if turn == attacker and answer is True:
                return True
            if turn == defender and answer is False:
                return False
            if answer is None:
                unknown = True

        if unknown:
            return None
        if turn == attacker:
            return False
        if legal_count == 0:
            # Passing permits the attacker another attempt without a ko ban.
            if len(liberties) == 1:
                p = next(iter(liberties))
                after = _play(board, p, attacker)
                return after is not None and after[target] != defender
        return True


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]],
           memory: dict) -> tuple[tuple[int, int], dict]:
    started = time.perf_counter()
    reader = _Reader(started + 0.76)

    board = [0] * N
    for r, c in me:
        board[(r - 1) * SIZE + c - 1] = 1
    for r, c in opponent:
        board[(r - 1) * SIZE + c - 1] = 2

    if not isinstance(memory, dict):
        memory = {}
    history = [
        s for s in memory.get("history", [])
        if isinstance(s, str) and len(s) == N
    ]
    historical = set(history)
    current_key = _key(board)
    if current_key not in historical:
        history.append(current_key)
        historical.add(current_key)

    turn_number = int(memory.get("turn", 0)) + 1

    def finish(p, after=None):
        if after is not None:
            k = _key(after)
            if k not in historical:
                history.append(k)
        updated = {"history": history, "turn": turn_number}
        if p is None:
            return (0, 0), updated
        return (p // SIZE + 1, p % SIZE + 1), updated

    if all(board):
        return finish(None)

    ids, groups = _groups(board)
    occupied = sum(v != 0 for v in board)
    own_dist = _distances(board, 1)
    enemy_dist = _distances(board, 2)
    region_owner = _small_regions(board)

    friendly_influence = [0.0] * N
    enemy_influence = [0.0] * N
    for p, color in enumerate(board):
        if color:
            destination = friendly_influence if color == 1 else enemy_influence
            for q, weight in KERNEL[p]:
                destination[q] += weight

    need = [
        0.0 if board[p] else
        1.0 / (1.0 + 1.6 * friendly_influence[p] + 0.9 * enemy_influence[p])
        for p in range(N)
    ]

    # Baseline endangered groups give saving moves appropriate urgency.
    original_lost = {}
    original_risk = {}
    baseline_risk = 0.0

    own_order = sorted(
        (g for g in range(len(groups))
         if groups[g][0] == 1 and len(groups[g][2]) <= 2),
        key=lambda g: (len(groups[g][2]), -len(groups[g][1]))
    )

    for gid in own_order:
        _, stones, liberties = groups[gid]
        if len(liberties) == 1:
            p = next(iter(liberties))
            after = _play(board, p, 2)
            lost = after is not None and after[stones[0]] != 1
        elif time.perf_counter() < started + 0.14:
            lost = reader.query(
                board, stones[0], 2, 2, budget=110, depth=22
            )
        else:
            lost = None

        original_lost[gid] = lost
        risk = 12.0 * len(stones) + 3.0 if lost is True else 0.0
        original_risk[gid] = risk
        baseline_risk += risk

    opening = max(0.0, 1.0 - occupied / 90.0)
    candidates = []

    for p in range(N):
        if board[p]:
            continue

        adjacent_own = set()
        adjacent_enemy = set()
        empty_neighbors = set()

        for q in NEIGHBORS[p]:
            if board[q] == 1:
                adjacent_own.add(ids[q])
            elif board[q] == 2:
                adjacent_enemy.add(ids[q])
            else:
                empty_neighbors.add(q)

        captured_groups = [
            gid for gid in adjacent_enemy if len(groups[gid][2]) == 1
        ]
        captured = [
            s for gid in captured_groups for s in groups[gid][1]
        ]
        capture_count = len(captured)

        liberties = set(empty_neighbors)
        new_size = 1
        for gid in adjacent_own:
            liberties.update(groups[gid][2])
            new_size += len(groups[gid][1])
        liberties.discard(p)

        opened_groups = set()
        for s in captured:
            bordering_new_group = False
            for q in NEIGHBORS[s]:
                if q == p:
                    bordering_new_group = True
                if board[q] == 1:
                    opened_groups.add(ids[q])
                    if ids[q] in adjacent_own:
                        bordering_new_group = True
            if bordering_new_group:
                liberties.add(s)

        liberty_count = len(liberties)
        if liberty_count == 0:
            continue
        if capture_count == 0 and _eye(board, p, 1):
            continue

        f = sum(board[q] == 1 for q in NEIGHBORS[p])
        e = sum(board[q] == 2 for q in NEIGHBORS[p])
        fd = sum(board[q] == 1 for q in DIAGONALS[p])
        ed = sum(board[q] == 2 for q in DIAGONALS[p])

        area = sum(weight * need[q] for q, weight in KERNEL[p])
        area /= KERNEL_SUM[p]
        raw = 5.2 * area + 12.0 * capture_count
        if capture_count:
            raw += 1.3 * len(captured_groups)

        # Shape, contact, cutting and connection.
        raw += 0.45 * fd + 0.20 * ed - 0.80 * f
        if f and e:
            raw += 1.35
        if len(adjacent_own) >= 2:
            raw += 1.65 * (len(adjacent_own) - 1)
        if len(adjacent_enemy) >= 2 and liberty_count >= 3:
            raw += 2.1 * (len(adjacent_enemy) - 1)

        for gid in adjacent_own:
            _, stones, old_liberties = groups[gid]
            old_count = len(old_liberties)
            size_bonus = min(3.0, math.sqrt(len(stones)))
            if old_count == 1 and liberty_count >= 2:
                raw += 2.0 + size_bonus
            elif old_count == 2 and liberty_count >= 3:
                raw += 2.0 + size_bonus
            elif old_count == 3 and liberty_count >= 4:
                raw += 1.25
            elif old_count >= 5 and not e and not capture_count:
                raw -= 0.35

        for gid in adjacent_enemy:
            if gid in captured_groups:
                continue
            _, stones, old_liberties = groups[gid]
            lc = len(old_liberties)
            pressure = min(2.0, 0.5 * math.sqrt(len(stones)))
            if lc == 2:
                raw += 1.8 + pressure
            elif lc == 3:
                raw += 1.25 + 0.6 * pressure
            elif lc == 4:
                raw += 0.45

        if liberty_count == 2:
            raw -= 0.9
        if liberty_count == 1 and not capture_count:
            raw -= 4.5
        if not f and e >= 2 and liberty_count <= 2:
            raw -= 3.0

        # Territorial development, with early preference for third/fourth lines.
        line = LINES[p]
        line_bonus = {
            1: -4.3, 2: -1.9, 3: 2.3, 4: 2.8, 5: 0.7
        }.get(line, -0.65)
        raw += opening * line_bonus

        nearest = min(own_dist[p], enemy_dist[p])
        if p in CORNERS and occupied < 45 and nearest >= 5:
            raw += 10.0 * (1.0 - occupied / 65.0)
        if p in SIDES and occupied < 65 and nearest >= 4:
            raw += 4.0 * (1.0 - occupied / 80.0)

        if own_dist[p] in (2, 3, 4) and enemy_dist[p] >= 2:
            raw += (0.95 if own_dist[p] == 2 else 0.65)
        if own_dist[p] >= 5 and enemy_dist[p] <= 2 and not capture_count:
            raw -= 4.0

        fi, ei = friendly_influence[p], enemy_influence[p]
        if ei > 2.2 * fi + 1.1 and not f and not capture_count:
            raw -= min(6.5, 1.7 * (ei - fi))
        if fi > 2.5 * ei + 1.3 and not e and not capture_count:
            raw -= 2.0
        if region_owner[p] == 1 and not capture_count:
            raw -= 7.5
        elif region_owner[p] == 2 and not capture_count:
            raw -= 7.0

        # Estimate remaining tactical loss to rank moves before deeper reading.
        estimated_risk = 0.0
        for gid, risk in original_risk.items():
            if not risk:
                continue
            if gid in adjacent_own:
                if liberty_count == 2:
                    estimated_risk += 0.65 * risk
            elif gid not in opened_groups:
                estimated_risk += risk

        if liberty_count == 1:
            estimated_risk += 12.0 * new_size + 3.0

        # Stable, very small tie breaker.
        raw += ((p * 1103515245 + occupied * 12345) & 1023) * 0.00001

        estimate = raw + baseline_risk - estimated_risk
        candidates.append((
            estimate, p, raw, captured, adjacent_own, adjacent_enemy,
            opened_groups, liberty_count
        ))

    if not candidates:
        return finish(None)

    candidates.sort(key=lambda item: item[0], reverse=True)
    enemy_dead_cache = {}
    best_score = -float("inf")
    best_move = None
    best_board = None
    best_capture_count = 0
    examined = 0

    # Extra slots allow illegal repeated positions to be discarded harmlessly.
    for candidate in candidates:
        if examined >= 26:
            break
        if best_move is not None and time.perf_counter() >= started + 0.91:
            break

        _, p, raw, captured, own_adj, enemy_adj, opened, new_lc = candidate

        after = board[:]
        after[p] = 1
        for s in captured:
            after[s] = 0

        if _key(after) in historical:
            continue

        examined += 1
        new_ids, new_groups = _groups(after)
        remaining_risk = 0.0

        own_weak = [
            (gid, g) for gid, g in enumerate(new_groups)
            if g[0] == 1 and len(g[2]) <= 2
        ]
        own_weak.sort(
            key=lambda item: (
                0 if item[0] == new_ids[p] else 1,
                len(item[1][2]),
                -len(item[1][1])
            )
        )

        for gid, (_, stones, liberties) in own_weak:
            if len(liberties) == 1:
                reply = _play(after, next(iter(liberties)), 2, board)
                lost = reply is not None and reply[stones[0]] != 1
            else:
                old_gid = next(
                    (ids[s] for s in stones if s != p and ids[s] >= 0), -1
                )
                affected = (
                    gid == new_ids[p] or old_gid in opened or
                    any(
                        abs(q // 19 - p // 19) + abs(q % 19 - p % 19) <= 3
                        for q in liberties
                    )
                )
                if affected:
                    lost = reader.query(
                        after, stones[0], 2, 2, previous=board,
                        budget=240 if gid == new_ids[p] else 140,
                        depth=30
                    )
                    if lost is None and old_gid not in own_adj:
                        lost = original_lost.get(old_gid)
                else:
                    lost = original_lost.get(old_gid)

                if lost is not True:
                    remaining_risk += min(2.5, 0.5 + 0.4 * math.sqrt(len(stones)))

            if lost is True:
                remaining_risk += 12.0 * len(stones) + 3.0

        score = raw + baseline_risk - remaining_risk

        # Reward genuine nets/ladders, not merely an easily answered atari.
        if score >= best_score - 35.0:
            for old_gid in enemy_adj:
                _, old_stones, old_liberties = groups[old_gid]
                anchor = old_stones[0]
                if after[anchor] != 2:
                    continue
                _, stones, liberties = new_groups[new_ids[anchor]]
                if len(liberties) > 2:
                    continue

                killed = reader.query(
                    after, anchor, 1, 2, previous=board,
                    budget=160, depth=26
                )
                if killed is not True:
                    continue

                if old_gid not in enemy_dead_cache:
                    if len(old_liberties) >= 3:
                        enemy_dead_cache[old_gid] = False
                    else:
                        enemy_dead_cache[old_gid] = reader.query(
                            board, anchor, 1, 2, budget=100, depth=22
                        )
                if enemy_dead_cache[old_gid] is not True:
                    score += min(35.0, 7.0 * len(stones) + 1.0)
                else:
                    score += 0.6

        if score > best_score:
            best_score = score
            best_move = p
            best_board = after
            best_capture_count = len(captured)

    if best_move is None:
        return finish(None)

    if occupied >= 90 and best_score < -0.4 and best_capture_count == 0:
        return finish(None)

    return finish(best_move, best_board)
