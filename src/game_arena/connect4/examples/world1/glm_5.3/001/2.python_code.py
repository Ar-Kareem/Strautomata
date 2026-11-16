
import time
import sys

sys.setrecursionlimit(20000)

# ---------------- constants ----------------
WIN = 1 << 20
WIN_THRESH = WIN - 64
INF = WIN * 2

BOARD_MASK = 0
BOTTOM = 0
for _c in range(7):
    for _y in range(6):
        BOARD_MASK |= 1 << (_c * 7 + _y)
    BOTTOM |= 1 << (_c * 7)

EVEN_ROWS = 0
for _c in range(7):
    for _y in (0, 2, 4):
        EVEN_ROWS |= 1 << (_c * 7 + _y)
ODD_ROWS = BOARD_MASK ^ EVEN_ROWS

COL3 = 0
for _y in range(6):
    COL3 |= 1 << (21 + _y)
COL24 = 0
for _c in (2, 4):
    for _y in range(6):
        COL24 |= 1 << (_c * 7 + _y)

COL_ORDER = (3, 4, 2, 5, 1, 6, 0)
COL_RANK = [0] * 7
for _i, _c in enumerate(COL_ORDER):
    COL_RANK[_c] = _i

BITCOL = {1 << _i: _i // 7 for _i in range(49)}

if hasattr(int, "bit_count"):
    def bc(x):
        return x.bit_count()
else:
    def bc(x):
        return bin(x).count("1")

TT = {}
HIST = [0] * 7
NODES = 0
DEADLINE_G = 1e18
BASECOUNT_G = 0
TIME_LIMIT = 0.85
TT_CAP = 300000


def win_cells(p):
    """All cells that would complete a 4-in-a-row for bitboard p."""
    r = (p << 1) & (p << 2) & (p << 3)                      # vertical
    q = (p << 7) & (p << 14)                                 # horizontal
    r |= q & (p << 21)
    r |= q & (p >> 7)
    q = (p >> 7) & (p >> 14)
    r |= q & (p << 7)
    r |= q & (p >> 21)
    q = (p << 6) & (p << 12)                                 # diag down-right
    r |= q & (p << 18)
    r |= q & (p >> 6)
    q = (p >> 6) & (p >> 12)
    r |= q & (p << 6)
    r |= q & (p >> 18)
    q = (p << 8) & (p << 16)                                 # diag up-right
    r |= q & (p << 24)
    r |= q & (p >> 8)
    q = (p >> 8) & (p >> 16)
    r |= q & (p << 8)
    r |= q & (p >> 24)
    return r


def negamax(pos, mask, depth, alpha, beta, ply,
            BM=BOARD_MASK, BTM=BOTTOM, WC=win_cells, TTd=TT,
            WI=WIN, WT=WIN_THRESH, NF=INF):
    global NODES
    NODES += 1
    if not (NODES & 31) and time.perf_counter() > DEADLINE_G:
        raise TimeoutError

    possible = (mask + BTM) & BM          # current landing cells
    if not possible:
        return 0                         # board full -> draw

    # transposition table (only for nodes at/above the horizon)
    tte = None
    key = 0
    if depth >= 0:
        key = (mask << 49) | pos
        tte = TTd.get(key)
        if tte is not None:
            td, tf, ts, tmv = tte
            if td >= depth:
                s = ts
                if s >= WT:
                    s -= ply
                elif s <= -WT:
                    s += ply
                if tf == 0:
                    return s
                if tf == 1:
                    if s >= beta:
                        return s
                    if s > alpha:
                        alpha = s
                else:
                    if s <= alpha:
                        return s
                    if s < beta:
                        beta = s
                if alpha >= beta:
                    return s

    empty = BM ^ mask
    myw = WC(pos) & empty
    if myw & possible:                   # immediate win available
        return WI - ply - 1

    oppw = WC(mask ^ pos) & empty
    forced = oppw & possible
    if forced:
        if forced & (forced - 1):         # two immediate threats: lost
            return ply + 2 - WI
        # single forced block, resolved exactly even beyond horizon
        return -negamax(mask ^ pos, mask | forced, depth - 1, -beta, -alpha, ply + 1)

    if depth <= 0:
        # static evaluation (mover's perspective)
        if (BASECOUNT_G + ply) & 1:
            mp = ODD_ROWS
            xp = EVEN_ROWS
        else:
            mp = EVEN_ROWS
            xp = ODD_ROWS
        s = 12 * (bc(myw) - bc(oppw))
        s += 5 * (bc(myw & mp) - bc(oppw & xp))
        s += 40 * (bc(myw & (myw >> 1)) - bc(oppw & (oppw >> 1)))
        o = mask ^ pos
        s += 4 * (bc(pos & COL3) - bc(o & COL3))
        s += 2 * (bc(pos & COL24) - bc(o & COL24))
        return s + 8

    cand = possible & ~(oppw << 1)       # never feed a win right above us
    if not cand:                         # all moves lose immediately
        return ply + 2 - WI

    tt_move = 0
    if tte is not None:
        tt_move = tte[3]
        if not (cand & tt_move):
            tt_move = 0

    moves = []
    m = cand
    while m:
        b = m & -m
        m ^= b
        moves.append(b)
    if len(moves) > 1:
        if tt_move:
            moves.sort(key=lambda b: (b == tt_move, HIST[BITCOL[b]], -COL_RANK[BITCOL[b]]), reverse=True)
        else:
            moves.sort(key=lambda b: (HIST[BITCOL[b]], -COL_RANK[BITCOL[b]]), reverse=True)

    best = -NF
    best_move = 0
    a = alpha
    npos = mask ^ pos
    first = True
    for b in moves:
        nmask = mask | b
        if first:
            first = False
            v = -negamax(npos, nmask, depth - 1, -beta, -a, ply + 1)
        else:
            v = -negamax(npos, nmask, depth - 1, -a - 1, -a, ply + 1)
            if a < v < beta:
                v = -negamax(npos, nmask, depth - 1, -beta, -v, ply + 1)
        if v > best:
            best = v
            best_move = b
        if v > a:
            a = v
            if a >= beta:
                HIST[BITCOL[b]] += depth * depth
                break

    if best >= beta:
        flag = 1
    elif best <= alpha:
        flag = 2
    else:
        flag = 0
    srel = best
    if best >= WT:
        srel = best + ply
    elif best <= -WT:
        srel = best - ply
    if tte is None or tte[0] <= depth:
        TTd[key] = (depth, flag, srel, best_move)
    return best


def _policy(board):
    global DEADLINE_G, NODES, BASECOUNT_G
    t0 = time.perf_counter()
    DEADLINE_G = t0 + TIME_LIMIT
    NODES = 0
    if len(TT) > TT_CAP:
        TT.clear()

    pos = 0
    mask = 0
    for r in range(6):
        row = board[r]
        y = 5 - r
        for c in range(7):
            v = row[c]
            if v:
                b = 1 << (c * 7 + y)
                mask |= b
                if v == 1:
                    pos |= b
    n = bc(mask)
    BASECOUNT_G = n

    if n == 0:
        return 3                          # play center first
    if n == 1:
        return 3                          # best reply to any opening move

    possible = (mask + BOTTOM) & BOARD_MASK
    if not possible:
        return 0

    empty = BOARD_MASK ^ mask
    myw = win_cells(pos) & empty
    w = myw & possible
    if w:                                 # immediate win
        return BITCOL[w & -w]

    oppw = win_cells(mask ^ pos) & empty
    forced = oppw & possible
    if forced:                            # must block
        best_rank = 99
        choice = 0
        m = forced
        while m:
            b = m & -m
            m ^= b
            c = BITCOL[b]
            rk = COL_RANK[c]
            if rk < best_rank:
                best_rank = rk
                choice = c
        return choice

    cand = possible & ~(oppw << 1)
    if not cand:                          # every move loses; delay centrally
        best_rank = 99
        choice = 0
        m = possible
        while m:
            b = m & -m
            m ^= b
            c = BITCOL[b]
            rk = COL_RANK[c]
            if rk < best_rank:
                best_rank = rk
                choice = c
        return choice

    if not (cand & (cand - 1)):           # only one non-losing move
        return BITCOL[cand]

    root_moves = []
    m = cand
    while m:
        b = m & -m
        m ^= b
        root_moves.append(b)
    root_moves.sort(key=lambda b: COL_RANK[BITCOL[b]])

    best_move = root_moves[0]
    npos = mask ^ pos

    try:
        for depth in range(2, 43):
            alpha = -INF
            it_best = 0
            it_best_v = -INF - 1
            scored = []
            first = True
            for b in root_moves:
                nmask = mask | b
                if first:
                    first = False
                    v = -negamax(npos, nmask, depth - 1, -INF, -alpha, 1)
                else:
                    v = -negamax(npos, nmask, depth - 1, -alpha - 1, -alpha, 1)
                    if v > alpha:
                        v = -negamax(npos, nmask, depth - 1, -INF, -v, 1)
                scored.append((v, b))
                if v > it_best_v:
                    it_best_v = v
                    it_best = b
                if v > alpha:
                    alpha = v
            best_move = it_best
            scored.sort(key=lambda t: -t[0])
            root_moves = [bb for (_, bb) in scored]
            if it_best_v >= WIN_THRESH or it_best_v <= -WIN_THRESH:
                break                     # proven win / proven loss: stop
    except TimeoutError:
        pass

    return BITCOL[best_move]


def policy(board):
    try:
        col = _policy(board)
        if isinstance(col, int) and 0 <= col <= 6:
            for r in range(6):
                if board[r][col] == 0:
                    return col
    except Exception:
        pass
    # ultra-safe fallback: most central legal column
    for c in (3, 2, 4, 1, 5, 0, 6):
        for r in range(6):
            try:
                if board[r][c] == 0:
                    return c
            except Exception:
                break
    return 3
