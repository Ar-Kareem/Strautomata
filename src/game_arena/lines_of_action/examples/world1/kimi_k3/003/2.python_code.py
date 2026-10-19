
import time
from functools import lru_cache

FULL = (1 << 64) - 1
NOT_A = FULL ^ 0x0101010101010101  # everything except column 0
NOT_H = FULL ^ 0x8080808080808080  # everything except column 7

DIRS = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, 1), (-1, 1), (1, -1))

# Precomputed tables
RAY = [[None] * 8 for _ in range(64)]    # squares along each direction, ordered outward
LINE = [[0] * 8 for _ in range(64)]      # full-line mask through square for that axis
BETWEEN = [0] * 4096                     # strict-between mask for aligned square pairs
CENT = [0] * 64                          # centralization bonus per square

for _s in range(64):
    _r, _c = _s >> 3, _s & 7
    CENT[_s] = 7 - max(abs(2 * _r - 7), abs(2 * _c - 7))
    for _d in range(8):
        dr, dc = DIRS[_d]
        ray = []
        rr, cc = _r + dr, _c + dc
        while 0 <= rr < 8 and 0 <= cc < 8:
            ray.append((rr << 3) | cc)
            rr += dr
            cc += dc
        RAY[_s][_d] = ray

for _s in range(64):
    for _d in range(8):
        mask = 1 << _s
        for _q in RAY[_s][_d]:
            mask |= 1 << _q
        for _q in RAY[_s][_d ^ 1]:
            mask |= 1 << _q
        LINE[_s][_d] = mask

for _s in range(64):
    for _d in range(8):
        running = 0
        for _q in RAY[_s][_d]:
            BETWEEN[(_s << 6) | _q] = running
            running |= 1 << _q

WIN = 1 << 22
INF = WIN << 2
QMAX_PLY = 32
MAX_DEPTH = 24

# Evaluation weights
W_CONN = 140   # per extra connected component (bad)
W_DIST = 2     # per unit of summed squared distance to centroid (bad)
W_CENT = 3     # centralization bonus (good)

TT = {}
HIST = [0] * 4096
KILLERS = [[-1, -1] for _ in range(128)]
NODES = 0
DEADLINE = 0.0


def _dilate(b):
    d = ((b >> 8) | ((b << 8) & FULL) |
         ((b >> 1) & NOT_H) | ((b << 1) & NOT_A) |
         ((b >> 9) & NOT_H) | ((b << 7) & NOT_H) |
         ((b >> 7) & NOT_A) | ((b << 9) & NOT_A))
    return b | d


@lru_cache(maxsize=1 << 18)
def _ccount(bb):
    if bb == 0:
        return 0
    if bb & (bb - 1) == 0:
        return 1
    count = 0
    while bb:
        count += 1
        region = bb & -bb
        while True:
            newr = region | (_dilate(region) & bb)
            if newr == region:
                break
            region = newr
        bb &= ~region
    return count


@lru_cache(maxsize=1 << 17)
def _features(bb):
    # (piece count, components, sum of squared dist to centroid, centralization)
    n = 0
    sr = sc = srr = scc = cent = 0
    m = bb
    while m:
        lsb = m & -m
        s = lsb.bit_length() - 1
        m ^= lsb
        r = s >> 3
        c = s & 7
        n += 1
        sr += r
        sc += c
        srr += r * r
        scc += c * c
        cent += CENT[s]
    comps = 0
    b = bb
    while b:
        comps += 1
        region = b & -b
        while True:
            newr = region | (_dilate(region) & b)
            if newr == region:
                break
            region = newr
        b &= ~region
    conc = ((srr * n - sr * sr) + (scc * n - sc * sc)) // n
    return (n, comps, conc, cent)


def _evaluate(my, opp):
    n1, c1, d1, e1 = _features(my)
    n2, c2, d2, e2 = _features(opp)
    return W_CONN * (c2 - c1) + W_DIST * (d2 - d1) + W_CENT * (e1 - e2)


def _gen_moves(my, opp):
    occ = my | opp
    moves = []
    ap = moves.append
    m = my
    while m:
        lsb = m & -m
        s = lsb.bit_length() - 1
        m ^= lsb
        Ls = LINE[s]
        Rs = RAY[s]
        Bs = s << 6
        for d in range(8):
            dist = (Ls[d] & occ).bit_count()
            ray = Rs[d]
            if dist > len(ray):
                continue
            t = ray[dist - 1]
            if (my >> t) & 1:
                continue
            if BETWEEN[Bs | t] & opp:
                continue
            ap(Bs | t)
    return moves


def _order(moves, opp, ttmove, k1, k2):
    hist = HIST
    def key(m):
        sc = hist[m]
        if (opp >> (m & 63)) & 1:
            sc += 1 << 16
        if m == ttmove:
            sc += 1 << 22
        elif m == k1 or m == k2:
            sc += 1 << 18
        return sc
    moves.sort(key=key, reverse=True)


def _qsearch(my, opp, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() > DEADLINE:
        raise TimeoutError
    if _ccount(opp) == 1 or my == 0:
        return -WIN + ply
    if _ccount(my) == 1:
        return WIN - ply
    stand = _evaluate(my, opp)
    if stand >= beta:
        return stand
    if stand > alpha:
        alpha = stand
    if ply >= QMAX_PLY:
        return stand
    moves = _gen_moves(my, opp)
    caps = [m for m in moves if (opp >> (m & 63)) & 1]
    for mv in caps:
        t = mv & 63
        tb = 1 << t
        nmy = (my ^ (1 << (mv >> 6))) | tb
        nop = opp & ~tb
        val = -_qsearch(nop, nmy, -beta, -alpha, ply + 1)
        if val >= beta:
            return val
        if val > alpha:
            alpha = val
    return alpha


def _negamax(my, opp, depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise TimeoutError

    if _ccount(opp) == 1 or my == 0:
        return -WIN + ply
    if _ccount(my) == 1:
        return WIN - ply

    orig_alpha = alpha
    ttmove = -1
    key = (my, opp)
    entry = TT.get(key)
    if entry is not None:
        ed, ef, ev, eb = entry
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
        ttmove = eb

    if depth <= 0:
        return _qsearch(my, opp, alpha, beta, ply)

    moves = _gen_moves(my, opp)
    if not moves:
        return -WIN + ply
    k1, k2 = KILLERS[ply]
    _order(moves, opp, ttmove, k1, k2)

    best = -INF
    bestmove = moves[0]
    a = alpha
    for mv in moves:
        s = mv >> 6
        t = mv & 63
        tb = 1 << t
        nmy = (my ^ (1 << s)) | tb
        nop = opp & ~tb
        val = -_negamax(nop, nmy, depth - 1, -beta, -a, ply + 1)
        if val > best:
            best = val
            bestmove = mv
            if val > a:
                a = val
        if a >= beta:
            HIST[mv] += depth * depth
            if mv != k1:
                KILLERS[ply][1] = k1
                KILLERS[ply][0] = mv
            break

    if best <= orig_alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, flag, best, bestmove)
    return best


def _fmt(mv):
    s = mv >> 6
    t = mv & 63
    return "%d,%d:%d,%d" % (s >> 3, s & 7, t >> 3, t & 7)


def policy(board) -> str:
    global NODES, DEADLINE
    start = time.perf_counter()
    DEADLINE = start + 0.90
    NODES = 0

    my = 0
    opp = 0
    for r in range(8):
        row = board[r]
        base = r << 3
        for c in range(8):
            v = row[c]
            if v == 1:
                my |= 1 << (base | c)
            elif v == -1:
                opp |= 1 << (base | c)

    moves = _gen_moves(my, opp)
    if not moves:
        return "0,0:0,0"  # no legal moves (game should already be over)
    if len(moves) == 1:
        return _fmt(moves[0])

    # Instant win? Play it.
    for mv in moves:
        t = mv & 63
        tb = 1 << t
        nmy = (my ^ (1 << (mv >> 6))) | tb
        nop = opp & ~tb
        if nop == 0 or _ccount(nmy) == 1:
            return _fmt(mv)

    best_move = moves[0]
    try:
        for depth in range(1, MAX_DEPTH + 1):
            entry = TT.get((my, opp))
            ttmove = entry[3] if entry else -1
            _order(moves, opp, ttmove, -1, -1)
            alpha = -INF
            cur_val = -INF
            cur_move = moves[0]
            for mv in moves:
                NODES += 1
                if (NODES & 255) == 0 and time.perf_counter() > DEADLINE:
                    raise TimeoutError
                t = mv & 63
                tb = 1 << t
                nmy = (my ^ (1 << (mv >> 6))) | tb
                nop = opp & ~tb
                val = -_negamax(nop, nmy, depth - 1, -INF, -alpha, 1)
                if val > cur_val:
                    cur_val = val
                    cur_move = mv
                    if val > alpha:
                        alpha = val
            TT[(my, opp)] = (depth, 0, cur_val, cur_move)
            best_move = cur_move
            if cur_val >= WIN - 64:  # forced win found
                break
    except TimeoutError:
        pass

    return _fmt(best_move)
