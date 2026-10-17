
import time

# ---------------- bitboard constants ----------------
FULL = (1 << 64) - 1
ROW0 = 0xFF
ROW1 = 0xFF00
ROW7 = 0xFF00000000000000
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = FULL ^ FILE_A
NOT_H = FULL ^ FILE_H

WIN = 1 << 20
MATE = WIN - 1000          # threshold above which values are true forced wins
RUNNER = 1 << 19           # guaranteed-promotion score (below MATE)
INF = 1 << 30

ADV = (0, 5, 12, 22, 36, 55, 80, 0)
PM = tuple(100 + a for a in ADV)                 # value of my piece by row
PO = tuple(100 + ADV[7 - r] for r in range(8))   # value of enemy piece by row
DEF_B = 6
ATT_B = 5
PROMO_THREAT = 2500

MAX_DEPTH = 30
MAX_QDEPTH = 8
TIME_LIMIT = 0.85

# ---------------- runner shadow masks ----------------
# SHADOW_UP[sq]: squares strictly ahead within |dc| <= dr (anything that can
# ever capture or block a straight-running piece on sq must be inside it).
SHADOW_UP = [0] * 64
SHADOW_DN = [0] * 64
for _sq in range(64):
    _r = _sq >> 3
    _c = _sq & 7
    _m = 0
    for _rr in range(_r + 1, 8):
        _dr = _rr - _r
        _lo = _c - _dr
        if _lo < 0: _lo = 0
        _hi = _c + _dr
        if _hi > 7: _hi = 7
        for _cc in range(_lo, _hi + 1):
            _m |= 1 << (_rr * 8 + _cc)
    SHADOW_UP[_sq] = _m
    _m = 0
    for _rr in range(_r - 1, -1, -1):
        _dr = _r - _rr
        _lo = _c - _dr
        if _lo < 0: _lo = 0
        _hi = _c + _dr
        if _hi > 7: _hi = 7
        for _cc in range(_lo, _hi + 1):
            _m |= 1 << (_rr * 8 + _cc)
    SHADOW_DN[_sq] = _m


def vflip(bb):
    """Vertical mirror (rank reversal), standard bit-trick."""
    bb = ((bb >> 8) & 0x00FF00FF00FF00FF) | ((bb & 0x00FF00FF00FF00FF) << 8)
    bb = ((bb >> 16) & 0x0000FFFF0000FFFF) | ((bb & 0x0000FFFF0000FFFF) << 16)
    bb = ((bb >> 32) | (bb << 32)) & FULL
    return bb


class Abort(Exception):
    pass


TT = {}
HISTORY = [0] * 4096
NODES = 0
DEADLINE = float("inf")


# ---------------- evaluation ----------------
def evaluate(me, opp):
    m_sc = 0
    o_sc = 0
    for r in range(8):
        sh = r << 3
        m_sc += PM[r] * ((me >> sh) & 255).bit_count()
        o_sc += PO[r] * ((opp >> sh) & 255).bit_count()
    sc = m_sc - o_sc

    my_att = ((me & NOT_A) << 7) | ((me & NOT_H) << 9)
    op_att = ((opp & NOT_A) >> 9) | ((opp & NOT_H) >> 7)
    sc += DEF_B * ((me & my_att).bit_count() - (opp & op_att).bit_count())
    sc += ATT_B * ((opp & my_att).bit_count() - (me & op_att).bit_count())

    occ = me | opp
    empty = FULL ^ occ
    # my immediate promotion threat (to row 7)
    if (((me << 8) & ROW7 & empty)
            | (((me & NOT_A) << 7) & ROW7 & ~me)
            | (((me & NOT_H) << 9) & ROW7 & ~me)):
        sc += PROMO_THREAT
    # opponent immediate promotion threat (to row 0)
    if (((opp >> 8) & ROW0 & empty)
            | (((opp & NOT_A) >> 9) & ROW0 & ~opp)
            | (((opp & NOT_H) >> 7) & ROW0 & ~opp)):
        sc -= PROMO_THREAT

    # unstoppable runners (exact: nothing outside the cone can ever interfere)
    SU = SHADOW_UP
    SD = SHADOW_DN
    my_best = 99
    bb = me
    while bb:
        lsb = bb & -bb
        bb ^= lsb
        sq = lsb.bit_length() - 1
        if not (SU[sq] & opp):
            d = 7 - (sq >> 3)
            if d < my_best:
                my_best = d
    op_best = 99
    bb = opp
    while bb:
        lsb = bb & -bb
        bb ^= lsb
        sq = lsb.bit_length() - 1
        if not (SD[sq] & me):
            d = sq >> 3
            if d < op_best:
                op_best = d
    if my_best != 99 and (op_best == 99 or my_best <= op_best):
        return RUNNER + sc - my_best * 400
    if op_best != 99 and (my_best == 99 or op_best < my_best):
        return -RUNNER + sc + op_best * 400
    return sc


# ---------------- move generation ----------------
# move encoded as int: src | (dst << 6)
def gen_moves(me, opp, tt_move=-1):
    occ = me | opp
    empty = FULL ^ occ
    res = []
    app = res.append
    H = HISTORY
    T = 1 << 28
    bb = ((me & NOT_A) << 7) & opp          # capture up-left
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        m = (d - 7) | (d << 6)
        k = 100000 + (d & 56)
        if d >= 56: k += 1000000
        if m == tt_move: k = T
        app((k, m))
    bb = ((me & NOT_H) << 9) & opp          # capture up-right
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        m = (d - 9) | (d << 6)
        k = 100000 + (d & 56)
        if d >= 56: k += 1000000
        if m == tt_move: k = T
        app((k, m))
    bb = (me << 8) & empty                  # straight
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        m = (d - 8) | (d << 6)
        r = d >> 3
        h = H[m]
        k = r * 1000 + (h if h < 900 else 900)
        if r == 7: k += 1000000
        if m == tt_move: k = T
        app((k, m))
    bb = ((me & NOT_A) << 7) & empty        # quiet up-left
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        m = (d - 7) | (d << 6)
        r = d >> 3
        h = H[m]
        k = r * 1000 + (h if h < 900 else 900)
        if r == 7: k += 1000000
        if m == tt_move: k = T
        app((k, m))
    bb = ((me & NOT_H) << 9) & empty        # quiet up-right
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        m = (d - 9) | (d << 6)
        r = d >> 3
        h = H[m]
        k = r * 1000 + (h if h < 900 else 900)
        if r == 7: k += 1000000
        if m == tt_move: k = T
        app((k, m))
    res.sort(reverse=True)
    return res


def gen_cap_promo(me, opp):
    """Captures plus any move landing on the promotion row (for quiescence)."""
    occ = me | opp
    empty = FULL ^ occ
    res = []
    app = res.append
    bb = ((me & NOT_A) << 7) & opp
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        app((100 + (d >> 3), (d - 7) | (d << 6)))
    bb = ((me & NOT_H) << 9) & opp
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        app((100 + (d >> 3), (d - 9) | (d << 6)))
    bb = (me << 8) & empty & ROW7
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        app((1000, (d - 8) | (d << 6)))
    bb = ((me & NOT_A) << 7) & empty & ROW7
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        app((1000, (d - 7) | (d << 6)))
    bb = ((me & NOT_H) << 9) & empty & ROW7
    while bb:
        lsb = bb & -bb; bb ^= lsb
        d = lsb.bit_length() - 1
        app((1000, (d - 9) | (d << 6)))
    res.sort(reverse=True)
    return res


# ---------------- quiescence ----------------
def qsearch(me, opp, alpha, beta, ply, qd):
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise Abort()
    stand = evaluate(me, opp)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    if qd >= MAX_QDEPTH:
        return alpha
    vf = vflip
    for k, m in gen_cap_promo(me, opp):
        d = m >> 6
        dm = 1 << d
        me2 = (me ^ (1 << (m & 63))) | dm
        if dm & opp:
            opp2 = opp ^ dm
        else:
            opp2 = opp
        if (me2 & ROW7) or opp2 == 0:
            return WIN - ply - 1
        sc = -qsearch(vf(opp2), vf(me2), -beta, -alpha, ply + 1, qd + 1)
        if sc >= beta:
            return beta
        if sc > alpha:
            alpha = sc
    return alpha


# ---------------- alpha-beta ----------------
def search(me, opp, depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise Abort()
    alpha0 = alpha
    beta0 = beta
    tt_move = -1
    key = (me << 64) | opp
    ent = TT.get(key)
    if ent is not None:
        ed, ev, ef, em = ent
        if ev > MATE: ev -= ply
        elif ev < -MATE: ev += ply
        if ed >= depth:
            if ef == 0:
                return ev
            elif ef == 1:
                if ev > alpha: alpha = ev
            else:
                if ev < beta: beta = ev
            if alpha >= beta:
                return ev
        tt_move = em
    if depth <= 0:
        return qsearch(me, opp, alpha, beta, ply, 0)
    moves = gen_moves(me, opp, tt_move)
    if not moves:
        return -WIN + ply          # no legal moves => lost
    best = -INF
    bm = -1
    vf = vflip
    H = HISTORY
    for k, m in moves:
        d = m >> 6
        dm = 1 << d
        me2 = (me ^ (1 << (m & 63))) | dm
        if dm & opp:
            opp2 = opp ^ dm
            cap = True
        else:
            opp2 = opp
            cap = False
        if (me2 & ROW7) or opp2 == 0:
            sc = WIN - ply - 1
        else:
            cd = depth - 1
            if cd == 0 and (opp2 & ROW1):   # horizon: opp about to promote
                cd = 1
            sc = -search(vf(opp2), vf(me2), cd, -beta, -alpha, ply + 1)
        if sc > best:
            best = sc
            bm = m
        if sc > alpha:
            alpha = sc
            if alpha >= beta:
                if not cap:
                    H[m] += depth * depth
                break
    if best <= alpha0:
        ef = 2
    elif best >= beta0:
        ef = 1
    else:
        ef = 0
    sv = best
    if sv > MATE: sv += ply
    elif sv < -MATE: sv -= ply
    TT[key] = (depth, sv, ef, bm)
    return best


# ---------------- helpers ----------------
def _convert(m, flip):
    s = m & 63
    d = m >> 6
    r1 = s >> 3; c1 = s & 7
    r2 = d >> 3; c2 = d & 7
    if flip:
        r1 = 7 - r1
        r2 = 7 - r2
    return ((r1, c1), (r2, c2))


def fallback_move(me, opp, color):
    """Always returns the first legal move in original coordinates."""
    try:
        dr = 1 if color == 'w' else -1
        occ = set(me) | set(opp)
        opps = set(opp)
        for (r, c) in me:
            nr = r + dr
            if 0 <= nr < 8:
                if (nr, c) not in occ:
                    return ((r, c), (nr, c))
                for nc in (c - 1, c + 1):
                    if 0 <= nc < 8 and ((nr, nc) not in occ or (nr, nc) in opps):
                        return ((r, c), (nr, nc))
        p = tuple(me[0])
        return (p, p)
    except Exception:
        return ((0, 0), (0, 0))


# ---------------- main policy ----------------
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global TT, HISTORY, NODES, DEADLINE
    DEADLINE = time.perf_counter() + TIME_LIMIT
    try:
        flip = (color == 'b')
        my_bb = 0
        op_bb = 0
        if flip:
            for r, c in me:
                my_bb |= 1 << ((7 - r) * 8 + c)
            for r, c in opp:
                op_bb |= 1 << ((7 - r) * 8 + c)
        else:
            for r, c in me:
                my_bb |= 1 << (r * 8 + c)
            for r, c in opp:
                op_bb |= 1 << (r * 8 + c)

        moves = gen_moves(my_bb, op_bb)
        if not moves:
            return fallback_move(me, opp, color)
        move_list = [m for k, m in moves]
        chosen = move_list[0]

        # play an immediate win instantly
        for m in move_list:
            d = m >> 6
            dm = 1 << d
            me2 = (my_bb ^ (1 << (m & 63))) | dm
            opp2 = (op_bb ^ dm) if (dm & op_bb) else op_bb
            if (me2 & ROW7) or opp2 == 0:
                return _convert(m, flip)

        if len(move_list) > 1:
            TT = {}
            HISTORY = [0] * 4096
            NODES = 0
            scores = {m: 0 for m in move_list}
            vf = vflip
            depth = 1
            while depth <= MAX_DEPTH:
                if time.perf_counter() > DEADLINE:
                    break
                move_list.sort(key=scores.__getitem__, reverse=True)
                cur_best = None
                cur_val = -INF
                alpha = -INF
                try:
                    for m in move_list:
                        d = m >> 6
                        dm = 1 << d
                        me2 = (my_bb ^ (1 << (m & 63))) | dm
                        opp2 = (op_bb ^ dm) if (dm & op_bb) else op_bb
                        if (me2 & ROW7) or opp2 == 0:
                            sc = WIN - 1
                        else:
                            cd = depth - 1
                            if cd == 0 and (opp2 & ROW1):
                                cd = 1
                            sc = -search(vf(opp2), vf(me2), cd, -INF, -alpha, 1)
                        scores[m] = sc
                        if sc > cur_val:
                            cur_val = sc
                            cur_best = m
                        if sc > alpha:
                            alpha = sc
                except Abort:
                    break
                if cur_best is not None:
                    chosen = cur_best
                    if cur_val >= MATE:
                        break
                depth += 1
        return _convert(chosen, flip)
    except Exception:
        return fallback_move(me, opp, color)
