
import time

N = 6
SIZE = 36
INF = 10 ** 9
WIN = 10 ** 7

DIRS = [
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
]

RAYS = []
ADJ = []
for i in range(SIZE):
    r, c = divmod(i, N)

    rays_i = []
    for dr, dc in DIRS:
        ray = []
        rr, cc = r + dr, c + dc
        while 0 <= rr < N and 0 <= cc < N:
            ray.append(rr * N + cc)
            rr += dr
            cc += dc
        rays_i.append(ray)
    RAYS.append(rays_i)

    adj_i = []
    for dr, dc in DIRS:
        rr, cc = r + dr, c + dc
        if 0 <= rr < N and 0 <= cc < N:
            adj_i.append(rr * N + cc)
    ADJ.append(adj_i)


_DEADLINE = 0.0
_NODES = 0
_EVAL_CACHE = {}


class SearchTimeout(Exception):
    pass


def _check_time():
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise SearchTimeout()


def _move_to_str(m):
    fr, to, ar = m
    fr_r, fr_c = divmod(fr, N)
    to_r, to_c = divmod(to, N)
    ar_r, ar_c = divmod(ar, N)
    return f"{fr_r},{fr_c}:{to_r},{to_c}:{ar_r},{ar_c}"


def _apply(b, m, player):
    fr, to, ar = m
    b[fr] = 0
    b[to] = player
    b[ar] = -1


def _undo(b, m, player):
    fr, to, ar = m
    b[ar] = 0
    b[to] = 0
    b[fr] = player


def _has_any_move(b, player):
    for i, v in enumerate(b):
        if v == player:
            for ray in RAYS[i]:
                for j in ray:
                    if b[j] == 0:
                        return True
                    break
    return False


def _generate_moves(b, player):
    moves = []
    for fr, v in enumerate(b):
        if v != player:
            continue

        for move_ray in RAYS[fr]:
            for to in move_ray:
                if b[to] != 0:
                    break

                # Arrow is shot after fr is vacated and to is occupied.
                for arrow_ray in RAYS[to]:
                    for ar in arrow_ray:
                        if b[ar] == 0 or ar == fr:
                            moves.append((fr, to, ar))
                            continue
                        break
    return moves


def _queen_move_count(b, player):
    cnt = 0
    for i, v in enumerate(b):
        if v == player:
            for ray in RAYS[i]:
                for j in ray:
                    if b[j] == 0:
                        cnt += 1
                    else:
                        break
    return cnt


def _adjacent_empty_count(b, player):
    cnt = 0
    for i, v in enumerate(b):
        if v == player:
            for j in ADJ[i]:
                if b[j] == 0:
                    cnt += 1
    return cnt


def _distances(b, player):
    # Queen-move distance through empty squares.
    dist = [99] * SIZE
    q = []

    for i, v in enumerate(b):
        if v == player:
            dist[i] = 0
            q.append(i)

    head = 0
    while head < len(q):
        x = q[head]
        head += 1
        nd = dist[x] + 1

        for ray in RAYS[x]:
            for y in ray:
                if b[y] != 0:
                    break
                if dist[y] > nd:
                    dist[y] = nd
                    q.append(y)

    return dist


def _evaluate(b):
    key = tuple(b)
    cached = _EVAL_CACHE.get(key)
    if cached is not None:
        return cached

    m1 = _queen_move_count(b, 1)
    m2 = _queen_move_count(b, 2)

    # If the opponent cannot move, this is winning for us.
    if m2 == 0:
        return WIN // 2
    if m1 == 0:
        return -WIN // 2

    d1 = _distances(b, 1)
    d2 = _distances(b, 2)

    territory = 0
    closeness = 0
    reach = 0

    for i, v in enumerate(b):
        if v != 0:
            continue

        a = d1[i]
        o = d2[i]

        if a < 99:
            reach += 1
        if o < 99:
            reach -= 1

        if a < o:
            territory += 1
            closeness += min(5, o - a)
        elif o < a:
            territory -= 1
            closeness -= min(5, a - o)

    adj = _adjacent_empty_count(b, 1) - _adjacent_empty_count(b, 2)

    score = (
        85 * territory +
        11 * closeness +
        9 * reach +
        6 * (m1 - m2) +
        3 * adj
    )

    if len(_EVAL_CACHE) < 50000:
        _EVAL_CACHE[key] = score

    return score


def _quick_eval(b):
    m1 = _queen_move_count(b, 1)
    m2 = _queen_move_count(b, 2)

    if m2 == 0:
        return WIN // 3
    if m1 == 0:
        return -WIN // 3

    adj = _adjacent_empty_count(b, 1) - _adjacent_empty_count(b, 2)
    return 8 * (m1 - m2) + 3 * adj


def _ordered_limited_moves(b, player, depth, ply):
    _check_time()
    moves = _generate_moves(b, player)
    if len(moves) <= 1:
        return moves

    n = len(moves)

    if n <= 45:
        limit = n
    elif depth >= 3:
        limit = 30
    elif depth == 2:
        limit = 45
    else:
        limit = 70

    scored = []
    for m in moves:
        _apply(b, m, player)
        s = _quick_eval(b)
        _undo(b, m, player)
        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=(player == 1))

    if len(scored) > limit:
        scored = scored[:limit]

    return [m for _, m in scored]


def _alphabeta(b, depth, player, alpha, beta, ply):
    _check_time()

    if not _has_any_move(b, player):
        if player == 1:
            return -WIN + ply
        else:
            return WIN - ply

    if depth <= 0:
        return _evaluate(b)

    moves = _ordered_limited_moves(b, player, depth, ply)

    if player == 1:
        value = -INF
        for m in moves:
            _apply(b, m, 1)
            value = max(value, _alphabeta(b, depth - 1, 2, alpha, beta, ply + 1))
            _undo(b, m, 1)

            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value

    else:
        value = INF
        for m in moves:
            _apply(b, m, 2)
            value = min(value, _alphabeta(b, depth - 1, 1, alpha, beta, ply + 1))
            _undo(b, m, 2)

            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return value


def _root_limit(total, depth):
    if total <= 60:
        return total
    if depth == 2:
        return min(total, 240)
    if depth == 3:
        return min(total, 90)
    if depth == 4:
        return min(total, 42)
    return min(total, 25)


def _root_search(b, ordered_moves, depth):
    best_move = ordered_moves[0]
    best_score = -INF
    alpha = -INF
    beta = INF

    limit = _root_limit(len(ordered_moves), depth)

    for m in ordered_moves[:limit]:
        _check_time()

        _apply(b, m, 1)
        score = _alphabeta(b, depth - 1, 2, alpha, beta, 1)
        _undo(b, m, 1)

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

    return best_move, best_score


def policy(board) -> str:
    global _DEADLINE, _NODES, _EVAL_CACHE

    _DEADLINE = time.perf_counter() + 0.92
    _NODES = 0
    _EVAL_CACHE = {}

    try:
        b = [int(x) for x in board.ravel()]
    except Exception:
        b = [int(x) for row in board for x in row]

    moves = _generate_moves(b, 1)

    # The environment should not call us here, but keep a robust fallback.
    if not moves:
        return "0,0:0,0:0,0"

    best_move = moves[0]

    try:
        # Static scoring of all root moves gives a strong and safe fallback.
        scored = []
        best_static = -INF

        for idx, m in enumerate(moves):
            if (idx & 15) == 0 and time.perf_counter() > _DEADLINE:
                raise SearchTimeout()

            _apply(b, m, 1)
            s = _evaluate(b)
            _undo(b, m, 1)

            scored.append((s, m))
            if s > best_static:
                best_static = s
                best_move = m

        scored.sort(key=lambda x: x[0], reverse=True)
        ordered = [m for _, m in scored]

        # If a static move already leaves the opponent with no move, take it.
        for s, m in scored[:8]:
            if s >= WIN // 3:
                return _move_to_str(m)

        # Iterative deepening. Later depths are selective, earlier depths are safer.
        root_count = len(ordered)
        if root_count <= 25:
            max_depth = 6
        elif root_count <= 80:
            max_depth = 5
        elif root_count <= 220:
            max_depth = 4
        else:
            max_depth = 3

        for depth in range(2, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break
            bm, _ = _root_search(b, ordered, depth)
            best_move = bm

    except SearchTimeout:
        pass
    except Exception:
        # Never risk failing to return a legal move.
        pass

    return _move_to_str(best_move)
