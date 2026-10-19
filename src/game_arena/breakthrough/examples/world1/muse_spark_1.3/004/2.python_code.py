
import time

INF = 1000000
MASK64 = (1 << 64) - 1
FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080
NOT_A = MASK64 ^ FILE_A
NOT_H = MASK64 ^ FILE_H

try:
    int.bit_count
    def popcnt(x):
        return x.bit_count()
except AttributeError:
    def popcnt(x):
        return bin(x).count("1")

CENTER_COL = [-12, -4, 4, 10, 10, 4, -4, -12]
ADV = [0, 10, 35, 75, 150, 260, 500, 0]

PST_W = [0]*64
PST_B = [0]*64
FRONT_W = [0]*64
FRONT_B = [0]*64
for _sq in range(64):
    _r = _sq >> 3
    _c = _sq & 7
    PST_W[_sq] = ADV[_r] + CENTER_COL[_c]
    PST_B[_sq] = ADV[7 - _r] + CENTER_COL[_c]
    _m = 0
    for _rr in range(_r+1, 8):
        for _cc in (_c-1, _c, _c+1):
            if 0 <= _cc < 8:
                _m |= 1 << (_rr*8+_cc)
    FRONT_W[_sq] = _m
    _m2 = 0
    for _rr in range(0, _r):
        for _cc in (_c-1, _c, _c+1):
            if 0 <= _cc < 8:
                _m2 |= 1 << (_rr*8+_cc)
    FRONT_B[_sq] = _m2

MAT = 350
DEF_BONUS = 30
HANG_PEN = 80
PASS_BONUS = 120

class _Timeout(Exception):
    pass

def _gen_moves(w, b, turn):
    occ = w | b
    moves = []
    if turn == 'w':
        p = w
        while p:
            lsb = p & -p
            f = lsb.bit_length() - 1
            p ^= lsb
            r = f >> 3
            c = f & 7
            if r >= 7:
                continue
            t = f + 8
            if ((occ >> t) & 1) == 0:
                moves.append((f, t))
            if c > 0:
                t2 = f + 7
                if (w >> t2) & 1 == 0:
                    moves.append((f, t2))
            if c < 7:
                t3 = f + 9
                if (w >> t3) & 1 == 0:
                    moves.append((f, t3))
    else:
        p = b
        while p:
            lsb = p & -p
            f = lsb.bit_length() - 1
            p ^= lsb
            r = f >> 3
            c = f & 7
            if r <= 0:
                continue
            t = f - 8
            if ((occ >> t) & 1) == 0:
                moves.append((f, t))
            if c > 0:
                t2 = f - 9
                if (b >> t2) & 1 == 0:
                    moves.append((f, t2))
            if c < 7:
                t3 = f - 7
                if (b >> t3) & 1 == 0:
                    moves.append((f, t3))
    return moves

def _do_move(w, b, turn, f, t):
    bf = 1 << f
    bt = 1 << t
    if turn == 'w':
        nw = (w ^ bf) | bt
        if b & bt:
            nb = b ^ bt
        else:
            nb = b
    else:
        nb = (b ^ bf) | bt
        if w & bt:
            nw = w ^ bt
        else:
            nw = w
    return nw, nb

def _eval_white(w, b):
    cw = popcnt(w)
    cb = popcnt(b)
    score = (cw - cb) * MAT
    # white PST + passed
    tmp = w
    sw = 0
    pw = 0
    while tmp:
        lsb = tmp & -tmp
        idx = lsb.bit_length() - 1
        tmp ^= lsb
        sw += PST_W[idx]
        if (b & FRONT_W[idx]) == 0:
            pw += 1
    tmp = b
    sb = 0
    pb = 0
    while tmp:
        lsb = tmp & -tmp
        idx = lsb.bit_length() - 1
        tmp ^= lsb
        sb += PST_B[idx]
        if (w & FRONT_B[idx]) == 0:
            pb += 1
    score += sw - sb
    score += (pw - pb) * PASS_BONUS
    wa = (((w & NOT_H) << 9) | ((w & NOT_A) << 7)) & MASK64
    ba = (((b & NOT_H) >> 7) | ((b & NOT_A) >> 9))
    wd = popcnt(wa & w)
    bd = popcnt(ba & b)
    score += (wd - bd) * DEF_BONUS
    # hanging: attacked but not defended
    wh = popcnt((ba & w) & (MASK64 ^ wa))
    bh = popcnt((wa & b) & (MASK64 ^ ba))
    score += (-wh + bh) * HANG_PEN
    return score

def policy(me, opp, color):
    try:
        start = time.perf_counter()
        deadline = start + 0.85
        if color == 'w':
            turn = 'w'
            w = 0
            for (r, c) in me:
                w |= 1 << (r*8+c)
            b = 0
            for (r, c) in opp:
                b |= 1 << (r*8+c)
        else:
            turn = 'b'
            b = 0
            for (r, c) in me:
                b |= 1 << (r*8+c)
            w = 0
            for (r, c) in opp:
                w |= 1 << (r*8+c)

        moves = _gen_moves(w, b, turn)

        def _to_rc(m):
            f, t = m
            return ((f>>3, f&7), (t>>3, t&7))

        if not moves:
            fr, fc = me[0]
            return ((fr, fc), (fr, fc))
        if len(moves) == 1:
            return _to_rc(moves[0])

        promo_row = 7 if turn == 'w' else 0
        for f, t in moves:
            if (t >> 3) == promo_row:
                return _to_rc((f, t))
        # capture last piece wins immediately
        opp_bb = b if turn == 'w' else w
        if popcnt(opp_bb) == 1:
            for f, t in moves:
                if (opp_bb >> t) & 1:
                    return _to_rc((f, t))

        # order helper
        def _order(mvs):
            scored = []
            if turn == 'w':
                for f, t in mvs:
                    s = 0
                    if (b >> t) & 1:
                        s += 2000
                    s += PST_W[t] - PST_W[f] // 2
                    if (t & 7) >= 2 and (t & 7) <= 5:
                        s += 5
                    scored.append((s, (f, t)))
            else:
                for f, t in mvs:
                    s = 0
                    if (w >> t) & 1:
                        s += 2000
                    s += PST_B[t] - PST_B[f] // 2
                    if (t & 7) >= 2 and (t & 7) <= 5:
                        s += 5
                    scored.append((s, (f, t)))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [m for _, m in scored]

        ordered = _order(moves)
        best = ordered[0]

        total = popcnt(w) + popcnt(b)
        if total > 24:
            max_depth = 3
        elif total > 16:
            max_depth = 4
        elif total > 10:
            max_depth = 5
        else:
            max_depth = 6

        nodes = [0]

        def negamax(cw, cb, cturn, depth, alpha, beta, ply):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0 and time.perf_counter() > deadline:
                raise _Timeout()
            if cw == 0:
                if cturn == 'w':
                    return -INF + ply
                else:
                    return INF - ply
            if cb == 0:
                if cturn == 'w':
                    return INF - ply
                else:
                    return -INF + ply
            if depth == 0:
                s = _eval_white(cw, cb)
                return s if cturn == 'w' else -s
            mvs = _gen_moves(cw, cb, cturn)
            if not mvs:
                return -INF + ply
            # quick win detection + ordering
            # build ordered list inline
            if cturn == 'w':
                # check promotion win first
                for ff, tt in mvs:
                    if (tt >> 3) == 7:
                        return INF - ply
                    if cb != 0 and popcnt(cb) == 1 and (cb >> tt) & 1:
                        return INF - ply
                # order captures first
                # simple sort by capture + pst
                scored = []
                for ff, tt in mvs:
                    sc = PST_W[tt]
                    if (cb >> tt) & 1:
                        sc += 2000
                    scored.append((sc, ff, tt))
                scored.sort(key=lambda x: x[0], reverse=True)
            else:
                for ff, tt in mvs:
                    if (tt >> 3) == 0:
                        return INF - ply
                    if cw != 0 and popcnt(cw) == 1 and (cw >> tt) & 1:
                        return INF - ply
                scored = []
                for ff, tt in mvs:
                    sc = PST_B[tt]
                    if (cw >> tt) & 1:
                        sc += 2000
                    scored.append((sc, ff, tt))
                scored.sort(key=lambda x: x[0], reverse=True)
            bestv = -INF
            nturn = 'b' if cturn == 'w' else 'w'
            for _, ff, tt in scored:
                nw2, nb2 = _do_move(cw, cb, cturn, ff, tt)
                # win by capture all already handled, but double check
                if nw2 == 0 or nb2 == 0:
                    return INF - ply
                v = -negamax(nw2, nb2, nturn, depth-1, -beta, -alpha, ply+1)
                if v > bestv:
                    bestv = v
                    if bestv >= beta:
                        break
                    if bestv > alpha:
                        alpha = bestv
            return bestv

        # iterative deepening at root
        for depth in range(1, max_depth+1):
            try:
                if time.perf_counter() > deadline:
                    break
                alpha = -INF
                beta = INF
                local_best = ordered[0]
                local_best_score = -INF
                # score each root move
                root_scores = []
                nturn = 'b' if turn == 'w' else 'w'
                for f, t in ordered:
                    nw, nb = _do_move(w, b, turn, f, t)
                    # already checked promotion, but deeper win by capture-all
                    if nw == 0 or nb == 0:
                        return _to_rc((f, t))
                    v = -negamax(nw, nb, nturn, depth-1, -beta, -alpha, 1)
                    root_scores.append((v, (f, t)))
                    if v > local_best_score:
                        local_best_score = v
                        local_best = (f, t)
                    if v > alpha:
                        alpha = v
                    if time.perf_counter() > deadline:
                        raise _Timeout()
                # reorder for next iteration
                root_scores.sort(key=lambda x: x[0], reverse=True)
                ordered = [m for _, m in root_scores]
                best = local_best
                if local_best_score >= INF - 1000:
                    break
                # if time very low, stop
                if time.perf_counter() > deadline:
                    break
            except _Timeout:
                break

        return _to_rc(best)
    except Exception:
        try:
            # fallback: first legal via set logic
            my_set = set((r, c) for r, c in me)
            op_set = set((r, c) for r, c in opp)
            occ = my_set | op_set
            d = 1 if color == 'w' else -1
            for (r, c) in me:
                nr = r + d
                if 0 <= nr < 8:
                    if (nr, c) not in occ:
                        return ((r, c), (nr, c))
                    for dc in (-1, 1):
                        nc = c + dc
                        if 0 <= nc < 8 and (nr, nc) not in my_set:
                            # diagonal allowed if empty or opp
                            return ((r, c), (nr, nc))
            # last resort
            fr, fc = me[0]
            return ((fr, fc), (fr, fc))
        except Exception:
            try:
                fr, fc = me[0]
                return ((fr, fc), (fr, fc))
            except Exception:
                return ((0, 0), (1, 0))
