
import numpy as np
import time

FULL = (1 << 64) - 1
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
INF = 10 ** 9


def _bit(r, c):
    return 1 << (r * 8 + c)


try:
    (0).bit_count()

    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')

CORNERS = _bit(0, 0) | _bit(0, 7) | _bit(7, 0) | _bit(7, 7)
CORNER_INFO = [
    (_bit(0, 0), _bit(1, 1), _bit(0, 1) | _bit(1, 0)),
    (_bit(0, 7), _bit(1, 6), _bit(0, 6) | _bit(1, 7)),
    (_bit(7, 0), _bit(6, 1), _bit(7, 1) | _bit(6, 0)),
    (_bit(7, 7), _bit(6, 6), _bit(7, 6) | _bit(6, 7)),
]
EDGE_ALL = 0xFF | (0xFF << 56) | 0x0101010101010101 | 0x8080808080808080
C_ALL = 0
for _ci in CORNER_INFO:
    C_ALL |= _ci[2]
EDGE_GOOD = EDGE_ALL & ~CORNERS & ~C_ALL

ROWS = [0xFF << (8 * r) for r in range(8)]
COLS = [0x0101010101010101 << c for c in range(8)]
DIAG1 = []
for k in range(-7, 8):
    m = 0
    for r in range(8):
        c = r - k
        if 0 <= c < 8:
            m |= _bit(r, c)
    DIAG1.append(m)
DIAG2 = []
for k in range(0, 15):
    m = 0
    for r in range(8):
        c = k - r
        if 0 <= c < 8:
            m |= _bit(r, c)
    DIAG2.append(m)

_W = [
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [5, -2, -1, -1, -1, -1, -2, 5],
    [10, -2, -1, -1, -1, -1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100],
]
SQW = [_W[i // 8][i % 8] for i in range(64)]

LEFT_DIRS = ((1, NOT_A), (9, NOT_A), (7, NOT_H), (8, FULL))
RIGHT_DIRS = ((1, NOT_H), (9, NOT_H), (7, NOT_A), (8, FULL))


def gen_moves(me, opp):
    empty = ~(me | opp) & FULL
    mv = 0
    for s, m in LEFT_DIRS:
        om = opp & m
        t = (me << s) & om
        t |= (t << s) & om
        t |= (t << s) & om
        t |= (t << s) & om
        t |= (t << s) & om
        t |= (t << s) & om
        mv |= (t << s) & m & empty
    for s, m in RIGHT_DIRS:
        om = opp & m
        t = (me >> s) & om
        t |= (t >> s) & om
        t |= (t >> s) & om
        t |= (t >> s) & om
        t |= (t >> s) & om
        t |= (t >> s) & om
        mv |= (t >> s) & m & empty
    return mv


def make_move(me, opp, bit):
    flips = 0
    for s, m in LEFT_DIRS:
        ray = 0
        cur = (bit << s) & m
        while cur & opp:
            ray |= cur
            cur = (cur << s) & m
        if cur & me:
            flips |= ray
    for s, m in RIGHT_DIRS:
        ray = 0
        cur = (bit >> s) & m
        while cur & opp:
            ray |= cur
            cur = (cur >> s) & m
        if cur & me:
            flips |= ray
    return me | bit | flips, opp & ~flips


def neighbors(b):
    return (((b << 1) & NOT_A) | ((b >> 1) & NOT_H) | ((b << 8) & FULL) | (b >> 8) |
            ((b << 9) & NOT_A) | ((b >> 9) & NOT_H) | ((b << 7) & NOT_H) | ((b >> 7) & NOT_A))


def full_lines(occ):
    fh = 0
    for m in ROWS:
        if occ & m == m:
            fh |= m
    fv = 0
    for m in COLS:
        if occ & m == m:
            fv |= m
    fd1 = 0
    for m in DIAG1:
        if occ & m == m:
            fd1 |= m
    fd2 = 0
    for m in DIAG2:
        if occ & m == m:
            fd2 |= m
    return fh, fv, fd1, fd2


def stable_discs(me, fh, fv, fd1, fd2):
    st = (me & fh & fv & fd1 & fd2) | (me & CORNERS)
    if not st:
        return 0
    while True:
        cand = me & ~st
        if not cand:
            return st
        h = fh | ((st << 1) & NOT_A) | ((st >> 1) & NOT_H)
        v = fv | ((st << 8) & FULL) | (st >> 8)
        d1 = fd1 | ((st << 9) & NOT_A) | ((st >> 9) & NOT_H)
        d2 = fd2 | ((st << 7) & NOT_H) | ((st >> 7) & NOT_A)
        new = cand & h & v & d1 & d2
        if not new:
            return st
        st |= new


def evaluate(me, opp):
    occ = me | opp
    empty = ~occ & FULL
    n_empty = popcount(empty)
    my_mob = popcount(gen_moves(me, opp))
    op_mob = popcount(gen_moves(opp, me))
    my_pot = popcount(neighbors(opp) & empty)
    op_pot = popcount(neighbors(me) & empty)
    ne = neighbors(empty)
    my_front = popcount(me & ne)
    op_front = popcount(opp & ne)
    fh, fv, fd1, fd2 = full_lines(occ)
    my_st = popcount(stable_discs(me, fh, fv, fd1, fd2))
    op_st = popcount(stable_discs(opp, fh, fv, fd1, fd2))
    my_c = popcount(me & CORNERS)
    op_c = popcount(opp & CORNERS)
    score = 0
    for corner, x, cm in CORNER_INFO:
        if not (occ & corner):
            if me & x:
                score -= 45
            if opp & x:
                score += 45
            score -= 10 * popcount(me & cm)
            score += 10 * popcount(opp & cm)
    score += 60 * (my_c - op_c)
    score += 22 * (my_st - op_st)
    score += 11 * (my_mob - op_mob)
    score += 4 * (my_pot - op_pot)
    score -= 3 * (my_front - op_front)
    score += 3 * (popcount(me & EDGE_GOOD) - popcount(opp & EDGE_GOOD))
    diff = popcount(me) - popcount(opp)
    if n_empty <= 18:
        score += (19 - n_empty) * 3 * diff
    elif n_empty > 44:
        score -= 2 * diff
    return score


class _Timeout(Exception):
    pass


_TT = {}
_deadline = 0.0
_nodes = 0


def negamax(me, opp, depth, alpha, beta):
    global _nodes
    _nodes += 1
    if (_nodes & 31) == 0 and time.perf_counter() > _deadline:
        raise _Timeout()
    mv = gen_moves(me, opp)
    if mv == 0:
        if gen_moves(opp, me) == 0:
            return (popcount(me) - popcount(opp)) * 10000
        return -negamax(opp, me, depth, -beta, -alpha)
    if depth <= 0:
        return evaluate(me, opp)
    key = (me, opp)
    entry = _TT.get(key)
    tt_move = 0
    if entry is not None:
        e_depth, e_val, e_flag, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == 0:
                return e_val
            if e_flag == 1 and e_val >= beta:
                return e_val
            if e_flag == 2 and e_val <= alpha:
                return e_val
    moves_list = []
    m = mv
    deep = depth >= 3
    while m:
        b = m & -m
        m ^= b
        sq = b.bit_length() - 1
        if deep:
            nme, nopp = make_move(me, opp, b)
            k = SQW[sq] - 6 * popcount(gen_moves(nopp, nme))
            if b == tt_move:
                k += 1000
            moves_list.append((k, b, nme, nopp))
        else:
            k = SQW[sq]
            if b == tt_move:
                k += 1000
            moves_list.append((k, b, None, None))
    moves_list.sort(key=lambda t: t[0], reverse=True)
    best = -INF
    best_move = 0
    a = alpha
    for k, b, nme, nopp in moves_list:
        if nme is None:
            nme, nopp = make_move(me, opp, b)
        v = -negamax(nopp, nme, depth - 1, -beta, -a)
        if v > best:
            best = v
            best_move = b
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
    _TT[key] = (depth, best, flag, best_move)
    return best


def choose_move(me, opp, time_limit):
    global _deadline, _TT, _nodes
    _TT = {}
    _nodes = 0
    _deadline = time.perf_counter() + time_limit
    mv = gen_moves(me, opp)
    if mv == 0:
        return None
    moves = []
    m = mv
    while m:
        b = m & -m
        m ^= b
        moves.append(b)
    if len(moves) == 1:
        return moves[0]
    n_empty = 64 - popcount(me | opp)
    order = sorted(moves, key=lambda b: SQW[b.bit_length() - 1], reverse=True)
    best_move = order[0]
    depth = 1
    while depth <= n_empty:
        scores = {}
        cur_best = None
        cur_best_val = -INF
        alpha = -INF
        try:
            for b in order:
                nme, nopp = make_move(me, opp, b)
                v = -negamax(nopp, nme, depth - 1, -INF, -alpha)
                scores[b] = v
                if v > cur_best_val:
                    cur_best_val = v
                    cur_best = b
                    if v > alpha:
                        alpha = v
        except _Timeout:
            if cur_best is not None:
                best_move = cur_best
            break
        best_move = cur_best
        order = sorted(order, key=lambda b: scores.get(b, -INF), reverse=True)
        depth += 1
    return best_move


def to_bits(arr):
    b = 0
    flat = np.asarray(arr).reshape(-1)
    for i in np.flatnonzero(flat):
        b |= 1 << int(i)
    return b


def sq_to_str(sq):
    r, c = sq // 8, sq % 8
    return "abcdefgh"[c] + str(r + 1)


_DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _legal_moves_simple(you, opp):
    res = []
    for r in range(8):
        for c in range(8):
            if you[r][c] or opp[r][c]:
                continue
            for dr, dc in _DIRS8:
                rr, cc = r + dr, c + dc
                n = 0
                while 0 <= rr < 8 and 0 <= cc < 8 and opp[rr][cc]:
                    rr += dr
                    cc += dc
                    n += 1
                if n > 0 and 0 <= rr < 8 and 0 <= cc < 8 and you[rr][cc]:
                    res.append((r, c))
                    break
    return res


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    you = np.asarray(you)
    opponent = np.asarray(opponent)
    try:
        me = to_bits(you)
        opp = to_bits(opponent)
        b = choose_move(me, opp, 0.55)
        if b is None:
            legal = _legal_moves_simple(you, opponent)
            if not legal:
                return "pass"
            r, c = legal[0]
            return "abcdefgh"[c] + str(r + 1)
        if not (gen_moves(me, opp) & b):
            raise ValueError("illegal move produced")
        return sq_to_str(b.bit_length() - 1)
    except Exception:
        legal = _legal_moves_simple(you, opponent)
        if not legal:
            return "pass"
        best = None
        best_w = -INF
        for r, c in legal:
            w = SQW[r * 8 + c]
            if w > best_w:
                best_w = w
                best = (r, c)
        return "abcdefgh"[best[1]] + str(best[0] + 1)
