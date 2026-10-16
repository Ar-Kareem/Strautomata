
import time
from collections import deque

# Board geometry
_SIZE = 6
_N = 36
_DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),             (0, 1),
    (1, -1),  (1, 0),    (1, 1),
)

_RAYS = [[] for _ in range(_N)]
_NEIGHBORS = [[] for _ in range(_N)]
_CENTER = [0] * _N

for r in range(_SIZE):
    for c in range(_SIZE):
        s = r * _SIZE + c
        _CENTER[s] = 12 - abs(2 * r - 5) - abs(2 * c - 5)

        for dr, dc in _DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < _SIZE and 0 <= cc < _SIZE:
                ray.append(rr * _SIZE + cc)
                rr += dr
                cc += dc
            _RAYS[s].append(ray)

            rr, cc = r + dr, c + dc
            if 0 <= rr < _SIZE and 0 <= cc < _SIZE:
                _NEIGHBORS[s].append(rr * _SIZE + cc)


_MATE = 1_000_000
_INFINITY = 2_000_000
_UNREACHED = 99

_DEADLINE = 0.0
_NODES = 0
_TT = {}
_EVAL_CACHE = {}
_HISTORY = {}
_KILLERS = []


class _SearchTimeout(Exception):
    pass


def _generate_moves(b, side):
    """Generate every legal (from, to, arrow) move."""
    moves = []

    for origin in range(_N):
        if b[origin] != side:
            continue

        b[origin] = 0

        for move_ray in _RAYS[origin]:
            for target in move_ray:
                if b[target] != 0:
                    break

                b[target] = side

                for arrow_ray in _RAYS[target]:
                    for arrow in arrow_ray:
                        if b[arrow] != 0:
                            break
                        moves.append((origin, target, arrow))

                b[target] = 0

        b[origin] = side

    return moves


def _apply(b, move, side):
    origin, target, arrow = move
    b[origin] = 0
    b[target] = side
    b[arrow] = -1


def _undo(b, move, side):
    origin, target, arrow = move
    b[arrow] = 0
    b[target] = 0
    b[origin] = side


def _mobility(b, side):
    """Number of queen landing squares available to all amazons."""
    total = 0
    for square in range(_N):
        if b[square] != side:
            continue
        for ray in _RAYS[square]:
            for x in ray:
                if b[x] != 0:
                    break
                total += 1
    return total


def _queen_distances(b, side):
    """Minimum number of queen moves needed to reach every empty square."""
    dist = [_UNREACHED] * _N
    queue = []
    head = 0

    for s in range(_N):
        if b[s] == side:
            dist[s] = 0
            queue.append(s)

    while head < len(queue):
        current = queue[head]
        head += 1
        next_dist = dist[current] + 1

        for ray in _RAYS[current]:
            for x in ray:
                if b[x] != 0:
                    break
                if dist[x] == _UNREACHED:
                    dist[x] = next_dist
                    queue.append(x)

    return dist


def _king_distances(b, side):
    """Obstacle-aware king-step distances, useful for local ownership."""
    dist = [_UNREACHED] * _N
    queue = deque()

    for s in range(_N):
        if b[s] == side:
            dist[s] = 0
            queue.append(s)

    while queue:
        current = queue.popleft()
        next_dist = dist[current] + 1

        for x in _NEIGHBORS[current]:
            if b[x] == 0 and dist[x] == _UNREACHED:
                dist[x] = next_dist
                queue.append(x)

    return dist


def _static_data(b):
    """
    Return an absolute player-1 evaluation, both mobilities, and the
    number of queen-distance ties.
    """
    key = tuple(b)
    cached = _EVAL_CACHE.get(key)
    if cached is not None:
        return cached

    mobility_1 = _mobility(b, 1)
    mobility_2 = _mobility(b, 2)

    q1 = _queen_distances(b, 1)
    q2 = _queen_distances(b, 2)
    k1 = _king_distances(b, 1)
    k2 = _king_distances(b, 2)

    empty_count = 0
    for value in b:
        if value == 0:
            empty_count += 1

    # Territory becomes increasingly important as chambers solidify.
    territory_weight = 70 + 3 * (32 - empty_count)
    if territory_weight < 65:
        territory_weight = 65
    elif territory_weight > 130:
        territory_weight = 130

    mobility_weight = 5 if empty_count > 18 else 3
    score = mobility_weight * (mobility_1 - mobility_2)
    tied = 0

    for s in range(_N):
        if b[s] != 0:
            continue

        d1 = q1[s]
        d2 = q2[s]

        if d1 != _UNREACHED or d2 != _UNREACHED:
            if d2 == _UNREACHED:
                score += territory_weight + 30
            elif d1 == _UNREACHED:
                score -= territory_weight + 30
            elif d1 < d2:
                score += territory_weight
            elif d2 < d1:
                score -= territory_weight
            else:
                tied += 1

            if d1 != _UNREACHED:
                score += 8 // max(1, d1)
            if d2 != _UNREACHED:
                score -= 8 // max(1, d2)

        kd1 = k1[s]
        kd2 = k2[s]
        if kd1 < kd2:
            score += 16
        elif kd2 < kd1:
            score -= 16

    result = (score, mobility_1, mobility_2, tied)

    if len(_EVAL_CACHE) < 100_000:
        _EVAL_CACHE[key] = result

    return result


def _evaluate_relative(b, side, ply):
    """Evaluate from the player-to-move's perspective."""
    absolute, mobility_1, mobility_2, tied = _static_data(b)
    current_mobility = mobility_1 if side == 1 else mobility_2

    if current_mobility == 0:
        return -_MATE + ply

    if side == 1:
        return absolute + 3 * tied
    return -absolute + 3 * tied


def _ordered_moves(b, side, moves, tt_move=None, ply=0):
    """
    Fast strategic ordering. It favors free landing squares and arrows
    that cut rays close to opposing amazons.
    """
    opponent = 3 - side
    freedom = [0] * _N
    pressure = [0] * _N

    for s in range(_N):
        if b[s] != 0:
            continue
        count = 0
        for ray in _RAYS[s]:
            for x in ray:
                if b[x] != 0:
                    break
                count += 1
        freedom[s] = count

    # Reward arrows on rays radiating from enemy amazons.
    for q in range(_N):
        if b[q] == opponent:
            for ray in _RAYS[q]:
                distance = 0
                for x in ray:
                    if b[x] != 0:
                        break
                    distance += 1
                    pressure[x] += max(2, 18 - 2 * distance)
        elif b[q] == side:
            for ray in _RAYS[q]:
                distance = 0
                for x in ray:
                    if b[x] != 0:
                        break
                    distance += 1
                    pressure[x] -= max(1, 7 - distance)

    killer_1 = None
    killer_2 = None
    if ply < len(_KILLERS):
        killer_1, killer_2 = _KILLERS[ply]

    def move_score(move):
        origin, target, arrow = move
        value = (
            5 * freedom[target]
            + 3 * pressure[arrow]
            + 2 * _CENTER[target]
            + _CENTER[arrow]
            + _HISTORY.get((side, move), 0)
        )

        if move == tt_move:
            value += 1_000_000_000
        elif move == killer_1:
            value += 20_000_000
        elif move == killer_2:
            value += 10_000_000

        if arrow == origin:
            value += 2

        return value

    moves.sort(key=move_score, reverse=True)
    return moves


def _record_killer(move, ply):
    while len(_KILLERS) <= ply:
        _KILLERS.append([None, None])

    if _KILLERS[ply][0] != move:
        _KILLERS[ply][1] = _KILLERS[ply][0]
        _KILLERS[ply][0] = move


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 31) == 0 and time.perf_counter() >= _DEADLINE:
        raise _SearchTimeout


def _negamax(b, side, depth, alpha, beta, ply):
    _check_time()

    if depth == 0:
        return _evaluate_relative(b, side, ply)

    key = (tuple(b), side)
    alpha_original = alpha
    beta_original = beta

    entry = _TT.get(key)
    tt_move = None

    if entry is not None:
        stored_depth, stored_value, flag, tt_move = entry
        if stored_depth >= depth:
            if flag == 0:
                return stored_value
            if flag == 1:
                if stored_value > alpha:
                    alpha = stored_value
            else:
                if stored_value < beta:
                    beta = stored_value
            if alpha >= beta:
                return stored_value

    moves = _generate_moves(b, side)
    if not moves:
        return -_MATE + ply

    _ordered_moves(b, side, moves, tt_move, ply)

    best_value = -_INFINITY
    best_move = moves[0]
    opponent = 3 - side

    for move in moves:
        _apply(b, move, side)
        try:
            value = -_negamax(
                b, opponent, depth - 1, -beta, -alpha, ply + 1
            )
        finally:
            _undo(b, move, side)

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

        if alpha >= beta:
            history_key = (side, move)
            _HISTORY[history_key] = min(
                1_000_000,
                _HISTORY.get(history_key, 0) + depth * depth
            )
            _record_killer(move, ply)
            break

    if best_value <= alpha_original:
        flag = 2  # Upper bound
    elif best_value >= beta_original:
        flag = 1  # Lower bound
    else:
        flag = 0  # Exact

    if len(_TT) < 120_000:
        old = _TT.get(key)
        if old is None or old[0] <= depth:
            _TT[key] = (depth, best_value, flag, best_move)

    return best_value


def _root_search(b, moves, depth):
    alpha = -_INFINITY
    beta = _INFINITY
    best_value = -_INFINITY
    best_move = moves[0]
    values = []

    for move in moves:
        if time.perf_counter() >= _DEADLINE:
            raise _SearchTimeout

        _apply(b, move, 1)
        try:
            value = -_negamax(
                b, 2, depth - 1, -beta, -alpha, 1
            )
        finally:
            _undo(b, move, 1)

        values.append((value, move))

        if value > best_value:
            best_value = value
            best_move = move

        if value > alpha:
            alpha = value

    values.sort(key=lambda item: item[0], reverse=True)
    ordered = [move for _, move in values]
    return best_value, best_move, ordered


def _format_move(move):
    origin, target, arrow = move
    fr, fc = divmod(origin, _SIZE)
    tr, tc = divmod(target, _SIZE)
    ar, ac = divmod(arrow, _SIZE)
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    global _DEADLINE, _NODES, _TT, _EVAL_CACHE, _HISTORY, _KILLERS

    start = time.perf_counter()
    _DEADLINE = start + 0.93
    _NODES = 0
    _TT = {}
    _EVAL_CACHE = {}
    _HISTORY = {}
    _KILLERS = []

    b = [
        int(board[r][c])
        for r in range(_SIZE)
        for c in range(_SIZE)
    ]

    legal_moves = _generate_moves(b, 1)

    # No legal string can exist in a terminal position. The environment
    # promises not to call policy in this case.
    if not legal_moves:
        return ""

    # Strategically order the initial list so even an extremely early
    # timeout leaves a reasonable legal fallback.
    _ordered_moves(b, 1, legal_moves, None, 0)
    best_move = legal_moves[0]
    best_value = -_INFINITY
    scored = []
    completed_baseline = True

    # Complete one-ply evaluation before attempting deeper minimax.
    for index, move in enumerate(legal_moves):
        if (index & 7) == 0 and time.perf_counter() >= _DEADLINE - 0.012:
            completed_baseline = False
            break

        _apply(b, move, 1)
        try:
            value = -_evaluate_relative(b, 2, 1)
        finally:
            _undo(b, move, 1)

        scored.append((value, move))

        if value > best_value:
            best_value = value
            best_move = move

        # This move immediately leaves the opponent without any move.
        if value >= _MATE // 2:
            return _format_move(move)

    if not completed_baseline:
        return _format_move(best_move)

    scored.sort(key=lambda item: item[0], reverse=True)
    ordered_moves = [move for _, move in scored]
    best_move = ordered_moves[0]
    best_value = scored[0][0]

    empty_count = sum(1 for value in b if value == 0)
    depth = 2

    while depth <= empty_count:
        if time.perf_counter() >= _DEADLINE - 0.025:
            break

        try:
            value, move, new_order = _root_search(
                b, ordered_moves, depth
            )
        except _SearchTimeout:
            break

        best_value = value
        best_move = move
        ordered_moves = new_order

        # A completed search has established a forced terminal result.
        if abs(best_value) >= _MATE // 2:
            break

        depth += 1

    return _format_move(best_move)
