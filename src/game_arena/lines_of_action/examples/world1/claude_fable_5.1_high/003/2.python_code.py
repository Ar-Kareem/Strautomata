
import time

try:
    (0).bit_count()
    def popcount(x):
        return x.bit_count()
except AttributeError:
    def popcount(x):
        return bin(x).count('1')

FULL = (1 << 64) - 1
NOT_A = sum(1 << (r * 8 + c) for r in range(8) for c in range(1, 8))
NOT_H = sum(1 << (r * 8 + c) for r in range(8) for c in range(0, 7))


def nbrs(bb):
    e = (bb & NOT_H) << 1
    w = (bb & NOT_A) >> 1
    h = bb | e | w
    return ((h << 8) | (h >> 8) | e | w) & FULL


PST_ROWS = [
    [-80, -25, -20, -20, -20, -20, -25, -80],
    [-25, 10, 10, 10, 10, 10, 10, -25],
    [-20, 10, 25, 25, 25, 25, 10, -20],
    [-20, 10, 25, 50, 50, 25, 10, -20],
    [-20, 10, 25, 50, 50, 25, 10, -20],
    [-20, 10, 25, 25, 25, 25, 10, -20],
    [-25, 10, 10, 10, 10, 10, 10, -25],
    [-80, -25, -20, -20, -20, -20, -25, -80],
]
PST = [PST_ROWS[r][c] for r in range(8) for c in range(8)]

DIRS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
AXIS_DIRS = [(1, 6), (3, 4), (0, 7), (2, 5)]
LINE = []
MOVEINFO = []
for s in range(64):
    r, c = divmod(s, 8)
    lines = []
    for axis in range(4):
        m = 1 << s
        for d in AXIS_DIRS[axis]:
            dr, dc = DIRS[d]
            rr, cc = r + dr, c + dc
            while 0 <= rr < 8 and 0 <= cc < 8:
                m |= 1 << (rr * 8 + cc)
                rr += dr
                cc += dc
        lines.append(m)
    LINE.append(lines)
    infos = []
    for d in range(8):
        dr, dc = DIRS[d]
        lst = []
        between = 0
        rr, cc = r + dr, c + dc
        while 0 <= rr < 8 and 0 <= cc < 8:
            sq = rr * 8 + cc
            lst.append((sq, 1 << sq, between))
            between |= 1 << sq
            rr += dr
            cc += dc
        infos.append(lst)
    MOVEINFO.append(infos)

INF = 10 ** 9
WIN = 1000000


class Timeout(Exception):
    pass


def gen_moves(me, opp):
    occ = me | opp
    moves = []
    bb = me
    while bb:
        lsb = bb & -bb
        s = lsb.bit_length() - 1
        bb ^= lsb
        lines = LINE[s]
        infos = MOVEINFO[s]
        for axis in range(4):
            cnt = popcount(occ & lines[axis])
            for d in AXIS_DIRS[axis]:
                info = infos[d]
                if cnt <= len(info):
                    to_sq, tb, between = info[cnt - 1]
                    if not (opp & between) and not (me & tb):
                        moves.append((s, to_sq, lsb, tb, opp & tb))
    return moves


def connected(bb):
    if bb == 0:
        return True
    fill = bb & -bb
    while True:
        nf = (fill | nbrs(fill)) & bb
        if nf == fill:
            return fill == bb
        fill = nf


def count_groups(bb):
    g = 0
    while bb:
        fill = bb & -bb
        while True:
            nf = (fill | nbrs(fill)) & bb
            if nf == fill:
                break
            fill = nf
        bb ^= fill
        g += 1
    return g


def min_sum(n):
    if n <= 1:
        return 0
    if n <= 9:
        return n - 1
    return 8 + 2 * (n - 9)


def side_eval(bb):
    n = 0
    sr = 0
    sc = 0
    pst = 0
    sqs = []
    b = bb
    while b:
        lsb = b & -b
        s = lsb.bit_length() - 1
        b ^= lsb
        pst += PST[s]
        sr += s >> 3
        sc += s & 7
        n += 1
        sqs.append(s)
    if n == 0:
        return 0
    cr = sr / n
    cc = sc / n
    dist = 0.0
    for s in sqs:
        dr = abs((s >> 3) - cr)
        dc = abs((s & 7) - cc)
        dist += dr if dr > dc else dc
    conc = dist - min_sum(n)
    groups = count_groups(bb)
    adj = popcount(bb & nbrs(bb))
    return pst - 10 * conc - 40 * (groups - 1) + 8 * adj


def evaluate(me, opp):
    return side_eval(me) - side_eval(opp)


STATE = {'nodes': 0, 'deadline': 0.0, 'iter_best': None}
TT = {}


def order_moves(moves, tt_move):
    keyed = []
    for m in moves:
        k = PST[m[1]] - PST[m[0]]
        if m[4]:
            k += 300
        if tt_move is not None and m == tt_move:
            k += 10000
        keyed.append((-k, m))
    keyed.sort(key=lambda x: x[0])
    return [m for _, m in keyed]


def search(me, opp, depth, alpha, beta, ply):
    STATE['nodes'] += 1
    if (STATE['nodes'] & 63) == 0 and time.perf_counter() > STATE['deadline']:
        raise Timeout()
    key = (me, opp)
    tt = TT.get(key)
    tt_move = None
    if tt is not None:
        tdepth, tscore, tflag, tmove = tt
        tt_move = tmove
        if tdepth >= depth:
            if tflag == 0:
                return tscore
            if tflag == 1 and tscore >= beta:
                return tscore
            if tflag == 2 and tscore <= alpha:
                return tscore
    if depth <= 0:
        return evaluate(me, opp)
    moves = gen_moves(me, opp)
    if not moves:
        return evaluate(me, opp)
    moves = order_moves(moves, tt_move)
    best = -INF
    best_move = None
    a = alpha
    for m in moves:
        fb = m[2]
        tb = m[3]
        nme = (me ^ fb) | tb
        if m[4]:
            nopp = opp ^ tb
            if connected(nme):
                score = WIN - ply
            elif connected(nopp):
                score = -WIN + ply
            else:
                score = -search(nopp, nme, depth - 1, -beta, -a, ply + 1)
        else:
            if connected(nme):
                score = WIN - ply
            else:
                score = -search(opp, nme, depth - 1, -beta, -a, ply + 1)
        if score > best:
            best = score
            best_move = m
        if best > a:
            a = best
        if a >= beta:
            break
    if best >= beta:
        flag = 1
    elif best <= alpha:
        flag = 2
    else:
        flag = 0
    TT[key] = (depth, best, flag, best_move)
    return best


def root_search(me, opp, depth, moves, prev_best):
    ordered = order_moves(moves, prev_best)
    best = -INF
    best_move = None
    a = -INF
    for m in ordered:
        fb = m[2]
        tb = m[3]
        nme = (me ^ fb) | tb
        if m[4]:
            nopp = opp ^ tb
            if connected(nme):
                score = WIN
            elif connected(nopp):
                score = -WIN
            else:
                score = -search(nopp, nme, depth - 1, -INF, -a, 1)
        else:
            if connected(nme):
                score = WIN
            else:
                score = -search(opp, nme, depth - 1, -INF, -a, 1)
        if score > best:
            best = score
            best_move = m
            STATE['iter_best'] = m
        if best > a:
            a = best
    return best, best_move


def fmt(m):
    fr, fc = divmod(m[0], 8)
    tr, tc = divmod(m[1], 8)
    return "%d,%d:%d,%d" % (fr, fc, tr, tc)


def to_bitboards(board):
    me = 0
    opp = 0
    for r in range(8):
        row = board[r]
        for c in range(8):
            v = int(row[c])
            if v == 1:
                me |= 1 << (r * 8 + c)
            elif v == -1:
                opp |= 1 << (r * 8 + c)
    return me, opp


def policy(board) -> str:
    start = time.perf_counter()
    me, opp = to_bitboards(board)
    moves = gen_moves(me, opp)
    if not moves:
        return "0,0:0,0"
    try:
        # immediate win check
        for m in moves:
            nme = (me ^ m[2]) | m[3]
            if connected(nme):
                return fmt(m)
        STATE['deadline'] = start + 0.7
        STATE['nodes'] = 0
        STATE['iter_best'] = None
        TT.clear()
        # quick static ordering fallback
        best_move = order_moves(moves, None)[0]
        depth = 1
        try:
            while depth <= 12:
                STATE['iter_best'] = None
                score, mv = root_search(me, opp, depth, moves, best_move)
                if mv is not None:
                    best_move = mv
                if abs(score) >= WIN - 100:
                    break
                depth += 1
        except Timeout:
            if STATE['iter_best'] is not None:
                best_move = STATE['iter_best']
        return fmt(best_move)
    except Exception:
        return fmt(moves[0])
