
import time

# ================= Precomputation =================
ORDER = (3, 2, 4, 1, 5, 0, 6)
BOT = tuple(1 << (7 * c) for c in range(7))          # bottom cell bit of each column
TOP = tuple(1 << (7 * c + 5) for c in range(7))      # top playable cell of each column
BROW = 0
FULL = 0
for _c in range(7):
    BROW |= 1 << (7 * _c)
    FULL |= 0x3F << (7 * _c)                          # all 42 playable cells


def _build_wt():
    """Cell weights = number of winning lines through each cell, packed as
    per-column 7-bit lookup tables for very fast positional evaluation."""
    cw = [0] * 49

    def add(m):
        mm = m
        while mm:
            b = mm & -mm
            cw[b.bit_length() - 1] += 1
            mm ^= b

    for h in range(6):                # horizontal
        for c in range(4):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + h)
            add(m)
    for c in range(7):                # vertical
        for h in range(3):
            m = 0
            for i in range(4):
                m |= 1 << (c * 7 + h + i)
            add(m)
    for c in range(4):                # diagonal /
        for h in range(3):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + h + i)
            add(m)
    for c in range(4):                # diagonal \
        for h in range(3, 6):
            m = 0
            for i in range(4):
                m |= 1 << ((c + i) * 7 + h - i)
            add(m)
    wt = []
    for c in range(7):
        t = [0] * 128
        base = 7 * c
        for b in range(1, 128):
            lb = b & -b
            t[b] = t[b ^ lb] + cw[base + lb.bit_length() - 1]
        wt.append(t)
    return wt


WT = _build_wt()

WIN = 1 << 20          # score base for a proven win
DBL = WIN >> 2         # near-certain loss (unblockable double threat)
INF = 1 << 30

TT = {}                # transposition table: key -> (depth, value, flag, best_col)
nodes = 0
deadline = 0.0


class _Abort(Exception):
    pass


def winpos(bb):
    """Bitboard of all cells that would complete a 4-in-a-row for `bb`
    (handles gaps, both sides, all 4 directions)."""
    r = (bb << 1) & (bb << 2) & (bb << 3)              # vertical
    p = (bb << 7) & (bb << 14)                         # horizontal
    r |= p & (bb << 21)
    r |= p & (bb >> 7)
    p = (bb >> 7) & (bb >> 14)
    r |= p & (bb >> 21)
    r |= p & (bb << 7)
    p = (bb << 6) & (bb << 12)                         # diagonal (shift 6)
    r |= p & (bb << 18)
    r |= p & (bb >> 6)
    p = (bb >> 6) & (bb >> 12)
    r |= p & (bb >> 18)
    r |= p & (bb << 6)
    p = (bb << 8) & (bb << 16)                         # diagonal (shift 8)
    r |= p & (bb << 24)
    r |= p & (bb >> 8)
    p = (bb >> 8) & (bb >> 16)
    r |= p & (bb >> 24)
    r |= p & (bb << 8)
    return r


def evaluate(pos, opp, _WT=WT):
    """Fast positional evaluation from the perspective of `pos`."""
    s = 0
    s += _WT[0][pos & 127] - _WT[0][opp & 127]
    s += _WT[1][(pos >> 7) & 127] - _WT[1][(opp >> 7) & 127]
    s += _WT[2][(pos >> 14) & 127] - _WT[2][(opp >> 14) & 127]
    s += _WT[3][(pos >> 21) & 127] - _WT[3][(opp >> 21) & 127]
    s += _WT[4][(pos >> 28) & 127] - _WT[4][(opp >> 28) & 127]
    s += _WT[5][(pos >> 35) & 127] - _WT[5][(opp >> 35) & 127]
    s += _WT[6][(pos >> 42) & 127] - _WT[6][(opp >> 42) & 127]
    for d in (1, 6, 7, 8):
        a = pos & (pos >> d)
        b = opp & (opp >> d)
        s += 6 * (a.bit_count() - b.bit_count())
        s += 28 * ((a & (pos >> (d * 2))).bit_count()
                   - (b & (opp >> (d * 2))).bit_count())
    return s


def negamax(pos, mask, depth, alpha, beta,
            _winpos=winpos, _eval=evaluate, _TT=TT, _BOT=BOT, _TOP=TOP,
            _ORDER=ORDER, _FULL=FULL, _BROW=BROW, _pc=time.perf_counter):
    """Negamax with alpha-beta + PVS. Score from side-to-move perspective."""
    global nodes
    nodes += 1
    if (nodes & 1023) == 0 and _pc() > deadline:
        raise _Abort()
    if (mask & _FULL) == _FULL:
        return 0                                        # draw
    possible = (mask + _BROW) & _FULL                   # playable cells
    if _winpos(pos) & possible:
        return WIN + depth                              # immediate win available
    if depth == 0:
        opp0 = mask ^ pos
        ot = (_winpos(opp0) & possible).bit_count()     # opponent threats
        if ot >= 2:
            return -DBL                                 # unblockable double threat
        s = _eval(pos, opp0)
        if ot == 1:
            s -= 400                                    # forced to block next
        return s
    opp = mask ^ pos
    owp = _winpos(opp) & _FULL                          # opponent winning cells
    key = (mask << 49) | pos
    ent = _TT.get(key)
    tt_col = -1
    if ent is not None:
        if ent[0] >= depth:
            ev = ent[1]
            ef = ent[2]
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
        tt_col = ent[3]
    alpha0 = alpha
    best = -INF
    best_col = -1
    safe = 0
    if tt_col >= 0:
        cols = (tt_col,) + tuple(c for c in _ORDER if c != tt_col)
    else:
        cols = _ORDER
    first = True
    for col in cols:
        if mask & _TOP[col]:
            continue
        nm = mask + _BOT[col]
        new_mask = mask | nm
        newbit = new_mask ^ mask
        # skip moves that hand the opponent an immediate winning cell
        if owp & ((possible ^ newbit) | (newbit << 1)):
            continue
        safe += 1
        if first:
            sc = -negamax(opp, new_mask, depth - 1, -beta, -alpha)
            first = False
        else:
            sc = -negamax(opp, new_mask, depth - 1, -alpha - 1, -alpha)
            if alpha < sc < beta:
                sc = -negamax(opp, new_mask, depth - 1, -beta, -alpha)
        if sc > best:
            best = sc
            best_col = col
            if sc > alpha:
                alpha = sc
                if alpha >= beta:
                    break
    if safe == 0:
        return -(WIN + depth - 1)                       # every move loses now
    if best_col >= 0 and (ent is None or depth >= ent[0]):
        if best <= alpha0:
            fl = 2                                      # upper bound
        elif best >= beta:
            fl = 1                                      # lower bound
        else:
            fl = 0                                      # exact
        _TT[key] = (depth, best, fl, best_col)
    return best


def policy(board: list[list[int]]) -> int:
    global deadline, nodes
    try:
        pos = 0
        mask = 0
        for r in range(6):
            row = board[r]
            h = 5 - r
            for c in range(7):
                v = row[c]
                if v:
                    b = 1 << (c * 7 + h)
                    mask |= b
                    if v == 1:
                        pos |= b

        legal = [c for c in ORDER if not (mask & TOP[c])]
        if not legal:
            return 3
        best_col = legal[0]

        if mask == 0:
            return 3                                    # opening: center
        if len(legal) == 1:
            return legal[0]

        possible = (mask + BROW) & FULL

        # 1. Immediate win
        wp = winpos(pos) & possible
        if wp:
            for c in ORDER:
                if mask & TOP[c]:
                    continue
                nm = mask + BOT[c]
                if ((mask | nm) ^ mask) & wp:
                    return c

        opp = mask ^ pos

        # 2. Forced block of opponent's immediate win
        owp_p = winpos(opp) & possible
        if owp_p:
            for c in ORDER:
                if mask & TOP[c]:
                    continue
                nm = mask + BOT[c]
                if ((mask | nm) ^ mask) & owp_p:
                    return c

        # 3. Iterative deepening alpha-beta search
        if len(TT) > 800000:
            TT.clear()
        nodes = 0
        deadline = time.perf_counter() + 0.88
        order = legal[:]

        for depth in range(1, 50):
            alpha = -INF
            best_d = -1
            best_s = -INF
            scores = {}
            losing = []
            owp = winpos(opp) & FULL
            try:
                for col in order:
                    nm = mask + BOT[col]
                    new_mask = mask | nm
                    newbit = new_mask ^ mask
                    if owp & ((possible ^ newbit) | (newbit << 1)):
                        scores[col] = -2 * WIN          # loses immediately
                        losing.append(col)
                        continue
                    sc = -negamax(opp, new_mask, depth - 1, -INF, -alpha)
                    scores[col] = sc
                    if sc > best_s:
                        best_s = sc
                        best_d = col
                        if sc > alpha:
                            alpha = sc
                if best_d < 0:                          # everything loses; pick slowest loss
                    for col in losing:
                        new_mask = mask | (mask + BOT[col])
                        sc = -negamax(opp, new_mask, depth - 1, -INF, INF)
                        scores[col] = sc
                        if sc > best_s:
                            best_s = sc
                            best_d = col
            except _Abort:
                break
            if best_d >= 0:
                best_col = best_d
            order = sorted(legal, key=lambda c: -scores.get(c, -INF))
            if best_s >= WIN or best_s <= -WIN:
                break                                   # forced result proven

        return best_col
    except Exception:
        # Emergency fallback: always return a legal move.
        for c in (3, 2, 4, 1, 5, 0, 6):
            if board[0][c] == 0:
                return c
        return 0
