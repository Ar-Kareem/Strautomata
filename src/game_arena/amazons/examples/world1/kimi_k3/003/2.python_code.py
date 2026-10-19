
import time
import random
from collections import deque

N = 6
NN = 36
DIRS = ((-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1))

ROWS = tuple(i // N for i in range(NN))
COLS = tuple(i % N for i in range(NN))

RAYS = []
for r in range(N):
    for c in range(N):
        rr = []
        for dr, dc in DIRS:
            line = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < N and 0 <= nc < N:
                line.append(nr * N + nc)
                nr += dr
                nc += dc
            rr.append(tuple(line))
        RAYS.append(tuple(rr))
RAYS = tuple(RAYS)

CENT = tuple(10 - (abs(2 * ROWS[i] - 5) + abs(2 * COLS[i] - 5)) for i in range(NN))

_rng = random.Random(0x5EED5EED)
ZOB = [[_rng.getrandbits(64) for _ in range(3)] for __ in range(NN)]  # 0: us, 1: opponent, 2: arrow

INF = 10 ** 12
MATE = 10 ** 9
DINF = 127

TT = {}
EVAL = {}
START = 0.0
LIMIT = 0.0
NODE = 0

class _Timeout(Exception):
    pass


def _tick():
    global NODE
    NODE += 1
    if (NODE & 1023) == 0 and time.time() >= LIMIT:
        raise _Timeout()


def _hash(b):
    h = 0
    for i, v in enumerate(b):
        if v == 1:
            h ^= ZOB[i][0]
        elif v == 2:
            h ^= ZOB[i][1]
        elif v == -1:
            h ^= ZOB[i][2]
    return h


def _has_move(b, p):
    for i, v in enumerate(b):
        if v != p:
            continue
        for ray in RAYS[i]:
            for t in ray:
                if b[t] != 0:
                    break
                return True
    return False


def _gen(b, p):
    moves = []
    for s, v in enumerate(b):
        if v != p:
            continue
        for ray in RAYS[s]:
            for t in ray:
                if b[t] != 0:
                    break
                # Amazon moves s -> t. Now shoot from t; s is vacated and may be crossed/occupied by the arrow.
                for ray2 in RAYS[t]:
                    for u in ray2:
                        if u == s:
                            moves.append((s, t, u))
                            continue
                        if b[u] != 0:
                            break
                        moves.append((s, t, u))
    return moves


def _dist(b, p):
    d = [DINF] * NN
    q = deque()
    for i, v in enumerate(b):
        if v == p:
            d[i] = 0
            q.append(i)
    while q:
        x = q.popleft()
        nd = d[x] + 1
        for ray in RAYS[x]:
            for y in ray:
                if b[y] != 0:
                    break
                if d[y] > nd:
                    d[y] = nd
                    q.append(y)
    return d


def _mobility(b, p):
    total = 0
    dead = 0
    n = 0
    for i, v in enumerate(b):
        if v != p:
            continue
        n += 1
        c = 0
        for ray in RAYS[i]:
            for t in ray:
                if b[t] != 0:
                    break
                c += 1
        total += c
        if c == 0:
            dead += 1
    return total, dead, n


def _evaluate(b):
    d1 = _dist(b, 1)
    d2 = _dist(b, 2)
    m1, dead1, _ = _mobility(b, 1)
    m2, dead2, _ = _mobility(b, 2)

    terr = 0
    ctrl = 0
    for i, v in enumerate(b):
        if v != 0:
            continue
        a = d1[i]
        o = d2[i]
        if a == DINF and o == DINF:
            continue
        if a < o:
            terr += 1
            if a <= 8:
                ctrl += 9 - a
        elif o < a:
            terr -= 1
            if o <= 8:
                ctrl -= 9 - o

    return 50 * terr + 7 * ctrl + 4 * (m1 - m2) + 150 * (dead2 - dead1)


def _order(b, p, moves, bm=None):
    opp = 2 if p == 1 else 1
    op = [i for i, v in enumerate(b) if v == opp]

    def key(mv):
        s, t, u = mv
        score = CENT[t] + 3 * CENT[u] - CENT[s]
        ur = ROWS[u]
        uc = COLS[u]
        for o in op:
            dr = ur - ROWS[o]
            dc = uc - COLS[o]
            if dr < 0:
                dr = -dr
            if dc < 0:
                dc = -dc
            ch = dr if dr >= dc else dc
            if ch == 1:
                score += 14
            elif ch == 2:
                score += 6
            if dr == 0 or dc == 0 or dr == dc:
                score += 3
        return score

    if bm is not None and bm in moves:
        moves.remove(bm)
        moves.sort(key=key, reverse=True)
        return [bm] + moves
    moves.sort(key=key, reverse=True)
    return moves


def _search(b, h, p, depth, alpha, beta, ply):
    _tick()
    key = (h, p)
    ent = TT.get(key)
    bm = None
    if ent is not None:
        if ent[0] >= depth and ent[2]:
            return ent[1]
        bm = ent[3]

    if depth == 0:
        if not _has_move(b, p):
            return -MATE + ply if p == 1 else MATE - ply
        val = EVAL.get(h)
        if val is None:
            val = _evaluate(b)
            if len(EVAL) > 250000:
                EVAL.clear()
            EVAL[h] = val
        return val

    moves = _gen(b, p)
    if not moves:
        return -MATE + ply if p == 1 else MATE - ply

    moves = _order(b, p, moves, bm)
    a0, b0 = alpha, beta
    pidx = p - 1
    bestmove = None

    if p == 1:
        best = -INF
        for s, t, u in moves:
            h2 = h ^ ZOB[s][pidx] ^ ZOB[t][pidx] ^ ZOB[u][2]
            b[s] = 0
            b[t] = p
            b[u] = -1
            try:
                val = _search(b, h2, 2, depth - 1, alpha, beta, ply + 1)
            finally:
                b[u] = 0
                b[t] = 0
                b[s] = p
            if val > best:
                best = val
                bestmove = (s, t, u)
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
    else:
        best = INF
        for s, t, u in moves:
            h2 = h ^ ZOB[s][pidx] ^ ZOB[t][pidx] ^ ZOB[u][2]
            b[s] = 0
            b[t] = p
            b[u] = -1
            try:
                val = _search(b, h2, 1, depth - 1, alpha, beta, ply + 1)
            finally:
                b[u] = 0
                b[t] = 0
                b[s] = p
            if val < best:
                best = val
                bestmove = (s, t, u)
            if best < beta:
                beta = best
            if alpha >= beta:
                break

    exact = a0 < best < b0
    old = TT.get(key)
    if old is None or depth > old[0] or (depth == old[0] and (exact or not old[2])):
        TT[key] = (depth, best, exact, bestmove)
    elif bestmove is not None and old[3] is None:
        TT[key] = (old[0], old[1], old[2], bestmove)
    return best


def _root(depth, b, h, first_move):
    _tick()
    moves = _gen(b, 1)
    if not moves:
        return -MATE, None
    moves = _order(b, 1, moves, first_move)

    alpha = -INF
    beta = INF
    bestval = -INF
    bestmove = moves[0]

    for s, t, u in moves:
        if time.time() >= LIMIT:
            raise _Timeout()
        h2 = h ^ ZOB[s][0] ^ ZOB[t][0] ^ ZOB[u][2]
        b[s] = 0
        b[t] = 1
        b[u] = -1
        try:
            val = _search(b, h2, 2, depth - 1, alpha, beta, 1)
        finally:
            b[u] = 0
            b[t] = 0
            b[s] = 1
        if val > bestval:
            bestval = val
            bestmove = (s, t, u)
        if bestval > alpha:
            alpha = bestval

    return bestval, bestmove


def _fmt(mv):
    s, t, u = mv
    return f"{ROWS[s]},{COLS[s]}:{ROWS[t]},{COLS[t]}:{ROWS[u]},{COLS[u]}"


def policy(board) -> str:
    global START, LIMIT, NODE
    START = time.time()
    LIMIT = START + 0.93
    NODE = 0

    b = [int(v) for v in board.ravel()]
    moves = _gen(b, 1)
    if not moves:
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        return _fmt(moves[0])

    if len(TT) > 250000:
        TT.clear()
    if len(EVAL) > 250000:
        EVAL.clear()

    h = _hash(b)
    best = _order(b, 1, moves, None)[0]

    for depth in range(1, 9):
        if time.time() >= LIMIT:
            break
        try:
            val, mv = _root(depth, b, h, best)
        except _Timeout:
            break
        if mv is not None:
            best = mv
            TT[(h, 1)] = (depth, val, True, best)
        if val >= MATE // 2 or val <= -MATE // 2:
            break

    return _fmt(best)
