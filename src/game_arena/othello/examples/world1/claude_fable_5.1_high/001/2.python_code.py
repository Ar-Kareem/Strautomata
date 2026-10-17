
import numpy as np
import time

FULL = 0xFFFFFFFFFFFFFFFF
NOT_A = 0xFEFEFEFEFEFEFEFE
NOT_H = 0x7F7F7F7F7F7F7F7F
INF = 10 ** 9
WIN_SCALE = 10000

try:
    (1).bit_count()
    def pc(x):
        return x.bit_count()
except AttributeError:
    def pc(x):
        return bin(x).count('1')

# (shift, mask, is_left_shift)
DIRS = (
    (1, NOT_A, True),   # E
    (1, NOT_H, False),  # W
    (8, FULL, True),    # S
    (8, FULL, False),   # N
    (9, NOT_A, True),   # SE
    (7, NOT_H, True),   # SW
    (7, NOT_A, False),  # NE
    (9, NOT_H, False),  # NW
)

WEIGHT = [
    100, -20, 10, 5, 5, 10, -20, 100,
    -20, -50, -2, -2, -2, -2, -50, -20,
    10, -2, -1, -1, -1, -1, -2, 10,
    5, -2, -1, -1, -1, -1, -2, 5,
    5, -2, -1, -1, -1, -1, -2, 5,
    10, -2, -1, -1, -1, -1, -2, 10,
    -20, -50, -2, -2, -2, -2, -50, -20,
    100, -20, 10, 5, 5, 10, -20, 100,
]

def _bit(i):
    return 1 << i

CORNERS = _bit(0) | _bit(7) | _bit(56) | _bit(63)
CORNER_INFO = (
    (_bit(0), _bit(9), _bit(1), _bit(8)),
    (_bit(7), _bit(14), _bit(6), _bit(15)),
    (_bit(56), _bit(49), _bit(57), _bit(48)),
    (_bit(63), _bit(54), _bit(62), _bit(55)),
)

ROWS = [0xFF << (8 * r) for r in range(8)]
COLS = [0x0101010101010101 << c for c in range(8)]
D1 = []  # c - r constant (SE/NW axis, shift 9)
for d in range(-7, 8):
    m = 0
    for r in range(8):
        c = r + d
        if 0 <= c < 8:
            m |= 1 << (r * 8 + c)
    D1.append(m)
D2 = []  # c + r constant (SW/NE axis, shift 7)
for s in range(0, 15):
    m = 0
    for r in range(8):
        c = s - r
        if 0 <= c < 8:
            m |= 1 << (r * 8 + c)
    D2.append(m)
FILES_AH = COLS[0] | COLS[7]
RANKS_18 = ROWS[0] | ROWS[7]
EDGES = FILES_AH | RANKS_18


def legal_moves(me, opp):
    empty = ~(me | opp) & FULL
    moves = 0
    for s, m, left in DIRS:
        if left:
            t = (me << s) & m & opp
            t |= (t << s) & m & opp
            t |= (t << s) & m & opp
            t |= (t << s) & m & opp
            t |= (t << s) & m & opp
            t |= (t << s) & m & opp
            moves |= (t << s) & m & empty
        else:
            t = (me >> s) & m & opp
            t |= (t >> s) & m & opp
            t |= (t >> s) & m & opp
            t |= (t >> s) & m & opp
            t |= (t >> s) & m & opp
            t |= (t >> s) & m & opp
            moves |= (t >> s) & m & empty
    return moves


def flips(me, opp, b):
    f = 0
    for s, m, left in DIRS:
        t = 0
        if left:
            c = (b << s) & m
            while c & opp:
                t |= c
                c = (c << s) & m
            if c & me:
                f |= t
        else:
            c = (b >> s) & m
            while c & opp:
                t |= c
                c = (c >> s) & m
            if c & me:
                f |= t
    return f


def neighbors(b):
    return (((b << 1) & NOT_A) | ((b >> 1) & NOT_H) | ((b << 8) & FULL) | (b >> 8) |
            ((b << 9) & NOT_A) | ((b << 7) & NOT_H) | ((b >> 7) & NOT_A) | ((b >> 9) & NOT_H))


def stability_counts(me, opp, occ):
    fullH = fullV = fullD1 = fullD2 = 0
    for m in ROWS:
        if (occ & m) == m:
            fullH |= m
    for m in COLS:
        if (occ & m) == m:
            fullV |= m
    for m in D1:
        if (occ & m) == m:
            fullD1 |= m
    for m in D2:
        if (occ & m) == m:
            fullD2 |= m
    protH = fullH | FILES_AH
    protV = fullV | RANKS_18
    protD1 = fullD1 | EDGES
    protD2 = fullD2 | EDGES
    res = []
    for P in (me, opp):
        stab = P & protH & protV & protD1 & protD2
        while True:
            new = (P
                   & (protH | ((stab << 1) & NOT_A) | ((stab >> 1) & NOT_H))
                   & (protV | ((stab << 8) & FULL) | (stab >> 8))
                   & (protD1 | ((stab << 9) & NOT_A) | ((stab >> 9) & NOT_H))
                   & (protD2 | ((stab << 7) & NOT_H) | ((stab >> 7) & NOT_A)))
            if new == stab:
                break
            stab = new
        res.append(pc(stab))
    return res


def final_score(me, opp):
    return (pc(me) - pc(opp)) * WIN_SCALE


def evaluate(me, opp, my_moves):
    occ = me | opp
    empty = FULL ^ occ
    ne = pc(empty)
    om = pc(legal_moves(opp, me))
    mm = pc(my_moves)
    mob = mm - om
    pot = pc(neighbors(opp) & empty) - pc(neighbors(me) & empty)
    corn = pc(me & CORNERS) - pc(opp & CORNERS)
    xs = 0
    cs = 0
    for corner, x, c1, c2 in CORNER_INFO:
        if not (occ & corner):
            if me & x:
                xs -= 1
            elif opp & x:
                xs += 1
            if me & c1:
                cs -= 1
            elif opp & c1:
                cs += 1
            if me & c2:
                cs -= 1
            elif opp & c2:
                cs += 1
    if (occ & CORNERS) or ne < 24:
        sm, so = stability_counts(me, opp, occ)
        st = sm - so
    else:
        st = 0
    disc = pc(me) - pc(opp)
    if ne >= 40:
        sc = 12 * mob + 5 * pot + 45 * corn + 12 * st + 25 * xs + 8 * cs - 3 * disc
    elif ne >= 20:
        sc = 10 * mob + 4 * pot + 45 * corn + 16 * st + 20 * xs + 6 * cs
    else:
        sc = 7 * mob + 2 * pot + 40 * corn + 22 * st + 10 * xs + 3 * cs + 5 * disc
        if ne & 1:
            sc += 8
    return sc


class Timeout(Exception):
    pass


TT = {}
NODES = 0
DEADLINE = 0.0


def search(me, opp, depth, alpha, beta, passed):
    global NODES
    NODES += 1
    if (NODES & 255) == 0 and time.time() > DEADLINE:
        raise Timeout()
    moves = legal_moves(me, opp)
    if moves == 0:
        if passed:
            return final_score(me, opp)
        return -search(opp, me, depth, -beta, -alpha, True)
    if depth <= 0:
        return evaluate(me, opp, moves)
    key = (me, opp)
    e = TT.get(key)
    ttmv = 0
    if e is not None:
        ed, ev, ef, em = e
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
        ttmv = em
    alpha0 = alpha
    children = []
    m = moves
    deep = depth >= 3
    if deep:
        while m:
            b = m & -m
            m ^= b
            f = flips(me, opp, b)
            nme = me | f | b
            nop = opp ^ f
            sc = WEIGHT[b.bit_length() - 1] - 8 * pc(legal_moves(nop, nme))
            if b == ttmv:
                sc += 100000
            children.append((sc, b, nme, nop))
        children.sort(reverse=True)
    else:
        while m:
            b = m & -m
            m ^= b
            sc = WEIGHT[b.bit_length() - 1]
            if b == ttmv:
                sc += 100000
            children.append((sc, b))
        children.sort(reverse=True)
    best = -INF
    bestmv = 0
    for ch in children:
        if deep:
            _, b, nme, nop = ch
        else:
            _, b = ch
            f = flips(me, opp, b)
            nme = me | f | b
            nop = opp ^ f
        v = -search(nop, nme, depth - 1, -beta, -alpha, False)
        if v > best:
            best = v
            bestmv = b
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    break
    if best <= alpha0:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[key] = (depth, best, flag, bestmv)
    return best


def _name(b):
    i = b.bit_length() - 1
    r, c = divmod(i, 8)
    return chr(97 + c) + str(r + 1)


def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    global TT, NODES, DEADLINE
    start = time.time()
    me = 0
    opp = 0
    for i in np.flatnonzero(np.asarray(you).ravel()):
        me |= 1 << int(i)
    for i in np.flatnonzero(np.asarray(opponent).ravel()):
        opp |= 1 << int(i)
    moves = legal_moves(me, opp)
    if moves == 0:
        return "pass"
    mvlist = []
    m = moves
    while m:
        b = m & -m
        m ^= b
        mvlist.append(b)
    if len(mvlist) == 1:
        return _name(mvlist[0])
    ne = pc(FULL ^ (me | opp))
    TT = {}
    NODES = 0
    DEADLINE = start + 0.6

    children = []
    for b in mvlist:
        f = flips(me, opp, b)
        children.append((WEIGHT[b.bit_length() - 1], b, me | f | b, opp ^ f))
    children.sort(reverse=True)
    best = children[0][1]
    max_depth = max(1, ne)
    depth = 1
    try:
        while depth <= max_depth:
            alpha = -INF
            cur_best = None
            cur_best_score = -INF
            scores = []
            for _, b, nme, nop in children:
                v = -search(nop, nme, depth - 1, -INF, -alpha, False)
                scores.append((v, b, nme, nop))
                if v > cur_best_score:
                    cur_best_score = v
                    cur_best = b
                    if v > alpha:
                        alpha = v
                if cur_best is not None:
                    best = cur_best
            scores.sort(reverse=True)
            children = scores
            best = children[0][1]
            depth += 1
    except Timeout:
        pass
    except Exception:
        pass
    if not (best & moves):
        best = mvlist[0]
    return _name(best)
