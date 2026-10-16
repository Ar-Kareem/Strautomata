
import time

_ROWS, _COLS = 5, 6
_N = 30
_FULL = (1 << _N) - 1
_COL0 = 0
_COL5 = 0
for _r in range(_ROWS):
    _COL0 |= 1 << (_r * 6)
    _COL5 |= 1 << (_r * 6 + 5)
_NOT_COL0 = _FULL ^ _COL0
_NOT_COL5 = _FULL ^ _COL5

try:
    _popcount = int.bit_count
except AttributeError:
    def _popcount(x):
        return bin(x).count('1')

WIN = 100000
INF = 10 ** 9

_TT = {}
_HIST = {}
_nodes = 0
_deadline = 0.0
_pbest = None
_pval = -INF
_pcount = 0


class _Timeout(Exception):
    pass


def _gen(me, opp):
    moves = []
    d = (me << 1) & _NOT_COL0 & opp          # right
    while d:
        b = d & -d
        moves.append((b >> 1, b))
        d ^= b
    d = (me >> 1) & _NOT_COL5 & opp          # left
    while d:
        b = d & -d
        moves.append((b << 1, b))
        d ^= b
    d = (me << 6) & opp                      # down
    while d:
        b = d & -d
        moves.append((b >> 6, b))
        d ^= b
    d = (me >> 6) & opp                      # up
    while d:
        b = d & -d
        moves.append((b << 6, b))
        d ^= b
    return moves


def _nb(x):
    return (((x << 1) & _NOT_COL0) | ((x >> 1) & _NOT_COL5)
            | ((x << 6) & _FULL) | (x >> 6))


def _eval(me, opp):
    return _popcount(me & _nb(opp)) - _popcount(opp & _nb(me))


def _search(me, opp, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()

    key = (me, opp)
    ttmove = None
    e = _TT.get(key)
    if e is not None:
        edepth, ev, eflag, ttmove = e
        if edepth >= depth:
            if ev > WIN - 5000:
                ev -= ply
            elif ev < -(WIN - 5000):
                ev += ply
            if eflag == 0:
                return ev
            if eflag == 1 and ev >= beta:
                return ev
            if eflag == 2 and ev <= alpha:
                return ev

    moves = _gen(me, opp)
    if not moves:
        return -(WIN - ply)
    if depth <= 0:
        return _eval(me, opp)

    if len(moves) > 1:
        moves.sort(key=lambda m: -_HIST.get(m, 0))
        if ttmove is not None and ttmove in moves:
            moves.remove(ttmove)
            moves.insert(0, ttmove)

    alpha_orig = alpha
    best = -INF
    bestmove = None
    for m in moves:
        s, d = m
        nme = (me ^ s) | d
        nopp = opp ^ d
        sc = -_search(nopp, nme, depth - 1, -beta, -alpha, ply + 1)
        if sc > best:
            best = sc
            bestmove = m
        if best > alpha:
            alpha = best
        if alpha >= beta:
            _HIST[m] = _HIST.get(m, 0) + depth * depth
            break

    if best <= alpha_orig:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    store = best
    if store > WIN - 5000:
        store += ply
    elif store < -(WIN - 5000):
        store -= ply
    _TT[key] = (depth, store, flag, bestmove)
    return best


def _root(me, opp, depth, order):
    global _pbest, _pval, _pcount
    _pbest = None
    _pval = -INF
    _pcount = 0
    alpha = -INF
    beta = INF
    scored = []
    for m in order:
        s, d = m
        nme = (me ^ s) | d
        nopp = opp ^ d
        sc = -_search(nopp, nme, depth - 1, -beta, -alpha, 1)
        scored.append((sc, m))
        _pcount += 1
        if sc > _pval:
            _pval = sc
            _pbest = m
        if sc > alpha:
            alpha = sc
    scored.sort(key=lambda x: -x[0])
    return _pval, _pbest, [m for _, m in scored]


def _fmt(m):
    s, d = m
    si = s.bit_length() - 1
    di = d.bit_length() - 1
    r, c = divmod(si, 6)
    diff = di - si
    if diff == 1:
        dr = 'R'
    elif diff == -1:
        dr = 'L'
    elif diff == 6:
        dr = 'D'
    else:
        dr = 'U'
    return "%d,%d,%s" % (r, c, dr)


def policy(you, opponent):
    global _deadline, _nodes, _TT
    start = time.perf_counter()
    me = 0
    opp = 0
    for r in range(_ROWS):
        for c in range(_COLS):
            if you[r][c]:
                me |= 1 << (r * 6 + c)
            if opponent[r][c]:
                opp |= 1 << (r * 6 + c)

    moves = _gen(me, opp)
    if not moves:
        return "0,0,U"
    if len(moves) == 1:
        return _fmt(moves[0])

    best_move = moves[0]
    try:
        if len(_TT) > 1500000:
            _TT = {}
        _deadline = start + 0.80
        _nodes = 0
        best_val = -INF
        order = list(moves)
        for depth in range(1, 40):
            try:
                val, mv, order = _root(me, opp, depth, order)
                if mv is not None:
                    best_move = mv
                    best_val = val
                if abs(val) >= WIN - 5000:
                    break
            except _Timeout:
                if _pcount >= 1 and _pbest is not None and _pval > -(WIN - 5000):
                    best_move = _pbest
                break
    except Exception:
        pass

    # Final legality safeguard
    if best_move not in moves:
        best_move = moves[0]
    return _fmt(best_move)
