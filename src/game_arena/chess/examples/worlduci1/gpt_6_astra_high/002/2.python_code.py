
import time
import random

# 0x88 board representation.
_SQUARES = tuple(r * 16 + f for r in range(8) for f in range(8))
_KNIGHT = (-33, -31, -18, -14, 14, 18, 31, 33)
_DIAG = (15, 17, -15, -17)
_ORTH = (1, -1, 16, -16)
_KING = _ORTH + _DIAG
_TYPES = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6}
_VALUE = (0, 100, 320, 335, 500, 950, 20000)
_PHASE = (0, 0, 1, 1, 2, 4, 0)
_MG_VALUE = (0, 82, 337, 365, 477, 1025, 0)
_EG_VALUE = (0, 94, 281, 297, 512, 936, 0)
_INF = 32000
_MATE = 30000

# Tables are written from White's perspective, rank 8 first.
_MG_RAW = (
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
       -73,-41, 72, 36, 23, 62,  7, -17,
       -47, 60, 37, 65, 84,129, 73,  44,
        -9, 17, 19, 53, 37, 69, 18,  22,
       -13,  4, 16, 13, 28, 19, 21,  -8,
       -23, -9, 12, 10, 19, 17, 25, -16,
       -29,-53,-12, -3, -1, 18,-14, -19,
      -105,-21,-58,-33,-17,-28,-19, -23,
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

_EG_RAW = (
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

_MT = [[0] * 128 for _ in range(13)]
_ET = [[0] * 128 for _ in range(13)]
for _p in range(1, 7):
    for _s in _SQUARES:
        _r, _f = _s >> 4, _s & 7
        _i = (7 - _r) * 8 + _f
        _j = _r * 8 + _f
        _MT[6 + _p][_s] = _MG_VALUE[_p] + _MG_RAW[_p][_i]
        _ET[6 + _p][_s] = _EG_VALUE[_p] + _EG_RAW[_p][_i]
        _MT[6 - _p][_s] = -_MG_VALUE[_p] - _MG_RAW[_p][_j]
        _ET[6 - _p][_s] = -_EG_VALUE[_p] - _EG_RAW[_p][_j]

_rng = random.Random(0x5EEDC0DE)
_Z = [[_rng.getrandbits(64) for _ in range(128)] for _ in range(13)]
_ZSIDE = _rng.getrandbits(64)
_ZEP = [_rng.getrandbits(64) for _ in range(128)]
_LAST_POSITION = None
_LAST_SIDE = None


class _Timeout(Exception):
    pass


def _square(name):
    return (ord(name[0]) - 97) + (int(name[1]) - 1) * 16


def _name(s):
    return chr(97 + (s & 7)) + str((s >> 4) + 1)


def _uci(move):
    a = move & 127
    b = (move >> 7) & 127
    promotion = (move >> 14) & 7
    return _name(a) + _name(b) + ("  nbrq"[promotion] if promotion else "")


def _distance(a, b):
    return max(abs((a & 7) - (b & 7)), abs((a >> 4) - (b >> 4)))


class _Engine:
    def __init__(self, pieces, side, ep, deadline):
        self.b = [0] * 128
        self.kings = [0, 0]
        self.bishops = [0, 0]
        self.mg = 0
        self.eg = 0
        self.phase = 0
        self.key = _ZSIDE if side == -1 else 0
        self.pkey = 0
        self.ep = ep
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.pawn_cache = {}
        self.path = []
        self.killers = [[0, 0] for _ in range(96)]
        self.history = [{}, {}]
        self.root_moves = None

        for name, code in pieces.items():
            s = _square(name)
            p = _TYPES[code[1]] * (1 if code[0] == "w" else -1)
            self.b[s] = p
            self.mg += _MT[p + 6][s]
            self.eg += _ET[p + 6][s]
            self.phase += _PHASE[abs(p)]
            self.key ^= _Z[p + 6][s]
            if abs(p) == 1:
                self.pkey ^= _Z[p + 6][s]
            elif abs(p) == 6:
                self.kings[0 if p > 0 else 1] = s
            elif abs(p) == 3:
                self.bishops[0 if p > 0 else 1] += 1
        if ep >= 0:
            self.key ^= _ZEP[ep]

    def tick(self):
        self.nodes += 1
        if not (self.nodes & 127) and time.perf_counter() >= self.deadline:
            raise _Timeout

    def attacked(self, s, side):
        b = self.b
        for d in (15, 17):
            t = s - side * d
            if not (t & 0x88) and b[t] == side:
                return True
        knight = 2 * side
        for d in _KNIGHT:
            t = s + d
            if not (t & 0x88) and b[t] == knight:
                return True

        queen, king = 5 * side, 6 * side
        for directions, slider in ((_ORTH, 4 * side), (_DIAG, 3 * side)):
            for d in directions:
                t = s + d
                first = True
                while not (t & 0x88):
                    p = b[t]
                    if p:
                        if p == slider or p == queen or (first and p == king):
                            return True
                        break
                    first = False
                    t += d
        return False

    def moves(self, side, captures=False):
        b = self.b
        result = []
        for s in _SQUARES:
            p = b[s]
            if p * side <= 0:
                continue
            kind = abs(p)
            if kind == 1:
                step = side * 16
                t = s + step
                promotion = (s >> 4) == (6 if side == 1 else 1)
                if not (t & 0x88) and b[t] == 0:
                    if promotion:
                        for pr in (5, 2, 4, 3):
                            result.append(s | (t << 7) | (pr << 14))
                    elif not captures:
                        result.append(s | (t << 7))
                        if (s >> 4) == (1 if side == 1 else 6):
                            u = t + step
                            if b[u] == 0:
                                result.append(s | (u << 7))
                for d in (step - 1, step + 1):
                    t = s + d
                    if t & 0x88:
                        continue
                    victim = b[t]
                    ordinary = victim * side < 0 and abs(victim) != 6
                    en_passant = (
                        t == self.ep and victim == 0 and
                        b[t - step] == -side
                    )
                    if ordinary or en_passant:
                        if promotion:
                            for pr in (5, 2, 4, 3):
                                result.append(s | (t << 7) | (pr << 14))
                        else:
                            result.append(s | (t << 7))
                continue

            if kind == 2 or kind == 6:
                for d in (_KNIGHT if kind == 2 else _KING):
                    t = s + d
                    if t & 0x88:
                        continue
                    q = b[t]
                    if q * side < 0:
                        if abs(q) != 6:
                            result.append(s | (t << 7))
                    elif not q and not captures:
                        result.append(s | (t << 7))
                continue

            directions = _DIAG if kind == 3 else _ORTH if kind == 4 else _KING
            for d in directions:
                t = s + d
                while not (t & 0x88):
                    q = b[t]
                    if q:
                        if q * side < 0 and abs(q) != 6:
                            result.append(s | (t << 7))
                        break
                    if not captures:
                        result.append(s | (t << 7))
                    t += d
        return result

    def make(self, move):
        a = move & 127
        t = (move >> 7) & 127
        promotion = (move >> 14) & 7
        b = self.b
        p = b[a]
        side = 1 if p > 0 else -1
        captured = b[t]
        capture_square = t
        if abs(p) == 1 and t == self.ep and not captured and (a & 7) != (t & 7):
            capture_square = t - side * 16
            captured = b[capture_square]

        state = (
            p, captured, capture_square, self.ep, self.key, self.pkey,
            self.mg, self.eg, self.phase,
            self.kings[0], self.kings[1],
            self.bishops[0], self.bishops[1],
        )

        if self.ep >= 0:
            self.key ^= _ZEP[self.ep]
        self.ep = -1
        self.key ^= _ZSIDE
        self.key ^= _Z[p + 6][a]
        self.mg -= _MT[p + 6][a]
        self.eg -= _ET[p + 6][a]
        if abs(p) == 1:
            self.pkey ^= _Z[p + 6][a]

        b[a] = 0
        if captured:
            b[capture_square] = 0
            self.key ^= _Z[captured + 6][capture_square]
            self.mg -= _MT[captured + 6][capture_square]
            self.eg -= _ET[captured + 6][capture_square]
            self.phase -= _PHASE[abs(captured)]
            if abs(captured) == 1:
                self.pkey ^= _Z[captured + 6][capture_square]
            elif abs(captured) == 3:
                self.bishops[0 if captured > 0 else 1] -= 1

        new_piece = side * promotion if promotion else p
        b[t] = new_piece
        self.key ^= _Z[new_piece + 6][t]
        self.mg += _MT[new_piece + 6][t]
        self.eg += _ET[new_piece + 6][t]
        if abs(new_piece) == 1:
            self.pkey ^= _Z[new_piece + 6][t]

        if promotion:
            self.phase += _PHASE[promotion]
            if promotion == 3:
                self.bishops[0 if side == 1 else 1] += 1
        if abs(p) == 6:
            self.kings[0 if side == 1 else 1] = t
        elif abs(p) == 1 and abs(t - a) == 32:
            self.ep = (a + t) // 2
            self.key ^= _ZEP[self.ep]

        return state

    def undo(self, move, state):
        a = move & 127
        t = (move >> 7) & 127
        (
            p, captured, capture_square, self.ep, self.key, self.pkey,
            self.mg, self.eg, self.phase,
            self.kings[0], self.kings[1],
            self.bishops[0], self.bishops[1],
        ) = state
        self.b[a] = p
        self.b[t] = 0
        if captured:
            self.b[capture_square] = captured

    def pawn_terms(self):
        cached = self.pawn_cache.get(self.pkey)
        if cached is not None:
            return cached

        b = self.b
        pawns = [[], []]
        files = [[0] * 8, [0] * 8]
        for s in _SQUARES:
            if abs(b[s]) == 1:
                c = 0 if b[s] > 0 else 1
                pawns[c].append(s)
                files[c][s & 7] += 1

        mg = eg = 0
        passed = []
        mg_bonus = (0, 0, 6, 13, 25, 45, 75, 0)
        eg_bonus = (0, 0, 12, 25, 48, 85, 145, 0)
        for c in (0, 1):
            side = 1 if c == 0 else -1
            own_files = files[c]
            enemies = pawns[1 - c]
            for f in range(8):
                extra = max(0, own_files[f] - 1)
                mg -= side * 12 * extra
                eg -= side * 20 * extra
            for s in pawns[c]:
                f = s & 7
                rank = s >> 4
                progress = rank if side == 1 else 7 - rank
                isolated = (
                    (f == 0 or own_files[f - 1] == 0) and
                    (f == 7 or own_files[f + 1] == 0)
                )
                if isolated:
                    mg -= side * 13
                    eg -= side * 10

                if f in (3, 4) and 2 <= progress <= 4:
                    mg += side * 14

                protected = False
                for d in (15, 17):
                    u = s - side * d
                    if not (u & 0x88) and b[u] == side:
                        protected = True
                        break
                if protected:
                    mg += side * 6
                    eg += side * 9

                is_passed = True
                for enemy in enemies:
                    if abs((enemy & 7) - f) <= 1 and side * ((enemy >> 4) - rank) > 0:
                        is_passed = False
                        break
                if is_passed:
                    mg += side * mg_bonus[progress]
                    eg += side * eg_bonus[progress]
                    passed.append((s, side, progress))

        result = (mg, eg, tuple(passed), len(pawns[0]) + len(pawns[1]))
        self.pawn_cache[self.pkey] = result
        return result

    def evaluate(self, side):
        pmg, peg, passed, pawn_count = self.pawn_terms()
        if pawn_count == 0 and self.phase <= 1:
            return 0

        mg, eg = self.mg + pmg, self.eg + peg
        if self.bishops[0] >= 2:
            mg += 28
            eg += 42
        if self.bishops[1] >= 2:
            mg -= 28
            eg -= 42

        phase = min(24, self.phase)
        if phase < 14:
            for s, color, progress in passed:
                t = s + 16 * color
                if t & 0x88:
                    continue
                own = self.kings[0 if color == 1 else 1]
                enemy = self.kings[1 if color == 1 else 0]
                eg += color * max(1, progress - 2) * (
                    3 * _distance(enemy, t) - 2 * _distance(own, t)
                )
                if self.b[t]:
                    eg -= color * (10 + 3 * progress)

        if phase > 10:
            for c, color in ((0, 1), (1, -1)):
                k = self.kings[c]
                rank = k >> 4
                if (color == 1 and rank > 2) or (color == -1 and rank < 5):
                    continue
                shelter = 0
                for f in range(max(0, (k & 7) - 1), min(7, (k & 7) + 1) + 1):
                    t = (rank + color) * 16 + f
                    u = t + color * 16
                    if not (t & 0x88) and self.b[t] == color:
                        shelter += 10
                    elif not (u & 0x88) and self.b[u] == color:
                        shelter += 4
                    else:
                        shelter -= 7
                mg += color * shelter

        if pawn_count == 0 and abs(eg) > 400:
            winner = 1 if eg > 0 else -1
            eg += winner * (80 - 10 * _distance(self.kings[0], self.kings[1]))

        score = (mg * phase + eg * (24 - phase)) // 24
        return side * score + 10

    def order(self, move, ttmove, ply, side):
        if move == ttmove:
            return 10000000
        a = move & 127
        t = (move >> 7) & 127
        promotion = (move >> 14) & 7
        attacker = abs(self.b[a])
        victim = abs(self.b[t])
        if not victim and attacker == 1 and (a & 7) != (t & 7):
            victim = 1
        if victim or promotion:
            return (
                100000 + 16 * _VALUE[victim] - _VALUE[attacker] +
                (20000 + _VALUE[promotion] if promotion else 0)
            )
        if move == self.killers[ply][0]:
            return 90000
        if move == self.killers[ply][1]:
            return 80000
        return self.history[0 if side == 1 else 1].get(move, 0)

    def quiescence(self, alpha, beta, side, ply, check=None, qply=0):
        self.tick()
        if ply >= 64:
            return self.evaluate(side)
        key = self.key
        if key in self.path:
            return 0
        if check is None:
            check = self.attacked(self.kings[0 if side == 1 else 1], -side)

        if check:
            best = -_INF
            stand = -_INF
        else:
            stand = self.evaluate(side)
            best = stand
            if stand >= beta:
                return stand
            if stand > alpha:
                alpha = stand
            if qply >= 12:
                return stand

        moves = self.moves(side, not check)
        moves.sort(key=lambda m: self.order(m, 0, ply, side), reverse=True)
        self.path.append(key)
        legal = 0
        for move in moves:
            t = (move >> 7) & 127
            promotion = (move >> 14) & 7
            victim = abs(self.b[t])
            if not victim and abs(self.b[move & 127]) == 1 and ((move & 7) != (t & 7)):
                victim = 1
            state = self.make(move)
            if self.attacked(self.kings[0 if side == 1 else 1], -side):
                self.undo(move, state)
                continue
            legal += 1
            gives_check = self.attacked(self.kings[1 if side == 1 else 0], side)
            if (
                not check and not gives_check and not promotion and
                self.phase > 6 and stand + _VALUE[victim] + 170 < alpha
            ):
                self.undo(move, state)
                continue

            score = -self.quiescence(-beta, -alpha, -side, ply + 1, gives_check, qply + 1)
            self.undo(move, state)
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                self.path.pop()
                return best
        self.path.pop()
        if check and not legal:
            return -_MATE + ply
        return best

    def search(self, depth, alpha, beta, side, ply=0, null_ok=True, check=None):
        if depth <= 0:
            return self.quiescence(alpha, beta, side, ply, check)
        self.tick()
        if ply >= 64:
            return self.evaluate(side)

        key = self.key
        if key in self.path:
            return 0
        if check is None:
            check = self.attacked(self.kings[0 if side == 1 else 1], -side)
        if check:
            depth += 1

        alpha = max(alpha, -_MATE + ply)
        beta = min(beta, _MATE - ply - 1)
        if alpha >= beta:
            return alpha

        original_alpha = alpha
        pv = beta - alpha > 1
        entry = self.tt.get(key)
        ttmove = 0
        if entry is not None:
            stored_depth, score, bound, ttmove = entry
            if score > 29000:
                score -= ply
            elif score < -29000:
                score += ply
            if stored_depth >= depth and ply:
                if bound == 0 or (bound == 1 and score >= beta) or (bound == -1 and score <= alpha):
                    return score

        static = self.evaluate(side)
        if (
            not check and not pv and ply and depth <= 3 and
            abs(beta) < 28000 and static - 105 * depth >= beta
        ):
            return static

        self.path.append(key)

        if (
            null_ok and not check and not pv and ply and depth >= 3 and
            static >= beta and self.phase > 6 and abs(beta) < 28000 and
            any(1 < self.b[s] * side < 6 for s in _SQUARES)
        ):
            old_ep, old_key = self.ep, self.key
            self.key ^= _ZSIDE
            if self.ep >= 0:
                self.key ^= _ZEP[self.ep]
            self.ep = -1
            reduction = 2 + depth // 4
            score = -self.search(
                depth - 1 - reduction, -beta, -beta + 1,
                -side, ply + 1, False
            )
            self.ep, self.key = old_ep, old_key
            if score >= beta:
                self.path.pop()
                return score if score < 29000 else beta

        moves = self.root_moves[:] if ply == 0 and self.root_moves is not None else self.moves(side)
        moves.sort(key=lambda m: self.order(m, ttmove, ply, side), reverse=True)

        best = -_INF
        best_move = 0
        legal = 0
        searched = 0

        for move in moves:
            a = move & 127
            t = (move >> 7) & 127
            promotion = (move >> 14) & 7
            capture = bool(self.b[t]) or (
                abs(self.b[a]) == 1 and (a & 7) != (t & 7)
            )
            quiet = not capture and not promotion

            state = self.make(move)
            if self.attacked(self.kings[0 if side == 1 else 1], -side):
                self.undo(move, state)
                continue
            legal += 1
            gives_check = self.attacked(self.kings[1 if side == 1 else 0], side)

            if (
                searched and quiet and not gives_check and not check and
                not pv and depth <= 2 and static + 125 * depth <= alpha and
                abs(alpha) < 28000
            ):
                self.undo(move, state)
                continue

            child_depth = depth - 1
            if searched == 0:
                score = -self.search(
                    child_depth, -beta, -alpha, -side,
                    ply + 1, True, gives_check
                )
            else:
                reduction = 0
                if (
                    depth >= 3 and legal >= 4 and quiet and
                    not check and not gives_check and
                    move != ttmove and move not in self.killers[ply]
                ):
                    reduction = 1
                    if not pv and depth >= 6 and legal >= 9:
                        reduction += 1
                score = -self.search(
                    max(0, child_depth - reduction), -alpha - 1, -alpha,
                    -side, ply + 1, True, gives_check
                )
                if reduction and score > alpha:
                    score = -self.search(
                        child_depth, -alpha - 1, -alpha,
                        -side, ply + 1, True, gives_check
                    )
                if alpha < score < beta:
                    score = -self.search(
                        child_depth, -beta, -alpha,
                        -side, ply + 1, True, gives_check
                    )

            self.undo(move, state)
            searched += 1
            if score > best:
                best, best_move = score, move
            if score > alpha:
                alpha = score
            if alpha >= beta:
                if quiet:
                    killers = self.killers[ply]
                    if killers[0] != move:
                        killers[1] = killers[0]
                        killers[0] = move
                    hist = self.history[0 if side == 1 else 1]
                    old = hist.get(move, 0)
                    bonus = min(1500, depth * depth * 24)
                    hist[move] = old + bonus - old * bonus // 16000
                break

        self.path.pop()
        if not legal:
            return -_MATE + ply if check else 0

        bound = -1 if best <= original_alpha else 1 if best >= beta else 0
        stored_score = best
        if best > 29000:
            stored_score += ply
        elif best < -29000:
            stored_score -= ply
        self.tt[key] = (depth, stored_score, bound, best_move)
        return best

    def legal_root(self, side):
        result = []
        for move in self.moves(side):
            state = self.make(move)
            legal = not self.attacked(self.kings[0 if side == 1 else 1], -side)
            self.undo(move, state)
            if legal:
                result.append(move)
        return result

    def choose(self, side):
        legal = self.legal_root(side)

        # If no ordinary move exists, an omitted en-passant right may be
        # the only reason the arena still considers the position playable.
        if not legal and self.ep < 0:
            rank = 4 if side == 1 else 3
            for s in _SQUARES:
                if self.b[s] != side or (s >> 4) != rank:
                    continue
                for d in (-1, 1):
                    adjacent = s + d
                    target = adjacent + side * 16
                    if (
                        not (adjacent & 0x88) and self.b[adjacent] == -side and
                        not (target & 0x88) and self.b[target] == 0
                    ):
                        self.ep = target
                        self.key ^= _ZEP[target]
                        candidates = self.legal_root(side)
                        if candidates:
                            legal = candidates
                            break
                        self.key ^= _ZEP[target]
                        self.ep = -1
                if legal:
                    break

        if not legal:
            # Terminal positions have no legal answer under this API.
            return None

        legal.sort(key=lambda m: self.order(m, 0, 0, side), reverse=True)
        self.root_moves = legal
        best_move = legal[0]
        if len(legal) == 1:
            return best_move

        root_key = self.key
        last_score = 0
        for depth in range(1, 40):
            if time.perf_counter() >= self.deadline:
                break
            try:
                if depth >= 4:
                    low, high = last_score - 40, last_score + 40
                    score = self.search(depth, low, high, side)
                    if score <= low or score >= high:
                        score = self.search(depth, -_INF, _INF, side)
                else:
                    score = self.search(depth, -_INF, _INF, side)
                entry = self.tt.get(root_key)
                if entry and entry[3] in legal:
                    best_move = entry[3]
                last_score = score
                if abs(score) > 29000:
                    break
            except _Timeout:
                break
        return best_move


def _recover_ep(pieces, side):
    if _LAST_POSITION is None or _LAST_SIDE != side:
        return -1
    old = _LAST_POSITION
    removed = [s for s in old if old.get(s) != pieces.get(s)]
    added = [s for s in pieces if old.get(s) != pieces.get(s)]
    if len(removed) != 1 or len(added) != 1:
        return -1
    a, b = removed[0], added[0]
    enemy = "bP" if side == 1 else "wP"
    if old.get(a) != enemy or pieces.get(b) != enemy:
        return -1
    if a[0] != b[0] or b in old or a in pieces:
        return -1
    expected_start = "7" if side == 1 else "2"
    if a[1] != expected_start:
        return -1
    x, y = _square(a), _square(b)
    if y - x != -side * 32:
        return -1
    return (x + y) // 2


def _remember(pieces, side, move):
    global _LAST_POSITION, _LAST_SIDE
    following = dict(pieces)
    a, b = move[:2], move[2:4]
    p = following.pop(a)
    if p[1] == "P" and a[0] != b[0] and b not in following:
        captured = b[0] + str(int(b[1]) - side)
        following.pop(captured, None)
    if len(move) == 5:
        p = p[0] + move[4].upper()
    following[b] = p
    _LAST_POSITION = following
    _LAST_SIDE = side


def policy(pieces: dict[str, str], to_play: str) -> str:
    started = time.perf_counter()
    side = 1 if to_play == "white" else -1
    ep = _recover_ep(pieces, side)
    engine = _Engine(pieces, side, ep, started + 0.90)
    move = engine.choose(side)
    if move is None:
        # The arena should never request a move in a terminal position.
        raise ValueError("The supplied position has no legal move.")
    result = _uci(move)
    _remember(pieces, side, result)
    return result
