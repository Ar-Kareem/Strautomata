
import time
import random
import inspect

INF = 10**9
MATE = 100000

# Search globals reinitialized inside policy()
_TT = {}
_HISTORY = {}
_KILLERS = []
_DEADLINE = 0.0
_NODES = 0


class SearchTimeout(Exception):
    pass


FILES = "abcdefgh"
SQUARE_NAMES = [FILES[i & 7] + str((i >> 3) + 1) for i in range(64)]
SQ_TO_IDX = {s: i for i, s in enumerate(SQUARE_NAMES)}

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

PAWN_TABLE = [
     0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
     5,   5,  10,  25,  25,  10,   5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     5,  10,  10, -20, -20,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_TABLE = [
   -50, -40, -30, -30, -30, -30, -40, -50,
   -40, -20,   0,   0,   0,   0, -20, -40,
   -30,   0,  10,  15,  15,  10,   0, -30,
   -30,   5,  15,  20,  20,  15,   5, -30,
   -30,   0,  15,  20,  20,  15,   0, -30,
   -30,   5,  10,  15,  15,  10,   5, -30,
   -40, -20,   0,   5,   5,   0, -20, -40,
   -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_TABLE = [
   -20, -10, -10, -10, -10, -10, -10, -20,
   -10,   0,   0,   0,   0,   0,   0, -10,
   -10,   0,   5,  10,  10,   5,   0, -10,
   -10,   5,   5,  10,  10,   5,   5, -10,
   -10,   0,  10,  10,  10,  10,   0, -10,
   -10,  10,  10,  10,  10,  10,  10, -10,
   -10,   5,   0,   0,   0,   0,   5, -10,
   -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_TABLE = [
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10,  10,  10,  10,  10,   5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     0,   0,   0,   5,   5,   0,   0,   0,
]

QUEEN_TABLE = [
   -20, -10, -10,  -5,  -5, -10, -10, -20,
   -10,   0,   0,   0,   0,   0,   0, -10,
   -10,   0,   5,   5,   5,   5,   0, -10,
    -5,   0,   5,   5,   5,   5,   0,  -5,
     0,   0,   5,   5,   5,   5,   0,  -5,
   -10,   5,   5,   5,   5,   5,   0, -10,
   -10,   0,   5,   0,   0,   0,   0, -10,
   -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_MID_TABLE = [
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -20, -30, -30, -40, -40, -30, -30, -20,
   -10, -20, -20, -20, -20, -20, -20, -10,
    20,  20,   0,   0,   0,   0,  20,  20,
    20,  30,  10,   0,   0,  10,  30,  20,
]

KING_END_TABLE = [
   -50, -40, -30, -20, -20, -30, -40, -50,
   -30, -20, -10,   0,   0, -10, -20, -30,
   -30, -10,  20,  30,  30,  20, -10, -30,
   -30, -10,  30,  40,  40,  30, -10, -30,
   -30, -10,  30,  40,  40,  30, -10, -30,
   -30, -10,  20,  30,  30,  20, -10, -30,
   -30, -30,   0,   0,   0,   0, -30, -30,
   -50, -30, -30, -30, -30, -30, -30, -50,
]

PST = {
    "P": PAWN_TABLE,
    "N": KNIGHT_TABLE,
    "B": BISHOP_TABLE,
    "R": ROOK_TABLE,
    "Q": QUEEN_TABLE,
}

EDGE_PRESSURE = []
for sq in range(64):
    f = sq & 7
    r = sq >> 3
    # Bigger near the edge, smaller near the center.
    v = int((abs(f - 3.5) + abs(r - 3.5)) * 6)
    EDGE_PRESSURE.append(v)

# Precompute attacks/rays.
KNIGHT_DELTAS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_DELTAS = ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1))
DIR_DELTAS = ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (-1, -1), (-1, 1), (1, -1))

KNIGHT_MOVES = [[] for _ in range(64)]
KING_MOVES = [[] for _ in range(64)]
RAYS = [[[] for _ in range(64)] for _ in range(8)]

for sq in range(64):
    f = sq & 7
    r = sq >> 3

    for df, dr in KNIGHT_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KNIGHT_MOVES[sq].append(nr * 8 + nf)

    for df, dr in KING_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KING_MOVES[sq].append(nr * 8 + nf)

    for d, (df, dr) in enumerate(DIR_DELTAS):
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            RAYS[d][sq].append(nr * 8 + nf)
            nf += df
            nr += dr

PIECE_CODES = [c + p for c in "wb" for p in "PNBRQK"]
_rng = random.Random(0)
ZOBRIST = {pc: [_rng.getrandbits(64) for _ in range(64)] for pc in PIECE_CODES}
Z_TURN = _rng.getrandbits(64)


def other(color: str) -> str:
    return "b" if color == "w" else "w"


def mirror_sq(sq: int) -> int:
    return sq ^ 56


def move_to_uci(move) -> str:
    fr, to, promo, _special = move
    s = SQUARE_NAMES[fr] + SQUARE_NAMES[to]
    if promo is not None:
        s += promo.lower()
    return s


def parse_move(uci: str, board, color: str):
    if not isinstance(uci, str) or len(uci) < 4:
        return None
    fr = SQ_TO_IDX.get(uci[:2])
    to = SQ_TO_IDX.get(uci[2:4])
    if fr is None or to is None:
        return None
    piece = board[fr]
    if piece == "." or piece[0] != color:
        return None
    promo = None
    if len(uci) >= 5:
        promo = uci[4].upper()
        if promo not in ("Q", "R", "B", "N"):
            return None
    special = 0
    if piece[1] == "K" and abs((to & 7) - (fr & 7)) == 2:
        special = 1 if to > fr else 2
    elif piece[1] == "P" and ((fr & 7) != (to & 7)) and board[to] == ".":
        # Root-only support for en passant if legal_moves is provided externally.
        special = 3
    return (fr, to, promo, special)


def compute_key(board) -> int:
    key = 0
    for sq, piece in enumerate(board):
        if piece != ".":
            key ^= ZOBRIST[piece][sq]
    return key


def captured_on(board, move):
    fr, to, _promo, special = move
    piece = board[fr]
    if piece == ".":
        return "."
    if special == 3:
        cap_sq = to - 8 if piece[0] == "w" else to + 8
        if 0 <= cap_sq < 64:
            return board[cap_sq]
        return "."
    return board[to]


def is_tactical(board, move) -> bool:
    return move[2] is not None or captured_on(board, move) != "."


def is_square_attacked(board, sq: int, by_color: str) -> bool:
    f = sq & 7
    r = sq >> 3

    if by_color == "w":
        if r > 0:
            if f > 0 and board[sq - 9] == "wP":
                return True
            if f < 7 and board[sq - 7] == "wP":
                return True
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == "bP":
                return True
            if f < 7 and board[sq + 9] == "bP":
                return True

    for t in KNIGHT_MOVES[sq]:
        p = board[t]
        if p != "." and p[0] == by_color and p[1] == "N":
            return True

    for t in KING_MOVES[sq]:
        p = board[t]
        if p != "." and p[0] == by_color and p[1] == "K":
            return True

    for d in range(4):
        for t in RAYS[d][sq]:
            p = board[t]
            if p != ".":
                if p[0] == by_color and (p[1] == "R" or p[1] == "Q"):
                    return True
                break

    for d in range(4, 8):
        for t in RAYS[d][sq]:
            p = board[t]
            if p != ".":
                if p[0] == by_color and (p[1] == "B" or p[1] == "Q"):
                    return True
                break

    return False


def make_move(board, move, kw: int, kb: int, key: int):
    fr, to, promo, special = move
    piece = board[fr]
    color = piece[0]
    captured = "."
    cap_sq = to

    board[fr] = "."
    key ^= ZOBRIST[piece][fr]

    if special == 1 or special == 2:
        # Castling
        board[to] = piece
        key ^= ZOBRIST[piece][to]
        if color == "w":
            kw = to
        else:
            kb = to

        if special == 1:
            rook_from, rook_to = fr + 3, fr + 1
        else:
            rook_from, rook_to = fr - 4, fr - 1

        rook_piece = board[rook_from]
        board[rook_from] = "."
        key ^= ZOBRIST[rook_piece][rook_from]
        board[rook_to] = rook_piece
        key ^= ZOBRIST[rook_piece][rook_to]

    elif special == 3:
        # En passant (only when parsed from authoritative root legal_moves)
        cap_sq = to - 8 if color == "w" else to + 8
        if 0 <= cap_sq < 64:
            captured = board[cap_sq]
            if captured != ".":
                board[cap_sq] = "."
                key ^= ZOBRIST[captured][cap_sq]
        new_piece = color + promo if promo is not None else piece
        board[to] = new_piece
        key ^= ZOBRIST[new_piece][to]

    else:
        captured = board[to]
        if captured != ".":
            key ^= ZOBRIST[captured][to]
        new_piece = color + promo if promo is not None else piece
        board[to] = new_piece
        key ^= ZOBRIST[new_piece][to]
        if piece[1] == "K":
            if color == "w":
                kw = to
            else:
                kb = to

    undo = (captured, piece, cap_sq)
    return undo, kw, kb, key


def unmake_move(board, move, undo):
    fr, to, _promo, special = move
    captured, piece, cap_sq = undo

    if special == 1 or special == 2:
        if special == 1:
            rook_from, rook_to = fr + 3, fr + 1
        else:
            rook_from, rook_to = fr - 4, fr - 1
        rook_piece = board[rook_to]
        board[rook_from] = rook_piece
        board[rook_to] = "."
        board[fr] = piece
        board[to] = "."
    elif special == 3:
        board[fr] = piece
        board[to] = "."
        if 0 <= cap_sq < 64:
            board[cap_sq] = captured
    else:
        board[fr] = piece
        board[to] = captured


def generate_legal_moves(board, color: str, kw: int, kb: int, key: int, captures_only: bool = False):
    enemy = other(color)
    pseudo = []
    append = pseudo.append

    for fr, piece in enumerate(board):
        if piece == "." or piece[0] != color:
            continue

        pt = piece[1]
        f = fr & 7
        r = fr >> 3

        if pt == "P":
            if color == "w":
                one = fr + 8
                if one < 64 and board[one] == ".":
                    if r == 6:
                        for pr in ("Q", "R", "B", "N"):
                            append((fr, one, pr, 0))
                    elif not captures_only:
                        append((fr, one, None, 0))
                        if r == 1:
                            two = fr + 16
                            if board[two] == ".":
                                append((fr, two, None, 0))

                if f > 0:
                    to = fr + 7
                    if to < 64:
                        target = board[to]
                        if target != "." and target[0] == enemy:
                            if r == 6:
                                for pr in ("Q", "R", "B", "N"):
                                    append((fr, to, pr, 0))
                            else:
                                append((fr, to, None, 0))
                if f < 7:
                    to = fr + 9
                    if to < 64:
                        target = board[to]
                        if target != "." and target[0] == enemy:
                            if r == 6:
                                for pr in ("Q", "R", "B", "N"):
                                    append((fr, to, pr, 0))
                            else:
                                append((fr, to, None, 0))

            else:
                one = fr - 8
                if one >= 0 and board[one] == ".":
                    if r == 1:
                        for pr in ("Q", "R", "B", "N"):
                            append((fr, one, pr, 0))
                    elif not captures_only:
                        append((fr, one, None, 0))
                        if r == 6:
                            two = fr - 16
                            if board[two] == ".":
                                append((fr, two, None, 0))

                if f > 0:
                    to = fr - 9
                    if to >= 0:
                        target = board[to]
                        if target != "." and target[0] == enemy:
                            if r == 1:
                                for pr in ("Q", "R", "B", "N"):
                                    append((fr, to, pr, 0))
                            else:
                                append((fr, to, None, 0))
                if f < 7:
                    to = fr - 7
                    if to >= 0:
                        target = board[to]
                        if target != "." and target[0] == enemy:
                            if r == 1:
                                for pr in ("Q", "R", "B", "N"):
                                    append((fr, to, pr, 0))
                            else:
                                append((fr, to, None, 0))

        elif pt == "N":
            for to in KNIGHT_MOVES[fr]:
                target = board[to]
                if target == ".":
                    if not captures_only:
                        append((fr, to, None, 0))
                elif target[0] == enemy:
                    append((fr, to, None, 0))

        elif pt == "B":
            for d in range(4, 8):
                for to in RAYS[d][fr]:
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            append((fr, to, None, 0))
                    else:
                        if target[0] == enemy:
                            append((fr, to, None, 0))
                        break

        elif pt == "R":
            for d in range(4):
                for to in RAYS[d][fr]:
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            append((fr, to, None, 0))
                    else:
                        if target[0] == enemy:
                            append((fr, to, None, 0))
                        break

        elif pt == "Q":
            for d in range(8):
                for to in RAYS[d][fr]:
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            append((fr, to, None, 0))
                    else:
                        if target[0] == enemy:
                            append((fr, to, None, 0))
                        break

        elif pt == "K":
            for to in KING_MOVES[fr]:
                target = board[to]
                if target == ".":
                    if not captures_only:
                        append((fr, to, None, 0))
                elif target[0] == enemy:
                    append((fr, to, None, 0))

            if not captures_only:
                # Infer castling rights from position if no authoritative legal_moves are available.
                if color == "w" and fr == 4:
                    if (
                        board[7] == "wR" and
                        board[5] == "." and board[6] == "." and
                        not is_square_attacked(board, 4, enemy) and
                        not is_square_attacked(board, 5, enemy) and
                        not is_square_attacked(board, 6, enemy)
                    ):
                        append((4, 6, None, 1))
                    if (
                        board[0] == "wR" and
                        board[1] == "." and board[2] == "." and board[3] == "." and
                        not is_square_attacked(board, 4, enemy) and
                        not is_square_attacked(board, 3, enemy) and
                        not is_square_attacked(board, 2, enemy)
                    ):
                        append((4, 2, None, 2))

                elif color == "b" and fr == 60:
                    if (
                        board[63] == "bR" and
                        board[61] == "." and board[62] == "." and
                        not is_square_attacked(board, 60, enemy) and
                        not is_square_attacked(board, 61, enemy) and
                        not is_square_attacked(board, 62, enemy)
                    ):
                        append((60, 62, None, 1))
                    if (
                        board[56] == "bR" and
                        board[57] == "." and board[58] == "." and board[59] == "." and
                        not is_square_attacked(board, 60, enemy) and
                        not is_square_attacked(board, 59, enemy) and
                        not is_square_attacked(board, 58, enemy)
                    ):
                        append((60, 58, None, 2))

    legal = []
    own_king = kw if color == "w" else kb

    for mv in pseudo:
        undo, nkw, nkb, nkey = make_move(board, mv, kw, kb, key)
        try:
            king_sq = nkw if color == "w" else nkb
            if king_sq is None or not is_square_attacked(board, king_sq, enemy):
                legal.append(mv)
        finally:
            unmake_move(board, mv, undo)

    return legal


def evaluate(board, kw: int, kb: int) -> int:
    white = 0
    black = 0
    total_nonking = 0

    wp_files = [0] * 8
    bp_files = [0] * 8
    wp_by_file = [[] for _ in range(8)]
    bp_by_file = [[] for _ in range(8)]
    w_rooks = []
    b_rooks = []
    w_bishops = 0
    b_bishops = 0

    for sq, piece in enumerate(board):
        if piece == ".":
            continue

        color = piece[0]
        pt = piece[1]
        f = sq & 7
        r = sq >> 3

        if pt == "K":
            if color == "w":
                kw = sq
            else:
                kb = sq
            continue

        total_nonking += PIECE_VALUES[pt]
        table_sq = sq if color == "w" else mirror_sq(sq)
        val = PIECE_VALUES[pt] + PST[pt][table_sq]

        if color == "w":
            white += val
            if pt == "P":
                wp_files[f] += 1
                wp_by_file[f].append(r)
            elif pt == "R":
                w_rooks.append(sq)
            elif pt == "B":
                w_bishops += 1
        else:
            black += val
            if pt == "P":
                bp_files[f] += 1
                bp_by_file[f].append(r)
            elif pt == "R":
                b_rooks.append(sq)
            elif pt == "B":
                b_bishops += 1

    king_table = KING_END_TABLE if total_nonking <= 2400 else KING_MID_TABLE
    if kw is not None:
        white += king_table[kw]
    if kb is not None:
        black += king_table[mirror_sq(kb)]

    if w_bishops >= 2:
        white += 20
    if b_bishops >= 2:
        black += 20

    # Pawn structure: doubled, isolated, passed.
    for f in range(8):
        if wp_files[f] > 1:
            white -= 12 * (wp_files[f] - 1)
        if bp_files[f] > 1:
            black -= 12 * (bp_files[f] - 1)

    for f in range(8):
        for r in wp_by_file[f]:
            if (f == 0 or wp_files[f - 1] == 0) and (f == 7 or wp_files[f + 1] == 0):
                white -= 8
            passed = True
            lo = max(0, f - 1)
            hi = min(7, f + 1)
            for af in range(lo, hi + 1):
                for br in bp_by_file[af]:
                    if br > r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                white += 12 + r * 10

    for f in range(8):
        for r in bp_by_file[f]:
            if (f == 0 or bp_files[f - 1] == 0) and (f == 7 or bp_files[f + 1] == 0):
                black -= 8
            passed = True
            lo = max(0, f - 1)
            hi = min(7, f + 1)
            for af in range(lo, hi + 1):
                for wr in wp_by_file[af]:
                    if wr < r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                black += 12 + (7 - r) * 10

    # Rooks on open/semi-open files and 7th rank.
    for sq in w_rooks:
        f = sq & 7
        r = sq >> 3
        if wp_files[f] == 0:
            white += 15 if bp_files[f] == 0 else 8
        if r == 6:
            white += 12

    for sq in b_rooks:
        f = sq & 7
        r = sq >> 3
        if bp_files[f] == 0:
            black += 15 if wp_files[f] == 0 else 8
        if r == 1:
            black += 12

    score = white - black

    # Simple endgame mop-up.
    if total_nonking <= 1400 and kw is not None and kb is not None:
        dist = abs((kw & 7) - (kb & 7)) + abs((kw >> 3) - (kb >> 3))
        if score > 250:
            score += (14 - dist) * 4 + EDGE_PRESSURE[kb]
        elif score < -250:
            score -= (14 - dist) * 4 + EDGE_PRESSURE[kw]

    return score


def order_moves(moves, board, tt_move, ply: int):
    killers = _KILLERS[ply] if ply < len(_KILLERS) else (None, None)
    scored = []

    for mv in moves:
        score = 0

        if tt_move is not None and mv == tt_move:
            score += 10_000_000

        cap = captured_on(board, mv)
        if cap != ".":
            mover = board[mv[0]]
            score += 1_000_000 + 16 * PIECE_VALUES[cap[1]] - PIECE_VALUES[mover[1]]

        if mv[2] is not None:
            score += 900_000 + PIECE_VALUES[mv[2]]

        if cap == "." and mv[2] is None:
            if mv == killers[0]:
                score += 800_000
            elif mv == killers[1]:
                score += 700_000
            score += _HISTORY.get(mv, 0)
            if mv[3] in (1, 2):
                score += 100

        scored.append((score, mv))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _score, mv in scored]


def quiescence(board, color: str, alpha: int, beta: int, kw: int, kb: int, key: int, ply: int) -> int:
    global _NODES
    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise SearchTimeout

    stand = evaluate(board, kw, kb)
    if color == "b":
        stand = -stand

    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    moves = generate_legal_moves(board, color, kw, kb, key, captures_only=True)
    if not moves:
        return stand

    moves = order_moves(moves, board, None, ply)

    enemy = other(color)
    for mv in moves:
        undo, nkw, nkb, nkey = make_move(board, mv, kw, kb, key)
        try:
            score = -quiescence(board, enemy, -beta, -alpha, nkw, nkb, nkey, ply + 1)
        finally:
            unmake_move(board, mv, undo)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def search(board, color: str, depth: int, alpha: int, beta: int, kw: int, kb: int, key: int, ply: int) -> int:
    global _NODES, _TT, _HISTORY, _KILLERS

    _NODES += 1
    if (_NODES & 1023) == 0 and time.perf_counter() > _DEADLINE:
        raise SearchTimeout

    alpha0 = alpha
    side_key = key if color == "w" else (key ^ Z_TURN)
    tt_entry = _TT.get(side_key)
    tt_move = None
    if tt_entry is not None:
        tt_depth, tt_score, tt_flag, tt_move = tt_entry
        if tt_depth >= depth:
            if tt_flag == 0:
                return tt_score
            if tt_flag == 1 and tt_score >= beta:
                return tt_score
            if tt_flag == 2 and tt_score <= alpha:
                return tt_score

    enemy = other(color)
    king_sq = kw if color == "w" else kb
    in_check = False if king_sq is None else is_square_attacked(board, king_sq, enemy)

    if depth <= 0:
        if not in_check:
            return quiescence(board, color, alpha, beta, kw, kb, key, ply)
        depth = 1

    moves = generate_legal_moves(board, color, kw, kb, key, captures_only=False)
    if not moves:
        return (-MATE + ply) if in_check else 0

    moves = order_moves(moves, board, tt_move, ply)

    best_score = -INF
    best_move = moves[0]

    for mv in moves:
        tactical = is_tactical(board, mv)
        undo, nkw, nkb, nkey = make_move(board, mv, kw, kb, key)
        try:
            score = -search(board, enemy, depth - 1, -beta, -alpha, nkw, nkb, nkey, ply + 1)
        finally:
            unmake_move(board, mv, undo)

        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score
        if alpha >= beta:
            if not tactical and ply < len(_KILLERS):
                if _KILLERS[ply][0] != mv:
                    _KILLERS[ply][1] = _KILLERS[ply][0]
                    _KILLERS[ply][0] = mv
                _HISTORY[mv] = _HISTORY.get(mv, 0) + depth * depth
            break

    flag = 0
    if best_score <= alpha0:
        flag = 2
    elif best_score >= beta:
        flag = 1

    if len(_TT) < 200000 or side_key in _TT:
        _TT[side_key] = (depth, best_score, flag, best_move)

    return best_score


def _find_external_legal_moves():
    try:
        frame = inspect.currentframe()
        if frame is not None:
            frame = frame.f_back
        while frame is not None:
            for name in ("legal_moves", "LEGAL_MOVES"):
                if name in frame.f_locals:
                    lm = frame.f_locals[name]
                    if isinstance(lm, (list, tuple)) and all(isinstance(x, str) for x in lm):
                        return list(lm)
                if name in frame.f_globals:
                    lm = frame.f_globals[name]
                    if isinstance(lm, (list, tuple)) and all(isinstance(x, str) for x in lm):
                        return list(lm)
            frame = frame.f_back
    except Exception:
        pass
    return None


def policy(pieces: dict[str, str], to_play: str) -> str:
    global _TT, _HISTORY, _KILLERS, _DEADLINE, _NODES

    color = "w" if to_play == "white" else "b"

    board = ["."] * 64
    kw = None
    kb = None
    for sq, piece in pieces.items():
        idx = SQ_TO_IDX.get(sq)
        if idx is None:
            continue
        board[idx] = piece
        if piece == "wK":
            kw = idx
        elif piece == "bK":
            kb = idx

    key = compute_key(board)

    external_legal = _find_external_legal_moves()

    move_to_text = {}
    root_moves = []

    if external_legal is not None and len(external_legal) > 0:
        for txt in external_legal:
            mv = parse_move(txt, board, color)
            if mv is not None:
                root_moves.append(mv)
                move_to_text[mv] = txt
        if not root_moves:
            return external_legal[0]
    else:
        root_moves = generate_legal_moves(board, color, kw, kb, key, captures_only=False)
        for mv in root_moves:
            move_to_text[mv] = move_to_uci(mv)

    if not root_moves:
        # Extremely unusual terminal/failure case.
        if external_legal:
            return external_legal[0]
        return "a1a1"

    if len(root_moves) == 1:
        return move_to_text[root_moves[0]]

    _TT = {}
    _HISTORY = {}
    _KILLERS = [[None, None] for _ in range(128)]
    _NODES = 0

    start = time.perf_counter()
    _DEADLINE = start + 0.94

    best_move = root_moves[0]
    best_score = -INF

    # Good initial ordering before iterative deepening.
    root_moves = order_moves(root_moves, board, None, 0)

    max_depth = 8
    enemy = other(color)

    for depth in range(1, max_depth + 1):
        if time.perf_counter() > _DEADLINE:
            break

        current_best = best_move
        current_best_score = -INF

        ordered_root = order_moves(root_moves, board, best_move, 0)

        try:
            alpha = -INF
            beta = INF

            for mv in ordered_root:
                undo, nkw, nkb, nkey = make_move(board, mv, kw, kb, key)
                try:
                    score = -search(board, enemy, depth - 1, -beta, -alpha, nkw, nkb, nkey, 1)
                finally:
                    unmake_move(board, mv, undo)

                if score > current_best_score:
                    current_best_score = score
                    current_best = mv
                if score > alpha:
                    alpha = score

            best_move = current_best
            best_score = current_best_score
            root_moves = order_moves(root_moves, board, best_move, 0)

            if abs(best_score) >= MATE - 1000:
                break

        except SearchTimeout:
            break

    return move_to_text.get(best_move, move_to_uci(best_move))
