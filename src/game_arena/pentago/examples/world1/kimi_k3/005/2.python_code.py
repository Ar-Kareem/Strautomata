
import time

# ============================ precomputed tables ============================
# Padded bitboard: cell (r, c) (0-indexed) <-> bit r*7 + c.  The 7th column is
# padding so horizontal/diagonal shift tests never wrap across rows.

def _idx(r, c):
    return r * 7 + c

BOARDMASK = 0
for _r in range(6):
    for _c in range(6):
        BOARDMASK |= 1 << _idx(_r, _c)

QBASE = (0, 3, 21, 24)          # padded bit index of top-left cell of quadrants 0..3

QMASK = []
for _b in QBASE:
    _m = 0
    for _i in range(3):
        for _j in range(3):
            _m |= 1 << (_b + 7 * _i + _j)
    QMASK.append(_m)
QMASK = tuple(QMASK)

def _build_rot(cw):
    # sub-pattern: bit 3*i+j = local cell (i, j) of the 3x3 quadrant
    tbl = []
    for p in range(512):
        q = 0
        for i in range(3):
            for j in range(3):
                if (p >> (3 * i + j)) & 1:
                    ni, nj = (j, 2 - i) if cw else (2 - j, i)
                    q |= 1 << (3 * ni + nj)
        tbl.append(q)
    return tuple(tbl)

ROTCW = _build_rot(True)        # 'R' = 90 deg clockwise
ROTCCW = _build_rot(False)      # 'L' = 90 deg anticlockwise

# all 32 length-5 straight lines
LINES = []
for _r in range(6):
    for _c0 in (0, 1):
        _m = 0
        for _k in range(5):
            _m |= 1 << _idx(_r, _c0 + _k)
        LINES.append(_m)
for _c in range(6):
    for _r0 in (0, 1):
        _m = 0
        for _k in range(5):
            _m |= 1 << _idx(_r0 + _k, _c)
        LINES.append(_m)
for _r0 in (0, 1):
    for _c0 in (0, 1):
        _m = 0
        for _k in range(5):
            _m |= 1 << _idx(_r0 + _k, _c0 + _k)
        LINES.append(_m)
for _r0 in (0, 1):
    for _c0 in (4, 5):
        _m = 0
        for _k in range(5):
            _m |= 1 << _idx(_r0 + _k, _c0 - _k)
        LINES.append(_m)
LINES = tuple(LINES)

# quadrant centres (never moved by rotations) and board centre
C4MASK = (1 << _idx(1, 1)) | (1 << _idx(1, 4)) | (1 << _idx(4, 1)) | (1 << _idx(4, 4))
M4MASK = (1 << _idx(2, 2)) | (1 << _idx(2, 3)) | (1 << _idx(3, 2)) | (1 << _idx(3, 3))

# static cell values for move ordering
_linecnt = [0] * 49
for _m in LINES:
    _mm = _m
    while _mm:
        _b = _mm & -_mm
        _linecnt[_b.bit_length() - 1] += 1
        _mm ^= _b

CELLVAL = [0] * 49
for _r in range(6):
    for _c in range(6):
        _i = _idx(_r, _c)
        _v = 2 * _linecnt[_i]
        if (C4MASK >> _i) & 1:
            _v += 5
        if (M4MASK >> _i) & 1:
            _v += 2
        CELLVAL[_i] = _v
CELL_ORDER = [i for i in sorted(range(49), key=lambda i: -CELLVAL[i])
              if (BOARDMASK >> i) & 1]

if hasattr(int, "bit_count"):
    _pc = int.bit_count
else:
    def _pc(x):
        return bin(x).count("1")

W = (0, 2, 10, 60, 400, 1 << 22)     # line pattern weights (by marble count)
INF = 1 << 40
WIN = 1 << 30

class _TO(Exception):
    pass

TT = {}
nodes = 0
deadline = 0.0

# ============================ primitives ============================

def has5(b):
    if b & (b >> 1) & (b >> 2) & (b >> 3) & (b >> 4):
        return True
    if b & (b >> 7) & (b >> 14) & (b >> 21) & (b >> 28):
        return True
    if b & (b >> 8) & (b >> 16) & (b >> 24) & (b >> 32):
        return True
    if b & (b >> 6) & (b >> 12) & (b >> 18) & (b >> 24):
        return True
    return False

def _dil(b):
    # Chebyshev distance-1 dilation (8 neighbourhood), clipped to the board
    return (b | (b << 1) | (b >> 1) | (b << 6) | (b >> 6)
            | (b << 7) | (b >> 7) | (b << 8) | (b >> 8)) & BOARDMASK

def evaluate(me, opp, _L=LINES, _W=W, _p=_pc, _C=C4MASK, _M=M4MASK):
    s = 0
    for m in _L:
        pm = _p(me & m)
        if pm:
            if not (opp & m):        # live line for me
                s += _W[pm]
        else:
            po = _p(opp & m)
            if po:                   # live line for opponent
                s -= _W[po]
    s += 3 * _p(me & _C) + _p(me & _M)
    s -= 3 * _p(opp & _C) + _p(opp & _M)
    return s

# outcome codes: 0 = nothing, 1 = side to move wins, 2 = draw, 3 = side to move loses
def gen_moves(me, opp, cells):
    res = []
    seen = set()
    app = res.append
    sadd = seen.add
    h5 = has5
    cw = ROTCW
    ccw = ROTCCW
    BM = BOARDMASK
    for cell in cells:
        bme = me | (1 << cell)
        for qi in range(4):
            B = QBASE[qi]
            B7 = B + 7
            B14 = B + 14
            nQM = ~QMASK[qi]
            so = ((opp >> B) & 7) | (((opp >> B7) & 7) << 3) | (((opp >> B14) & 7) << 6)
            sm = ((bme >> B) & 7) | (((bme >> B7) & 7) << 3) | (((bme >> B14) & 7) << 6)
            roL = ccw[so]; roR = cw[so]
            rmL = ccw[sm]; rmR = cw[sm]
            for rm, ro, dch in ((rmL, roL, 'L'), (rmR, roR, 'R')):
                if rm == sm:
                    me2 = bme
                else:
                    me2 = (bme & nQM) | ((rm & 7) << B) | (((rm >> 3) & 7) << B7) | (((rm >> 6) & 7) << B14)
                if ro == so:
                    opp2 = opp
                    ch = False
                else:
                    opp2 = (opp & nQM) | ((ro & 7) << B) | (((ro >> 3) & 7) << B7) | (((ro >> 6) & 7) << B14)
                    ch = True
                key = (me2, opp2)
                if key in seen:
                    continue
                sadd(key)
                if h5(me2):
                    oc = 2 if (ch and h5(opp2)) else 1   # both -> draw
                elif ch and h5(opp2):
                    oc = 3                               # my rotation gave opponent 5
                elif (me2 | opp2) == BM:
                    oc = 2                               # board full -> draw
                else:
                    oc = 0
                app((me2, opp2, oc, (cell, qi, dch)))
    return res

# ============================ search ============================

def search(me, opp, depth, alpha, beta, ply):
    global nodes
    key = (me, opp)
    a0 = alpha
    b0 = beta
    ttm = None
    ent = TT.get(key)
    if ent is not None:
        ed, ev, ef, emv = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1:
                if ev > alpha:
                    alpha = ev
            elif ev < beta:
                beta = ev
            if alpha >= beta:
                return ev
        ttm = emv
    occ = me | opp
    empt = BOARDMASK & ~occ
    if depth <= 1:
        # distance-3 dilation: provably contains every immediately winning placement
        cm = empt & _dil(_dil(_dil(occ)))
        need = 12
    else:
        cm = empt & _dil(_dil(occ))
        need = 10
    cells = [c for c in CELL_ORDER if (cm >> c) & 1] if cm else []
    if len(cells) < need:
        cells = [c for c in CELL_ORDER if (empt >> c) & 1]
    moves = gen_moves(me, opp, cells)
    if ttm is not None:
        for i in range(len(moves)):
            if moves[i][3] == ttm:
                moves.insert(0, moves.pop(i))
                break
    best = -INF
    bestm = moves[0][3]
    nwin = WIN - ply
    nd1 = depth - 1
    for me2, opp2, oc, mv in moves:
        nodes += 1
        if (nodes & 63) == 0 and time.perf_counter() > deadline:
            raise _TO
        if oc == 1:
            sc = nwin
        elif oc == 2:
            sc = 0
        elif oc == 3:
            sc = -nwin
        elif depth <= 1:
            sc = -evaluate(opp2, me2)
        else:
            sc = -search(opp2, me2, nd1, -beta, -alpha, ply + 1)
        if sc > best:
            best = sc
            bestm = mv
            if sc > alpha:
                alpha = sc
                if alpha >= beta:
                    break
    if best <= a0:
        TT[key] = (depth, best, 2, bestm)
    elif best >= b0:
        TT[key] = (depth, best, 1, bestm)
    else:
        TT[key] = (depth, best, 0, bestm)
    return best

def root_search(moves, depth, partial):
    global nodes
    best = -INF
    bestmv = moves[0][3]
    alpha = -INF
    cnt = 0
    scmap = partial[3]
    for me2, opp2, oc, mv in moves:
        nodes += 1
        if (nodes & 63) == 0 and time.perf_counter() > deadline:
            raise _TO
        if oc == 1:
            sc = WIN
        elif oc == 2:
            sc = 0
        elif oc == 3:
            sc = -WIN
        elif depth <= 1:
            sc = -evaluate(opp2, me2)
        else:
            sc = -search(opp2, me2, depth - 1, -INF, -alpha, 1)
        if sc > best:
            best = sc
            bestmv = mv
        if sc > alpha:
            alpha = sc
        cnt += 1
        partial[0] = best
        partial[1] = bestmv
        partial[2] = cnt
        scmap[mv] = sc
    return best, bestmv

# ============================ policy ============================

def _policy(you, opponent):
    global TT, nodes, deadline
    t0 = time.perf_counter()
    deadline = t0 + 0.85
    TT = {}
    nodes = 0

    me = 0
    opp = 0
    for r in range(6):
        yr = you[r]
        orw = opponent[r]
        b = r * 7
        for c in range(6):
            if yr[c]:
                me |= 1 << (b + c)
            elif orw[c]:
                opp |= 1 << (b + c)

    empt = BOARDMASK & ~(me | opp)
    cells = [c for c in CELL_ORDER if (empt >> c) & 1]
    moves = gen_moves(me, opp, cells)

    def actstr(mv):
        cell, qi, dch = mv
        return "%d,%d,%d,%s" % (cell // 7 + 1, cell % 7 + 1, qi, dch)

    if not moves:
        return actstr((cells[0], 0, 'L'))
    if len(moves) == 1:
        return actstr(moves[0][3])

    # immediate win?
    for me2, opp2, oc, mv in moves:
        if oc == 1:
            return actstr(mv)

    bestmv = moves[0][3]
    partial = [-INF, bestmv, 0, {}]
    depth = 1
    while depth <= 16:
        partial[3] = {}
        try:
            val, mv = root_search(moves, depth, partial)
        except _TO:
            # adopt the best fully evaluated move of the aborted iteration
            # (the previous best move is always evaluated first)
            if partial[2] > 0:
                bestmv = partial[1]
            break
        bestmv = mv
        # order root moves by this iteration's scores for the next one
        scmap = partial[3]
        moves.sort(key=lambda m: -scmap.get(m[3], -INF))
        if val >= WIN - 60:
            break
        depth += 1
        if time.perf_counter() > deadline - 0.05:
            break
    return actstr(bestmv)

def policy(you, opponent):
    try:
        return _policy(you, opponent)
    except Exception:
        # last-resort: any legal move (first empty cell + rotate quadrant 0)
        try:
            for r in range(6):
                for c in range(6):
                    if not you[r][c] and not opponent[r][c]:
                        return "%d,%d,0,L" % (r + 1, c + 1)
        except Exception:
            pass
        return "1,1,0,L"
