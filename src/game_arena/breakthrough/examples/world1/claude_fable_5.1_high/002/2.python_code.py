
import time

FULL = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H
ROW = [0xFF << (8 * r) for r in range(8)]
GOAL = [ROW[7], ROW[0]]  # indexed by side to move: 0 = white, 1 = black
WIN = 100000
INF = 10 ** 9
RUN = 1500
QMAX = 3
TIME_BUDGET = 0.65

try:
    popcount = int.bit_count
    popcount(3)
except AttributeError:
    def popcount(x):
        return bin(x).count('1')

# Cones: squares from which an enemy could possibly intercept a runner
CONE_W = [0] * 64
CONE_B = [0] * 64
for _s in range(64):
    _r, _c = divmod(_s, 8)
    _mw = 0
    _mb = 0
    for _r2 in range(8):
        for _c2 in range(8):
            _dr = _r2 - _r
            if _dr > 0 and abs(_c2 - _c) <= _dr:
                _mw |= 1 << (_r2 * 8 + _c2)
            _dr = _r - _r2
            if _dr > 0 and abs(_c2 - _c) <= _dr:
                _mb |= 1 << (_r2 * 8 + _c2)
    CONE_W[_s] = _mw
    CONE_B[_s] = _mb

WROW = [0, 1, 3, 7, 13, 22, 40, 0]
BROW = [0, 40, 22, 13, 7, 3, 1, 0]
HOME = [0, 10, 18, 25, 30, 33, 35, 36, 37]


class TimeUp(Exception):
    pass


TT = {}
HIST = {}
KILLERS = [[None, None] for _ in range(96)]
nodes = 0
deadline = 0.0
root_partial = [None]


def attacks(own, stm):
    if stm == 0:
        return (((own & NOT_A) << 7) | ((own & NOT_H) << 9)) & FULL
    return ((own & NOT_A) >> 9) | ((own & NOT_H) >> 7)


def goal_threats(own, other, stm):
    """Bitboard of 'own' pieces (side stm) that can reach the goal row next move."""
    if stm == 0:
        pen = own & ROW[6]
        if not pen:
            return 0
        empty = FULL & ~(own | other)
        srcs = (((pen << 8) & empty) >> 8)
        srcs |= ((((pen & NOT_A) << 7) & FULL & ~own) >> 7)
        srcs |= ((((pen & NOT_H) << 9) & FULL & ~own) >> 9)
        return srcs & pen
    else:
        pen = own & ROW[1]
        if not pen:
            return 0
        empty = FULL & ~(own | other)
        srcs = (((pen >> 8) & empty) << 8)
        srcs |= ((((pen & NOT_A) >> 9) & ~own) << 9)
        srcs |= ((((pen & NOT_H) >> 7) & ~own) << 7)
        return srcs & pen


def gen(w, b, stm, caps_only=False):
    moves = []
    if stm == 0:
        own = w
        opp = b
        notown = FULL ^ own
        if not caps_only:
            empty = notown ^ opp
            t = (own << 8) & empty
            while t:
                l = t & -t
                s = l.bit_length() - 1
                t ^= l
                moves.append((s - 8, s, 0))
            mask = notown
        else:
            mask = opp
        t = ((own & NOT_A) << 7) & mask
        while t:
            l = t & -t
            s = l.bit_length() - 1
            t ^= l
            moves.append((s - 7, s, 1 if (l & opp) else 0))
        t = ((own & NOT_H) << 9) & mask
        while t:
            l = t & -t
            s = l.bit_length() - 1
            t ^= l
            moves.append((s - 9, s, 1 if (l & opp) else 0))
    else:
        own = b
        opp = w
        notown = FULL ^ own
        if not caps_only:
            empty = notown ^ opp
            t = (own >> 8) & empty
            while t:
                l = t & -t
                s = l.bit_length() - 1
                t ^= l
                moves.append((s + 8, s, 0))
            mask = notown
        else:
            mask = opp
        t = ((own & NOT_A) >> 9) & mask
        while t:
            l = t & -t
            s = l.bit_length() - 1
            t ^= l
            moves.append((s + 9, s, 1 if (l & opp) else 0))
        t = ((own & NOT_H) >> 7) & mask
        while t:
            l = t & -t
            s = l.bit_length() - 1
            t ^= l
            moves.append((s + 7, s, 1 if (l & opp) else 0))
    return moves


def evaluate(w, b, stm):
    wc = popcount(w)
    bc = popcount(b)
    score = (wc - bc) * 100
    for r in range(1, 7):
        m = ROW[r]
        score += popcount(w & m) * WROW[r] - popcount(b & m) * BROW[r]
    score += HOME[popcount(w & ROW[0])] - HOME[popcount(b & ROW[7])]
    watt = (((w & NOT_A) << 7) | ((w & NOT_H) << 9)) & FULL
    batt = ((b & NOT_A) >> 9) | ((b & NOT_H) >> 7)
    score += (popcount(w & watt) - popcount(b & batt)) * 4
    hw = w & batt & ~watt
    hb = b & watt & ~batt
    if stm == 0:
        score += popcount(hb) * 45 - popcount(hw) * 12
    else:
        score += popcount(hb) * 12 - popcount(hw) * 45
    # free runners
    wbest = 99
    x = w
    while x:
        l = x & -x
        s = l.bit_length() - 1
        x ^= l
        if not (b & CONE_W[s]):
            d = 7 - (s >> 3)
            if d < wbest:
                wbest = d
    bbest = 99
    x = b
    while x:
        l = x & -x
        s = l.bit_length() - 1
        x ^= l
        if not (w & CONE_B[s]):
            d = s >> 3
            if d < bbest:
                bbest = d
    if wbest < 99 or bbest < 99:
        if stm == 0:
            if wbest <= bbest:
                score += RUN - wbest * 100
            else:
                score -= RUN - bbest * 100
        else:
            if bbest <= wbest:
                score -= RUN - bbest * 100
            else:
                score += RUN - wbest * 100
    return score if stm == 0 else -score


def order(moves, stm, ttm, ply):
    k0, k1 = KILLERS[ply]
    if stm == 0:
        def key(m):
            if m == ttm:
                return 1 << 30
            frm, to, cap = m
            if cap:
                return 100000 + (to >> 3) * 100
            if m == k0:
                return 90000
            if m == k1:
                return 80000
            return HIST.get((0, frm, to), 0) * 4 + (to >> 3)
    else:
        def key(m):
            if m == ttm:
                return 1 << 30
            frm, to, cap = m
            if cap:
                return 100000 + (7 - (to >> 3)) * 100
            if m == k0:
                return 90000
            if m == k1:
                return 80000
            return HIST.get((1, frm, to), 0) * 4 + (7 - (to >> 3))
    moves.sort(key=key, reverse=True)


def search(w, b, stm, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 511) == 0 and time.perf_counter() > deadline:
        raise TimeUp()
    if stm == 0:
        own = w
        opp = b
    else:
        own = b
        opp = w
    if goal_threats(own, opp, stm):
        return WIN - ply
    thr = goal_threats(opp, own, 1 - stm)
    forced = 0
    if thr:
        if (thr & (thr - 1)) or not (thr & attacks(own, stm)):
            return -(WIN - ply - 1)
        forced = thr
    key = (w, b, stm)
    e = TT.get(key)
    ttm = None
    if e is not None:
        if e[0] >= depth:
            f = e[1]
            sc = e[2]
            if f == 0 or (f == 1 and sc >= beta) or (f == 2 and sc <= alpha):
                return sc
        ttm = e[3]
    qmode = depth <= 0
    best = -INF
    if qmode and not forced:
        stand = evaluate(w, b, stm)
        if depth <= -QMAX or stand >= beta:
            return stand
        if stand > alpha:
            alpha = stand
        best = stand
    moves = gen(w, b, stm, qmode)
    if forced:
        moves = [m for m in moves if (1 << m[1]) & forced]
    if not moves:
        if qmode:
            return best
        return evaluate(w, b, stm)
    if len(moves) > 1:
        order(moves, stm, ttm, ply)
    alpha0 = alpha
    bestm = None
    goal = GOAL[stm]
    for m in moves:
        frm, to, cap = m
        tb = 1 << to
        if tb & goal:
            sc = WIN - ply
        elif stm == 0:
            nw = (w ^ (1 << frm)) | tb
            nb = b & ~tb
            if nb == 0:
                sc = WIN - ply
            else:
                sc = -search(nw, nb, 1, depth - 1, -beta, -alpha, ply + 1)
        else:
            nb = (b ^ (1 << frm)) | tb
            nw = w & ~tb
            if nw == 0:
                sc = WIN - ply
            else:
                sc = -search(nw, nb, 0, depth - 1, -beta, -alpha, ply + 1)
        if sc > best:
            best = sc
            bestm = m
            if sc > alpha:
                alpha = sc
                if alpha >= beta:
                    if not cap:
                        k = KILLERS[ply]
                        if k[0] != m:
                            k[1] = k[0]
                            k[0] = m
                        hk = (stm, frm, to)
                        HIST[hk] = HIST.get(hk, 0) + depth * depth
                    break
    if depth >= 1:
        if best <= alpha0:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        TT[key] = (depth, flag, best, bestm)
    return best


def root(w, b, stm, depth, prev):
    if stm == 0:
        own, opp = w, b
    else:
        own, opp = b, w
    moves = gen(w, b, stm)
    thr = goal_threats(opp, own, 1 - stm)
    if thr and not (thr & (thr - 1)):
        f = [m for m in moves if (1 << m[1]) & thr]
        if f:
            moves = f
    order(moves, stm, prev, 0)
    alpha = -INF
    beta = INF
    best = -INF
    bestm = None
    goal = GOAL[stm]
    for m in moves:
        frm, to, cap = m
        tb = 1 << to
        if tb & goal:
            sc = WIN
        elif stm == 0:
            nw = (w ^ (1 << frm)) | tb
            nb = b & ~tb
            if nb == 0:
                sc = WIN
            else:
                sc = -search(nw, nb, 1, depth - 1, -beta, -alpha, 1)
        else:
            nb = (b ^ (1 << frm)) | tb
            nw = w & ~tb
            if nw == 0:
                sc = WIN
            else:
                sc = -search(nw, nb, 0, depth - 1, -beta, -alpha, 1)
        if sc > best:
            best = sc
            bestm = m
            root_partial[0] = m
        if sc > alpha:
            alpha = sc
    return best, bestm


def fmt(m):
    frm, to = m[0], m[1]
    return ((frm >> 3, frm & 7), (to >> 3, to & 7))


def policy(me, opp, color):
    global deadline, nodes
    start = time.perf_counter()
    mine = 0
    for r, c in me:
        mine |= 1 << (r * 8 + c)
    theirs = 0
    for r, c in opp:
        theirs |= 1 << (r * 8 + c)
    if color == 'w':
        w, b, stm = mine, theirs, 0
    else:
        w, b, stm = theirs, mine, 1
    moves = gen(w, b, stm)
    if not moves:
        r, c = me[0]
        return ((r, c), (r + (1 if color == 'w' else -1), c))
    goal = GOAL[stm]
    for m in moves:
        if (1 << m[1]) & goal:
            return fmt(m)
    # heuristic fallback
    fb = list(moves)
    try:
        order(fb, stm, None, 0)
    except Exception:
        pass
    fallback = fb[0]
    best = fallback
    try:
        deadline = start + TIME_BUDGET
        nodes = 0
        TT.clear()
        HIST.clear()
        for k in KILLERS:
            k[0] = None
            k[1] = None
        prev = None
        try:
            for depth in range(1, 40):
                root_partial[0] = None
                sc, mv = root(w, b, stm, depth, prev)
                if mv is not None:
                    best = mv
                    prev = mv
                if abs(sc) >= WIN - 200:
                    break
                if time.perf_counter() > deadline:
                    break
        except TimeUp:
            if root_partial[0] is not None:
                best = root_partial[0]
    except Exception:
        best = fallback
    if best not in moves:
        best = fallback
    return fmt(best)
