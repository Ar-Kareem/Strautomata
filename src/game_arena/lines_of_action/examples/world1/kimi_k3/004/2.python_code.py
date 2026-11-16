
import time

ME = 1
OPP = -1
WIN = 1000000
INF = 10 ** 9

# ---------------------------------------------------------------------------
# Precomputed tables (built once at import time)
# ---------------------------------------------------------------------------
_DIRS8 = ((-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1))
# direction indices per axis: horizontal, vertical, main diagonal, anti diagonal
_AXDIR = ((3, 4), (1, 6), (0, 7), (2, 5))

if hasattr(int, "bit_count"):
    _popcount = int.bit_count
else:  # pragma: no cover
    def _popcount(x):
        return bin(x).count("1")


def _build():
    bit = [1 << s for s in range(64)]
    row = [s >> 3 for s in range(64)]
    col = [s & 7 for s in range(64)]

    nei = [0] * 64
    for s in range(64):
        r, c = row[s], col[s]
        m = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    m |= bit[nr * 8 + nc]
        nei[s] = m

    # full line masks per square per axis (includes the square itself)
    lmask = [[0, 0, 0, 0] for _ in range(64)]
    for s in range(64):
        r, c = row[s], col[s]
        m0 = m1 = m2 = m3 = 0
        for t in range(64):
            tr, tc = row[t], col[t]
            if tr == r:
                m0 |= bit[t]
            if tc == c:
                m1 |= bit[t]
            if tr - tc == r - c:
                m2 |= bit[t]
            if tr + tc == r + c:
                m3 |= bit[t]
        lmask[s] = (m0, m1, m2, m3)

    # per square/direction: list over step k of (target_bit, between_mask)
    raygen = []
    for s in range(64):
        r, c = row[s], col[s]
        per_dir = []
        for dr, dc in _DIRS8:
            entries = []
            between = 0
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                q = nr * 8 + nc
                entries.append((bit[q], between))
                between |= bit[q]
                nr += dr
                nc += dc
            per_dir.append(tuple(entries))
        raygen.append(tuple(per_dir))

    ctr = []
    for s in range(64):
        r, c = row[s], col[s]
        ctr.append(7.0 - (abs(r - 3.5) + abs(c - 3.5)))

    return bit, row, col, nei, lmask, raygen, tuple(ctr)


BIT, ROW, COL, NEI_MASK, LMASK, RAYGEN, CTR = _build()


class _Timeout(Exception):
    pass


# ---------------------------------------------------------------------------
# Core move generation (fully legal according to LOA rules)
# ---------------------------------------------------------------------------
def _gen_moves(mover, other):
    occ = mover | other
    res = []
    lm_all = LMASK
    rg_all = RAYGEN
    ad = _AXDIR
    pc = _popcount
    m = mover
    while m:
        sb = m & -m
        m ^= sb
        s = sb.bit_length() - 1
        lm = lm_all[s]
        rg = rg_all[s]
        for ax in range(4):
            cnt = pc(occ & lm[ax])
            d1, d2 = ad[ax]
            e = rg[d1]
            if cnt <= len(e):
                tb, bw = e[cnt - 1]
                if (bw & other) == 0 and (tb & mover) == 0:
                    res.append((sb, tb))
            e = rg[d2]
            if cnt <= len(e):
                tb, bw = e[cnt - 1]
                if (bw & other) == 0 and (tb & mover) == 0:
                    res.append((sb, tb))
    return res


# ---------------------------------------------------------------------------
# Connectivity helpers
# ---------------------------------------------------------------------------
def _connected(bits):
    """True iff nonzero bitboard forms a single 8-connected group."""
    lsb = bits & -bits
    frontier = lsb
    rest = bits ^ lsb
    nm = NEI_MASK
    while frontier:
        nb = 0
        f = frontier
        while f:
            b0 = f & -f
            nb |= nm[b0.bit_length() - 1]
            f ^= b0
        nb &= rest
        if not nb:
            break
        rest &= ~nb
        frontier = nb
    return rest == 0


def _comp_stats(bits):
    """(number of connected components, largest component size)."""
    comps = 0
    largest = 0
    rest = bits
    nm = NEI_MASK
    pc = _popcount
    while rest:
        lsb = rest & -rest
        rest ^= lsb
        comps += 1
        size = 1
        frontier = lsb
        while frontier:
            nb = 0
            f = frontier
            while f:
                b0 = f & -f
                nb |= nm[b0.bit_length() - 1]
                f ^= b0
            nb &= rest
            if not nb:
                break
            size += pc(nb)
            rest &= ~nb
            frontier = nb
        if size > largest:
            largest = size
    return comps, largest


# ---------------------------------------------------------------------------
# Evaluation (always from the perspective of player ME)
# ---------------------------------------------------------------------------
def _evaluate(me_b, op_b):
    pc = _popcount
    my_n = pc(me_b)
    op_n = pc(op_b)
    if my_n == 0:
        return -WIN + 200
    if op_n == 0:
        return WIN - 200
    my_c, my_l = _comp_stats(me_b)
    op_c, op_l = _comp_stats(op_b)
    if my_c == 1:
        return WIN - 100
    if op_c == 1:
        return -WIN + 100

    rw = ROW
    cl = COL
    ct = CTR
    mrs = mcs = ors = ocs = 0
    mctr = 0.0
    octr = 0.0
    m = me_b
    while m:
        b0 = m & -m
        m ^= b0
        s = b0.bit_length() - 1
        mrs += rw[s]
        mcs += cl[s]
        mctr += ct[s]
    m = op_b
    while m:
        b0 = m & -m
        m ^= b0
        s = b0.bit_length() - 1
        ors += rw[s]
        ocs += cl[s]
        octr += ct[s]
    mcr = mrs / my_n
    mcc = mcs / my_n
    ocr = ors / op_n
    occ = ocs / op_n
    mconc = 0.0
    oconc = 0.0
    m = me_b
    while m:
        b0 = m & -m
        m ^= b0
        s = b0.bit_length() - 1
        dr = rw[s] - mcr
        dc = cl[s] - mcc
        mconc += dr * dr + dc * dc
    m = op_b
    while m:
        b0 = m & -m
        m ^= b0
        s = b0.bit_length() - 1
        dr = rw[s] - ocr
        dc = cl[s] - occ
        oconc += dr * dr + dc * dc
    mconc /= my_n
    oconc /= op_n

    return (700.0 * (op_c - my_c)
            + 80.0 * (my_l - op_l)
            + 20.0 * (oconc - mconc)
            + 4.0 * (mctr - octr)
            + 3.0 * (my_n - op_n))


# ---------------------------------------------------------------------------
# Move ordering
# ---------------------------------------------------------------------------
def _order_moves(mover, other, moves, ttmove):
    scored = []
    nm = NEI_MASK
    pc = _popcount
    ct = CTR
    for m in moves:
        sb, tb = m
        sc = 0.0
        if m == ttmove:
            sc += 100000.0
        if tb & other:
            sc += 500.0
        t = tb.bit_length() - 1
        sc += 60.0 * pc(nm[t] & mover)
        sc += ct[t]
        scored.append((sc, m))
    scored.sort(key=lambda x: -x[0])
    return [m for _, m in scored]


# ---------------------------------------------------------------------------
# Alpha-beta search with transposition table
# ---------------------------------------------------------------------------
TT = {}
NODES = 0
DEADLINE = 0.0


def _search(me_b, op_b, depth, alpha, beta, turn):
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.time() > DEADLINE:
        raise _Timeout()

    key = (me_b, op_b, turn)
    ent = TT.get(key)
    if ent is not None and ent[0] >= depth:
        val = ent[1]
        flag = ent[2]
        if flag == 0:
            return val
        if flag == 1:
            if val > alpha:
                alpha = val
        else:
            if val < beta:
                beta = val
        if alpha >= beta:
            return val

    if depth <= 0:
        return _evaluate(me_b, op_b)

    ttmove = ent[3] if ent is not None else None
    a0 = alpha
    b0 = beta
    nm = NEI_MASK

    if turn == ME:
        moves = _gen_moves(me_b, op_b)
        if not moves:
            return -WIN - 50
        moves = _order_moves(me_b, op_b, moves, ttmove)
        value = -INF
        best = moves[0]
        for m in moves:
            sb, tb = m
            nme = (me_b ^ sb) | tb
            nop = op_b & ~tb
            sc = None
            t = tb.bit_length() - 1
            if (nm[t] & nme) or (nme & (nme - 1)) == 0:
                if _connected(nme):
                    sc = WIN + depth
            if sc is None and (tb & op_b):
                if nop == 0:
                    sc = WIN + depth
                elif (nop & (nop - 1)) == 0:
                    sc = -WIN - depth
            if sc is None:
                sc = _search(nme, nop, depth - 1, alpha, beta, OPP)
            if sc > value:
                value = sc
                best = m
            if sc > alpha:
                alpha = sc
            if alpha >= beta:
                break
    else:
        moves = _gen_moves(op_b, me_b)
        if not moves:
            return WIN + 50
        moves = _order_moves(op_b, me_b, moves, ttmove)
        value = INF
        best = moves[0]
        for m in moves:
            sb, tb = m
            nop = (op_b ^ sb) | tb
            nme = me_b & ~tb
            sc = None
            t = tb.bit_length() - 1
            if (nm[t] & nop) or (nop & (nop - 1)) == 0:
                if _connected(nop):
                    sc = -WIN - depth
            if sc is None and (tb & me_b):
                if nme == 0:
                    sc = -WIN - depth
                elif (nme & (nme - 1)) == 0:
                    sc = WIN + depth
            if sc is None:
                sc = _search(nme, nop, depth - 1, alpha, beta, ME)
            if sc < value:
                value = sc
                best = m
            if sc < beta:
                beta = sc
            if alpha >= beta:
                break

    if value <= a0:
        flag = 2
    elif value >= b0:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, value, flag, best)
    return value


def _root(me_b, op_b, moves, depth, prev):
    alpha = -INF
    best = None
    bestsc = -INF
    nm = NEI_MASK
    for m in _order_moves(me_b, op_b, moves, prev):
        sb, tb = m
        nme = (me_b ^ sb) | tb
        nop = op_b & ~tb
        sc = None
        t = tb.bit_length() - 1
        if (nm[t] & nme) or (nme & (nme - 1)) == 0:
            if _connected(nme):
                sc = WIN + depth
        if sc is None and (tb & op_b):
            if nop == 0:
                sc = WIN + depth
            elif (nop & (nop - 1)) == 0:
                sc = -WIN - depth
        if sc is None:
            sc = _search(nme, nop, depth - 1, alpha, INF, OPP)
        if sc > bestsc:
            bestsc = sc
            best = m
        if sc > alpha:
            alpha = sc
    return bestsc, best


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def _fmt(move):
    sb, tb = move
    s = sb.bit_length() - 1
    t = tb.bit_length() - 1
    return "%d,%d:%d,%d" % (s >> 3, s & 7, t >> 3, t & 7)


def _to_bits(board):
    me_b = 0
    op_b = 0
    i = 0
    for row in board:
        for v in row:
            if v == 1:
                me_b |= BIT[i]
            elif v == -1:
                op_b |= BIT[i]
            i += 1
    return me_b, op_b


def _policy_impl(board):
    global TT, NODES, DEADLINE
    me_b, op_b = _to_bits(board)
    moves = _gen_moves(me_b, op_b)
    if not moves:
        # No legal move: the game should already be over. Return a dummy.
        return "0,0:0,0"
    if len(moves) == 1:
        return _fmt(moves[0])

    TT = {}
    NODES = 0
    DEADLINE = time.time() + 0.9

    best = _order_moves(me_b, op_b, moves, None)[0]
    prev = None
    try:
        depth = 1
        while depth <= 40:
            sc, bm = _root(me_b, op_b, moves, depth, prev)
            if bm is not None:
                best = bm
                prev = bm
            if sc >= WIN:
                break
            depth += 1
    except _Timeout:
        pass
    return _fmt(best)


def policy(board) -> str:
    try:
        return _policy_impl(board)
    except Exception:
        # Absolute fallback: return any legal move.
        try:
            me_b, op_b = _to_bits(board)
            moves = _gen_moves(me_b, op_b)
            if moves:
                return _fmt(moves[0])
        except Exception:
            pass
        return "0,0:0,0"
