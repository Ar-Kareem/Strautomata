
import time
from collections import deque

_SIZE = 21
_POINTS = tuple(r * _SIZE + c for r in range(1, 20) for c in range(1, 20))
_NEIGHBORS = {
    p: (p - _SIZE, p + 1, p + _SIZE, p - 1)
    for p in _POINTS
}
_DIAGONALS = {
    p: (p - _SIZE - 1, p - _SIZE + 1,
        p + _SIZE - 1, p + _SIZE + 1)
    for p in _POINTS
}
_COORD = {p: divmod(p, _SIZE) for p in _POINTS}
_EDGE = {
    p: min(r, c, 20 - r, 20 - c)
    for p, (r, c) in _COORD.items()
}

_WEIGHTS = (1.5, 1.0, 0.55, 0.30, 0.16, 0.08, 0.035)
_NEAR = {}
for _p in _POINTS:
    _r, _c = _COORD[_p]
    _items = []
    for _dr in range(-6, 7):
        for _dc in range(-6, 7):
            _d = abs(_dr) + abs(_dc)
            if (_d <= 6 and 1 <= _r + _dr <= 19
                    and 1 <= _c + _dc <= 19):
                _items.append(
                    ((_r + _dr) * _SIZE + _c + _dc, _WEIGHTS[_d])
                )
    _NEAR[_p] = tuple(_items)


class _Timeout(Exception):
    pass


def _eye(board, p, color):
    ns = _NEIGHBORS[p]
    if any(board[q] != color and board[q] != 3 for q in ns):
        return False
    bad = sum(board[q] not in (color, 3) for q in _DIAGONALS[p])
    return bad == 0 if any(board[q] == 3 for q in ns) else bad <= 1


class _Group:
    __slots__ = ("color", "stones", "libs", "eyes")

    def __init__(self, color, stones, libs):
        self.color = color
        self.stones = stones
        self.libs = libs
        self.eyes = 0


class _Position:
    __slots__ = ("board", "groups", "ids", "value", "ko", "taken")

    def __init__(self, board, ko=-1, taken=0):
        self.board = board
        self.ko = ko
        self.taken = taken
        ids = [-1] * 441
        groups = []

        for p in _POINTS:
            color = board[p]
            if color == 0 or ids[p] != -1:
                continue

            gi = len(groups)
            ids[p] = gi
            stones = [p]
            liberties = set()
            for s in stones:
                for q in _NEIGHBORS[s]:
                    v = board[q]
                    if v == 0:
                        liberties.add(q)
                    elif v == color and ids[q] == -1:
                        ids[q] = gi
                        stones.append(q)
            groups.append(_Group(color, stones, liberties))

        value = 0.0
        for gi, g in enumerate(groups):
            n = len(g.stones)
            liberties = len(g.libs)

            if liberties <= 6:
                for p in g.libs:
                    if (_eye(board, p, g.color)
                            and all(board[q] == 3 or ids[q] == gi
                                    for q in _NEIGHBORS[p])):
                        g.eyes += 1

            if g.eyes >= 2:
                penalty = 0.0
            elif liberties == 1:
                penalty = 2.5 * n + 2.5
            elif liberties == 2:
                penalty = 0.60 * n + 1.2
            elif liberties == 3:
                penalty = 0.15 * n + 0.25
            elif liberties == 4:
                penalty = 0.035 * n
            else:
                penalty = 0.0

            score = 4.0 * n - penalty + 1.2 * min(2, g.eyes)
            value += score if g.color == 1 else -score

        self.ids = ids
        self.groups = groups
        self.value = value


def _play(pos, p, color, conservative_ko=False):
    board = pos.board
    if board[p] != 0 or p == pos.ko:
        return None

    enemy = 3 - color
    friends = set()
    opponents = set()
    empty_neighbor = False

    for q in _NEIGHBORS[p]:
        if board[q] == 0:
            empty_neighbor = True
        elif board[q] == color:
            friends.add(pos.ids[q])
        elif board[q] == enemy:
            opponents.add(pos.ids[q])

    captured = []
    for gi in opponents:
        g = pos.groups[gi]
        if len(g.libs) == 1:
            captured.extend(g.stones)

    if (not empty_neighbor and not captured
            and not any(len(pos.groups[gi].libs) > 1 for gi in friends)):
        return None

    # Any simple-ko recapture must have this form. Without history,
    # reject the entire form rather than risk returning an illegal move.
    if (conservative_ko and len(captured) == 1
            and not friends and not empty_neighbor):
        return None

    new_board = board.copy()
    new_board[p] = color
    for q in captured:
        new_board[q] = 0

    result = _Position(new_board, taken=len(captured))
    new_group = result.groups[result.ids[p]]
    if not new_group.libs:
        return None

    if (len(captured) == 1 and len(new_group.stones) == 1
            and len(new_group.libs) == 1):
        result.ko = captured[0]

    return result


def _internal_eye(pos, p, color):
    if not _eye(pos.board, p, color):
        return False
    adjacent = {
        pos.ids[q] for q in _NEIGHBORS[p]
        if pos.board[q] == color
    }
    return len(adjacent) == 1


def _distances(board, color):
    distances = [30] * 441
    queue = deque()
    for p in _POINTS:
        if board[p] == color:
            distances[p] = 0
            queue.append(p)
    while queue:
        p = queue.popleft()
        nd = distances[p] + 1
        for q in _NEIGHBORS[p]:
            if board[q] != 3 and distances[q] > nd:
                distances[q] = nd
                queue.append(q)
    return distances


def _strategic_scores(pos, count):
    board = pos.board
    friendly = [0.0] * 441
    enemy = [0.0] * 441

    for g in pos.groups:
        strength = 0.45 if len(g.libs) == 1 else (
            0.75 if len(g.libs) == 2 and g.eyes < 2 else 1.0
        )
        target = friendly if g.color == 1 else enemy
        for p in g.stones:
            for q, w in _NEAR[p]:
                target[q] += w * strength

    df = _distances(board, 1)
    de = _distances(board, 2)
    denominator = [
        friendly[p] + enemy[p] + 0.8 for p in range(441)
    ]
    numerator = [2.0 * enemy[p] + 0.8 for p in range(441)]

    empty_corners = set()
    for rr, cc in ((4, 4), (4, 16), (16, 4), (16, 16)):
        rows = range(1, 8) if rr == 4 else range(13, 20)
        cols = range(1, 8) if cc == 4 else range(13, 20)
        if not any(board[r * _SIZE + c] for r in rows for c in cols):
            empty_corners.add(rr * _SIZE + cc)

    phase = min(1.0, count / 110.0)
    line_values = {
        3: 1.65, 4: 2.10, 5: 0.80, 6: 0.10,
        7: -0.25, 8: -0.45, 9: -0.55, 10: -0.60,
    }
    scores = {}

    for p in _POINTS:
        if board[p]:
            continue

        gain = 0.0
        for q, w in _NEAR[p]:
            if board[q] == 0:
                a = denominator[q]
                gain += w * numerator[q] / (a * (a + w))
        score = 0.27 * gain

        edge = _EDGE[p]
        if edge == 1:
            score += -2.6 + 2.3 * phase
        elif edge == 2:
            score += -1.1 + 1.1 * phase
        else:
            score += line_values[edge] * (1.0 - 0.8 * phase)

        if p in empty_corners:
            score += 6.0

        if df[p] == 1:
            if de[p] >= 4:
                score -= 1.45
            elif de[p] == 3:
                score -= 0.55
        elif df[p] == 3 and de[p] >= 3:
            score += 0.55
        elif df[p] == 4 and de[p] >= 4:
            score += 0.35

        if de[p] == 1 and df[p] >= 3:
            score -= 2.6 if df[p] == 3 else 4.5
        elif de[p] == 2 and df[p] >= 5:
            score -= 1.6
        elif de[p] == 3 and df[p] >= 5 and edge in (3, 4):
            score += 0.7

        if count < 20 and edge > 5 and min(df[p], de[p]) >= 6:
            score -= 1.6

        ns = _NEIGHBORS[p]
        own_ids = {pos.ids[q] for q in ns if board[q] == 1}
        opp_ids = {pos.ids[q] for q in ns if board[q] == 2}
        own_neighbors = sum(board[q] == 1 for q in ns)
        opp_neighbors = sum(board[q] == 2 for q in ns)

        if len(own_ids) > 1:
            score += 0.65 * (len(own_ids) - 1)
        if len(opp_ids) > 1 and df[p] <= 2:
            score += 0.50 * (len(opp_ids) - 1)

        if own_neighbors >= 3 and opp_neighbors == 0:
            score -= 0.9

        if own_neighbors >= 2 and len(own_ids) == 1:
            offsets = (-_SIZE, 1, _SIZE, -1)
            for i in range(4):
                a, b = offsets[i], offsets[(i + 1) % 4]
                if board[p + a] == 1 and board[p + b] == 1:
                    diagonal = board[p + a + b]
                    score -= 0.9 if diagonal == 1 else (
                        0.35 if diagonal == 0 else 0.0
                    )

        if own_neighbors == 0 and opp_neighbors == 0:
            if any(board[q] == 1 for q in _DIAGONALS[p]):
                score += 0.35

        if de[p] <= 3:
            if any(len(pos.groups[gi].libs) <= 3 for gi in own_ids):
                score += 0.35

        scores[p] = score

    return scores


def _forcing_moves(pos, color, depth):
    weights = {}
    for g in pos.groups:
        liberties = len(g.libs)
        if g.eyes >= 2:
            continue
        n = len(g.stones)

        if liberties == 1:
            w = 10.0 + 2.5 * n if g.color == color else 12.0 + 3.0 * n
        elif liberties == 2 and depth > 1:
            w = (1.0 + 0.20 * min(n, 20) if g.color == color
                 else 2.0 + 0.40 * min(n, 20))
        else:
            continue

        for p in g.libs:
            weights[p] = weights.get(p, 0.0) + w

    return weights


def _quiescence(pos, color, depth, alpha, beta, context):
    if time.perf_counter() >= context[2]:
        raise _Timeout

    stand = pos.value if color == 1 else -pos.value
    if depth <= 0 or context[0] >= context[1]:
        return stand
    context[0] += 1

    if stand >= beta:
        return stand
    if stand > alpha:
        alpha = stand

    weights = _forcing_moves(pos, color, depth)
    raw = sorted(weights, key=weights.get, reverse=True)[:10]
    children = []
    sign = 1 if color == 1 else -1

    for p in raw:
        if _internal_eye(pos, p, color):
            continue
        child = _play(pos, p, color)
        if child is None:
            continue
        g = child.groups[child.ids[p]]
        if len(g.libs) == 1 and child.taken == 0:
            continue
        order = sign * (child.value - pos.value) - 4.0
        children.append((order + 0.06 * weights[p], child))

    children.sort(key=lambda item: item[0], reverse=True)
    width = 6 if depth >= 3 else 5
    best = stand

    for _, child in children[:width]:
        if context[0] >= context[1]:
            break

        # Subtract the normal value of placing a stone: tactical search
        # should reward captures and safety, not merely extra search plies.
        value = -_quiescence(
            child, 3 - color, depth - 1,
            -beta - 4.0, -alpha - 4.0, context
        ) - 4.0

        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def _catch(pos, anchor, attacker, turn, depth, budget, deadline):
    """Conservative ladder reader: True means a capture was proved."""
    if time.perf_counter() >= deadline:
        raise _Timeout

    defender = 3 - attacker
    if pos.board[anchor] != defender:
        return True

    g = pos.groups[pos.ids[anchor]]
    if len(g.libs) >= 3 or g.eyes >= 2:
        return False
    if depth <= 0 or budget[0] <= 0:
        return None
    budget[0] -= 1

    choices = set(g.libs)
    if turn == defender:
        adjacent = set()
        for p in g.stones:
            for q in _NEIGHBORS[p]:
                if pos.board[q] == attacker:
                    adjacent.add(pos.ids[q])
        for gi in adjacent:
            enemy_group = pos.groups[gi]
            if len(enemy_group.libs) == 1:
                choices.update(enemy_group.libs)

    children = []
    for p in choices:
        child = _play(pos, p, turn)
        if child is None:
            continue
        if child.board[anchor] != defender:
            if turn == attacker:
                return True
            continue
        child_group = child.groups[child.ids[anchor]]
        if turn == defender and len(child_group.libs) >= 3:
            return False
        children.append((len(child_group.libs), child))

    children.sort(key=lambda item: item[0], reverse=(turn == defender))
    unknown = False

    for _, child in children:
        result = _catch(
            child, anchor, attacker, 3 - turn,
            depth - 1, budget, deadline
        )
        if turn == attacker and result is True:
            return True
        if turn == defender and result is False:
            return False
        if result is None:
            unknown = True

    if unknown:
        return None
    return turn == defender


def _ladder_adjustment(pos, move, deadline):
    adjustment = 0.0
    own = pos.groups[pos.ids[move]]

    if len(own.libs) == 2 and own.eyes < 2:
        caught = _catch(pos, move, 2, 2, 22, [72], deadline)
        if caught is True:
            adjustment -= min(45.0, 2.8 * len(own.stones) + 2.0)

    targets = {
        pos.ids[q] for q in _NEIGHBORS[move]
        if pos.board[q] == 2
    }
    for gi in targets:
        g = pos.groups[gi]
        if len(g.libs) == 1:
            caught = _catch(
                pos, g.stones[0], 1, 2, 22, [64], deadline
            )
            if caught is True:
                adjustment += min(24.0, 2.2 * len(g.stones) + 1.0)

    return adjustment


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]]) -> tuple[int, int]:
    start = time.perf_counter()
    deadline = start + 0.90

    board = [3] * 441
    for p in _POINTS:
        board[p] = 0
    for r, c in me:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * _SIZE + c] = 1
    for r, c in opponent:
        if 1 <= r <= 19 and 1 <= c <= 19:
            board[r * _SIZE + c] = 2

    count = sum(board[p] != 0 for p in _POINTS)
    if count == 0:
        return (4, 4)

    original = _Position(board)
    strategy = _strategic_scores(original, count)
    forcing = _forcing_moves(original, 1, 2)

    ordered = sorted(
        strategy,
        key=lambda p: strategy[p] + 0.38 * forcing.get(p, 0.0),
        reverse=True
    )

    records = []
    for p in ordered[:112]:
        if records and time.perf_counter() >= deadline - 0.025:
            break
        if _internal_eye(original, p, 1):
            continue

        child = _play(original, p, 1, conservative_ko=True)
        if child is None:
            continue

        group = child.groups[child.ids[p]]
        if len(group.libs) == 1 and child.taken == 0:
            continue

        score = strategy[p] + child.value - original.value - 4.0
        # score, strategic score, move, position, shallow score, ladder term
        records.append([score, strategy[p], p, child, score, 0.0])

    if not records:
        return (0, 0)

    records.sort(key=lambda item: item[0], reverse=True)
    best = records[0]
    searched = []
    pass_value = 0.0
    pass_evaluated = False

    try:
        if count > 80:
            context = [0, 45, deadline]
            pass_value = (
                -_quiescence(
                    original, 2, 2, -1e9, 1e9, context
                ) - original.value
            )
            pass_evaluated = True

        for record in records[:20]:
            if len(searched) >= 8 and time.perf_counter() - start > 0.52:
                break
            context = [0, 48, deadline]
            tactical = -_quiescence(
                record[3], 2, 2, -1e9, 1e9, context
            )
            score = record[1] + tactical - original.value - 4.0
            record[0] = score
            record[4] = score
            searched.append(record)
            best = max(searched, key=lambda item: item[0])

        if searched:
            searched.sort(key=lambda item: item[0], reverse=True)

            for record in searched[:8]:
                if time.perf_counter() - start > 0.70:
                    break
                adjustment = _ladder_adjustment(
                    record[3], record[2], deadline
                )
                record[5] = adjustment
                record[0] = record[4] + adjustment
                best = max(searched, key=lambda item: item[0])

            finalists = sorted(
                searched, key=lambda item: item[0], reverse=True
            )[:6]
            deep_results = []

            for record in finalists:
                if time.perf_counter() >= deadline - 0.015:
                    break
                context = [0, 145, deadline]
                tactical = -_quiescence(
                    record[3], 2, 4, -1e9, 1e9, context
                )
                deep = record.copy()
                deep[0] = (
                    record[1] + tactical - original.value - 4.0
                    + record[5]
                )
                deep_results.append(deep)
                if len(deep_results) >= 3:
                    best = max(deep_results, key=lambda item: item[0])

    except _Timeout:
        pass

    if pass_evaluated and searched:
        strongest_shallow = max(record[4] for record in searched)
        if max(best[0], strongest_shallow) <= pass_value + 0.08:
            return (0, 0)

    # Every candidate reaching this point was explicitly checked for
    # occupancy, capture-dependent liberties, suicide, and ko shape.
    return _COORD[best[2]]
