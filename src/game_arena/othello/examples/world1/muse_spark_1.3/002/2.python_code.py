
import numpy as np
import time

_FULL = 0xFFFFFFFFFFFFFFFF
_NOT_A = 0xfefefefefefefefe
_NOT_H = 0x7f7f7f7f7f7f7f7f
_DIRS = ((1, _NOT_A), (-1, _NOT_H), (8, _FULL), (-8, _FULL), (9, _NOT_A), (7, _NOT_H), (-7, _NOT_A), (-9, _NOT_H))
CORNERS_BB = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)

_PST = [
100, -20, 10, 5, 5, 10, -20, 100,
-20, -50, -2, -2, -2, -2, -50, -20,
10, -2, 5, 1, 1, 5, -2, 10,
5, -2, 1, 1, 1, 1, -2, 5,
5, -2, 1, 1, 1, 1, -2, 5,
10, -2, 5, 1, 1, 5, -2, 10,
-20, -50, -2, -2, -2, -2, -50, -20,
100, -20, 10, 5, 5, 10, -20, 100,
]

# corner -> (X squares, C squares)
_CORNER_INFO = (
    (0, (9,), (1, 8)),
    (7, (14,), (6, 15)),
    (56, (49,), (48, 57)),
    (63, (54,), (55, 62)),
)

try:
    _HAS_BITCOUNT = hasattr(0, "bit_count")
except Exception:
    _HAS_BITCOUNT = False

def _pop(x):
    if _HAS_BITCOUNT:
        return x.bit_count()
    return bin(x).count("1")

def _get_moves(P, O):
    empty = (~(P | O)) & _FULL
    res = 0
    for s, m in _DIRS:
        if s > 0:
            t = O & m
            x = (P << s) & t
            x |= (x << s) & t
            x |= (x << s) & t
            x |= (x << s) & t
            x |= (x << s) & t
            x |= (x << s) & t
            res |= (x << s) & m & empty
        else:
            ss = -s
            t = O & m
            x = (P >> ss) & t
            x |= (x >> ss) & t
            x |= (x >> ss) & t
            x |= (x >> ss) & t
            x |= (x >> ss) & t
            x |= (x >> ss) & t
            res |= (x >> ss) & m & empty
    return res & _FULL

def _calc_flips(P, O, move):
    flips = 0
    for s, m in _DIRS:
        if s > 0:
            cur = (move << s) & m
            cap = 0
            for _ in range(6):
                if cur == 0:
                    break
                if cur & O:
                    cap |= cur
                    cur = (cur << s) & m
                    continue
                elif cur & P:
                    flips |= cap
                    break
                else:
                    break
        else:
            ss = -s
            cur = (move >> ss) & m
            cap = 0
            for _ in range(6):
                if cur == 0:
                    break
                if cur & O:
                    cap |= cur
                    cur = (cur >> ss) & m
                    continue
                elif cur & P:
                    flips |= cap
                    break
                else:
                    break
    return flips

def _evaluate(P, O):
    my_bb = _get_moves(P, O)
    op_bb = _get_moves(O, P)
    my_mob = _pop(my_bb)
    op_mob = _pop(op_bb)
    mob = my_mob - op_mob

    my_c = _pop(P & CORNERS_BB)
    op_c = _pop(O & CORNERS_BB)
    corner = my_c - op_c

    # adjacency danger when corner empty
    adj = 0
    occ = P | O
    for c, xs, cs in _CORNER_INFO:
        bit = 1 << c
        if occ & bit == 0:
            for xb in xs:
                b = 1 << xb
                if P & b:
                    adj -= 120
                elif O & b:
                    adj += 120
            for cb in cs:
                b = 1 << cb
                if P & b:
                    adj -= 45
                elif O & b:
                    adj += 45
        elif P & bit:
            for xb in xs:
                if P & (1 << xb):
                    adj += 15
            for cb in cs:
                if P & (1 << cb):
                    adj += 10
        else:
            for xb in xs:
                if O & (1 << xb):
                    adj -= 15
            for cb in cs:
                if O & (1 << cb):
                    adj -= 10

    # piece square
    pst = 0
    t = P
    while t:
        lsb = t & -t
        idx = (lsb.bit_length() - 1)
        pst += _PST[idx]
        t ^= lsb
    t = O
    while t:
        lsb = t & -t
        idx = (lsb.bit_length() - 1)
        pst -= _PST[idx]
        t ^= lsb

    # frontier
    empty = (~(P | O)) & _FULL
    neigh = 0
    for s, m in _DIRS:
        if s > 0:
            neigh |= (empty << s) & m
        else:
            neigh |= (empty >> (-s)) & m
    neigh &= _FULL
    my_f = _pop(P & neigh)
    op_f = _pop(O & neigh)
    front = op_f - my_f

    discs = _pop(P) - _pop(O)
    total = _pop(P | O)

    if total < 30:
        return mob * 22 + corner * 900 + adj + pst * 1 + front * 12
    elif total < 46:
        return mob * 16 + corner * 700 + adj + pst * 2 + front * 6 + discs * 2
    elif total < 56:
        return mob * 10 + corner * 500 + adj * 1 + pst * 2 + front * 4 + discs * 8
    else:
        return mob * 5 + corner * 350 + adj + pst * 1 + front * 2 + discs * 25

class _Timeout(Exception):
    pass

_DEADLINE = 0.0
_NODES = [0]

def _negamax(P, O, depth, alpha, beta):
    _NODES[0] += 1
    if (_NODES[0] & 511) == 0:
        if time.perf_counter() > _DEADLINE:
            raise _Timeout()
    moves = _get_moves(P, O)
    if moves == 0:
        om = _get_moves(O, P)
        if om == 0:
            d = _pop(P) - _pop(O)
            if d > 0:
                return 100000 + d
            elif d < 0:
                return -100000 + d
            else:
                return 0
        if depth <= 0:
            return -_evaluate(O, P)
        return -_negamax(O, P, depth - 1, -beta, -alpha)
    if depth <= 0:
        return _evaluate(P, O)
    # order moves
    ml = []
    mm = moves
    while mm:
        lsb = mm & -mm
        idx = (lsb.bit_length() - 1)
        h = _PST[idx]
        if lsb & CORNERS_BB:
            h += 2000
        # penalize X/C if corner empty
        # quick check
        if idx == 9 or idx == 14 or idx == 49 or idx == 54:
            h -= 400
        elif idx == 1 or idx == 8 or idx == 6 or idx == 15 or idx == 48 or idx == 57 or idx == 55 or idx == 62:
            h -= 120
        ml.append((h, lsb))
        mm ^= lsb
    ml.sort(key=lambda x: x[0], reverse=True)
    best = -1000000
    for _, mv in ml:
        f = _calc_flips(P, O, mv)
        P2 = P | mv | f
        O2 = O & (~f)
        sc = -_negamax(O2, P2, depth - 1, -beta, -alpha)
        if sc > best:
            best = sc
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def _bit_to_str(bit):
    idx = (bit.bit_length() - 1)
    c = idx % 8
    r = idx // 8
    return chr(ord('a') + c) + str(r + 1)

def _brute_moves(you, opp):
    res = []
    occ_y = you
    occ_o = opp
    dirs = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    for r in range(8):
        for c in range(8):
            if occ_y[r, c] != 0 or occ_o[r, c] != 0:
                continue
            legal = False
            for dr, dc in dirs:
                rr, cc = r + dr, c + dc
                cnt = 0
                while 0 <= rr < 8 and 0 <= cc < 8 and occ_o[rr, cc] == 1:
                    cnt += 1
                    rr += dr
                    cc += dc
                if cnt > 0 and 0 <= rr < 8 and 0 <= cc < 8 and occ_y[rr, cc] == 1:
                    legal = True
                    break
            if legal:
                res.append(chr(ord('a') + c) + str(r + 1))
    return res

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _DEADLINE
    try:
        P = 0
        O = 0
        for r in range(8):
            for c in range(8):
                if you[r, c] == 1:
                    P |= 1 << (r * 8 + c)
                elif opponent[r, c] == 1:
                    O |= 1 << (r * 8 + c)
        moves_bb = _get_moves(P, O)
        if moves_bb == 0:
            # verify with brute in case of bug
            b = _brute_moves(np.asarray(you), np.asarray(opponent))
            if len(b) > 0:
                return b[0]
            return "pass"
        # collect moves
        bits = []
        mm = moves_bb
        while mm:
            lsb = mm & -mm
            bits.append(lsb)
            mm ^= lsb
        if len(bits) == 1:
            return _bit_to_str(bits[0])
        # static order for first guess
        scored = []
        for b in bits:
            idx = (b.bit_length() - 1)
            h = _PST[idx]
            if b & CORNERS_BB:
                h += 5000
            scored.append((h, b))
        scored.sort(key=lambda x: x[0], reverse=True)
        ordered_bits = [b for _, b in scored]
        best_bit = ordered_bits[0]

        empties = 64 - _pop(P | O)
        _DEADLINE = time.perf_counter() + 0.88
        _NODES[0] = 0

        max_depth = 64
        if empties > 30:
            max_depth = 7
        elif empties > 20:
            max_depth = 8
        elif empties > 14:
            max_depth = 10
        else:
            max_depth = empties

        # iterative deepening
        # scores for ordering
        order = ordered_bits[:]
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > _DEADLINE:
                break
            alpha = -1000000
            beta = 1000000
            cur_scores = []
            best_score = -1000000
            best_local = order[0]
            try:
                for mv in order:
                    f = _calc_flips(P, O, mv)
                    P2 = P | mv | f
                    O2 = O & (~f)
                    sc = -_negamax(O2, P2, depth - 1, -beta, -alpha)
                    cur_scores.append((sc, mv))
                    if sc > best_score:
                        best_score = sc
                        best_local = mv
                    if sc > alpha:
                        alpha = sc
                # completed depth
                best_bit = best_local
                cur_scores.sort(key=lambda x: x[0], reverse=True)
                order = [b for _, b in cur_scores]
                if abs(best_score) > 50000:
                    break
            except _Timeout:
                break
        s = _bit_to_str(best_bit)
        # safety: ensure legal
        if (best_bit & moves_bb) == 0:
            return _bit_to_str(ordered_bits[0])
        return s
    except Exception:
        try:
            b = _brute_moves(np.asarray(you), np.asarray(opponent))
            if len(b) == 0:
                return "pass"
            return b[0]
        except Exception:
            return "pass"
