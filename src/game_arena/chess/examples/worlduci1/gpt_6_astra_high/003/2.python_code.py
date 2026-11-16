
import time
import random

# Piece encoding: white positive, black negative.
# Pawn=1, Knight=2, Bishop=3, Rook=4, Queen=5, King=6.
_TYPES = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6}
_PROM_CHAR = {2: "n", 3: "b", 4: "r", 5: "q"}
_SQUARES = tuple(r * 16 + f for r in range(8) for f in range(8))
_VALUES = (0, 100, 320, 335, 500, 975, 20000)
_PHASE = (0, 0, 1, 1, 2, 4, 0)
_MATE = 30000
_INF = 32000

_KNIGHT_DIRS = (33, 31, 18, 14, -14, -18, -31, -33)
_KING_DIRS = (15, 17, -15, -17, 16, -16, 1, -1)
_RAY_DIRS = (15, 17, -15, -17, 16, -16, 1, -1)

_KNIGHTS = [()] * 128
_KINGS = [()] * 128
_RAYS = [()] * 128

for _s in _SQUARES:
    _KNIGHTS[_s] = tuple(
        _s + d for d in _KNIGHT_DIRS if not ((_s + d) & 0x88)
    )
    _KINGS[_s] = tuple(
        _s + d for d in _KING_DIRS if not ((_s + d) & 0x88)
    )
    rays = []
    for d in _RAY_DIRS:
        ray = []
        t = _s + d
        while not (t & 0x88):
            ray.append(t)
            t += d
        rays.append(tuple(ray))
    _RAYS[_s] = tuple(rays)

# Piece-square tables, listed from a8 through h1 for White.
_MG_TABLES = (
    (
          0,   0,   0,   0,   0,   0,   0,   0,
         98, 134,  61,  95,  68, 126,  34, -11,
         -6,   7,  26,  31,  65,  56,  25, -20,
        -14,  13,   6,  21,  23,  12,  17, -23,
        -27,  -2,  -5,  12,  17,   6,  10, -25,
        -26,  -4,  -4, -10,   3,   3,  33, -12,
        -35,  -1, -20, -23, -15,  24,  38, -22,
          0,   0,   0,   0,   0,   0,   0,   0,
    ),
    (
       -167, -89, -34, -49,  61, -97, -15,-107,
        -73, -41,  72,  36,  23,  62,   7, -17,
        -47,  60,  37,  65,  84, 129,  73,  44,
         -9,  17,  19,  53,  37,  69,  18,  22,
        -13,   4,  16,  13,  28,  19,  21,  -8,
        -23,  -9,  12,  10,  19,  17,  25, -16,
        -29, -53, -12,  -3,  -1,  18, -14, -19,
       -105, -21, -58, -33, -17, -28, -19, -23,
    ),
    (
        -29,   4, -82, -37, -25, -42,   7,  -8,
        -26,  16, -18, -13,  30,  59,  18, -47,
        -16,  37,  43,  40,  35,  50,  37,  -2,
         -4,   5,  19,  50,  37,  37,   7,  -2,
         -6,  13,  13,  26,  34,  12,  10,   4,
          0,  15,  15,  15,  14,  27,  18,  10,
          4,  15,  16,   0,   7,  21,  33,   1,
        -33,  -3, -14, -21, -13, -12, -39, -21,
    ),
    (
         32,  42,  32,  51,  63,   9,  31,  43,
         27,  32,  58,  62,  80,  67,  26,  44,
         -5,  19,  26,  36,  17,  45,  61,  16,
        -24, -11,   7,  26,  24,  35,  -8, -20,
        -36, -26, -12,  -1,   9,  -7,   6, -23,
        -45, -25, -16, -17,   3,   0,  -5, -33,
        -44, -16, -20,  -9,  -1,  11,  -6, -71,
        -19, -13,   1,  17,  16,   7, -37, -26,
    ),
    (
        -28,   0,  29,  12,  59,  44,  43,  45,
        -24, -39,  -5,   1, -16,  57,  28,  54,
        -13, -17,   7,   8,  29,  56,  47,  57,
        -27, -27, -16, -16,  -1,  17,  -2,   1,
         -9, -26,  -9, -10,  -2,  -4,   3,  -3,
        -14,   2, -11,  -2,  -5,   2,  14,   5,
        -35,  -8,  11,   2,   8,  15,  -3,   1,
         -1, -18,  -9,  10, -15, -25, -31, -50,
    ),
    (
        -65,  23,  16, -15, -56, -34,   2,  13,
         29,  -1, -20,  -7,  -8,  -4, -38, -29,
         -9,  24,   2, -16, -20,   6,  22, -22,
        -17, -20, -12, -27, -30, -25, -14, -36,
        -49,  -1, -27, -39, -46, -44, -33, -51,
        -14, -14, -22, -46, -44, -30, -15, -27,
          1,   7,  -8, -64, -43, -16,   9,   8,
        -15,  36,  12, -54,   8, -28,  24,  14,
    ),
)

_EG_TABLES = (
    (
          0,   0,   0,   0,   0,   0,   0,   0,
        178, 173, 158, 134, 147, 132, 165, 187,
         94, 100,  85,  67,  56,  53,  82,  84,
         32,  24,  13,   5,  -2,   4,  17,  17,
         13,   9,  -3,  -7,  -7,  -8,   3,  -1,
          4,   7,  -6,   1,   0,  -5,  -1,  -8,
         13,   8,   8,  10,  13,   0,   2,  -7,
          0,   0,   0,   0,   0,   0,   0,   0,
    ),
    (
        -58, -38, -13, -28, -31, -27, -63, -99,
        -25,  -8, -25,  -2,  -9, -25, -24, -52,
        -24, -20,  10,   9,  -1,  -9, -19, -41,
        -17,   3,  22,  22,  22,  11,   8, -18,
        -18,  -6,  16,  25,  16,  17,   4, -18,
        -23,  -3,  -1,  15,  10,  -3, -20, -22,
        -42, -20, -10,  -5,  -2, -20, -23, -44,
        -29, -51, -23, -15, -22, -18, -50, -64,
    ),
    (
        -14, -21, -11,  -8,  -7,  -9, -17, -24,
         -8,  -4,   7, -12,  -3, -13,  -4, -14,
          2,  -8,   0,  -1,  -2,   6,   0,   4,
         -3,   9,  12,   9,  14,  10,   3,   2,
         -6,   3,  13,  19,   7,  10,  -3,  -9,
        -12,  -3,   8,  10,  13,   3,  -7, -15,
        -14, -18,  -7,  -1,   4,  -9, -15, -27,
        -23,  -9, -23,  -5,  -9, -16,  -5, -17,
    ),
    (
         13,  10,  18,  15,  12,  12,   8,   5,
         11,  13,  13,  11,  -3,   3,   8,   3,
          7,   7,   7,   5,   4,  -3,  -5,  -3,
          4,   3,  13,   1,   2,   1,  -1,   2,
          3,   5,   8,   4,  -5,  -6,  -8, -11,
         -4,   0,  -5,  -1,  -7, -12,  -8, -16,
         -6,  -6,   0,   2,  -9,  -9, -11,  -3,
         -9,   2,   3,  -1,  -5, -13,   4, -20,
    ),
    (
         -9,  22,  22,  27,  27,  19,  10,  20,
        -17,  20,  32,  41,  58,  25,  30,   0,
        -20,   6,   9,  49,  47,  35,  19,   9,
          3,  22,  24,  45,  57,  40,  57,  36,
        -18,  28,  19,  47,  31,   34, 39,  23,
        -16, -27,  15,   6,   9,  17,  10,   5,
        -22, -23, -30, -16, -16, -23, -36, -32,
        -33, -28, -22, -43,  -5, -32, -20, -41,
    ),
    (
        -74, -35, -18, -18, -11,  15,   4, -17,
        -12,  17,  14,  17,  17,  38,  23,  11,
         10,  17,  23,  15,  20,  45,  44,  13,
         -8,  22,  24,  27,  26,  33,  26,   3,
        -18,  -4,  21,  24,  27,  23,   9, -11,
        -19,  -3,  11,  21,  23,  16,   7,  -9,
        -27, -11,   4,  13,  14,   4,  -5, -17,
        -53, -34, -21, -11, -28, -14, -24, -43,
    ),
)

_MG_VALUES = (0, 82, 337, 365, 477, 1025, 0)
_EG_VALUES = (0, 94, 281, 297, 512, 936, 0)
_MG = [[0] * 128 for _ in range(13)]
_EG = [[0] * 128 for _ in range(13)]

for _p in range(-6, 7):
    if not _p:
        continue
    _sign = 1 if _p > 0 else -1
    _pt = abs(_p)
    for _s in _SQUARES:
        _rank, _file = _s >> 4, _s & 7
        _index = (7 - _rank) * 8 + _file if _p > 0 else _rank * 8 + _file
        _MG[_p + 6][_s] = _sign * (
            _MG_VALUES[_pt] + _MG_TABLES[_pt - 1][_index]
        )
        _EG[_p + 6][_s] = _sign * (
            _EG_VALUES[_pt] + _EG_TABLES[_pt - 1][_index]
        )

_rng = random.Random(734921)
_ZOBRIST = [[_rng.getrandbits(64) for _ in range(128)] for _ in range(13)]
_EP_KEYS = [_rng.getrandbits(64) for _ in range(128)]
_TURN_KEY = _rng.getrandbits(64)


def _square(text):
    return (ord(text[1]) - 49) * 16 + ord(text[0]) - 97


def _uci(move):
    source = move & 127
    target = (move >> 7) & 127
    promotion = move >> 14
    text = (
        chr(97 + (source & 7)) + chr(49 + (source >> 4))
        + chr(97 + (target & 7)) + chr(49 + (target >> 4))
    )
    if promotion:
        text += _PROM_CHAR[promotion]
    return text


def _make_book():
    initial = {}
    back = "RNBQKBNR"
    for f in range(8):
        file_name = chr(97 + f)
        initial[file_name + "1"] = "w" + back[f]
        initial[file_name + "2"] = "wP"
        initial[file_name + "7"] = "bP"
        initial[file_name + "8"] = "b" + back[f]

    lines = (
        "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 d2d3 f8c5 c2c3 d7d6",
        "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6 f1e2",
        "e2e4 e7e6 d2d4 d7d5 b1c3 g8f6 e4e5 f6d7 f2f4",
        "e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 c8f5",
        "e2e4 d7d5 e4d5 d8d5 b1c3 d5a5 d2d4",
        "e2e4 g8f6 e4e5 f6d5 d2d4 d7d6 g1f3",
        "d2d4 g8f6 c2c4 e7e6 b1c3 d7d5 g1f3 f8e7 c1f4",
        "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7 e2e3",
        "g1f3 d7d5 d2d4 g8f6 c2c4 e7e6",
        "c2c4 e7e5 b1c3 g8f6 g1f3 b8c6",
    )
    book = {}
    for line in lines:
        board = initial.copy()
        side = "white"
        for move in line.split():
            key = (side, tuple(sorted(board.items())))
            book.setdefault(key, move)
            board[move[2:4]] = board.pop(move[:2])
            side = "black" if side == "white" else "white"
    return book


_BOOK = _make_book()


class _SearchTimeout(Exception):
    pass


class _Engine:
    def __init__(self, pieces, to_play, deadline):
        self.board = [0] * 128
        self.side = 1 if to_play == "white" else -1
        self.kings = [-1, -1]
        self.count = [0] * 13
        self.ep = -1
        self.key = _TURN_KEY if self.side == -1 else 0
        self.pawn_key = 0
        self.mg = 0
        self.eg = 0
        self.phase = 0

        for name, code in pieces.items():
            s = _square(name)
            p = _TYPES[code[1]] * (1 if code[0] == "w" else -1)
            self.board[s] = p
            self.count[p + 6] += 1
            self.key ^= _ZOBRIST[p + 6][s]
            self.mg += _MG[p + 6][s]
            self.eg += _EG[p + 6][s]
            self.phase += _PHASE[abs(p)]
            if abs(p) == 1:
                self.pawn_key ^= _ZOBRIST[p + 6][s]
            elif abs(p) == 6:
                self.kings[0 if p > 0 else 1] = s

        self.deadline = deadline
        self.nodes = 0
        self.tt = {}
        self.pawn_cache = {}
        self.history = [[0] * 16384 for _ in range(2)]
        self.killers = [[0, 0] for _ in range(80)]
        self.path = set()
        self.root_moves = []
        self.iteration = 1
        self.pending_best = 0

    def tick(self):
        self.nodes += 1
        if (self.nodes & 127) == 0 and time.perf_counter() >= self.deadline:
            raise _SearchTimeout

    def attacked(self, square, by):
        b = self.board
        pawn_source = square - 16 * by
        t = pawn_source - 1
        if not (t & 0x88) and b[t] == by:
            return True
        t = pawn_source + 1
        if not (t & 0x88) and b[t] == by:
            return True

        knight = 2 * by
        for t in _KNIGHTS[square]:
            if b[t] == knight:
                return True

        king = 6 * by
        for t in _KINGS[square]:
            if b[t] == king:
                return True

        queen = 5 * by
        bishop = 3 * by
        rook = 4 * by
        for i, ray in enumerate(_RAYS[square]):
            slider = bishop if i < 4 else rook
            for t in ray:
                p = b[t]
                if p:
                    if p == queen or p == slider:
                        return True
                    break
        return False

    def moves(self, captures_only=False):
        b = self.board
        side = self.side
        result = []
        append = result.append

        for source in _SQUARES:
            p = b[source]
            if p * side <= 0:
                continue
            pt = abs(p)

            if pt == 1:
                step = 16 * side
                target = source + step
                if not (target & 0x88) and not b[target]:
                    if target >> 4 in (0, 7):
                        base = source | (target << 7)
                        for promotion in (5, 2, 4, 3):
                            append(base | (promotion << 14))
                    elif not captures_only:
                        append(source | (target << 7))
                        start_rank = 1 if side == 1 else 6
                        if source >> 4 == start_rank and not b[target + step]:
                            append(source | ((target + step) << 7))

                for target in (source + step - 1, source + step + 1):
                    if target & 0x88:
                        continue
                    victim = b[target]
                    if (victim * side < 0 and abs(victim) != 6) or target == self.ep:
                        base = source | (target << 7)
                        if target >> 4 in (0, 7):
                            for promotion in (5, 2, 4, 3):
                                append(base | (promotion << 14))
                        else:
                            append(base)

            elif pt == 2 or pt == 6:
                targets = _KNIGHTS[source] if pt == 2 else _KINGS[source]
                for target in targets:
                    victim = b[target]
                    if victim * side <= 0 and abs(victim) != 6:
                        if victim or not captures_only:
                            append(source | (target << 7))
            else:
                rays = _RAYS[source]
                if pt == 3:
                    rays = rays[:4]
                elif pt == 4:
                    rays = rays[4:]
                for ray in rays:
                    for target in ray:
                        victim = b[target]
                        if not victim:
                            if not captures_only:
                                append(source | (target << 7))
                        else:
                            if victim * side < 0 and abs(victim) != 6:
                                append(source | (target << 7))
                            break
        return result

    def make(self, move):
        b = self.board
        source = move & 127
        target = (move >> 7) & 127
        promotion = move >> 14
        p = b[source]
        side = self.side
        capture_square = target

        if abs(p) == 1 and target == self.ep and not b[target]:
            capture_square = target - 16 * side
        captured = b[capture_square]

        undo = (
            captured, self.ep, self.key, self.pawn_key,
            self.mg, self.eg, self.phase
        )

        if self.ep != -1:
            self.key ^= _EP_KEYS[self.ep]
        self.ep = -1

        new_piece = side * promotion if promotion else p
        old_index = p + 6
        new_index = new_piece + 6

        self.key ^= _ZOBRIST[old_index][source] ^ _ZOBRIST[new_index][target]
        self.mg += _MG[new_index][target] - _MG[old_index][source]
        self.eg += _EG[new_index][target] - _EG[old_index][source]

        if captured:
            index = captured + 6
            self.count[index] -= 1
            self.key ^= _ZOBRIST[index][capture_square]
            self.mg -= _MG[index][capture_square]
            self.eg -= _EG[index][capture_square]
            self.phase -= _PHASE[abs(captured)]
            if abs(captured) == 1:
                self.pawn_key ^= _ZOBRIST[index][capture_square]

        if abs(p) == 1:
            self.pawn_key ^= _ZOBRIST[old_index][source]
            if promotion:
                self.count[old_index] -= 1
                self.count[new_index] += 1
                self.phase += _PHASE[promotion]
            else:
                self.pawn_key ^= _ZOBRIST[old_index][target]
                if abs(target - source) == 32:
                    self.ep = (source + target) // 2
                    self.key ^= _EP_KEYS[self.ep]

        b[source] = 0
        if capture_square != target:
            b[capture_square] = 0
        b[target] = new_piece

        if abs(p) == 6:
            self.kings[0 if side == 1 else 1] = target

        self.side = -side
        self.key ^= _TURN_KEY
        return undo

    def unmake(self, move, undo):
        b = self.board
        source = move & 127
        target = (move >> 7) & 127
        promotion = move >> 14
        side = -self.side
        self.side = side
        captured, old_ep = undo[0], undo[1]
        p = side if promotion else b[target]

        b[source] = p
        if abs(p) == 1 and target == old_ep:
            b[target] = 0
            b[target - 16 * side] = captured
        else:
            b[target] = captured

        if captured:
            self.count[captured + 6] += 1
        if promotion:
            self.count[side + 6] += 1
            self.count[side * promotion + 6] -= 1
        if abs(p) == 6:
            self.kings[0 if side == 1 else 1] = source

        (
            _, self.ep, self.key, self.pawn_key,
            self.mg, self.eg, self.phase
        ) = undo

    def legal_root_moves(self):
        legal = []
        side = self.side
        index = 0 if side == 1 else 1
        for move in self.moves():
            undo = self.make(move)
            safe = not self.attacked(self.kings[index], -side)
            self.unmake(move, undo)
            if safe:
                legal.append(move)
        return legal

    def pawn_evaluation(self):
        cached = self.pawn_cache.get(self.pawn_key)
        if cached is not None:
            return cached

        white = [[] for _ in range(8)]
        black = [[] for _ in range(8)]
        for square in _SQUARES:
            p = self.board[square]
            if p == 1:
                white[square & 7].append(square >> 4)
            elif p == -1:
                black[square & 7].append(square >> 4)

        wmin = [min(ranks) if ranks else 8 for ranks in white]
        bmax = [max(ranks) if ranks else -1 for ranks in black]
        mg = eg = 0
        passed = []
        white_mask = black_mask = 0
        mg_bonus = (0, 0, 5, 12, 26, 48, 82, 0)
        eg_bonus = (0, 3, 12, 26, 50, 90, 150, 0)

        for f in range(8):
            if white[f]:
                white_mask |= 1 << f
            if black[f]:
                black_mask |= 1 << f

            for side, ours in ((1, white), (-1, black)):
                ranks = ours[f]
                if not ranks:
                    continue

                extra = len(ranks) - 1
                mg -= side * 12 * extra
                eg -= side * 20 * extra

                isolated = (
                    (f == 0 or not ours[f - 1])
                    and (f == 7 or not ours[f + 1])
                )
                if isolated:
                    mg -= side * 11 * len(ranks)
                    eg -= side * 15 * len(ranks)

                left = max(0, f - 1)
                right = min(7, f + 1)

                for rank in ranks:
                    advance = rank if side == 1 else 7 - rank
                    if side == 1:
                        is_passed = (
                            rank == max(ranks)
                            and all(bmax[j] <= rank for j in range(left, right + 1))
                        )
                    else:
                        is_passed = (
                            rank == min(ranks)
                            and all(wmin[j] >= rank for j in range(left, right + 1))
                        )

                    if is_passed:
                        mg += side * mg_bonus[advance]
                        eg += side * eg_bonus[advance]
                        passed.append((side, rank * 16 + f, advance))

                    connected = False
                    for nf in (f - 1, f + 1):
                        if 0 <= nf < 8:
                            if rank in ours[nf] or rank - side in ours[nf]:
                                connected = True
                                break
                    if connected:
                        mg += side * 5
                        eg += side * (5 + advance)

        result = (mg, eg, tuple(passed), white_mask, black_mask)
        self.pawn_cache[self.pawn_key] = result
        return result

    @staticmethod
    def distance(a, b):
        return max(abs((a & 7) - (b & 7)), abs((a >> 4) - (b >> 4)))

    def evaluate(self):
        cnt = self.count

        # Elementary drawn material configurations.
        if not (cnt[5] or cnt[7] or cnt[1] or cnt[2] or cnt[10] or cnt[11]):
            minors = cnt[3] + cnt[4] + cnt[8] + cnt[9]
            if minors <= 1:
                return 0
            if not (cnt[3] or cnt[9]) and minors <= 2:
                if not cnt[4] or not cnt[8]:
                    return 0

        pmg, peg, passed, wmask, bmask = self.pawn_evaluation()
        mg = self.mg + pmg
        eg = self.eg + peg

        if cnt[9] >= 2:
            mg += 28
            eg += 42
        if cnt[3] >= 2:
            mg -= 28
            eg -= 42

        phase = min(24, self.phase)

        if phase > 10:
            b = self.board
            for side, king, mask in (
                (1, self.kings[0], wmask),
                (-1, self.kings[1], bmask),
            ):
                rank = king >> 4
                file = king & 7
                home_rank = rank if side == 1 else 7 - rank
                if home_rank <= 1:
                    penalty = 0
                    for f in range(max(0, file - 1), min(8, file + 2)):
                        near = (rank + side) * 16 + f
                        far = (rank + 2 * side) * 16 + f
                        if b[near] != side:
                            penalty += 10
                            if b[far] != side:
                                penalty += 7
                        if not (mask & (1 << f)):
                            penalty += 11
                    mg -= side * penalty
                else:
                    mg -= side * 10 * (home_rank - 1)

        if phase < 14:
            for side, square, advance in passed:
                front = square + 16 * side
                if front & 0x88:
                    continue
                friendly = self.kings[0 if side == 1 else 1]
                enemy = self.kings[1 if side == 1 else 0]
                eg += side * max(1, advance - 1) * (
                    4 * self.distance(enemy, front)
                    - 2 * self.distance(friendly, front)
                )

        # Drive a bare king to the edge and bring our king closer.
        if phase <= 4 and not (cnt[5] or cnt[7]) and abs(eg) > 400:
            winning = 1 if eg > 0 else -1
            own = self.kings[0 if winning == 1 else 1]
            enemy = self.kings[1 if winning == 1 else 0]
            edge = abs(2 * (enemy & 7) - 7) + abs(2 * (enemy >> 4) - 7)
            eg += winning * (9 * edge - 12 * self.distance(own, enemy))

        value = (mg * phase + eg * (24 - phase)) // 24
        return self.side * value + 10

    def capture_value(self, move):
        source = move & 127
        target = (move >> 7) & 127
        victim = self.board[target]
        if victim:
            return _VALUES[abs(victim)]
        if abs(self.board[source]) == 1 and target == self.ep:
            return 100
        return 0

    def ordered(self, moves, tt_move, ply):
        b = self.board
        killers = self.killers[min(ply, 79)]
        history = self.history[0 if self.side == 1 else 1]
        ep = self.ep

        def score(move):
            if move == tt_move:
                return 10000000
            source = move & 127
            target = (move >> 7) & 127
            promotion = move >> 14
            victim = abs(b[target])
            if not victim and abs(b[source]) == 1 and target == ep:
                victim = 1
            if promotion:
                return 2000000 + 16 * _VALUES[promotion] + 16 * _VALUES[victim]
            if victim:
                return 1000000 + 16 * _VALUES[victim] - _VALUES[abs(b[source])]
            if move == killers[0]:
                return 900000
            if move == killers[1]:
                return 800000
            return history[move & 16383]

        return sorted(moves, key=score, reverse=True)

    def only_king(self):
        c = self.count
        if self.side == 1:
            return not (c[7] or c[8] or c[9] or c[10] or c[11])
        return not (c[1] or c[2] or c[3] or c[4] or c[5])

    def king_has_move(self):
        side = self.side
        source = self.kings[0 if side == 1 else 1]
        b = self.board
        for target in _KINGS[source]:
            captured = b[target]
            if captured * side > 0 or abs(captured) == 6:
                continue
            b[source] = 0
            b[target] = 6 * side
            safe = not self.attacked(target, -side)
            b[source] = 6 * side
            b[target] = captured
            if safe:
                return True
        return False

    def quiescence(self, alpha, beta, ply, remaining=8):
        self.tick()
        if ply >= 64:
            return self.evaluate()

        key = self.key
        if key in self.path:
            return 0

        side = self.side
        king_index = 0 if side == 1 else 1
        in_check = self.attacked(self.kings[king_index], -side)

        if not in_check:
            if self.only_king() and not self.king_has_move():
                return 0
            stand = self.evaluate()
            if stand >= beta:
                return stand
            if stand > alpha:
                alpha = stand
            if remaining <= 0:
                return alpha
        else:
            stand = -_INF

        self.path.add(key)
        try:
            moves = self.ordered(self.moves(not in_check), 0, ply)
            legal_count = 0

            for move in moves:
                promotion = move >> 14
                gain = self.capture_value(move)
                delta_candidate = (
                    not in_check
                    and not promotion
                    and stand + gain + 180 < alpha
                )

                undo = self.make(move)
                try:
                    if self.attacked(self.kings[king_index], -side):
                        continue
                    legal_count += 1

                    if delta_candidate:
                        if not self.attacked(self.kings[1 - king_index], side):
                            continue

                    value = -self.quiescence(
                        -beta, -alpha, ply + 1, remaining - 1
                    )
                finally:
                    self.unmake(move, undo)

                if value >= beta:
                    return value
                if value > alpha:
                    alpha = value

            if in_check and not legal_count:
                return -_MATE + ply
            return alpha
        finally:
            self.path.remove(key)

    def search(self, depth, alpha, beta, ply=0, allow_null=True):
        if depth <= 0:
            return self.quiescence(alpha, beta, ply)

        self.tick()
        if ply >= 64:
            return self.evaluate()

        key = self.key
        if key in self.path:
            return 0

        side = self.side
        side_index = 0 if side == 1 else 1
        in_check = self.attacked(self.kings[side_index], -side)
        if in_check and ply < self.iteration + 4:
            depth += 1

        original_alpha = alpha
        pv_node = beta - alpha > 1
        entry = self.tt.get(key)
        tt_move = entry[3] if entry else 0

        if entry and ply:
            stored_depth, score, flag, _ = entry
            if score > _MATE - 1000:
                score -= ply
            elif score < -_MATE + 1000:
                score += ply

            if stored_depth >= depth:
                if flag == 0:
                    return score
                if flag == 1 and score >= beta:
                    return score
                if flag == 2 and score <= alpha:
                    return score

        static = self.evaluate() if not in_check else -_INF

        if (
            not pv_node and not in_check and depth <= 2
            and self.phase > 4 and abs(beta) < _MATE - 1000
            and static - 95 * depth >= beta
        ):
            return static

        self.path.add(key)
        try:
            # Null-move pruning is disabled in pawn-only endings.
            c = self.count
            nonpawn = (
                c[8] + c[9] + c[10] + c[11]
                if side == 1 else c[1] + c[2] + c[3] + c[4]
            )
            if (
                allow_null and not pv_node and not in_check
                and depth >= 3 and nonpawn and static >= beta
                and abs(beta) < _MATE - 1000
            ):
                old_side, old_ep, old_key = self.side, self.ep, self.key
                self.side = -self.side
                self.key ^= _TURN_KEY
                if self.ep != -1:
                    self.key ^= _EP_KEYS[self.ep]
                self.ep = -1
                try:
                    reduction = 2 + depth // 4
                    score = -self.search(
                        depth - 1 - reduction, -beta, -beta + 1,
                        ply + 1, False
                    )
                finally:
                    self.side, self.ep, self.key = old_side, old_ep, old_key

                if score >= beta:
                    return score if score < _MATE - 1000 else beta

            candidates = self.root_moves if ply == 0 else self.moves()
            candidates = self.ordered(candidates, tt_move, ply)
            best_score = -_INF
            best_move = 0
            legal_count = 0
            searched_count = 0

            for move in candidates:
                quiet = not (move >> 14) and not self.capture_value(move)
                undo = self.make(move)
                try:
                    if self.attacked(self.kings[side_index], -side):
                        continue
                    legal_count += 1

                    gives_check = False
                    if quiet and not in_check:
                        if depth >= 3 or (depth == 1 and not pv_node):
                            gives_check = self.attacked(
                                self.kings[1 - side_index], side
                            )

                    if (
                        searched_count and depth == 1 and not pv_node
                        and not in_check and quiet and not gives_check
                        and static + 120 <= alpha
                        and abs(alpha) < _MATE - 1000
                    ):
                        continue

                    next_depth = depth - 1
                    reduction = 0
                    if (
                        depth >= 3 and searched_count >= 4 and quiet
                        and not in_check and not gives_check
                        and move != tt_move
                        and move not in self.killers[min(ply, 79)]
                        and (not pv_node or searched_count >= 7)
                    ):
                        reduction = 1
                        if depth >= 5 and searched_count >= 10:
                            reduction += 1
                        reduction = min(reduction, max(0, next_depth - 1))

                    if searched_count == 0:
                        score = -self.search(
                            next_depth, -beta, -alpha, ply + 1
                        )
                    else:
                        score = -self.search(
                            next_depth - reduction,
                            -alpha - 1, -alpha, ply + 1
                        )
                        if reduction and score > alpha:
                            score = -self.search(
                                next_depth, -alpha - 1, -alpha, ply + 1
                            )
                        if alpha < score < beta:
                            score = -self.search(
                                next_depth, -beta, -alpha, ply + 1
                            )
                finally:
                    self.unmake(move, undo)

                searched_count += 1
                if score > best_score:
                    best_score = score
                    best_move = move
                    if ply == 0:
                        self.pending_best = move

                if score > alpha:
                    alpha = score

                if alpha >= beta:
                    if quiet:
                        killers = self.killers[min(ply, 79)]
                        if move != killers[0]:
                            killers[1] = killers[0]
                            killers[0] = move
                        history = self.history[side_index]
                        index = move & 16383
                        bonus = min(2000, depth * depth * 20)
                        history[index] += bonus - history[index] * bonus // 24000
                    break

            if not legal_count:
                return -_MATE + ply if in_check else 0

            flag = 0
            if best_score <= original_alpha:
                flag = 2
            elif best_score >= beta:
                flag = 1

            stored_score = best_score
            if stored_score > _MATE - 1000:
                stored_score += ply
            elif stored_score < -_MATE + 1000:
                stored_score -= ply

            self.tt[key] = (depth, stored_score, flag, best_move)
            return best_score
        finally:
            self.path.remove(key)


def policy(pieces: dict[str, str], to_play: str) -> str:
    start = time.perf_counter()

    book_move = _BOOK.get((to_play, tuple(sorted(pieces.items()))))
    if book_move is not None:
        return book_move

    engine = _Engine(pieces, to_play, start + 0.88)
    legal = engine.legal_root_moves()

    # A terminal position has no legal move under the requested API.
    # Arena calls are expected to be nonterminal.
    if not legal:
        return "0000"

    if len(legal) == 1:
        return _uci(legal[0])

    engine.root_moves = legal
    best_move = engine.ordered(legal, 0, 0)[0]

    for depth in range(1, 64):
        if time.perf_counter() >= engine.deadline:
            break

        engine.iteration = depth
        engine.pending_best = 0

        try:
            score = engine.search(depth, -_INF, _INF)
        except _SearchTimeout:
            if engine.pending_best:
                best_move = engine.pending_best
            break

        if engine.pending_best:
            best_move = engine.pending_best

        if abs(score) >= _MATE - 128:
            break

    return _uci(best_move)
