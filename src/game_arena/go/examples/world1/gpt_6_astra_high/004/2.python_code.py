
import math
import time
from collections import deque

_N = 21
_POINTS = tuple(r * _N + c for r in range(1, 20) for c in range(1, 20))
_NB = [()] * (_N * _N)
for _p in _POINTS:
    _NB[_p] = (_p - _N, _p + _N, _p - 1, _p + 1)

_EXP = tuple(math.exp(-0.64 * d) for d in range(17))
_LOCAL = [()] * (_N * _N)
for _p in _POINTS:
    _r, _c = divmod(_p, _N)
    _items = []
    for _dr in range(-5, 6):
        for _dc in range(-5, 6):
            _d = abs(_dr) + abs(_dc)
            if _d <= 5 and 1 <= _r + _dr <= 19 and 1 <= _c + _dc <= 19:
                _items.append(((_r + _dr) * _N + _c + _dc, _EXP[_d]))
    _LOCAL[_p] = tuple(_items)


class _State:
    __slots__ = ("b", "gid", "groups")

    def __init__(self, board):
        self.b = board
        ids = [-1] * 441
        groups = []
        for p in _POINTS:
            color = board[p]
            if color not in (1, -1) or ids[p] != -1:
                continue
            ident = len(groups)
            ids[p] = ident
            stack = [p]
            stones = []
            liberties = set()
            while stack:
                x = stack.pop()
                stones.append(x)
                for q in _NB[x]:
                    v = board[q]
                    if v == 0:
                        liberties.add(q)
                    elif v == color and ids[q] == -1:
                        ids[q] = ident
                        stack.append(q)
            groups.append((color, tuple(stones), frozenset(liberties)))
        self.gid = ids
        self.groups = groups


def _play(state, p, color, strict=False):
    if state.b[p] != 0:
        return None

    b = state.b[:]
    b[p] = color
    enemy_ids = {
        state.gid[q] for q in _NB[p] if state.b[q] == -color
    }
    captured = 0
    for ident in enemy_ids:
        group = state.groups[ident]
        if len(group[2]) == 1:
            captured += len(group[1])
            for q in group[1]:
                b[q] = 0

    if not captured:
        has_liberty = False
        for q in _NB[p]:
            if b[q] == 0:
                has_liberty = True
                break
            if b[q] == color:
                if len(state.groups[state.gid[q]][2]) > 1:
                    has_liberty = True
                    break
        if not has_liberty:
            return None

    result = _State(b)
    group = result.groups[result.gid[p]]
    if not group[2]:
        return None

    # Without history, do not risk an immediate ko recapture.
    if strict and captured == 1 and len(group[1]) == 1 and len(group[2]) == 1:
        return None
    return result, captured


def _eye(board, p, color):
    if board[p] != 0:
        return False
    if any(board[q] not in (color, 2) for q in _NB[p]):
        return False
    diagonals = (p - 22, p - 20, p + 20, p + 22)
    bad = sum(board[q] == -color for q in diagonals)
    edge = any(board[q] == 2 for q in diagonals)
    return bad == 0 if edge else bad <= 1


def _two_eyes(state, group):
    return sum(_eye(state.b, p, group[0]) for p in group[2]) >= 2


def _distances(board, color):
    dist = [16] * 441
    queue = deque()
    for p in _POINTS:
        if board[p] == color:
            dist[p] = 0
            queue.append(p)
    while queue:
        p = queue.popleft()
        nd = dist[p] + 1
        if nd > 12:
            continue
        for q in _NB[p]:
            if dist[q] > nd and board[q] not in (-color, 2):
                dist[q] = nd
                queue.append(q)
    return dist


def _regions(board):
    owner = [0] * 441
    sizes = [0] * 441
    seen = set()
    for p in _POINTS:
        if board[p] != 0 or p in seen:
            continue
        seen.add(p)
        stack = [p]
        region = []
        boundary = 0
        while stack:
            x = stack.pop()
            region.append(x)
            for q in _NB[x]:
                v = board[q]
                if v == 0 and q not in seen:
                    seen.add(q)
                    stack.append(q)
                elif v == 1:
                    boundary |= 1
                elif v == -1:
                    boundary |= 2
        if len(region) <= 40 and boundary in (1, 2):
            color = 1 if boundary == 1 else -1
            for x in region:
                owner[x] = color
                sizes[x] = len(region)
    return owner, sizes


def _positional(state):
    b = state.b
    dm = _distances(b, 1)
    do = _distances(b, -1)
    owner, sizes = _regions(b)
    count = sum(b[p] != 0 for p in _POINTS)
    have_own = any(b[p] == 1 for p in _POINTS)

    strength = [_EXP[d] if d <= 12 else 0.0 for d in dm]
    resistance = [(_EXP[d] if d <= 12 else 0.0) + 0.12 for d in do]
    old_fraction = [
        strength[p] / (strength[p] + resistance[p]) for p in range(441)
    ]

    corner_bonus = [0.0] * 441
    if count < 90:
        scale = max(0.3, 1.0 - max(0, count - 20) / 100.0)
        for flip_r in (False, True):
            for flip_c in (False, True):
                r = 16 if flip_r else 4
                c = 16 if flip_c else 4
                anchor = r * _N + c
                if min(dm[anchor], do[anchor]) >= 5:
                    for rr, cc, value in (
                        (4, 4, 4.0), (3, 4, 2.7), (4, 3, 2.7),
                        (3, 3, 1.8), (4, 5, 0.8), (5, 4, 0.8)
                    ):
                        if flip_r:
                            rr = 20 - rr
                        if flip_c:
                            cc = 20 - cc
                        corner_bonus[rr * _N + cc] += value * scale

    distance_bonus = (
        0.0, 0.10, 0.85, 1.35, 1.15, 0.65, 0.05,
        -0.35, -0.75, -1.0, -1.2, -1.2, -1.2,
        -1.2, -1.2, -1.2, -1.2
    )
    seed = sum((p + 11) * (1 if b[p] == 1 else 3)
               for p in _POINTS if b[p])
    scores = [-1000.0] * 441

    for p in _POINTS:
        if b[p] != 0:
            continue

        gain = 0.0
        for q, influence in _LOCAL[p]:
            if b[q] != 0 or influence <= strength[q]:
                continue
            delta = influence / (influence + resistance[q]) - old_fraction[q]
            if owner[q] == 1:
                delta *= 0.06
            elif owner[q] == -1:
                delta *= 0.20
            gain += delta

        r, c = divmod(p, _N)
        line = min(r, c, 20 - r, 20 - c)
        edge_value = {
            1: -2.6, 2: -0.45, 3: 1.15, 4: 1.20,
            5: 0.60, 6: 0.20
        }.get(line, -0.10)
        phase = 0.30 + 0.70 * max(0.0, 1.0 - count / 140.0)
        if line <= 2 and do[p] <= 2:
            phase *= 0.35

        score = 0.21 * gain + edge_value * phase + corner_bonus[p]
        if have_own:
            score += distance_bonus[dm[p]]

        if do[p] == 1:
            score += 0.25 if dm[p] <= 2 else -3.0
        elif do[p] == 2:
            score += 0.45 if dm[p] <= 3 else -1.8
        elif do[p] == 3:
            score += 0.55
        elif do[p] == 4:
            score += 0.25

        if dm[p] > 3 and do[p] + 3 < dm[p]:
            score -= 1.5

        # Light bonuses for diagonal connections, jumps, and knight's moves.
        score += 0.13 * sum(b[q] == 1 for q in
                            (p - 22, p - 20, p + 20, p + 22))
        for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2)):
            rr, cc = r + dr, c + dc
            if 1 <= rr <= 19 and 1 <= cc <= 19:
                q = rr * _N + cc
                mid = p + (dr // 2) * _N + dc // 2
                if b[q] == 1 and b[mid] == 0:
                    contested = any(b[x] == -1 for x in _NB[mid])
                    score += 0.12 if contested else 0.40

        knight_count = 0
        for dr, dc in ((-2, -1), (-2, 1), (2, -1), (2, 1),
                       (-1, -2), (-1, 2), (1, -2), (1, 2)):
            rr, cc = r + dr, c + dc
            if 1 <= rr <= 19 and 1 <= cc <= 19:
                knight_count += b[rr * _N + cc] == 1
        score += min(0.40, 0.12 * knight_count)

        if owner[p] == 1:
            score -= 5.0 if sizes[p] <= 8 else 2.5
        elif owner[p] == -1 and sizes[p] <= 5:
            score -= 3.5

        score += 0.00003 * ((p * 167 + seed) % 997)
        scores[p] = score
    return scores, dm, do


class _Reader:
    __slots__ = ("deadline", "memo")

    def __init__(self, deadline):
        self.deadline = deadline
        self.memo = {}

    def capture(self, state, anchor, target, turn, budget=190):
        remaining = [budget]
        path = set()
        memo = self.memo
        deadline = self.deadline

        def search(s, player, depth):
            if s.b[anchor] != target:
                return 1

            group = s.groups[s.gid[anchor]]
            liberties = group[2]
            if len(liberties) >= 3:
                return -1
            if player != target and len(liberties) == 1:
                return 1
            if len(liberties) == 2 and _two_eyes(s, group):
                return -1
            if depth <= 0 or remaining[0] <= 0 or time.perf_counter() >= deadline:
                return 0

            h = hash(tuple(s.b))
            if h in path:
                return -1
            key = (h, anchor, target, player, depth)
            if key in memo:
                return memo[key]

            remaining[0] -= 1
            moves = set(liberties)
            if player == target:
                adjacent = set()
                for stone in group[1]:
                    for q in _NB[stone]:
                        if s.b[q] == -target:
                            adjacent.add(s.gid[q])
                for ident in adjacent:
                    enemy = s.groups[ident]
                    if len(enemy[2]) == 1:
                        moves.update(enemy[2])

            moves = sorted(
                moves,
                key=lambda m: sum(s.b[q] == 0 for q in _NB[m]),
                reverse=(player == target)
            )
            wanted = -1 if player == target else 1
            unknown = False
            path.add(h)

            for move in moves:
                played = _play(s, move, player)
                if played is None:
                    continue
                result = search(played[0], -player, depth - 1)
                if result == wanted:
                    path.remove(h)
                    memo[key] = wanted
                    return wanted
                if result == 0:
                    unknown = True

            path.remove(h)
            result = 0 if unknown else -wanted
            if result:
                memo[key] = result
            return result

        return search(state, turn, 42)


def _danger(state, reader=None):
    threatened = []
    for group in state.groups:
        if group[0] != 1 or len(group[2]) > 2:
            continue
        if len(group[2]) == 2 and _two_eyes(state, group):
            continue
        value = 8.5 * len(group[1]) + 2.0
        threatened.append((value, group))

    threatened.sort(key=lambda item: item[0], reverse=True)
    losses = []
    reads = 0
    for value, group in threatened:
        if len(group[2]) <= 1:
            factor = 1.0
        elif reader is None or reads >= 5:
            factor = 0.24
        else:
            reads += 1
            result = reader.capture(state, group[1][0], 1, -1)
            factor = 1.0 if result == 1 else 0.025 if result == -1 else 0.24
        losses.append(value * factor)

    if not losses:
        return 0.0
    largest = max(losses)
    return largest + 0.20 * (sum(losses) - largest)


def _base_score(root, state, p, captured, positional, opponent_distance):
    b = root.b
    friend_ids = {root.gid[q] for q in _NB[p] if b[q] == 1}
    enemy_ids = {root.gid[q] for q in _NB[p] if b[q] == -1}
    group = state.groups[state.gid[p]]
    liberties = len(group[2])

    score = positional[p] + 10.0 * captured
    score += 0.25 if liberties >= 4 else 0.0
    if liberties == 2:
        score -= 0.5
    elif liberties == 1:
        score -= 1.5

    if len(friend_ids) >= 2 and opponent_distance[p] <= 4:
        score += 0.9 * (len(friend_ids) - 1)
    if len(enemy_ids) >= 2 and liberties >= 3:
        score += 0.65 * (len(enemy_ids) - 1)
    if not friend_ids and len(enemy_ids) >= 2:
        score -= 0.8

    for a, d in ((-21, -1), (-21, 1), (21, -1), (21, 1)):
        if b[p + a] == b[p + d] == b[p + a + d] == 1:
            score -= 0.55

    own_neighbors = sum(b[q] == 1 for q in _NB[p])
    if own_neighbors >= 3:
        score -= 0.4
    if own_neighbors >= 2 and len(friend_ids) == 1:
        score -= 0.35

    interest = 0.0
    for ident in enemy_ids:
        old = root.groups[ident]
        anchor = old[1][0]
        if state.b[anchor] != -1:
            continue
        new = state.groups[state.gid[anchor]]
        if len(new[2]) == 1 and len(old[2]) > 1:
            score += 0.7 + 0.23 * math.sqrt(len(old[1]))
            interest += min(6.0, 0.8 * math.sqrt(len(old[1])))
        elif len(new[2]) == 2 and len(old[2]) > 2:
            score += 0.4 + 0.12 * math.sqrt(len(old[1]))

    return score, min(8.0, interest)


def _fork_value(state, reader):
    ataris = [
        g for g in state.groups if g[0] == -1 and len(g[2]) == 1
    ]
    if len(ataris) < 2:
        return 0.0
    ataris.sort(key=lambda g: len(g[1]), reverse=True)
    ataris = ataris[:6]

    replies = set()
    for group in ataris:
        replies.update(group[2])
    for group in state.groups:
        if group[0] == 1 and len(group[2]) == 1:
            replies.update(group[2])

    unavoidable = max(len(g[1]) for g in ataris)
    for reply in replies:
        if time.perf_counter() >= reader.deadline:
            return 0.0
        played = _play(state, reply, -1)
        if played is None:
            continue
        child = played[0]
        largest = 0
        seen = set()
        for old in ataris:
            anchor = old[1][0]
            if child.b[anchor] != -1:
                continue
            ident = child.gid[anchor]
            if ident in seen:
                continue
            seen.add(ident)
            group = child.groups[ident]
            if len(group[2]) == 1:
                largest = max(largest, len(group[1]))
        unavoidable = min(unavoidable, largest)
        if unavoidable == 0:
            return 0.0
    return 7.5 * unavoidable + 1.5


def _future_gain(root, state, p, reader):
    targets = {}
    for q in _NB[p]:
        if root.b[q] != -1:
            continue
        old = root.groups[root.gid[q]]
        anchor = old[1][0]
        if len(old[2]) >= 2 and state.b[anchor] == -1:
            group = state.groups[state.gid[anchor]]
            if len(group[2]) == 1:
                targets[state.gid[anchor]] = group

    forced = []
    groups = sorted(targets.values(), key=lambda g: len(g[1]), reverse=True)
    for group in groups[:3]:
        if time.perf_counter() >= reader.deadline:
            break
        result = reader.capture(state, group[1][0], -1, -1, 170)
        if result == 1:
            forced.append(7.5 * len(group[1]) + 1.5)

    value = 0.0
    if forced:
        largest = max(forced)
        value = largest + 0.25 * (sum(forced) - largest)
    if time.perf_counter() < reader.deadline:
        value = max(value, _fork_value(state, reader))
    return value


def _choose(me, opponent):
    start = time.perf_counter()
    deadline = start + 0.88

    board = [2] * 441
    for p in _POINTS:
        board[p] = 0
    for r, c in me:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * _N + c] = 1
    for r, c in opponent:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * _N + c] = -1

    if not me and not opponent:
        return (4, 4)

    root = _State(board)
    positional, own_distance, opponent_distance = _positional(root)

    preliminary = []
    for p in _POINTS:
        if board[p] != 0 or _eye(board, p, 1):
            continue
        estimate = positional[p]
        adjacent = {
            root.gid[q] for q in _NB[p] if board[q] in (1, -1)
        }
        for ident in adjacent:
            group = root.groups[ident]
            libs = len(group[2])
            size = len(group[1])
            if group[0] == -1:
                if libs == 1:
                    estimate += 10.0 * size
                elif libs == 2:
                    estimate += 0.7 + min(7.0, math.sqrt(size))
            elif libs == 1:
                estimate += 8.5 * size + 2.0
            elif libs == 2 and not _two_eyes(root, group):
                estimate += 0.24 * (8.5 * size + 2.0)
        preliminary.append((estimate, p))

    preliminary.sort(reverse=True)
    candidates = []
    for i, (_, p) in enumerate(preliminary[:128]):
        if i >= 24 and time.perf_counter() - start > 0.28:
            break
        played = _play(root, p, 1, strict=True)
        if played is None:
            continue
        child, captured = played
        base, interest = _base_score(
            root, child, p, captured, positional, opponent_distance
        )
        quick = base - _danger(child) + interest
        candidates.append((quick, base, p, child))

    if not candidates:
        return (0, 0)

    candidates.sort(key=lambda item: item[0], reverse=True)
    candidates = candidates[:18]
    fallback = candidates[0][2]

    reader = _Reader(deadline)
    pass_score = -_danger(root, reader)
    best_score = -float("inf")
    best_move = fallback

    for _, base, p, child in candidates:
        if time.perf_counter() >= deadline:
            break
        score = base - _danger(child, reader)
        score += _future_gain(root, child, p, reader)
        if score > best_score:
            best_score = score
            best_move = p

    if best_score == -float("inf"):
        return divmod(fallback, _N)
    if best_score <= pass_score + 0.12:
        return (0, 0)
    return divmod(best_move, _N)


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]]) -> tuple[int, int]:
    try:
        return _choose(me, opponent)
    except Exception:
        # Passing is a legal fallback even if an unexpected input/runtime
        # issue prevents normal analysis.
        return (0, 0)
