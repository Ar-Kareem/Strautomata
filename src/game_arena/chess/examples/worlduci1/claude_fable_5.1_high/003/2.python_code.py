
import time
import random

OFF = 99
INF = 10 ** 9
MATE = 100000
MATE_BOUND = MATE - 2000
MAX_PLY = 60

PTYPE = {'P': 1, 'N': 2, 'B': 3, 'R': 4, 'Q': 5, 'K': 6}
PROMO_CH = {2: 'n', 3: 'b', 4: 'r', 5: 'q'}
VAL = [0, 100, 320, 330, 500, 900, 0]
ORD13 = [1500, 900, 500, 330, 320, 100, 0, 100, 320, 330, 500, 900, 1500]
PHASE_INC = [0, 4, 2, 1, 1, 0, 0, 0, 1, 1, 2, 4, 0]

KNIGHT_DIRS = (-21, -19, -12, -8, 8, 12, 19, 21)
BISHOP_DIRS = (-11, -9, 9, 11)
ROOK_DIRS = (-10, -1, 1, 10)
KING_DIRS = (-11, -10, -9, -1, 1, 9, 10, 11)

SQUARES = [21 + r * 10 + f for r in range(8) for f in range(8)]


def sq_of(alg):
    f = ord(alg[0]) - 97
    r = int(alg[1]) - 1
    return 21 + (7 - r) * 10 + f


def alg_of(sq):
    r = 7 - (sq - 21) // 10
    f = (sq - 21) % 10
    return chr(97 + f) + str(r + 1)


PAWN_MG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5, 5, 10, 25, 25, 10, 5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, -5, -10, 0, 0, -10, -5, 5,
    5, 10, 10, -20, -20, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0]
PAWN_EG = [
    0, 0, 0, 0, 0, 0, 0, 0,
    90, 90, 90, 90, 90, 90, 90, 90,
    50, 50, 50, 50, 50, 50, 50, 50,
    30, 30, 30, 30, 30, 30, 30, 30,
    15, 15, 15, 15, 15, 15, 15, 15,
    5, 5, 5, 5, 5, 5, 5, 5,
    0, 0, 0, 0, 0, 0, 0, 0,
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
KING_MG = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20, 20, 0, 0, 0, 0, 20, 20,
    20, 30, 10, 0, 0, 10, 30, 20]
KING_EG = [
    -50, -40, -30, -20, -20, -30, -40, -50,
    -30, -20, -10, 0, 0, -10, -20, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 30, 40, 40, 30, -10, -30,
    -30, -10, 20, 30, 30, 20, -10, -30,
    -30, -30, 0, 0, 0, 0, -30, -30,
    -50, -30, -30, -30, -30, -30, -30, -50]

PST_MG = [[0] * 120 for _ in range(13)]
PST_EG = [[0] * 120 for _ in range(13)]


def _build(tmg, teg, val, ptype):
    for color in (1, -1):
        amg = [0] * 120
        aeg = [0] * 120
        for sq in SQUARES:
            row = (sq - 21) // 10
            col = (sq - 21) % 10
            if color == 1:
                i = row * 8 + col
            else:
                i = (7 - row) * 8 + col
            amg[sq] = color * (val + tmg[i])
            aeg[sq] = color * (val + teg[i])
        PST_MG[6 + color * ptype] = amg
        PST_EG[6 + color * ptype] = aeg


_build(PAWN_MG, PAWN_EG, 100, 1)
_build(KNIGHT_T, KNIGHT_T, 320, 2)
_build(BISHOP_T, BISHOP_T, 330, 3)
_build(ROOK_T, ROOK_T, 500, 4)
_build(QUEEN_T, QUEEN_T, 900, 5)
_build(KING_MG, KING_EG, 0, 6)

_rng = random.Random(123456789)
ZOB = [[_rng.getrandbits(64) for _ in range(120)] for _ in range(13)]
SIDE_KEY = _rng.getrandbits(64)

TT = {}
SEEN = set()
LAST_COUNT = [0]


class Timeout(Exception):
    pass


class Engine:
    def __init__(self, pieces, side):
        b = [OFF] * 120
        for sq in SQUARES:
            b[sq] = 0
        self.ksq = {1: 0, -1: 0}
        self.mat = {1: 0, -1: 0}
        self.pawns = {1: 0, -1: 0}
        mg = eg = ph = 0
        h = 0
        for alg, code in pieces.items():
            try:
                sq = sq_of(alg)
                c = 1 if code[0] == 'w' else -1
                t = PTYPE[code[1]]
            except Exception:
                continue
            p = c * t
            b[sq] = p
            mg += PST_MG[p + 6][sq]
            eg += PST_EG[p + 6][sq]
            ph += PHASE_INC[p + 6]
            h ^= ZOB[p + 6][sq]
            if t == 6:
                self.ksq[c] = sq
            elif t == 1:
                self.pawns[c] += 1
            else:
                self.mat[c] += VAL[t]
        if side == -1:
            h ^= SIDE_KEY
        self.board = b
        self.side = side
        self.mg = mg
        self.eg = eg
        self.phase = ph
        self.hash = h
        self.nodes = 0
        self.deadline = 0.0
        self.path = [h]
        self.root_side = side
        self.killers = [[None, None] for _ in range(MAX_PLY + 4)]
        self.hist = {}

    # ---------- attack detection ----------
    def attacked(self, sq, by):
        b = self.board
        n = 2 * by
        for d in KNIGHT_DIRS:
            if b[sq + d] == n:
                return True
        k = 6 * by
        for d in KING_DIRS:
            if b[sq + d] == k:
                return True
        if by == 1:
            if b[sq + 9] == 1 or b[sq + 11] == 1:
                return True
        else:
            if b[sq - 9] == -1 or b[sq - 11] == -1:
                return True
        r = 4 * by
        q = 5 * by
        for d in ROOK_DIRS:
            t = sq + d
            x = b[t]
            while x == 0:
                t += d
                x = b[t]
            if x == r or x == q:
                return True
        bi = 3 * by
        for d in BISHOP_DIRS:
            t = sq + d
            x = b[t]
            while x == 0:
                t += d
                x = b[t]
            if x == bi or x == q:
                return True
        return False

    def king_attacked(self, color):
        k = self.ksq[color]
        if not k:
            return False
        return self.attacked(k, -color)

    # ---------- move generation ----------
    def gen(self, caps_only=False, all_promos=False):
        b = self.board
        side = self.side
        moves = []
        if side == 1:
            elo, ehi = -6, -1
            fwd = -10
            plo, phi = 21, 28
            slo, shi = 81, 88
        else:
            elo, ehi = 1, 6
            fwd = 10
            plo, phi = 91, 98
            slo, shi = 31, 38
        promos = (5, 2, 4, 3) if all_promos else (5, 2)
        for sq in SQUARES:
            p = b[sq]
            if p == 0 or p * side < 0:
                continue
            t = p * side
            if t == 1:
                to = sq + fwd
                if plo <= to <= phi:
                    if b[to] == 0:
                        for pr in promos:
                            moves.append((sq, to, pr))
                    for d in (fwd - 1, fwd + 1):
                        x = b[sq + d]
                        if elo <= x <= ehi:
                            for pr in promos:
                                moves.append((sq, sq + d, pr))
                else:
                    if not caps_only and b[to] == 0:
                        moves.append((sq, to, 0))
                        if slo <= sq <= shi and b[to + fwd] == 0:
                            moves.append((sq, to + fwd, 0))
                    for d in (fwd - 1, fwd + 1):
                        x = b[sq + d]
                        if elo <= x <= ehi:
                            moves.append((sq, sq + d, 0))
            elif t == 2 or t == 6:
                dirs = KNIGHT_DIRS if t == 2 else KING_DIRS
                for d in dirs:
                    to = sq + d
                    x = b[to]
                    if x == 0:
                        if not caps_only:
                            moves.append((sq, to, 0))
                    elif elo <= x <= ehi:
                        moves.append((sq, to, 0))
            else:
                if t == 3:
                    dirs = BISHOP_DIRS
                elif t == 4:
                    dirs = ROOK_DIRS
                else:
                    dirs = KING_DIRS
                for d in dirs:
                    to = sq + d
                    x = b[to]
                    while x == 0:
                        if not caps_only:
                            moves.append((sq, to, 0))
                        to += d
                        x = b[to]
                    if elo <= x <= ehi:
                        moves.append((sq, to, 0))
        return moves

    # ---------- make / unmake ----------
    def make(self, m):
        frm, to, promo = m
        b = self.board
        p = b[frm]
        cap = b[to]
        side = self.side
        undo = (frm, to, p, cap, self.mg, self.eg, self.phase, self.hash,
                self.mat[1], self.mat[-1], self.pawns[1], self.pawns[-1])
        np_ = promo * side if promo else p
        b[frm] = 0
        b[to] = np_
        mg = self.mg - PST_MG[p + 6][frm] + PST_MG[np_ + 6][to]
        eg = self.eg - PST_EG[p + 6][frm] + PST_EG[np_ + 6][to]
        h = self.hash ^ ZOB[p + 6][frm] ^ ZOB[np_ + 6][to] ^ SIDE_KEY
        ph = self.phase
        if cap:
            mg -= PST_MG[cap + 6][to]
            eg -= PST_EG[cap + 6][to]
            h ^= ZOB[cap + 6][to]
            ph -= PHASE_INC[cap + 6]
            ct = cap if cap > 0 else -cap
            if ct == 1:
                self.pawns[-side] -= 1
            elif ct != 6:
                self.mat[-side] -= VAL[ct]
        if promo:
            ph += PHASE_INC[np_ + 6]
            self.pawns[side] -= 1
            self.mat[side] += VAL[promo]
        if p == 6 * side:
            self.ksq[side] = to
        self.mg = mg
        self.eg = eg
        self.phase = ph
        self.hash = h
        self.side = -side
        return undo

    def unmake(self, u):
        frm, to, p, cap, mg, eg, ph, h, mw, mb, pw, pb = u
        b = self.board
        b[frm] = p
        b[to] = cap
        side = -self.side
        self.side = side
        if p == 6 * side:
            self.ksq[side] = frm
        self.mg = mg
        self.eg = eg
        self.phase = ph
        self.hash = h
        self.mat[1] = mw
        self.mat[-1] = mb
        self.pawns[1] = pw
        self.pawns[-1] = pb

    # ---------- evaluation ----------
    def evaluate(self):
        ph = self.phase
        if ph > 24:
            ph = 24
        s = (self.mg * ph + self.eg * (24 - ph)) // 24
        mw = self.mat[1]
        mb = self.mat[-1]
        pw = self.pawns[1]
        pb = self.pawns[-1]
        if pw == 0 and pb == 0 and mw < 400 and mb < 400:
            return 0
        if pb == 0 and mw - mb >= 400 and self.ksq[1] and self.ksq[-1]:
            lk = self.ksq[-1]
            wk = self.ksq[1]
            lf = (lk - 21) % 10
            lr = (lk - 21) // 10
            wf = (wk - 21) % 10
            wr = (wk - 21) // 10
            cd = max(3 - lf if lf < 4 else lf - 4, 3 - lr if lr < 4 else lr - 4)
            dist = abs(lf - wf) + abs(lr - wr)
            s += 10 * cd + 4 * (14 - dist)
        elif pw == 0 and mb - mw >= 400 and self.ksq[1] and self.ksq[-1]:
            lk = self.ksq[1]
            wk = self.ksq[-1]
            lf = (lk - 21) % 10
            lr = (lk - 21) // 10
            wf = (wk - 21) % 10
            wr = (wk - 21) // 10
            cd = max(3 - lf if lf < 4 else lf - 4, 3 - lr if lr < 4 else lr - 4)
            dist = abs(lf - wf) + abs(lr - wr)
            s -= 10 * cd + 4 * (14 - dist)
        return s if self.side == 1 else -s

    # ---------- ordering ----------
    def order(self, moves, tt_move, ply):
        b = self.board
        killers = self.killers[ply]
        hist = self.hist
        side = self.side
        k0 = killers[0]
        k1 = killers[1]

        def key(m):
            if m == tt_move:
                return 100000000
            cap = b[m[1]]
            if cap:
                return 1000000 + ORD13[cap + 6] * 10 - ORD13[b[m[0]] + 6]
            if m[2]:
                return 1000000 + (900 if m[2] == 5 else 0)
            if m == k0:
                return 100001
            if m == k1:
                return 100000
            return hist.get((side, m[0], m[1]), 0)

        moves.sort(key=key, reverse=True)

    # ---------- search ----------
    def search(self, depth, alpha, beta, ply, allow_null):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.time() > self.deadline:
            raise Timeout()
        if ply >= MAX_PLY:
            return self.evaluate()
        h = self.hash
        if ply >= 2:
            if self.side == self.root_side and h in SEEN:
                return 0
            path = self.path
            i = ply - 4
            while i >= 0:
                if path[i] == h:
                    return 0
                i -= 2
        in_chk = self.king_attacked(self.side)
        if depth <= 0:
            if in_chk:
                depth = 1
            else:
                return self.qsearch(alpha, beta, ply)
        tte = TT.get(h)
        tt_move = None
        if tte is not None:
            tdepth, tscore, tflag, tt_move = tte
            if tdepth >= depth:
                if tscore > MATE_BOUND:
                    tscore -= ply
                elif tscore < -MATE_BOUND:
                    tscore += ply
                if tflag == 0:
                    return tscore
                if tflag == 1 and tscore >= beta:
                    return tscore
                if tflag == 2 and tscore <= alpha:
                    return tscore
        if allow_null and depth >= 3 and not in_chk and self.mat[self.side] > 0 and beta < MATE_BOUND:
            self.side = -self.side
            self.hash ^= SIDE_KEY
            self.path.append(self.hash)
            try:
                sc = -self.search(depth - 3, -beta, -beta + 1, ply + 1, False)
            finally:
                self.path.pop()
                self.side = -self.side
                self.hash ^= SIDE_KEY
            if sc >= beta:
                return beta
        fut = False
        if depth <= 2 and not in_chk and -MATE_BOUND < alpha < MATE_BOUND:
            static = self.evaluate()
            if static + 130 * depth <= alpha:
                fut = True
        moves = self.gen()
        self.order(moves, tt_move, ply)
        b = self.board
        side = self.side
        best = -INF
        best_move = None
        legal = 0
        alpha0 = alpha
        killers = self.killers[ply]
        for m in moves:
            cap = b[m[1]]
            quiet = (cap == 0 and m[2] == 0)
            if fut and quiet and legal > 0:
                continue
            u = self.make(m)
            if self.king_attacked(side):
                self.unmake(u)
                continue
            legal += 1
            self.path.append(self.hash)
            try:
                if legal == 1:
                    score = -self.search(depth - 1, -beta, -alpha, ply + 1, True)
                else:
                    r = 1 if (depth >= 3 and quiet and not in_chk and legal > 3 and m != killers[0] and m != killers[1]) else 0
                    score = -self.search(depth - 1 - r, -alpha - 1, -alpha, ply + 1, True)
                    if score > alpha and (r or score < beta):
                        score = -self.search(depth - 1, -beta, -alpha, ply + 1, True)
            finally:
                self.path.pop()
                self.unmake(u)
            if score > best:
                best = score
                best_move = m
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        if quiet:
                            if killers[0] != m:
                                killers[1] = killers[0]
                                killers[0] = m
                            key = (side, m[0], m[1])
                            self.hist[key] = self.hist.get(key, 0) + depth * depth
                        break
        if legal == 0:
            return -(MATE - ply) if in_chk else 0
        flag = 1 if best >= beta else (2 if best <= alpha0 else 0)
        s = best
        if s > MATE_BOUND:
            s += ply
        elif s < -MATE_BOUND:
            s -= ply
        TT[h] = (depth, s, flag, best_move)
        return best

    def qsearch(self, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 511) == 0 and time.time() > self.deadline:
            raise Timeout()
        stand = self.evaluate()
        if stand >= beta:
            return stand
        if ply >= MAX_PLY:
            return stand
        if stand > alpha:
            alpha = stand
        moves = self.gen(True)
        b = self.board
        moves.sort(key=lambda m: ORD13[b[m[1]] + 6] * 10 - ORD13[b[m[0]] + 6] + (900 if m[2] else 0), reverse=True)
        side = self.side
        best = stand
        for m in moves:
            cap = b[m[1]]
            if cap and not m[2] and stand + ORD13[cap + 6] + 200 < alpha:
                continue
            u = self.make(m)
            if self.king_attacked(side):
                self.unmake(u)
                continue
            try:
                score = -self.qsearch(-beta, -alpha, ply + 1)
            finally:
                self.unmake(u)
            if score > best:
                best = score
                if score > alpha:
                    alpha = score
                    if alpha >= beta:
                        break
        return best

    def root_legal(self):
        moves = self.gen(False, True)
        legal = []
        side = self.side
        for m in moves:
            u = self.make(m)
            ok = not self.king_attacked(side)
            self.unmake(u)
            if ok:
                legal.append(m)
        return legal


def uci(m):
    return alg_of(m[0]) + alg_of(m[1]) + PROMO_CH.get(m[2], '')


def root_search(eng, legal, deadline):
    eng.deadline = deadline
    b = eng.board
    root_moves = list(legal)
    root_moves.sort(key=lambda m: ORD13[b[m[1]] + 6] * 10 + (900 if m[2] == 5 else 0), reverse=True)
    best_move = root_moves[0]
    depth = 1
    while depth < 60:
        alpha = -INF
        beta = INF
        iter_best = None
        scores = []
        try:
            for m in root_moves:
                u = eng.make(m)
                eng.path.append(eng.hash)
                try:
                    if iter_best is None:
                        score = -eng.search(depth - 1, -beta, -alpha, 1, True)
                    else:
                        score = -eng.search(depth - 1, -alpha - 1, -alpha, 1, True)
                        if score > alpha:
                            score = -eng.search(depth - 1, -beta, -alpha, 1, True)
                finally:
                    eng.path.pop()
                    eng.unmake(u)
                scores.append((score, m))
                if score > alpha:
                    alpha = score
                    iter_best = m
        except Timeout:
            if iter_best is not None:
                best_move = iter_best
            break
        if iter_best is not None:
            best_move = iter_best
        scores.sort(key=lambda x: x[0], reverse=True)
        root_moves = [m for s, m in scores]
        if alpha > MATE_BOUND:
            break
        depth += 1
    return best_move


def policy(pieces: dict, to_play: str) -> str:
    start = time.time()
    deadline = start + 0.70
    side = 1 if to_play == 'white' else -1
    try:
        count = len(pieces)
        if count > LAST_COUNT[0]:
            SEEN.clear()
            TT.clear()
        LAST_COUNT[0] = count
        if len(TT) > 1500000:
            TT.clear()
    except Exception:
        pass
    try:
        eng = Engine(pieces, side)
        legal = eng.root_legal()
    except Exception:
        # last-resort fallback (should never happen)
        for sq, code in pieces.items():
            if code[0] == ('w' if side == 1 else 'b') and code[1] == 'K':
                f = ord(sq[0]) - 97
                r = int(sq[1]) - 1
                nf = f + 1 if f < 7 else f - 1
                return sq + chr(97 + nf) + str(r + 1)
        return 'a1a1'
    if not legal:
        return 'a1a1'
    fallback = uci(legal[0])
    if len(legal) == 1:
        return fallback
    try:
        SEEN.add(eng.hash)
        best = root_search(eng, legal, deadline)
        if best in legal:
            return uci(best)
        return fallback
    except Exception:
        return fallback
