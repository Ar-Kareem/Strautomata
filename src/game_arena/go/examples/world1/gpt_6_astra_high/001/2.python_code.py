
import math
import time
from collections import deque

_SIZE = 19
_STRIDE = 21
_POINTS = tuple(r * 21 + c for r in range(1, 20) for c in range(1, 20))
_NB = [()] * 441
_DIAG = [()] * 441
_LINE = [0] * 441
_LOCAL = [[] for _ in range(441)]

for _p in _POINTS:
    _r, _c = divmod(_p, 21)
    _NB[_p] = (_p - 21, _p + 21, _p - 1, _p + 1)
    _DIAG[_p] = (_p - 22, _p - 20, _p + 20, _p + 22)
    _LINE[_p] = min(_r, _c, 20 - _r, 20 - _c)
    for _dr in range(-6, 7):
        for _dc in range(-6, 7):
            _d = abs(_dr) + abs(_dc)
            _rr, _cc = _r + _dr, _c + _dc
            if _d <= 6 and 1 <= _rr <= 19 and 1 <= _cc <= 19:
                _w = (1.6, 1.0, .55, .30, .16, .085, .045)[_d]
                _LOCAL[_p].append((_rr * 21 + _cc, _w))

_CORNERS = ((4, 4), (4, 16), (16, 4), (16, 16))
_SIDES = ((4, 10), (10, 4), (10, 16), (16, 10))


def _chain(board, start):
    color = board[start]
    stones = [start]
    seen = {start}
    liberties = set()
    for p in stones:
        for q in _NB[p]:
            v = board[q]
            if v == 0:
                liberties.add(q)
            elif v == color and q not in seen:
                seen.add(q)
                stones.append(q)
    return stones, liberties


def _play(board, p, color):
    if board[p] != 0:
        return None
    other = 3 - color
    b = board[:]
    b[p] = color
    captured = []
    checked = set()

    for q in _NB[p]:
        if b[q] == other and q not in checked:
            stones, liberties = _chain(b, q)
            checked.update(stones)
            if not liberties:
                captured.extend(stones)
                for x in stones:
                    b[x] = 0

    stones, liberties = _chain(b, p)
    if not liberties:
        return None

    ko_shape = (
        len(captured) == 1 and len(stones) == 1 and len(liberties) == 1
    )
    return b, stones, liberties, captured, ko_shape


class _Group:
    __slots__ = ("color", "stones", "libs", "alive")

    def __init__(self, color, stones, libs):
        self.color = color
        self.stones = stones
        self.libs = libs
        self.alive = False


def _groups(board):
    ids = [-1] * 441
    groups = []
    for p in _POINTS:
        if board[p] in (1, 2) and ids[p] == -1:
            stones, libs = _chain(board, p)
            k = len(groups)
            for q in stones:
                ids[q] = k
            groups.append(_Group(board[p], stones, libs))
    return ids, groups


def _true_eye(board, p, color):
    if any(board[q] not in (color, 3) for q in _NB[p]):
        return False
    bad = sum(board[q] == 3 - color for q in _DIAG[p])
    edge = any(board[q] == 3 for q in _DIAG[p])
    return bad == 0 if edge else bad <= 1


def _territories(board, ids, groups):
    owner = [0] * 441
    seen = bytearray(441)
    eyes = [0] * len(groups)

    for p in _POINTS:
        if board[p] or seen[p]:
            continue
        region = [p]
        seen[p] = 1
        boundary = set()
        colors = set()
        for x in region:
            for q in _NB[x]:
                v = board[q]
                if v == 0:
                    if not seen[q]:
                        seen[q] = 1
                        region.append(q)
                elif v != 3:
                    boundary.add(ids[q])
                    colors.add(v)

        if len(colors) == 1:
            color = next(iter(colors))
            if len(region) <= 40:
                for x in region:
                    owner[x] = color
            if len(boundary) == 1 and len(region) <= 10:
                k = next(iter(boundary))
                if len(region) >= 5:
                    eyes[k] += 2
                elif len(region) >= 2 or _true_eye(board, p, color):
                    eyes[k] += 1

    for k, g in enumerate(groups):
        g.alive = eyes[k] >= 2
    return owner


def _distances(board, color):
    distance = [40] * 441
    queue = deque()
    for p in _POINTS:
        if board[p] == color:
            distance[p] = 0
            queue.append(p)
    while queue:
        p = queue.popleft()
        d = distance[p] + 1
        for q in _NB[p]:
            if board[q] != 3 and distance[q] > d:
                distance[q] = d
                queue.append(q)
    return distance


class _Reader:
    """Local alternating capture search; 1=caught, -1=escape, 0=unknown."""
    def __init__(self, deadline):
        self.deadline = deadline
        self.cache = {}
        self.nodes = 0
        self.limit = 0
        self.stop = deadline

    def read(self, board, anchor, color, attack=True,
             limit=220, depth=44, until=None):
        self.nodes = 0
        self.limit = limit
        self.stop = self.deadline if until is None else min(until, self.deadline)
        return self._solve(board, anchor, color, attack, depth)

    def _solve(self, board, anchor, color, attack, depth):
        if board[anchor] != color:
            return 1
        self.nodes += 1
        if self.nodes > self.limit or time.perf_counter() >= self.stop:
            return 0

        stones, libs = _chain(board, anchor)
        if len(libs) >= 3:
            return -1
        if not libs:
            return 1
        if depth <= 0:
            return 0

        key = (bytes(board), anchor, color, attack)
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        moves = set(libs)
        if not attack:
            checked = set()
            for p in stones:
                for q in _NB[p]:
                    if board[q] == 3 - color and q not in checked:
                        enemy, elibs = _chain(board, q)
                        checked.update(enemy)
                        if len(elibs) == 1:
                            moves.update(elibs)
                        elif len(libs) == 2 and len(elibs) == 2:
                            moves.update(elibs)

        moves = sorted(
            moves,
            key=lambda p: sum(board[q] == 0 for q in _NB[p]),
            reverse=True,
        )
        player = 3 - color if attack else color
        unknown = False

        for p in moves:
            result = _play(board, p, player)
            if result is None:
                continue
            if result[4]:
                unknown = True
                continue
            value = self._solve(result[0], anchor, color, not attack, depth - 1)
            if attack and value == 1:
                self.cache[key] = 1
                return 1
            if not attack and value == -1:
                self.cache[key] = -1
                return -1
            if value == 0:
                unknown = True

        value = 0 if unknown else (-1 if attack else 1)
        if value:
            self.cache[key] = value
        return value


class _Move:
    __slots__ = (
        "p", "board", "stones", "libs", "score", "friends",
        "saved", "attacks", "risk", "lowpen", "double"
    )


def _immediate_loss(board, anchors):
    moves = set()
    visited = set()
    for anchor in anchors:
        if board[anchor] != 2 or anchor in visited:
            continue
        stones, libs = _chain(board, anchor)
        visited.update(stones)
        if len(libs) == 1:
            moves.update(libs)

    loss = 0
    for p in moves:
        result = _play(board, p, 1)
        if result is not None and not result[4]:
            loss = max(loss, len(result[3]))
    return loss


def _double_threat(board, anchors, deadline):
    replies = set()
    checked = set()
    for anchor in anchors:
        if board[anchor] != 2:
            continue
        stones, libs = _chain(board, anchor)
        replies.update(libs)
        for p in stones:
            for q in _NB[p]:
                if board[q] == 1 and q not in checked:
                    enemy, elibs = _chain(board, q)
                    checked.update(enemy)
                    if len(elibs) == 1:
                        replies.update(elibs)

    best = _immediate_loss(board, anchors)
    for p in replies:
        if time.perf_counter() >= deadline:
            return 0
        result = _play(board, p, 2)
        if result is None:
            continue
        if result[4]:
            return 0
        best = min(best, _immediate_loss(result[0], anchors))
        if best == 0:
            break
    return best


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]]) -> tuple[int, int]:
    start = time.perf_counter()
    deadline = start + .87

    board = bytearray([3]) * 441
    for p in _POINTS:
        board[p] = 0
    for r, c in me:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * 21 + c] = 1
    for r, c in opponent:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * 21 + c] = 2

    total = sum(board[p] != 0 for p in _POINTS)
    if total == 0:
        return (4, 4)
    if total == 361:
        return (0, 0)

    ids, groups = _groups(board)
    owner = _territories(board, ids, groups)
    dm = _distances(board, 1)
    do = _distances(board, 2)
    my_inf = [0.0] * 441
    op_inf = [0.0] * 441
    for p in _POINTS:
        if board[p] in (1, 2):
            field = my_inf if board[p] == 1 else op_inf
            for q, weight in _LOCAL[p]:
                field[q] += weight

    reader = _Reader(deadline)
    risk = [False] * len(groups)
    urgency = [0.0] * len(groups)

    for k, g in enumerate(groups):
        if g.color == 1 and len(g.libs) == 1:
            risk[k] = True
            urgency[k] = 8.0 * len(g.stones) + 2.0

    weak = sorted(
        (k for k, g in enumerate(groups)
         if g.color == 1 and len(g.libs) == 2 and not g.alive),
        key=lambda k: len(groups[k].stones), reverse=True,
    )
    for k in weak:
        if time.perf_counter() >= start + .16:
            break
        g = groups[k]
        if reader.read(board, g.stones[0], 1, True, 300,
                       until=start + .16) == 1:
            risk[k] = True
            urgency[k] = 7.0 * len(g.stones) + 1.0

    opening = max(0.0, 1.0 - total / 120.0)
    empty_corners = [
        (r, c) for r, c in _CORNERS
        if min(dm[r * 21 + c], do[r * 21 + c]) >= 5
    ]
    empty_sides = [
        (r, c) for r, c in _SIDES
        if total < 70 and min(dm[r * 21 + c], do[r * 21 + c]) >= 4
    ]
    quiet_spacing = (-2.0, -1.4, -.3, .7, 1.7, 1.6, 1.0, .4)
    fight_spacing = (-2.0, .15, 1.0, 1.1, .7, .1, -.5, -.8)
    edge_early = (0, -5.0, -2.0, 1.0, 1.25, .15, -.4)
    edge_late = (0, -.8, .05, .4, .4, .25, .2)
    moves = []

    for p in _POINTS:
        if board[p] != 0:
            continue
        result = _play(board, p, 1)
        if result is None or result[4]:
            continue

        b, stones, libs, captured, _ = result
        nlibs = len(libs)
        r, c = divmod(p, 21)
        friends = {ids[q] for q in _NB[p] if board[q] == 1}
        enemies = {ids[q] for q in _NB[p] if board[q] == 2}
        captured_ids = {ids[q] for q in captured}
        dmy, dop = dm[p], do[p]
        mi, oi = my_inf[p], op_inf[p]
        line = min(_LINE[p], 6)

        score = .15 + opening * edge_early[line]
        score += (1.0 - opening) * edge_late[line]
        spacing = quiet_spacing if dop >= 5 else fight_spacing
        score += spacing[min(dmy, 7)] if dmy <= 7 else -.9
        if not me:
            score += .9

        if dop == 3:
            score += 1.0
        elif dop == 4:
            score += .65
        elif dop == 2:
            score += .35 if dmy <= 3 else -.7
        elif dop == 1 and dmy >= 3:
            score -= 2.5

        score += 1.3 * min(mi, oi) / (max(mi, oi) + .15)
        if dmy <= 2 and dop >= 6:
            score -= 1.0
        if mi > 1.8 and oi < .25:
            score -= 1.7
        if oi > 2.0 * mi + .65 and dmy >= 3:
            score -= 2.0
        if dmy >= 5 and dop <= 2:
            score -= 2.3
        if _LINE[p] >= 6 and total < 45 and dmy >= 4:
            score -= 1.0

        if owner[p] == 1:
            score -= 8.0
        elif owner[p] == 2 and dmy > 1:
            score -= 5.0
        if not captured and _true_eye(board, p, 1):
            score -= 20.0

        for rr, cc in empty_corners:
            d2 = (r - rr) ** 2 + (c - cc) ** 2
            score += 7.5 * math.exp(-d2 / 3.2)
        for rr, cc in empty_sides:
            d2 = (r - rr) ** 2 + (c - cc) ** 2
            score += 1.2 * math.exp(-d2 / 7.0)

        score += .65 * max(0, len(friends) - 1)
        if len(friends) >= 2 and dop <= 2:
            score += .8
        if len(enemies) >= 2:
            score += 1.2 if dmy <= 2 and nlibs >= 3 else .3
        adjacent_friends = sum(board[q] == 1 for q in _NB[p])
        if len(friends) == 1 and adjacent_friends >= 2:
            score -= .5 * (adjacent_friends - 1)

        score += 10.0 * len(captured) + .5 * len(captured_ids)

        additions = {}
        for x in captured:
            for q in _NB[x]:
                if board[q] == 1 and ids[q] not in friends:
                    additions.setdefault(ids[q], set()).add(x)

        impacted = friends | additions.keys()
        saved = []
        for k in impacted:
            g = groups[k]
            new_count = nlibs if k in friends else len(g.libs | additions[k])
            old_count = len(g.libs)
            if risk[k] and new_count >= 2:
                bonus = urgency[k] * (1.0 if new_count >= 3 else .82)
                score += bonus
                saved.append((k, bonus, k in friends, new_count))
            elif not g.alive:
                gain = max(0, min(3, new_count - old_count))
                if old_count == 2:
                    score += gain * (.9 + .13 * math.sqrt(len(g.stones)))
                elif old_count == 3:
                    score += .45 * min(gain, 2)

        risk_size = sum(len(groups[k].stones) for k in friends if risk[k])
        lowpen = 0.0
        if nlibs == 1:
            lowpen = 10.0 * (len(stones) - risk_size) + 3.0
        elif nlibs == 2 and dop <= 2:
            lowpen = .8 + .35 * math.sqrt(len(stones))
        score -= lowpen

        attacks = []
        ataris = []
        for k in enemies - captured_ids:
            g = groups[k]
            remaining = g.libs - {p}
            count = len(remaining)
            bonus = 0.0
            if count == 1:
                bonus = 1.6 + min(2.8, .55 * math.sqrt(len(g.stones)))
                ataris.append((k, next(iter(remaining))))
            elif count == 2:
                bonus = .65 + .25 * math.sqrt(len(g.stones))
            elif count == 3:
                bonus = .25
            if g.alive:
                bonus *= .2
            score += bonus
            if count <= 2:
                attacks.append((k, bonus, count))

        double = 0.0
        if len(ataris) >= 2 and len({q for _, q in ataris}) >= 2:
            sizes = sorted(len(groups[k].stones) for k, _ in ataris)
            double = 5.0 * sizes[-2]
            score += double

        score += ((p * 2654435761 + total * 97) & 1023) * .000006

        move = _Move()
        move.p, move.board = p, b
        move.stones, move.libs = stones, libs
        move.score, move.friends = score, friends
        move.saved, move.attacks = saved, attacks
        move.risk, move.lowpen, move.double = risk_size, lowpen, double
        moves.append(move)

    if not moves:
        return (0, 0)

    moves.sort(key=lambda m: m.score, reverse=True)
    shortlist = moves[:20]
    included = {m.p for m in shortlist}
    tactical = sorted(
        (m for m in moves if m.attacks and m.p not in included),
        key=lambda m: m.score + min(
            8.0, 1.5 * math.sqrt(max(
                len(groups[k].stones) for k, _, _ in m.attacks
            ))
        ),
        reverse=True,
    )
    shortlist.extend(tactical[:6])

    best_move = moves[0]
    best_score = -float("inf")
    refined = False

    for index, move in enumerate(shortlist):
        if time.perf_counter() >= deadline:
            break
        score = move.score - move.double
        nlibs = len(move.libs)
        outcome = -1

        if nlibs == 2:
            outcome = reader.read(move.board, move.p, 1, True, 280)
        elif (nlibs == 3 and index < 7 and len(move.stones) >= 3
              and do[move.p] <= 1):
            # One additional attacking move detects small nets and squeezes.
            for q in move.libs:
                if time.perf_counter() >= deadline:
                    break
                reply = _play(move.board, q, 2)
                if reply is None or reply[4]:
                    continue
                if reader.read(reply[0], move.p, 1, False, 150) == 1:
                    outcome = 1
                    break

        if outcome == 1 and nlibs >= 2:
            score += move.lowpen
            score -= 10.0 * (len(move.stones) - move.risk) + 2.0
            score -= sum(bonus for _, bonus, merged, _ in move.saved if merged)
        elif outcome == 0:
            score -= min(4.0, .4 * math.sqrt(len(move.stones)))
        elif outcome == -1 and nlibs == 2:
            for k, bonus, merged, _ in move.saved:
                if merged:
                    score += urgency[k] - bonus

        for k, bonus, merged, count in move.saved:
            if not merged and count == 2:
                status = reader.read(
                    move.board, groups[k].stones[0], 1, True, 160
                )
                if status == 1:
                    score -= bonus
                elif status == -1:
                    score += urgency[k] - bonus

        forced_bonus = 0.0
        anchors = []
        attacks = sorted(
            move.attacks,
            key=lambda item: len(groups[item[0]].stones),
            reverse=True,
        )
        for k, bonus, count in attacks[:4]:
            g = groups[k]
            if count == 1:
                anchors.append(g.stones[0])
            if g.alive or time.perf_counter() >= deadline:
                continue
            status = reader.read(
                move.board, g.stones[0], 2, False,
                210 if count == 1 else 140,
            )
            if status == 1:
                forced_bonus += max(0.0, 8.0 * len(g.stones) + 1.0 - bonus)

        double_value = 0.0
        if len(anchors) >= 2 and time.perf_counter() < deadline:
            double_value = 8.0 * _double_threat(move.board, anchors, deadline)
        score += max(forced_bonus, double_value)

        if score > best_score:
            best_score = score
            best_move = move
        refined = True

    if not refined:
        best_score = best_move.score

    if total > 60 and best_score < -.25:
        return (0, 0)

    return divmod(best_move.p, 21)
