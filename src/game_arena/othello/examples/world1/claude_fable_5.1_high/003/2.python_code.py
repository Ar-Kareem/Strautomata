
import numpy as np
import time

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
INF = 10 ** 9

try:
    _ = (1).bit_count()
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')


def _sq(name):
    c = ord(name[0]) - 97
    r = int(name[1]) - 1
    return 1 << (r * 8 + c)


ROWS = [0xFF << (8 * r) for r in range(8)]
COLS = [0x0101010101010101 << c for c in range(8)]
DIAG1 = []
for k in range(-7, 8):
    m = 0
    for r in range(8):
        c = r - k
        if 0 <= c < 8:
            m |= 1 << (r * 8 + c)
    DIAG1.append(m)
DIAG2 = []
for s in range(15):
    m = 0
    for r in range(8):
        c = s - r
        if 0 <= c < 8:
            m |= 1 << (r * 8 + c)
    DIAG2.append(m)

EDGE_LR = COLS[0] | COLS[7]
EDGE_TB = ROWS[0] | ROWS[7]
EDGE = EDGE_LR | EDGE_TB
CORNERS = _sq('a1') | _sq('h1') | _sq('a8') | _sq('h8')
CORNER_INFO = [
    (_sq('a1'), _sq('b2'), _sq('a2') | _sq('b1')),
    (_sq('h1'), _sq('g2'), _sq('g1') | _sq('h2')),
    (_sq('a8'), _sq('b7'), _sq('a7') | _sq('b8')),
    (_sq('h8'), _sq('g7'), _sq('g8') | _sq('h7')),
]
A_SQ = 0
for n in ('a3', 'a6', 'c1', 'f1', 'h3', 'h6', 'c8', 'f8'):
    A_SQ |= _sq(n)
B_SQ = 0
for n in ('a4', 'a5', 'd1', 'e1', 'h4', 'h5', 'd8', 'e8'):
    B_SQ |= _sq(n)

_W0 = [100, -20, 10, 5, 5, 10, -20, 100]
_W1 = [-20, -50, -2, -2, -2, -2, -50, -20]
_W2 = [10, -2, -1, -1, -1, -1, -2, 10]
_W3 = [5, -2, -1, -1, -1, -1, -2, 5]
WEIGHT = _W0 + _W1 + _W2 + _W3 + _W3 + _W2 + _W1 + _W0

TT = {}
_nodes = 0
_deadline = 0.0


class _Timeout(Exception):
    pass


def gen_moves(P, O):
    E = ~(P | O) & FULL
    OA = O & NOT_A
    OH = O & NOT_H
    EA = E & NOT_A
    EH = E & NOT_H
    # East
    t = (P << 1) & OA
    t |= (t << 1) & OA
    t |= (t << 1) & OA
    t |= (t << 1) & OA
    t |= (t << 1) & OA
    t |= (t << 1) & OA
    M = (t << 1) & EA
    # West
    t = (P >> 1) & OH
    t |= (t >> 1) & OH
    t |= (t >> 1) & OH
    t |= (t >> 1) & OH
    t |= (t >> 1) & OH
    t |= (t >> 1) & OH
    M |= (t >> 1) & EH
    # South
    t = (P << 8) & O
    t |= (t << 8) & O
    t |= (t << 8) & O
    t |= (t << 8) & O
    t |= (t << 8) & O
    t |= (t << 8) & O
    M |= (t << 8) & E
    # North
    t = (P >> 8) & O
    t |= (t >> 8) & O
    t |= (t >> 8) & O
    t |= (t >> 8) & O
    t |= (t >> 8) & O
    t |= (t >> 8) & O
    M |= (t >> 8) & E
    # SE
    t = (P << 9) & OA
    t |= (t << 9) & OA
    t |= (t << 9) & OA
    t |= (t << 9) & OA
    t |= (t << 9) & OA
    t |= (t << 9) & OA
    M |= (t << 9) & EA
    # SW
    t = (P << 7) & OH
    t |= (t << 7) & OH
    t |= (t << 7) & OH
    t |= (t << 7) & OH
    t |= (t << 7) & OH
    t |= (t << 7) & OH
    M |= (t << 7) & EH
    # NE
    t = (P >> 7) & OA
    t |= (t >> 7) & OA
    t |= (t >> 7) & OA
    t |= (t >> 7) & OA
    t |= (t >> 7) & OA
    t |= (t >> 7) & OA
    M |= (t >> 7) & EA
    # NW
    t = (P >> 9) & OH
    t |= (t >> 9) & OH
    t |= (t >> 9) & OH
    t |= (t >> 9) & OH
    t |= (t >> 9) & OH
    t |= (t >> 9) & OH
    M |= (t >> 9) & EH
    return M


def get_flips(P, O, b):
    F = 0
    OA = O & NOT_A
    OH = O & NOT_H
    t = (b << 1) & OA
    if t:
        t |= (t << 1) & OA
        t |= (t << 1) & OA
        t |= (t << 1) & OA
        t |= (t << 1) & OA
        t |= (t << 1) & OA
        if (t << 1) & NOT_A & P:
            F |= t
    t = (b >> 1) & OH
    if t:
        t |= (t >> 1) & OH
        t |= (t >> 1) & OH
        t |= (t >> 1) & OH
        t |= (t >> 1) & OH
        t |= (t >> 1) & OH
        if (t >> 1) & NOT_H & P:
            F |= t
    t = (b << 8) & O
    if t:
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        t |= (t << 8) & O
        if (t << 8) & P:
            F |= t
    t = (b >> 8) & O
    if t:
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        t |= (t >> 8) & O
        if (t >> 8) & P:
            F |= t
    t = (b << 9) & OA
    if t:
        t |= (t << 9) & OA
        t |= (t << 9) & OA
        t |= (t << 9) & OA
        t |= (t << 9) & OA
        t |= (t << 9) & OA
        if (t << 9) & NOT_A & P:
            F |= t
    t = (b << 7) & OH
    if t:
        t |= (t << 7) & OH
        t |= (t << 7) & OH
        t |= (t << 7) & OH
        t |= (t << 7) & OH
        t |= (t << 7) & OH
        if (t << 7) & NOT_H & P:
            F |= t
    t = (b >> 7) & OA
    if t:
        t |= (t >> 7) & OA
        t |= (t >> 7) & OA
        t |= (t >> 7) & OA
        t |= (t >> 7) & OA
        t |= (t >> 7) & OA
        if (t >> 7) & NOT_A & P:
            F |= t
    t = (b >> 9) & OH
    if t:
        t |= (t >> 9) & OH
        t |= (t >> 9) & OH
        t |= (t >> 9) & OH
        t |= (t >> 9) & OH
        t |= (t >> 9) & OH
        if (t >> 9) & NOT_H & P:
            F |= t
    return F


def neighbors(X):
    return ((((X << 1) | (X << 9) | (X >> 7)) & NOT_A)
            | (((X >> 1) | (X >> 9) | (X << 7)) & NOT_H)
            | ((X << 8) & FULL) | (X >> 8))


def full_lines(full):
    fh = 0
    for m in ROWS:
        if (full & m) == m:
            fh |= m
    fv = 0
    for m in COLS:
        if (full & m) == m:
            fv |= m
    fd1 = 0
    for m in DIAG1:
        if (full & m) == m:
            fd1 |= m
    fd2 = 0
    for m in DIAG2:
        if (full & m) == m:
            fd2 |= m
    return fh, fv, fd1, fd2


def stable_discs(P, fh, fv, fd1, fd2):
    S = P & ((fh & fv & fd1 & fd2) | CORNERS)
    while True:
        h = fh | EDGE_LR | ((S << 1) & NOT_A) | ((S >> 1) & NOT_H)
        v = fv | EDGE_TB | ((S << 8) & FULL) | (S >> 8)
        d1 = fd1 | EDGE | ((S << 9) & NOT_A) | ((S >> 9) & NOT_H)
        d2 = fd2 | EDGE | ((S << 7) & NOT_H) | ((S >> 7) & NOT_A)
        N = S | (P & h & v & d1 & d2)
        if N == S:
            return S
        S = N


def final_score(P, O):
    dd = popcount(P) - popcount(O)
    e = 64 - popcount(P | O)
    if dd > 0:
        dd += e
    elif dd < 0:
        dd -= e
    return dd * 1000


def evaluate(P, O):
    full = P | O
    E = ~full & FULL
    nE = popcount(E)
    mp = gen_moves(P, O)
    mo = gen_moves(O, P)
    nmp = popcount(mp)
    nmo = popcount(mo)
    if nmp == 0 and nmo == 0:
        return final_score(P, O)
    score = 9 * (nmp - nmo)
    if nmo == 0:
        score += 20
    elif nmp == 0:
        score -= 20
    score += 3 * (popcount(neighbors(O) & E) - popcount(neighbors(P) & E))
    if full & EDGE:
        fh, fv, fd1, fd2 = full_lines(full)
        sp = stable_discs(P, fh, fv, fd1, fd2)
        so = stable_discs(O, fh, fv, fd1, fd2)
        score += 14 * (popcount(sp) - popcount(so))
    for corner, x, cs in CORNER_INFO:
        if full & corner:
            if P & corner:
                score += 20
            else:
                score -= 20
        else:
            if P & x:
                score -= 25
            elif O & x:
                score += 25
            score -= 8 * (popcount(P & cs) - popcount(O & cs))
    score += 5 * (popcount(P & A_SQ) - popcount(O & A_SQ))
    score += 3 * (popcount(P & B_SQ) - popcount(O & B_SQ))
    if nE < 30:
        dd = popcount(P) - popcount(O)
        score += ((30 - nE) // 2) * dd
    return score


def negamax(P, O, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 127) == 0 and time.time() > _deadline:
        raise _Timeout()
    if depth <= 0:
        return evaluate(P, O)
    moves = gen_moves(P, O)
    if moves == 0:
        if gen_moves(O, P) == 0:
            return final_score(P, O)
        return -negamax(O, P, depth, -beta, -alpha)
    key = (P, O)
    tt = TT.get(key)
    tt_move = 0
    if tt is not None:
        td, tv, tf, tm = tt
        if td >= depth:
            if tf == 0:
                return tv
            if tf == 1 and tv >= beta:
                return tv
            if tf == 2 and tv <= alpha:
                return tv
        tt_move = tm
    children = []
    m = moves
    deep = depth >= 3
    while m:
        b = m & -m
        m ^= b
        F = get_flips(P, O, b)
        NP = O ^ F
        NO = P | F | b
        if b == tt_move:
            s = 1000000
        else:
            s = WEIGHT[b.bit_length() - 1]
            if deep:
                s -= 6 * popcount(gen_moves(NP, NO))
        children.append((s, b, NP, NO))
    children.sort(key=lambda t: t[0], reverse=True)
    best = -INF
    bestmove = 0
    a = alpha
    for s, b, NP, NO in children:
        v = -negamax(NP, NO, depth - 1, -beta, -a)
        if v > best:
            best = v
            bestmove = b
            if v > a:
                a = v
                if a >= beta:
                    break
    if best >= beta:
        flag = 1
    elif best <= alpha:
        flag = 2
    else:
        flag = 0
    TT[key] = (depth, best, flag, bestmove)
    return best


def _to_str(b):
    idx = b.bit_length() - 1
    r, c = divmod(idx, 8)
    return "abcdefgh"[c] + str(r + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global _deadline, _nodes
    start = time.time()
    _deadline = start + 0.6
    you = np.asarray(you)
    opponent = np.asarray(opponent)
    P = 0
    O = 0
    for r in range(8):
        for c in range(8):
            if you[r][c]:
                P |= 1 << (r * 8 + c)
            elif opponent[r][c]:
                O |= 1 << (r * 8 + c)
    moves = gen_moves(P, O)
    if moves == 0:
        return "pass"
    move_list = []
    m = moves
    while m:
        b = m & -m
        m ^= b
        move_list.append(b)
    if len(move_list) == 1:
        return _to_str(move_list[0])

    TT.clear()
    _nodes = 0
    empties = 64 - popcount(P | O)

    root_moves = []
    for b in move_list:
        F = get_flips(P, O, b)
        NP = O ^ F
        NO = P | F | b
        root_moves.append((WEIGHT[b.bit_length() - 1], b, NP, NO))
    root_moves.sort(key=lambda t: t[0], reverse=True)
    best_move = root_moves[0][1]

    depth = 1
    max_depth = max(empties, 1)
    while depth <= max_depth:
        a = -INF
        best_val = -INF
        best_b = None
        scores = []
        try:
            for (_, b, NP, NO) in root_moves:
                v = -negamax(NP, NO, depth - 1, -INF, -a)
                scores.append((v, b, NP, NO))
                if v > best_val:
                    best_val = v
                    best_b = b
                    if v > a:
                        a = v
        except _Timeout:
            if best_b is not None:
                best_move = best_b
            break
        best_move = best_b
        scores.sort(key=lambda t: t[0], reverse=True)
        root_moves = scores
        if depth >= empties:
            break
        if best_val >= 1000:
            break
        depth += 1
        if time.time() > _deadline:
            break

    if not (best_move & moves):
        best_move = move_list[0]
    return _to_str(best_move)
