
from time import perf_counter
from random import Random

# Piece numbers: pawn, knight, bishop, rook, queen, king.
P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6
INF = 32000
MATE = 30000
MATE_BOUND = 29000
MAX_PLY = 80
EP_FLAG = 1 << 17

SQUARES = tuple(r * 16 + f for r in range(8) for f in range(8))
BIT = tuple(1 << s for s in range(128))
VALUE = (0, 100, 325, 340, 510, 1000, 20000)
MG_VALUE = (0, 82, 337, 365, 477, 1025, 0)
EG_VALUE = (0, 94, 281, 297, 512, 936, 0)

# Tables are written from a8 to h1.
MG_PST = (
    (
        0, 0, 0, 0, 0, 0, 0, 0,
        98, 134, 61, 95, 68, 126, 34, -11,
        -6, 7, 26, 31, 65, 56, 25, -20,
        -14, 13, 6, 21, 23, 12, 17, -23,
        -27, -2, -5, 12, 17, 6, 10, -25,
        -26, -4, -4, -10, 3, 3, 33, -12,
        -35, -1, -20, -23, -15, 24, 38, -22,
        0, 0, 0, 0, 0, 0, 0, 0,
    ),
    (
        -167, -89, -34, -49, 61, -97, -15, -107,
        -73, -41, 72, 36, 23, 62, 7, -17,
        -47, 60, 37, 65, 84, 129, 73, 44,
        -9, 17, 19, 53, 37, 69, 18, 22,
        -13, 4, 16, 13, 28, 19, 21, -8,
        -23, -9, 12, 10, 19, 17, 25, -16,
        -29, -53, -12, -3, -1, 18, -14, -19,
        -105, -21, -58, -33, -17, -28, -19, -23,
    ),
    (
        -29, 4, -82, -37, -25, -42, 7, -8,
        -26, 16, -18, -13, 30, 59, 18, -47,
        -16, 37, 43, 40, 35, 50, 37, -2,
        -4, 5, 19, 50, 37, 37, 7, -2,
        -6, 13, 13, 26, 34, 12, 10, 4,
        0, 15, 15, 15, 14, 27, 18, 10,
        4, 15, 16, 0, 7, 21, 33, 1,
        -33, -3, -14, -21, -13, -12, -39, -21,
    ),
    (
        32, 42, 32, 51, 63, 9, 31, 43,
        27, 32, 58, 62, 80, 67, 26, 44,
        -5, 19, 26, 36, 17, 45, 61, 16,
        -24, -11, 7, 26, 24, 35, -8, -20,
        -36, -26, -12, -1, 9, -7, 6, -23,
        -45, -25, -16, -17, 3, 0, -5, -33,
        -44, -16, -20, -9, -1, 11, -6, -71,
        -19, -13, 1, 17, 16, 7, -37, -26,
    ),
    (
        -28, 0, 29, 12, 59, 44, 43, 45,
        -24, -39, -5, 1, -16, 57, 28, 54,
        -13, -17, 7, 8, 29, 56, 47, 57,
        -27, -27, -16, -16, -1, 17, -2, 1,
        -9, -26, -9, -10, -2, -4, 3, -3,
        -14, 2, -11, -2, -5, 2, 14, 5,
        -35, -8, 11, 2, 8, 15, -3, 1,
        -1, -18, -9, 10, -15, -25, -31, -50,
    ),
    (
        -65, 23, 16, -15, -56, -34, 2, 13,
        29, -1, -20, -7, -8, -4, -38, -29,
        -9, 24, 2, -16, -20, 6, 22, -22,
        -17, -20, -12, -27, -30, -25, -14, -36,
        -49, -1, -27, -39, -46, -44, -33, -51,
        -14, -14, -22, -46, -44, -30, -15, -27,
        1, 7, -8, -64, -43, -16, 9, 8,
        -15, 36, 12, -54, 8, -28, 24, 14,
    ),
)

EG_PST = (
    (
        0, 0, 0, 0, 0, 0, 0, 0,
        178, 173, 158, 134, 147, 132, 165, 187,
        94, 100, 85, 67, 56, 53, 82, 84,
        32, 24, 13, 5, -2, 4, 17, 17,
        13, 9, -3, -7, -7, -8, 3, -1,
        4, 7, -6, 1, 0, -5, -1, -8,
        13, 8, 8, 10, 13, 0, 2, -7,
        0, 0, 0, 0, 0, 0, 0, 0,
    ),
    (
        -58, -38, -13, -28, -31, -27, -63, -99,
        -25, -8, -25, -2, -9, -25, -24, -52,
        -24, -20, 10, 9, -1, -9, -19, -41,
        -17, 3, 22, 22, 22, 11, 8, -18,
        -18, -6, 16, 25, 16, 17, 4, -18,
        -23, -3, -1, 15, 10, -3, -20, -22,
        -42, -20, -10, -5, -2, -20, -23, -44,
        -29, -51, -23, -15, -22, -18, -50, -64,
    ),
    (
        -14, -21, -11, -8, -7, -9, -17, -24,
        -8, -4, 7, -12, -3, -13, -4, -14,
        2, -8, 0, -1, -2, 6, 0, 4,
        -3, 9, 12, 9, 14, 10, 3, 2,
        -6, 3, 13, 19, 7, 10, -3, -9,
        -12, -3, 8, 10, 13, 3, -7, -15,
        -14, -18, -7, -1, 4, -9, -15, -27,
        -23, -9, -23, -5, -9, -16, -5, -17,
    ),
    (
        13, 10, 18, 15, 12, 12, 8, 5,
        11, 13, 13, 11, -3, 3, 8, 3,
        7, 7, 7, 5, 4, -3, -5, -3,
        4, 3, 13, 1, 2, 1, -1, 2,
        3, 5, 8, 4, -5, -6, -8, -11,
        -4, 0, -5, -1, -7, -12, -8, -16,
        -6, -6, 0, 2, -9, -9, -11, -3,
        -9, 2, 3, -1, -5, -13, 4, -20,
    ),
    (
        -9, 22, 22, 27, 27, 19, 10, 20,
        -17, 20, 32, 41, 58, 25, 30, 0,
        -20, 6, 9, 49, 47, 35, 19, 9,
        3, 22, 24, 45, 57, 40, 57, 36,
        -18, 28, 19, 47, 31, 34, 39, 23,
        -16, -27, 15, 6, 9, 17, 10, 5,
        -22, -23, -30, -16, -16, -23, -36, -32,
        -33, -28, -22, -43, -5, -32, -20, -41,
    ),
    (
        -74, -35, -18, -18, -11, 15, 4, -17,
        -12, 17, 14, 17, 17, 38, 23, 11,
        10, 17, 23, 15, 20, 45, 44, 13,
        -8, 22, 24, 27, 26, 33, 26, 3,
        -18, -4, 21, 24, 27, 23, 9, -11,
        -19, -3, 11, 21, 23, 16, 7, -9,
        -27, -11, 4, 13, 14, 4, -5, -17,
        -53, -34, -21, -11, -28, -14, -24, -43,
    ),
)

MG = [[0] * 128 for _ in range(13)]
EG = [[0] * 128 for _ in range(13)]
PHASE = [0] * 13

for p, weight in enumerate((0, 0, 1, 1, 2, 4, 0)):
    PHASE[p] = PHASE[-p] = weight

for p in range(1, 7):
    for s in SQUARES:
        r, f = s >> 4, s & 7
        wi = (7 - r) * 8 + f
        bi = r * 8 + f
        MG[p][s] = MG_VALUE[p] + MG_PST[p - 1][wi]
        EG[p][s] = EG_VALUE[p] + EG_PST[p - 1][wi]
        MG[-p][s] = -MG_VALUE[p] - MG_PST[p - 1][bi]
        EG[-p][s] = -EG_VALUE[p] - EG_PST[p - 1][bi]

KNIGHT = [[] for _ in range(128)]
KING = [[] for _ in range(128)]
DIAGONAL = [[] for _ in range(128)]
ORTHOGONAL = [[] for _ in range(128)]
ALL_RAYS = [[] for _ in range(128)]

for s in SQUARES:
    KNIGHT[s] = tuple(
        s + d for d in (-33, -31, -18, -14, 14, 18, 31, 33)
        if not ((s + d) & 0x88)
    )
    KING[s] = tuple(
        s + d for d in (-17, -16, -15, -1, 1, 15, 16, 17)
        if not ((s + d) & 0x88)
    )
    for directions, target in (
        ((-17, -15, 15, 17), DIAGONAL),
        ((-16, -1, 1, 16), ORTHOGONAL),
    ):
        rays = []
        for d in directions:
            ray = []
            t = s + d
            while not (t & 0x88):
                ray.append(t)
                t += d
            rays.append(tuple(ray))
        target[s] = tuple(rays)
    ALL_RAYS[s] = DIAGONAL[s] + ORTHOGONAL[s]

SLIDING = (None, None, None, DIAGONAL, ORTHOGONAL, ALL_RAYS, None)

_rng = Random(0x93A65B17)
ZOBRIST = [[_rng.getrandbits(64) for _ in range(128)] for _ in range(13)]
ZOBRIST[0] = [0] * 128
Z_SIDE = _rng.getrandbits(64)
Z_EP = [_rng.getrandbits(64) for _ in range(128)]

_TT = {}
_PAWN_CACHE = {}
PIECE_CODE = {"P": P, "N": N, "B": B, "R": R, "Q": Q, "K": K}


class SearchTimeout(Exception):
    pass


def move_string(move):
    f = move & 127
    t = (move >> 7) & 127
    result = (
        chr(97 + (f & 7)) + str((f >> 4) + 1)
        + chr(97 + (t & 7)) + str((t >> 4) + 1)
    )
    promotion = (move >> 14) & 7
    if promotion:
        result += {N: "n", B: "b", R: "r", Q: "q"}[promotion]
    return result


def king_distance(a, b):
    return max(abs((a & 7) - (b & 7)), abs((a >> 4) - (b >> 4)))


class Engine:
    def __init__(self, pieces, side, deadline):
        self.board = [0] * 128
        self.locations = [set() for _ in range(13)]
        self.kings = [4, 116]
        self.side = side
        self.ep = -1
        self.mg = 0
        self.eg = 0
        self.phase = 0
        self.key = Z_SIDE if side == -1 else 0
        self.pawn_key = 0
        self.deadline = deadline
        self.nodes = 0
        self.iteration = 1
        self.path = [0] * (MAX_PLY + 8)
        self.killers = [[0, 0] for _ in range(MAX_PLY + 8)]
        self.history = [[0] * 16384 for _ in range(2)]
        self.tt = _TT

        for square, code in pieces.items():
            s = (ord(square[0]) - 97) + 16 * (int(square[1]) - 1)
            p = PIECE_CODE[code[1]]
            if code[0] == "b":
                p = -p
            self.board[s] = p
            self.locations[p].add(s)
            self.mg += MG[p][s]
            self.eg += EG[p][s]
            self.phase += PHASE[p]
            self.key ^= ZOBRIST[p][s]
            if abs(p) == P:
                self.pawn_key ^= ZOBRIST[p][s]
            elif p == K:
                self.kings[0] = s
            elif p == -K:
                self.kings[1] = s

    def tick(self):
        self.nodes += 1
        if not (self.nodes & 255) and perf_counter() >= self.deadline:
            raise SearchTimeout

    def attacked(self, square, side):
        b = self.board
        pawn = side
        a = square - 15 * side
        if not (a & 0x88) and b[a] == pawn:
            return True
        a = square - 17 * side
        if not (a & 0x88) and b[a] == pawn:
            return True

        knight = N * side
        for a in KNIGHT[square]:
            if b[a] == knight:
                return True

        king = K * side
        for a in KING[square]:
            if b[a] == king:
                return True

        bishop, rook, queen = B * side, R * side, Q * side
        for ray in DIAGONAL[square]:
            for a in ray:
                p = b[a]
                if p:
                    if p == bishop or p == queen:
                        return True
                    break

        for ray in ORTHOGONAL[square]:
            for a in ray:
                p = b[a]
                if p:
                    if p == rook or p == queen:
                        return True
                    break
        return False

    def moves(self, captures_only=False):
        b = self.board
        side = self.side
        result = []
        append = result.append
        step = 16 * side

        for f in self.locations[side]:
            t = f + step
            if not (t & 0x88) and b[t] == 0:
                base = f | (t << 7)
                if (t >> 4) in (0, 7):
                    for promotion in (Q, N, R, B):
                        append(base | (promotion << 14))
                elif not captures_only:
                    append(base)
                    if (f >> 4) == (1 if side == 1 else 6):
                        t2 = t + step
                        if b[t2] == 0:
                            append(f | (t2 << 7))

            for t in (f + 15 * side, f + 17 * side):
                if t & 0x88:
                    continue
                captured = b[t]
                if captured * side < 0 and abs(captured) != K:
                    base = f | (t << 7)
                    if (t >> 4) in (0, 7):
                        for promotion in (Q, N, R, B):
                            append(base | (promotion << 14))
                    else:
                        append(base)
                elif (
                    t == self.ep and captured == 0
                    and b[t - step] == -side
                ):
                    append(f | (t << 7) | EP_FLAG)

        for kind in (N, B, R, Q, K):
            for f in self.locations[kind * side]:
                if kind == N or kind == K:
                    targets = KNIGHT[f] if kind == N else KING[f]
                    for t in targets:
                        captured = b[t]
                        if captured == 0:
                            if not captures_only:
                                append(f | (t << 7))
                        elif captured * side < 0 and abs(captured) != K:
                            append(f | (t << 7))
                else:
                    for ray in SLIDING[kind][f]:
                        for t in ray:
                            captured = b[t]
                            if captured == 0:
                                if not captures_only:
                                    append(f | (t << 7))
                            else:
                                if captured * side < 0 and abs(captured) != K:
                                    append(f | (t << 7))
                                break
        return result

    def make(self, move):
        b = self.board
        f = move & 127
        t = (move >> 7) & 127
        promotion = (move >> 14) & 7
        p = b[f]
        side = self.side
        np = promotion * side if promotion else p
        cs = t - 16 * side if move & EP_FLAG else t
        captured = b[cs]

        undo = (
            captured, p, self.mg, self.eg, self.phase,
            self.key, self.pawn_key, self.ep,
        )

        self.locations[p].remove(f)
        if captured:
            self.locations[captured].remove(cs)
        self.locations[np].add(t)

        b[f] = 0
        b[cs] = 0
        b[t] = np

        self.mg += MG[np][t] - MG[p][f] - MG[captured][cs]
        self.eg += EG[np][t] - EG[p][f] - EG[captured][cs]
        self.phase -= PHASE[captured]
        if promotion:
            self.phase += PHASE[np]

        self.key ^= (
            ZOBRIST[p][f] ^ ZOBRIST[np][t]
            ^ ZOBRIST[captured][cs] ^ Z_SIDE
        )
        if self.ep >= 0:
            self.key ^= Z_EP[self.ep]
        self.ep = -1
        if abs(p) == P:
            self.pawn_key ^= ZOBRIST[p][f]
            if not promotion:
                self.pawn_key ^= ZOBRIST[p][t]
            if abs(t - f) == 32:
                self.ep = (f + t) // 2
                self.key ^= Z_EP[self.ep]
        if abs(captured) == P:
            self.pawn_key ^= ZOBRIST[captured][cs]

        if p == K:
            self.kings[0] = t
        elif p == -K:
            self.kings[1] = t

        self.side = -side
        return undo

    def unmake(self, move, undo):
        f = move & 127
        t = (move >> 7) & 127
        np = self.board[t]
        (
            captured, p, self.mg, self.eg, self.phase,
            self.key, self.pawn_key, self.ep,
        ) = undo

        self.side = -self.side
        cs = t - 16 * self.side if move & EP_FLAG else t

        self.locations[np].remove(t)
        self.locations[p].add(f)
        if captured:
            self.locations[captured].add(cs)

        self.board[t] = 0
        self.board[cs] = captured
        self.board[f] = p
        if p == K:
            self.kings[0] = f
        elif p == -K:
            self.kings[1] = f

    def legal_moves(self):
        result = []
        side = self.side
        ci = 0 if side == 1 else 1
        for move in self.moves():
            undo = self.make(move)
            if not self.attacked(self.kings[ci], -side):
                result.append(move)
            self.unmake(move, undo)
        return result

    def emergency_ep_moves(self):
        # With no supplied history, use this only if no ordinary move exists.
        # In a nonterminal position, en passant can be the only legal action.
        result = []
        side = self.side
        ci = 0 if side == 1 else 1
        required_rank = 4 if side == 1 else 3
        b = self.board
        candidates = []

        for f in self.locations[side]:
            if (f >> 4) != required_rank:
                continue
            for t in (f + 15 * side, f + 17 * side):
                if (
                    not (t & 0x88) and b[t] == 0
                    and b[t - 16 * side] == -side
                ):
                    candidates.append(f | (t << 7) | EP_FLAG)

        for move in candidates:
            undo = self.make(move)
            if not self.attacked(self.kings[ci], -side):
                result.append(move)
            self.unmake(move, undo)
        return result

    def pawn_info(self):
        cached = _PAWN_CACHE.get(self.pawn_key)
        if cached is not None:
            return cached

        files = [[0] * 8, [0] * 8]
        attacks = [0, 0]
        passed = []
        mg = eg = 0
        passed_mg = (0, 4, 8, 15, 28, 50, 80, 0)
        passed_eg = (0, 8, 16, 32, 60, 105, 175, 0)

        for ci, side in ((0, 1), (1, -1)):
            for s in self.locations[side]:
                files[ci][s & 7] |= 1 << (s >> 4)
                for t in (s + 15 * side, s + 17 * side):
                    if not (t & 0x88):
                        attacks[ci] |= BIT[t]

        for ci, side in ((0, 1), (1, -1)):
            own = files[ci]
            enemy = files[1 - ci]
            for f in range(8):
                count = own[f].bit_count()
                if count > 1:
                    mg -= side * 12 * (count - 1)
                    eg -= side * 20 * (count - 1)
                if count:
                    neighbours = (
                        (own[f - 1] if f else 0)
                        | (own[f + 1] if f < 7 else 0)
                    )
                    if not neighbours:
                        mg -= side * 12 * count
                        eg -= side * 16 * count

            for s in self.locations[side]:
                f, r = s & 7, s >> 4
                rr = r if side == 1 else 7 - r
                adjacent = (
                    (own[f - 1] if f else 0)
                    | (own[f + 1] if f < 7 else 0)
                )
                near = (1 << r)
                if r:
                    near |= 1 << (r - 1)
                if r < 7:
                    near |= 1 << (r + 1)
                if adjacent & near:
                    mg += side * 5
                    eg += side * 7

                opposing = enemy[f]
                if f:
                    opposing |= enemy[f - 1]
                if f < 7:
                    opposing |= enemy[f + 1]

                if side == 1:
                    is_passed = not (opposing >> (r + 1))
                    foremost = not (own[f] >> (r + 1))
                else:
                    front = (1 << r) - 1
                    is_passed = not (opposing & front)
                    foremost = not (own[f] & front)

                if is_passed and foremost:
                    mg += side * passed_mg[rr]
                    eg += side * passed_eg[rr]
                    passed.append((s, side, rr))

        cached = (
            mg, eg, files[0], files[1],
            attacks[0], attacks[1], tuple(passed),
        )
        _PAWN_CACHE[self.pawn_key] = cached
        return cached

    def evaluate(self):
        pm, pe, wf, bf, wa, ba, passed = self.pawn_info()
        mg = self.mg + pm
        eg = self.eg + pe
        loc = self.locations
        b = self.board

        for ci, side in ((0, 1), (1, -1)):
            own_files = wf if side == 1 else bf
            enemy_files = bf if side == 1 else wf
            own_attacks = wa if side == 1 else ba
            enemy_attacks = ba if side == 1 else wa

            if len(loc[B * side]) >= 2:
                mg += side * 30
                eg += side * 45

            pawn_count = len(loc[side])
            eg += side * (
                (pawn_count - 5) * 3 * len(loc[N * side])
                + (5 - pawn_count) * 3 * len(loc[R * side])
            )

            for s in loc[R * side]:
                f, r = s & 7, s >> 4
                if not own_files[f]:
                    if not enemy_files[f]:
                        mg += side * 27
                        eg += side * 14
                    else:
                        mg += side * 17
                        eg += side * 9
                if (r if side == 1 else 7 - r) == 6:
                    mg += side * 20
                    eg += side * 30

            for kind in (N, B):
                for s in loc[kind * side]:
                    if enemy_attacks & BIT[s]:
                        mg -= side * 22
                        eg -= side * 12

            for s in loc[N * side]:
                f, r = s & 7, s >> 4
                rr = r if side == 1 else 7 - r
                if 3 <= rr <= 5 and own_attacks & BIT[s]:
                    adjacent_enemy = (
                        (enemy_files[f - 1] if f else 0)
                        | (enemy_files[f + 1] if f < 7 else 0)
                    )
                    if side == 1:
                        stable = not (adjacent_enemy >> (r + 1))
                    else:
                        stable = not (adjacent_enemy & ((1 << r) - 1))
                    if stable:
                        mg += side * 18
                        eg += side * 10

            king = self.kings[ci]
            kf, kr = king & 7, king >> 4
            relative_rank = kr if side == 1 else 7 - kr

            if relative_rank <= 1 and (kf <= 2 or kf >= 5):
                shield = 0
                for f in range(max(0, kf - 1), min(8, kf + 2)):
                    first = (kr + side) * 16 + f
                    second = (kr + 2 * side) * 16 + f
                    if not (first & 0x88) and b[first] == side:
                        shield += 12
                    elif not (second & 0x88) and b[second] == side:
                        shield += 5
                    else:
                        shield -= 13
                if not loc[-Q * side]:
                    shield //= 2
                mg += side * shield

        for s, side, rr in passed:
            if rr < 2 or rr > 6:
                continue
            front = s + 16 * side
            own_king = self.kings[0 if side == 1 else 1]
            enemy_king = self.kings[1 if side == 1 else 0]
            eg += side * (
                4 * king_distance(enemy_king, front)
                - 2 * king_distance(own_king, front)
            ) * (rr - 1)
            if b[front] == 0:
                eg += side * rr * 3
            else:
                eg -= side * rr * rr * 2

        phase = min(24, self.phase)
        score = (mg * phase + eg * (24 - phase)) // 24

        # Encourage efficient conversion of elementary mating endings.
        if self.phase <= 4 and not loc[P] and not loc[-P]:
            winner = 1 if score > 450 else -1 if score < -450 else 0
            if winner:
                own = self.kings[0 if winner == 1 else 1]
                enemy = self.kings[1 if winner == 1 else 0]
                f, r = enemy & 7, enemy >> 4
                edge = max(abs(2 * f - 7), abs(2 * r - 7))
                distance = abs((own & 7) - f) + abs((own >> 4) - r)
                score += winner * (12 * edge + 7 * (14 - distance))

        score = max(-20000, min(20000, score))
        return score * self.side + 12

    def insufficient(self):
        return (
            self.phase <= 1
            and not self.locations[P]
            and not self.locations[-P]
        )

    def king_has_move(self):
        side = self.side
        ci = 0 if side == 1 else 1
        f = self.kings[ci]
        b = self.board

        for t in KING[f]:
            captured = b[t]
            if captured * side > 0 or captured == -K * side:
                continue
            b[f] = 0
            b[t] = K * side
            safe = not self.attacked(t, -side)
            b[f] = K * side
            b[t] = captured
            if safe:
                return True
        return False

    def ordered(self, moves, ply, tt_move=0):
        b = self.board
        side = self.side
        ci = 0 if side == 1 else 1
        history = self.history[ci]
        killer1, killer2 = self.killers[ply]

        def priority(move):
            if move == tt_move:
                return 20000000
            f = move & 127
            t = (move >> 7) & 127
            promotion = (move >> 14) & 7
            p = b[f]
            captured = -side if move & EP_FLAG else b[t]

            if promotion:
                return 3000000 + VALUE[promotion] * 16 + VALUE[abs(captured)]
            if captured:
                return 2000000 + VALUE[abs(captured)] * 16 - VALUE[abs(p)]
            if move == killer1:
                return 900000
            if move == killer2:
                return 800000
            return history[move & 16383] + side * (MG[p][t] - MG[p][f])

        return sorted(moves, key=priority, reverse=True)

    def store(self, depth, score, flag, move, ply):
        if score > MATE_BOUND:
            score += ply
        elif score < -MATE_BOUND:
            score -= ply
        old = self.tt.get(self.key)
        if old is None or depth >= old[0] or flag == 0:
            self.tt[self.key] = (depth, score, flag, move)

    def quiescence(self, alpha, beta, ply):
        self.tick()
        if ply >= MAX_PLY:
            return self.evaluate()
        if self.key in self.path[:ply]:
            return 0
        self.path[ply] = self.key
        if self.insufficient():
            return 0

        side = self.side
        ci = 0 if side == 1 else 1
        in_check = self.attacked(self.kings[ci], -side)
        static = -INF

        if not in_check:
            if self.phase <= 4:
                loc = self.locations
                if not any(loc[k * side] for k in (P, N, B, R, Q)):
                    if not self.king_has_move():
                        return 0

            static = self.evaluate()
            if static >= beta:
                return static
            if static > alpha:
                alpha = static

        moves = self.ordered(self.moves(not in_check), ply)
        legal_count = 0

        for move in moves:
            t = (move >> 7) & 127
            promotion = (move >> 14) & 7
            captured = -side if move & EP_FLAG else self.board[t]
            delta_prune = (
                not in_check and not promotion and self.phase > 4
                and static + VALUE[abs(captured)] + 180 < alpha
            )

            undo = self.make(move)
            if self.attacked(self.kings[ci], -side):
                self.unmake(move, undo)
                continue
            legal_count += 1

            if delta_prune and not self.attacked(self.kings[1 - ci], side):
                self.unmake(move, undo)
                continue

            score = -self.quiescence(-beta, -alpha, ply + 1)
            self.unmake(move, undo)

            if score >= beta:
                return score
            if score > alpha:
                alpha = score

        if in_check and legal_count == 0:
            return -MATE + ply
        return alpha

    def search(self, depth, alpha, beta, ply, allow_null=True):
        if depth <= 0:
            return self.quiescence(alpha, beta, ply)

        self.tick()
        if ply >= MAX_PLY:
            return self.evaluate()
        if self.key in self.path[:ply]:
            return 0
        self.path[ply] = self.key
        if self.insufficient():
            return 0

        alpha = max(alpha, -MATE + ply)
        beta = min(beta, MATE - ply - 1)
        if alpha >= beta:
            return alpha

        original_alpha = alpha
        side = self.side
        ci = 0 if side == 1 else 1
        in_check = self.attacked(self.kings[ci], -side)
        if in_check and ply < 2 * self.iteration + 4:
            depth += 1

        entry = self.tt.get(self.key)
        tt_move = entry[3] if entry else 0
        if entry is not None and entry[0] >= depth:
            score = entry[1]
            if score > MATE_BOUND:
                score -= ply
            elif score < -MATE_BOUND:
                score += ply

            if entry[2] == 0:
                return score
            if entry[2] == 1 and score >= beta:
                return score
            if entry[2] == 2 and score <= alpha:
                return score

        pv_node = beta - alpha > 1
        static = self.evaluate() if not in_check else -INF

        if (
            not in_check and not pv_node and self.phase > 4
            and depth <= 2 and abs(beta) < MATE_BOUND
            and static - 130 * depth >= beta
        ):
            return static

        if (
            allow_null and not in_check and not pv_node
            and depth >= 3 and self.phase > 4
            and static >= beta and abs(beta) < MATE_BOUND
            and any(self.locations[k * side] for k in (N, B, R, Q))
        ):
            old_key, old_ep = self.key, self.ep
            self.side = -side
            self.key ^= Z_SIDE
            if self.ep >= 0:
                self.key ^= Z_EP[self.ep]
            self.ep = -1

            reduction = 2 + depth // 4
            score = -self.search(
                depth - reduction - 1, -beta, -beta + 1, ply + 1, False
            )
            self.side = side
            self.key, self.ep = old_key, old_ep
            if score >= beta:
                return beta if score > MATE_BOUND else score

        moves = self.ordered(self.moves(), ply, tt_move)
        best = -INF
        best_move = 0
        legal_count = 0
        killers = self.killers[ply]

        for move in moves:
            f = move & 127
            t = (move >> 7) & 127
            p = self.board[f]
            promotion = (move >> 14) & 7
            quiet = self.board[t] == 0 and not promotion and not (move & EP_FLAG)
            advanced_pawn = (
                abs(p) == P
                and ((t >> 4) >= 5 if side == 1 else (t >> 4) <= 2)
            )

            undo = self.make(move)
            if self.attacked(self.kings[ci], -side):
                self.unmake(move, undo)
                continue
            legal_count += 1

            gives_check = False
            if quiet and (depth >= 3 or (depth == 1 and not pv_node)):
                gives_check = self.attacked(self.kings[1 - ci], side)

            if (
                depth == 1 and not pv_node and not in_check
                and quiet and not gives_check and not advanced_pawn
                and legal_count > 1 and best > -MATE_BOUND
                and static + 150 <= alpha
                and move != tt_move and move not in killers
            ):
                self.unmake(move, undo)
                continue

            next_depth = depth - 1
            if legal_count == 1:
                score = -self.search(next_depth, -beta, -alpha, ply + 1)
            else:
                reduction = 0
                if (
                    depth >= 3 and legal_count >= 4 and quiet
                    and not in_check and not gives_check
                    and not advanced_pawn and move not in killers
                ):
                    reduction = 1
                    if depth >= 5 and legal_count >= 10 and not pv_node:
                        reduction = 2

                score = -self.search(
                    next_depth - reduction, -alpha - 1, -alpha, ply + 1
                )
                if reduction and score > alpha:
                    score = -self.search(
                        next_depth, -alpha - 1, -alpha, ply + 1
                    )
                if alpha < score < beta:
                    score = -self.search(next_depth, -beta, -alpha, ply + 1)

            self.unmake(move, undo)

            if score > best:
                best = score
                best_move = move
            if score > alpha:
                alpha = score

            if alpha >= beta:
                if quiet:
                    if killers[0] != move:
                        killers[1] = killers[0]
                        killers[0] = move
                    index = move & 16383
                    old = self.history[ci][index]
                    bonus = min(2000, depth * depth * 32)
                    self.history[ci][index] = old + bonus - old * bonus // 16384
                self.store(depth, best, 1, best_move, ply)
                return best

        if legal_count == 0:
            return -MATE + ply if in_check else 0

        flag = 0 if best > original_alpha else 2
        self.store(depth, best, flag, best_move, ply)
        return best

    def root(self, moves, depth, alpha, beta, hint):
        self.path[0] = self.key
        original_alpha = alpha
        best = -INF
        best_move = moves[0]

        for i, move in enumerate(self.ordered(moves, 0, hint)):
            if perf_counter() >= self.deadline:
                raise SearchTimeout

            undo = self.make(move)
            if i == 0:
                score = -self.search(depth - 1, -beta, -alpha, 1)
            else:
                score = -self.search(depth - 1, -alpha - 1, -alpha, 1)
                if alpha < score < beta:
                    score = -self.search(depth - 1, -beta, -alpha, 1)
            self.unmake(move, undo)

            if score > best:
                best = score
                best_move = move
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        flag = 1 if best >= beta else 0 if best > original_alpha else 2
        self.store(depth, best, flag, best_move, 0)
        return best, best_move


def policy(pieces: dict[str, str], to_play: str) -> str:
    deadline = perf_counter() + 0.90
    side = 1 if to_play in ("white", "w") else -1

    if len(_TT) > 120000:
        _TT.clear()
    if len(_PAWN_CACHE) > 20000:
        _PAWN_CACHE.clear()

    engine = Engine(pieces, side, deadline)
    moves = engine.legal_moves()

    if not moves:
        moves = engine.emergency_ep_moves()

    if not moves:
        # Terminal positions have no legal move. Arenas should not query them.
        return "0000"

    if len(moves) == 1:
        return move_string(moves[0])

    # A fully legal, positionally reasonable fallback is selected before search.
    chosen = moves[0]
    fallback_score = -INF
    for move in moves:
        t = (move >> 7) & 127
        undo = engine.make(move)
        score = -engine.evaluate()
        moved_piece = abs(engine.board[t])
        if moved_piece != K and engine.attacked(t, -side):
            score -= VALUE[moved_piece] * 2 // 3
        engine.unmake(move, undo)
        if score > fallback_score:
            fallback_score = score
            chosen = move

    entry = engine.tt.get(engine.key)
    hint = entry[3] if entry and entry[3] in moves else chosen
    last_score = 0

    try:
        for depth in range(1, 65):
            if perf_counter() >= deadline:
                break
            engine.iteration = depth

            if depth >= 4:
                low, high = last_score - 45, last_score + 45
            else:
                low, high = -INF, INF

            score, move = engine.root(moves, depth, low, high, hint)
            if score <= low or score >= high:
                score, move = engine.root(moves, depth, -INF, INF, move)

            chosen = move
            hint = move
            last_score = score
            if score >= MATE - MAX_PLY:
                break

    except SearchTimeout:
        pass

    return move_string(chosen)
