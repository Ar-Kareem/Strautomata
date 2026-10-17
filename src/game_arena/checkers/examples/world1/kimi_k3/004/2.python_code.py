
import time

MAN = 100
KING = 300
INF = 10 ** 9
DIRS4 = ((-1, -1), (-1, 1), (1, -1), (1, 1))

def _forward(side):
    return -1 if side == 'b' else 1

def _promo(side):
    return 0 if side == 'b' else 7

def _opp(side):
    return 'w' if side == 'b' else 'b'

def _gen(bm, bk, wm, wk, side):
    """Return (moves, is_capture). Move=(fr,fc,tr,tc,captured_sq_or_None,is_king)."""
    if side == 'b':
        mym, myk, om, ok = bm, bk, wm, wk
    else:
        mym, myk, om, ok = wm, wk, bm, bk
    f = _forward(side)
    occ = bm | bk | wm | wk
    opp = om | ok
    caps = []
    for (r, c) in mym:
        mr = r + f
        tr = r + 2 * f
        for dc in (-1, 1):
            mc = c + dc
            tc = c + 2 * dc
            if 0 <= tr < 8 and 0 <= tc < 8 and (mr, mc) in opp and (tr, tc) not in occ:
                caps.append((r, c, tr, tc, (mr, mc), False))
    for (r, c) in myk:
        for (drr, dcc) in DIRS4:
            mr, mc = r + drr, c + dcc
            tr, tc = r + 2 * drr, c + 2 * dcc
            if 0 <= tr < 8 and 0 <= tc < 8 and (mr, mc) in opp and (tr, tc) not in occ:
                caps.append((r, c, tr, tc, (mr, mc), True))
    if caps:
        return caps, True
    moves = []
    for (r, c) in mym:
        tr = r + f
        for dc in (-1, 1):
            tc = c + dc
            if 0 <= tr < 8 and 0 <= tc < 8 and (tr, tc) not in occ:
                moves.append((r, c, tr, tc, None, False))
    for (r, c) in myk:
        for (drr, dcc) in DIRS4:
            tr, tc = r + drr, c + dcc
            if 0 <= tr < 8 and 0 <= tc < 8 and (tr, tc) not in occ:
                moves.append((r, c, tr, tc, None, True))
    return moves, False

def _has_capture(bm, bk, wm, wk, side):
    if side == 'b':
        mym, myk = bm, bk
        opp = wm | wk
    else:
        mym, myk = wm, wk
        opp = bm | bk
    f = _forward(side)
    occ = bm | bk | wm | wk
    for (r, c) in mym:
        mr = r + f
        tr = r + 2 * f
        for dc in (-1, 1):
            if (mr, c + dc) in opp:
                tc = c + 2 * dc
                if 0 <= tr < 8 and 0 <= tc < 8 and (tr, tc) not in occ:
                    return True
    for (r, c) in myk:
        for (drr, dcc) in DIRS4:
            if (r + drr, c + dcc) in opp:
                tr, tc = r + 2 * drr, c + 2 * dcc
                if 0 <= tr < 8 and 0 <= tc < 8 and (tr, tc) not in occ:
                    return True
    return False

def _make(bm, bk, wm, wk, side, mv):
    fr, fc, tr, tc, cap, is_king = mv
    if side == 'b':
        nm, nk, om, ok = set(bm), set(bk), set(wm), set(wk)
    else:
        nm, nk, om, ok = set(wm), set(wk), set(bm), set(bk)
    if is_king:
        nk.discard((fr, fc))
        nk.add((tr, tc))
    else:
        nm.discard((fr, fc))
        if tr == _promo(side):
            nk.add((tr, tc))
        else:
            nm.add((tr, tc))
    if cap is not None:
        if cap in om:
            om.discard(cap)
        else:
            ok.discard(cap)
    if side == 'b':
        return nm, nk, om, ok
    return om, ok, nm, nk

def _features(men, kings, color):
    sc = MAN * len(men) + KING * len(kings)
    if color == 'w':
        for (r, c) in men:
            prog = r
            sc += 4 * prog
            if prog >= 5:
                sc += 10
            if c == 0 or c == 7:
                sc += 2
            elif 2 <= c <= 5:
                sc += 2
    else:
        for (r, c) in men:
            prog = 7 - r
            sc += 4 * prog
            if prog >= 5:
                sc += 10
            if c == 0 or c == 7:
                sc += 2
            elif 2 <= c <= 5:
                sc += 2
    for (r, c) in kings:
        if 2 <= r <= 5:
            sc += 4
        if 2 <= c <= 5:
            sc += 3
    return sc

def policy(my_men, my_kings, opp_men, opp_kings, color):
    root = 'b' if color == 'b' else 'w'
    if root == 'b':
        bm = set(tuple(s) for s in my_men)
        bk = set(tuple(s) for s in my_kings)
        wm = set(tuple(s) for s in opp_men)
        wk = set(tuple(s) for s in opp_kings)
    else:
        wm = set(tuple(s) for s in my_men)
        wk = set(tuple(s) for s in my_kings)
        bm = set(tuple(s) for s in opp_men)
        bk = set(tuple(s) for s in opp_kings)

    deadline = time.time() + 0.9
    nodes = 0

    def eval_pos(bm_, bk_, wm_, wk_):
        sb = _features(bm_, bk_, 'b')
        sw = _features(wm_, wk_, 'w')
        return (sb - sw) if root == 'b' else (sw - sb)

    def move_key(side, mv):
        fr, fc, tr, tc, cap, is_king = mv
        promote = (not is_king) and tr == _promo(side)
        adv = (tr - fr) * (1 if side == 'w' else -1)
        return (cap is not None, promote, adv)

    class _TO(Exception):
        pass

    def search(bm_, bk_, wm_, wk_, side, depth, alpha, beta):
        nonlocal nodes
        nodes += 1
        if (nodes & 2047) == 0 and time.time() > deadline:
            raise _TO()
        moves, _ = _gen(bm_, bk_, wm_, wk_, side)
        if not moves:
            return -1000000 if side == root else 1000000
        if depth == 0:
            return eval_pos(bm_, bk_, wm_, wk_)
        pr = _promo(side)
        other = _opp(side)
        ordered = sorted(moves, key=lambda m: move_key(side, m), reverse=True)
        if side == root:
            best = -INF
            for mv in ordered:
                nbm, nbk, nwm, nwk = _make(bm_, bk_, wm_, wk_, side, mv)
                cap = mv[4]
                promoted = (not mv[5]) and (mv[3] == pr)
                if cap is not None and not promoted and _has_capture(nbm, nbk, nwm, nwk, side):
                    ns = side
                else:
                    ns = other
                val = search(nbm, nbk, nwm, nwk, ns, depth - 1, alpha, beta)
                if val > best:
                    best = val
                if best > alpha:
                    alpha = best
                if alpha >= beta:
                    break
            return best
        else:
            best = INF
            for mv in ordered:
                nbm, nbk, nwm, nwk = _make(bm_, bk_, wm_, wk_, side, mv)
                cap = mv[4]
                promoted = (not mv[5]) and (mv[3] == pr)
                if cap is not None and not promoted and _has_capture(nbm, nbk, nwm, nwk, side):
                    ns = side
                else:
                    ns = other
                val = search(nbm, nbk, nwm, nwk, ns, depth - 1, alpha, beta)
                if val < best:
                    best = val
                if best < beta:
                    beta = best
                if alpha >= beta:
                    break
            return best

    moves, _ = _gen(bm, bk, wm, wk, root)
    if not moves:
        # No legal move (terminal). Should not be queried; return a harmless tuple.
        anyp = (my_men or my_kings or [(0, 0)])[0]
        anyp = tuple(anyp)
        return (anyp, anyp)

    moves = sorted(moves, key=lambda m: move_key(root, m), reverse=True)
    best = moves[0]
    pr = _promo(root)
    other = _opp(root)
    try:
        for depth in range(1, 40):
            alpha = -INF
            beta = INF
            bestval = -INF
            bestmv = moves[0]
            for mv in moves:
                nbm, nbk, nwm, nwk = _make(bm, bk, wm, wk, root, mv)
                cap = mv[4]
                promoted = (not mv[5]) and (mv[3] == pr)
                if cap is not None and not promoted and _has_capture(nbm, nbk, nwm, nwk, root):
                    ns = root
                else:
                    ns = other
                val = search(nbm, nbk, nwm, nwk, ns, depth - 1, alpha, beta)
                if val > bestval:
                    bestval = val
                    bestmv = mv
                if val > alpha:
                    alpha = val
            best = bestmv
            moves.remove(bestmv)
            moves.insert(0, bestmv)
            if time.time() > deadline:
                break
    except _TO:
        pass

    return ((best[0], best[1]), (best[2], best[3]))
