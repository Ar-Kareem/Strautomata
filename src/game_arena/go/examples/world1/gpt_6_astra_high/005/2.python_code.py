
import time

_SIZE = 19
_STRIDE = 21
_WALL = 2
_POINTS = tuple(
    r * _STRIDE + c
    for r in range(1, 20)
    for c in range(1, 20)
)
_NEIGHBORS = {
    p: (p - 21, p + 21, p - 1, p + 1)
    for p in _POINTS
}
_DIAGONALS = {
    p: (p - 22, p - 20, p + 20, p + 22)
    for p in _POINTS
}
_EDGE = {}
_CORNER_BONUS = {}
_SIDE_BONUS = {}
_KERNEL = {}

_weights = (1.0, 0.62, 0.35, 0.18, 0.09, 0.04, 0.015)
_corners = ((4, 4), (4, 16), (16, 4), (16, 16))
_sides = ((4, 10), (10, 4), (10, 16), (16, 10))

for _p in _POINTS:
    _r, _c = divmod(_p, 21)
    _EDGE[_p] = min(_r, _c, 20 - _r, 20 - _c)
    _d = min(abs(_r - a) + abs(_c - b) for a, b in _corners)
    _CORNER_BONUS[_p] = 0.80 * max(0.0, 1.0 - _d / 5.0)
    _d = min(abs(_r - a) + abs(_c - b) for a, b in _sides)
    _SIDE_BONUS[_p] = 0.28 * max(0.0, 1.0 - _d / 4.0)

    _entries = []
    for _dr in range(-6, 7):
        _rr = _r + _dr
        if not 1 <= _rr <= 19:
            continue
        _reach = 6 - abs(_dr)
        for _dc in range(-_reach, _reach + 1):
            _cc = _c + _dc
            if 1 <= _cc <= 19:
                _entries.append(
                    (_rr * 21 + _cc, _weights[abs(_dr) + abs(_dc)])
                )
    _KERNEL[_p] = tuple(_entries)

_HISTORY = set()
_INF = 1.0e30


class _Timeout(Exception):
    pass


def _check_time(deadline):
    if time.perf_counter() >= deadline:
        raise _Timeout


def _is_eye(board, p, color):
    for q in _NEIGHBORS[p]:
        if board[q] != color and board[q] != _WALL:
            return False
    bad = 0
    edge = False
    for q in _DIAGONALS[p]:
        value = board[q]
        if value == _WALL:
            edge = True
        elif value != color:
            bad += 1
    return bad == 0 if edge else bad <= 1


class _Position:
    __slots__ = (
        "board", "field", "gid", "groups", "n",
        "plus_value", "minus_value", "ko", "cache", "regions"
    )

    def __init__(self, board, field=None, ko=0):
        self.board = board
        self.ko = ko
        self.cache = {}
        self.regions = None

        gids = [-1] * 441
        groups = []
        material = 0
        count = 0

        for p in _POINTS:
            color = board[p]
            if color == 0:
                continue
            material += color
            count += 1
            if gids[p] != -1:
                continue

            number = len(groups)
            gids[p] = number
            stack = [p]
            stones = []
            liberties = set()

            while stack:
                q = stack.pop()
                stones.append(q)
                for z in _NEIGHBORS[q]:
                    value = board[z]
                    if value == 0:
                        liberties.add(z)
                    elif value == color and gids[z] == -1:
                        gids[z] = number
                        stack.append(z)

            groups.append((color, tuple(stones), frozenset(liberties)))

        self.gid = gids
        self.groups = groups
        self.n = count

        if field is None:
            field = [0.0] * 441
            for p in _POINTS:
                color = board[p]
                if color:
                    for q, weight in _KERNEL[p]:
                        field[q] += color * weight
        self.field = field

        control = 0.0
        for p in _POINTS:
            color = board[p]
            if color:
                control += color
            else:
                strength = field[p]
                control += strength / (0.70 + abs(strength))

        base = 0.55 * material + 0.32 * control
        plus = base
        minus = base

        for color, stones, liberties in groups:
            size = len(stones)
            count_lib = len(liberties)

            if count_lib == 1:
                defender_risk = 0.45 * size + 0.65
                attacker_risk = 0.95 * size + 1.10
                if color == 1:
                    plus -= defender_risk
                    minus -= attacker_risk
                else:
                    plus += attacker_risk
                    minus += defender_risk
            elif count_lib == 2:
                eyes = sum(_is_eye(board, p, color) for p in liberties)
                risk = 0.0 if eyes >= 2 else 0.12 * size + 0.45
                plus -= color * risk
                minus -= color * risk
            elif count_lib == 3:
                risk = 0.025 * size + 0.10
                plus -= color * risk
                minus -= color * risk

        self.plus_value = plus
        self.minus_value = minus

    def value(self, turn):
        return self.plus_value if turn == 1 else self.minus_value

    def region_map(self):
        if self.regions is not None:
            return self.regions

        board = self.board
        seen = set()
        result = {}

        for start in _POINTS:
            if board[start] != 0 or start in seen:
                continue

            stack = [start]
            seen.add(start)
            points = []
            colors = set()
            boundary = set()

            while stack:
                p = stack.pop()
                points.append(p)
                for q in _NEIGHBORS[p]:
                    value = board[q]
                    if value == 0:
                        if q not in seen:
                            seen.add(q)
                            stack.append(q)
                    elif value != _WALL:
                        colors.add(value)
                        boundary.add(self.gid[q])

            if len(colors) == 1:
                owner = next(iter(colors))
                size = len(points)
                healthy = all(
                    len(self.groups[g][2]) >= 3 for g in boundary
                )
                information = (owner, size, healthy)
                for p in points:
                    result[p] = information

        self.regions = result
        return result


def _play(position, p, color):
    if p == 0:
        return position

    board = position.board
    if board[p] != 0 or p == position.ko:
        return None

    friends = set()
    enemies = set()
    has_air = False

    for q in _NEIGHBORS[p]:
        value = board[q]
        if value == 0:
            has_air = True
        elif value == color:
            friends.add(position.gid[q])
        elif value == -color:
            enemies.add(position.gid[q])

    captured = []
    for g in enemies:
        group = position.groups[g]
        if len(group[2]) == 1:
            captured.extend(group[1])

    if not has_air and not captured:
        if not any(len(position.groups[g][2]) > 1 for g in friends):
            return None

    new_board = board.copy()
    new_board[p] = color
    for q in captured:
        new_board[q] = 0

    field = position.field.copy()
    for q, weight in _KERNEL[p]:
        field[q] += color * weight
    for stone in captured:
        for q, weight in _KERNEL[stone]:
            field[q] += color * weight

    child = _Position(new_board, field)
    group = child.groups[child.gid[p]]

    if not group[2]:
        return None

    if len(captured) == 1 and len(group[1]) == 1 and len(group[2]) == 1:
        child.ko = captured[0]

    return child


def _candidates(position, color, deadline):
    board = position.board
    groups = position.groups
    gids = position.gid
    regions = position.region_map()
    opening = max(0.0, 1.0 - position.n / 95.0)
    result = []

    for index, p in enumerate(_POINTS):
        if index % 64 == 0:
            _check_time(deadline)
        if board[p] != 0 or p == position.ko:
            continue

        friends = set()
        enemies = set()
        empty_neighbors = []
        own_adjacent = 0
        enemy_adjacent = 0

        for q in _NEIGHBORS[p]:
            value = board[q]
            if value == color:
                friends.add(gids[q])
                own_adjacent += 1
            elif value == -color:
                enemies.add(gids[q])
                enemy_adjacent += 1
            elif value == 0:
                empty_neighbors.append(q)

        captured = sum(
            len(groups[g][1]) for g in enemies if len(groups[g][2]) == 1
        )
        saved = sum(
            len(groups[g][1]) for g in friends if len(groups[g][2]) == 1
        )

        if not empty_neighbors and not captured:
            if not any(len(groups[g][2]) > 1 for g in friends):
                continue

        if not captured and not saved and _is_eye(board, p, color):
            continue

        region = regions.get(p)
        if region is not None and not captured and not saved:
            owner, size, healthy = region
            if owner == color and size <= 60:
                continue
            if owner == -color and size <= 8 and healthy:
                continue

        own_diagonal = sum(board[q] == color for q in _DIAGONALS[p])
        prior = -0.025
        edge = _EDGE[p]

        if edge == 1:
            prior -= 0.24 + 0.85 * opening
        elif edge == 2:
            prior -= 0.12 + 0.45 * opening
        elif edge == 3:
            prior += 0.13 + 0.15 * opening
        elif edge == 4:
            prior += 0.12 + 0.25 * opening
        elif edge == 5:
            prior += 0.08 * opening

        prior += opening * (_CORNER_BONUS[p] + _SIDE_BONUS[p])

        if len(friends) > 1:
            prior += 0.26 * (len(friends) - 1)
        if len(enemies) > 1 and own_adjacent + own_diagonal:
            prior += 0.15 * (len(enemies) - 1)

        if own_adjacent == 0 and own_diagonal:
            prior += 0.13

        if own_adjacent >= 2 and not enemy_adjacent and not captured:
            prior -= 0.18 * (own_adjacent - 1)

        if enemy_adjacent and own_adjacent + own_diagonal == 0:
            prior -= 0.20 + 0.25 * opening

        if not captured and not saved:
            for a, b in ((-21, -1), (-21, 1), (21, -1), (21, 1)):
                if (
                    board[p + a] == color
                    and board[p + b] == color
                    and board[p + a + b] == color
                ):
                    prior -= 0.32

        local_field = color * position.field[p]
        prior -= 0.10 * max(0.0, local_field - 1.5)

        expansion = 4.0 / (1.0 + 0.80 * max(0.0, local_field))
        if not own_adjacent and not own_diagonal:
            expansion -= 0.65 * max(0.0, -local_field)

        tactical = 2.1 * captured
        if captured:
            tactical += 0.8
        tactical += 0.90 * saved

        for g in enemies:
            if len(groups[g][2]) == 2:
                tactical += 0.35 + 0.13 * len(groups[g][1])
        for g in friends:
            if len(groups[g][2]) == 2:
                tactical += 0.12 + 0.05 * len(groups[g][1])

        if not captured and len(empty_neighbors) <= 1:
            liberties = set(empty_neighbors)
            size = 1
            for g in friends:
                liberties.update(groups[g][2])
                size += len(groups[g][1])
            liberties.discard(p)
            if len(liberties) == 1:
                prior -= 0.45 + 0.25 * size
                tactical -= 0.90 * size

        rank = prior + expansion + tactical
        result.append((rank, prior, p))

    result.sort(key=lambda item: item[0], reverse=True)
    return result


def _ordered(position, color, deadline, root=False):
    key = (color, root)
    cached = position.cache.get(key)
    if cached is not None:
        return cached

    _check_time(deadline)
    candidates = _candidates(position, color, deadline)
    limit = 36 if root else 9
    moves = []

    for _, prior, p in candidates[:limit]:
        _check_time(deadline)
        child = _play(position, p, color)
        if child is None:
            continue

        if root:
            # With no supplied last move, a ko-shaped single capture is
            # conservatively omitted. This also prevents unknown recaptures.
            if child.ko:
                continue
            if tuple(child.board) in _HISTORY:
                continue

        score = color * child.value(-color) + prior
        moves.append((score, prior, p, child))

    # Passing is always available.
    pass_prior = -0.08
    moves.append((
        color * position.value(-color) + pass_prior,
        pass_prior,
        0,
        position
    ))
    moves.sort(key=lambda item: item[0], reverse=True)
    position.cache[key] = moves
    return moves


def _quiescence(position, color, alpha, beta, depth, deadline):
    _check_time(deadline)
    best = color * position.value(color)

    if best >= beta or depth == 0:
        return best
    if best > alpha:
        alpha = best

    tactical = {}
    for owner, stones, liberties in position.groups:
        if len(liberties) != 1:
            continue
        p = next(iter(liberties))
        urgency = len(stones) * (2.0 if owner == -color else 0.9)
        tactical[p] = tactical.get(p, 0.0) + urgency

    if not tactical:
        return best

    points = sorted(tactical, key=tactical.get, reverse=True)[:3]
    children = []

    for p in points:
        child = _play(position, p, color)
        if child is not None:
            children.append((color * child.value(-color), child))

    children.sort(key=lambda item: item[0], reverse=True)

    for _, child in children:
        value = -_quiescence(
            child, -color, -beta, -alpha, depth - 1, deadline
        )
        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def _search(position, color, depth, alpha, beta, deadline):
    _check_time(deadline)

    if depth == 0:
        return _quiescence(position, color, alpha, beta, 2, deadline)

    moves = _ordered(position, color, deadline)
    width = 6 if depth == 1 else 5
    best = -_INF

    for _, prior, p, child in moves[:width]:
        value = prior - _search(
            child,
            -color,
            depth - 1,
            prior - beta,
            prior - alpha,
            deadline
        )
        if value > best:
            best = value
        if value > alpha:
            alpha = value
        if alpha >= beta:
            break

    return best


def policy(me: list[tuple[int, int]],
           opponent: list[tuple[int, int]]) -> tuple[int, int]:
    deadline = time.perf_counter() + 0.88

    if not me and not opponent:
        _HISTORY.clear()
        return (4, 4)

    board = [_WALL] * 441
    for p in _POINTS:
        board[p] = 0
    for r, c in me:
        board[r * 21 + c] = 1
    for r, c in opponent:
        board[r * 21 + c] = -1

    if len(me) + len(opponent) <= 2 or len(_HISTORY) > 1500:
        _HISTORY.clear()
    _HISTORY.add(tuple(board))

    position = _Position(board)
    chosen_p = 0
    chosen_child = position

    try:
        roots = _ordered(position, 1, deadline, root=True)

        # A fully checked, legal fallback exists before deeper search.
        _, _, chosen_p, chosen_child = roots[0]

        ranked = []
        alpha = -_INF

        # Complete the two-ply iteration before replacing the fallback.
        for item in roots[:18]:
            _, prior, p, child = item
            value = prior - _search(
                child, -1, 1, -_INF, prior - alpha, deadline
            )
            ranked.append((value, item))
            if value > alpha:
                alpha = value

        ranked.sort(key=lambda item: item[0], reverse=True)
        _, best_item = ranked[0]
        _, _, chosen_p, chosen_child = best_item

        remaining = deadline - time.perf_counter()
        if remaining > 0.07:
            root_width = 10 if remaining > 0.25 else 6
            deeper = []
            alpha = -_INF

            for _, item in ranked[:root_width]:
                _, prior, p, child = item
                value = prior - _search(
                    child, -1, 2, -_INF, prior - alpha, deadline
                )
                deeper.append((value, item))
                if value > alpha:
                    alpha = value

            deeper.sort(key=lambda item: item[0], reverse=True)
            _, best_item = deeper[0]
            _, _, chosen_p, chosen_child = best_item

    except _Timeout:
        pass

    if chosen_p == 0:
        return (0, 0)

    _HISTORY.add(tuple(chosen_child.board))
    return divmod(chosen_p, 21)
