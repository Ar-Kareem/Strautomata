
import time

# --------------------------------------------------------------------------
# 4x4 Tic-Tac-Toe policy: bitboard alpha-beta engine with iterative deepening
# --------------------------------------------------------------------------

def _build():
    l4 = []
    for r in range(4):
        l4.append(tuple(r * 4 + c for c in range(4)))
    for c in range(4):
        l4.append(tuple(r * 4 + c for r in range(4)))
    l4.append((0, 5, 10, 15))
    l4.append((3, 6, 9, 12))
    w3 = []
    for r in range(4):
        for c in (0, 1):
            w3.append(tuple(r * 4 + c + k for k in range(3)))
    for c in range(4):
        for r in (0, 1):
            w3.append(tuple((r + k) * 4 + c for k in range(3)))
    for r in (0, 1):
        for c in (0, 1):
            w3.append(tuple((r + k) * 4 + (c + k) for k in range(3)))
    for r in (0, 1):
        for c in (2, 3):
            w3.append(tuple((r + k) * 4 + (c - k) for k in range(3)))
    return l4, w3

_L4, _W3 = _build()
_L4M = tuple(sum(1 << i for i in t) for t in _L4)
_W3M = tuple(sum(1 << i for i in t) for t in _W3)

_CELL_L4 = [[] for _ in range(16)]
for _lm in _L4M:
    for _i in range(16):
        if (_lm >> _i) & 1:
            _CELL_L4[_i].append(_lm)
_CELL_L4 = tuple(tuple(t) for t in _CELL_L4)

_CELL_W3 = [[] for _ in range(16)]
for _lm in _W3M:
    for _i in range(16):
        if (_lm >> _i) & 1:
            _CELL_W3[_i].append(_lm)
_CELL_W3 = tuple(tuple(t) for t in _CELL_W3)

_NEIGH = []
for _i in range(16):
    _r, _c = divmod(_i, 4)
    _m = 0
    for _dr in (-1, 0, 1):
        for _dc in (-1, 0, 1):
            if _dr or _dc:
                _nr, _nc = _r + _dr, _c + _dc
                if 0 <= _nr < 4 and 0 <= _nc < 4:
                    _m |= 1 << (_nr * 4 + _nc)
    _NEIGH.append(_m)
_NEIGH = tuple(_NEIGH)

_COVER = tuple(2 * len(_CELL_L4[i]) + len(_CELL_W3[i]) for i in range(16))

# evaluation pattern tables (indexed by stone count in a line/window)
_T4 = (0, 5, 60, 9000, 0)
_T3 = (0, 3, 28, 2500)
# move-ordering tables
_O4 = (0, 3, 20, 300, 5000)
_B4 = (0, 3, 16, 220, 4000)
_O3 = (0, 2, 10, 120)
_B3 = (0, 2, 8, 90)

_V4 = 9000000      # four in a row (terminal)
_V3 = 120000       # our three in a row (near-terminal win)
_PEN = 60000       # opponent three in a row penalty (per window)
_TB = 40000        # bonus per open 4-threat created with our three
_FULL = 0xFFFF
_INF = 10 ** 9

# popcount with fallback for older Python versions
try:
    _bc = int.bit_count
    _bc(3)
except AttributeError:
    _POPT = tuple(bin(i).count("1") for i in range(1 << 16))
    def _bc(n, _p=_POPT):
        s = 0
        while n:
            s += _p[n & 0xFFFF]
            n >>= 16
        return s

_TT = {}
_N = [0]
_DL = 0.0


class _Abort(Exception):
    pass


def _eval(x, o):
    """Static evaluation from player 1's (our) perspective."""
    s = 0
    bc = _bc
    for lm in _L4M:
        pa = bc(x & lm)
        pb = bc(o & lm)
        if pa and pb:
            continue
        s += _T4[pa] - _T4[pb]
    for lm in _W3M:
        pa = bc(x & lm)
        pb = bc(o & lm)
        if pa and pb:
            continue
        s += _T3[pa] - _T3[pb]
    for i in range(16):
        if (x >> i) & 1:
            s += _COVER[i]
        elif (o >> i) & 1:
            s -= _COVER[i]
    return s


def _ordered(mine, opp, occ, empt, tm, full_score):
    """Generate empty cells ordered best-first for the side to move."""
    res = []
    bc = _bc
    e = empt
    while e:
        lb = e & -e
        m = lb.bit_length() - 1
        e ^= lb
        s = _COVER[m] * 4 + 2 * bc(occ & _NEIGH[m])
        if m == tm:
            s += 1 << 22
        if full_score:
            so = 0
            for lm in _CELL_L4[m]:
                pa = bc(mine & lm)
                pb = bc(opp & lm)
                if pb == 0:
                    so += _O4[pa]
                if pa == 0:
                    so += _B4[pb]
            for lm in _CELL_W3[m]:
                pa = bc(mine & lm)
                pb = bc(opp & lm)
                if pb == 0:
                    so += _O3[pa]
                if pa == 0:
                    so += _B3[pb]
            s += so
        res.append((s, m))
    res.sort(key=lambda t: -t[0])
    return [m for _, m in res]


def _search(x, o, player, depth, alpha, beta, ply):
    """Negamax with alpha-beta. Value is from the side-to-move's perspective."""
    _N[0] += 1
    if (_N[0] & 1023) == 0 and time.time() > _DL:
        raise _Abort
    key = (((x << 16) | o) << 1) | (0 if player == 1 else 1)
    ent = _TT.get(key)
    a0 = alpha
    b0 = beta
    tm = -1
    if ent is not None:
        ed, ev, ef, em = ent
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
        tm = em
    if depth <= 0:
        return player * _eval(x, o)
    occ = x | o
    empt = (~occ) & _FULL
    if empt == 0:
        return 0
    if player == 1:
        mine = x
        opp = o
    else:
        mine = o
        opp = x
    bc = _bc
    # immediate 4-in-a-row available for the side to move?
    for lm in _L4M:
        if (opp & lm) == 0 and bc(mine & lm) == 3:
            return _V4 - ply
    # opponent open 4-threats: the side to move is forced to answer
    threats = 0
    for lm in _L4M:
        if (mine & lm) == 0 and bc(opp & lm) == 3:
            threats |= lm & ~opp
    if threats:
        if threats & (threats - 1):
            return -(_V4 - ply)          # double threat: lost
        ml = [threats.bit_length() - 1]  # single threat: forced block
    else:
        ml = _ordered(mine, opp, occ, empt, tm, ply <= 2)
    best = -_INF
    bm = -1
    a = alpha
    is_us = player == 1
    for m in ml:
        bit = 1 << m
        if is_us:
            nx = x | bit
            no = o
            mm = nx
        else:
            nx = x
            no = o | bit
            mm = no
        term = 0
        for lm in _CELL_L4[m]:
            if mm & lm == lm:
                term = 1
                break
        if term:
            val = _V4 - ply
        else:
            k3 = 0
            for lm in _CELL_W3[m]:
                if mm & lm == lm:
                    k3 += 1
            if k3 and is_us:
                nt = 0
                for lm in _CELL_L4[m]:
                    if bc(mm & lm) == 3 and (no & lm) == 0:
                        nt += 1
                val = _V3 - ply + _TB * nt
            elif (occ | bit) == _FULL:
                val = 0
                if k3:
                    val += _PEN * k3
            else:
                val = -_search(nx, no, -player, depth - 1, -beta, -a, ply + 1)
                if k3:
                    val += _PEN * k3
        if val > best:
            best = val
            bm = m
            if val > a:
                a = val
                if a >= beta:
                    break
    if len(_TT) < 1200000:
        if best <= a0:
            fl = 2
        elif best >= b0:
            fl = 1
        else:
            fl = 0
        _TT[key] = (depth, best, fl, bm)
    return best


def _choose(board):
    flat = []
    for row in board:
        flat.extend(row)
    empties = [i for i, v in enumerate(flat) if v == 0]
    if not empties:
        return (0, 0)
    if len(empties) == 16:
        return (1, 1)
    if len(empties) == 1:
        return divmod(empties[0], 4)
    x = 0
    o = 0
    for i, v in enumerate(flat):
        if v == 1:
            x |= 1 << i
        elif v == -1:
            o |= 1 << i
    occ = x | o
    empt = (~occ) & _FULL
    # play an immediate 4-in-a-row win
    e = empt
    while e:
        lb = e & -e
        m = lb.bit_length() - 1
        e ^= lb
        nm = x | lb
        for lm in _CELL_L4[m]:
            if nm & lm == lm:
                return divmod(m, 4)
    # block the opponent's immediate 4-in-a-row win
    e = empt
    while e:
        lb = e & -e
        m = lb.bit_length() - 1
        e ^= lb
        nm = o | lb
        for lm in _CELL_L4[m]:
            if nm & lm == lm:
                return divmod(m, 4)
    global _TT, _DL
    _TT = {}
    _N[0] = 0
    _DL = time.time() + 0.80
    order = _ordered(x, o, occ, empt, -1, True)
    best_move = order[0]
    maxdepth = len(order)
    if maxdepth > 12:
        maxdepth = 12
    try:
        depth = 1
        while depth <= maxdepth:
            alpha = -_INF
            cur = -_INF
            curm = best_move
            scored = []
            for m in order:
                bit = 1 << m
                nx = x | bit
                term = 0
                for lm in _CELL_L4[m]:
                    if nx & lm == lm:
                        term = 1
                        break
                if term:
                    val = _V4
                else:
                    k3 = 0
                    for lm in _CELL_W3[m]:
                        if nx & lm == lm:
                            k3 += 1
                    if k3:
                        nt = 0
                        bc = _bc
                        for lm in _CELL_L4[m]:
                            if bc(nx & lm) == 3 and (o & lm) == 0:
                                nt += 1
                        val = _V3 + _TB * nt
                    elif (occ | bit) == _FULL:
                        val = 0
                    else:
                        val = -_search(nx, o, -1, depth - 1, -_INF, -alpha, 1)
                scored.append((val, m))
                if val > cur:
                    cur = val
                    curm = m
                if val > alpha:
                    alpha = val
            best_move = curm
            scored.sort(key=lambda t: -t[0])
            order = [m for _, m in scored]
            if cur >= _V4 - 40:
                break
            depth += 1
    except _Abort:
        pass
    if best_move < 0 or ((occ >> best_move) & 1):
        best_move = empties[0]
    return divmod(best_move, 4)


def policy(board):
    try:
        r, c = _choose(board)
        if 0 <= r < 4 and 0 <= c < 4 and board[r][c] == 0:
            return (int(r), int(c))
    except Exception:
        pass
    try:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)
