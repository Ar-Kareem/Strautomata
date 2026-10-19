
import time

R, C = 5, 6
N = R * C
FULL = (1 << N) - 1
COL0 = 0
COL5 = 0
for _r in range(R):
    COL0 |= 1 << (_r * C)
    COL5 |= 1 << (_r * C + C - 1)
NC0 = FULL & ~COL0
NC5 = FULL & ~COL5

try:
    (0).bit_count()
    def pc(x):
        return x.bit_count()
except AttributeError:
    def pc(x):
        return bin(x).count('1')

WIN = 100000
TIME_LIMIT = 0.72
INF = float('inf')

TT = {}
_nodes = 0
_deadline = 0.0


class Timeout(Exception):
    pass


def mob(me, opp):
    return (pc(((me & NC5) << 1) & opp) + pc(((me & NC0) >> 1) & opp)
            + pc((me << 6) & opp) + pc((me >> 6) & opp))


def children(me, opp):
    res = []
    d = ((me & NC5) << 1) & opp
    while d:
        b = d & -d
        d ^= b
        s = b >> 1
        res.append(((me ^ s) | b, opp ^ b, s, 'R'))
    d = ((me & NC0) >> 1) & opp
    while d:
        b = d & -d
        d ^= b
        s = b << 1
        res.append(((me ^ s) | b, opp ^ b, s, 'L'))
    d = (me << 6) & opp
    while d:
        b = d & -d
        d ^= b
        s = b >> 6
        res.append(((me ^ s) | b, opp ^ b, s, 'D'))
    d = (me >> 6) & opp
    while d:
        b = d & -d
        d ^= b
        s = b << 6
        res.append(((me ^ s) | b, opp ^ b, s, 'U'))
    return res


def search(me, opp, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 255) == 0 and time.time() > _deadline:
        raise Timeout()
    # normalize: drop isolated pieces (they can never take part in play)
    a = me | opp
    nb = ((a & NC5) << 1) | ((a & NC0) >> 1) | ((a << 6) & FULL) | (a >> 6)
    me &= nb
    opp &= nb
    key = (me, opp)
    e = TT.get(key)
    ebest = None
    if e is not None:
        ed, ev, ef, ebest = e
        if ed >= depth or ev >= WIN - 100 or ev <= -WIN + 100:
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
    ch = children(me, opp)
    if not ch:
        return -(WIN - ply)
    if depth <= 1:
        best = -INF
        for nme, nopp, s, dr in ch:
            om = mob(nopp, nme)
            if om == 0:
                v = WIN - ply - 1
            else:
                v = mob(nme, nopp) - om
            if v > best:
                best = v
        return best
    scored = []
    for c in ch:
        nme = c[0]
        nopp = c[1]
        om = mob(nopp, nme)
        if om == 0:
            v = WIN - ply - 1
            TT[key] = (depth, v, 0, (nme, nopp))
            return v
        sc = mob(nme, nopp) - om
        if ebest is not None and nme == ebest[0] and nopp == ebest[1]:
            sc += 1000
        scored.append((sc, c))
    scored.sort(key=lambda t: t[0], reverse=True)
    best = -INF
    bestmove = None
    a0 = alpha
    for sc, c in scored:
        v = -search(c[0], c[1], depth - 1, -beta, -alpha, ply + 1)
        if v > best:
            best = v
            bestmove = (c[0], c[1])
        if v > alpha:
            alpha = v
        if alpha >= beta:
            break
    if best >= beta:
        flag = 1
    elif best <= a0:
        flag = 2
    else:
        flag = 0
    TT[key] = (depth, best, flag, bestmove)
    return best


def _move_str(c):
    s = c[2]
    idx = s.bit_length() - 1
    return "%d,%d,%s" % (idx // 6, idx % 6, c[3])


def policy(you, opponent):
    global _deadline, _nodes, TT
    start = time.time()
    _deadline = start + TIME_LIMIT
    me = 0
    opp = 0
    for r in range(R):
        yr = you[r]
        orow = opponent[r]
        for c in range(C):
            if int(yr[c]) == 1:
                me |= 1 << (r * C + c)
            elif int(orow[c]) == 1:
                opp |= 1 << (r * C + c)
    if len(TT) > 400000:
        TT = {}
    ch = children(me, opp)
    if not ch:
        return "0,0,U"
    # heuristic ordering / immediate wins
    scored = []
    for c in ch:
        om = mob(c[1], c[0])
        if om == 0:
            return _move_str(c)
        scored.append((mob(c[0], c[1]) - om, c))
    scored.sort(key=lambda t: t[0], reverse=True)
    order = [c for sc, c in scored]
    best_move = order[0]
    if len(order) == 1:
        return _move_str(best_move)
    depth = 2
    max_depth = pc(me | opp) + 2
    try:
        while depth <= max_depth:
            alpha = -INF
            beta = INF
            results = []
            cur_best = None
            cur_best_v = -INF
            try:
                for c in order:
                    v = -search(c[0], c[1], depth - 1, -beta, -alpha, 1)
                    results.append((v, c))
                    if v > cur_best_v:
                        cur_best_v = v
                        cur_best = c
                    if v > alpha:
                        alpha = v
            except Timeout:
                if cur_best is not None and results:
                    # first move fully searched; any later improvement is reliable
                    if cur_best_v > results[0][0] or cur_best is order[0]:
                        best_move = cur_best
                raise
            results.sort(key=lambda t: t[0], reverse=True)
            order = [c for v, c in results]
            best_move = order[0]
            top = results[0][0]
            if top >= WIN - 100:
                break
            if top <= -WIN + 100:
                break
            depth += 1
    except Timeout:
        pass
    return _move_str(best_move)
