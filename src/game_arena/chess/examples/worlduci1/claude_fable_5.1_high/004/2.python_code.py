
import time
import random
from operator import itemgetter

random.seed(987654321)

INF = 10 ** 9
MATE = 100000
MAX_PLY = 96
TIME_BUDGET = 0.55

VAL = [0, 100, 320, 330, 500, 900, 0]
PT_MAP = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}
PROMO_CH = {5: 'q', 2: 'n', 4: 'r', 3: 'b'}
_key0 = itemgetter(0)


class TimeUp(Exception):
    pass


# ---------------- piece-square tables (rank 8 row first) ----------------
_PAWN = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0]
_KNIGHT = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50]
_BISHOP = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20]
_ROOK = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0]
_QUEEN = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20]
_KING_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20]
_KING_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50]


def _build(tbl):
    w = [0] * 64
    b = [0] * 64
    for sq in range(64):
        r, f = divmod(sq, 8)
        w[sq] = tbl[(7 - r) * 8 + f]
        b[sq] = tbl[r * 8 + f]
    return w, b


PSTV = [None] * 13
for _pt, _tbl in ((1, _PAWN), (2, _KNIGHT), (3, _BISHOP), (4, _ROOK), (5, _QUEEN)):
    _w, _b = _build(_tbl)
    PSTV[_pt + 6] = [VAL[_pt] + _w[s] for s in range(64)]
    PSTV[-_pt + 6] = [-(VAL[_pt] + _b[s]) for s in range(64)]
PSTV[6] = [0] * 64
PSTV[12] = [0] * 64
PSTV[0] = [0] * 64
KING_MG_W, KING_MG_B = _build(_KING_MG)
KING_EG_W, KING_EG_B = _build(_KING_EG)

# ---------------- geometry ----------------
KNIGHT = []
KING_M = []
RAYS = []
WP_ATT = []
BP_ATT = []
_KN = ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1))
_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
for _sq in range(64):
    _r, _f = divmod(_sq, 8)
    _kn = []
    for _dr, _df in _KN:
        _rr, _ff = _r + _dr, _f + _df
        if 0 <= _rr < 8 and 0 <= _ff < 8:
            _kn.append(_rr * 8 + _ff)
    KNIGHT.append(_kn)
    _km = []
    _rays = []
    for _dr, _df in _DIRS:
        _rr, _ff = _r + _dr, _f + _df
        if 0 <= _rr < 8 and 0 <= _ff < 8:
            _km.append(_rr * 8 + _ff)
        _ray = []
        _rr, _ff = _r + _dr, _f + _df
        while 0 <= _rr < 8 and 0 <= _ff < 8:
            _ray.append(_rr * 8 + _ff)
            _rr += _dr
            _ff += _df
        _rays.append(_ray)
    KING_M.append(_km)
    RAYS.append(_rays)
    _wp = []
    if _r > 0:
        if _f < 7:
            _wp.append(_sq - 7)
        if _f > 0:
            _wp.append(_sq - 9)
    WP_ATT.append(_wp)
    _bp = []
    if _r < 7:
        if _f > 0:
            _bp.append(_sq + 7)
        if _f < 7:
            _bp.append(_sq + 9)
    BP_ATT.append(_bp)

ALIGNED = [[False] * 64 for _ in range(64)]
DIST = [[0] * 64 for _ in range(64)]
for _a in range(64):
    _ra, _fa = divmod(_a, 8)
    for _b2 in range(64):
        _rb, _fb = divmod(_b2, 8)
        if _ra == _rb or _fa == _fb or abs(_ra - _rb) == abs(_fa - _fb):
            ALIGNED[_a][_b2] = True
        DIST[_a][_b2] = abs(_ra - _rb) + abs(_fa - _fb)
CMD = [0] * 64
for _sq in range(64):
    _r, _f = divmod(_sq, 8)
    CMD[_sq] = abs(2 * _r - 7) + abs(2 * _f - 7)

R_DIRS = (0, 1, 2, 3)
B_DIRS = (4, 5, 6, 7)
Q_DIRS = (0, 1, 2, 3, 4, 5, 6, 7)

ZOB = [[random.getrandbits(64) for _ in range(13)] for _ in range(64)]
SIDE_KEY = random.getrandbits(64)

# ---------------- global state ----------------
board = [0] * 64
KSQ = [0, 0, 0]
PST_SCORE = 0
NPM_W = 0
NPM_B = 0
PAWN_W = 0
PAWN_B = 0
HASH = 0
NODES = 0
DEADLINE = 0.0
ROOT_DEPTH = 1
ROOT_BEST = None
ROOT_COMPLETED = 0
TT = {}
SEEN = {}
LAST_COUNT = -1
PATH = [0] * (MAX_PLY + 8)
KILLERS = [[None, None] for _ in range(MAX_PLY + 8)]
HIST = [[0] * 4096, [0] * 4096]


def setup(pieces, side):
    global board, PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH
    board = [0] * 64
    KSQ[1] = -1
    KSQ[-1] = -1
    PST_SCORE = 0
    NPM_W = NPM_B = PAWN_W = PAWN_B = 0
    HASH = 0
    for sq_str, code in pieces.items():
        f = ord(sq_str[0].lower()) - 97
        r = int(sq_str[1]) - 1
        if not (0 <= f < 8 and 0 <= r < 8):
            continue
        sq = r * 8 + f
        pt = PT_MAP.get(code[1].upper())
        if pt is None:
            continue
        p = pt if code[0].lower() == 'w' else -pt
        board[sq] = p
        HASH ^= ZOB[sq][p + 6]
        PST_SCORE += PSTV[p + 6][sq]
        if p == 6:
            KSQ[1] = sq
        elif p == -6:
            KSQ[-1] = sq
        elif p == 1:
            PAWN_W += 1
        elif p == -1:
            PAWN_B += 1
        elif p > 0:
            NPM_W += VAL[p]
        else:
            NPM_B += VAL[-p]
    if side == -1:
        HASH ^= SIDE_KEY


def attacked(sq, by):
    bd = board
    if by == 1:
        for a in WP_ATT[sq]:
            if bd[a] == 1:
                return True
        for a in KNIGHT[sq]:
            if bd[a] == 2:
                return True
        for a in KING_M[sq]:
            if bd[a] == 6:
                return True
        rays = RAYS[sq]
        for d in R_DIRS:
            for a in rays[d]:
                q = bd[a]
                if q:
                    if q == 4 or q == 5:
                        return True
                    break
        for d in B_DIRS:
            for a in rays[d]:
                q = bd[a]
                if q:
                    if q == 3 or q == 5:
                        return True
                    break
        return False
    else:
        for a in BP_ATT[sq]:
            if bd[a] == -1:
                return True
        for a in KNIGHT[sq]:
            if bd[a] == -2:
                return True
        for a in KING_M[sq]:
            if bd[a] == -6:
                return True
        rays = RAYS[sq]
        for d in R_DIRS:
            for a in rays[d]:
                q = bd[a]
                if q:
                    if q == -4 or q == -5:
                        return True
                    break
        for d in B_DIRS:
            for a in rays[d]:
                q = bd[a]
                if q:
                    if q == -3 or q == -5:
                        return True
                    break
        return False


def gen_moves(side):
    bd = board
    moves = []
    app = moves.append
    for sq in range(64):
        p = bd[sq]
        if p * side <= 0:
            continue
        pt = p if p > 0 else -p
        if pt == 1:
            f = sq & 7
            if side == 1:
                t = sq + 8
                if t < 64 and bd[t] == 0:
                    if t >= 56:
                        app((sq, t, 5))
                        app((sq, t, 2))
                    else:
                        app((sq, t, 0))
                        if sq < 16 and bd[sq + 16] == 0:
                            app((sq, sq + 16, 0))
                if f > 0:
                    t = sq + 7
                    if t < 64 and bd[t] < 0:
                        if t >= 56:
                            app((sq, t, 5))
                            app((sq, t, 2))
                        else:
                            app((sq, t, 0))
                if f < 7:
                    t = sq + 9
                    if t < 64 and bd[t] < 0:
                        if t >= 56:
                            app((sq, t, 5))
                            app((sq, t, 2))
                        else:
                            app((sq, t, 0))
            else:
                t = sq - 8
                if t >= 0 and bd[t] == 0:
                    if t < 8:
                        app((sq, t, 5))
                        app((sq, t, 2))
                    else:
                        app((sq, t, 0))
                        if sq >= 48 and bd[sq - 16] == 0:
                            app((sq, sq - 16, 0))
                if f > 0:
                    t = sq - 9
                    if t >= 0 and bd[t] > 0:
                        if t < 8:
                            app((sq, t, 5))
                            app((sq, t, 2))
                        else:
                            app((sq, t, 0))
                if f < 7:
                    t = sq - 7
                    if t >= 0 and bd[t] > 0:
                        if t < 8:
                            app((sq, t, 5))
                            app((sq, t, 2))
                        else:
                            app((sq, t, 0))
        elif pt == 2:
            for t in KNIGHT[sq]:
                if bd[t] * side <= 0:
                    app((sq, t, 0))
        elif pt == 6:
            for t in KING_M[sq]:
                if bd[t] * side <= 0:
                    app((sq, t, 0))
        else:
            if pt == 4:
                dirs = R_DIRS
            elif pt == 3:
                dirs = B_DIRS
            else:
                dirs = Q_DIRS
            rays = RAYS[sq]
            for d in dirs:
                for t in rays[d]:
                    q = bd[t]
                    if q == 0:
                        app((sq, t, 0))
                    else:
                        if q * side < 0:
                            app((sq, t, 0))
                        break
    return moves


def gen_captures(side):
    bd = board
    moves = []
    app = moves.append
    for sq in range(64):
        p = bd[sq]
        if p * side <= 0:
            continue
        pt = p if p > 0 else -p
        if pt == 1:
            f = sq & 7
            if side == 1:
                t = sq + 8
                if 56 <= t < 64 and bd[t] == 0:
                    app((sq, t, 5))
                if f > 0:
                    t = sq + 7
                    if t < 64 and bd[t] < 0:
                        app((sq, t, 5 if t >= 56 else 0))
                if f < 7:
                    t = sq + 9
                    if t < 64 and bd[t] < 0:
                        app((sq, t, 5 if t >= 56 else 0))
            else:
                t = sq - 8
                if 0 <= t < 8 and bd[t] == 0:
                    app((sq, t, 5))
                if f > 0:
                    t = sq - 9
                    if t >= 0 and bd[t] > 0:
                        app((sq, t, 5 if t < 8 else 0))
                if f < 7:
                    t = sq - 7
                    if t >= 0 and bd[t] > 0:
                        app((sq, t, 5 if t < 8 else 0))
        elif pt == 2:
            for t in KNIGHT[sq]:
                if bd[t] * side < 0:
                    app((sq, t, 0))
        elif pt == 6:
            for t in KING_M[sq]:
                if bd[t] * side < 0:
                    app((sq, t, 0))
        else:
            if pt == 4:
                dirs = R_DIRS
            elif pt == 3:
                dirs = B_DIRS
            else:
                dirs = Q_DIRS
            rays = RAYS[sq]
            for d in dirs:
                for t in rays[d]:
                    q = bd[t]
                    if q:
                        if q * side < 0:
                            app((sq, t, 0))
                        break
    return moves


def make(m, side):
    global PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH
    frm, to, promo = m
    bd = board
    p = bd[frm]
    cap = bd[to]
    h = HASH ^ ZOB[frm][p + 6] ^ SIDE_KEY
    sc = PST_SCORE - PSTV[p + 6][frm]
    if cap:
        h ^= ZOB[to][cap + 6]
        sc -= PSTV[cap + 6][to]
        if cap == 1:
            PAWN_W -= 1
        elif cap == -1:
            PAWN_B -= 1
        elif cap > 0:
            NPM_W -= VAL[cap]
        else:
            NPM_B -= VAL[-cap]
    if promo:
        if side == 1:
            np_ = promo
            PAWN_W -= 1
            NPM_W += VAL[promo]
        else:
            np_ = -promo
            PAWN_B -= 1
            NPM_B += VAL[promo]
    else:
        np_ = p
        if p == 6:
            KSQ[1] = to
        elif p == -6:
            KSQ[-1] = to
    bd[to] = np_
    bd[frm] = 0
    HASH = h ^ ZOB[to][np_ + 6]
    PST_SCORE = sc + PSTV[np_ + 6][to]
    return cap


def unmake(m, cap, saved):
    global PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH
    frm, to, promo = m
    bd = board
    p = bd[to]
    if promo:
        p = 1 if p > 0 else -1
    elif p == 6:
        KSQ[1] = frm
    elif p == -6:
        KSQ[-1] = frm
    bd[frm] = p
    bd[to] = cap
    PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH = saved


def evaluate(side):
    if PAWN_W == 0 and PAWN_B == 0 and NPM_W <= 330 and NPM_B <= 330:
        return 0
    wk = KSQ[1]
    bk = KSQ[-1]
    if NPM_W + NPM_B <= 1600:
        s = PST_SCORE + KING_EG_W[wk] - KING_EG_B[bk]
        if NPM_B == 0 and PAWN_B == 0 and NPM_W >= 500:
            s += 4 * CMD[bk] + 4 * (14 - DIST[wk][bk])
        elif NPM_W == 0 and PAWN_W == 0 and NPM_B >= 500:
            s -= 4 * CMD[wk] + 4 * (14 - DIST[wk][bk])
    else:
        s = PST_SCORE + KING_MG_W[wk] - KING_MG_B[bk]
    return s if side == 1 else -s


def quiesce(alpha, beta, side, ply):
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.time() > DEADLINE:
        raise TimeUp()
    ksq = KSQ[side]
    in_check = attacked(ksq, -side)
    bd = board
    if in_check:
        if ply >= MAX_PLY:
            return evaluate(side)
        moves = gen_moves(side)
        scored = []
        for m in moves:
            cap = bd[m[1]]
            scored.append((VAL[cap if cap > 0 else -cap] if cap else 0, m))
        scored.sort(key=_key0, reverse=True)
        best = -INF
        for s, m in scored:
            saved = (PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH)
            cap = make(m, side)
            if attacked(KSQ[side], -side):
                unmake(m, cap, saved)
                continue
            score = -quiesce(-beta, -alpha, -side, ply + 1)
            unmake(m, cap, saved)
            if score > best:
                best = score
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break
        if best == -INF:
            return -(MATE - ply)
        return best
    stand = evaluate(side)
    if stand >= beta:
        return stand
    if ply >= MAX_PLY - 1:
        return stand
    if stand > alpha:
        alpha = stand
    moves = gen_captures(side)
    scored = []
    for m in moves:
        frm, to, promo = m
        cap = bd[to]
        if cap:
            a = bd[frm]
            s = VAL[cap if cap > 0 else -cap] * 16 - (a if a > 0 else -a)
        else:
            s = 0
        if promo:
            s += 1000
        scored.append((s, m))
    scored.sort(key=_key0, reverse=True)
    best = stand
    for s, m in scored:
        frm, to, promo = m
        cap0 = bd[to]
        if not promo and stand + VAL[cap0 if cap0 > 0 else -cap0] + 200 <= alpha:
            continue
        saved = (PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH)
        p = bd[frm]
        cap = make(m, side)
        if p == 6 or p == -6 or ALIGNED[ksq][frm]:
            if attacked(KSQ[side], -side):
                unmake(m, cap, saved)
                continue
        score = -quiesce(-beta, -alpha, -side, ply + 1)
        unmake(m, cap, saved)
        if score > best:
            best = score
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    break
    return best


def search(depth, alpha, beta, side, ply, can_null):
    global NODES, HASH
    NODES += 1
    if (NODES & 511) == 0 and time.time() > DEADLINE:
        raise TimeUp()
    h = HASH
    if h in SEEN:
        return 0
    i = ply - 4
    while i >= 0:
        if PATH[i] == h:
            return 0
        i -= 2
    if ply >= MAX_PLY:
        return evaluate(side)
    in_check = attacked(KSQ[side], -side)
    if in_check and ply <= 2 * ROOT_DEPTH:
        depth += 1
    if depth <= 0:
        return quiesce(alpha, beta, side, ply)
    tt_move = None
    e = TT.get(h)
    if e is not None:
        tt_move = e[3]
        if e[0] >= depth:
            es = e[1]
            if es > MATE - 2000:
                es -= ply
            elif es < -MATE + 2000:
                es += ply
            ef = e[2]
            if ef == 0:
                return es
            if ef == 1:
                if es > alpha:
                    alpha = es
            else:
                if es < beta:
                    beta = es
            if alpha >= beta:
                return es
    PATH[ply] = h
    if can_null and depth >= 3 and not in_check and beta < MATE - 2000 and \
            (NPM_W if side == 1 else NPM_B) > 0:
        HASH = h ^ SIDE_KEY
        score = -search(depth - 3, -beta, -beta + 1, -side, ply + 1, False)
        HASH = h
        if score >= beta:
            return beta
    moves = gen_moves(side)
    hist = HIST[0] if side == 1 else HIST[1]
    k1, k2 = KILLERS[ply]
    bd = board
    scored = []
    for m in moves:
        frm, to, promo = m
        if m == tt_move:
            s = 100000000
        else:
            cap = bd[to]
            if cap:
                a = bd[frm]
                s = 1000000 + VAL[cap if cap > 0 else -cap] * 16 - (a if a > 0 else -a)
                if promo:
                    s += VAL[promo]
            elif promo:
                s = 900000 + VAL[promo]
            elif m == k1:
                s = 850000
            elif m == k2:
                s = 840000
            else:
                s = hist[frm * 64 + to]
        scored.append((s, m))
    scored.sort(key=_key0, reverse=True)
    best = -INF
    best_move = None
    legal = 0
    orig_alpha = alpha
    ksq = KSQ[side]
    for s, m in scored:
        frm, to, promo = m
        saved = (PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH)
        p = bd[frm]
        cap = make(m, side)
        if in_check or p == 6 or p == -6 or ALIGNED[ksq][frm]:
            if attacked(KSQ[side], -side):
                unmake(m, cap, saved)
                continue
        legal += 1
        if legal > 3 and depth >= 3 and not in_check and cap == 0 and promo == 0 and s < 840000:
            score = -search(depth - 2, -alpha - 1, -alpha, -side, ply + 1, True)
            if score > alpha:
                score = -search(depth - 1, -beta, -alpha, -side, ply + 1, True)
        else:
            score = -search(depth - 1, -beta, -alpha, -side, ply + 1, True)
        unmake(m, cap, saved)
        if score > best:
            best = score
            best_move = m
            if score > alpha:
                alpha = score
                if alpha >= beta:
                    if cap == 0 and promo == 0:
                        if k1 != m:
                            KILLERS[ply][1] = k1
                            KILLERS[ply][0] = m
                        hist[frm * 64 + to] += depth * depth
                    break
    if legal == 0:
        return -(MATE - ply) if in_check else 0
    if best >= beta:
        flag = 1
    elif best <= orig_alpha:
        flag = 2
    else:
        flag = 0
    st = best
    if st > MATE - 2000:
        st += ply
    elif st < -MATE + 2000:
        st -= ply
    TT[h] = (depth, st, flag, best_move)
    return best


def root_search(depth, root_moves, side):
    global ROOT_BEST, ROOT_COMPLETED
    ROOT_BEST = None
    ROOT_COMPLETED = 0
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = root_moves[0]
    scores = {}
    PATH[0] = HASH
    for m in root_moves:
        saved = (PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH)
        cap = make(m, side)
        score = -search(depth - 1, -beta, -alpha, -side, 1, True)
        unmake(m, cap, saved)
        scores[m] = score
        ROOT_COMPLETED += 1
        if score > best_score:
            best_score = score
            best_move = m
            ROOT_BEST = m
            if score > alpha:
                alpha = score
    return best_move, best_score, scores


def mstr(m):
    frm, to, promo = m
    s = "abcdefgh"[frm & 7] + str((frm >> 3) + 1) + "abcdefgh"[to & 7] + str((to >> 3) + 1)
    if promo:
        s += PROMO_CH.get(promo, 'q')
    return s


def policy(pieces, to_play):
    global DEADLINE, ROOT_DEPTH, LAST_COUNT, NODES
    start = time.time()
    DEADLINE = start + TIME_BUDGET
    side = 1 if str(to_play).lower().startswith('w') else -1
    fallback = None
    try:
        setup(pieces, side)
        pseudo = gen_moves(side)
        if not pseudo:
            return 'a1a1'
        if KSQ[side] < 0:
            return mstr(pseudo[0])
        legal = []
        for m in pseudo:
            saved = (PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH)
            cap = make(m, side)
            ok = not attacked(KSQ[side], -side)
            unmake(m, cap, saved)
            if ok:
                legal.append(m)
        if not legal:
            return mstr(pseudo[0])
        bd = board
        legal.sort(key=lambda m: -(VAL[abs(bd[m[1]])] + (VAL[m[2]] if m[2] else 0)))
        fallback = mstr(legal[0])
        count = len(pieces)
        if count != LAST_COUNT:
            SEEN.clear()
            LAST_COUNT = count
        root_hash = HASH
        SEEN[root_hash] = SEEN.get(root_hash, 0) + 1
        best = legal[0]
        if len(legal) > 1:
            TT.clear()
            for k in KILLERS:
                k[0] = None
                k[1] = None
            HIST[0] = [0] * 4096
            HIST[1] = [0] * 4096
            NODES = 0
            root_moves = list(legal)
            for depth in range(1, 60):
                ROOT_DEPTH = depth
                try:
                    bm, bs, scores = root_search(depth, root_moves, side)
                except TimeUp:
                    if ROOT_COMPLETED >= 1 and ROOT_BEST is not None:
                        best = ROOT_BEST
                    break
                best = bm
                root_moves.sort(key=lambda m: -scores[m])
                if abs(bs) >= MATE - 2000:
                    break
                if time.time() > DEADLINE:
                    break
        # fresh state, verify and record
        setup(pieces, side)
        saved = (PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH)
        cap = make(best, side)
        ok = not attacked(KSQ[side], -side)
        if ok:
            SEEN[HASH] = SEEN.get(HASH, 0) + 1
        unmake(best, cap, saved)
        if not ok:
            return fallback
        return mstr(best)
    except Exception:
        if fallback:
            return fallback
        try:
            setup(pieces, side)
            pseudo = gen_moves(side)
            for m in pseudo:
                saved = (PST_SCORE, NPM_W, NPM_B, PAWN_W, PAWN_B, HASH)
                cap = make(m, side)
                ok = KSQ[side] < 0 or not attacked(KSQ[side], -side)
                unmake(m, cap, saved)
                if ok:
                    return mstr(m)
            if pseudo:
                return mstr(pseudo[0])
        except Exception:
            pass
        return 'a1a1'
