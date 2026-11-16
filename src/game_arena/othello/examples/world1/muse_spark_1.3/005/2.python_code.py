
import numpy as np
import time

FULL = (1 << 64) - 1
NOT_A = 0xfefefefefefefefe
NOT_H = 0x7f7f7f7f7f7f7f7f
_CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
W = [
120,-20,20,5,5,20,-20,120,
-20,-40,-5,-5,-5,-5,-40,-20,
20,-5,15,3,3,15,-5,20,
5,-5,3,3,3,3,-5,5,
5,-5,3,3,3,3,-5,5,
20,-5,15,3,3,15,-5,20,
-20,-40,-5,-5,-5,-5,-40,-20,
120,-20,20,5,5,20,-20,120,
]
_INF = 10 ** 18

try:
    (1).bit_count()
    def _popcnt(x):
        return x.bit_count()
except Exception:
    def _popcnt(x):
        return bin(x).count("1")

class _Timeout(Exception):
    pass

_deadline = 0.0
_nodes = 0
_tt = {}

def _moves_bb(P, O):
    empty = FULL ^ (P | O)
    if empty == 0:
        return 0
    moves = 0
    # N (+8)
    m = ((P << 8) & FULL) & O
    m |= ((m << 8) & FULL) & O
    m |= ((m << 8) & FULL) & O
    m |= ((m << 8) & FULL) & O
    m |= ((m << 8) & FULL) & O
    m |= ((m << 8) & FULL) & O
    moves |= ((m << 8) & FULL) & empty
    # S (-8)
    m = (P >> 8) & O
    m |= (m >> 8) & O
    m |= (m >> 8) & O
    m |= (m >> 8) & O
    m |= (m >> 8) & O
    m |= (m >> 8) & O
    moves |= (m >> 8) & empty
    # E (+1)
    m = (((P & NOT_H) << 1) & FULL) & O
    m |= (((m & NOT_H) << 1) & O)
    m |= (((m & NOT_H) << 1) & O)
    m |= (((m & NOT_H) << 1) & O)
    m |= (((m & NOT_H) << 1) & O)
    m |= (((m & NOT_H) << 1) & O)
    moves |= (((m & NOT_H) << 1) & FULL) & empty
    # W (-1)
    m = ((P & NOT_A) >> 1) & O
    m |= ((m & NOT_A) >> 1) & O
    m |= ((m & NOT_A) >> 1) & O
    m |= ((m & NOT_A) >> 1) & O
    m |= ((m & NOT_A) >> 1) & O
    m |= ((m & NOT_A) >> 1) & O
    moves |= ((m & NOT_A) >> 1) & empty
    # NE (+9)
    m = (((P & NOT_H) << 9) & FULL) & O
    m |= (((m & NOT_H) << 9) & FULL) & O
    m |= (((m & NOT_H) << 9) & FULL) & O
    m |= (((m & NOT_H) << 9) & FULL) & O
    m |= (((m & NOT_H) << 9) & FULL) & O
    m |= (((m & NOT_H) << 9) & FULL) & O
    moves |= (((m & NOT_H) << 9) & FULL) & empty
    # NW (+7)
    m = (((P & NOT_A) << 7) & FULL) & O
    m |= (((m & NOT_A) << 7) & FULL) & O
    m |= (((m & NOT_A) << 7) & FULL) & O
    m |= (((m & NOT_A) << 7) & FULL) & O
    m |= (((m & NOT_A) << 7) & FULL) & O
    m |= (((m & NOT_A) << 7) & FULL) & O
    moves |= (((m & NOT_A) << 7) & FULL) & empty
    # SE (-7)
    m = ((P & NOT_H) >> 7) & O
    m |= ((m & NOT_H) >> 7) & O
    m |= ((m & NOT_H) >> 7) & O
    m |= ((m & NOT_H) >> 7) & O
    m |= ((m & NOT_H) >> 7) & O
    m |= ((m & NOT_H) >> 7) & O
    moves |= ((m & NOT_H) >> 7) & empty
    # SW (-9)
    m = ((P & NOT_A) >> 9) & O
    m |= ((m & NOT_A) >> 9) & O
    m |= ((m & NOT_A) >> 9) & O
    m |= ((m & NOT_A) >> 9) & O
    m |= ((m & NOT_A) >> 9) & O
    m |= ((m & NOT_A) >> 9) & O
    moves |= ((m & NOT_A) >> 9) & empty
    return moves & FULL

def _calc_flip(mo, P, O):
    flips = 0
    cur = (mo << 8) & FULL
    if cur & O:
        cap = cur
        cur = (cur << 8) & FULL
        while cur & O:
            cap |= cur
            cur = (cur << 8) & FULL
        if cur & P:
            flips |= cap
    cur = mo >> 8
    if cur & O:
        cap = cur
        cur = cur >> 8
        while cur & O:
            cap |= cur
            cur = cur >> 8
        if cur & P:
            flips |= cap
    cur = (((mo & NOT_H) << 1) & FULL)
    if cur & O:
        cap = cur
        cur = (((cur & NOT_H) << 1) & FULL)
        while cur & O:
            cap |= cur
            cur = (((cur & NOT_H) << 1) & FULL)
        if cur & P:
            flips |= cap
    cur = ((mo & NOT_A) >> 1)
    if cur & O:
        cap = cur
        cur = ((cur & NOT_A) >> 1)
        while cur & O:
            cap |= cur
            cur = ((cur & NOT_A) >> 1)
        if cur & P:
            flips |= cap
    cur = (((mo & NOT_H) << 9) & FULL)
    if cur & O:
        cap = cur
        cur = (((cur & NOT_H) << 9) & FULL)
        while cur & O:
            cap |= cur
            cur = (((cur & NOT_H) << 9) & FULL)
        if cur & P:
            flips |= cap
    cur = (((mo & NOT_A) << 7) & FULL)
    if cur & O:
        cap = cur
        cur = (((cur & NOT_A) << 7) & FULL)
        while cur & O:
            cap |= cur
            cur = (((cur & NOT_A) << 7) & FULL)
        if cur & P:
            flips |= cap
    cur = ((mo & NOT_H) >> 7)
    if cur & O:
        cap = cur
        cur = ((cur & NOT_H) >> 7)
        while cur & O:
            cap |= cur
            cur = ((cur & NOT_H) >> 7)
        if cur & P:
            flips |= cap
    cur = ((mo & NOT_A) >> 9)
    if cur & O:
        cap = cur
        cur = ((cur & NOT_A) >> 9)
        while cur & O:
            cap |= cur
            cur = ((cur & NOT_A) >> 9)
        if cur & P:
            flips |= cap
    return flips

def _evaluate(P, O):
    my_bb = _moves_bb(P, O)
    op_bb = _moves_bb(O, P)
    my_mob = _popcnt(my_bb)
    op_mob = _popcnt(op_bb)
    if my_mob == 0 and op_mob == 0:
        d = _popcnt(P) - _popcnt(O)
        if d > 0:
            return 1000000 + d
        if d < 0:
            return -1000000 + d
        return 0
    s = 0
    t = P
    while t:
        lsb = t & -t
        s += W[lsb.bit_length() - 1]
        t ^= lsb
    t = O
    while t:
        lsb = t & -t
        s -= W[lsb.bit_length() - 1]
        t ^= lsb
    mc = _popcnt(P & _CORNERS) - _popcnt(O & _CORNERS)
    s += mc * 350
    occ = P | O
    if not (occ & 1):
        if P & 2:
            s -= 80
        elif O & 2:
            s += 80
        if P & 256:
            s -= 80
        elif O & 256:
            s += 80
        if P & 512:
            s -= 180
        elif O & 512:
            s += 180
    if not (occ & 128):
        if P & 64:
            s -= 80
        elif O & 64:
            s += 80
        if P & 32768:
            s -= 80
        elif O & 32768:
            s += 80
        if P & 16384:
            s -= 180
        elif O & 16384:
            s += 180
    if not (occ & (1 << 56)):
        if P & (1 << 48):
            s -= 80
        elif O & (1 << 48):
            s += 80
        if P & (1 << 57):
            s -= 80
        elif O & (1 << 57):
            s += 80
        if P & (1 << 49):
            s -= 180
        elif O & (1 << 49):
            s += 180
    if not (occ & (1 << 63)):
        if P & (1 << 62):
            s -= 80
        elif O & (1 << 62):
            s += 80
        if P & (1 << 55):
            s -= 80
        elif O & (1 << 55):
            s += 80
        if P & (1 << 54):
            s -= 180
        elif O & (1 << 54):
            s += 180
    s += (my_mob - op_mob) * 18
    e = FULL ^ (P | O)
    neigh = (((e << 8) & FULL) | (e >> 8) | ((((e & NOT_H) << 1) & FULL)) | (((e & NOT_A) >> 1)) | ((((e & NOT_H) << 9) & FULL)) | ((((e & NOT_A) << 7) & FULL)) | (((e & NOT_H) >> 7)) | (((e & NOT_A) >> 9)))
    fm = _popcnt(P & neigh) - _popcnt(O & neigh)
    s -= fm * 8
    empt = _popcnt(e)
    pd = _popcnt(P) - _popcnt(O)
    if empt > 30:
        s -= pd * 10
    elif empt > 20:
        s -= pd * 5
    elif empt > 14:
        pass
    elif empt > 10:
        s += pd * 5
    else:
        s += pd * 20
    return s

def _negamax(P, O, depth, alpha, beta):
    global _deadline, _nodes, _tt
    _nodes += 1
    if (_nodes & 511) == 0 and time.time() > _deadline:
        raise _Timeout()
    key = (P, O)
    if key in _tt:
        sd, sv, sf, sbm = _tt[key]
        if sd >= depth:
            if sf == 0:
                return sv
            elif sf == 1:
                if sv >= beta:
                    return sv
                if sv > alpha:
                    alpha = sv
            else:
                if sv <= alpha:
                    return sv
                if sv < beta:
                    beta = sv
    mb = _moves_bb(P, O)
    if mb == 0:
        ob = _moves_bb(O, P)
        if ob == 0:
            d = _popcnt(P) - _popcnt(O)
            if d > 0:
                return 1000000 + d
            elif d < 0:
                return -1000000 + d
            else:
                return 0
        if depth <= 0:
            return -_evaluate(O, P)
        v = -_negamax(O, P, depth - 1, -beta, -alpha)
        return v
    if depth <= 0:
        return _evaluate(P, O)
    moves = []
    b = mb
    tt_move = None
    if key in _tt:
        tt_move = _tt[key][3]
        if tt_move is not None and (mb & tt_move):
            fl = _calc_flip(tt_move, P, O)
            if fl:
                moves.append((tt_move, fl))
                b ^= tt_move
    tmp = []
    while b:
        lsb = b & -b
        fl = _calc_flip(lsb, P, O)
        if fl:
            pos = lsb.bit_length() - 1
            tmp.append((W[pos], lsb, fl))
        b ^= lsb
    if tt_move is None and not tmp and not moves:
        return _evaluate(P, O)
    tmp.sort(key=lambda x: x[0], reverse=True)
    for _, lsb, fl in tmp:
        moves.append((lsb, fl))
    best = -_INF
    best_move = moves[0][0] if moves else None
    orig_alpha = alpha
    for mo, fl in moves:
        P2 = P | mo | fl
        O2 = O ^ fl
        v = -_negamax(O2, P2, depth - 1, -beta, -alpha)
        if v > best:
            best = v
            best_move = mo
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    if best <= orig_alpha:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    _tt[key] = (depth, best, flag, best_move)
    return best

def _to_str(pos):
    c = pos & 7
    r = pos >> 3
    return chr(ord('a') + c) + str(r + 1)

def _brute_fallback(you, opponent):
    try:
        dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
        for r in range(8):
            for c in range(8):
                if you[r][c] == 0 and opponent[r][c] == 0:
                    legal = False
                    for dr, dc in dirs:
                        nr, nc = r + dr, c + dc
                        seen_opp = False
                        while 0 <= nr < 8 and 0 <= nc < 8:
                            if opponent[nr][nc] == 1:
                                seen_opp = True
                            elif you[nr][nc] == 1:
                                if seen_opp:
                                    legal = True
                                break
                            else:
                                break
                            nr += dr
                            nc += dc
                        if legal:
                            break
                    if legal:
                        return chr(ord('a') + c) + str(r + 1)
    except Exception:
        pass
    return "pass"

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _deadline, _nodes, _tt
    P = 0
    O = 0
    try:
        for r in range(8):
            for c in range(8):
                if you[r][c] == 1:
                    P |= 1 << (r * 8 + c)
                elif opponent[r][c] == 1:
                    O |= 1 << (r * 8 + c)
    except Exception:
        return _brute_fallback(you, opponent)
    try:
        mb = _moves_bb(P, O)
        if mb == 0:
            return "pass"
        if mb & (mb - 1) == 0:
            pos = mb.bit_length() - 1
            return _to_str(pos)
        start = time.time()
        _deadline = start + 0.85
        _nodes = 0
        _tt = {}
        empties = 64 - _popcnt(P) - _popcnt(O)
        if empties <= 14:
            max_depth = empties
        elif empties <= 20:
            max_depth = 7
        elif empties <= 30:
            max_depth = 6
        else:
            max_depth = 5
        moves = []
        b = mb
        while b:
            lsb = b & -b
            fl = _calc_flip(lsb, P, O)
            pos = lsb.bit_length() - 1
            moves.append([pos, lsb, fl])
            b ^= lsb
        moves.sort(key=lambda x: W[x[0]], reverse=True)
        best_pos = moves[0][0]
        for depth in range(1, max_depth + 1):
            if time.time() > _deadline:
                break
            try:
                alpha = -_INF
                beta = _INF
                scored = []
                for pos, bit, fl in moves:
                    if time.time() > _deadline:
                        raise _Timeout()
                    P2 = P | bit | fl
                    O2 = O ^ fl
                    v = -_negamax(O2, P2, depth - 1, -beta, -alpha)
                    scored.append((v, pos, bit, fl))
                    if v > alpha:
                        alpha = v
                scored.sort(key=lambda x: x[0], reverse=True)
                moves = [[p, bi, f] for _, p, bi, f in scored]
                best_pos = scored[0][1]
                if scored[0][0] > 900000:
                    break
            except _Timeout:
                break
            except Exception:
                break
        return _to_str(best_pos)
    except Exception:
        try:
            mb2 = _moves_bb(P, O)
            if mb2 == 0:
                return "pass"
            lsb = mb2 & -mb2
            pos = lsb.bit_length() - 1
            return _to_str(pos)
        except Exception:
            return _brute_fallback(you, opponent)
