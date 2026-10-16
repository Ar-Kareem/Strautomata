
import time
import random

INF = 10 ** 9
WIN = 10 ** 6

# ---------------- Evaluation constants ----------------
PIECE = 100
ADV = [0, 5, 12, 24, 42, 70, 110, 0]          # value by distance advanced
PASSED = [0, 25, 60, 130, 260, 520, 1000, 0]  # passed-pawn bonus by advancement
HANG = 45       # attacked and undefended
ATT_DEF = 12    # attacked but defended
DEFB = 6        # defended and not attacked

# ---------------- Precomputed masks ----------------
DIAG_UP = [0] * 64    # squares (r+1, c+-1)
DIAG_DOWN = [0] * 64  # squares (r-1, c+-1)
SPAN_W = [0] * 64     # rows ahead of a white piece, cols c-1..c+1
SPAN_B = [0] * 64     # rows ahead of a black piece, cols c-1..c+1

for _i in range(64):
    _r, _c = divmod(_i, 8)
    _m = 0
    if _r < 7:
        if _c > 0:
            _m |= 1 << ((_r + 1) * 8 + _c - 1)
        if _c < 7:
            _m |= 1 << ((_r + 1) * 8 + _c + 1)
    DIAG_UP[_i] = _m
    _m = 0
    if _r > 0:
        if _c > 0:
            _m |= 1 << ((_r - 1) * 8 + _c - 1)
        if _c < 7:
            _m |= 1 << ((_r - 1) * 8 + _c + 1)
    DIAG_DOWN[_i] = _m
    _m = 0
    for _rr in range(_r + 1, 8):
        for _cc in (_c - 1, _c, _c + 1):
            if 0 <= _cc < 8:
                _m |= 1 << (_rr * 8 + _cc)
    SPAN_W[_i] = _m
    _m = 0
    for _rr in range(0, _r):
        for _cc in (_c - 1, _c, _c + 1):
            if 0 <= _cc < 8:
                _m |= 1 << (_rr * 8 + _cc)
    SPAN_B[_i] = _m

# ---------------- Zobrist hashing ----------------
_rng = random.Random(0xC0FFEE)
Z = [[0, 0, 0] for _ in range(64)]  # index piece+1: black(-1)->0, white(1)->2
for _i in range(64):
    Z[_i][0] = _rng.getrandbits(64)
    Z[_i][2] = _rng.getrandbits(64)
ZSIDE = _rng.getrandbits(64)

TT = {}    # transposition table (persists across turns)
HIST = {}  # history heuristic


def _gen(board, side, bits):
    """All legal moves for `side`. side=1 white (up), side=-1 black (down)."""
    moves = []
    step = 8 * side
    m = bits
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb
        c = i & 7
        t = i + step
        if 0 <= t < 64:
            if board[t] == 0:
                moves.append((i, t))
            if c > 0:
                u = t - 1
                if board[u] != side:  # empty or enemy
                    moves.append((i, u))
            if c < 7:
                u = t + 1
                if board[u] != side:
                    moves.append((i, u))
    return moves


def _gen_tactical(board, side, bits):
    """Captures, promotions, and moves onto the penultimate rank (threats)."""
    moves = []
    step = 8 * side
    m = bits
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb
        c = i & 7
        t = i + step
        if 0 <= t < 64:
            if side == 1:
                special = i >= 40   # rows 5-6: threat or promotion
            else:
                special = i < 24    # rows 0-2 for black
            if special:
                if board[t] == 0:
                    moves.append((i, t))
                if c > 0 and board[t - 1] != side:
                    moves.append((i, t - 1))
                if c < 7 and board[t + 1] != side:
                    moves.append((i, t + 1))
            else:
                if c > 0 and board[t - 1] == -side:
                    moves.append((i, t - 1))
                if c < 7 and board[t + 1] == -side:
                    moves.append((i, t + 1))
    return moves


def _evaluate(board, wb, bb):
    """Score from White's perspective."""
    score = 0
    m = wb
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb
        r = i >> 3
        score += PIECE + ADV[r]
        if not (bb & SPAN_W[i]):
            score += PASSED[r]
        if bb & DIAG_UP[i]:                      # attacked by black
            score -= ATT_DEF if (wb & DIAG_DOWN[i]) else HANG
        elif wb & DIAG_DOWN[i]:                  # defended
            score += DEFB
    m = bb
    while m:
        lsb = m & -m
        i = lsb.bit_length() - 1
        m ^= lsb
        r = i >> 3
        p = 7 - r
        score -= PIECE + ADV[p]
        if not (wb & SPAN_B[i]):
            score -= PASSED[p]
        if wb & DIAG_DOWN[i]:                    # attacked by white
            score += ATT_DEF if (bb & DIAG_UP[i]) else HANG
        elif bb & DIAG_UP[i]:
            score -= DEFB
    return score


def _order(moves, board, side, ttm):
    tf = ttm[0] if ttm else -1
    tt = ttm[1] if ttm else -1
    scored = []
    for (f, t) in moves:
        s = ADV[(t >> 3) if side == 1 else 7 - (t >> 3)] * 10
        s += HIST.get((side, f, t), 0)
        if board[t] != 0:
            s += 2_000_000                        # capture
        if (side == 1 and t >= 56) or (side == -1 and t < 8):
            s += 50_000_000                       # promotion
        if f == tf and t == tt:
            s += 30_000_000                       # TT move
        scored.append((s, f, t))
    scored.sort(reverse=True)
    return [(f, t) for (s, f, t) in scored]


def _qs(board, wb, bb, side, alpha, beta, ply, dl, st, qd):
    st[0] += 1
    if (st[0] & 1023) == 0 and time.time() >= dl:
        raise TimeoutError
    stand = _evaluate(board, wb, bb) * side
    if stand >= beta:
        return stand
    if stand > alpha:
        alpha = stand
    if qd <= 0:
        return stand
    bits = wb if side == 1 else bb
    if bits == 0:
        return -WIN + ply
    for (f, t) in _gen_tactical(board, side, bits):
        cap = board[t]
        board[f] = 0
        board[t] = side
        bf = 1 << f
        bt = 1 << t
        if side == 1:
            nwb = (wb ^ bf) | bt
            nbb = (bb ^ bt) if cap else bb
            won = t >= 56 or nbb == 0
        else:
            nbb = (bb ^ bf) | bt
            nwb = (wb ^ bt) if cap else wb
            won = t < 8 or nwb == 0
        if won:
            sc = WIN - ply
        else:
            sc = -_qs(board, nwb, nbb, -side, -beta, -alpha, ply + 1, dl, st, qd - 1)
        board[f] = side
        board[t] = cap
        if sc > alpha:
            alpha = sc
        if alpha >= beta:
            break
    return alpha


def _search(board, wb, bb, h, side, depth, alpha, beta, ply, dl, st):
    st[0] += 1
    if (st[0] & 1023) == 0 and time.time() >= dl:
        raise TimeoutError
    key = (h ^ ZSIDE) if side == -1 else h
    e = TT.get(key)
    ttm = None
    if e is not None:
        ed, ev, ef, em = e
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
        ttm = em
    if depth <= 0:
        return _qs(board, wb, bb, side, alpha, beta, ply, dl, st, 6)
    bits = wb if side == 1 else bb
    moves = _gen(board, side, bits)
    if not moves:
        return -WIN + ply   # no pieces or no moves => loss
    moves = _order(moves, board, side, ttm)
    a0 = alpha
    best = -INF
    bm = None
    for (f, t) in moves:
        cap = board[t]
        board[f] = 0
        board[t] = side
        bf = 1 << f
        bt = 1 << t
        h2 = h ^ Z[f][side + 1] ^ Z[t][side + 1]
        if side == 1:
            nwb = (wb ^ bf) | bt
            nbb = bb
            if cap:
                nbb = bb ^ bt
                h2 ^= Z[t][cap + 1]
            won = t >= 56 or nbb == 0
        else:
            nbb = (bb ^ bf) | bt
            nwb = wb
            if cap:
                nwb = wb ^ bt
                h2 ^= Z[t][cap + 1]
            won = t < 8 or nwb == 0
        if won:
            sc = WIN - ply
        else:
            sc = -_search(board, nwb, nbb, h2, -side, depth - 1, -beta, -alpha, ply + 1, dl, st)
        board[f] = side
        board[t] = cap
        if sc > best:
            best = sc
            bm = (f, t)
        if sc > alpha:
            alpha = sc
        if alpha >= beta:
            HIST[(side, f, t)] = HIST.get((side, f, t), 0) + depth * depth
            break
    if best <= a0:
        fl = 2          # upper bound
    elif best >= beta:
        fl = 1          # lower bound
    else:
        fl = 0          # exact
    TT[key] = (depth, best, fl, bm)
    return best


def policy(me, opp, color):
    global TT, HIST
    board = [0] * 64
    if color == 'w':
        side = 1
        for p in me:
            board[p[0] * 8 + p[1]] = 1
        for p in opp:
            board[p[0] * 8 + p[1]] = -1
    else:
        side = -1
        for p in me:
            board[p[0] * 8 + p[1]] = -1
        for p in opp:
            board[p[0] * 8 + p[1]] = 1

    wb = 0
    bb = 0
    h = 0
    for i in range(64):
        v = board[i]
        if v == 1:
            wb |= 1 << i
            h ^= Z[i][2]
        elif v == -1:
            bb |= 1 << i
            h ^= Z[i][0]

    bits = wb if side == 1 else bb
    moves = _gen(board, side, bits)
    if not moves:
        # Should not happen; return a harmless dummy to avoid disqualification.
        if me:
            p = me[0]
            return ((p[0], p[1]), (p[0], p[1]))
        return ((0, 0), (0, 0))

    # Immediate winning move short-circuit.
    obits = bb if side == 1 else wb
    for (f, t) in moves:
        if (side == 1 and t >= 56) or (side == -1 and t < 8):
            return ((f >> 3, f & 7), (t >> 3, t & 7))
        if board[t] == -side and obits == (1 << t):
            return ((f >> 3, f & 7), (t >> 3, t & 7))

    if len(moves) == 1:
        f, t = moves[0]
        return ((f >> 3, f & 7), (t >> 3, t & 7))

    if len(TT) > 1_500_000:
        TT.clear()
    if len(HIST) > 400_000:
        HIST.clear()

    dl = time.time() + 0.92
    st = [0]
    best_move = _order(moves, board, side, None)[0]
    try:
        depth = 1
        while depth <= 64:
            if time.time() >= dl:
                break
            alpha = -INF
            cur = -INF
            curm = None
            for (f, t) in _order(moves, board, side, best_move):
                cap = board[t]
                board[f] = 0
                board[t] = side
                bf = 1 << f
                bt = 1 << t
                h2 = h ^ Z[f][side + 1] ^ Z[t][side + 1]
                if side == 1:
                    nwb = (wb ^ bf) | bt
                    nbb = bb
                    if cap:
                        nbb = bb ^ bt
                        h2 ^= Z[t][cap + 1]
                else:
                    nbb = (bb ^ bf) | bt
                    nwb = wb
                    if cap:
                        nwb = wb ^ bt
                        h2 ^= Z[t][cap + 1]
                sc = -_search(board, nwb, nbb, h2, -side, depth - 1, -INF, -alpha, 1, dl, st)
                board[f] = side
                board[t] = cap
                if sc > cur:
                    cur = sc
                    curm = (f, t)
                if sc > alpha:
                    alpha = sc
            if curm is not None:
                best_move = curm
            if cur >= WIN - 1000 or cur <= -WIN + 1000:
                break   # forced win found (or all is lost); no point searching deeper
            depth += 1
    except TimeoutError:
        pass

    f, t = best_move
    return ((f >> 3, f & 7), (t >> 3, t & 7))
