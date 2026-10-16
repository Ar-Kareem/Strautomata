
import time
import random
import sys

sys.setrecursionlimit(10000)

# ---------------- constants ----------------
MANV = 100
KINGV = 160
INF = 1 << 30
MATE = 1 << 20
MAX_DEPTH = 24
TIME_LIMIT = 0.80
MOB = 1

PROG = (4, 5, 6, 7, 9, 11, 14)          # man bonus by advancement
COLB = (0, 1, 2, 3, 3, 2, 1, 0)         # man bonus by column
MPSTW = [[PROG[min(r, 6)] + COLB[c] for c in range(8)] for r in range(8)]
MPSTB = [[PROG[min(7 - r, 6)] + COLB[c] for c in range(8)] for r in range(8)]
_CENTERS = ((3, 3), (3, 4), (4, 3), (4, 4))
KCEN = [[6 - 2 * min(abs(r - cr) + abs(c - cc) for cr, cc in _CENTERS)
         for c in range(8)] for r in range(8)]

# Zobrist keys: 0 white man, 1 white king, 2 black man, 3 black king
_rng = random.Random(20240501)
ZOB = [[_rng.getrandbits(64) for _ in range(64)] for _ in range(4)]
ZWSIDE = _rng.getrandbits(64)

TT = {}
DEADLINE = 0.0
NODES = 0
_LAST = None      # ((mm, mk, om, ok) after our capture, landing square)


class _Timeout(Exception):
    pass


# ---------------- move generation ----------------
def _caps_piece(r, c, king, om, ok, occ, color):
    res = []
    if king:
        dirs = ((1, 1), (1, -1), (-1, 1), (-1, -1))
        pr = -1
    elif color == 'w':
        dirs = ((1, 1), (1, -1))
        pr = 7
    else:
        dirs = ((-1, 1), (-1, -1))
        pr = 0
    for dr, dc in dirs:
        tr = r + dr + dr
        tc = c + dc + dc
        if 0 <= tr < 8 and 0 <= tc < 8:
            mid = (r + dr, c + dc)
            dst = (tr, tc)
            if (mid in om or mid in ok) and dst not in occ:
                res.append(((r, c), dst, mid, (not king) and tr == pr))
    return res


def _all_caps(mm, mk, om, ok, occ, color):
    res = []
    for r, c in mm:
        res += _caps_piece(r, c, False, om, ok, occ, color)
    for r, c in mk:
        res += _caps_piece(r, c, True, om, ok, occ, color)
    return res


def _quiets(mm, mk, occ, color):
    res = []
    if color == 'w':
        dr, pr = 1, 7
    else:
        dr, pr = -1, 0
    for r, c in mm:
        nr = r + dr
        if 0 <= nr < 8:
            nc = c + 1
            if nc < 8 and (nr, nc) not in occ:
                res.append(((r, c), (nr, nc), None, nr == pr))
            nc = c - 1
            if nc >= 0 and (nr, nc) not in occ:
                res.append(((r, c), (nr, nc), None, nr == pr))
    for r, c in mk:
        for dr2, dc2 in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
            nr = r + dr2
            nc = c + dc2
            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in occ:
                res.append(((r, c), (nr, nc), None, False))
    return res


# ---------------- make / unmake ----------------
def _do_move(mv, mm, mk, om, ok, occ, h, color):
    src, dst, cap, promo = mv
    if color == 'w':
        im = 1 if src in mk else 0
    else:
        im = 3 if src in mk else 2
    king = im & 1
    if king:
        mk.discard(src)
    else:
        mm.discard(src)
    if king:
        idst = im
    elif promo:
        idst = 1 if color == 'w' else 3
    else:
        idst = 0 if color == 'w' else 2
    if idst & 1:
        mk.add(dst)
    else:
        mm.add(dst)
    occ.discard(src)
    occ.add(dst)
    h ^= ZOB[im][src[0] * 8 + src[1]] ^ ZOB[idst][dst[0] * 8 + dst[1]]
    icap = -1
    if cap is not None:
        if cap in ok:
            ok.discard(cap)
            icap = 3 if color == 'w' else 1
        else:
            om.discard(cap)
            icap = 2 if color == 'w' else 0
        occ.discard(cap)
        h ^= ZOB[icap][cap[0] * 8 + cap[1]]
    return h, (king, idst, im, icap)


def _undo_move(mv, undo, mm, mk, om, ok, occ, h, color):
    src, dst, cap, promo = mv
    king, idst, im, icap = undo
    if idst & 1:
        mk.discard(dst)
    else:
        mm.discard(dst)
    if king:
        mk.add(src)
    else:
        mm.add(src)
    occ.discard(dst)
    occ.add(src)
    if cap is not None:
        if icap & 1:
            ok.add(cap)
        else:
            om.add(cap)
        occ.add(cap)
    return h


# ---------------- evaluation ----------------
def _evaluate(mm, mk, om, ok, color):
    if color == 'w':
        pm, po = MPSTW, MPSTB
    else:
        pm, po = MPSTB, MPSTW
    s = 0
    for r, c in mm:
        s += MANV + pm[r][c]
    for r, c in mk:
        s += KINGV + KCEN[r][c]
    for r, c in om:
        s -= MANV + po[r][c]
    for r, c in ok:
        s -= KINGV + KCEN[r][c]
    return s


def _tt_store(key, depth, best, alpha0, beta, bestmove):
    if best >= beta:
        flag = 1
    elif best <= alpha0:
        flag = 2
    else:
        flag = 0
    TT[key] = (depth, best, flag, bestmove)


# ---------------- search ----------------
def _cont_search(mm, mk, om, ok, color, occ, h, sq, depth, alpha, beta, ply):
    # forced continuation of a multi-jump with the piece on sq
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() >= DEADLINE:
        raise _Timeout()
    caps = _caps_piece(sq[0], sq[1], sq in mk, om, ok, occ, color)
    best = -INF
    oc = 'b' if color == 'w' else 'w'
    for mv in caps:
        h2, undo = _do_move(mv, mm, mk, om, ok, occ, h, color)
        dst = mv[1]
        if not mv[3]:
            cont = _caps_piece(dst[0], dst[1], dst in mk, om, ok, occ, color)
        else:
            cont = ()
        if cont:
            val = _cont_search(mm, mk, om, ok, color, occ, h2, dst, depth,
                               alpha, beta, ply)
        else:
            val = -_search(om, ok, mm, mk, oc, occ, h2, depth,
                           -beta, -alpha, ply + 1)
        _undo_move(mv, undo, mm, mk, om, ok, occ, h2, color)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
            if alpha >= beta:
                break
    return best


def _search(mm, mk, om, ok, color, occ, h, depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() >= DEADLINE:
        raise _Timeout()
    ttkey = (h ^ ZWSIDE) if color == 'w' else h
    ent = TT.get(ttkey)
    ttmove = None
    if ent is not None:
        ed, ev, ef, em = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev >= beta:
                return ev
            if ef == 2 and ev <= alpha:
                return ev
        ttmove = em
    alpha0 = alpha
    best = -INF
    bestmove = None
    oc = 'b' if color == 'w' else 'w'
    caps = _all_caps(mm, mk, om, ok, occ, color)
    if caps:                                   # captures are mandatory
        if ttmove is not None:
            caps.sort(key=lambda m: m != ttmove)
        else:
            caps.sort(key=lambda m: 0 if m[2] in ok else 1)
        nd = depth - 1 if depth > 0 else 0     # quiescence: search captures
        for mv in caps:
            h2, undo = _do_move(mv, mm, mk, om, ok, occ, h, color)
            dst = mv[1]
            if not mv[3]:
                cont = _caps_piece(dst[0], dst[1], dst in mk, om, ok, occ, color)
            else:
                cont = ()
            if cont:
                val = _cont_search(mm, mk, om, ok, color, occ, h2, dst, nd,
                                   alpha, beta, ply)
            else:
                val = -_search(om, ok, mm, mk, oc, occ, h2, nd,
                               -beta, -alpha, ply + 1)
            _undo_move(mv, undo, mm, mk, om, ok, occ, h2, color)
            if val > best:
                best = val
                bestmove = mv
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break
        _tt_store(ttkey, depth, best, alpha0, beta, bestmove)
        return best
    qm = _quiets(mm, mk, occ, color)
    if not qm:
        return -MATE + ply                      # no legal moves: loss
    if depth <= 0:
        return _evaluate(mm, mk, om, ok, color) + MOB * len(qm)
    pt = MPSTW if color == 'w' else MPSTB

    def qkey(m):
        s, d = m[0], m[1]
        v = 0
        if m[3]:
            v += 500
        if s in mk:
            v += KCEN[d[0]][d[1]] - KCEN[s[0]][s[1]]
        else:
            v += pt[d[0]][d[1]] - pt[s[0]][s[1]]
        if m == ttmove:
            v += 100000
        return v

    qm.sort(key=qkey, reverse=True)
    for mv in qm:
        h2, undo = _do_move(mv, mm, mk, om, ok, occ, h, color)
        val = -_search(om, ok, mm, mk, oc, occ, h2, depth - 1,
                       -beta, -alpha, ply + 1)
        _undo_move(mv, undo, mm, mk, om, ok, occ, h2, color)
        if val > best:
            best = val
            bestmove = mv
        if val > alpha:
            alpha = val
            if alpha >= beta:
                break
    _tt_store(ttkey, depth, best, alpha0, beta, bestmove)
    return best


# ---------------- helpers ----------------
def _init_hash(mm, mk, om, ok, color):
    if color == 'w':
        im, ik, jm, jk = 0, 1, 2, 3
    else:
        im, ik, jm, jk = 2, 3, 0, 1
    h = 0
    for r, c in mm:
        h ^= ZOB[im][r * 8 + c]
    for r, c in mk:
        h ^= ZOB[ik][r * 8 + c]
    for r, c in om:
        h ^= ZOB[jm][r * 8 + c]
    for r, c in ok:
        h ^= ZOB[jk][r * 8 + c]
    return h


def _root_key(m, mk, ok, pt):
    s, d, cap, promo = m
    v = 0
    if cap is not None:
        v += 10000 + (KINGV if cap in ok else MANV)
    if promo:
        v += 500
    if s in mk:
        v += KCEN[d[0]][d[1]] - KCEN[s[0]][s[1]]
    else:
        v += pt[d[0]][d[1]] - pt[s[0]][s[1]]
    return v


def _fallback(my_men, my_kings, opp_men, opp_kings, color):
    mm = {(int(r), int(c)) for r, c in my_men}
    mk = {(int(r), int(c)) for r, c in my_kings}
    om = {(int(r), int(c)) for r, c in opp_men}
    ok = {(int(r), int(c)) for r, c in opp_kings}
    occ = mm | mk | om | ok
    if color != 'w':
        color = 'b'
    caps = _all_caps(mm, mk, om, ok, occ, color)
    if caps:
        return (caps[0][0], caps[0][1])
    qm = _quiets(mm, mk, occ, color)
    if qm:
        return (qm[0][0], qm[0][1])
    if mm:
        s = next(iter(mm))
        return (s, s)
    if mk:
        s = next(iter(mk))
        return (s, s)
    return ((0, 0), (0, 0))


# ---------------- required API ----------------
def policy(my_men, my_kings, opp_men, opp_kings, color):
    global DEADLINE, NODES, TT, _LAST
    DEADLINE = time.perf_counter() + TIME_LIMIT
    NODES = 0
    TT = {}
    try:
        mm = {(int(r), int(c)) for r, c in my_men}
        mk = {(int(r), int(c)) for r, c in my_kings}
        om = {(int(r), int(c)) for r, c in opp_men}
        ok = {(int(r), int(c)) for r, c in opp_kings}
        occ = mm | mk | om | ok
        if color != 'w':
            color = 'b'

        # If we are asked to move again from the exact position left by our
        # previous capture, we must continue the multi-jump with that piece.
        moves = None
        forced = None
        if _LAST is not None:
            snap, fdst = _LAST
            if snap[0] == mm and snap[1] == mk and snap[2] == om and snap[3] == ok:
                forced = fdst
        _LAST = None
        if forced is not None:
            caps = _caps_piece(forced[0], forced[1], forced in mk,
                               om, ok, occ, color)
            if caps:
                moves = caps
        if moves is None:
            moves = _all_caps(mm, mk, om, ok, occ, color)
            if not moves:
                moves = _quiets(mm, mk, occ, color)
        if not moves:
            return _fallback(my_men, my_kings, opp_men, opp_kings, color)

        best = moves[0]
        if len(moves) > 1:
            h0 = _init_hash(mm, mk, om, ok, color)
            oc = 'b' if color == 'w' else 'w'
            pt = MPSTW if color == 'w' else MPSTB
            moves.sort(key=lambda m: _root_key(m, mk, ok, pt), reverse=True)
            try:
                depth = 1
                while depth <= MAX_DEPTH:
                    cur = None
                    curv = -INF
                    alpha = -INF
                    nd = depth - 1
                    for mv in moves:
                        h2, undo = _do_move(mv, mm, mk, om, ok, occ, h0, color)
                        dst = mv[1]
                        if mv[2] is not None and not mv[3]:
                            cont = _caps_piece(dst[0], dst[1], dst in mk,
                                               om, ok, occ, color)
                        else:
                            cont = ()
                        if cont:
                            val = _cont_search(mm, mk, om, ok, color, occ,
                                               h2, dst, nd, alpha, INF, 1)
                        else:
                            val = -_search(om, ok, mm, mk, oc, occ, h2, nd,
                                           -INF, -alpha, 1)
                        _undo_move(mv, undo, mm, mk, om, ok, occ, h2, color)
                        if val > curv:
                            curv = val
                            cur = mv
                        if val > alpha:
                            alpha = val
                    best = cur
                    moves.sort(key=lambda m: m != cur)
                    depth += 1
                    if curv >= MATE - 100:
                        break
                    if time.perf_counter() >= DEADLINE:
                        break
            except _Timeout:
                pass
            except Exception:
                pass

        # Remember the position after a capture for multi-jump continuity.
        if best[2] is not None:
            try:
                mm2 = {(int(r), int(c)) for r, c in my_men}
                mk2 = {(int(r), int(c)) for r, c in my_kings}
                om2 = {(int(r), int(c)) for r, c in opp_men}
                ok2 = {(int(r), int(c)) for r, c in opp_kings}
                occ2 = mm2 | mk2 | om2 | ok2
                _do_move(best, mm2, mk2, om2, ok2, occ2, 0, color)
                _LAST = ((mm2, mk2, om2, ok2), best[1])
            except Exception:
                _LAST = None
        return (best[0], best[1])
    except Exception:
        try:
            return _fallback(my_men, my_kings, opp_men, opp_kings, color)
        except Exception:
            return ((0, 0), (0, 0))
