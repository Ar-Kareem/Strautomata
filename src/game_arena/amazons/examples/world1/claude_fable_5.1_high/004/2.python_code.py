
import time
import numpy as np

ALL = (1 << 36) - 1
COL0 = 0
COL5 = 0
for _r in range(6):
    COL0 |= 1 << (_r * 6)
    COL5 |= 1 << (_r * 6 + 5)
NC0 = ALL & ~COL0
NC5 = ALL & ~COL5

WIN = 10000
INF = 10 ** 9
KAPPA = 0.3
MOBW = 0.15
BUDGET = 0.55

try:
    (5).bit_count()
    pc = int.bit_count
except AttributeError:
    def pc(x):
        return bin(x).count('1')


class TimeUp(Exception):
    pass


_deadline = 0.0
HIST = [{}, {}]


def reach(x, e):
    r = 0
    g = ((x & NC5) << 1) & e
    while g:
        r |= g
        g = ((g & NC5) << 1) & e
    g = ((x & NC0) >> 1) & e
    while g:
        r |= g
        g = ((g & NC0) >> 1) & e
    g = (x << 6) & e
    while g:
        r |= g
        g = (g << 6) & e
    g = (x >> 6) & e
    while g:
        r |= g
        g = (g >> 6) & e
    g = ((x & NC5) << 7) & e
    while g:
        r |= g
        g = ((g & NC5) << 7) & e
    g = ((x & NC0) << 5) & e
    while g:
        r |= g
        g = ((g & NC0) << 5) & e
    g = ((x & NC5) >> 5) & e
    while g:
        r |= g
        g = ((g & NC5) >> 5) & e
    g = ((x & NC0) >> 7) & e
    while g:
        r |= g
        g = ((g & NC0) >> 7) & e
    return r


def king_adj(x):
    a = ((x & NC5) << 1) | ((x & NC0) >> 1)
    b = x | a
    return (a | (b << 6) | (b >> 6)) & ALL & ~x


def gen_moves(mine, theirs, arrows):
    e = ALL & ~(mine | theirs | arrows)
    moves = []
    m = mine
    while m:
        fb = m & -m
        m ^= fb
        e2 = e | fb
        t = reach(fb, e)
        while t:
            tb = t & -t
            t ^= tb
            a = reach(tb, e2 & ~tb)
            while a:
                ab = a & -a
                a ^= ab
                moves.append((fb, tb, ab))
    return moves


def evaluate(mine, theirs, arrows, e):
    mf = reach(mine, e)
    if not mf:
        return -WIN
    of = reach(theirs, e)
    if not of:
        return WIN
    mv = mf
    ov = of
    score = pc(mf & ~of) - pc(of & ~mf) + KAPPA * pc(mf & of)
    mob = pc(mf) - pc(of)
    ml = mf
    ol = of
    while ml or ol:
        if ml:
            ml = reach(ml, e) & ~mv
            mv |= ml
        if ol:
            ol = reach(ol, e) & ~ov
            ov |= ol
        score += pc(ml & ~ov) - pc(ol & ~mv) + KAPPA * pc(ml & ol)
    return score + MOBW * mob


def negamax(mine, theirs, arrows, depth, alpha, beta, side):
    if time.perf_counter() > _deadline:
        raise TimeUp()
    e = ALL & ~(mine | theirs | arrows)
    if depth <= 0:
        return evaluate(mine, theirs, arrows, e)
    moves = gen_moves(mine, theirs, arrows)
    if not moves:
        return -WIN - depth
    hist = HIST[side]
    adj = king_adj(theirs)
    hg = hist.get
    moves.sort(key=lambda mv: hg((mv[1], mv[2]), 0) + (8 if mv[2] & adj else 0), reverse=True)
    best = -INF
    nside = 1 - side
    for fb, tb, ab in moves:
        v = -negamax(theirs, (mine ^ fb) | tb, arrows | ab, depth - 1, -beta, -alpha, nside)
        if v > best:
            best = v
            if v > alpha:
                alpha = v
                if alpha >= beta:
                    k = (tb, ab)
                    hist[k] = hg(k, 0) + depth * depth
                    break
    return best


def fmt(mv):
    fb, tb, ab = mv
    fi = fb.bit_length() - 1
    ti = tb.bit_length() - 1
    ai = ab.bit_length() - 1
    return "%d,%d:%d,%d:%d,%d" % (fi // 6, fi % 6, ti // 6, ti % 6, ai // 6, ai % 6)


def policy(board) -> str:
    global _deadline, HIST
    start = time.perf_counter()
    _deadline = start + BUDGET
    HIST = [{}, {}]

    mine = 0
    theirs = 0
    arrows = 0
    for r in range(6):
        for c in range(6):
            v = int(board[r][c])
            b = 1 << (r * 6 + c)
            if v == 1:
                mine |= b
            elif v == 2:
                theirs |= b
            elif v != 0:
                arrows |= b

    moves = gen_moves(mine, theirs, arrows)
    if not moves:
        return "0,0:0,0:0,0"
    if len(moves) == 1:
        return fmt(moves[0])

    best_mv = moves[0]
    best_v = -INF
    # Depth 1
    scored = []
    try:
        for mv in moves:
            fb, tb, ab = mv
            v = -negamax(theirs, (mine ^ fb) | tb, arrows | ab, 0, -INF, INF, 1)
            scored.append((v, mv))
            if v > best_v:
                best_v = v
                best_mv = mv
    except TimeUp:
        return fmt(best_mv)

    scored.sort(key=lambda x: x[0], reverse=True)
    order = [mv for (_, mv) in scored]

    depth = 2
    while depth <= 60:
        if best_v >= WIN or best_v <= -WIN:
            break
        new_scores = {}
        cur_best = None
        cur_v = -INF
        alpha = -INF
        try:
            for mv in order:
                fb, tb, ab = mv
                v = -negamax(theirs, (mine ^ fb) | tb, arrows | ab, depth - 1, -INF, -alpha, 1)
                new_scores[mv] = v
                if v > cur_v:
                    cur_v = v
                    cur_best = mv
                    if v > alpha:
                        alpha = v
        except TimeUp:
            if cur_best is not None:
                best_mv = cur_best
            break
        best_mv = cur_best
        best_v = cur_v
        order.sort(key=lambda m: new_scores[m], reverse=True)
        depth += 1

    return fmt(best_mv)
