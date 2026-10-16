
import time
import numpy as np


class _Timeout(Exception):
    pass


_tmono = time.monotonic

FULL = (1 << 64) - 1
NOT_A = FULL ^ 0x0101010101010101   # squares not on file a
NOT_H = FULL ^ 0x8080808080808080   # squares not on file h

if hasattr(int, "bit_count"):
    def pc(x):
        return x.bit_count()
else:
    def pc(x):
        return bin(x).count("1")

# positional weights (corners handled dynamically)
EVALW = [
      0,  -6,   8,   5,   5,   8,  -6,   0,
     -6, -14,  -4,  -3,  -3,  -4, -14,  -6,
      8,  -4,   5,   2,   2,   5,  -4,   8,
      5,  -3,   2,   1,   1,   2,  -3,   5,
      5,  -3,   2,   1,   1,   2,  -3,   5,
      8,  -4,   5,   2,   2,   5,  -4,   8,
     -6, -14,  -4,  -3,  -3,  -4, -14,  -6,
      0,  -6,   8,   5,   5,   8,  -6,   0,
]

# static move-ordering weights
GOOD = [
     40, -25,  10,   6,   6,  10, -25,  40,
    -25, -45,  -5,  -3,  -3,  -5, -45, -25,
     10,  -5,   8,   3,   3,   8,  -5,  10,
      6,  -3,   3,   1,   1,   3,  -3,   6,
      6,  -3,   3,   1,   1,   3,  -3,   6,
     10,  -5,   8,   3,   3,   8,  -5,  10,
    -25, -45,  -5,  -3,  -3,  -5, -45, -25,
     40, -25,  10,   6,   6,  10, -25,  40,
]

# per-row byte lookup tables for the positional score
_tabs = []
for _r in range(8):
    _w = EVALW[8 * _r:8 * _r + 8]
    _t = [0] * 256
    for _v in range(256):
        _s = 0
        for _c in range(8):
            if (_v >> _c) & 1:
                _s += _w[_c]
        _t[_v] = _s
    _tabs.append(_t)
T0, T1, T2, T3, T4, T5, T6, T7 = _tabs

# (corner bit, X-square bit, C-squares mask)
CORNER_DATA = []
for _k in (0, 7, 56, 63):
    _r = _k >> 3
    _c = _k & 7
    _dr = 1 if _r == 0 else -1
    _dc = 1 if _c == 0 else -1
    _xb = 1 << ((_r + _dr) * 8 + (_c + _dc))
    _cm = (1 << (_r * 8 + _c + _dc)) | (1 << ((_r + _dr) * 8 + _c))
    CORNER_DATA.append((1 << _k, _xb, _cm))


def pos_score(P, O):
    return (T0[P & 255] - T0[O & 255]
            + T1[(P >> 8) & 255] - T1[(O >> 8) & 255]
            + T2[(P >> 16) & 255] - T2[(O >> 16) & 255]
            + T3[(P >> 24) & 255] - T3[(O >> 24) & 255]
            + T4[(P >> 32) & 255] - T4[(O >> 32) & 255]
            + T5[(P >> 40) & 255] - T5[(O >> 40) & 255]
            + T6[(P >> 48) & 255] - T6[(O >> 48) & 255]
            + T7[(P >> 56) & 255] - T7[(O >> 56) & 255])


def legal_moves(P, O):
    empty = ~(P | O) & FULL
    moves = 0
    # East
    t = ((P << 1) & NOT_A) & O
    if t:
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        moves |= ((t << 1) & NOT_A) & empty
    # West
    t = ((P >> 1) & NOT_H) & O
    if t:
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        moves |= ((t >> 1) & NOT_H) & empty
    # North
    t = (P >> 8) & O
    if t:
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        moves |= (t >> 8) & empty
    # South
    t = (P << 8) & O
    if t:
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        moves |= (t << 8) & empty
    # North-East
    t = ((P >> 7) & NOT_A) & O
    if t:
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        moves |= ((t >> 7) & NOT_A) & empty
    # North-West
    t = ((P >> 9) & NOT_H) & O
    if t:
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        moves |= ((t >> 9) & NOT_H) & empty
    # South-East
    t = ((P << 9) & NOT_A) & O
    if t:
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        moves |= ((t << 9) & NOT_A) & empty
    # South-West
    t = ((P << 7) & NOT_H) & O
    if t:
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        moves |= ((t << 7) & NOT_H) & empty
    return moves


def flips(P, O, m):
    f = 0
    # East
    t = ((m << 1) & NOT_A) & O
    if t:
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        t |= ((t << 1) & NOT_A) & O
        if ((t << 1) & NOT_A) & P:
            f |= t
    # West
    t = ((m >> 1) & NOT_H) & O
    if t:
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        t |= ((t >> 1) & NOT_H) & O
        if ((t >> 1) & NOT_H) & P:
            f |= t
    # North
    t = (m >> 8) & O
    if t:
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        if (t >> 8) & P:
            f |= t
    # South
    t = (m << 8) & O
    if t:
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        if (t << 8) & P:
            f |= t
    # North-East
    t = ((m >> 7) & NOT_A) & O
    if t:
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        t |= ((t >> 7) & NOT_A) & O
        if ((t >> 7) & NOT_A) & P:
            f |= t
    # North-West
    t = ((m >> 9) & NOT_H) & O
    if t:
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        t |= ((t >> 9) & NOT_H) & O
        if ((t >> 9) & NOT_H) & P:
            f |= t
    # South-East
    t = ((m << 9) & NOT_A) & O
    if t:
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        t |= ((t << 9) & NOT_A) & O
        if ((t << 9) & NOT_A) & P:
            f |= t
    # South-West
    t = ((m << 7) & NOT_H) & O
    if t:
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        t |= ((t << 7) & NOT_H) & O
        if ((t << 7) & NOT_H) & P:
            f |= t
    return f


def evaluate(P, O, mymoves):
    pd = pc(P)
    od = pc(O)
    e = 64 - pd - od
    d = pd - od
    if e <= 14:
        return d * 200
    m = pc(mymoves) - pc(legal_moves(O, P))
    cor = 0
    for cb, xb, cm in CORNER_DATA:
        if P & cb:
            cor += 50
        elif O & cb:
            cor -= 50
        else:
            if P & xb:
                cor -= 30
            elif O & xb:
                cor += 30
            if P & cm:
                cor -= 12 * pc(P & cm)
            if O & cm:
                cor += 12 * pc(O & cm)
    return pos_score(P, O) + cor + 8 * m + d * ((64 - e) >> 2)


INF = 1 << 30
EXACT, LOWER, UPPER = 0, 1, 2
TT = {}
HIST = [0] * 64
NODES = 0
DEADLINE = 0.0


def negamax(P, O, depth, alpha, beta, passed):
    global NODES
    NODES += 1
    if (NODES & 255) == 0 and _tmono() >= DEADLINE:
        raise _Timeout()
    key = (P, O)
    tte = TT.get(key)
    tmove = 0
    if tte is not None:
        td, fl, ts, tmove = tte
        if td >= depth:
            if fl == EXACT:
                return ts
            if fl == LOWER and ts >= beta:
                return ts
            if fl == UPPER and ts <= alpha:
                return ts
    moves = legal_moves(P, O)
    if not moves:
        if passed:
            return (pc(P) - pc(O)) * 100000   # game over: exact result
        return -negamax(O, P, depth, -beta, -alpha, 1)  # forced pass
    if depth <= 0:
        v = evaluate(P, O, moves)
        if tte is None:
            TT[key] = (0, EXACT, v, 0)
        return v
    lst = []
    mm = moves
    while mm:
        b = mm & -mm
        mm ^= b
        s = b.bit_length() - 1
        g = (HIST[s] << 4) + GOOD[s]
        if b == tmove:
            g += 1 << 30
        lst.append((-g, b))
    lst.sort()
    best = -INF
    bbest = 0
    a0 = alpha
    first = True
    for _g, b in lst:
        f = flips(P, O, b)
        nP = O ^ f
        nO = P | b | f
        if first:
            sc = -negamax(nP, nO, depth - 1, -beta, -alpha, 0)
            first = False
        else:
            sc = -negamax(nP, nO, depth - 1, -alpha - 1, -alpha, 0)
            if alpha < sc < beta:
                sc = -negamax(nP, nO, depth - 1, -beta, -alpha, 0)
        if sc > best:
            best = sc
            bbest = b
            if sc > alpha:
                alpha = sc
                if alpha >= beta:
                    HIST[b.bit_length() - 1] += depth * depth
                    break
    if best <= a0:
        fl = UPPER
    elif best >= beta:
        fl = LOWER
    else:
        fl = EXACT
    TT[key] = (depth, fl, best, bbest)
    return best


def _to_str(b):
    s = b.bit_length() - 1
    return "abcdefgh"[s & 7] + str((s >> 3) + 1)


def _ordkey(b):
    return -GOOD[b.bit_length() - 1]


def policy(you, opponent):
    global NODES, DEADLINE
    t0 = _tmono()
    yl = np.asarray(you, dtype=np.uint8).tolist()
    ol = np.asarray(opponent, dtype=np.uint8).tolist()
    P = 0
    O = 0
    for r in range(8):
        yrow = yl[r]
        orow = ol[r]
        base = r * 8
        for c in range(8):
            if yrow[c]:
                P |= 1 << (base + c)
            elif orow[c]:
                O |= 1 << (base + c)
    moves = legal_moves(P, O)
    if not moves:
        return "pass"
    root = []
    m = moves
    while m:
        b = m & -m
        m ^= b
        root.append(b)
    if len(root) == 1:
        return _to_str(root[0])
    legal = set(root)
    TT.clear()
    for i in range(64):
        HIST[i] = 0
    NODES = 0
    DEADLINE = t0 + 0.85
    root.sort(key=_ordkey)
    best_move = root[0]
    empties = 64 - pc(P) - pc(O)
    try:
        for d in range(2, empties + 1):
            alpha = -INF
            best = -INF
            bm = root[0]
            first = True
            for b in root:
                f = flips(P, O, b)
                nP = O ^ f
                nO = P | b | f
                if first:
                    sc = -negamax(nP, nO, d - 1, -INF, -alpha, 0)
                    first = False
                else:
                    sc = -negamax(nP, nO, d - 1, -alpha - 1, -alpha, 0)
                    if sc > alpha:
                        sc = -negamax(nP, nO, d - 1, -INF, -alpha, 0)
                if sc > best:
                    best = sc
                    bm = b
                    if sc > alpha:
                        alpha = sc
            best_move = bm
            root.remove(bm)
            root.insert(0, bm)
            if d >= empties:
                break  # full-depth search completed: exact result
    except Exception:
        pass
    if best_move not in legal:
        best_move = root[0]
    return _to_str(best_move)
