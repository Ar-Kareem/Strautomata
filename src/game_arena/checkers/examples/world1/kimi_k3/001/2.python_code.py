
import time

# Piece encoding: 0 empty, 1 black man, 2 black king, 3 white man, 4 white king
BM, BK, WM, WK = 1, 2, 3, 4
INF = 10 ** 9
MATE = 10 ** 7

DIRS = ((-1, -1), (-1, 1), (1, -1), (1, 1))  # 0,1 = "down" (black), 2,3 = "up" (white)

# Precomputed neighbor/jump tables
MID = [[-1] * 4 for _ in range(64)]
LAND = [[-1] * 4 for _ in range(64)]
for _i in range(64):
    _r, _c = divmod(_i, 8)
    for _d in range(4):
        _dr, _dc = DIRS[_d]
        _mr, _mc = _r + _dr, _c + _dc
        if 0 <= _mr < 8 and 0 <= _mc < 8:
            MID[_i][_d] = _mr * 8 + _mc
            _lr, _lc = _r + 2 * _dr, _c + 2 * _dc
            if 0 <= _lr < 8 and 0 <= _lc < 8:
                LAND[_i][_d] = _lr * 8 + _lc

# Precomputed piece-square tables
PST = [[0] * 64 for _ in range(5)]
for _i in range(64):
    _r, _c = _i >> 3, _i & 7
    _center = (3 <= _r <= 4) and (2 <= _c <= 5)
    _v = 100 + 6 * (7 - _r) + (4 if _center else 0)
    if _r == 7:
        _v += 6
    elif _c == 0 or _c == 7:
        _v -= 2
    PST[BM][_i] = _v
    _v = 100 + 6 * _r + (4 if _center else 0)
    if _r == 0:
        _v += 6
    elif _c == 0 or _c == 7:
        _v -= 2
    PST[WM][_i] = _v
    PST[BK][_i] = 330 + (6 if _center else 0)
    PST[WK][_i] = 330 + (6 if _center else 0)

TT = {}
deadline = 0.0
nodes = 0


class _Timeout(Exception):
    pass


def _chains(b, i, black, king, dirs, promo):
    """All maximal capture chains for the piece at square i. Mutates/restores b."""
    out = []
    v = b[i]
    for d in dirs:
        m = MID[i][d]
        if m < 0:
            continue
        mv = b[m]
        if mv == 0:
            continue
        if black:
            if mv < 3:
                continue
        else:
            if mv >= 3:
                continue
        l = LAND[i][d]
        if l < 0 or b[l] != 0:
            continue
        if not king and (l >> 3) == promo:  # crowned: chain stops
            out.append(((m, l),))
            continue
        b[i] = 0
        b[m] = 0
        b[l] = v
        sub = _chains(b, l, black, king, dirs, promo)
        b[i] = v
        b[m] = mv
        b[l] = 0
        if sub:
            for s in sub:
                out.append(((m, l),) + s)
        else:
            out.append(((m, l),))
    return out


def _gen(b, black):
    """Returns (moves, is_capture). Captures are mandatory when available."""
    if black:
        man, king, mdirs, promo = BM, BK, (0, 1), 0
    else:
        man, king, mdirs, promo = WM, WK, (2, 3), 7
    caps = []
    for i in range(64):
        v = b[i]
        if v == man:
            for ch in _chains(b, i, black, False, mdirs, promo):
                caps.append((i, ch))
        elif v == king:
            for ch in _chains(b, i, black, True, (0, 1, 2, 3), -1):
                caps.append((i, ch))
    if caps:
        return caps, True
    simps = []
    for i in range(64):
        v = b[i]
        if v == man:
            for d in mdirs:
                m = MID[i][d]
                if m >= 0 and b[m] == 0:
                    simps.append((i, m))
        elif v == king:
            for d in (0, 1, 2, 3):
                m = MID[i][d]
                if m >= 0 and b[m] == 0:
                    simps.append((i, m))
    return simps, False


def _apply(b, move, is_cap):
    nb = b[:]
    if is_cap:
        i, ch = move
        v = nb[i]
        nb[i] = 0
        for (m, l) in ch:
            nb[m] = 0
        last = ch[-1][1]
        if v == BM and last < 8:
            v = BK
        elif v == WM and last >= 56:
            v = WK
        nb[last] = v
    else:
        i, j = move
        v = nb[i]
        nb[i] = 0
        if v == BM and j < 8:
            v = BK
        elif v == WM and j >= 56:
            v = WK
        nb[j] = v
    return nb


def _eval(b):
    """Static evaluation, positive favors black."""
    bs = 0
    ws = 0
    for i in range(64):
        v = b[i]
        if v == 0:
            continue
        if v <= 2:
            bs += PST[v][i]
        else:
            ws += PST[v][i]
    return bs - ws


def _order(b, moves, is_cap, black):
    if is_cap:
        def kf(mv):
            cv = 0
            for (m, l) in mv[1]:
                cv += 3 if (b[m] & 1) == 0 else 1  # kings are even-valued pieces
            return (len(mv[1]), cv)
    else:
        promo = 0 if black else 7

        def kf(mv):
            i, j = mv
            v = b[i]
            r = j >> 3
            c = j & 7
            s = 0
            if (v & 1) == 1:  # man
                if r == promo:
                    s += 60
                s += (7 - r) if black else r
            if 3 <= r <= 4 and 2 <= c <= 5:
                s += 8
            return s
    return sorted(moves, key=kf, reverse=True)


def _search(b, black, depth, alpha, beta, ply):
    global nodes
    nodes += 1
    if (nodes & 1023) == 0 and time.perf_counter() >= deadline:
        raise _Timeout()
    key = (bytes(b), black)
    ent = TT.get(key)
    if ent is not None and ent[0] >= depth:
        ed, ev, ef = ent
        if ef == 0:
            return ev
        if ef == 1 and ev <= alpha:
            return ev
        if ef == 2 and ev >= beta:
            return ev
    moves, is_cap = _gen(b, black)
    if not moves:
        return -MATE + ply  # no legal moves: side to move loses
    if depth <= 0:
        if not is_cap:
            v = _eval(b)
            return v if black else -v
        depth = 1  # capture quiescence: don't evaluate mid-tactics
    moves = _order(b, moves, is_cap, black)
    best = -INF
    a0 = alpha
    for mv in moves:
        val = -_search(_apply(b, mv, is_cap), not black, depth - 1, -beta, -alpha, ply + 1)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
            if alpha >= beta:
                break
    if best <= a0:
        f = 1  # upper bound
    elif best >= beta:
        f = 2  # lower bound
    else:
        f = 0  # exact
    TT[key] = (depth, best, f)
    return best


def _root(b, black, moves, is_cap, depth, prev):
    ordered = _order(b, moves, is_cap, black)
    if prev is not None:
        for k in range(len(ordered)):
            if ordered[k] == prev:
                ordered.insert(0, ordered.pop(k))
                break
    best_val = -INF
    best_mv = ordered[0]
    alpha = -INF
    for mv in ordered:
        val = -_search(_apply(b, mv, is_cap), not black, depth - 1, -INF, -alpha, 1)
        if val > best_val:
            best_val = val
            best_mv = mv
        if val > alpha:
            alpha = val
    return best_val, best_mv


def policy(my_men, my_kings, opp_men, opp_kings, color):
    global deadline, nodes, TT
    board = [0] * 64
    try:
        black = (str(color).lower()[0] == 'b')
        if black:
            mm, mk, om, ok = BM, BK, WM, WK
        else:
            mm, mk, om, ok = WM, WK, BM, BK
        for sq in my_men:
            r, c = int(sq[0]), int(sq[1])
            board[r * 8 + c] = mm
        for sq in my_kings:
            r, c = int(sq[0]), int(sq[1])
            board[r * 8 + c] = mk
        for sq in opp_men:
            r, c = int(sq[0]), int(sq[1])
            board[r * 8 + c] = om
        for sq in opp_kings:
            r, c = int(sq[0]), int(sq[1])
            board[r * 8 + c] = ok
    except Exception:
        black = (color == 'b')

    moves, is_cap = _gen(board, black)

    def ret(mv):
        # Return the first step of the move (first jump of a capture chain).
        if is_cap:
            i = mv[0]
            j = mv[1][0][1]
        else:
            i, j = mv
        return ((i >> 3, i & 7), (j >> 3, j & 7))

    if not moves:
        return ((0, 1), (1, 0))  # no legal moves; game is already lost

    best_mv = moves[0]
    if len(moves) == 1:
        return ret(best_mv)

    start = time.perf_counter()
    deadline = start + 0.82
    nodes = 0
    if len(TT) > 200000:
        TT.clear()

    prev = None
    last_t = 0.0
    try:
        for depth in range(1, 60):
            t0 = time.perf_counter()
            val, bm = _root(board, black, moves, is_cap, depth, prev)
            last_t = time.perf_counter() - t0
            best_mv = bm
            prev = bm
            if val > MATE - 1000:
                break  # forced win found
            if time.perf_counter() - start + 4 * last_t > 0.82:
                break  # next iteration likely won't finish
    except _Timeout:
        pass
    except Exception:
        pass
    return ret(best_mv)
