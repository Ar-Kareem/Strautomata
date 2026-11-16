
import time

N = 6
SIZE = 36

DIRECTIONS = (
    (-1, 0), (1, 0), (0, -1), (0, 1),
    (-1, -1), (-1, 1), (1, -1), (1, 1)
)

RAYS = [[] for _ in range(SIZE)]
NEIGHBORS = [[] for _ in range(SIZE)]
CENTER = [0] * SIZE

for r in range(N):
    for c in range(N):
        s = r * N + c

        cr = 2.5
        cc = 2.5
        CENTER[s] = int(10 - 2 * (abs(r - cr) + abs(c - cc)))

        for dr, dc in DIRECTIONS:
            line = []
            rr, cc2 = r + dr, c + dc
            while 0 <= rr < N and 0 <= cc2 < N:
                line.append(rr * N + cc2)
                rr += dr
                cc2 += dc
            RAYS[s].append(line)

        for dr, dc in DIRECTIONS:
            rr, cc2 = r + dr, c + dc
            if 0 <= rr < N and 0 <= cc2 < N:
                NEIGHBORS[s].append(rr * N + cc2)

WIN_SCORE = 1_000_000
INF = 10 ** 9
INF_DIST = 99

_EVAL_CACHE = {}
_DEADLINE = 0.0
_NODE_COUNT = 0


class _Timeout(Exception):
    pass


def _to_tuple(board):
    try:
        flat = board.reshape(SIZE)
        return tuple(int(x) for x in flat)
    except Exception:
        return tuple(int(board[r][c]) for r in range(N) for c in range(N))


def _move_to_str(m):
    f, t, a = m
    return f"{f // N},{f % N}:{t // N},{t % N}:{a // N},{a % N}"


def _iter_moves(b):
    rays = RAYS
    for f, v in enumerate(b):
        if v != 1:
            continue

        for ray in rays[f]:
            for t in ray:
                if b[t] != 0:
                    break

                for aray in rays[t]:
                    for a in aray:
                        if a == f:
                            yield (f, t, a)
                            continue
                        if b[a] != 0:
                            break
                        yield (f, t, a)


def _has_any_move(b):
    for f, v in enumerate(b):
        if v == 1:
            for ray in RAYS[f]:
                for t in ray:
                    if b[t] != 0:
                        break
                    return True
    return False


def _mobility(b, piece):
    total = 0
    for s, v in enumerate(b):
        if v != piece:
            continue
        for ray in RAYS[s]:
            for u in ray:
                if b[u] != 0:
                    break
                total += 1
    return total


def _apply_swap(b, m):
    f, t, a = m
    nb = list(b)

    nb[f] = 0
    nb[t] = 1
    nb[a] = -1

    for i, x in enumerate(nb):
        if x == 1:
            nb[i] = 2
        elif x == 2:
            nb[i] = 1

    return tuple(nb)


def _degree_after(b, pos, empty_sq, block_sq):
    cnt = 0
    for ray in RAYS[pos]:
        for s in ray:
            if s == block_sq:
                break
            if s == empty_sq or b[s] == 0:
                cnt += 1
            else:
                break
    return cnt


def _quick_score(b, m):
    f, t, a = m

    score = 0
    score += 3 * _degree_after(b, t, f, a)
    score += 2 * CENTER[t] + CENTER[a]

    if a == f:
        score += 2

    for n in NEIGHBORS[a]:
        if n == t:
            score -= 6
        elif n == f:
            continue
        else:
            val = b[n]
            if val == 2:
                score += 12
            elif val == 1:
                score -= 5
            elif val == -1:
                score += 1

    for ray in RAYS[a]:
        step = 0
        for s in ray:
            step += 1
            if s == f:
                val = 0
            elif s == t:
                val = 1
            else:
                val = b[s]

            if val != 0:
                if val == 2:
                    score += max(1, 12 - 2 * step)
                elif val == 1:
                    score -= max(1, 6 - step)
                break

    return score


def _queen_dist(b, piece):
    dist = [INF_DIST] * SIZE
    q = []

    for i, v in enumerate(b):
        if v == piece:
            dist[i] = 0
            q.append(i)

    head = 0
    while head < len(q):
        s = q[head]
        head += 1
        nd = dist[s] + 1

        for ray in RAYS[s]:
            for u in ray:
                if b[u] != 0:
                    break
                if dist[u] > nd:
                    dist[u] = nd
                    q.append(u)

    return dist


def _king_dist(b, piece):
    dist = [INF_DIST] * SIZE
    q = []

    for i, v in enumerate(b):
        if v == piece:
            dist[i] = 0
            q.append(i)

    head = 0
    while head < len(q):
        s = q[head]
        head += 1
        nd = dist[s] + 1

        for u in NEIGHBORS[s]:
            if b[u] == 0 and dist[u] > nd:
                dist[u] = nd
                q.append(u)

    return dist


def _evaluate(b):
    try:
        return _EVAL_CACHE[b]
    except KeyError:
        pass

    if len(_EVAL_CACHE) > 80000:
        _EVAL_CACHE.clear()

    own_mob = _mobility(b, 1)
    if own_mob == 0:
        val = -WIN_SCORE
        _EVAL_CACHE[b] = val
        return val

    opp_mob = _mobility(b, 2)

    q1 = _queen_dist(b, 1)
    q2 = _queen_dist(b, 2)
    k1 = _king_dist(b, 1)
    k2 = _king_dist(b, 2)

    qterr = 0
    qclose = 0
    kterr = 0
    kclose = 0
    empties = 0

    for i, v in enumerate(b):
        if v != 0:
            continue

        empties += 1

        d1 = q1[i]
        d2 = q2[i]
        if d1 < d2:
            qterr += 1
        elif d2 < d1:
            qterr -= 1

        if d1 < INF_DIST and d2 < INF_DIST:
            diff = d2 - d1
            if diff > 4:
                diff = 4
            elif diff < -4:
                diff = -4
            qclose += diff
        elif d1 < INF_DIST:
            qclose += 5
        elif d2 < INF_DIST:
            qclose -= 5

        d1 = k1[i]
        d2 = k2[i]
        if d1 < d2:
            kterr += 1
        elif d2 < d1:
            kterr -= 1

        if d1 < INF_DIST and d2 < INF_DIST:
            diff = d2 - d1
            if diff > 6:
                diff = 6
            elif diff < -6:
                diff = -6
            kclose += diff
        elif d1 < INF_DIST:
            kclose += 7
        elif d2 < INF_DIST:
            kclose -= 7

    phase = SIZE - empties
    terr_weight = 88 + 2 * phase

    val = 0
    val += terr_weight * qterr
    val += 10 * qclose
    val += 30 * kterr
    val += 3 * kclose
    val += 7 * (own_mob - opp_mob)

    if opp_mob == 0:
        val += 6000

    _EVAL_CACHE[b] = val
    return val


def _check_time():
    global _NODE_COUNT
    _NODE_COUNT += 1
    if (_NODE_COUNT & 255) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()


def _limit_for(depth, n, ply):
    if n <= 90:
        return n
    if depth <= 1:
        return n if n <= 130 else 110
    if depth == 2:
        return n if n <= 100 else 60
    if depth == 3:
        return n if n <= 80 else 38
    return min(n, 28)


def _ordered_moves(b, moves, depth):
    if len(moves) <= 1:
        return moves

    scored = []
    detect_wins = depth >= 2 and len(moves) <= 160

    for i, m in enumerate(moves):
        if (i & 63) == 0 and time.perf_counter() > _DEADLINE:
            raise _Timeout()

        s = _quick_score(b, m)

        if detect_wins:
            child = _apply_swap(b, m)
            if not _has_any_move(child):
                s += 1_000_000

        scored.append((s, m))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def _negamax(b, depth, alpha, beta, ply, tt):
    _check_time()

    if depth <= 0:
        return _evaluate(b)

    key = (b, depth)
    entry = tt.get(key)
    if entry is not None:
        val, flag = entry
        if flag == 0:
            return val
        if flag == 1:
            if val > alpha:
                alpha = val
        elif flag == -1:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    moves = list(_iter_moves(b))
    if not moves:
        return -WIN_SCORE + ply

    alpha0 = alpha
    beta0 = beta
    best = -INF

    ordered = _ordered_moves(b, moves, depth)
    limit = _limit_for(depth, len(ordered), ply)

    if depth <= 1:
        for i, m in enumerate(ordered[:limit]):
            if (i & 15) == 0 and time.perf_counter() > _DEADLINE:
                raise _Timeout()

            score = -_evaluate(_apply_swap(b, m))
            if score > best:
                best = score
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break
    else:
        for i, m in enumerate(ordered[:limit]):
            if (i & 15) == 0 and time.perf_counter() > _DEADLINE:
                raise _Timeout()

            child = _apply_swap(b, m)
            score = -_negamax(child, depth - 1, -beta, -alpha, ply + 1, tt)

            if score > best:
                best = score
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break

    if best <= alpha0:
        flag = -1
    elif best >= beta0:
        flag = 1
    else:
        flag = 0

    tt[key] = (best, flag)
    return best


def _root_cap(depth, n):
    if depth <= 2:
        return n
    if depth == 3:
        return min(n, 90)
    if depth == 4:
        return min(n, 60)
    return min(n, 40)


def _search_root(b, root_order, depth, tt):
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = root_order[0]

    cap = _root_cap(depth, len(root_order))
    searched = []

    for i, m in enumerate(root_order[:cap]):
        if (i & 7) == 0 and time.perf_counter() > _DEADLINE:
            raise _Timeout()

        child = _apply_swap(b, m)
        score = -_negamax(child, depth - 1, -beta, -alpha, 1, tt)
        searched.append((score, m))

        if score > best_score:
            best_score = score
            best_move = m

        if score > alpha:
            alpha = score

    searched.sort(key=lambda x: x[0], reverse=True)
    new_order = [m for _, m in searched]

    if cap < len(root_order):
        new_order.extend(root_order[cap:])

    return best_move, best_score, new_order


def policy(board) -> str:
    global _DEADLINE, _NODE_COUNT

    b = None
    try:
        start = time.perf_counter()
        _DEADLINE = start + 0.88
        _NODE_COUNT = 0

        b = _to_tuple(board)
        moves = list(_iter_moves(b))

        if not moves:
            return "0,0:0,0:0,0"

        if len(moves) == 1:
            return _move_to_str(moves[0])

        quick_order = sorted(moves, key=lambda m: _quick_score(b, m), reverse=True)

        scored = []
        best_move = quick_order[0]
        best_score = -INF

        for i, m in enumerate(quick_order):
            if (i & 15) == 0 and time.perf_counter() > _DEADLINE:
                break

            child = _apply_swap(b, m)
            sc = -_evaluate(child) + _quick_score(b, m) // 20

            if sc > best_score:
                best_score = sc
                best_move = m

            if sc > WIN_SCORE // 2:
                return _move_to_str(m)

            scored.append((sc, m))

        if scored:
            scored.sort(key=lambda x: x[0], reverse=True)
            root_order = [m for _, m in scored]

            if len(root_order) < len(quick_order):
                seen = set(root_order)
                root_order.extend(m for m in quick_order if m not in seen)

            best_move = root_order[0]
        else:
            root_order = quick_order

        if time.perf_counter() > _DEADLINE:
            return _move_to_str(best_move)

        tt = {}
        depth = 2

        while depth <= 12 and time.perf_counter() < _DEADLINE:
            try:
                bm, bs, root_order = _search_root(b, root_order, depth, tt)
                best_move = bm
                best_score = bs
                depth += 1
            except _Timeout:
                break

        return _move_to_str(best_move)

    except Exception:
        try:
            if b is None:
                b = _to_tuple(board)
            for m in _iter_moves(b):
                return _move_to_str(m)
        except Exception:
            pass

        return "0,0:0,0:0,0"
