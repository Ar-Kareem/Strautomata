
import time

N = 6
S = 36

_DIRS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
)

_RAYS = []
_NEIGH = []
_CENTER = []

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
        _NEIGH.append(tuple(neigh))

        d2 = (r - 2.5) * (r - 2.5) + (c - 2.5) * (c - 2.5)
        _CENTER.append(int(8 - d2))

_WIN = 10_000_000
_INF = 1_000_000_000
_DIST_INF = 99

_DEADLINE = 0.0
_NODES = 0
_EVAL_CACHE = {}


class _Timeout(Exception):
    pass


def _check_time():
    if time.perf_counter() >= _DEADLINE:
        raise _Timeout()


def _format_move(m):
    fr, to, ar = m
    return f"{fr // N},{fr % N}:{to // N},{to % N}:{ar // N},{ar % N}"


def _apply_move(b, m, side):
    fr, to, ar = m
    nb = list(b)
    nb[fr] = 0
    nb[to] = side
    nb[ar] = -1
    return tuple(nb)


def _gen_moves(b, side):
    rays = _RAYS
    for fr, v in enumerate(b):
        if v != side:
            continue
        for ray in rays[fr]:
            for to in ray:
                if b[to] != 0:
                    break

                # Shoot from "to" after vacating "fr".  The arrow may pass
                # through or land on the vacated origin square.
                for aray in rays[to]:
                    for ar in aray:
                        if ar == fr or b[ar] == 0:
                            yield (fr, to, ar)
                        else:
                            break


def _first_move(b):
    for m in _gen_moves(b, 1):
        return m
    return None


def _has_any_move(b, side):
    rays = _RAYS
    for fr, v in enumerate(b):
        if v != side:
            continue
        for ray in rays[fr]:
            for q in ray:
                if b[q] == 0:
                    return True
                break
    return False


def _dest_count(b, side):
    cnt = 0
    rays = _RAYS
    for fr, v in enumerate(b):
        if v != side:
            continue
        for ray in rays[fr]:
            for q in ray:
                if b[q] == 0:
                    cnt += 1
                else:
                    break
    return cnt


def _center_score(b):
    s = 0
    cen = _CENTER
    for i, v in enumerate(b):
        if v == 1:
            s += cen[i]
        elif v == 2:
            s -= cen[i]
    return s


def _component_score(b):
    seen = [False] * S
    score = 0

    for i in range(S):
        if seen[i] or b[i] == -1:
            continue

        stack = [i]
        seen[i] = True
        empty = own = opp = 0

        while stack:
            p = stack.pop()
            v = b[p]
            if v == 0:
                empty += 1
            elif v == 1:
                own += 1
            elif v == 2:
                opp += 1

            for q in _NEIGH[p]:
                if not seen[q] and b[q] != -1:
                    seen[q] = True
                    stack.append(q)

        if own and not opp:
            score += 10 * empty + 2 * own
        elif opp and not own:
            score -= 10 * empty + 2 * opp
        elif own or opp:
            score += (own - opp) * min(empty, 8)

    return score


def _queen_distances(b, side):
    dist = [_DIST_INF] * S
    q = []
    for i, v in enumerate(b):
        if v == side:
            dist[i] = 0
            q.append(i)

    head = 0
    rays = _RAYS
    while head < len(q):
        p = q[head]
        head += 1
        nd = dist[p] + 1

        for ray in rays[p]:
            for x in ray:
                if b[x] != 0:
                    break
                if dist[x] > nd:
                    dist[x] = nd
                    q.append(x)

    return dist


def _king_distances(b, side):
    dist = [_DIST_INF] * S
    q = []
    for i, v in enumerate(b):
        if v == side:
            dist[i] = 0
            q.append(i)

    head = 0
    while head < len(q):
        p = q[head]
        head += 1
        nd = dist[p] + 1

        for x in _NEIGH[p]:
            if b[x] == 0 and dist[x] > nd:
                dist[x] = nd
                q.append(x)

    return dist


def _quick_eval(b, side_to_move=0):
    m1 = _dest_count(b, 1)
    m2 = _dest_count(b, 2)

    if side_to_move == 1 and m1 == 0:
        return -_WIN // 2
    if side_to_move == 2 and m2 == 0:
        return _WIN // 2

    if m1 == 0 and m2 == 0:
        return 0
    if m1 == 0:
        return -_WIN // 3
    if m2 == 0:
        return _WIN // 3

    return 18 * (m1 - m2) + 3 * _center_score(b) + _component_score(b)


def _evaluate(b):
    cached = _EVAL_CACHE.get(b)
    if cached is not None:
        return cached

    m1 = _dest_count(b, 1)
    m2 = _dest_count(b, 2)

    if m1 == 0 and m2 == 0:
        val = 0
        _EVAL_CACHE[b] = val
        return val
    if m1 == 0:
        val = -_WIN // 3
        _EVAL_CACHE[b] = val
        return val
    if m2 == 0:
        val = _WIN // 3
        _EVAL_CACHE[b] = val
        return val

    score = 16 * (m1 - m2)
    score += 3 * _center_score(b)
    score += _component_score(b)

    q1 = _queen_distances(b, 1)
    q2 = _queen_distances(b, 2)
    k1 = _king_distances(b, 1)
    k2 = _king_distances(b, 2)

    for i, v in enumerate(b):
        if v != 0:
            continue

        a = q1[i]
        c = q2[i]

        if a >= _DIST_INF and c >= _DIST_INF:
            continue

        if a < c:
            if c >= _DIST_INF:
                score += 38
            else:
                score += 26 + 4 * min(c - a, 3)
        elif c < a:
            if a >= _DIST_INF:
                score -= 38
            else:
                score -= 26 + 4 * min(a - c, 3)
        else:
            ka = k1[i]
            kc = k2[i]
            if ka < kc:
                if kc >= _DIST_INF:
                    score += 20
                else:
                    score += 12 + 2 * min(kc - ka, 4)
            elif kc < ka:
                if ka >= _DIST_INF:
                    score -= 20
                else:
                    score -= 12 + 2 * min(ka - kc, 4)

    _EVAL_CACHE[b] = score
    return score


def _child_limit(n, depth, ply):
    if n <= 70:
        return n
    if depth <= 1:
        if ply <= 1:
            return min(n, 260)
        if ply <= 2:
            return min(n, 180)
        return min(n, 120)
    if depth == 2:
        if ply <= 1:
            return min(n, 90)
        return min(n, 60)
    if depth == 3:
        return min(n, 42)
    return min(n, 30)


def _ordered_children(b, side, depth, ply):
    moves = list(_gen_moves(b, side))
    n = len(moves)
    if n == 0:
        return []

    limit = _child_limit(n, depth, ply)
    next_side = 2 if side == 1 else 1
    scored = []

    for i, m in enumerate(moves):
        if (i & 63) == 0:
            _check_time()
        nb = _apply_move(b, m, side)
        scored.append((_quick_eval(nb, next_side), m, nb))

    scored.sort(key=lambda x: x[0], reverse=(side == 1))
    if limit < n:
        del scored[limit:]
    return scored


def _search(b, depth, side, alpha, beta, ply):
    global _NODES
    _NODES += 1
    if (_NODES & 127) == 0:
        _check_time()

    if depth <= 0:
        if not _has_any_move(b, side):
            return -_WIN + ply if side == 1 else _WIN - ply
        return _evaluate(b)

    children = _ordered_children(b, side, depth, ply)
    if not children:
        return -_WIN + ply if side == 1 else _WIN - ply

    if side == 1:
        best = -_INF
        for _, _, nb in children:
            val = _search(nb, depth - 1, 2, alpha, beta, ply + 1)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    best = _INF
    for _, _, nb in children:
        val = _search(nb, depth - 1, 1, alpha, beta, ply + 1)
        if val < best:
            best = val
        if best < beta:
            beta = best
        if alpha >= beta:
            break
    return best


def _root_cap(n, depth):
    if n <= 70:
        return n
    if depth == 2:
        if n <= 180:
            return min(n, 70)
        if n <= 600:
            return min(n, 48)
        return min(n, 34)
    if depth == 3:
        if n <= 180:
            return min(n, 34)
        if n <= 600:
            return min(n, 22)
        return min(n, 14)
    if depth == 4:
        if n <= 100:
            return min(n, 24)
        return min(n, 12)
    return min(n, 10)


def _choose_move(b, fallback):
    global _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.92
    _NODES = 0

    if len(_EVAL_CACHE) > 100000:
        _EVAL_CACHE.clear()

    moves = list(_gen_moves(b, 1))
    if not moves:
        return _format_move(fallback) if fallback is not None else "0,0:0,0:0,0"
    if len(moves) == 1:
        return _format_move(moves[0])

    best_move = moves[0]
    root = []

    try:
        for i, m in enumerate(moves):
            if (i & 31) == 0:
                _check_time()

            nb = _apply_move(b, m, 1)
            q = _quick_eval(nb, 2)

            # Immediate win: opponent to move has no legal move.
            if q >= _WIN // 2:
                return _format_move(m)

            root.append([q, m, nb])

        root.sort(key=lambda x: x[0], reverse=True)
        n = len(root)

        if n <= 220:
            full_limit = n
        elif n <= 600:
            full_limit = 320
        else:
            full_limit = 240

        budget = start + (0.36 if n > 600 else 0.46 if n > 250 else 0.56)
        min_full = min(n, 60)

        for i in range(min(full_limit, n)):
            if (i & 7) == 0:
                _check_time()
                if i >= min_full and time.perf_counter() > budget:
                    break

            item = root[i]
            item[0] = _evaluate(item[2])

        root.sort(key=lambda x: x[0], reverse=True)
        best_move = root[0][1]
        best_score = root[0][0]

        if best_score >= _WIN // 3:
            return _format_move(best_move)

        if n <= 18:
            max_depth = 7
        elif n <= 45:
            max_depth = 6
        elif n <= 100:
            max_depth = 5
        elif n <= 250:
            max_depth = 4
        else:
            max_depth = 3

        for depth in range(2, max_depth + 1):
            if time.perf_counter() > _DEADLINE - 0.05:
                break

            cap = _root_cap(n, depth)
            candidates = root[:cap]

            local_best = best_move
            local_score = -_INF
            alpha = -_INF
            searched = []

            for item in candidates:
                _check_time()
                val = _search(item[2], depth - 1, 2, alpha, _INF, 1)
                searched.append((item, val))

                if val > local_score:
                    local_score = val
                    local_best = item[1]
                if val > alpha:
                    alpha = val

            for item, val in searched:
                item[0] = val

            root.sort(key=lambda x: x[0], reverse=True)
            best_move = local_best
            best_score = local_score

        return _format_move(best_move)

    except _Timeout:
        return _format_move(best_move)


def policy(board) -> str:
    try:
        b = tuple(int(x) for x in board.ravel())
    except Exception:
        try:
            b = tuple(int(x) for row in board for x in row)
        except Exception:
            return "0,0:0,0:0,0"

    fallback = _first_move(b)
    if fallback is None:
        return "0,0:0,0:0,0"

    try:
        return _choose_move(b, fallback)
    except Exception:
        return _format_move(fallback)
