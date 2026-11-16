
import time

R, C, N = 5, 6, 30
FULL = (1 << N) - 1

LEFT_COL = 0
RIGHT_COL = 0
for r in range(R):
    LEFT_COL |= 1 << (r * C)
    RIGHT_COL |= 1 << (r * C + C - 1)
NOT_LEFT = FULL ^ LEFT_COL
NOT_RIGHT = FULL ^ RIGHT_COL

ADJ = []
for r in range(R):
    for c in range(C):
        i = r * C + c
        m = 0
        if r > 0:
            m |= 1 << (i - C)
        if c + 1 < C:
            m |= 1 << (i + 1)
        if r + 1 < R:
            m |= 1 << (i + C)
        if c > 0:
            m |= 1 << (i - 1)
        ADJ.append(m)

DIR_CHAR = {-C: "U", 1: "R", C: "D", -1: "L"}
WIN = 10_000_000
INF = 10**15

TT = {}
HIST = {}
_DEADLINE = 0.0
_NODES = 0


class _Timeout(Exception):
    pass


def _bits(board) -> int:
    b = 0
    if len(board) == R:
        try:
            if len(board[0]) == C:
                for r in range(R):
                    row = board[r]
                    base = r * C
                    for c in range(C):
                        if row[c]:
                            b |= 1 << (base + c)
                return b
        except Exception:
            pass
    for i in range(N):
        if board[i]:
            b |= 1 << i
    return b


def _nmask(x: int) -> int:
    return ((((x & NOT_RIGHT) << 1) |
             ((x & NOT_LEFT) >> 1) |
             ((x << C) & FULL) |
             (x >> C)) & FULL)


def _move_count(me: int, opp: int) -> int:
    # Every bichromatic edge is one legal move for the side to move.
    return ((((me & NOT_RIGHT) << 1) & opp).bit_count() +
            (((me & NOT_LEFT) >> 1) & opp).bit_count() +
            (((me << C) & FULL) & opp).bit_count() +
            ((me >> C) & opp).bit_count())


def _gen_moves(me: int, opp: int):
    tb = ((me & NOT_RIGHT) << 1) & opp
    while tb:
        bit = tb & -tb
        t = bit.bit_length() - 1
        tb ^= bit
        yield t - 1, t

    tb = ((me & NOT_LEFT) >> 1) & opp
    while tb:
        bit = tb & -tb
        t = bit.bit_length() - 1
        tb ^= bit
        yield t + 1, t

    tb = ((me << C) & FULL) & opp
    while tb:
        bit = tb & -tb
        t = bit.bit_length() - 1
        tb ^= bit
        yield t - C, t

    tb = (me >> C) & opp
    while tb:
        bit = tb & -tb
        t = bit.bit_length() - 1
        tb ^= bit
        yield t + C, t


def _make_move(me: int, opp: int, m: int):
    s = m >> 5
    t = m & 31
    bs = 1 << s
    bt = 1 << t
    return (me & ~bs) | bt, opp & ~bt


def _order_moves(me: int, opp: int, e: int, pv: int = -1):
    # For a capture s -> t:
    #   x = opponent neighbors of s (removed when s becomes empty)
    #   a = own neighbors of t before the flip, includes s
    #   c = opponent neighbors of t before the flip; these become new edges
    # Remaining bichromatic edges: e - (x + a - 1) + c.
    out = []
    hist = HIST
    for s, t in _gen_moves(me, opp):
        x = (ADJ[s] & opp).bit_count()
        a = (ADJ[t] & me).bit_count()
        c = (ADJ[t] & opp).bit_count()
        ce = e - x - a + 1 + c
        m = (s << 5) | t
        rank = 0 if ce == 0 else (1 if m == pv else 2)
        key = (rank, ce, c, -(a - 1), -x, -hist.get(m, 0), m)
        out.append((key, m, ce))
    out.sort(key=lambda z: z[0])
    return [(m, ce) for _, m, ce in out]


def _has_mate_in_one(me: int, opp: int, e: int) -> bool:
    # One capture can touch at most 4 + 4 - 1 = 7 grid edges.
    if e > 7:
        return False
    for s, t in _gen_moves(me, opp):
        x = (ADJ[s] & opp).bit_count()
        a = (ADJ[t] & me).bit_count()
        c = (ADJ[t] & opp).bit_count()
        if e - x - a + 1 + c == 0:
            return True
    return False


def _active_mask(me: int, opp: int) -> int:
    # Pieces in sealed monochromatic components are irrelevant forever.
    occ = me | opp
    a = ((_nmask(opp) & me) | (_nmask(me) & opp)) & occ
    while True:
        b = a | (_nmask(a) & occ)
        if b == a:
            return a
        a = b


def _same_pairs(x: int) -> int:
    return ((((x & NOT_RIGHT) << 1) & x).bit_count() +
            (((x << C) & FULL) & x).bit_count())


def _evaluate(me: int, opp: int, e: int) -> int:
    if e == 0:
        return -WIN
    if e <= 7 and _has_mate_in_one(me, opp, e):
        return WIN - 1000

    act = _active_mask(me, opp)
    am = me & act
    ao = opp & act

    piece_diff = am.bit_count() - ao.bit_count()
    same_diff = _same_pairs(am) - _same_pairs(ao)

    # For each frontier edge own->enemy:
    # good: same-color backup behind our endpoint helps us recapture if attacked.
    # bad: same-color backup behind the enemy endpoint gives the enemy a recapture.
    good = 0
    bad = 0
    frontier = am & _nmask(ao)
    while frontier:
        bit = frontier & -frontier
        s = bit.bit_length() - 1
        frontier ^= bit
        support = (ADJ[s] & am).bit_count()
        ts = ADJ[s] & ao
        while ts:
            tb = ts & -ts
            t = tb.bit_length() - 1
            ts ^= tb
            good += support
            bad += (ADJ[t] & ao).bit_count()

    return 28 * piece_diff + 16 * same_diff + 9 * (good - bad)


def _search(me: int, opp: int, depth: int, alpha: int, beta: int):
    global _NODES, TT, HIST

    _NODES += 1
    if (_NODES & 511) == 0 and time.perf_counter() >= _DEADLINE:
        raise _Timeout

    e = _move_count(me, opp)
    if e == 0:
        return -WIN, -1

    key = (me, opp)
    ent = TT.get(key)
    if ent is not None:
        d, v, f, bm = ent
        if d >= depth:
            if f == 0:
                return v, bm
            if f == 1:
                if v > alpha:
                    alpha = v
            else:
                if v < beta:
                    beta = v
            if alpha >= beta:
                return v, bm

    if depth <= 0:
        return _evaluate(me, opp, e), -1

    pv = ent[3] if ent is not None else -1
    moves = _order_moves(me, opp, e, pv)
    if not moves:
        return _evaluate(me, opp, e), -1

    if moves[0][1] == 0:
        TT[key] = (depth, WIN, 0, moves[0][0])
        return WIN, moves[0][0]

    a0 = alpha
    b0 = beta
    best = -INF
    bestm = moves[0][0]

    for m, _ce in moves:
        nme, nopp = _make_move(me, opp, m)
        v = -_search(nopp, nme, depth - 1, -beta, -alpha)
        if v > best:
            best = v
            bestm = m
            if v > alpha:
                alpha = v
            if alpha >= beta:
                HIST[m] = HIST.get(m, 0) + depth * depth
                break

    if len(TT) > 250000:
        TT.clear()

    if best <= a0:
        f = 2  # upper bound
    elif best >= b0:
        f = 1  # lower bound
    else:
        f = 0  # exact for this depth
    TT[key] = (depth, best, f, bestm)
    return best, bestm


def _fmt(m: int) -> str:
    if m < 0:
        return "0,0,R"
    s = m >> 5
    t = m & 31
    return f"{s // C},{s % C},{DIR_CHAR.get(t - s, 'R')}"


def policy(you: list[int], opponent: list[int]) -> str:
    global _DEADLINE, _NODES

    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0

    me = _bits(you)
    opp = _bits(opponent)

    e = _move_count(me, opp)
    moves = _order_moves(me, opp, e, -1) if e else []
    if not moves:
        # The game should be over already; keep a syntactically valid fallback.
        return "0,0,R"

    # Immediate winning capture.
    if moves[0][1] == 0:
        return _fmt(moves[0][0])

    best = moves[0][0]

    # Active pieces cannot increase, so this is a safe exact-search horizon.
    max_depth = _active_mask(me, opp).bit_count()
    if max_depth < 1:
        max_depth = 1
    elif max_depth > N:
        max_depth = N

    try:
        for depth in range(1, max_depth + 1):
            v, m = _search(me, opp, depth, -INF, INF)
            if m >= 0:
                best = m
            if v >= WIN // 2 or v <= -WIN // 2:
                break
            if time.perf_counter() >= _DEADLINE:
                break
    except _Timeout:
        pass

    return _fmt(best)
