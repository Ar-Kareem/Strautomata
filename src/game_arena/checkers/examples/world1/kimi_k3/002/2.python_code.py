
import time
import sys

sys.setrecursionlimit(1000000)

# ======================================================================
# Geometry precomputation
# ======================================================================
_D = ((-1, -1), (-1, 1), (1, -1), (1, 1))   # down-left, down-right, up-left, up-right
_NEI = [[-1] * 4 for _ in range(64)]
_JMP = [[-1] * 4 for _ in range(64)]
for _r in range(8):
    for _c in range(8):
        _s = _r * 8 + _c
        for _i in range(4):
            dr, dc = _D[_i]
            nr, nc = _r + dr, _c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                _NEI[_s][_i] = nr * 8 + nc
                jr, jc = _r + 2 * dr, _c + 2 * dc
                if 0 <= jr < 8 and 0 <= jc < 8:
                    _JMP[_s][_i] = jr * 8 + jc

_B_DIRS = (0, 1)          # black men move to lower rows
_W_DIRS = (2, 3)          # white men move to higher rows
_ALL_DIRS = (0, 1, 2, 3)
_OTHER = {'b': 'w', 'w': 'b'}

# ======================================================================
# Evaluation constants / tables
# ======================================================================
MAN = 100
KING = 300
MOB = 2
INF = 10 ** 7
MATE = 10 ** 6

_COL_BONUS = (-1, 1, 3, 4, 4, 3, 1, -1)
_PST_MAN = {'b': [0] * 64, 'w': [0] * 64}
_PST_KING = [0] * 64
for r in range(8):
    for c in range(8):
        s = r * 8 + c
        _PST_MAN['w'][s] = (5 * r + _COL_BONUS[c]
                            + (8 if r == 0 else 0)
                            + (6 if r == 5 else 0)
                            + (16 if r == 6 else 0))
        a = 7 - r
        _PST_MAN['b'][s] = (5 * a + _COL_BONUS[c]
                            + (8 if r == 7 else 0)
                            + (6 if r == 2 else 0)
                            + (16 if r == 1 else 0))
        _PST_KING[s] = int(3 * ((3 - abs(3.5 - r)) + (3 - abs(3.5 - c))))

_TT = {}
_nodes = 0
_deadline = 0.0


class _Timeout(Exception):
    pass


def _bits(sqs):
    b = 0
    for sq in sqs:
        r, c = sq
        b |= 1 << (r * 8 + c)
    return b


def _gen_moves(mm, mk, om, ok, side):
    """Returns (moves, captures_exist). Captures are mandatory."""
    occ = mm | mk | om | ok
    opp = om | ok
    moves = []
    mdirs = _B_DIRS if side == 'b' else _W_DIRS
    NEI = _NEI
    JMP = _JMP
    b = mm
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        b ^= lsb
        for d in mdirs:
            mid = NEI[s][d]
            if mid >= 0 and (opp >> mid) & 1:
                t = JMP[s][d]
                if t >= 0 and not (occ >> t) & 1:
                    moves.append((s, t, mid))
    b = mk
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        b ^= lsb
        for d in _ALL_DIRS:
            mid = NEI[s][d]
            if mid >= 0 and (opp >> mid) & 1:
                t = JMP[s][d]
                if t >= 0 and not (occ >> t) & 1:
                    moves.append((s, t, mid))
    if moves:
        return moves, True
    b = mm
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        b ^= lsb
        for d in mdirs:
            t = NEI[s][d]
            if t >= 0 and not (occ >> t) & 1:
                moves.append((s, t, -1))
    b = mk
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        b ^= lsb
        for d in _ALL_DIRS:
            t = NEI[s][d]
            if t >= 0 and not (occ >> t) & 1:
                moves.append((s, t, -1))
    return moves, False


def _piece_caps(mm, mk, om, ok, side, sq, king):
    occ = mm | mk | om | ok
    opp = om | ok
    dirs = _ALL_DIRS if king else (_B_DIRS if side == 'b' else _W_DIRS)
    res = []
    for d in dirs:
        mid = _NEI[sq][d]
        if mid >= 0 and (opp >> mid) & 1:
            t = _JMP[sq][d]
            if t >= 0 and not (occ >> t) & 1:
                res.append((sq, t, mid))
    return res


def _apply(mm, mk, om, ok, side, mv):
    s, t, c = mv
    fb = 1 << s
    tb = 1 << t
    promoted = False
    if mm & fb:
        mm &= ~fb
        if side == 'b':
            if t < 8:
                mk |= tb
                promoted = True
            else:
                mm |= tb
        else:
            if t >= 56:
                mk |= tb
                promoted = True
            else:
                mm |= tb
    else:
        mk &= ~fb
        mk |= tb
    if c >= 0:
        cb = 1 << c
        if om & cb:
            om &= ~cb
        else:
            ok &= ~cb
    return mm, mk, om, ok, promoted


def _order_moves(moves, side, ttmv, ok, mk):
    if side == 'b':
        def promo(t): return t < 8
    else:
        def promo(t): return t >= 56

    def keyf(mv):
        s, t, c = mv
        v = 0
        if c >= 0:
            v = 20 + (10 if (ok >> c) & 1 else 0) - (1 if (mk >> s) & 1 else 0)
        if promo(t):
            v += 6
        return v

    moves.sort(key=keyf, reverse=True)
    if ttmv is not None:
        try:
            moves.remove(ttmv)
            moves.insert(0, ttmv)
        except ValueError:
            pass


def _mobility(men, kings, occ, side):
    n = 0
    dirs = _B_DIRS if side == 'b' else _W_DIRS
    b = men
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        b ^= lsb
        for d in dirs:
            t = _NEI[s][d]
            if t >= 0 and not (occ >> t) & 1:
                n += 1
    b = kings
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        b ^= lsb
        for d in _ALL_DIRS:
            t = _NEI[s][d]
            if t >= 0 and not (occ >> t) & 1:
                n += 1
    return n


def _side_score(men, kings, pst):
    s = 0
    b = men
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb
        s += MAN + pst[sq]
    b = kings
    while b:
        lsb = b & -b
        sq = lsb.bit_length() - 1
        b ^= lsb
        s += KING + _PST_KING[sq]
    return s


def _evaluate(mm, mk, om, ok, side):
    opp = _OTHER[side]
    my = _side_score(mm, mk, _PST_MAN[side])
    op = _side_score(om, ok, _PST_MAN[opp])
    occ = mm | mk | om | ok
    return (my - op) + MOB * (_mobility(mm, mk, occ, side)
                              - _mobility(om, ok, occ, opp))


def _search(mm, mk, om, ok, side, depth, alpha, beta, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.time() >= _deadline:
        raise _Timeout()
    alpha0 = alpha
    key = (mm, mk, om, ok, side)
    ttmv = None
    ent = _TT.get(key)
    if ent is not None:
        ed, ev, ef, em = ent
        if ev > MATE // 2:
            ev -= ply
        elif ev < -MATE // 2:
            ev += ply
        if ed >= depth:
            if ef == 0:
                return ev
            elif ef == 1:
                if ev > alpha:
                    alpha = ev
            else:
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev
        ttmv = em
    moves, iscap = _gen_moves(mm, mk, om, ok, side)
    if not moves:
        return -MATE + ply
    if depth <= 0 and not iscap:
        return _evaluate(mm, mk, om, ok, side)
    _order_moves(moves, side, ttmv, ok, mk)
    best = -INF
    bestmv = None
    opp = _OTHER[side]
    for mv in moves:
        s, t, c = mv
        is_king = (mk >> s) & 1
        nmm, nmk, nom, nok, prom = _apply(mm, mk, om, ok, side, mv)
        if c >= 0 and not prom:
            val = _cont(nmm, nmk, nom, nok, side, t, is_king,
                        depth - 1, alpha, beta, ply + 1)
        else:
            val = -_search(nmm, nmk, nom, nok, opp,
                           depth - 1, -beta, -alpha, ply + 1)
        if val > best:
            best = val
            bestmv = mv
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break
    sv = best
    if best > MATE // 2:
        sv = best + ply
    elif best < -MATE // 2:
        sv = best - ply
    if best <= alpha0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _TT[key] = (depth, sv, flag, bestmv)
    return best


def _cont(mm, mk, om, ok, side, sq, king, depth, alpha, beta, ply):
    """Continue a multi-jump chain with the piece on sq (same side to move)."""
    caps = _piece_caps(mm, mk, om, ok, side, sq, king)
    opp = _OTHER[side]
    if not caps:
        return -_search(mm, mk, om, ok, opp, depth, -beta, -alpha, ply + 1)
    best = -INF
    for mv in caps:
        nmm, nmk, nom, nok, prom = _apply(mm, mk, om, ok, side, mv)
        if prom:
            val = -_search(nmm, nmk, nom, nok, opp, depth, -beta, -alpha, ply + 1)
        else:
            val = _cont(nmm, nmk, nom, nok, side, mv[1], king,
                        depth, alpha, beta, ply)
        if val > best:
            best = val
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break
    return best


def _root(mm, mk, om, ok, side, depth):
    global _nodes
    moves, iscap = _gen_moves(mm, mk, om, ok, side)
    ent = _TT.get((mm, mk, om, ok, side))
    ttmv = ent[3] if ent is not None else None
    _order_moves(moves, side, ttmv, ok, mk)
    best = -INF
    bestmv = None
    alpha = -INF
    beta = INF
    opp = _OTHER[side]
    for mv in moves:
        _nodes += 1
        if (_nodes & 1023) == 0 and time.time() >= _deadline:
            raise _Timeout()
        s, t, c = mv
        is_king = (mk >> s) & 1
        nmm, nmk, nom, nok, prom = _apply(mm, mk, om, ok, side, mv)
        if c >= 0 and not prom:
            val = _cont(nmm, nmk, nom, nok, side, t, is_king,
                        depth - 1, alpha, beta, 1)
        else:
            val = -_search(nmm, nmk, nom, nok, opp,
                           depth - 1, -beta, -alpha, 1)
        if val > best:
            best = val
            bestmv = mv
            if val > alpha:
                alpha = val
    _TT[(mm, mk, om, ok, side)] = (depth, best, 0, bestmv)
    return best, bestmv


def policy(my_men, my_kings, opp_men, opp_kings, color):
    global _deadline, _nodes, _TT
    mm = _bits(my_men)
    mk = _bits(my_kings)
    om = _bits(opp_men)
    ok = _bits(opp_kings)
    bestmv = None
    try:
        moves, _ = _gen_moves(mm, mk, om, ok, color)
        if not moves:
            return ((0, 0), (0, 0))      # no legal move (game over; never expected)
        bestmv = moves[0]
        if len(moves) > 1:
            _deadline = time.time() + 0.90
            _nodes = 0
            if len(_TT) > 1500000:
                _TT.clear()
            for depth in range(1, 64):
                try:
                    val, mv = _root(mm, mk, om, ok, color, depth)
                except _Timeout:
                    break
                if mv is not None:
                    bestmv = mv
                if val >= MATE // 2:
                    break
                if time.time() >= _deadline:
                    break
    except Exception:
        if bestmv is None:
            return ((0, 0), (0, 0))
    return ((bestmv[0] // 8, bestmv[0] % 8), (bestmv[1] // 8, bestmv[1] % 8))
