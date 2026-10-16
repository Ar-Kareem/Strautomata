
import numpy as np
import time

FULL = (1 << 64) - 1
NOT_A = 0xfefefefefefefefe
NOT_H = 0x7f7f7f7f7f7f7f7f
CORNERS = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)
INF = 10 ** 18
WIN = 100000

W_BOARD = [
    [120, -20, 20, 5, 5, 20, -20, 120],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [5, -5, 3, 3, 3, 3, -5, 5],
    [20, -5, 15, 3, 3, 15, -5, 20],
    [-20, -40, -5, -5, -5, -5, -40, -20],
    [120, -20, 20, 5, 5, 20, -20, 120],
]
W64 = [0] * 64
for _r in range(8):
    for _c in range(8):
        W64[_r * 8 + _c] = W_BOARD[_r][_c]

TABLE = [[0] * 256 for _ in range(8)]
for _k in range(8):
    base = _k * 8
    row = TABLE[_k]
    for _b in range(256):
        s = 0
        if _b:
            if _b & 1:
                s += W64[base]
            if _b & 2:
                s += W64[base + 1]
            if _b & 4:
                s += W64[base + 2]
            if _b & 8:
                s += W64[base + 3]
            if _b & 16:
                s += W64[base + 4]
            if _b & 32:
                s += W64[base + 5]
            if _b & 64:
                s += W64[base + 6]
            if _b & 128:
                s += W64[base + 7]
        row[_b] = s

try:
    (0).bit_count()
    def popcnt(x):
        return x.bit_count()
except Exception:
    def popcnt(x):
        return bin(x).count("1")

class _Timeout(Exception):
    pass

_deadline = 0.0
_nodes = 0

def get_moves(player, opponent):
    empty = (~(player | opponent)) & FULL
    moves = 0
    t = ((player << 8) & FULL) & opponent
    t |= ((t << 8) & FULL) & opponent
    t |= ((t << 8) & FULL) & opponent
    t |= ((t << 8) & FULL) & opponent
    t |= ((t << 8) & FULL) & opponent
    t |= ((t << 8) & FULL) & opponent
    moves |= ((t << 8) & FULL) & empty
    t = (player >> 8) & opponent
    t |= (t >> 8) & opponent
    t |= (t >> 8) & opponent
    t |= (t >> 8) & opponent
    t |= (t >> 8) & opponent
    t |= (t >> 8) & opponent
    moves |= (t >> 8) & empty
    t = (((player & NOT_H) << 1) & FULL) & opponent
    t |= (((t & NOT_H) << 1) & FULL) & opponent
    t |= (((t & NOT_H) << 1) & FULL) & opponent
    t |= (((t & NOT_H) << 1) & FULL) & opponent
    t |= (((t & NOT_H) << 1) & FULL) & opponent
    t |= (((t & NOT_H) << 1) & FULL) & opponent
    moves |= (((t & NOT_H) << 1) & FULL) & empty
    t = ((player & NOT_A) >> 1) & opponent
    t |= ((t & NOT_A) >> 1) & opponent
    t |= ((t & NOT_A) >> 1) & opponent
    t |= ((t & NOT_A) >> 1) & opponent
    t |= ((t & NOT_A) >> 1) & opponent
    t |= ((t & NOT_A) >> 1) & opponent
    moves |= ((t & NOT_A) >> 1) & empty
    t = (((player & NOT_H) << 9) & FULL) & opponent
    t |= (((t & NOT_H) << 9) & FULL) & opponent
    t |= (((t & NOT_H) << 9) & FULL) & opponent
    t |= (((t & NOT_H) << 9) & FULL) & opponent
    t |= (((t & NOT_H) << 9) & FULL) & opponent
    t |= (((t & NOT_H) << 9) & FULL) & opponent
    moves |= (((t & NOT_H) << 9) & FULL) & empty
    t = (((player & NOT_A) << 7) & FULL) & opponent
    t |= (((t & NOT_A) << 7) & FULL) & opponent
    t |= (((t & NOT_A) << 7) & FULL) & opponent
    t |= (((t & NOT_A) << 7) & FULL) & opponent
    t |= (((t & NOT_A) << 7) & FULL) & opponent
    t |= (((t & NOT_A) << 7) & FULL) & opponent
    moves |= (((t & NOT_A) << 7) & FULL) & empty
    t = ((player & NOT_H) >> 7) & opponent
    t |= ((t & NOT_H) >> 7) & opponent
    t |= ((t & NOT_H) >> 7) & opponent
    t |= ((t & NOT_H) >> 7) & opponent
    t |= ((t & NOT_H) >> 7) & opponent
    t |= ((t & NOT_H) >> 7) & opponent
    moves |= ((t & NOT_H) >> 7) & empty
    t = ((player & NOT_A) >> 9) & opponent
    t |= ((t & NOT_A) >> 9) & opponent
    t |= ((t & NOT_A) >> 9) & opponent
    t |= ((t & NOT_A) >> 9) & opponent
    t |= ((t & NOT_A) >> 9) & opponent
    t |= ((t & NOT_A) >> 9) & opponent
    moves |= ((t & NOT_A) >> 9) & empty
    return moves

def get_flips(player, opponent, move):
    flips = 0
    cur = (move << 8) & FULL
    line = 0
    while cur & opponent:
        line |= cur
        cur = (cur << 8) & FULL
    if cur & player:
        flips |= line
    cur = move >> 8
    line = 0
    while cur & opponent:
        line |= cur
        cur >>= 8
    if cur & player:
        flips |= line
    cur = (((move & NOT_H) << 1) & FULL)
    line = 0
    while cur & opponent:
        line |= cur
        cur = (((cur & NOT_H) << 1) & FULL)
    if cur & player:
        flips |= line
    cur = ((move & NOT_A) >> 1)
    line = 0
    while cur & opponent:
        line |= cur
        cur = ((cur & NOT_A) >> 1)
    if cur & player:
        flips |= line
    cur = (((move & NOT_H) << 9) & FULL)
    line = 0
    while cur & opponent:
        line |= cur
        cur = (((cur & NOT_H) << 9) & FULL)
    if cur & player:
        flips |= line
    cur = (((move & NOT_A) << 7) & FULL)
    line = 0
    while cur & opponent:
        line |= cur
        cur = (((cur & NOT_A) << 7) & FULL)
    if cur & player:
        flips |= line
    cur = ((move & NOT_H) >> 7)
    line = 0
    while cur & opponent:
        line |= cur
        cur = ((cur & NOT_H) >> 7)
    if cur & player:
        flips |= line
    cur = ((move & NOT_A) >> 9)
    line = 0
    while cur & opponent:
        line |= cur
        cur = ((cur & NOT_A) >> 9)
    if cur & player:
        flips |= line
    return flips

def evaluate(p, o):
    my_bb = get_moves(p, o)
    opp_bb = get_moves(o, p)
    my_mob = popcnt(my_bb)
    opp_mob = popcnt(opp_bb)
    if my_mob == 0 and opp_mob == 0:
        d = popcnt(p) - popcnt(o)
        if d > 0:
            return WIN + d
        elif d < 0:
            return -WIN + d
        else:
            return 0
    pc = popcnt(p & CORNERS)
    oc = popcnt(o & CORNERS)
    score = (pc - oc) * 2500
    occ = p | o
    if ((occ >> 0) & 1) == 0:
        if (p >> 9) & 1:
            score -= 450
        if (p >> 1) & 1:
            score -= 150
        if (p >> 8) & 1:
            score -= 150
        if (o >> 9) & 1:
            score += 450
        if (o >> 1) & 1:
            score += 150
        if (o >> 8) & 1:
            score += 150
    if ((occ >> 7) & 1) == 0:
        if (p >> 14) & 1:
            score -= 450
        if (p >> 6) & 1:
            score -= 150
        if (p >> 15) & 1:
            score -= 150
        if (o >> 14) & 1:
            score += 450
        if (o >> 6) & 1:
            score += 150
        if (o >> 15) & 1:
            score += 150
    if ((occ >> 56) & 1) == 0:
        if (p >> 49) & 1:
            score -= 450
        if (p >> 48) & 1:
            score -= 150
        if (p >> 57) & 1:
            score -= 150
        if (o >> 49) & 1:
            score += 450
        if (o >> 48) & 1:
            score += 150
        if (o >> 57) & 1:
            score += 150
    if ((occ >> 63) & 1) == 0:
        if (p >> 54) & 1:
            score -= 450
        if (p >> 62) & 1:
            score -= 150
        if (p >> 55) & 1:
            score -= 150
        if (o >> 54) & 1:
            score += 450
        if (o >> 62) & 1:
            score += 150
        if (o >> 55) & 1:
            score += 150
    score += (my_mob - opp_mob) * 140
    empty = (~occ) & FULL
    neigh = ((empty << 8) & FULL) | (empty >> 8) | ((((empty & NOT_H) << 1) & FULL)) | (((empty & NOT_A) >> 1)) | ((((empty & NOT_H) << 9) & FULL)) | ((((empty & NOT_A) << 7) & FULL)) | (((empty & NOT_H) >> 7)) | (((empty & NOT_A) >> 9))
    my_f = popcnt(p & neigh)
    opp_f = popcnt(o & neigh)
    score += (opp_f - my_f) * 25
    st = TABLE[0][p & 255] - TABLE[0][o & 255]
    st += TABLE[1][(p >> 8) & 255] - TABLE[1][(o >> 8) & 255]
    st += TABLE[2][(p >> 16) & 255] - TABLE[2][(o >> 16) & 255]
    st += TABLE[3][(p >> 24) & 255] - TABLE[3][(o >> 24) & 255]
    st += TABLE[4][(p >> 32) & 255] - TABLE[4][(o >> 32) & 255]
    st += TABLE[5][(p >> 40) & 255] - TABLE[5][(o >> 40) & 255]
    st += TABLE[6][(p >> 48) & 255] - TABLE[6][(o >> 48) & 255]
    st += TABLE[7][(p >> 56) & 255] - TABLE[7][(o >> 56) & 255]
    score += st
    dp = popcnt(p)
    do = popcnt(o)
    tot = dp + do
    dd = dp - do
    if tot < 40:
        score += dd * -15
    elif tot < 52:
        score += dd * -5
    elif tot < 58:
        score += dd * 20
    else:
        score += dd * 150
    return score

def _negamax(p, o, depth, alpha, beta):
    global _nodes, _deadline
    _nodes += 1
    if (_nodes & 511) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()
    if depth <= 0:
        return evaluate(p, o)
    moves_bb = get_moves(p, o)
    if moves_bb == 0:
        opp_bb = get_moves(o, p)
        if opp_bb == 0:
            d = popcnt(p) - popcnt(o)
            if d > 0:
                return WIN + d
            elif d < 0:
                return -WIN + d
            else:
                return 0
        return -_negamax(o, p, depth - 1, -beta, -alpha)
    occ = p | o
    lst = []
    mm = moves_bb
    while mm:
        lsb = mm & -mm
        mm ^= lsb
        idx = (lsb.bit_length() - 1)
        f = get_flips(p, o, lsb)
        ordv = W64[idx]
        if lsb & CORNERS:
            ordv += 5000
        else:
            if idx == 9:
                if ((occ >> 0) & 1) == 0:
                    ordv -= 2000
            elif idx == 14:
                if ((occ >> 7) & 1) == 0:
                    ordv -= 2000
            elif idx == 49:
                if ((occ >> 56) & 1) == 0:
                    ordv -= 2000
            elif idx == 54:
                if ((occ >> 63) & 1) == 0:
                    ordv -= 2000
            elif idx in (1, 8, 6, 15, 48, 57, 55, 62):
                if idx in (1, 8):
                    c = 0
                elif idx in (6, 15):
                    c = 7
                elif idx in (48, 57):
                    c = 56
                else:
                    c = 63
                if ((occ >> c) & 1) == 0:
                    ordv -= 600
        lst.append((ordv, lsb, f))
    lst.sort(key=lambda x: x[0], reverse=True)
    best = -INF
    for _, mv, f in lst:
        p2 = p | mv | f
        o2 = o ^ f
        s = -_negamax(o2, p2, depth - 1, -beta, -alpha)
        if s > best:
            best = s
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def _bit_to_str(bit):
    idx = (bit.bit_length() - 1)
    r = idx // 8
    c = idx % 8
    return chr(ord('a') + c) + str(r + 1)

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _deadline, _nodes
    try:
        p = 0
        o = 0
        for r in range(8):
            yr = you[r]
            orr = opponent[r]
            for c in range(8):
                if yr[c]:
                    p |= (1 << (r * 8 + c))
                elif orr[c]:
                    o |= (1 << (r * 8 + c))
        legal = get_moves(p, o)
        if legal == 0:
            return "pass"
        moves = []
        tmp = legal
        while tmp:
            lsb = tmp & -tmp
            tmp ^= lsb
            moves.append(lsb)
        if len(moves) == 1:
            return _bit_to_str(moves[0])
        occ = p | o
        empties = 64 - popcnt(occ)
        def static_order(bit):
            idx = (bit.bit_length() - 1)
            v = W64[idx]
            if bit & CORNERS:
                v += 5000
            else:
                if idx == 9:
                    if ((occ >> 0) & 1) == 0:
                        v -= 2000
                elif idx == 14:
                    if ((occ >> 7) & 1) == 0:
                        v -= 2000
                elif idx == 49:
                    if ((occ >> 56) & 1) == 0:
                        v -= 2000
                elif idx == 54:
                    if ((occ >> 63) & 1) == 0:
                        v -= 2000
                elif idx in (1, 8, 6, 15, 48, 57, 55, 62):
                    if idx in (1, 8):
                        c0 = 0
                    elif idx in (6, 15):
                        c0 = 7
                    elif idx in (48, 57):
                        c0 = 56
                    else:
                        c0 = 63
                    if ((occ >> c0) & 1) == 0:
                        v -= 600
            return v
        moves.sort(key=static_order, reverse=True)
        best_move = moves[0]
        _deadline = time.perf_counter() + 0.88
        _nodes = 0
        if empties > 30:
            max_depth = 5
        elif empties > 20:
            max_depth = 6
        elif empties > 14:
            max_depth = 7
        else:
            max_depth = 14
            if empties > 12:
                _deadline = time.perf_counter() + 0.90
        scores = {}
        for mv in moves:
            idx = (mv.bit_length() - 1)
            scores[mv] = static_order(mv)
        for depth in range(1, max_depth + 1):
            try:
                ordered = sorted(moves, key=lambda m: scores.get(m, 0), reverse=True)
                alpha = -INF
                beta = INF
                cur_best = ordered[0]
                cur_best_score = -INF
                for mv in ordered:
                    f = get_flips(p, o, mv)
                    p2 = p | mv | f
                    o2 = o ^ f
                    s = -_negamax(o2, p2, depth - 1, -beta, -alpha)
                    scores[mv] = s
                    if s > cur_best_score:
                        cur_best_score = s
                        cur_best = mv
                    if s > alpha:
                        alpha = s
                    if alpha >= beta:
                        break
                best_move = cur_best
                if cur_best_score >= WIN - 64:
                    break
                if time.perf_counter() > _deadline - 0.05:
                    break
            except _Timeout:
                break
        return _bit_to_str(best_move)
    except Exception:
        try:
            p2 = 0
            o2 = 0
            for r in range(8):
                for c in range(8):
                    if you[r][c]:
                        p2 |= (1 << (r * 8 + c))
                    elif opponent[r][c]:
                        o2 |= (1 << (r * 8 + c))
            lg = get_moves(p2, o2)
            if lg == 0:
                return "pass"
            lsb = lg & -lg
            return _bit_to_str(lsb)
        except Exception:
            return "pass"
