
import time
import random
from operator import itemgetter

BUDGET = 0.6
MAXPLY = 60
MATE = 100000
INF = 10 ** 9
VALUE = [0, 100, 320, 330, 500, 900, 0]
PIECE_CODE = {'wP': 1, 'wN': 2, 'wB': 3, 'wR': 4, 'wQ': 5, 'wK': 6,
              'bP': -1, 'bN': -2, 'bB': -3, 'bR': -4, 'bQ': -5, 'bK': -6}
PROMO_CHAR = {5: 'q', 4: 'r', 3: 'b', 2: 'n'}

KNIGHT_OFF = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)]

N_MOVES = []
K_MOVES = []
RAYS = []
for _sq in range(64):
    _f = _sq & 7
    _r = _sq >> 3
    N_MOVES.append([(_r + dr) * 8 + _f + df for df, dr in KNIGHT_OFF
                    if 0 <= _f + df < 8 and 0 <= _r + dr < 8])
    K_MOVES.append([(_r + dr) * 8 + _f + df for df, dr in DIRS
                    if 0 <= _f + df < 8 and 0 <= _r + dr < 8])
    _rays = []
    for df, dr in DIRS:
        ray = []
        nf, nr = _f + df, _r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            ray.append(nr * 8 + nf)
            nf += df
            nr += dr
        _rays.append(ray)
    RAYS.append(_rays)

SLIDE_DIRS = {3: (4, 5, 6, 7), 4: (0, 1, 2, 3), 5: (0, 1, 2, 3, 4, 5, 6, 7)}

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
KING_MID_T = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20]
KING_END_T = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -50, -50]


def _build(table, value):
    w = [0] * 64
    b = [0] * 64
    for sq in range(64):
        f = sq & 7
        r = sq >> 3
        w[sq] = value + table[(7 - r) * 8 + f]
        b[sq] = -(value + table[r * 8 + f])
    return w, b


PSTV = [None] * 13
for _t, _tab in ((1, PAWN_T), (2, KNIGHT_T), (3, BISHOP_T), (4, ROOK_T), (5, QUEEN_T)):
    _w, _b = _build(_tab, VALUE[_t])
    PSTV[_t] = _w
    PSTV[_t + 6] = _b
PSTV[0] = [0] * 64
PSTV[6] = [0] * 64
PSTV[12] = [0] * 64
KMID_W, KMID_B = _build(KING_MID_T, 0)
KEND_W, KEND_B = _build(KING_END_T, 0)

NPMV = [0] * 13
for _t in (2, 3, 4, 5):
    NPMV[_t] = VALUE[_t]
    NPMV[_t + 6] = VALUE[_t]

_rng = random.Random(1234567)
ZOB = [[_rng.getrandbits(64) for _ in range(64)] for _ in range(13)]
ZOB_SIDE = _rng.getrandbits(64)

DIST = [[max(abs((a & 7) - (b & 7)), abs((a >> 3) - (b >> 3))) for b in range(64)] for a in range(64)]
CENTER = [max(abs(2 * (sq & 7) - 7), abs(2 * (sq >> 3) - 7)) for sq in range(64)]

SEEN = {}


def sq_index(s):
    return (ord(s[1]) - 49) * 8 + (ord(s[0]) - 97)


def sq_name(i):
    return chr(97 + (i & 7)) + chr(49 + (i >> 3))


def mstr(m):
    s = sq_name(m[0]) + sq_name(m[1])
    if m[2]:
        s += PROMO_CHAR[m[2]]
    return s


class Timeout(Exception):
    pass


class Engine:
    def __init__(self, board, side):
        self.board = board
        self.side = side
        sc = 0
        npm = 0
        h = 0
        wk = 0
        bk = 0
        for sq in range(64):
            p = board[sq]
            if p:
                pi = p if p > 0 else 6 - p
                sc += PSTV[pi][sq]
                npm += NPMV[pi]
                h ^= ZOB[pi][sq]
                if p == 6:
                    wk = sq
                elif p == -6:
                    bk = sq
        if side == -1:
            h ^= ZOB_SIDE
        self.score = sc
        self.npm = npm
        self.hash = h
        self.wk = wk
        self.bk = bk
        self.tt = {}
        self.killers = [[None, None] for _ in range(MAXPLY + 4)]
        self.history = [0] * 4096
        self.nodes = 0
        self.deadline = 0.0

    def attacked(self, sq, by):
        b = self.board
        kn = 2 * by
        for t in N_MOVES[sq]:
            if b[t] == kn:
                return True
        kk = 6 * by
        for t in K_MOVES[sq]:
            if b[t] == kk:
                return True
        f = sq & 7
        if by == 1:
            if sq >= 9 and f > 0 and b[sq - 9] == 1:
                return True
            if sq >= 7 and f < 7 and b[sq - 7] == 1:
                return True
        else:
            if sq <= 56 and f > 0 and b[sq + 7] == -1:
                return True
            if sq <= 54 and f < 7 and b[sq + 9] == -1:
                return True
        rook = 4 * by
        queen = 5 * by
        bishop = 3 * by
        rays = RAYS[sq]
        for d in (0, 1, 2, 3):
            for t in rays[d]:
                q = b[t]
                if q:
                    if q == rook or q == queen:
                        return True
                    break
        for d in (4, 5, 6, 7):
            for t in rays[d]:
                q = b[t]
                if q:
                    if q == bishop or q == queen:
                        return True
                    break
        return False

    def gen(self, caps_only=False):
        b = self.board
        side = self.side
        moves = []
        app = moves.append
        for fr in range(64):
            p = b[fr]
            if p * side <= 0:
                continue
            t = p if p > 0 else -p
            if t == 1:
                r = fr >> 3
                f = fr & 7
                if side == 1:
                    to = fr + 8
                    promo_rank = (r == 6)
                    start = (r == 1)
                else:
                    to = fr - 8
                    promo_rank = (r == 1)
                    start = (r == 6)
                if b[to] == 0:
                    if promo_rank:
                        app((fr, to, 5))
                        app((fr, to, 2))
                        if not caps_only:
                            app((fr, to, 4))
                            app((fr, to, 3))
                    elif not caps_only:
                        app((fr, to, 0))
                        if start:
                            to2 = to + 8 if side == 1 else to - 8
                            if b[to2] == 0:
                                app((fr, to2, 0))
                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        tc = to + df
                        if b[tc] * side < 0:
                            if promo_rank:
                                app((fr, tc, 5))
                                app((fr, tc, 2))
                                if not caps_only:
                                    app((fr, tc, 4))
                                    app((fr, tc, 3))
                            else:
                                app((fr, tc, 0))
            elif t == 2 or t == 6:
                tbl = N_MOVES[fr] if t == 2 else K_MOVES[fr]
                for to in tbl:
                    q = b[to]
                    if q == 0:
                        if not caps_only:
                            app((fr, to, 0))
                    elif q * side < 0:
                        app((fr, to, 0))
            else:
                rays = RAYS[fr]
                for d in SLIDE_DIRS[t]:
                    for to in rays[d]:
                        q = b[to]
                        if q == 0:
                            if not caps_only:
                                app((fr, to, 0))
                        elif q * side < 0:
                            app((fr, to, 0))
                            break
                        else:
                            break
        return moves

    def make(self, m):
        b = self.board
        fr, to, promo = m
        p = b[fr]
        cap = b[to]
        side = self.side
        st = (p, cap, self.score, self.npm, self.hash, self.wk, self.bk)
        sc = self.score
        h = self.hash
        npm = self.npm
        pi = p if p > 0 else 6 - p
        h ^= ZOB[pi][fr]
        if cap:
            ci = cap if cap > 0 else 6 - cap
            h ^= ZOB[ci][to]
            sc -= PSTV[ci][to]
            npm -= NPMV[ci]
        if promo:
            newp = promo * side
            ni = newp if newp > 0 else 6 - newp
            b[to] = newp
            sc += PSTV[ni][to] - PSTV[pi][fr]
            npm += NPMV[ni]
            h ^= ZOB[ni][to]
        else:
            b[to] = p
            sc += PSTV[pi][to] - PSTV[pi][fr]
            h ^= ZOB[pi][to]
            if p == 6:
                self.wk = to
            elif p == -6:
                self.bk = to
        b[fr] = 0
        h ^= ZOB_SIDE
        self.score = sc
        self.npm = npm
        self.hash = h
        self.side = -side
        return st

    def unmake(self, m, st):
        fr, to, promo = m
        p, cap, self.score, self.npm, self.hash, self.wk, self.bk = st
        b = self.board
        b[fr] = p
        b[to] = cap
        self.side = -self.side

    def evaluate(self):
        s = self.score
        npm = self.npm
        wk = self.wk
        bk = self.bk
        if npm > 1600:
            s += KMID_W[wk] + KMID_B[bk]
        else:
            s += KEND_W[wk] + KEND_B[bk]
            if npm <= 1300 and (s > 300 or s < -300):
                if s > 0:
                    lk = bk
                    kk = wk
                else:
                    lk = wk
                    kk = bk
                bonus = 5 * CENTER[lk] + 4 * (14 - DIST[kk][lk])
                s += bonus if s > 0 else -bonus
        return s

    def quiesce(self, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()
        side = self.side
        stand = self.evaluate() * side
        if stand >= beta or ply >= MAXPLY:
            return stand
        if alpha < stand:
            alpha = stand
        best = stand
        b = self.board
        moves = self.gen(True)
        scored = []
        for m in moves:
            cap = b[m[1]]
            s = 10 * VALUE[cap if cap > 0 else -cap] - VALUE[abs(b[m[0]])]
            if m[2]:
                s += VALUE[m[2]]
            scored.append((s, m))
        scored.sort(key=itemgetter(0), reverse=True)
        for _, m in scored:
            cap = b[m[1]]
            if not m[2] and stand + VALUE[cap if cap > 0 else -cap] + 200 <= alpha:
                continue
            st = self.make(m)
            if self.attacked(self.wk if side == 1 else self.bk, -side):
                self.unmake(m, st)
                continue
            sc = -self.quiesce(-beta, -alpha, ply + 1)
            self.unmake(m, st)
            if sc > best:
                best = sc
                if sc > alpha:
                    alpha = sc
                    if alpha >= beta:
                        break
        return best

    def search(self, depth, alpha, beta, ply, null_ok):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.perf_counter() > self.deadline:
            raise Timeout()
        side = self.side
        if ply > 0 and self.hash in SEEN:
            return 0
        if ply >= MAXPLY:
            return self.evaluate() * side
        in_check = self.attacked(self.wk if side == 1 else self.bk, -side)
        if in_check and ply < 40:
            depth += 1
        if depth <= 0:
            return self.quiesce(alpha, beta, ply)
        alpha0 = alpha
        h = self.hash
        ttmove = None
        e = self.tt.get(h)
        if e is not None:
            edepth, escore, eflag, ttmove = e
            if edepth >= depth and ply > 0:
                if eflag == 0:
                    return escore
                if eflag == 1 and escore >= beta:
                    return escore
                if eflag == 2 and escore <= alpha:
                    return escore
        # null move pruning
        if null_ok and not in_check and depth >= 3 and ply > 0 and self.npm > 1300:
            self.side = -side
            self.hash ^= ZOB_SIDE
            sc = -self.search(depth - 3, -beta, -beta + 1, ply + 1, False)
            self.side = side
            self.hash ^= ZOB_SIDE
            if sc >= beta:
                return beta
        b = self.board
        kl = self.killers[ply]
        hist = self.history
        moves = self.gen(False)
        scored = []
        for m in moves:
            fr, to, promo = m
            if m == ttmove:
                s = 10000000
            else:
                cap = b[to]
                if cap:
                    s = 1000000 + 10 * VALUE[cap if cap > 0 else -cap] - VALUE[abs(b[fr])]
                    if promo:
                        s += VALUE[promo]
                elif promo:
                    s = 500000 + VALUE[promo]
                elif m == kl[0]:
                    s = 800000
                elif m == kl[1]:
                    s = 790000
                else:
                    s = hist[fr * 64 + to]
            scored.append((s, m))
        scored.sort(key=itemgetter(0), reverse=True)
        best = -INF
        bestm = None
        legal = 0
        for _, m in scored:
            fr, to, promo = m
            cap = b[to]
            st = self.make(m)
            if self.attacked(self.wk if side == 1 else self.bk, -side):
                self.unmake(m, st)
                continue
            legal += 1
            if depth >= 3 and legal > 4 and not in_check and cap == 0 and promo == 0:
                sc = -self.search(depth - 2, -alpha - 1, -alpha, ply + 1, True)
                if sc > alpha:
                    sc = -self.search(depth - 1, -beta, -alpha, ply + 1, True)
            else:
                sc = -self.search(depth - 1, -beta, -alpha, ply + 1, True)
            self.unmake(m, st)
            if sc > best:
                best = sc
                bestm = m
                if sc > alpha:
                    alpha = sc
                    if alpha >= beta:
                        if cap == 0 and promo == 0:
                            if kl[0] != m:
                                kl[1] = kl[0]
                                kl[0] = m
                            hist[fr * 64 + to] += depth * depth
                        break
        if legal == 0:
            return (-MATE + ply) if in_check else 0
        if best >= beta:
            flag = 1
        elif best <= alpha0:
            flag = 2
        else:
            flag = 0
        self.tt[h] = (depth, best, flag, bestm)
        return best

    def legal_moves(self):
        side = self.side
        res = []
        for m in self.gen(False):
            st = self.make(m)
            if not self.attacked(self.wk if side == 1 else self.bk, -side):
                res.append(m)
            self.unmake(m, st)
        return res

    def think(self, legal, deadline):
        self.deadline = deadline
        b = self.board

        def key(m):
            cap = b[m[1]]
            s = 0
            if cap:
                s = 10 * VALUE[cap if cap > 0 else -cap] - VALUE[abs(b[m[0]])]
            if m[2]:
                s += VALUE[m[2]]
            return s

        legal = sorted(legal, key=key, reverse=True)
        best = legal[0]
        for depth in range(1, 40):
            alpha = -INF
            cur_best = None
            cur_score = -INF
            moves = [best] + [m for m in legal if m != best]
            try:
                for m in moves:
                    st = self.make(m)
                    sc = -self.search(depth - 1, -INF, -alpha, 1, True)
                    self.unmake(m, st)
                    if sc > cur_score:
                        cur_score = sc
                        cur_best = m
                        if sc > alpha:
                            alpha = sc
            except Timeout:
                if cur_best is not None:
                    best = cur_best
                break
            best = cur_best
            if cur_score >= MATE - 1000:
                break
            if time.perf_counter() > deadline:
                break
        return best


def _fallback(board, side):
    # only possible remaining legal move type: en passant
    for fr in range(64):
        p = board[fr]
        if p != side:
            continue
        r = fr >> 3
        f = fr & 7
        if (side == 1 and r == 4) or (side == -1 and r == 3):
            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8:
                    adj = fr + df
                    if board[adj] == -side:
                        to = fr + df + (8 if side == 1 else -8)
                        if board[to] == 0:
                            return sq_name(fr) + sq_name(to)
    try:
        eng = Engine(board[:], side)
        pm = eng.gen(False)
        if pm:
            return mstr(pm[0])
    except Exception:
        pass
    return 'a1a1'


def _is_start_position(pieces):
    if len(pieces) != 32:
        return False
    for sq, code in pieces.items():
        if code[1] == 'P' and sq[1] not in '27':
            return False
    return pieces.get('e1') == 'wK' and pieces.get('e8') == 'bK'


def policy(pieces, to_play):
    start = time.perf_counter()
    try:
        board = [0] * 64
        for s, code in pieces.items():
            board[sq_index(s)] = PIECE_CODE[code]
        side = 1 if str(to_play).lower().startswith('w') else -1
        if _is_start_position(pieces):
            SEEN.clear()
        eng = Engine(board, side)
        legal = eng.legal_moves()
        if not legal:
            return _fallback(board, side)
        if len(legal) == 1:
            SEEN[eng.hash] = SEEN.get(eng.hash, 0) + 1
            return mstr(legal[0])
        root_hash = eng.hash
        try:
            m = eng.think(legal, start + BUDGET)
        except Exception:
            b = board
            m = max(legal, key=lambda mv: (VALUE[abs(b[mv[1]])] if b[mv[1]] else 0) + (VALUE[mv[2]] if mv[2] else 0))
        if m not in legal:
            m = legal[0]
        SEEN[root_hash] = SEEN.get(root_hash, 0) + 1
        if len(SEEN) > 5000:
            SEEN.clear()
        return mstr(m)
    except Exception:
        try:
            board = [0] * 64
            for s, code in pieces.items():
                board[sq_index(s)] = PIECE_CODE[code]
            side = 1 if str(to_play).lower().startswith('w') else -1
            eng = Engine(board, side)
            legal = eng.legal_moves()
            if legal:
                return mstr(legal[0])
            return _fallback(board, side)
        except Exception:
            return 'a1a1'
