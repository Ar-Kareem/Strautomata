
import time
import random

# Piece types: pawn, knight, bishop, rook, queen, king.
P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6
INF, MATE = 32000, 30000
CASTLE, EP = 1 << 17, 1 << 18
SQUARES = tuple(r * 16 + f for r in range(8) for f in range(8))
KNIGHT = (33, 31, 18, 14, -14, -18, -31, -33)
BISHOP = (15, 17, -15, -17)
ROOK = (1, -1, 16, -16)
KING = BISHOP + ROOK
VALUE = (0, 100, 320, 335, 500, 975, 20000)
PHASE = (0, 0, 1, 1, 2, 4, 0)
MG_VALUE = (0, 82, 337, 365, 477, 1025, 0)
EG_VALUE = (0, 94, 281, 297, 512, 936, 0)

# Tables are listed from rank eight to rank one, from White's viewpoint.
MG_RAW = (
    (),
    (
         0,  0,  0,  0,  0,  0,  0,  0,
        98,134, 61, 95, 68,126, 34,-11,
        -6,  7, 26, 31, 65, 56, 25,-20,
       -14, 13,  6, 21, 23, 12, 17,-23,
       -27, -2, -5, 12, 17,  6, 10,-25,
       -26, -4, -4,-10,  3,  3, 33,-12,
       -35, -1,-20,-23,-15, 24, 38,-22,
         0,  0,  0,  0,  0,  0,  0,  0,
    ),
    (
      -167,-89,-34,-49, 61,-97,-15,-107,
       -73,-41, 72, 36, 23, 62,  7,-17,
       -47, 60, 37, 65, 84,129, 73, 44,
        -9, 17, 19, 53, 37, 69, 18, 22,
       -13,  4, 16, 13, 28, 19, 21, -8,
       -23, -9, 12, 10, 19, 17, 25,-16,
       -29,-53,-12, -3, -1, 18,-14,-19,
      -105,-21,-58,-33,-17,-28,-19,-23,
    ),
    (
       -29,  4,-82,-37,-25,-42,  7, -8,
       -26, 16,-18,-13, 30, 59, 18,-47,
       -16, 37, 43, 40, 35, 50, 37, -2,
        -4,  5, 19, 50, 37, 37,  7, -2,
        -6, 13, 13, 26, 34, 12, 10,  4,
         0, 15, 15, 15, 14, 27, 18, 10,
         4, 15, 16,  0,  7, 21, 33,  1,
       -33, -3,-14,-21,-13,-12,-39,-21,
    ),
    (
        32, 42, 32, 51, 63,  9, 31, 43,
        27, 32, 58, 62, 80, 67, 26, 44,
        -5, 19, 26, 36, 17, 45, 61, 16,
       -24,-11,  7, 26, 24, 35, -8,-20,
       -36,-26,-12, -1,  9, -7,  6,-23,
       -45,-25,-16,-17,  3,  0, -5,-33,
       -44,-16,-20, -9, -1, 11, -6,-71,
       -19,-13,  1, 17, 16,  7,-37,-26,
    ),
    (
       -28,  0, 29, 12, 59, 44, 43, 45,
       -24,-39, -5,  1,-16, 57, 28, 54,
       -13,-17,  7,  8, 29, 56, 47, 57,
       -27,-27,-16,-16, -1, 17, -2,  1,
        -9,-26, -9,-10, -2, -4,  3, -3,
       -14,  2,-11, -2, -5,  2, 14,  5,
       -35, -8, 11,  2,  8, 15, -3,  1,
        -1,-18, -9, 10,-15,-25,-31,-50,
    ),
    (
       -65, 23, 16,-15,-56,-34,  2, 13,
        29, -1,-20, -7, -8, -4,-38,-29,
        -9, 24,  2,-16,-20,  6, 22,-22,
       -17,-20,-12,-27,-30,-25,-14,-36,
       -49, -1,-27,-39,-46,-44,-33,-51,
       -14,-14,-22,-46,-44,-30,-15,-27,
         1,  7, -8,-64,-43,-16,  9,  8,
       -15, 36, 12,-54,  8,-28, 24, 14,
    ),
)

EG_RAW = (
    (),
    (
         0,  0,  0,  0,  0,  0,  0,  0,
       178,173,158,134,147,132,165,187,
        94,100, 85, 67, 56, 53, 82, 84,
        32, 24, 13,  5, -2,  4, 17, 17,
        13,  9, -3, -7, -7, -8,  3, -1,
         4,  7, -6,  1,  0, -5, -1, -8,
        13,  8,  8, 10, 13,  0,  2, -7,
         0,  0,  0,  0,  0,  0,  0,  0,
    ),
    (
       -58,-38,-13,-28,-31,-27,-63,-99,
       -25, -8,-25, -2, -9,-25,-24,-52,
       -24,-20, 10,  9, -1, -9,-19,-41,
       -17,  3, 22, 22, 22, 11,  8,-18,
       -18, -6, 16, 25, 16, 17,  4,-18,
       -23, -3, -1, 15, 10, -3,-20,-22,
       -42,-20,-10, -5, -2,-20,-23,-44,
       -29,-51,-23,-15,-22,-18,-50,-64,
    ),
    (
       -14,-21,-11, -8, -7, -9,-17,-24,
        -8, -4,  7,-12, -3,-13, -4,-14,
         2, -8,  0, -1, -2,  6,  0,  4,
        -3,  9, 12,  9, 14, 10,  3,  2,
        -6,  3, 13, 19,  7, 10, -3, -9,
       -12, -3,  8, 10, 13,  3, -7,-15,
       -14,-18, -7, -1,  4, -9,-15,-27,
       -23, -9,-23, -5, -9,-16, -5,-17,
    ),
    (
        13, 10, 18, 15, 12, 12,  8,  5,
        11, 13, 13, 11, -3,  3,  8,  3,
         7,  7,  7,  5,  4, -3, -5, -3,
         4,  3, 13,  1,  2,  1, -1,  2,
         3,  5,  8,  4, -5, -6, -8,-11,
        -4,  0, -5, -1, -7,-12, -8,-16,
        -6, -6,  0,  2, -9, -9,-11, -3,
        -9,  2,  3, -1, -5,-13,  4,-20,
    ),
    (
        -9, 22, 22, 27, 27, 19, 10, 20,
       -17, 20, 32, 41, 58, 25, 30,  0,
       -20,  6,  9, 49, 47, 35, 19,  9,
         3, 22, 24, 45, 57, 40, 57, 36,
       -18, 28, 19, 47, 31, 34, 39, 23,
       -16,-27, 15,  6,  9, 17, 10,  5,
       -22,-23,-30,-16,-16,-23,-36,-32,
       -33,-28,-22,-43, -5,-32,-20,-41,
    ),
    (
       -74,-35,-18,-18,-11, 15,  4,-17,
       -12, 17, 14, 17, 17, 38, 23, 11,
        10, 17, 23, 15, 20, 45, 44, 13,
        -8, 22, 24, 27, 26, 33, 26,  3,
       -18, -4, 21, 24, 27, 23,  9,-11,
       -19, -3, 11, 21, 23, 16,  7, -9,
       -27,-11,  4, 13, 14,  4, -5,-17,
       -53,-34,-21,-11,-28,-14,-24,-43,
    ),
)

MG = [[0] * 128 for _ in range(13)]
EG = [[0] * 128 for _ in range(13)]
for _side in (1, -1):
    for _p in range(1, 7):
        for _s in SQUARES:
            _r, _f = _s >> 4, _s & 7
            _i = (7 - _r if _side == 1 else _r) * 8 + _f
            MG[_side * _p + 6][_s] = _side * (
                MG_VALUE[_p] + MG_RAW[_p][_i]
            )
            EG[_side * _p + 6][_s] = _side * (
                EG_VALUE[_p] + EG_RAW[_p][_i]
            )

_rng = random.Random(712367821)
Z = [[_rng.getrandbits(64) for _ in range(128)] for _ in range(13)]
Z_SIDE = _rng.getrandbits(64)
Z_RIGHTS = [_rng.getrandbits(64) for _ in range(16)]
Z_EP = [_rng.getrandbits(64) for _ in range(128)]

RIGHT_MASK = [15] * 128
for _s, _mask in ((0, 13), (4, 12), (7, 14),
                  (112, 7), (116, 3), (119, 11)):
    RIGHT_MASK[_s] = _mask

_INITIAL = [0] * 128
for _f, _p in enumerate((R, N, B, Q, K, B, N, R)):
    _INITIAL[_f] = _p
    _INITIAL[16 + _f] = P
    _INITIAL[96 + _f] = -P
    _INITIAL[112 + _f] = -_p
_INITIAL = tuple(_INITIAL)

_MEMORY = None
PIECE_CODE = {"P": P, "N": N, "B": B, "R": R, "Q": Q, "K": K}
PROMO_CODE = {"n": N, "b": B, "r": R, "q": Q}
PROMO_TEXT = {N: "n", B: "b", R: "r", Q: "q"}
PASS_MG = (0, 0, 4, 10, 20, 36, 65, 0)
PASS_EG = (0, 4, 9, 20, 40, 72, 125, 0)


def _square(text):
    return (ord(text[0]) - 97) + 16 * (ord(text[1]) - 49)


def _square_text(s):
    return chr(97 + (s & 7)) + chr(49 + (s >> 4))


def _uci(m):
    result = _square_text(m & 127) + _square_text((m >> 7) & 127)
    promotion = (m >> 14) & 7
    if promotion:
        result += PROMO_TEXT[promotion]
    return result


def _distance(a, b):
    return max(abs((a & 7) - (b & 7)), abs((a >> 4) - (b >> 4)))


class _Timeout(Exception):
    pass


class _Engine:
    def __init__(self, board, side, rights, ep, deadline):
        self.b = board
        self.side = side
        self.rights = rights
        self.ep = ep
        self.deadline = deadline
        self.nodes = 0
        self.nulls = 0
        self.mg = self.eg = self.phase = self.pkey = 0
        self.key = Z_RIGHTS[rights]
        if side == -1:
            self.key ^= Z_SIDE
        if ep >= 0:
            self.key ^= Z_EP[ep]
        self.kings = [0, 0]
        self.count = [0] * 13
        for s in SQUARES:
            p = board[s]
            if not p:
                continue
            i = p + 6
            self.count[i] += 1
            self.mg += MG[i][s]
            self.eg += EG[i][s]
            self.phase += PHASE[abs(p)]
            self.key ^= Z[i][s]
            if abs(p) == P:
                self.pkey ^= Z[i][s]
            elif abs(p) == K:
                self.kings[0 if p > 0 else 1] = s
        self.path = [self.key]
        self.tt = {}
        self.pawn_cache = {}
        self.history = [0] * (13 * 128)
        self.killers = [[0, 0] for _ in range(96)]
        self.root_moves = []
        self.root_best = 0

    def tick(self):
        self.nodes += 1
        if not (self.nodes & 127) and time.perf_counter() >= self.deadline:
            raise _Timeout

    def attacked(self, s, by):
        b = self.b
        for d in (15, 17):
            t = s - by * d
            if not (t & 0x88) and b[t] == by:
                return True
        knight = by * N
        for d in KNIGHT:
            t = s + d
            if not (t & 0x88) and b[t] == knight:
                return True
        for directions, slider in ((BISHOP, B), (ROOK, R)):
            for d in directions:
                t = s + d
                first = True
                while not (t & 0x88):
                    p = b[t]
                    if p:
                        if p * by > 0:
                            a = abs(p)
                            if a == Q or a == slider or (first and a == K):
                                return True
                        break
                    first = False
                    t += d
        return False

    def generate(self, captures=False):
        b, side = self.b, self.side
        moves = []
        add = moves.append
        for s in SQUARES:
            p = b[s]
            if p * side <= 0:
                continue
            a = abs(p)
            if a == P:
                step = side * 16
                t = s + step
                if not (t & 0x88) and not b[t]:
                    if (t >> 4) in (0, 7):
                        for pro in (Q, N, R, B):
                            add(s | (t << 7) | (pro << 14))
                    elif not captures:
                        add(s | (t << 7))
                        if (s >> 4) == (1 if side == 1 else 6):
                            u = t + step
                            if not b[u]:
                                add(s | (u << 7))
                for d in (step - 1, step + 1):
                    t = s + d
                    if t & 0x88:
                        continue
                    q = b[t]
                    if q * side < 0 and abs(q) != K:
                        if (t >> 4) in (0, 7):
                            for pro in (Q, N, R, B):
                                add(s | (t << 7) | (pro << 14))
                        else:
                            add(s | (t << 7))
                    elif t == self.ep and not q and b[t - step] == -side:
                        add(s | (t << 7) | EP)
            elif a == N or a == K:
                for d in KNIGHT if a == N else KING:
                    t = s + d
                    if t & 0x88:
                        continue
                    q = b[t]
                    if q * side > 0 or abs(q) == K:
                        continue
                    if q or not captures:
                        add(s | (t << 7))
                if a == K and not captures and self.rights:
                    base = 0 if side == 1 else 112
                    ks = 1 if side == 1 else 4
                    qs = ks << 1
                    if s == base + 4 and not self.attacked(s, -side):
                        if (self.rights & ks
                                and b[base + 7] == side * R
                                and not b[base + 5] and not b[base + 6]
                                and not self.attacked(base + 5, -side)
                                and not self.attacked(base + 6, -side)):
                            add(s | ((base + 6) << 7) | CASTLE)
                        if (self.rights & qs
                                and b[base] == side * R
                                and not b[base + 1] and not b[base + 2]
                                and not b[base + 3]
                                and not self.attacked(base + 3, -side)
                                and not self.attacked(base + 2, -side)):
                            add(s | ((base + 2) << 7) | CASTLE)
            else:
                directions = BISHOP if a == B else ROOK if a == R else KING
                for d in directions:
                    t = s + d
                    while not (t & 0x88):
                        q = b[t]
                        if q:
                            if q * side < 0 and abs(q) != K:
                                add(s | (t << 7))
                            break
                        if not captures:
                            add(s | (t << 7))
                        t += d
        return moves

    def make(self, m):
        b, side = self.b, self.side
        s, t = m & 127, (m >> 7) & 127
        pro = (m >> 14) & 7
        p = b[s]
        new = side * pro if pro else p
        cs = t - side * 16 if m & EP else t
        captured = b[cs]
        old = (captured, self.rights, self.ep, self.key,
               self.pkey, self.mg, self.eg, self.phase)

        self.key ^= Z[p + 6][s] ^ Z[new + 6][t]
        self.mg += MG[new + 6][t] - MG[p + 6][s]
        self.eg += EG[new + 6][t] - EG[p + 6][s]
        if captured:
            self.key ^= Z[captured + 6][cs]
            self.mg -= MG[captured + 6][cs]
            self.eg -= EG[captured + 6][cs]
            self.phase -= PHASE[abs(captured)]
            self.count[captured + 6] -= 1
            if abs(captured) == P:
                self.pkey ^= Z[captured + 6][cs]
        if abs(p) == P:
            self.pkey ^= Z[p + 6][s]
            if not pro:
                self.pkey ^= Z[p + 6][t]
        if pro:
            self.count[p + 6] -= 1
            self.count[new + 6] += 1
            self.phase += PHASE[pro]

        b[s] = 0
        b[cs] = 0
        b[t] = new
        if abs(p) == K:
            self.kings[0 if side == 1 else 1] = t
        if m & CASTLE:
            rf, rt = (s + 3, s + 1) if t > s else (s - 4, s - 1)
            rook = side * R
            b[rf], b[rt] = 0, rook
            self.key ^= Z[rook + 6][rf] ^ Z[rook + 6][rt]
            self.mg += MG[rook + 6][rt] - MG[rook + 6][rf]
            self.eg += EG[rook + 6][rt] - EG[rook + 6][rf]

        rights = self.rights & RIGHT_MASK[s] & RIGHT_MASK[t]
        self.key ^= Z_RIGHTS[self.rights] ^ Z_RIGHTS[rights]
        self.rights = rights
        if self.ep >= 0:
            self.key ^= Z_EP[self.ep]
        self.ep = s + side * 16 if abs(p) == P and abs(t - s) == 32 else -1
        if self.ep >= 0:
            self.key ^= Z_EP[self.ep]
        self.side = -side
        self.key ^= Z_SIDE
        self.path.append(self.key)
        return old

    def undo(self, m, old):
        b = self.b
        self.side = -self.side
        side = self.side
        s, t = m & 127, (m >> 7) & 127
        pro = (m >> 14) & 7
        new = b[t]
        p = side * P if pro else new
        captured = old[0]
        b[s] = p
        if m & EP:
            b[t] = 0
            b[t - side * 16] = captured
        else:
            b[t] = captured
        if pro:
            self.count[new + 6] -= 1
            self.count[p + 6] += 1
        if captured:
            self.count[captured + 6] += 1
        if abs(p) == K:
            self.kings[0 if side == 1 else 1] = s
        if m & CASTLE:
            rf, rt = (s + 3, s + 1) if t > s else (s - 4, s - 1)
            b[rf], b[rt] = side * R, 0
        (_, self.rights, self.ep, self.key, self.pkey,
         self.mg, self.eg, self.phase) = old
        self.path.pop()

    def repeated(self):
        if self.nulls:
            return False
        key = self.key
        for i in range(len(self.path) - 5, -1, -2):
            if self.path[i] == key:
                return True
        return False

    def pawn_info(self):
        cached = self.pawn_cache.get(self.pkey)
        if cached is not None:
            return cached
        b = self.b
        pawns = [[], []]
        files = [[[] for _ in range(8)] for _ in range(2)]
        masks = [0, 0]
        for s in SQUARES:
            p = b[s]
            if abs(p) == P:
                c = 0 if p > 0 else 1
                pawns[c].append(s)
                files[c][s & 7].append(s >> 4)
                masks[c] |= 1 << (s & 7)
        mg = eg = 0
        passed = []
        for c, side in ((0, 1), (1, -1)):
            own, enemy = files[c], files[1 - c]
            for f in range(8):
                extra = len(own[f]) - 1
                if extra > 0:
                    mg -= side * 12 * extra
                    eg -= side * 19 * extra
            for s in pawns[c]:
                f, r = s & 7, s >> 4
                advance = r if side == 1 else 7 - r
                neighbors = range(max(0, f - 1), min(8, f + 2))
                if not ((f and own[f - 1]) or (f < 7 and own[f + 1])):
                    mg -= side * 12
                    eg -= side * 14
                supported = False
                for d in (15, 17):
                    t = s - side * d
                    if not (t & 0x88) and b[t] == side:
                        supported = True
                if supported:
                    mg += side * (5 + advance)
                    eg += side * (7 + advance * 2)
                is_passed = True
                for nf in neighbors:
                    for er in enemy[nf]:
                        if (er - r) * side > 0:
                            is_passed = False
                            break
                    if not is_passed:
                        break
                if is_passed and not any((rr - r) * side > 0 for rr in own[f]):
                    mg += side * PASS_MG[advance]
                    eg += side * PASS_EG[advance]
                    passed.append((s, side, advance))
        result = (mg, eg, masks[0], masks[1], tuple(passed))
        self.pawn_cache[self.pkey] = result
        return result

    def evaluate(self):
        c, b = self.count, self.b
        if not (c[5] or c[7] or c[1] or c[2] or c[10] or c[11]):
            if c[3] + c[4] + c[8] + c[9] <= 1:
                return 0
        pmg, peg, wf, bf, passed = self.pawn_info()
        mg, eg = self.mg + pmg, self.eg + peg
        phase = min(24, self.phase)
        if c[9] >= 2:
            mg += 28
            eg += 45
        if c[3] >= 2:
            mg -= 28
            eg -= 45

        if c[2] or c[10]:
            for s in SQUARES:
                p = b[s]
                if abs(p) != R:
                    continue
                side = 1 if p > 0 else -1
                own, enemy = (wf, bf) if side == 1 else (bf, wf)
                bit = 1 << (s & 7)
                if not own & bit:
                    mg += side * (12 if enemy & bit else 24)
                    eg += side * 7
                rank = s >> 4
                enemy_king = self.kings[1 if side == 1 else 0] >> 4
                if ((side == 1 and rank == 6 and enemy_king >= 6)
                        or (side == -1 and rank == 1 and enemy_king <= 1)):
                    mg += side * 17
                    eg += side * 23

        if phase > 6:
            for color, side in ((0, 1), (1, -1)):
                king = self.kings[color]
                f, r = king & 7, king >> 4
                own = wf if side == 1 else bf
                enemy = bf if side == 1 else wf
                danger = 14 if c[-side * Q + 6] else 6
                for ff in range(max(0, f - 1), min(8, f + 2)):
                    near = (r + side) * 16 + ff
                    far = (r + 2 * side) * 16 + ff
                    if not (near & 0x88) and b[near] == side:
                        mg += side * 8
                    elif not (far & 0x88) and b[far] == side:
                        mg += side * 2
                    else:
                        mg -= side * danger
                    if not own & (1 << ff):
                        mg -= side * danger
                        if not enemy & (1 << ff):
                            mg -= side * 5

        for s, side, advance in passed:
            if advance < 3:
                continue
            color = 0 if side == 1 else 1
            nxt = s + side * 16
            if nxt & 0x88:
                continue
            if b[nxt]:
                eg -= side * (PASS_EG[advance] // 3)
            eg += side * (
                5 * _distance(self.kings[1 - color], nxt)
                - 2 * _distance(self.kings[color], nxt)
            ) * (advance - 2)
            enemy_nonpawn = sum(c[-side * p + 6] for p in (N, B, R, Q))
            if not enemy_nonpawn:
                steps = 7 - advance
                target = (112 if side == 1 else 0) + (s & 7)
                clear = True
                t = nxt
                while not (t & 0x88):
                    if b[t]:
                        clear = False
                        break
                    t += side * 16
                tempo = 0 if self.side == side else 1
                if clear and _distance(self.kings[1 - color], target) > steps - tempo:
                    eg += side * (80 + 20 * advance)

        # Encourage reliable conversion against a bare king.
        for color, side in ((0, 1), (1, -1)):
            if any(c[-side * p + 6] for p in (P, N, B, R, Q)):
                continue
            enough = (c[side * R + 6] or c[side * Q + 6]
                      or c[side * B + 6] >= 2
                      or (c[side * B + 6] and c[side * N + 6]))
            if enough:
                enemy_king = self.kings[1 - color]
                f, r = enemy_king & 7, enemy_king >> 4
                edge = min(f, 7 - f, r, 7 - r)
                eg += side * (
                    40 * (3 - edge)
                    + 12 * (7 - _distance(self.kings[color], enemy_king))
                )

        return self.side * ((mg * phase + eg * (24 - phase)) // 24) + 10

    def order(self, moves, ttmove, ply):
        b, side = self.b, self.side
        killer1, killer2 = self.killers[min(ply, 95)]
        history = self.history

        def score(m):
            if m == ttmove:
                return 100000000
            s, t = m & 127, (m >> 7) & 127
            p = b[s]
            captured = P if m & EP else abs(b[t])
            pro = (m >> 14) & 7
            if captured or pro:
                return 2000000 + 16 * VALUE[captured] - VALUE[abs(p)] + (
                    VALUE[pro] if pro else 0
                )
            if m == killer1:
                return 1000000
            if m == killer2:
                return 999000
            return (history[(p + 6) * 128 + t]
                    + side * (MG[p + 6][t] - MG[p + 6][s]))

        moves.sort(key=score, reverse=True)
        return moves

    def quiescence(self, alpha, beta, ply, qdepth=0, checked=None):
        self.tick()
        if ply >= 80:
            return self.evaluate()
        if self.repeated():
            return 0
        side = self.side
        if checked is None:
            checked = self.attacked(self.kings[0 if side == 1 else 1], -side)
        if checked:
            stand = -INF
        else:
            stand = self.evaluate()
            if stand >= beta:
                return stand
            if stand > alpha:
                alpha = stand
            if qdepth >= 12:
                return stand

        moves = self.order(self.generate(not checked), 0, ply)
        legal = 0
        for m in moves:
            t = (m >> 7) & 127
            pro = (m >> 14) & 7
            victim = P if m & EP else abs(self.b[t])
            delta = (not checked and not pro and self.phase > 5
                     and stand + VALUE[victim] + 190 < alpha)
            old = self.make(m)
            try:
                if self.attacked(self.kings[0 if side == 1 else 1], -side):
                    continue
                legal += 1
                gives_check = self.attacked(
                    self.kings[1 if side == 1 else 0], side
                )
                if delta and not gives_check:
                    continue
                score = -self.quiescence(
                    -beta, -alpha, ply + 1, qdepth + 1, gives_check
                )
            finally:
                self.undo(m, old)
            if score >= beta:
                return score
            if score > alpha:
                alpha = score
        if checked and not legal:
            return -MATE + ply
        return alpha

    def search(self, depth, alpha, beta, ply=0, allow_null=True, checked=None):
        if depth <= 0:
            return self.quiescence(alpha, beta, ply, checked=checked)
        self.tick()
        if ply >= 80:
            return self.evaluate()
        if ply and self.repeated():
            return 0

        alpha = max(alpha, -MATE + ply)
        beta = min(beta, MATE - ply - 1)
        if alpha >= beta:
            return alpha

        side = self.side
        if checked is None:
            checked = self.attacked(self.kings[0 if side == 1 else 1], -side)
        if checked and ply < 12:
            depth += 1

        original_alpha = alpha
        key = self.key
        entry = self.tt.get(key)
        ttmove = 0
        if entry is not None:
            td, ts, bound, ttmove = entry
            if ts > MATE - 100:
                ts -= ply
            elif ts < -MATE + 100:
                ts += ply
            if td >= depth and ply:
                if bound == 0:
                    return ts
                if bound == 1 and ts >= beta:
                    return ts
                if bound == 2 and ts <= alpha:
                    return ts

        static = None
        if not checked and ply:
            static = self.evaluate()
            if depth <= 2 and abs(beta) < MATE - 100:
                if static - 100 * depth >= beta:
                    return static
            nonpawn = sum(self.count[side * p + 6] for p in (N, B, R, Q))
            if (allow_null and depth >= 3 and self.phase > 5 and nonpawn
                    and static >= beta and abs(beta) < MATE - 100):
                old_ep, old_key = self.ep, self.key
                if self.ep >= 0:
                    self.key ^= Z_EP[self.ep]
                self.ep = -1
                self.side = -side
                self.key ^= Z_SIDE
                self.path.append(self.key)
                self.nulls += 1
                try:
                    reduction = 2 + depth // 4
                    score = -self.search(
                        depth - 1 - reduction, -beta, -beta + 1,
                        ply + 1, False, False
                    )
                finally:
                    self.nulls -= 1
                    self.path.pop()
                    self.ep, self.key, self.side = old_ep, old_key, side
                if score >= beta:
                    return score

        moves = self.root_moves[:] if ply == 0 else self.generate()
        self.order(moves, ttmove, ply)
        best = -INF
        bestmove = 0
        legal = searched = 0
        killers = self.killers[min(ply, 95)]

        for m in moves:
            s, t = m & 127, (m >> 7) & 127
            moving = self.b[s]
            noisy = bool(self.b[t] or (m & EP) or ((m >> 14) & 7))
            old = self.make(m)
            try:
                if self.attacked(self.kings[0 if side == 1 else 1], -side):
                    continue
                legal += 1
                gives_check = self.attacked(
                    self.kings[1 if side == 1 else 0], side
                )
                if (ply and searched and not noisy and not checked
                        and not gives_check and depth <= 2
                        and static is not None
                        and static + 110 * depth <= alpha
                        and abs(alpha) < MATE - 100):
                    continue

                newdepth = depth - 1
                reduction = 0
                if (searched >= 4 and depth >= 3 and not noisy
                        and not checked and not gives_check
                        and m not in killers):
                    reduction = 1
                    if depth >= 6 and searched >= 8:
                        reduction += 1
                    if searched >= 16:
                        reduction += 1
                    reduction = min(reduction, newdepth)

                if searched == 0:
                    score = -self.search(
                        newdepth, -beta, -alpha, ply + 1, True, gives_check
                    )
                else:
                    score = -self.search(
                        newdepth - reduction, -alpha - 1, -alpha,
                        ply + 1, True, gives_check
                    )
                    if reduction and score > alpha:
                        score = -self.search(
                            newdepth, -alpha - 1, -alpha,
                            ply + 1, True, gives_check
                        )
                    if alpha < score < beta:
                        score = -self.search(
                            newdepth, -beta, -alpha,
                            ply + 1, True, gives_check
                        )
            finally:
                self.undo(m, old)

            searched += 1
            if score > best:
                best, bestmove = score, m
                if ply == 0:
                    self.root_best = m
            if score > alpha:
                alpha = score
            if alpha >= beta:
                if not noisy:
                    if killers[0] != m:
                        killers[1], killers[0] = killers[0], m
                    index = (moving + 6) * 128 + t
                    self.history[index] = min(
                        200000, self.history[index] + depth * depth * 16
                    )
                break

        if not legal:
            return -MATE + ply if checked else 0

        bound = 2 if best <= original_alpha else 1 if best >= beta else 0
        stored = best
        if stored > MATE - 100:
            stored += ply
        elif stored < -MATE + 100:
            stored -= ply
        self.tt[key] = (depth, stored, bound, bestmove)
        return best


def _recover_context(board, side, deadline):
    """Recover special-move state without inventing castling rights."""
    rights = 15 if side == 1 and tuple(board) == _INITIAL else 0
    ep = -1
    if _MEMORY is None:
        return rights, ep
    previous, previous_side, previous_rights, previous_ep = _MEMORY
    if previous_side == side and previous == tuple(board):
        return previous_rights, previous_ep
    if previous_side != -side:
        return rights, ep

    changed = {s for s in SQUARES if previous[s] != board[s]}
    if not 2 <= len(changed) <= 4:
        return rights, ep
    probe = _Engine(
        list(previous), previous_side, previous_rights, previous_ep, deadline
    )
    for m in probe.generate():
        if (m & 127) not in changed or ((m >> 7) & 127) not in changed:
            continue
        old = probe.make(m)
        try:
            if probe.b == board and not probe.attacked(
                probe.kings[0 if previous_side == 1 else 1], side
            ):
                return probe.rights, probe.ep
        finally:
            probe.undo(m, old)
    return rights, ep


def _encode_external(text, board):
    s, t = _square(text[:2]), _square(text[2:4])
    m = s | (t << 7)
    if len(text) == 5:
        m |= PROMO_CODE[text[4].lower()] << 14
    p = abs(board[s])
    if p == K and abs(t - s) == 2:
        m |= CASTLE
    elif p == P and not board[t] and (s & 7) != (t & 7):
        m |= EP
    return m


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _MEMORY

    deadline = time.perf_counter() + 0.88
    side = 1 if to_play == "white" else -1
    board = [0] * 128
    for square, code in pieces.items():
        board[_square(square)] = (
            1 if code[0] == "w" else -1
        ) * PIECE_CODE[code[1]]

    rights, ep = _recover_context(board, side, deadline)
    engine = _Engine(board, side, rights, ep, deadline)

    # The required two-argument API does not contain a legal-move list.
    # Also support harnesses that expose that list as a module global.
    supplied = globals().get("legal_moves")
    external = {}
    if isinstance(supplied, (list, tuple)) and supplied:
        for text in supplied:
            if isinstance(text, str) and len(text) in (4, 5):
                try:
                    external[_encode_external(text, board)] = text
                except (KeyError, IndexError, ValueError):
                    pass

    roots = []
    candidates = list(external) if external else engine.generate()
    for m in candidates:
        old = engine.make(m)
        try:
            if not engine.attacked(engine.kings[0 if side == 1 else 1], -side):
                roots.append(m)
        finally:
            engine.undo(m, old)

    # In a nonterminal position with no ordinary legal move, an unrecorded
    # en-passant capture can be the only possible action. Infer candidates
    # only in this otherwise actionless case.
    if not roots and not external:
        rank = 4 if side == 1 else 3
        for f in range(8):
            s = rank * 16 + f
            if board[s] != side * P:
                continue
            for df in (-1, 1):
                adjacent = s + df
                if adjacent & 0x88 or board[adjacent] != -side * P:
                    continue
                t = adjacent + side * 16
                origin = adjacent + side * 32
                if board[t] or board[origin]:
                    continue
                m = s | (t << 7) | EP
                old = engine.make(m)
                try:
                    if not engine.attacked(
                        engine.kings[0 if side == 1 else 1], -side
                    ):
                        roots.append(m)
                finally:
                    engine.undo(m, old)

    if not roots:
        # A supplied legal list remains authoritative if its rule metadata
        # cannot be reproduced from the board-only observation.
        if external:
            return next(iter(external.values()))
        raise ValueError("policy must be called on a nonterminal position")

    engine.root_moves = roots
    engine.order(roots, 0, 0)
    best = roots[0]
    engine.root_best = best

    if len(roots) > 1:
        previous_score = 0
        completed = False
        for depth in range(1, 40):
            if time.perf_counter() >= deadline:
                break
            alpha, beta = -INF, INF
            if depth >= 4:
                alpha, beta = previous_score - 40, previous_score + 40
            try:
                while True:
                    score = engine.search(depth, alpha, beta)
                    if score <= alpha and alpha != -INF:
                        alpha = -INF
                        continue
                    if score >= beta and beta != INF:
                        beta = INF
                        continue
                    break
            except _Timeout:
                if not completed and engine.root_best in roots:
                    best = engine.root_best
                break
            if engine.root_best in roots:
                best = engine.root_best
            previous_score = score
            completed = True
            if abs(score) >= MATE - 80:
                break

    result = external.get(best, _uci(best))
    old = engine.make(best)
    try:
        _MEMORY = (
            tuple(engine.b), engine.side, engine.rights, engine.ep
        )
    finally:
        engine.undo(best, old)
    return result
