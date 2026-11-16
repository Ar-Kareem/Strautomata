
import numpy as np
import time

N = 6
NN = 36
INF = 99
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
RAYS = []
for _r in range(N):
    for _c in range(N):
        _rays = []
        for _dr, _dc in DIRS:
            _ray = []
            _rr, _cc = _r + _dr, _c + _dc
            while 0 <= _rr < N and 0 <= _cc < N:
                _ray.append(_rr * N + _cc)
                _rr += _dr
                _cc += _dc
            if _ray:
                _rays.append(tuple(_ray))
        RAYS.append(tuple(_rays))


class Timeout(Exception):
    pass


_deadline = 0.0
_nodes = 0


def gen_moves(b, player):
    moves = []
    app = moves.append
    for sq in range(NN):
        if b[sq] == player:
            b[sq] = 0
            for ray in RAYS[sq]:
                for t in ray:
                    if b[t]:
                        break
                    for aray in RAYS[t]:
                        for a in aray:
                            if b[a]:
                                break
                            app((sq, t, a))
            b[sq] = player
    return moves


def queen_dist(b, player, dist):
    frontier = [sq for sq in range(NN) if b[sq] == player]
    for sq in frontier:
        dist[sq] = 0
    d = 0
    while frontier:
        d += 1
        nxt = []
        for sq in frontier:
            for ray in RAYS[sq]:
                for t in ray:
                    if b[t]:
                        break
                    if dist[t] > d:
                        dist[t] = d
                        nxt.append(t)
        frontier = nxt


def evaluate(b, player):
    opp = 3 - player
    dm = [INF] * NN
    do = [INF] * NN
    queen_dist(b, player, dm)
    queen_dist(b, opp, do)
    t = 0.0
    mm = 0
    mo = 0
    for sq in range(NN):
        if b[sq]:
            continue
        a = dm[sq]
        o = do[sq]
        if a == 1:
            mm += 1
        if o == 1:
            mo += 1
        if a < o:
            t += 1.0
        elif o < a:
            t -= 1.0
        elif a < INF:
            t += 0.15
    if mm == 0:
        return -1000.0
    if mo == 0:
        t += 30.0
    return t + 0.15 * (mm - mo)


def make(b, m, player):
    b[m[0]] = 0
    b[m[1]] = player
    b[m[2]] = -1


def unmake(b, m, player):
    b[m[2]] = 0
    b[m[1]] = 0
    b[m[0]] = player


def kfor(nm):
    k = 2200 // max(nm, 1)
    return max(3, min(k, 20))


def search(b, player, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 7) == 0 and time.time() > _deadline:
        raise Timeout()
    moves = gen_moves(b, player)
    if not moves:
        return -1000.0 - depth
    opp = 3 - player
    scored = []
    i = 0
    for m in moves:
        i += 1
        if (i & 31) == 0 and time.time() > _deadline:
            raise Timeout()
        make(b, m, player)
        v = -evaluate(b, opp)
        unmake(b, m, player)
        scored.append((v, m))
    scored.sort(reverse=True)
    if depth <= 1:
        return scored[0][0]
    K = kfor(len(moves))
    best = -1e9
    for v, m in scored[:K]:
        make(b, m, player)
        try:
            val = -search(b, opp, depth - 1, -beta, -alpha)
        finally:
            unmake(b, m, player)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best


def fmt(m):
    fr, fc = divmod(m[0], N)
    tr, tc = divmod(m[1], N)
    ar, ac = divmod(m[2], N)
    return "%d,%d:%d,%d:%d,%d" % (fr, fc, tr, tc, ar, ac)


def policy(board) -> str:
    global _deadline, _nodes
    start = time.time()
    _deadline = start + 0.70
    _nodes = 0
    try:
        b = [int(x) for x in np.asarray(board).reshape(-1)]
    except Exception:
        b = [int(board[r][c]) for r in range(N) for c in range(N)]
    moves = gen_moves(b, 1)
    if not moves:
        return "0,0:0,1:0,2"
    if len(moves) == 1:
        return fmt(moves[0])
    best = moves[0]
    # depth-1 static ordering (always completed)
    scored = []
    bestv = -1e9
    for m in moves:
        make(b, m, 1)
        v = -evaluate(b, 2)
        unmake(b, m, 1)
        scored.append((v, m))
        if v > bestv:
            bestv = v
            best = m
    scored.sort(reverse=True)
    best = scored[0][1]
    if bestv >= 900:
        return fmt(best)
    ordered = scored
    rootK = max(5, kfor(len(moves)))
    depth = 2
    while depth <= 12:
        if time.time() > _deadline:
            break
        cur = []
        alpha = -1e9
        cur_best = None
        try:
            for v0, m in ordered[:rootK]:
                make(b, m, 1)
                val = -search(b, 2, depth - 1, -1e9, -alpha)
                unmake(b, m, 1)
                cur.append((val, m))
                if val > alpha:
                    alpha = val
                    cur_best = m
        except Timeout:
            if cur_best is not None:
                best = cur_best
            break
        cur.sort(reverse=True)
        best = cur[0][1]
        ordered = cur + list(ordered[rootK:])
        if abs(alpha) >= 900:
            break
        depth += 1
    return fmt(best)
