
import time
import random as _random

# ------------------------- winning lines -------------------------
def _build_lines():
    lines = []
    for a in range(3):
        for b in range(3):
            lines.append(((a, b, 0), (a, b, 1), (a, b, 2)))
            lines.append(((a, 0, b), (a, 1, b), (a, 2, b)))
            lines.append(((0, a, b), (1, a, b), (2, a, b)))
    for v in range(3):
        lines.append(((v, 0, 0), (v, 1, 1), (v, 2, 2)))
        lines.append(((v, 0, 2), (v, 1, 1), (v, 2, 0)))
        lines.append(((0, v, 0), (1, v, 1), (2, v, 2)))
        lines.append(((0, v, 2), (1, v, 1), (2, v, 0)))
        lines.append(((0, 0, v), (1, 1, v), (2, 2, v)))
        lines.append(((0, 2, v), (1, 1, v), (2, 0, v)))
    lines.append(((0, 0, 0), (1, 1, 1), (2, 2, 2)))
    lines.append(((0, 0, 2), (1, 1, 1), (2, 2, 0)))
    lines.append(((0, 2, 0), (1, 1, 1), (2, 0, 2)))
    lines.append(((0, 2, 2), (1, 1, 1), (2, 0, 0)))
    return lines

def _flat(c):
    return c[0] * 9 + c[1] * 3 + c[2]

_LN = [tuple(_flat(c) for c in line) for line in _build_lines()]  # 49 lines
_NL = len(_LN)
_CL = [[] for _ in range(27)]
for _li in range(_NL):
    for _c in _LN[_li]:
        _CL[_c].append(_li)
_CL = [tuple(x) for x in _CL]
_ST = tuple(len(_CL[c]) for c in range(27))  # static line-count per cell

_rng = _random.Random(20240501)
_Z = [[_rng.getrandbits(64) for _ in range(3)] for _ in range(27)]

WIN = 1000000
INF = 2000000
W1 = (0, 3, 40, 0)      # our line with n marks (no opponent mark)
WO = (0, 3, 44, 0)      # opponent line with n marks (defensive bias)
TOURS = (0, 50, 400, 700)   # bonus per number of our distinct threats
TOPP = (0, 60, 500, 850)    # penalty per number of opponent threats
ATT = (1, 5, 30, 0)
DEF = (0, 4, 24, 0)

class _Timeout(Exception):
    pass

# ------------------------- search state -------------------------
_b = [0] * 27
_c1 = [0] * _NL
_co = [0] * _NL
_th1 = {}
_tho = {}
_empty = []
_pos = [-1] * 27
_tlog = []
_dlog = []
_tt = {}
_eval = 0
_h = 0
_nodes = 0
_deadline = 0.0

def _place(m, side):
    global _eval, _h
    _b[m] = side
    _h ^= _Z[m][1 if side == 1 else 2]
    b = _b
    logs = []
    delta = 0
    won = False
    if side == 1:
        c1 = _c1; co = _co; ths = _th1; tho = _tho
        for L in _CL[m]:
            a = c1[L]; o = co[L]
            c1[L] = a + 1
            if o == 0:
                delta += W1[a + 1] - W1[a]
                if a == 1:  # new threat for us
                    x, y, z = _LN[L]
                    if x != m and b[x] == 0:
                        e = x
                    elif y != m and b[y] == 0:
                        e = y
                    else:
                        e = z
                    ths[e] = ths.get(e, 0) + 1
                    logs.append((0, e, 1))
                elif a == 2:  # we win; remove our threat on m
                    won = True
                    v = ths.get(m)
                    if v is not None:
                        if v > 1:
                            ths[m] = v - 1
                        else:
                            del ths[m]
                        logs.append((0, m, -1))
            elif a == 0:
                delta += WO[o]  # opponent line died
                if o == 2:      # we blocked an opponent threat on m
                    v = tho.get(m)
                    if v > 1:
                        tho[m] = v - 1
                    else:
                        del tho[m]
                    logs.append((1, m, -1))
    else:
        c1 = _c1; co = _co; ths = _tho; tho = _th1
        for L in _CL[m]:
            o = co[L]; a = c1[L]
            co[L] = o + 1
            if a == 0:
                delta += WO[o] - WO[o + 1]
                if o == 1:  # new opponent threat
                    x, y, z = _LN[L]
                    if x != m and b[x] == 0:
                        e = x
                    elif y != m and b[y] == 0:
                        e = y
                    else:
                        e = z
                    ths[e] = ths.get(e, 0) + 1
                    logs.append((1, e, 1))
                elif o == 2:  # opponent wins; remove their threat on m
                    won = True
                    v = ths.get(m)
                    if v is not None:
                        if v > 1:
                            ths[m] = v - 1
                        else:
                            del ths[m]
                        logs.append((1, m, -1))
            elif o == 0:
                delta -= W1[a]  # our line died
                if a == 2:      # they blocked our threat on m
                    v = tho.get(m)
                    if v > 1:
                        tho[m] = v - 1
                    else:
                        del tho[m]
                    logs.append((0, m, -1))
    _tlog.append(logs)
    _dlog.append(delta)
    _eval += delta
    i = _pos[m]
    last = _empty[-1]
    _empty[i] = last
    _pos[last] = i
    _empty.pop()
    _pos[m] = -1
    return won

def _unplace(m, side):
    global _eval, _h
    if side == 1:
        c1 = _c1
        for L in _CL[m]:
            c1[L] -= 1
    else:
        co = _co
        for L in _CL[m]:
            co[L] -= 1
    _b[m] = 0
    _h ^= _Z[m][1 if side == 1 else 2]
    _eval -= _dlog.pop()
    for w, cell, d in _tlog.pop():
        dct = _th1 if w == 0 else _tho
        nv = dct.get(cell, 0) - d
        if nv:
            dct[cell] = nv
        elif cell in dct:
            del dct[cell]
    _pos[m] = len(_empty)
    _empty.append(m)

def _gen_moves(side, tt_move):
    if side == 1:
        if _th1:
            return list(_th1)
        if _tho:
            return list(_tho)
    else:
        if _tho:
            return list(_tho)
        if _th1:
            return list(_th1)
    scored = []
    c1 = _c1; co = _co
    if side == 1:
        for m in _empty:
            s = _ST[m]
            for L in _CL[m]:
                a = c1[L]; o = co[L]
                if o == 0:
                    s += ATT[a]
                elif a == 0:
                    s += DEF[o]
            scored.append((-s, m))
    else:
        for m in _empty:
            s = _ST[m]
            for L in _CL[m]:
                a = c1[L]; o = co[L]
                if a == 0:
                    s += ATT[o]
                elif o == 0:
                    s += DEF[a]
            scored.append((-s, m))
    scored.sort()
    if tt_move >= 0:
        for i in range(len(scored)):
            if scored[i][1] == tt_move:
                scored.insert(0, scored.pop(i))
                break
    return [p[1] for p in scored]

def _leaf_val():
    t1 = len(_th1); t2 = len(_tho)
    return _eval + TOURS[t1 if t1 < 3 else 3] - TOPP[t2 if t2 < 3 else 3]

def _search(depth, alpha, beta, side, ply):
    global _nodes
    _nodes += 1
    if (_nodes & 1023) == 0 and time.time() >= _deadline:
        raise _Timeout()
    alpha0 = alpha
    key = _h + _h + (0 if side == 1 else 1)
    tt_move = -1
    ent = _tt.get(key)
    if ent is not None:
        ed, ev, ef, em = ent
        if ed >= depth:
            if ef == 0:
                return ev
            if ef == 1:
                if ev > alpha:
                    alpha = ev
            else:
                if ev < beta:
                    beta = ev
            if alpha >= beta:
                return ev
        tt_move = em
    moves = _gen_moves(side, tt_move)
    if not moves:
        return 0
    best = -INF
    best_move = moves[0]
    for m in moves:
        won = _place(m, side)
        if won:
            val = WIN - ply
        elif depth <= 1:
            v = _leaf_val()
            val = v if side == 1 else -v
        else:
            val = -_search(depth - 1, -beta, -alpha, -side, ply + 1)
        _unplace(m, side)
        if val > best:
            best = val
            best_move = m
            if val > alpha:
                alpha = val
                if alpha >= beta:
                    break
    if best <= alpha0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _tt[key] = (depth, best, flag, best_move)
    return best

def _root(depth):
    global _nodes
    _nodes += 1
    alpha = -INF
    beta = INF
    key = _h + _h
    tt_move = -1
    ent = _tt.get(key)
    if ent is not None:
        tt_move = ent[3]
    moves = _gen_moves(1, tt_move)
    if not moves:
        return 0, -1
    best = -INF
    best_move = moves[0]
    for m in moves:
        won = _place(m, 1)
        if won:
            val = WIN
        elif depth <= 1:
            val = _leaf_val()
        else:
            val = -_search(depth - 1, -beta, -alpha, -1, 1)
        _unplace(m, 1)
        if val > best:
            best = val
            best_move = m
            if val > alpha:
                alpha = val
    _tt[key] = (depth, best, 0, best_move)
    return best, best_move

def policy(board):
    global _eval, _h, _nodes, _deadline, _tt, _tlog, _dlog, _empty, _pos
    start = time.time()
    _deadline = start + 0.85
    _tt = {}
    _tlog = []
    _dlog = []
    _eval = 0
    _h = 0
    _nodes = 0
    _th1.clear()
    _tho.clear()
    _empty = []
    _pos = [-1] * 27

    n_moves = 0
    for i in range(3):
        bi = board[i]
        base_i = i * 9
        for j in range(3):
            row = bi[j]
            base = base_i + j * 3
            for k in range(3):
                v = row[k]
                idx = base + k
                _b[idx] = v
                if v == 0:
                    _pos[idx] = len(_empty)
                    _empty.append(idx)
                else:
                    n_moves += 1

    if not _empty:
        return (0, 0, 0)  # board full (should not happen); must return something
    if n_moves == 0:
        return (1, 1, 1)  # take the center on an empty board
    if len(_empty) == 1:
        m = _empty[0]
        return (m // 9, (m // 3) % 3, m % 3)

    for li in range(_NL):
        x, y, z = _LN[li]
        bx = _b[x]; by = _b[y]; bz = _b[z]
        a = (1 if bx == 1 else 0) + (1 if by == 1 else 0) + (1 if bz == 1 else 0)
        o = (1 if bx == -1 else 0) + (1 if by == -1 else 0) + (1 if bz == -1 else 0)
        _c1[li] = a
        _co[li] = o
        if a:
            if o == 0:
                _eval += W1[a]
                if a == 2:
                    e = x if bx == 0 else (y if by == 0 else z)
                    _th1[e] = _th1.get(e, 0) + 1
        elif o:
            _eval -= WO[o]
            if o == 2:
                e = x if bx == 0 else (y if by == 0 else z)
                _tho[e] = _tho.get(e, 0) + 1
    for c in range(27):
        v = _b[c]
        if v == 1:
            _h ^= _Z[c][1]
        elif v == -1:
            _h ^= _Z[c][2]

    # immediate win
    if _th1:
        m = next(iter(_th1))
        return (m // 9, (m // 3) % 3, m % 3)

    moves0 = _gen_moves(1, -1)
    best_move = moves0[0]

    max_depth = len(_empty)
    if max_depth > 12:
        max_depth = 12
    depth = 1
    while depth <= max_depth:
        try:
            val, mv = _root(depth)
        except _Timeout:
            break
        if mv >= 0:
            best_move = mv
        if val >= WIN - 100 or val <= -WIN + 100:
            break
        if time.time() >= _deadline - 0.05:
            break
        depth += 1

    return (best_move // 9, (best_move // 3) % 3, best_move % 3)
