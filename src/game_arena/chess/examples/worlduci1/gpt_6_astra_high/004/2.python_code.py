
import time
import random

# Mailbox board: a1=21, h1=28, a8=91, h8=98.
SQUARES = tuple(21 + f + 10 * r for r in range(8) for f in range(8))
VALID = frozenset(SQUARES)
ND = (-21, -19, -12, -8, 8, 12, 19, 21)
BD = (-11, -9, 9, 11)
RD = (-10, -1, 1, 10)
KD = BD + RD
KNIGHTS = {s: tuple(s + d for d in ND if s + d in VALID) for s in SQUARES}
KINGS = {s: tuple(s + d for d in KD if s + d in VALID) for s in SQUARES}
COORD = {s: chr(97 + s % 10 - 1) + str(s // 10 - 1) for s in SQUARES}

MG_VALUE = (0, 82, 337, 365, 477, 1025, 0)
EG_VALUE = (0, 94, 281, 297, 512, 936, 0)
VALUE = (0, 100, 320, 335, 510, 1000, 20000)
PHASE = (0, 0, 1, 1, 2, 4, 0)
INF = 32000
MATE = 30000
EP_FLAG = 1 << 17

# Tables are listed from rank eight to rank one, from White's perspective.
_MG_TEXT = (
    "",
    """
      0 0 0 0 0 0 0 0
      98 134 61 95 68 126 34 -11
      -6 7 26 31 65 56 25 -20
      -14 13 6 21 23 12 17 -23
      -27 -2 -5 12 17 6 10 -25
      -26 -4 -4 -10 3 3 33 -12
      -35 -1 -20 -23 -15 24 38 -22
      0 0 0 0 0 0 0 0
    """,
    """
      -167 -89 -34 -49 61 -97 -15 -107
      -73 -41 72 36 23 62 7 -17
      -47 60 37 65 84 129 73 44
      -9 17 19 53 37 69 18 22
      -13 4 16 13 28 19 21 -8
      -23 -9 12 10 19 17 25 -16
      -29 -53 -12 -3 -1 18 -14 -19
      -105 -21 -58 -33 -17 -28 -19 -23
    """,
    """
      -29 4 -82 -37 -25 -42 7 -8
      -26 16 -18 -13 30 59 18 -47
      -16 37 43 40 35 50 37 -2
      -4 5 19 50 37 37 7 -2
      -6 13 13 26 34 12 10 4
      0 15 15 15 14 27 18 10
      4 15 16 0 7 21 33 1
      -33 -3 -14 -21 -13 -12 -39 -21
    """,
    """
      32 42 32 51 63 9 31 43
      27 32 58 62 80 67 26 44
      -5 19 26 36 17 45 61 16
      -24 -11 7 26 24 35 -8 -20
      -36 -26 -12 -1 9 -7 6 -23
      -45 -25 -16 -17 3 0 -5 -33
      -44 -16 -20 -9 -1 11 -6 -71
      -19 -13 1 17 16 7 -37 -26
    """,
    """
      -28 0 29 12 59 44 43 45
      -24 -39 -5 1 -16 57 28 54
      -13 -17 7 8 29 56 47 57
      -27 -27 -16 -16 -1 17 -2 1
      -9 -26 -9 -10 -2 -4 3 -3
      -14 2 -11 -2 -5 2 14 5
      -35 -8 11 2 8 15 -3 1
      -1 -18 -9 10 -15 -25 -31 -50
    """,
    """
      -65 23 16 -15 -56 -34 2 13
      29 -1 -20 -7 -8 -4 -38 -29
      -9 24 2 -16 -20 6 22 -22
      -17 -20 -12 -27 -30 -25 -14 -36
      -49 -1 -27 -39 -46 -44 -33 -51
      -14 -14 -22 -46 -44 -30 -15 -27
      1 7 -8 -64 -43 -16 9 8
      -15 36 12 -54 8 -28 24 14
    """,
)
_EG_TEXT = (
    "",
    """
      0 0 0 0 0 0 0 0
      178 173 158 134 147 132 165 187
      94 100 85 67 56 53 82 84
      32 24 13 5 -2 4 17 17
      13 9 -3 -7 -7 -8 3 -1
      4 7 -6 1 0 -5 -1 -8
      13 8 8 10 13 0 2 -7
      0 0 0 0 0 0 0 0
    """,
    """
      -58 -38 -13 -28 -31 -27 -63 -99
      -25 -8 -25 -2 -9 -25 -24 -52
      -24 -20 10 9 -1 -9 -19 -41
      -17 3 22 22 22 11 8 -18
      -18 -6 16 25 16 17 4 -18
      -23 -3 -1 15 10 -3 -20 -22
      -42 -20 -10 -5 -2 -20 -23 -44
      -29 -51 -23 -15 -22 -18 -50 -64
    """,
    """
      -14 -21 -11 -8 -7 -9 -17 -24
      -8 -4 7 -12 -3 -13 -4 -14
      2 -8 0 -1 -2 6 0 4
      -3 9 12 9 14 10 3 2
      -6 3 13 19 7 10 -3 -9
      -12 -3 8 10 13 3 -7 -15
      -14 -18 -7 -1 4 -9 -15 -27
      -23 -9 -23 -5 -9 -16 -5 -17
    """,
    """
      13 10 18 15 12 12 8 5
      11 13 13 11 -3 3 8 3
      7 7 7 5 4 -3 -5 -3
      4 3 13 1 2 1 -1 2
      3 5 8 4 -5 -6 -8 -11
      -4 0 -5 -1 -7 -12 -8 -16
      -6 -6 0 2 -9 -9 -11 -3
      -9 2 3 -1 -5 -13 4 -20
    """,
    """
      -9 22 22 27 27 19 10 20
      -17 20 32 41 58 25 30 0
      -20 6 9 49 47 35 19 9
      3 22 24 45 57 40 57 36
      -18 28 19 47 31 34 39 23
      -16 -27 15 6 9 17 10 5
      -22 -23 -30 -16 -16 -23 -36 -32
      -33 -28 -22 -43 -5 -32 -20 -41
    """,
    """
      -74 -35 -18 -18 -11 15 4 -17
      -12 17 14 17 17 38 23 11
      10 17 23 15 20 45 44 13
      -8 22 24 27 26 33 26 3
      -18 -4 21 24 27 23 9 -11
      -19 -3 11 21 23 16 7 -9
      -27 -11 4 13 14 4 -5 -17
      -53 -34 -21 -11 -28 -14 -24 -43
    """,
)
_MG_RAW = [()] + [tuple(map(int, text.split())) for text in _MG_TEXT[1:]]
_EG_RAW = [()] + [tuple(map(int, text.split())) for text in _EG_TEXT[1:]]
MG = [[0] * 120 for _ in range(13)]
EG = [[0] * 120 for _ in range(13)]
for _p in range(1, 7):
    for _s in SQUARES:
        _f = _s % 10 - 1
        _r = _s // 10 - 2
        for _side in (1, -1):
            _i = (7 - _r if _side == 1 else _r) * 8 + _f
            MG[6 + _side * _p][_s] = _side * (MG_VALUE[_p] + _MG_RAW[_p][_i])
            EG[6 + _side * _p][_s] = _side * (EG_VALUE[_p] + _EG_RAW[_p][_i])

_rng = random.Random(724193)
Z = [[_rng.getrandbits(64) for _ in range(120)] for _ in range(13)]
Z[6] = [0] * 120
ZEP = [_rng.getrandbits(64) for _ in range(120)]
ZEP[0] = 0
ZTURN = _rng.getrandbits(64)


class _Timeout(Exception):
    pass


def _uci(move):
    fr = move & 127
    to = (move >> 7) & 127
    promotion = (move >> 14) & 7
    return COORD[fr] + COORD[to] + ("  nbrq"[promotion] if promotion else "")


def _distance(a, b):
    return max(abs(a % 10 - b % 10), abs(a // 10 - b // 10))


class _Engine:
    def __init__(self, pieces, side, deadline):
        self.b = [7] * 120
        for s in SQUARES:
            self.b[s] = 0
        self.kings = [0, 0]
        self.count = [0] * 13
        self.mg = self.eg = self.phase = 0
        self.key = self.pawnkey = 0
        types = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6}
        for square, code in pieces.items():
            s = 21 + ord(square[0]) - 97 + 10 * (int(square[1]) - 1)
            p = types[code[1]] * (1 if code[0] == "w" else -1)
            self.b[s] = p
            self.count[p + 6] += 1
            self.mg += MG[p + 6][s]
            self.eg += EG[p + 6][s]
            self.phase += PHASE[abs(p)]
            self.key ^= Z[p + 6][s]
            if abs(p) == 1:
                self.pawnkey ^= Z[p + 6][s]
            elif abs(p) == 6:
                self.kings[p < 0] = s
        self.ep = 0
        self.side = side
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.pawn_cache = {}
        self.path = set()
        self.killers = [[0, 0] for _ in range(90)]
        self.history = [[0] * 16384 for _ in range(2)]
        self.root_moves = []
        self.root_best = 0

    def attacked(self, s, side):
        b = self.b
        if b[s - 9 * side] == side or b[s - 11 * side] == side:
            return True
        n = 2 * side
        for t in KNIGHTS[s]:
            if b[t] == n:
                return True
        k = 6 * side
        for t in KINGS[s]:
            if b[t] == k:
                return True
        bishop, rook, queen = 3 * side, 4 * side, 5 * side
        for d in BD:
            t = s + d
            while b[t] == 0:
                t += d
            if b[t] == bishop or b[t] == queen:
                return True
        for d in RD:
            t = s + d
            while b[t] == 0:
                t += d
            if b[t] == rook or b[t] == queen:
                return True
        return False

    def generate(self, side, captures=False):
        b = self.b
        moves = []
        add = moves.append
        enemy_king = -6 * side
        for fr in SQUARES:
            p = b[fr]
            if p * side <= 0:
                continue
            ap = abs(p)
            if ap == 1:
                step = 10 * side
                to = fr + step
                if b[to] == 0:
                    promotion = to >= 91 if side == 1 else to <= 28
                    base = fr | (to << 7)
                    if promotion:
                        for pr in (5, 2, 4, 3):
                            add(base | (pr << 14))
                    elif not captures:
                        add(base)
                        if (fr // 10 == (3 if side == 1 else 8)
                                and b[to + step] == 0):
                            add(fr | ((to + step) << 7))
                for d in (step - 1, step + 1):
                    to = fr + d
                    target = b[to]
                    if target != 7 and target * side < 0 and target != enemy_king:
                        base = fr | (to << 7)
                        if (to >= 91 if side == 1 else to <= 28):
                            for pr in (5, 2, 4, 3):
                                add(base | (pr << 14))
                        else:
                            add(base)
                    elif self.ep and to == self.ep:
                        add(fr | (to << 7) | EP_FLAG)
            elif ap == 2 or ap == 6:
                targets = KNIGHTS[fr] if ap == 2 else KINGS[fr]
                for to in targets:
                    target = b[to]
                    if target == 0:
                        if not captures:
                            add(fr | (to << 7))
                    elif target * side < 0 and target != enemy_king:
                        add(fr | (to << 7))
            else:
                dirs = BD if ap == 3 else RD if ap == 4 else KD
                for d in dirs:
                    to = fr + d
                    while b[to] == 0:
                        if not captures:
                            add(fr | (to << 7))
                        to += d
                    target = b[to]
                    if target != 7 and target * side < 0 and target != enemy_king:
                        add(fr | (to << 7))
        return moves

    def make(self, move):
        b = self.b
        fr = move & 127
        to = (move >> 7) & 127
        promotion = (move >> 14) & 7
        p = b[fr]
        side = 1 if p > 0 else -1
        cs = to - 10 * side if move & EP_FLAG else to
        captured = b[cs]
        newp = side * promotion if promotion else p
        undo = (p, captured, cs, self.ep, self.key, self.pawnkey,
                self.mg, self.eg, self.phase)

        self.key ^= ZEP[self.ep] ^ Z[p + 6][fr] ^ Z[newp + 6][to]
        if captured:
            self.key ^= Z[captured + 6][cs]
            self.count[captured + 6] -= 1
        if abs(p) == 1:
            self.pawnkey ^= Z[p + 6][fr]
            if not promotion:
                self.pawnkey ^= Z[p + 6][to]
        if abs(captured) == 1:
            self.pawnkey ^= Z[captured + 6][cs]
        if promotion:
            self.count[p + 6] -= 1
            self.count[newp + 6] += 1

        self.mg += MG[newp + 6][to] - MG[p + 6][fr] - MG[captured + 6][cs]
        self.eg += EG[newp + 6][to] - EG[p + 6][fr] - EG[captured + 6][cs]
        self.phase += PHASE[abs(newp)] - PHASE[abs(p)] - PHASE[abs(captured)]
        b[fr] = 0
        b[cs] = 0
        b[to] = newp
        if abs(p) == 6:
            self.kings[side < 0] = to
        self.ep = (fr + to) // 2 if abs(p) == 1 and abs(to - fr) == 20 else 0
        self.key ^= ZEP[self.ep]
        return undo

    def unmake(self, move, undo):
        fr = move & 127
        to = (move >> 7) & 127
        promotion = (move >> 14) & 7
        p, captured, cs, ep, key, pk, mg, eg, phase = undo
        if promotion:
            self.count[self.b[to] + 6] -= 1
            self.count[p + 6] += 1
        if captured:
            self.count[captured + 6] += 1
        self.b[to] = 0
        self.b[fr] = p
        self.b[cs] = captured
        if abs(p) == 6:
            self.kings[p < 0] = fr
        self.ep, self.key, self.pawnkey = ep, key, pk
        self.mg, self.eg, self.phase = mg, eg, phase

    def pawn_terms(self):
        cached = self.pawn_cache.get(self.pawnkey)
        if cached is not None:
            return cached
        b = self.b
        pawns = ([s for s in SQUARES if b[s] == 1],
                 [s for s in SQUARES if b[s] == -1])
        files = [[0] * 8, [0] * 8]
        masks = [0, 0]
        for c in (0, 1):
            for s in pawns[c]:
                f = s % 10 - 1
                files[c][f] += 1
                masks[c] |= 1 << f
        mg = eg = 0
        passed = []
        for c, sign in ((0, 1), (1, -1)):
            own, enemy = pawns[c], pawns[1 - c]
            for n in files[c]:
                if n > 1:
                    mg -= sign * 12 * (n - 1)
                    eg -= sign * 21 * (n - 1)
            for s in own:
                f = s % 10 - 1
                rank = s // 10 - 2
                rr = rank if sign == 1 else 7 - rank
                left = f > 0 and files[c][f - 1]
                right = f < 7 and files[c][f + 1]
                if not left and not right:
                    mg -= sign * 12
                    eg -= sign * 15
                if b[s - 9 * sign] == sign or b[s - 11 * sign] == sign:
                    mg += sign * 8
                    eg += sign * 7
                is_passed = True
                for t in enemy:
                    if abs(t % 10 - s % 10) <= 1 and (t // 10 - s // 10) * sign > 0:
                        is_passed = False
                        break
                if is_passed:
                    for t in own:
                        if t != s and t % 10 == s % 10 and (t - s) * sign > 0:
                            is_passed = False
                            break
                if is_passed:
                    mg += sign * (0, 0, 5, 12, 24, 43, 70, 0)[rr]
                    eg += sign * (0, 3, 9, 20, 40, 75, 125, 0)[rr]
                    passed.append((sign, s, rr))
        result = (mg, eg, masks[0], masks[1], tuple(passed))
        self.pawn_cache[self.pawnkey] = result
        return result

    def evaluate(self, side):
        c = self.count
        if not (c[5] or c[7] or c[2] or c[10] or c[1] or c[11]):
            if c[3] + c[9] + c[4] + c[8] <= 1:
                return 0
        pm, pe, wm, bm, passed = self.pawn_terms()
        mg = self.mg + pm
        eg = self.eg + pe
        if c[9] >= 2:
            mg += 28
            eg += 42
        if c[3] >= 2:
            mg -= 28
            eg -= 42

        b = self.b
        for sign, king, mask, enemy_queens in (
                (1, self.kings[0], wm, c[1]),
                (-1, self.kings[1], bm, c[11])):
            if enemy_queens:
                f = king % 10 - 1
                shield = 0
                for df in (-1, 0, 1):
                    if 0 <= f + df < 8:
                        if not (mask & (1 << (f + df))):
                            shield -= 14 if df == 0 else 8
                        t = king + df + sign * 10
                        if 0 <= t < 120 and b[t] == sign:
                            shield += 9
                        else:
                            t += sign * 10
                            if 0 <= t < 120 and b[t] == sign:
                                shield += 4
                mg += sign * shield

        for sign, s, rr in passed:
            if 2 <= rr <= 6:
                target = s + sign * 10
                ownking = self.kings[sign < 0]
                enemyking = self.kings[sign > 0]
                eg += sign * 4 * rr * (
                    _distance(enemyking, target) - _distance(ownking, target))
        phase = min(24, max(0, self.phase))
        score = (mg * phase + eg * (24 - phase)) // 24
        return side * score + 12

    def order(self, moves, side, ply, ttmove=0):
        b = self.b
        history = self.history[side < 0]
        killer1, killer2 = self.killers[ply]
        table = MG if self.phase > 12 else EG

        def score(m):
            if m == ttmove:
                return 2000000000
            fr = m & 127
            to = (m >> 7) & 127
            pr = (m >> 14) & 7
            victim = 1 if m & EP_FLAG else abs(b[to])
            if victim or pr:
                return (1000000 + 16 * VALUE[victim] - VALUE[abs(b[fr])]
                        + (VALUE[pr] * 12 if pr else 0))
            if m == killer1:
                return 900000
            if m == killer2:
                return 899000
            p = b[fr] + 6
            return history[fr * 128 + to] + side * (table[p][to] - table[p][fr])

        moves.sort(key=score, reverse=True)
        return moves

    def tick(self):
        self.nodes += 1
        if self.nodes & 127 == 0 and time.perf_counter() >= self.deadline:
            raise _Timeout

    def qsearch(self, alpha, beta, side, ply):
        self.tick()
        if ply >= 76:
            return self.evaluate(side)
        key = self.key ^ (ZTURN if side < 0 else 0)
        if key in self.path:
            return 0
        check = self.attacked(self.kings[side < 0], -side)
        if check:
            stand = -INF
        else:
            stand = self.evaluate(side)
            if stand >= beta:
                return stand
            if stand > alpha:
                alpha = stand

        moves = self.order(self.generate(side, not check), side, ply)
        self.path.add(key)
        best = stand
        legal = 0
        for move in moves:
            to = (move >> 7) & 127
            promotion = (move >> 14) & 7
            victim = 1 if move & EP_FLAG else abs(self.b[to])
            undo = self.make(move)
            if self.attacked(self.kings[side < 0], -side):
                self.unmake(move, undo)
                continue
            legal += 1
            if (not check and not promotion and self.phase > 0
                    and stand + VALUE[victim] + 220 < alpha
                    and not self.attacked(self.kings[side > 0], side)):
                self.unmake(move, undo)
                continue
            value = -self.qsearch(-beta, -alpha, -side, ply + 1)
            self.unmake(move, undo)
            if value > best:
                best = value
            if value > alpha:
                alpha = value
                if alpha >= beta:
                    break
        self.path.remove(key)
        if check and not legal:
            return -MATE + ply
        return best

    def search(self, depth, alpha, beta, side, ply, allow_null=True):
        if depth <= 0:
            return self.qsearch(alpha, beta, side, ply)
        self.tick()
        if ply >= 76:
            return self.evaluate(side)
        key = self.key ^ (ZTURN if side < 0 else 0)
        if key in self.path:
            return 0
        alpha = max(alpha, -MATE + ply)
        beta = min(beta, MATE - ply - 1)
        if alpha >= beta:
            return alpha
        original_alpha = alpha
        check = self.attacked(self.kings[side < 0], -side)
        if check:
            depth += 1

        entry = self.tt.get(key)
        ttmove = 0
        if entry is not None:
            td, ts, flag, ttmove = entry
            if ts > 29000:
                ts -= ply
            elif ts < -29000:
                ts += ply
            if td >= depth and ply:
                if flag == 0 or (flag == 1 and ts >= beta) or (flag == 2 and ts <= alpha):
                    return ts

        static = self.evaluate(side) if not check else -INF
        narrow = beta - alpha == 1
        if (ply and narrow and not check and depth <= 3
                and abs(beta) < 28000 and static - 100 * depth >= beta):
            return static

        self.path.add(key)
        if (allow_null and ply and narrow and not check and depth >= 3
                and static >= beta and abs(beta) < 28000):
            c = self.count
            if c[6 + side * 2] + c[6 + side * 3] + c[6 + side * 4] + c[6 + side * 5]:
                old_ep, old_key = self.ep, self.key
                self.key ^= ZEP[self.ep]
                self.ep = 0
                reduction = 2 + depth // 5
                value = -self.search(depth - 1 - reduction, -beta, -beta + 1,
                                     -side, ply + 1, False)
                self.ep, self.key = old_ep, old_key
                if value >= beta:
                    self.path.remove(key)
                    return value if value < 29000 else beta

        moves = list(self.root_moves) if ply == 0 else self.generate(side)
        self.order(moves, side, ply, ttmove)
        best = -INF
        bestmove = 0
        legal = 0

        for move in moves:
            fr = move & 127
            to = (move >> 7) & 127
            quiet = not self.b[to] and not (move & EP_FLAG) and not ((move >> 14) & 7)
            undo = self.make(move)
            if self.attacked(self.kings[side < 0], -side):
                self.unmake(move, undo)
                continue
            legal += 1
            nd = depth - 1
            if legal == 1:
                value = -self.search(nd, -beta, -alpha, -side, ply + 1)
            else:
                reduction = 0
                if (ply and quiet and not check and depth >= 3 and legal >= 4
                        and not self.attacked(self.kings[side > 0], side)):
                    reduction = 1 + (depth >= 6 and legal >= 8)
                value = -self.search(max(0, nd - reduction), -alpha - 1, -alpha,
                                     -side, ply + 1)
                if reduction and value > alpha:
                    value = -self.search(nd, -alpha - 1, -alpha, -side, ply + 1)
                if alpha < value < beta:
                    value = -self.search(nd, -beta, -alpha, -side, ply + 1)
            self.unmake(move, undo)

            if value > best:
                best = value
                bestmove = move
                if ply == 0:
                    self.root_best = move
            if value > alpha:
                alpha = value
                if alpha >= beta:
                    if quiet:
                        killers = self.killers[ply]
                        if move != killers[0]:
                            killers[1] = killers[0]
                            killers[0] = move
                        hist = self.history[side < 0]
                        idx = fr * 128 + to
                        hist[idx] = min(700000, hist[idx] + 32 * depth * depth)
                    break

        self.path.remove(key)
        if not legal:
            best = -MATE + ply if check else 0
        flag = 2 if best <= original_alpha else 1 if best >= beta else 0
        stored = best + ply if best > 29000 else best - ply if best < -29000 else best
        self.tt[key] = (depth, stored, flag, bestmove)
        return best

    def legal_roots(self):
        result = []
        for move in self.generate(self.side):
            undo = self.make(move)
            legal = not self.attacked(self.kings[self.side < 0], -self.side)
            self.unmake(move, undo)
            if legal:
                result.append(move)
        return result

    def forced_ep(self):
        # Only used when no ordinary move exists. In a nonterminal position,
        # an en-passant move must then be the available action.
        side = self.side
        pawn_rank = 6 if side == 1 else 5
        for s in SQUARES:
            if self.b[s] != side or s // 10 != pawn_rank:
                continue
            for df in (-1, 1):
                enemy = s + df
                target = enemy + 10 * side
                origin = enemy + 20 * side
                if (self.b[enemy] == -side and self.b[target] == 0
                        and self.b[origin] == 0):
                    move = s | (target << 7) | EP_FLAG
                    undo = self.make(move)
                    legal = not self.attacked(self.kings[side < 0], -side)
                    self.unmake(move, undo)
                    if legal:
                        return move
        return 0


def policy(pieces: dict[str, str], to_play: str) -> str:
    deadline = time.perf_counter() + 0.88
    side = 1 if to_play == "white" else -1
    engine = _Engine(pieces, side, deadline)
    roots = engine.legal_roots()

    if not roots:
        ep = engine.forced_ep()
        if ep:
            return _uci(ep)
        # A checkmated or stalemated board has no legal action.
        raise ValueError("The supplied position has no legal move.")

    engine.root_moves = roots
    engine.order(roots, side, 0)
    best = roots[0]
    if len(roots) == 1:
        return _uci(best)

    engine.root_best = best
    for depth in range(1, 65):
        if time.perf_counter() >= deadline:
            break
        try:
            score = engine.search(depth, -INF, INF, side, 0)
        except _Timeout:
            break
        best = engine.root_best
        if abs(score) > 29000:
            break

    return _uci(best)
