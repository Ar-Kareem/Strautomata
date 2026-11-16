
import sys
import time

sys.setrecursionlimit(10000)

ROWS = 5
COLS = 6
STRIDE = 7                 # 6 columns + 1 guard column (wrap-safe shifts)
WIN = 1 << 20
INF = 1 << 21
TERM = 1 << 19             # scores beyond this are terminal (mate) scores
TIME_BUDGET = 0.85         # seconds per move (hard cap is 1s)

TT = {}                    # persistent transposition table
MAX_TT = 400000

_nodes = 0


class _Timeout(Exception):
    pass


def _mob(me, opp):
    """Exact number of legal captures for side `me`."""
    return (((me << 1) & opp).bit_count()
            + ((me >> 1) & opp).bit_count()
            + ((me << STRIDE) & opp).bit_count()
            + ((me >> STRIDE) & opp).bit_count())


def _eval(me, opp):
    """Heuristic score from the perspective of the side to move."""
    return ((_mob(me, opp) - _mob(opp, me)) << 5) \
        + (me.bit_count() - opp.bit_count())


def _gen(me, opp):
    """All legal captures as (from, to) index pairs."""
    moves = []
    ap = moves.append
    t = (me << 1) & opp
    while t:
        b = t & -t
        j = b.bit_length() - 1
        t ^= b
        ap((j - 1, j))
    t = (me >> 1) & opp
    while t:
        b = t & -t
        j = b.bit_length() - 1
        t ^= b
        ap((j + 1, j))
    t = (me << STRIDE) & opp
    while t:
        b = t & -t
        j = b.bit_length() - 1
        t ^= b
        ap((j - STRIDE, j))
    t = (me >> STRIDE) & opp
    while t:
        b = t & -t
        j = b.bit_length() - 1
        t ^= b
        ap((j + STRIDE, j))
    return moves


def _search(me, opp, depth, alpha, beta, ply, deadline):
    """Negamax with alpha-beta, PVS, and transposition table."""
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() >= deadline:
        raise _Timeout()

    key = me | (opp << 40)
    a0, b0 = alpha, beta
    tt_move = None
    e = TT.get(key)
    if e is not None:
        ed, ev, ef, em = e
        if ed >= depth:
            v = ev - ply if ev > TERM else (ev + ply if ev < -TERM else ev)
            if ef == 0:
                return v
            if ef == 1:
                if v >= beta:
                    return v
                if v > alpha:
                    alpha = v
            else:
                if v <= alpha:
                    return v
                if v < beta:
                    beta = v
            if alpha >= beta:
                return v
        tt_move = em

    moves = _gen(me, opp)
    if not moves:
        return -(WIN - ply)          # side to move has no capture: loss
    if depth <= 0:
        return _eval(me, opp)

    # Build child states; order by opponent mobility ascending (deep nodes only).
    scored = []
    ap = scored.append
    if depth >= 2:
        for (i, j) in moves:
            bj = 1 << j
            m2 = (me ^ (1 << i)) | bj
            o2 = opp ^ bj
            ap((_mob(o2, m2), i, j, m2, o2))
        scored.sort(key=lambda x: x[0])
    else:
        for (i, j) in moves:
            bj = 1 << j
            m2 = (me ^ (1 << i)) | bj
            o2 = opp ^ bj
            ap((0, i, j, m2, o2))

    if tt_move is not None:
        ti, tj = tt_move
        for k in range(len(scored)):
            if scored[k][1] == ti and scored[k][2] == tj:
                scored.insert(0, scored.pop(k))
                break

    best = -INF
    best_move = (scored[0][1], scored[0][2])
    first = True
    for (s, i, j, m2, o2) in scored:
        if first:
            v = -_search(o2, m2, depth - 1, -beta, -alpha, ply + 1, deadline)
            first = False
        else:
            v = -_search(o2, m2, depth - 1, -alpha - 1, -alpha, ply + 1, deadline)
            if alpha < v < beta:
                v = -_search(o2, m2, depth - 1, -beta, -alpha, ply + 1, deadline)
        if v > best:
            best = v
            best_move = (i, j)
        if v > alpha:
            alpha = v
            if alpha >= beta:
                break

    if best <= a0:
        flag = 2                     # upper bound
    elif best >= b0:
        flag = 1                     # lower bound
    else:
        flag = 0                     # exact
    sv = best + ply if best > TERM else (best - ply if best < -TERM else best)
    TT[key] = (depth, sv, flag, best_move)
    return best


def _root(me, opp, moves, depth, deadline):
    """One iterative-deepening iteration over the root moves."""
    alpha = -INF
    best_val = -INF
    best_move = None
    results = []
    for (i, j) in moves:
        bj = 1 << j
        m2 = (me ^ (1 << i)) | bj
        o2 = opp ^ bj
        v = -_search(o2, m2, depth - 1, -INF, -alpha, 1, deadline)
        results.append((v, i, j))
        if v > best_val:
            best_val = v
            best_move = (i, j)
        if v > alpha:
            alpha = v
    results.sort(key=lambda x: -x[0])
    return best_val, best_move, [(i, j) for (v, i, j) in results]


def _fmt(i, j):
    r, c = divmod(i, STRIDE)
    d = j - i
    if d == 1:
        ch = 'R'
    elif d == -1:
        ch = 'L'
    elif d == STRIDE:
        ch = 'D'
    else:
        ch = 'U'
    return str(r) + ',' + str(c) + ',' + ch


def policy(you, opponent):
    global _nodes

    me = 0
    opp = 0
    idx = 0
    for r in range(ROWS):
        base = r * STRIDE
        for c in range(COLS):
            if you[idx]:
                me |= 1 << (base + c)
            elif opponent[idx]:
                opp |= 1 << (base + c)
            idx += 1

    moves = _gen(me, opp)
    if not moves:
        # No legal move exists (game over); return a placeholder string.
        return "0,0,U"
    if len(moves) == 1:
        i, j = moves[0]
        return _fmt(i, j)

    if len(TT) > MAX_TT:
        TT.clear()

    deadline = time.perf_counter() + TIME_BUDGET
    _nodes = 0

    # Fallback move: the statically best-ordered legal move (always legal).
    scored = []
    for (i, j) in moves:
        bj = 1 << j
        m2 = (me ^ (1 << i)) | bj
        o2 = opp ^ bj
        scored.append((_mob(o2, m2), i, j))
    scored.sort(key=lambda x: x[0])
    moves = [(i, j) for (_, i, j) in scored]
    best = moves[0]

    try:
        depth = 1
        while depth <= 40:
            val, mv, moves = _root(me, opp, moves, depth, deadline)
            if mv is not None:
                best = mv
            if val > TERM or val < -TERM:   # forced result found
                break
            depth += 1
    except _Timeout:
        pass

    i, j = best
    return _fmt(i, j)
