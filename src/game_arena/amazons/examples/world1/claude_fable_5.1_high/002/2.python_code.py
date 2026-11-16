
import time
import numpy as np

N = 6
DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
RAYS = []
NEIGH = []
for _r in range(N):
    for _c in range(N):
        _rays = []
        _nb = []
        for _dr, _dc in DIRS:
            _ray = []
            _rr, _cc = _r + _dr, _c + _dc
            while 0 <= _rr < N and 0 <= _cc < N:
                _ray.append(_rr * N + _cc)
                _rr += _dr
                _cc += _dc
            if _ray:
                _rays.append(tuple(_ray))
                _nb.append(_ray[0])
        RAYS.append(tuple(_rays))
        NEIGH.append(tuple(_nb))

TIME_LIMIT = 0.6
WIN = 1000.0


class Timeout(Exception):
    pass


_deadline = 0.0
_killers = {}


def gen_moves(b, p):
    moves = []
    app = moves.append
    for frm in range(36):
        if b[frm] != p:
            continue
        b[frm] = 0
        for ray in RAYS[frm]:
            for to in ray:
                if b[to] != 0:
                    break
                for ray2 in RAYS[to]:
                    for a in ray2:
                        if b[a] != 0:
                            break
                        app((frm, to, a))
        b[frm] = p
    return moves


def has_move(b, p):
    for i in range(36):
        if b[i] == p:
            for n in NEIGH[i]:
                if b[n] == 0:
                    return True
    return False


def dists(b, p):
    d = [99] * 36
    frontier = []
    for i in range(36):
        if b[i] == p:
            d[i] = 0
            frontier.append(i)
    mob = 0
    nxt = []
    # first layer (also counts mobility)
    for sq in frontier:
        for ray in RAYS[sq]:
            for t in ray:
                if b[t] != 0:
                    break
                mob += 1
                if d[t] == 99:
                    d[t] = 1
                    nxt.append(t)
    frontier = nxt
    dist = 1
    while frontier:
        dist += 1
        nxt = []
        for sq in frontier:
            for ray in RAYS[sq]:
                for t in ray:
                    if b[t] != 0:
                        break
                    if d[t] == 99:
                        d[t] = dist
                        nxt.append(t)
        frontier = nxt
    return d, mob


def evaluate(b, p):
    q = 3 - p
    dm, mm = dists(b, p)
    do, mo = dists(b, q)
    t = 0.0
    for i in range(36):
        if b[i] == 0:
            a = dm[i]
            o = do[i]
            if a < o:
                t += 1.0
            elif o < a:
                t -= 1.0
            elif a < 99:
                t += 0.25
    return t + 0.12 * (mm - mo)


def negamax(b, p, depth, alpha, beta):
    if time.perf_counter() > _deadline:
        raise Timeout()
    if not has_move(b, p):
        return -(WIN + depth)
    if depth == 0:
        return evaluate(b, p)
    q = 3 - p
    moves = gen_moves(b, p)
    # ordering
    adjq = [0] * 36
    for sq in range(36):
        s = 0
        for n in NEIGH[sq]:
            if b[n] == q:
                s += 1
        adjq[sq] = s
    killer = _killers.get(depth)
    moves.sort(key=lambda m: -(3 * adjq[m[2]] + adjq[m[1]] + (1000 if m == killer else 0)))
    best = -1e9
    for m in moves:
        frm, to, a = m
        b[frm] = 0
        b[to] = p
        b[a] = -1
        try:
            v = -negamax(b, q, depth - 1, -beta, -alpha)
        finally:
            b[a] = 0
            b[to] = 0
            b[frm] = p
        if v > best:
            best = v
        if v > alpha:
            alpha = v
        if alpha >= beta:
            _killers[depth] = m
            break
    return best


def fmt(m):
    frm, to, a = m
    return "%d,%d:%d,%d:%d,%d" % (frm // N, frm % N, to // N, to % N, a // N, a % N)


def policy(board) -> str:
    global _deadline, _killers
    start = time.perf_counter()
    _deadline = start + TIME_LIMIT
    _killers = {}
    arr = np.asarray(board)
    b = [int(v) for row in arr.tolist() for v in row]
    moves = gen_moves(b, 1)
    if not moves:
        return "0,0:0,1:0,2"
    best_move = moves[0]
    order = moves
    depth = 1
    while depth <= 12:
        alpha = -1e9
        cur_best = None
        cur_scores = []
        try:
            for m in order:
                frm, to, a = m
                b[frm] = 0
                b[to] = 1
                b[a] = -1
                try:
                    v = -negamax(b, 2, depth - 1, -1e9, -alpha)
                finally:
                    b[a] = 0
                    b[to] = 0
                    b[frm] = 1
                cur_scores.append((v, m))
                if v > alpha:
                    alpha = v
                    cur_best = m
        except Timeout:
            if cur_best is not None:
                best_move = cur_best
            break
        if cur_best is not None:
            best_move = cur_best
        cur_scores.sort(key=lambda x: -x[0])
        order = [m for _, m in cur_scores]
        if alpha >= WIN or alpha <= -WIN:
            break
        depth += 1
        if time.perf_counter() > _deadline:
            break
    return fmt(best_move)
