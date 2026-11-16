
import time
import random
from operator import itemgetter

OFF = 100
P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6
PVAL = [0, 100, 320, 330, 500, 900, 0]
MATE = 100000
INF = 10 ** 9
MAX_PLY = 64
TIME_BUDGET = 0.5

N_OFF = (-21, -19, -12, -8, 8, 12, 19, 21)
K_OFF = (-11, -10, -9, -1, 1, 9, 10, 11)
B_DIR = (-11, -9, 9, 11)
R_DIR = (-10, -1, 1, 10)
ALL_DIR = B_DIR + R_DIR

SQUARES = [21 + f + 10 * r for r in range(8) for f in range(8)]
RANK = [-1] * 120
FILE = [-1] * 120
SQN = [''] * 120
CMD = [0] * 120
for _r in range(8):
    for _f in range(8):
        _s = 21 + _f + 10 * _r
        RANK[_s] = _r
        FILE[_s] = _f
        SQN[_s] = chr(97 + _f) + str(_r + 1)
        CMD[_s] = max(3 - _f, _f - 4) + max(3 - _r, _r - 4)

PAWN_T = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0]
KNIGHT_T = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50]
BISHOP_T = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20]
ROOK_T = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, 10, 10, 10, 10, 5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    0, 0, 0, 5, 5, 0, 0, 0]
QUEEN_T = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -5, 0, 5, 5, 5, 5, 0, -5,
    0, 0, 5, 5, 5, 5, 0, -5,
    -10, 5, 5, 5, 5, 5, 0, -10,
    -10, 0, 5, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20]
KING_MG_T = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 5, 5, 10, 30, 20]
KING_EG_T = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50]
TABLES = {P: PAWN_T, N: KNIGHT_T, B: BISHOP_T, R: ROOK_T, Q: QUEEN_T, K: KING_MG_T}

PST = [[0] * 120 for _ in range(13)]
ADJ_W = [0] * 120
ADJ_B = [0] * 120
for _pt in range(1, 7):
    _t = TABLES[_pt]
    for _s in SQUARES:
        _f = FILE[_s]
        _r = RANK[_s]
        PST[6 + _pt][_s] = PVAL[_pt] + _t[(7 - _r) * 8 + _f]
        PST[6 - _pt][_s] = -(PVAL[_pt] + _t[_r * 8 + _f])
for _s in SQUARES:
    _f = FILE[_s]
    _r = RANK[_s]
    ADJ_W[_s] = KING_EG_T[(7 - _r) * 8 + _f] - KING_MG_T[(7 - _r) * 8 + _f]
    ADJ_B[_s] = KING_EG_T[_r * 8 + _f] - KING_MG_T[_r * 8 + _f]

_rng = random.Random(918273645)
ZOB = [[_rng.getrandbits(64) for _ in range(120)] for _ in range(13)]
ZOB_SIDE = _rng.getrandbits(64)

PROMO_CH = {Q: 'q', R: 'r', B: 'b', N: 'n'}

TT = {}
KILLERS = [[None, None] for _ in range(MAX_PLY + 2)]
HIST = [[0] * 120 for _ in range(120)]
NODES = 0
DEADLINE = 0.0
PARTIAL = None
SEEN = set()


class Timeout(Exception):
    pass


class Pos:
    __slots__ = ('b', 'side', 'score', 'npm_w', 'npm_b', 'npawn', 'hash', 'wk', 'bk', 'stack')

    def __init__(self, pieces, side):
        b = [OFF] * 120
        for sq in SQUARES:
            b[sq] = 0
        self.score = 0
        self.npm_w = 0
        self.npm_b = 0
        self.npawn = 0
        self.wk = 0
        self.bk = 0
        h = 0
        for s, code in pieces.items():
            try:
                f = ord(s[0]) - 97
                r = int(s[1]) - 1
                if not (0 <= f < 8 and 0 <= r < 8):
                    continue
                col = 1 if code[0] in 'wW' else -1
                pt = 'PNBRQK'.index(code[1].upper()) + 1
            except Exception:
                continue
            sq = 21 + f + 10 * r
            p = col * pt
            b[sq] = p
            self.score += PST[p + 6][sq]
            h ^= ZOB[p + 6][sq]
            if pt == P:
                self.npawn += 1
            elif pt == K:
                if col == 1:
                    self.wk = sq
                else:
                    self.bk = sq
            else:
                if col == 1:
                    self.npm_w += PVAL[pt]
                else:
                    self.npm_b += PVAL[pt]
        self.b = b
        self.side = side
        if side == -1:
            h ^= ZOB_SIDE
        self.hash = h
        self.stack = []

    def gen(self, caps_only=False):
        b = self.b
        side = self.side
        moves = []
        app = moves.append
        if side == 1:
            fwd = 10
            start_rank = 1
            promo_rank = 7
        else:
            fwd = -10
            start_rank = 6
            promo_rank = 0
        for sq in SQUARES:
            p = b[sq]
            if p == 0 or p * side < 0:
                continue
            pt = p * side
            if pt == P:
                to = sq + fwd
                c = b[to]
                if c == 0:
                    if RANK[to] == promo_rank:
                        app((sq, to, Q))
                        app((sq, to, N))
                        if not caps_only:
                            app((sq, to, R))
                            app((sq, to, B))
                    elif not caps_only:
                        app((sq, to, 0))
                        if RANK[sq] == start_rank and b[to + fwd] == 0:
                            app((sq, to + fwd, 0))
                for d in (fwd - 1, fwd + 1):
                    t = sq + d
                    c = b[t]
                    if c != OFF and c * side < 0:
                        if RANK[t] == promo_rank:
                            app((sq, t, Q))
                            app((sq, t, N))
                            if not caps_only:
                                app((sq, t, R))
                                app((sq, t, B))
                        else:
                            app((sq, t, 0))
            elif pt == N or pt == K:
                for o in (N_OFF if pt == N else K_OFF):
                    t = sq + o
                    c = b[t]
                    if c == 0:
                        if not caps_only:
                            app((sq, t, 0))
                    elif c != OFF and c * side < 0:
                        app((sq, t, 0))
            else:
                dirs = B_DIR if pt == B else (R_DIR if pt == R else ALL_DIR)
                for d in dirs:
                    t = sq + d
                    c = b[t]
                    while c == 0:
                        if not caps_only:
                            app((sq, t, 0))
                        t += d
                        c = b[t]
                    if c != OFF and c * side < 0:
                        app((sq, t, 0))
        return moves

    def attacked(self, sq, by):
        b = self.b
        if by == 1:
            if b[sq - 9] == P or b[sq - 11] == P:
                return True
            n, k, bi, ro, q = N, K, B, R, Q
        else:
            if b[sq + 9] == -P or b[sq + 11] == -P:
                return True
            n, k, bi, ro, q = -N, -K, -B, -R, -Q
        for o in N_OFF:
            if b[sq + o] == n:
                return True
        for o in K_OFF:
            if b[sq + o] == k:
                return True
        for d in B_DIR:
            t = sq + d
            c = b[t]
            while c == 0:
                t += d
                c = b[t]
            if c == bi or c == q:
                return True
        for d in R_DIR:
            t = sq + d
            c = b[t]
            while c == 0:
                t += d
                c = b[t]
            if c == ro or c == q:
                return True
        return False

    def in_check(self):
        k = self.wk if self.side == 1 else self.bk
        if not k:
            return False
        return self.attacked(k, -self.side)

    def illegal(self):
        # side that just moved is -self.side
        k = self.bk if self.side == 1 else self.wk
        if not k:
            return False
        return self.attacked(k, self.side)

    def make(self, m):
        frm, to, promo = m
        b = self.b
        piece = b[frm]
        cap = b[to]
        self.stack.append((m, cap, self.score, self.npm_w, self.npm_b, self.npawn, self.hash, self.wk, self.bk))
        h = self.hash ^ ZOB[piece + 6][frm] ^ ZOB[piece + 6][to]
        score = self.score - PST[piece + 6][frm]
        if cap:
            h ^= ZOB[cap + 6][to]
            score -= PST[cap + 6][to]
            ac = cap if cap > 0 else -cap
            if ac == P:
                self.npawn -= 1
            elif ac == K:
                if cap > 0:
                    self.wk = 0
                else:
                    self.bk = 0
            else:
                if cap > 0:
                    self.npm_w -= PVAL[ac]
                else:
                    self.npm_b -= PVAL[ac]
        if promo:
            newp = promo if piece > 0 else -promo
            b[to] = newp
            h ^= ZOB[piece + 6][to] ^ ZOB[newp + 6][to]
            score += PST[newp + 6][to]
            self.npawn -= 1
            if piece > 0:
                self.npm_w += PVAL[promo]
            else:
                self.npm_b += PVAL[promo]
        else:
            b[to] = piece
            score += PST[piece + 6][to]
            if piece == K:
                self.wk = to
            elif piece == -K:
                self.bk = to
        b[frm] = 0
        self.score = score
        self.hash = h ^ ZOB_SIDE
        self.side = -self.side

    def unmake(self):
        m, cap, score, npm_w, npm_b, npawn, h, wk, bk = self.stack.pop()
        frm, to, promo = m
        b = self.b
        self.side = -self.side
        if promo:
            piece = P if self.side == 1 else -P
        else:
            piece = b[to]
        b[frm] = piece
        b[to] = cap
        self.score = score
        self.npm_w = npm_w
        self.npm_b = npm_b
        self.npawn = npawn
        self.hash = h
        self.wk = wk
        self.bk = bk

    def evaluate(self):
        s = self.score
        npm = self.npm_w + self.npm_b
        if self.npawn == 0 and npm <= 330:
            return 0
        wk = self.wk
        bk = self.bk
        if npm <= 1600:
            if wk:
                s += ADJ_W[wk]
            if bk:
                s -= ADJ_B[bk]
        if self.npawn == 0 and wk and bk:
            md = abs(FILE[wk] - FILE[bk]) + abs(RANK[wk] - RANK[bk])
            if self.npm_b == 0 and self.npm_w >= 500:
                s += 47 * CMD[bk] + 16 * (14 - md)
            elif self.npm_w == 0 and self.npm_b >= 500:
                s -= 47 * CMD[wk] + 16 * (14 - md)
        return s if self.side == 1 else -s


def quiesce(pos, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.time() > DEADLINE:
        raise Timeout
    in_check = pos.in_check()
    b = pos.b
    stand = 0
    if in_check:
        if ply >= MAX_PLY:
            return 0
        moves = pos.gen()
        best = -INF
    else:
        stand = pos.evaluate()
        if ply >= MAX_PLY or stand >= beta:
            return stand
        if stand > alpha:
            alpha = stand
        moves = pos.gen(True)
        best = stand
    moves.sort(key=lambda m: PVAL[abs(b[m[1]])] * 10 - PVAL[abs(b[m[0]])] // 10 + PVAL[m[2]], reverse=True)
    legal = 0
    for m in moves:
        if not in_check and not m[2] and stand + PVAL[abs(b[m[1]])] + 200 < alpha:
            continue
        pos.make(m)
        if pos.illegal():
            pos.unmake()
            continue
        legal += 1
        sc = -quiesce(pos, -beta, -alpha, ply + 1)
        pos.unmake()
        if sc > best:
            best = sc
            if sc > alpha:
                alpha = sc
                if sc >= beta:
                    return sc
    if in_check and legal == 0:
        return -MATE + ply
    return best


def search(pos, depth, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.time() > DEADLINE:
        raise Timeout
    if ply >= MAX_PLY:
        return pos.evaluate()
    in_check = pos.in_check()
    if in_check:
        depth += 1
    if depth <= 0:
        return quiesce(pos, alpha, beta, ply)
    if pos.npawn == 0 and pos.npm_w + pos.npm_b <= 330:
        return 0
    tt_move = None
    e = TT.get(pos.hash)
    if e is not None:
        tdepth, tscore, tflag, tmove = e
        tt_move = tmove
        if tdepth >= depth:
            if tflag == 0:
                return tscore
            if tflag == 1 and tscore >= beta:
                return tscore
            if tflag == 2 and tscore <= alpha:
                return tscore
    # null move pruning
    if depth >= 3 and not in_check and ply > 0 and beta < MATE - 2000 and \
            (pos.npm_w if pos.side == 1 else pos.npm_b) > 0:
        pos.side = -pos.side
        pos.hash ^= ZOB_SIDE
        sc = -search(pos, depth - 3, -beta, -beta + 1, ply + 1)
        pos.side = -pos.side
        pos.hash ^= ZOB_SIDE
        if sc >= beta:
            return beta
    moves = pos.gen()
    b = pos.b
    k1, k2 = KILLERS[ply]
    keyed = []
    for m in moves:
        frm, to, promo = m
        if m == tt_move:
            s = 10000000
        else:
            cap = b[to]
            if cap:
                s = 1000000 + PVAL[abs(cap)] * 10 - PVAL[abs(b[frm])] // 10 + PVAL[promo]
            elif promo:
                s = 900000 + PVAL[promo]
            elif m == k1:
                s = 800000
            elif m == k2:
                s = 790000
            else:
                s = HIST[frm][to]
        keyed.append((s, m))
    keyed.sort(key=itemgetter(0), reverse=True)
    alpha_orig = alpha
    best = -INF
    best_move = None
    legal = 0
    for _, m in keyed:
        pos.make(m)
        if pos.illegal():
            pos.unmake()
            continue
        legal += 1
        sc = -search(pos, depth - 1, -beta, -alpha, ply + 1)
        pos.unmake()
        if sc > best:
            best = sc
            best_move = m
            if sc > alpha:
                alpha = sc
                if sc >= beta:
                    if b[m[1]] == 0 and not m[2]:
                        kl = KILLERS[ply]
                        if kl[0] != m:
                            kl[1] = kl[0]
                            kl[0] = m
                        HIST[m[0]][m[1]] += depth * depth
                    break
    if legal == 0:
        return (-MATE + ply) if in_check else 0
    if best <= alpha_orig:
        flag = 2
    elif best >= beta:
        flag = 1
    else:
        flag = 0
    TT[pos.hash] = (depth, best, flag, best_move)
    return best


def root_search(pos, moves, depth):
    global PARTIAL
    alpha = -INF
    beta = INF
    scores = []
    best = -INF
    best_move = None
    for m in moves:
        pos.make(m)
        rep = pos.hash in SEEN
        sc = -search(pos, depth - 1, -beta, -alpha, 1)
        pos.unmake()
        if rep and sc > -MATE + 5000:
            sc -= 25
        scores.append((sc, m))
        if sc > best:
            best = sc
            best_move = m
            PARTIAL = m
            if sc > alpha:
                alpha = sc
    scores.sort(key=lambda x: -x[0])
    return best, best_move, [m for _, m in scores]


def mstr(m):
    frm, to, promo = m
    s = SQN[frm] + SQN[to]
    if promo:
        s += PROMO_CH.get(promo, 'q')
    return s


def policy(pieces, to_play):
    global DEADLINE, NODES, KILLERS, HIST, PARTIAL, TT, SEEN
    start = time.time()
    DEADLINE = start + TIME_BUDGET
    side = 1 if str(to_play).lower().startswith('w') else -1
    pos = Pos(pieces, side)
    pseudo = pos.gen()
    legal = []
    for m in pseudo:
        pos.make(m)
        if not pos.illegal():
            legal.append(m)
        pos.unmake()
    if not legal:
        if pseudo:
            return mstr(pseudo[0])
        return '0000'
    if len(legal) == 1:
        best = legal[0]
        pos.make(best)
        SEEN.add(pos.hash)
        pos.unmake()
        return mstr(best)
    if len(TT) > 400000:
        TT.clear()
    if len(SEEN) > 4000:
        SEEN.clear()
    KILLERS = [[None, None] for _ in range(MAX_PLY + 2)]
    HIST = [[0] * 120 for _ in range(120)]
    NODES = 0
    b = pos.b
    legal.sort(key=lambda m: PVAL[abs(b[m[1]])] * 10 - PVAL[abs(b[m[0]])] // 10 + PVAL[m[2]], reverse=True)
    best = legal[0]
    depth = 1
    while depth <= 40:
        PARTIAL = None
        try:
            sc, bm, legal = root_search(pos, legal, depth)
            if bm is not None:
                best = bm
        except Timeout:
            if PARTIAL is not None:
                best = PARTIAL
            break
        except Exception:
            break
        if abs(sc) >= MATE - 1000:
            break
        if time.time() - start > TIME_BUDGET * 0.6:
            break
        depth += 1
    try:
        pos.stack = []
        pos.make(best)
        SEEN.add(pos.hash)
        pos.unmake()
    except Exception:
        pass
    return mstr(best)
