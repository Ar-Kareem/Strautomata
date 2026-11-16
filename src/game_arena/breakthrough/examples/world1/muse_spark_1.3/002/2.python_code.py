
import time

MASK64 = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
ROW0 = 0xFF
ROW1 = 0xFF << 8
ROW6 = 0xFF << 48
ROW7 = 0xFF << 56
ROW_MASK = [(0xFF << (8 * r)) & MASK64 for r in range(8)]

ADV_W = [0, 15, 30, 60, 100, 150, 220, 0]
FILE_BONUS = [-8, -3, 2, 7, 7, 2, -3, -8]

WHITE_CONE = [0]*64
BLACK_CONE = [0]*64
for sq in range(64):
    r = sq >> 3
    c = sq & 7
    m = 0
    for k in range(1, 8):
        r2 = r + k
        if r2 > 7:
            break
        for dc in range(-k, k+1):
            c2 = c + dc
            if 0 <= c2 < 8:
                m |= 1 << ((r2 << 3) | c2)
    WHITE_CONE[sq] = m
    m = 0
    for k in range(1, 8):
        r2 = r - k
        if r2 < 0:
            break
        for dc in range(-k, k+1):
            c2 = c + dc
            if 0 <= c2 < 8:
                m |= 1 << ((r2 << 3) | c2)
    BLACK_CONE[sq] = m

INF = 100000

class _Timeout(Exception):
    pass

_DEADLINE = 0.0
_NODES = 0
_TT = {}

def _bitcount(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")

def _gen_moves(W, B, wtm):
    if wtm:
        my = W
        occ = W | B
        dr = 1
    else:
        my = B
        occ = W | B
        dr = -1
    moves = []
    tmp = my
    while tmp:
        lsb = tmp & -tmp
        fr = lsb.bit_length() - 1
        tmp ^= lsb
        r = fr >> 3
        c = fr & 7
        r2 = r + dr
        if r2 < 0 or r2 > 7:
            continue
        base = r2 << 3
        # straight
        c2 = c
        to = base | c2
        bit = 1 << to
        if (occ & bit) == 0:
            moves.append((fr, to))
        # diag left c-1
        if c > 0:
            to2 = base | (c - 1)
            bit2 = 1 << to2
            if (my & bit2) == 0:
                moves.append((fr, to2))
        # diag right c+1
        if c < 7:
            to2 = base | (c + 1)
            bit2 = 1 << to2
            if (my & bit2) == 0:
                moves.append((fr, to2))
    return moves

def _move_score(fr, to, W, B, wtm):
    tr = to >> 3
    tc = to & 7
    if wtm:
        opp = B
        promo = (tr == 7)
        prog = tr
    else:
        opp = W
        promo = (tr == 0)
        prog = 7 - tr
    s = prog * 10 + FILE_BONUS[tc]
    if (opp >> to) & 1:
        s += 500
    if promo:
        s += 10000
    return s

def _evaluate_white(W, B, wtm):
    occ = W | B
    empty = (~occ) & MASK64
    W_att = (((W & (~FILE_A & MASK64)) << 7) | ((W & (~FILE_H & MASK64)) << 9)) & MASK64
    B_att = (((B & (~FILE_A & MASK64)) >> 9) | ((B & (~FILE_H & MASK64)) >> 7)) & MASK64
    if wtm:
        W6 = W & ROW6
        if W6:
            if ((W6 << 8) & empty & ROW7) != 0:
                return 9000
            notW = (~W) & MASK64
            if ((((W6 & (~FILE_A & MASK64)) << 7) & notW & ROW7) != 0) or ((((W6 & (~FILE_H & MASK64)) << 9) & notW & ROW7) != 0):
                return 9000
        if B != 0 and (B & (B - 1)) == 0:
            if (W_att & B) != 0:
                return 9000
    else:
        B1 = B & ROW1
        if B1:
            if ((B1 >> 8) & empty & ROW0) != 0:
                return -9000
            notB = (~B) & MASK64
            if ((((B1 & (~FILE_A & MASK64)) >> 9) & notB & ROW0) != 0) or ((((B1 & (~FILE_H & MASK64)) >> 7) & notB & ROW0) != 0):
                return -9000
        if W != 0 and (W & (W - 1)) == 0:
            if (B_att & W) != 0:
                return -9000

    pw = _bitcount(W)
    pb = _bitcount(B)
    score = (pw - pb) * 100

    tmp = W
    while tmp:
        lsb = tmp & -tmp
        sq = lsb.bit_length() - 1
        tmp ^= lsb
        r = sq >> 3
        c = sq & 7
        score += ADV_W[r] + FILE_BONUS[c]
        bit = 1 << sq
        attacked = (B_att & bit) != 0
        defended = (W_att & bit) != 0
        if attacked:
            if defended:
                score -= 8
            else:
                score -= 30
        else:
            if defended:
                score += 4

    tmp = B
    while tmp:
        lsb = tmp & -tmp
        sq = lsb.bit_length() - 1
        tmp ^= lsb
        r = sq >> 3
        c = sq & 7
        score -= (ADV_W[7 - r] + FILE_BONUS[c])
        bit = 1 << sq
        attacked = (W_att & bit) != 0
        defended = (B_att & bit) != 0
        if attacked:
            if defended:
                score += 8
            else:
                score += 30
        else:
            if defended:
                score -= 4

    # unstoppable runners
    wdist = 8
    tmp = W
    while tmp:
        lsb = tmp & -tmp
        sq = lsb.bit_length() - 1
        tmp ^= lsb
        if (WHITE_CONE[sq] & B) == 0:
            d = 7 - (sq >> 3)
            if d < wdist:
                wdist = d
                if d == 1:
                    break
    bdist = 8
    tmp = B
    while tmp:
        lsb = tmp & -tmp
        sq = lsb.bit_length() - 1
        tmp ^= lsb
        if (BLACK_CONE[sq] & W) == 0:
            d = (sq >> 3)
            if d < bdist:
                bdist = d
                if d == 1:
                    break
    hasW = wdist < 8
    hasB = bdist < 8
    if hasW and hasB:
        if wtm:
            white_wins = wdist <= bdist
        else:
            white_wins = wdist < bdist
        if white_wins:
            return 8000 - wdist * 20
        else:
            return -8000 + bdist * 20
    elif hasW:
        score += 450 + (6 - wdist) * 25
    elif hasB:
        score -= 450 + (6 - bdist) * 25
    return score

def _negamax(W, B, wtm, depth, alpha, beta, ply):
    global _NODES, _TT, _DEADLINE
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise _Timeout()
    # already decided positions
    if (W & ROW7) != 0:
        v = INF - ply
        return v if wtm else -v
    if (B & ROW0) != 0:
        v = -INF + ply
        return v if wtm else -v
    if W == 0:
        v = -INF + ply
        return v if wtm else -v
    if B == 0:
        v = INF - ply
        return v if wtm else -v

    moves = _gen_moves(W, B, wtm)
    if not moves:
        return -INF + ply

    if depth == 0:
        ev = _evaluate_white(W, B, wtm)
        return ev if wtm else -ev

    # TT
    key = (W, B, wtm)
    tt_best = None
    ent = _TT.get(key)
    if ent is not None:
        ed, es, ef, eb = ent
        if ed >= depth:
            if ef == 0:
                return es
            elif ef == 1:
                if es >= beta:
                    return es
            else:
                if es <= alpha:
                    return es
        tt_best = eb

    # order
    scored = []
    for fr, to in moves:
        if tt_best is not None and fr == tt_best[0] and to == tt_best[1]:
            s = 20000
        else:
            s = _move_score(fr, to, W, B, wtm)
        scored.append((s, fr, to))
    scored.sort(reverse=True, key=lambda x: x[0])

    best = -INF
    best_mv = (scored[0][1], scored[0][2])
    orig_alpha = alpha
    for _, fr, to in scored:
        fr_bit = 1 << fr
        to_bit = 1 << to
        if wtm:
            W2 = (W & (~fr_bit & MASK64)) | to_bit
            B2 = B & (~to_bit & MASK64)
            if (to_bit & ROW7) != 0 or B2 == 0:
                sc = INF - ply
            else:
                sc = -_negamax(W2, B2, False, depth - 1, -beta, -alpha, ply + 1)
        else:
            B2 = (B & (~fr_bit & MASK64)) | to_bit
            W2 = W & (~to_bit & MASK64)
            if (to_bit & ROW0) != 0 or W2 == 0:
                sc = INF - ply
            else:
                sc = -_negamax(W2, B2, True, depth - 1, -beta, -alpha, ply + 1)
        if sc > best:
            best = sc
            best_mv = (fr, to)
            if sc > alpha:
                alpha = sc
            if alpha >= beta:
                break
    # store
    if best <= orig_alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _TT[key] = (depth, best, flag, best_mv)
    return best

def policy(me, opp, color):
    global _DEADLINE, _NODES, _TT
    start = time.perf_counter()
    _DEADLINE = start + 0.88
    _NODES = 0
    _TT = {}
    wtm = (color == 'w')
    W = 0
    B = 0
    if wtm:
        for r, c in me:
            W |= 1 << ((r << 3) | c)
        for r, c in opp:
            B |= 1 << ((r << 3) | c)
    else:
        for r, c in me:
            B |= 1 << ((r << 3) | c)
        for r, c in opp:
            W |= 1 << ((r << 3) | c)
    W &= MASK64
    B &= MASK64

    moves = _gen_moves(W, B, wtm)
    if not moves:
        # no legal move, return something (will lose)
        if me:
            fr = me[0]
            return (fr, fr)
        return ((0, 0), (0, 0))
    # immediate winning moves
    last = 7 if wtm else 0
    for fr, to in moves:
        if (to >> 3) == last:
            return ((fr >> 3, fr & 7), (to >> 3, to & 7))
    if len(opp) == 1:
        orr, occ = opp[0]
        oto = (orr << 3) | occ
        for fr, to in moves:
            if to == oto:
                return ((fr >> 3, fr & 7), (to >> 3, to & 7))

    # order root
    scored_root = [(_move_score(fr, to, W, B, wtm), fr, to) for fr, to in moves]
    scored_root.sort(reverse=True, key=lambda x: x[0])
    ordered = [(fr, to) for _, fr, to in scored_root]
    best = ordered[0]

    try:
        # quick depth 1 to have score
        depth = 1
        while True:
            alpha = -INF
            beta = INF
            cur_best = best
            cur_best_score = -INF
            # move best from previous iteration first
            if best in ordered:
                ordered.remove(best)
                ordered.insert(0, best)
            # re-sort but keep best first? use scores + tt
            # build scored with tt hint
            tmp_scored = []
            key_root = None
            for fr, to in ordered:
                s = _move_score(fr, to, W, B, wtm)
                tmp_scored.append((s, fr, to))
            # put previous best on top
            tmp_scored.sort(reverse=True, key=lambda x: x[0])
            for _, fr, to in tmp_scored:
                if (fr, to) == best:
                    # ensure first
                    pass
            # force best first
            for i, (_, fr, to) in enumerate(tmp_scored):
                if (fr, to) == best:
                    tmp_scored.insert(0, tmp_scored.pop(i))
                    break
            for _, fr, to in tmp_scored:
                fr_bit = 1 << fr
                to_bit = 1 << to
                if wtm:
                    W2 = (W & (~fr_bit & MASK64)) | to_bit
                    B2 = B & (~to_bit & MASK64)
                    if (to_bit & ROW7) != 0 or B2 == 0:
                        sc = INF
                    else:
                        sc = -_negamax(W2, B2, False, depth - 1, -beta, -alpha, 1)
                else:
                    B2 = (B & (~fr_bit & MASK64)) | to_bit
                    W2 = W & (~to_bit & MASK64)
                    if (to_bit & ROW0) != 0 or W2 == 0:
                        sc = INF
                    else:
                        sc = -_negamax(W2, B2, True, depth - 1, -beta, -alpha, 1)
                if sc > cur_best_score:
                    cur_best_score = sc
                    cur_best = (fr, to)
                if sc > alpha:
                    alpha = sc
                if alpha >= beta:
                    break
            best = cur_best
            if cur_best_score >= INF - 50:
                break
            if time.perf_counter() > _DEADLINE - 0.05:
                break
            depth += 1
            if depth > 12:
                break
            # if not enough time for next depth, stop
            # estimate: need at least 0.05s
            if time.perf_counter() > _DEADLINE - 0.08 and depth > 3:
                break
    except _Timeout:
        pass
    except Exception:
        pass
    fr, to = best
    return ((fr >> 3, fr & 7), (to >> 3, to & 7))
