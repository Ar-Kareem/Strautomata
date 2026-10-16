
import time

N = 6
NSQ = 36

_DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

_RAYS = []
_NEIGHBORS = []
_CENTRAL = []
_CHEB = [[0] * NSQ for _ in range(NSQ)]
_BETWEEN = [[None] * NSQ for _ in range(NSQ)]

for r in range(N):
    for c in range(N):
        rays = []
        for dr, dc in _DIRS:
            ray = []
            rr, cc = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc < N:
                ray.append(rr * N + cc)
                rr += dr
                cc += dc
            rays.append(tuple(ray))
        _RAYS.append(tuple(rays))

        neigh = []
        for dr, dc in _DIRS:
            rr, cc = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc < N:
                neigh.append(rr * N + cc)
        _NEIGHBORS.append(tuple(neigh))

        # Highest near the four central squares, lowest in corners.
        _CENTRAL.append(int(10 - 2 * (abs(r - 2.5) + abs(c - 2.5))))

_RAYS = tuple(_RAYS)
_NEIGHBORS = tuple(_NEIGHBORS)
_CENTRAL = tuple(_CENTRAL)

for a in range(NSQ):
    r1, c1 = divmod(a, N)
    for b in range(NSQ):
        r2, c2 = divmod(b, N)
        _CHEB[a][b] = max(abs(r1 - r2), abs(c1 - c2))

        if a == b:
            continue
        dr = r2 - r1
        dc = c2 - c1
        if dr == 0 or dc == 0 or abs(dr) == abs(dc):
            sr = 0 if dr == 0 else (1 if dr > 0 else -1)
            sc = 0 if dc == 0 else (1 if dc > 0 else -1)
            rr, cc = r1 + sr, c1 + sc
            cells = []
            while rr != r2 or cc != c2:
                cells.append(rr * N + cc)
                rr += sr
                cc += sc
            _BETWEEN[a][b] = tuple(cells)

_INF = 10 ** 9
_WIN = 10 ** 6


class _SearchTimeout(Exception):
    pass


def _move_to_str(m):
    fr, to, ar = m
    return f"{fr // N},{fr % N}:{to // N},{to % N}:{ar // N},{ar % N}"


def _do_move(b, m, side):
    fr, to, ar = m
    b[fr] = 0
    b[to] = side
    b[ar] = -1


def _undo_move(b, m, side):
    fr, to, ar = m
    b[ar] = 0
    b[to] = 0
    b[fr] = side


def _visible_count(b, pos):
    cnt = 0
    for ray in _RAYS[pos]:
        for sq in ray:
            if b[sq] != 0:
                break
            cnt += 1
    return cnt


def _adjacent_count(b, pos):
    cnt = 0
    for sq in _NEIGHBORS[pos]:
        if b[sq] == 0:
            cnt += 1
    return cnt


def _has_any_move(b, side):
    for i, v in enumerate(b):
        if v == side:
            for ray in _RAYS[i]:
                for sq in ray:
                    if b[sq] != 0:
                        break
                    return True
    return False


def _generate_moves(b, side):
    moves = []
    for fr, v in enumerate(b):
        if v != side:
            continue

        b[fr] = 0
        for ray in _RAYS[fr]:
            for to in ray:
                if b[to] != 0:
                    break

                b[to] = side

                for ar_ray in _RAYS[to]:
                    for ar in ar_ray:
                        if b[ar] != 0:
                            break
                        moves.append((fr, to, ar))

                b[to] = 0
        b[fr] = side

    return moves


def _queen_distances(b, sources):
    dist = [99] * NSQ
    q = []
    for s in sources:
        dist[s] = 0
        q.append(s)

    head = 0
    while head < len(q):
        p = q[head]
        head += 1
        nd = dist[p] + 1

        for ray in _RAYS[p]:
            for sq in ray:
                if b[sq] != 0:
                    break
                if nd < dist[sq]:
                    dist[sq] = nd
                    q.append(sq)

    return dist


def _evaluate(b, side):
    other = 3 - side

    my_pos = []
    op_pos = []
    my_mob = 0
    op_mob = 0
    my_adj = 0
    op_adj = 0

    for i, v in enumerate(b):
        if v == side:
            my_pos.append(i)
            my_mob += _visible_count(b, i)
            my_adj += _adjacent_count(b, i)
        elif v == other:
            op_pos.append(i)
            op_mob += _visible_count(b, i)
            op_adj += _adjacent_count(b, i)

    # Current player with no amazon mobility loses.
    if my_mob == 0:
        return -_WIN
    if op_mob == 0:
        return _WIN

    my_dist = _queen_distances(b, my_pos)
    op_dist = _queen_distances(b, op_pos)

    territory = 0
    my_reach = 0
    op_reach = 0
    empties = 0

    for i, v in enumerate(b):
        if v != 0:
            continue

        empties += 1
        md = my_dist[i]
        od = op_dist[i]

        if md < 99:
            my_reach += 1
        if od < 99:
            op_reach += 1

        if md == 99 and od == 99:
            continue

        if md < od:
            if od == 99:
                territory += 150
            else:
                territory += 90 + 15 * (od - md)
        elif od < md:
            if md == 99:
                territory -= 150
            else:
                territory -= 90 + 15 * (md - od)
        else:
            # Small tempo bonus for cells both sides reach equally soon.
            territory += 4

    mobility_weight = 10 + empties // 4

    return (
        territory
        + mobility_weight * (my_mob - op_mob)
        + 7 * (my_adj - op_adj)
        + 6 * (my_reach - op_reach)
    )


def _quick_score(b, side, m, opps):
    other = 3 - side
    fr, to, ar = m

    _do_move(b, m, side)

    if not _has_any_move(b, other):
        score = 900000
    else:
        score = (
            16 * _visible_count(b, to)
            + 3 * _visible_count(b, ar)
            + 3 * _CENTRAL[to]
            + 4 * _CENTRAL[ar]
        )

        attack = 0
        for op in opps:
            d = _CHEB[ar][op]
            if d <= 2:
                attack += (4 - d) * 20
            elif d <= 4:
                attack += (5 - d) * 5

            between = _BETWEEN[op][ar]
            if between is not None:
                clear = True
                for x in between:
                    if b[x] != 0:
                        clear = False
                        break
                if clear:
                    attack += 45 // max(1, d)

        score += attack

    _undo_move(b, m, side)
    return score


def _node_limit(depth, ply, n):
    if n <= 18:
        return n
    if depth <= 1:
        return min(n, 70)
    if depth == 2:
        return min(n, 42)
    if depth == 3:
        return min(n, 28)
    return min(n, 18)


def _root_limit(depth, n):
    if n <= 25:
        return n
    if depth <= 2:
        return min(n, 90)
    if depth == 3:
        return min(n, 55)
    if depth == 4:
        return min(n, 34)
    if depth == 5:
        return min(n, 24)
    return min(n, 18)


def _order_moves(b, side, moves, depth, ply, end_time):
    n = len(moves)
    if n <= 1:
        return moves

    limit = _node_limit(depth, ply, n)
    other = 3 - side
    opps = [i for i, v in enumerate(b) if v == other]

    scored = []
    for idx, m in enumerate(moves):
        if (idx & 31) == 0 and time.perf_counter() >= end_time:
            raise _SearchTimeout
        scored.append((_quick_score(b, side, m, opps), m))

    scored.sort(key=lambda x: x[0], reverse=True)
    if limit < n:
        scored = scored[:limit]
    return [m for _, m in scored]


def _negamax(b, side, depth, alpha, beta, end_time, ply):
    if time.perf_counter() >= end_time:
        raise _SearchTimeout

    if depth <= 0:
        return _evaluate(b, side)

    if not _has_any_move(b, side):
        return -_WIN + ply

    moves = _generate_moves(b, side)
    if not moves:
        return -_WIN + ply

    moves = _order_moves(b, side, moves, depth, ply, end_time)

    best = -_INF
    other = 3 - side

    for m in moves:
        _do_move(b, m, side)
        try:
            val = -_negamax(b, other, depth - 1, -beta, -alpha, end_time, ply + 1)
        finally:
            _undo_move(b, m, side)

        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break

    return best


def policy(board) -> str:
    # Leave a small safety margin under a 1 second limit.
    end_time = time.perf_counter() + 0.93

    try:
        b = [int(x) for x in board.ravel()]
    except Exception:
        b = [int(board[r][c]) for r in range(N) for c in range(N)]

    moves = _generate_moves(b, 1)

    # Terminal robustness. In a real terminal state there is no legal string,
    # but the environment should not call us then.
    if not moves:
        return "0,0:0,0:0,0"

    if len(moves) == 1:
        return _move_to_str(moves[0])

    best = moves[0]

    # Static root evaluation of as many legal moves as time allows.
    scored = []
    for idx, m in enumerate(moves):
        if idx and (idx & 7) == 0 and time.perf_counter() >= end_time:
            break

        _do_move(b, m, 1)
        val = -_evaluate(b, 2) + _visible_count(b, m[1])
        _undo_move(b, m, 1)

        if val > _WIN // 2:
            return _move_to_str(m)

        scored.append((val, m))

    if not scored:
        return _move_to_str(best)

    scored.sort(key=lambda x: x[0], reverse=True)
    root_moves = [m for _, m in scored]
    best = root_moves[0]

    if time.perf_counter() >= end_time:
        return _move_to_str(best)

    # Iterative deepening selective alpha-beta.
    max_depth = 8

    for depth in range(2, max_depth + 1):
        if time.perf_counter() >= end_time:
            break

        limit = _root_limit(depth, len(root_moves))
        candidates = root_moves[:limit]

        alpha = -_INF
        local_best = best
        local_score = -_INF
        searched = []

        try:
            for m in candidates:
                if time.perf_counter() >= end_time:
                    raise _SearchTimeout

                _do_move(b, m, 1)
                try:
                    val = -_negamax(b, 2, depth - 1, -_INF, -alpha, end_time, 1)
                finally:
                    _undo_move(b, m, 1)

                searched.append((val, m))

                if val > local_score:
                    local_score = val
                    local_best = m
                    best = m

                if val > alpha:
                    alpha = val

        except _SearchTimeout:
            break

        if not searched:
            break

        searched.sort(key=lambda x: x[0], reverse=True)
        best = searched[0][1]

        searched_set = set(m for _, m in searched)
        root_moves = [m for _, m in searched] + [m for m in root_moves if m not in searched_set]

        if searched[0][0] > _WIN // 2:
            break

    return _move_to_str(best)
