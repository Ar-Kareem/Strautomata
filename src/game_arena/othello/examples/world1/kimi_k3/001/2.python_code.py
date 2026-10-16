
import time
import numpy as np

FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE   # everything except file a (col 0)
NOT_H = 0x7F7F7F7F7F7F7F7F   # everything except file h (col 7)

WIN = 100000
INF = 1 << 30

# Positional weights, index = row*8 + col  (row 0 = rank 1, col 0 = file a)
W = (
    120, -20,  20,   5,   5,  20, -20, 120,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
     20,  -5,  15,   3,   3,  15,  -5,  20,
      5,  -5,   3,   3,   3,   3,  -5,   5,
      5,  -5,   3,   3,   3,   3,  -5,   5,
     20,  -5,  15,   3,   3,  15,  -5,  20,
    -20, -40,  -5,  -5,  -5,  -5, -40, -20,
    120, -20,  20,   5,   5,  20, -20, 120,
)

# Corners with adjacent squares and extra penalties when corner is empty
_CORNERS = (
    (0,  ((1, 12), (8, 12), (9, 20))),
    (7,  ((6, 12), (14, 20), (15, 12))),
    (56, ((48, 12), (49, 20), (57, 12))),
    (63, ((54, 20), (55, 12), (62, 12))),
)


def _build_byte_w():
    tbl = []
    for i in range(8):
        base = 8 * i
        row = [0] * 256
        for v in range(1, 256):
            lsb = v & -v
            row[v] = row[v ^ lsb] + W[base + lsb.bit_length() - 1]
        tbl.append(row)
    return tbl


BYTE_W = _build_byte_w()

if hasattr(int, "bit_count"):
    def _pop(x):
        return x.bit_count()
else:
    _POPT = [bin(i).count("1") for i in range(256)]

    def _pop(x):
        c = 0
        while x:
            c += _POPT[x & 255]
            x >>= 8
        return c


def _legal(me, opp):
    """Bitboard of all legal moves for side `me`."""
    empty = FULL ^ (me | opp)
    m = 0
    # East (+1)
    x = ((me & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    x |= ((x & NOT_H) << 1) & opp
    m |= ((x & NOT_H) << 1) & empty
    # West (-1)
    x = ((me & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    x |= ((x & NOT_A) >> 1) & opp
    m |= ((x & NOT_A) >> 1) & empty
    # South (+8)
    x = (me << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    x |= (x << 8) & opp
    m |= (x << 8) & empty
    # North (-8)
    x = (me >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    x |= (x >> 8) & opp
    m |= (x >> 8) & empty
    # South-East (+9)
    x = ((me & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    x |= ((x & NOT_H) << 9) & opp
    m |= ((x & NOT_H) << 9) & empty
    # South-West (+7)
    x = ((me & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    x |= ((x & NOT_A) << 7) & opp
    m |= ((x & NOT_A) << 7) & empty
    # North-East (-7)
    x = ((me & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    x |= ((x & NOT_H) >> 7) & opp
    m |= ((x & NOT_H) >> 7) & empty
    # North-West (-9)
    x = ((me & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    x |= ((x & NOT_A) >> 9) & opp
    m |= ((x & NOT_A) >> 9) & empty
    return m


_DIRS = (
    (1, NOT_H, 1),
    (1, NOT_A, 0),
    (8, FULL, 1),
    (8, FULL, 0),
    (9, NOT_H, 1),
    (7, NOT_A, 1),
    (7, NOT_H, 0),
    (9, NOT_A, 0),
)


def _flips(move, me, opp):
    """Bitboard of opponent discs flipped by placing `move` (single bit)."""
    f = 0
    for s, mask, up in _DIRS:
        if up:
            x = (move & mask) << s
            run = 0
            while x & opp:
                run |= x
                x = (x & mask) << s
        else:
            x = (move & mask) >> s
            run = 0
            while x & opp:
                run |= x
                x = (x & mask) >> s
        if x & me:
            f |= run
    return f


def _eval(me, opp):
    """Heuristic score from side-to-move (`me`) perspective."""
    mm = _legal(me, opp)
    om = _legal(opp, me)
    if mm == 0 and om == 0:
        return (_pop(me) - _pop(opp)) * WIN
    s = 0
    for i in range(8):
        t = BYTE_W[i]
        sh = 8 * i
        s += t[(me >> sh) & 255] - t[(opp >> sh) & 255]
    s += 10 * (_pop(mm) - _pop(om))
    occ = me | opp
    for c, adjs in _CORNERS:
        if not (occ >> c) & 1:
            for a, pen in adjs:
                if (me >> a) & 1:
                    s -= pen
                elif (opp >> a) & 1:
                    s += pen
    return s


class _Timeout(Exception):
    pass


TT = {}
_nodes = 0


def _search(me, opp, depth, alpha, beta, deadline):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.perf_counter() > deadline:
        raise _Timeout
    alpha0 = alpha
    beta0 = beta
    key = (me << 64) | opp
    ent = TT.get(key)
    tt_bit = 0
    if ent is not None:
        ed, ev, ef, eb = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1 and ev <= alpha:
                return ev
            if ef == 2 and ev >= beta:
                return ev
        tt_bit = eb
    if depth <= 0:
        return _eval(me, opp)
    mv = _legal(me, opp)
    if mv == 0:
        if _legal(opp, me) == 0:
            return (_pop(me) - _pop(opp)) * WIN
        return -_search(opp, me, depth, -beta, -alpha, deadline)
    moves = []
    m = mv
    while m:
        b = m & -m
        moves.append((W[b.bit_length() - 1], b))
        m ^= b
    moves.sort(reverse=True)
    if tt_bit:
        for i in range(len(moves)):
            if moves[i][1] == tt_bit:
                if i:
                    moves.insert(0, moves.pop(i))
                break
    best = -INF
    best_bit = moves[0][1]
    a = alpha
    first = True
    for _, b in moves:
        f = _flips(b, me, opp)
        nme = opp ^ f
        nopp = me | b | f
        if first:
            v = -_search(nme, nopp, depth - 1, -beta, -a, deadline)
            first = False
        else:
            v = -_search(nme, nopp, depth - 1, -a - 1, -a, deadline)
            if a < v < beta:
                v = -_search(nme, nopp, depth - 1, -beta, -a, deadline)
        if v > best:
            best = v
            best_bit = b
            if v > a:
                a = v
                if a >= beta:
                    break
    if best <= alpha0:
        flag = 1
    elif best >= beta0:
        flag = 2
    else:
        flag = 0
    old = TT.get(key)
    if old is None or depth >= old[0]:
        TT[key] = (depth, best, flag, best_bit)
    return best


def _root(me, opp, depth, deadline, moves):
    best = -INF
    best_bit = moves[0][1]
    a = -INF
    beta = INF
    first = True
    for i in range(len(moves)):
        b = moves[i][1]
        f = _flips(b, me, opp)
        nme = opp ^ f
        nopp = me | b | f
        if first:
            v = -_search(nme, nopp, depth - 1, -beta, -a, deadline)
            first = False
        else:
            v = -_search(nme, nopp, depth - 1, -a - 1, -a, deadline)
            if a < v:
                v = -_search(nme, nopp, depth - 1, -beta, -a, deadline)
        if v > best:
            best = v
            best_bit = b
            if v > a:
                a = v
    for i in range(len(moves)):
        if moves[i][1] == best_bit:
            if i:
                moves.insert(0, moves.pop(i))
            break
    return best, best_bit


def _to_bits(arr):
    b = 0
    bit = 1
    for v in np.asarray(arr).reshape(-1):
        if v:
            b |= bit
        bit <<= 1
    return b


def _sq_name(sq):
    return chr(97 + (sq & 7)) + str((sq >> 3) + 1)


def policy(you, opponent):
    global _nodes
    me = _to_bits(you)
    opp = _to_bits(opponent)
    mv = _legal(me, opp)
    if mv == 0:
        return "pass"
    if mv & (mv - 1) == 0:
        return _sq_name(mv.bit_length() - 1)
    fallback = _sq_name((mv & -mv).bit_length() - 1)
    try:
        if len(TT) > 500000:
            TT.clear()
        _nodes = 0
        deadline = time.perf_counter() + 0.90
        empties = _pop(FULL ^ (me | opp))
        moves = []
        m = mv
        while m:
            b = m & -m
            moves.append((W[b.bit_length() - 1], b))
            m ^= b
        moves.sort(reverse=True)
        best_bit = moves[0][1]
        try:
            depth = 1
            while depth <= empties:
                v, bit = _root(me, opp, depth, deadline, moves)
                best_bit = bit
                if v >= WIN or v <= -WIN:
                    break  # game is decided; no need to search deeper
                depth += 1
        except _Timeout:
            pass
        return _sq_name(best_bit.bit_length() - 1)
    except Exception:
        return fallback
