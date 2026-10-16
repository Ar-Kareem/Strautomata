
from __future__ import annotations
import time

FILES = "abcdefgh"
SQUARES = [chr(97 + f) + str(r + 1) for r in range(8) for f in range(8)]
SQ_TO_IDX = {sq: i for i, sq in enumerate(SQUARES)}
MIRROR = [((7 - (i >> 3)) * 8 + (i & 7)) for i in range(64)]

OPP = {"w": "b", "b": "w"}
PROMOS = ("q", "r", "b", "n")

PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
PROMO_VALUES = {"q": 900, "r": 500, "b": 330, "n": 320}
PHASE = {"N": 1, "B": 1, "R": 2, "Q": 4}

MATE_SCORE = 1000000
INF = 1000000000

KNIGHT_STEPS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_STEPS = ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1))
BISHOP_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ROOK_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


def _pst(rows_rank8_to_rank1):
    arr = []
    for row in reversed(rows_rank8_to_rank1):
        arr.extend(row)
    return arr


PAWN_PST = _pst([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5, 5, 10, 25, 25, 10, 5, 5],
    [0, 0, 0, 20, 20, 0, 0, 0],
    [5, -5, -10, 0, 0, -10, -5, 5],
    [5, 10, 10, -20, -20, 10, 10, 5],
    [0, 0, 0, 0, 0, 0, 0, 0],
])

KNIGHT_PST = _pst([
    [-50, -40, -30, -30, -30, -30, -40, -50],
    [-40, -20, 0, 5, 5, 0, -20, -40],
    [-30, 5, 10, 15, 15, 10, 5, -30],
    [-30, 0, 15, 20, 20, 15, 0, -30],
    [-30, 5, 15, 20, 20, 15, 5, -30],
    [-30, 0, 10, 15, 15, 10, 0, -30],
    [-40, -20, 0, 0, 0, 0, -20, -40],
    [-50, -40, -30, -30, -30, -30, -40, -50],
])

BISHOP_PST = _pst([
    [-20, -10, -10, -10, -10, -10, -10, -20],
    [-10, 5, 0, 0, 0, 0, 5, -10],
    [-10, 10, 10, 10, 10, 10, 10, -10],
    [-10, 0, 10, 10, 10, 10, 0, -10],
    [-10, 5, 5, 10, 10, 5, 5, -10],
    [-10, 0, 5, 10, 10, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -10, -10, -10, -10, -20],
])

ROOK_PST = _pst([
    [0, 0, 0, 0, 0, 0, 0, 0],
    [5, 10, 10, 10, 10, 10, 10, 5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [-5, 0, 0, 0, 0, 0, 0, -5],
    [0, 0, 0, 5, 5, 0, 0, 0],
])

QUEEN_PST = _pst([
    [-20, -10, -10, -5, -5, -10, -10, -20],
    [-10, 0, 5, 0, 0, 0, 0, -10],
    [-10, 5, 5, 5, 5, 5, 0, -10],
    [0, 0, 5, 5, 5, 5, 0, -5],
    [-5, 0, 5, 5, 5, 5, 0, -5],
    [-10, 0, 5, 5, 5, 5, 0, -10],
    [-10, 0, 0, 0, 0, 0, 0, -10],
    [-20, -10, -10, -5, -5, -10, -10, -20],
])

KING_MID_PST = _pst([
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-30, -40, -40, -50, -50, -40, -40, -30],
    [-20, -30, -30, -40, -40, -30, -30, -20],
    [-10, -20, -20, -20, -20, -20, -20, -10],
    [20, 20, 0, 0, 0, 0, 20, 20],
    [20, 30, 10, 0, 0, 10, 30, 20],
])

KING_END_PST = _pst([
    [-50, -40, -30, -20, -20, -30, -40, -50],
    [-30, -20, -10, 0, 0, -10, -20, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 30, 40, 40, 30, -10, -30],
    [-30, -10, 20, 30, 30, 20, -10, -30],
    [-30, -30, 0, 0, 0, 0, -30, -30],
    [-50, -30, -30, -30, -30, -30, -30, -50],
])

PST = {"P": PAWN_PST, "N": KNIGHT_PST, "B": BISHOP_PST, "R": ROOK_PST, "Q": QUEEN_PST}

PIECE_CODES = ["wP", "wN", "wB", "wR", "wQ", "wK", "bP", "bN", "bB", "bR", "bQ", "bK"]
PIECE_TO_ID = {p: i for i, p in enumerate(PIECE_CODES)}
MASK64 = (1 << 64) - 1


def _splitmix64(x):
    x = (x + 0x9E3779B97F4A7C15) & MASK64
    z = x
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK64
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK64
    return (z ^ (z >> 31)) & MASK64


ZOBRIST = [[_splitmix64(0xC0FFEE + 97 * i + 13 * j) for j in range(12)] for i in range(64)]


def _make_start_board():
    b = [None] * 64
    back = "RNBQKBNR"
    for f, p in enumerate(back):
        b[f] = "w" + p
        b[8 + f] = "wP"
        b[48 + f] = "bP"
        b[56 + f] = "b" + p
    return b


START_BOARD = _make_start_board()

ORIGINAL_MINORS = (
    (SQ_TO_IDX["b1"], "wN"), (SQ_TO_IDX["g1"], "wN"),
    (SQ_TO_IDX["c1"], "wB"), (SQ_TO_IDX["f1"], "wB"),
    (SQ_TO_IDX["b8"], "bN"), (SQ_TO_IDX["g8"], "bN"),
    (SQ_TO_IDX["c8"], "bB"), (SQ_TO_IDX["f8"], "bB"),
)

PASSED_BONUS = [0, 0, 8, 18, 35, 60, 100, 0]


class SearchTimeout(Exception):
    pass


def _board_from_pieces(pieces):
    board = [None] * 64
    for sq, pc in pieces.items():
        idx = SQ_TO_IDX.get(sq)
        if idx is not None and isinstance(pc, str) and len(pc) == 2:
            if pc[0] in ("w", "b") and pc[1] in PIECE_VALUES:
                board[idx] = pc
    return board


def compute_hash(board):
    h = 0
    for i, p in enumerate(board):
        if p is not None:
            pid = PIECE_TO_ID.get(p)
            if pid is not None:
                h ^= ZOBRIST[i][pid]
    return h


def find_king(board, color):
    target = color + "K"
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1


def is_attacked(board, sq, by_color):
    if sq < 0 or sq >= 64:
        return False

    f = sq & 7
    r = sq >> 3
    pawn = by_color + "P"

    if by_color == "w":
        rr = r - 1
        if rr >= 0:
            if f > 0 and board[rr * 8 + f - 1] == pawn:
                return True
            if f < 7 and board[rr * 8 + f + 1] == pawn:
                return True
    else:
        rr = r + 1
        if rr < 8:
            if f > 0 and board[rr * 8 + f - 1] == pawn:
                return True
            if f < 7 and board[rr * 8 + f + 1] == pawn:
                return True

    knight = by_color + "N"
    for df, dr in KNIGHT_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == knight:
            return True

    king = by_color + "K"
    for df, dr in KING_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == king:
            return True

    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p is not None:
                if p[0] == by_color and (p[1] == "B" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p is not None:
                if p[0] == by_color and (p[1] == "R" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    return False


def in_check(board, color):
    k = find_king(board, color)
    if k < 0:
        return False
    return is_attacked(board, k, OPP[color])


def _add_board_castles(board, color, king_sq, moves):
    # Only used when explicitly requested. Normal search avoids castling unless supplied externally,
    # because castling rights are not part of the input representation.
    opp = OPP[color]
    if color == "w" and king_sq == SQ_TO_IDX["e1"]:
        if board[SQ_TO_IDX["h1"]] == "wR" and board[SQ_TO_IDX["f1"]] is None and board[SQ_TO_IDX["g1"]] is None:
            if not is_attacked(board, SQ_TO_IDX["e1"], opp) and not is_attacked(board, SQ_TO_IDX["f1"], opp) and not is_attacked(board, SQ_TO_IDX["g1"], opp):
                moves.append((SQ_TO_IDX["e1"], SQ_TO_IDX["g1"], "", "c"))
        if board[SQ_TO_IDX["a1"]] == "wR" and board[SQ_TO_IDX["d1"]] is None and board[SQ_TO_IDX["c1"]] is None and board[SQ_TO_IDX["b1"]] is None:
            if not is_attacked(board, SQ_TO_IDX["e1"], opp) and not is_attacked(board, SQ_TO_IDX["d1"], opp) and not is_attacked(board, SQ_TO_IDX["c1"], opp):
                moves.append((SQ_TO_IDX["e1"], SQ_TO_IDX["c1"], "", "c"))
    elif color == "b" and king_sq == SQ_TO_IDX["e8"]:
        if board[SQ_TO_IDX["h8"]] == "bR" and board[SQ_TO_IDX["f8"]] is None and board[SQ_TO_IDX["g8"]] is None:
            if not is_attacked(board, SQ_TO_IDX["e8"], opp) and not is_attacked(board, SQ_TO_IDX["f8"], opp) and not is_attacked(board, SQ_TO_IDX["g8"], opp):
                moves.append((SQ_TO_IDX["e8"], SQ_TO_IDX["g8"], "", "c"))
        if board[SQ_TO_IDX["a8"]] == "bR" and board[SQ_TO_IDX["d8"]] is None and board[SQ_TO_IDX["c8"]] is None and board[SQ_TO_IDX["b8"]] is None:
            if not is_attacked(board, SQ_TO_IDX["e8"], opp) and not is_attacked(board, SQ_TO_IDX["d8"], opp) and not is_attacked(board, SQ_TO_IDX["c8"], opp):
                moves.append((SQ_TO_IDX["e8"], SQ_TO_IDX["c8"], "", "c"))


def generate_pseudo_moves(board, color, tactical=False, include_castles=False):
    moves = []
    for i, p in enumerate(board):
        if p is None or p[0] != color:
            continue

        t = p[1]
        f = i & 7
        r = i >> 3

        if t == "P":
            dr = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promo_rank = 7 if color == "w" else 0

            nr = r + dr
            if 0 <= nr < 8:
                one = nr * 8 + f
                if board[one] is None:
                    if nr == promo_rank:
                        for pr in PROMOS:
                            moves.append((i, one, pr, ""))
                    elif not tactical:
                        moves.append((i, one, "", ""))
                        if r == start_rank:
                            nr2 = r + 2 * dr
                            two = nr2 * 8 + f
                            if board[two] is None:
                                moves.append((i, two, "", ""))

                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if target is not None and target[0] != color and target[1] != "K":
                            if nr == promo_rank:
                                for pr in PROMOS:
                                    moves.append((i, to, pr, ""))
                            else:
                                moves.append((i, to, "", ""))

        elif t == "N":
            for df, dr in KNIGHT_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not tactical:
                            moves.append((i, to, "", ""))
                    elif target[0] != color and target[1] != "K":
                        moves.append((i, to, "", ""))

        elif t == "B" or t == "R" or t == "Q":
            dirs = BISHOP_DIRS if t == "B" else ROOK_DIRS if t == "R" else BISHOP_DIRS + ROOK_DIRS
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not tactical:
                            moves.append((i, to, "", ""))
                    else:
                        if target[0] != color and target[1] != "K":
                            moves.append((i, to, "", ""))
                        break
                    nf += df
                    nr += dr

        elif t == "K":
            for df, dr in KING_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not tactical:
                            moves.append((i, to, "", ""))
                    elif target[0] != color and target[1] != "K":
                        moves.append((i, to, "", ""))

            if include_castles and not tactical:
                _add_board_castles(board, color, i, moves)

    return moves


def make_move_simple(board, m):
    fr, to, promo, flag = m
    piece = board[fr]
    if piece is None:
        return None

    if flag == "c":
        rook_from = (fr >> 3) * 8 + (7 if to > fr else 0)
        rook_to = fr + (1 if to > fr else -1)
        cap_to = board[to]
        rook = board[rook_from]
        cap_rook_to = board[rook_to]
        board[fr] = None
        board[to] = piece
        board[rook_from] = None
        board[rook_to] = rook
        return (piece, cap_to, rook_from, rook_to, rook, cap_rook_to)

    if flag == "e":
        cap_sq = to - 8 if piece[0] == "w" else to + 8
        cap = board[cap_sq] if 0 <= cap_sq < 64 else None
        board[fr] = None
        board[to] = piece
        if 0 <= cap_sq < 64:
            board[cap_sq] = None
        return (piece, cap_sq, cap)

    cap = board[to]
    new_piece = piece[0] + promo.upper() if promo else piece
    board[fr] = None
    board[to] = new_piece
    return (piece, cap)


def undo_move_simple(board, m, undo):
    if undo is None:
        return

    fr, to, promo, flag = m
    if flag == "c":
        piece, cap_to, rook_from, rook_to, rook, cap_rook_to = undo
        board[fr] = piece
        board[to] = cap_to
        board[rook_from] = rook
        board[rook_to] = cap_rook_to
    elif flag == "e":
        piece, cap_sq, cap = undo
        board[fr] = piece
        board[to] = None
        if 0 <= cap_sq < 64:
            board[cap_sq] = cap
    else:
        piece, cap = undo
        board[fr] = piece
        board[to] = cap


def make_move_hash(board, m, h):
    fr, to, promo, flag = m
    piece = board[fr]
    if piece is None:
        return None, h

    nh = h

    if flag == "c":
        rook_from = (fr >> 3) * 8 + (7 if to > fr else 0)
        rook_to = fr + (1 if to > fr else -1)

        cap_to = board[to]
        rook = board[rook_from]
        cap_rook_to = board[rook_to]

        nh ^= ZOBRIST[fr][PIECE_TO_ID[piece]]
        if cap_to is not None:
            nh ^= ZOBRIST[to][PIECE_TO_ID[cap_to]]
        nh ^= ZOBRIST[to][PIECE_TO_ID[piece]]

        if rook is not None:
            nh ^= ZOBRIST[rook_from][PIECE_TO_ID[rook]]
        if cap_rook_to is not None:
            nh ^= ZOBRIST[rook_to][PIECE_TO_ID[cap_rook_to]]
        if rook is not None:
            nh ^= ZOBRIST[rook_to][PIECE_TO_ID[rook]]

        board[fr] = None
        board[to] = piece
        board[rook_from] = None
        board[rook_to] = rook
        return (piece, cap_to, rook_from, rook_to, rook, cap_rook_to), nh

    if flag == "e":
        cap_sq = to - 8 if piece[0] == "w" else to + 8
        cap = board[cap_sq] if 0 <= cap_sq < 64 else None

        nh ^= ZOBRIST[fr][PIECE_TO_ID[piece]]
        if cap is not None:
            nh ^= ZOBRIST[cap_sq][PIECE_TO_ID[cap]]
        nh ^= ZOBRIST[to][PIECE_TO_ID[piece]]

        board[fr] = None
        board[to] = piece
        if 0 <= cap_sq < 64:
            board[cap_sq] = None
        return (piece, cap_sq, cap), nh

    cap = board[to]
    new_piece = piece[0] + promo.upper() if promo else piece

    nh ^= ZOBRIST[fr][PIECE_TO_ID[piece]]
    if cap is not None:
        nh ^= ZOBRIST[to][PIECE_TO_ID[cap]]
    nh ^= ZOBRIST[to][PIECE_TO_ID[new_piece]]

    board[fr] = None
    board[to] = new_piece
    return (piece, cap), nh


def generate_legal(board, color, tactical=False, include_castles=False):
    legal = []
    for m in generate_pseudo_moves(board, color, tactical, include_castles):
        undo = make_move_simple(board, m)
        if undo is None:
            continue
        try:
            if not in_check(board, color):
                legal.append(m)
        finally:
            undo_move_simple(board, m, undo)
    return legal


def move_to_uci(m):
    return SQUARES[m[0]] + SQUARES[m[1]] + (m[2] if m[2] else "")


def parse_uci_move(s, board):
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    if len(s) not in (4, 5):
        return None
    fr = SQ_TO_IDX.get(s[:2])
    to = SQ_TO_IDX.get(s[2:4])
    if fr is None or to is None:
        return None
    promo = ""
    if len(s) == 5:
        promo = s[4].lower()
        if promo not in PROMOS:
            return None

    flag = ""
    piece = board[fr]
    if piece is not None:
        if piece[1] == "K" and abs((to & 7) - (fr & 7)) == 2:
            flag = "c"
        elif piece[1] == "P" and (to & 7) != (fr & 7) and board[to] is None:
            flag = "e"
    return (fr, to, promo, flag)


def captured_piece_for_move(board, m):
    fr, to, promo, flag = m
    piece = board[fr]
    if piece is None:
        return None
    if flag == "e":
        cap_sq = to - 8 if piece[0] == "w" else to + 8
        return board[cap_sq] if 0 <= cap_sq < 64 else None
    if flag == "c":
        return None
    return board[to]


def move_order_score(board, m, side, tt_move=None, ply=0, killers=None, history=None):
    if tt_move is not None and m == tt_move:
        return 10000000

    fr, to, promo, flag = m
    piece = board[fr]
    if piece is None:
        return -10000000

    score = 0
    cap = captured_piece_for_move(board, m)

    if cap is not None:
        score += 1000000 + 10 * PIECE_VALUES.get(cap[1], 0) - PIECE_VALUES.get(piece[1], 0)

    if promo:
        score += 900000 + PROMO_VALUES.get(promo, 0)

    if flag == "c":
        score += 50000

    if killers is not None and ply < len(killers):
        if m == killers[ply][0] or m == killers[ply][1]:
            score += 800000

    if history is not None:
        score += history.get((side, fr, to, promo), 0)

    t = piece[1]
    if t in PST:
        idx_to = to if side == "w" else MIRROR[to]
        idx_fr = fr if side == "w" else MIRROR[fr]
        score += PST[t][idx_to] - PST[t][idx_fr]

    tf = to & 7
    tr = to >> 3
    center_dist = abs(tf - 3.5) + abs(tr - 3.5)
    score += int(14 - 2 * center_dist)

    return score


def _mop_up_bonus(own_king, enemy_king):
    of, orank = own_king & 7, own_king >> 3
    ef, erank = enemy_king & 7, enemy_king >> 3
    edge = min(ef, 7 - ef, erank, 7 - erank)
    edge_bonus = (3.5 - edge) * 24
    dist = abs(of - ef) + abs(orank - erank)
    close_bonus = (14 - dist) * 4
    return edge_bonus + close_bonus


def evaluate(board, side):
    score = 0.0
    phase = 0
    material = {"w": 0, "b": 0}
    bishops = {"w": 0, "b": 0}
    pawns_files = {"w": [0] * 8, "b": [0] * 8}
    pawn_squares = {"w": [], "b": []}
    rooks = {"w": [], "b": []}
    kings = {"w": -1, "b": -1}

    for i, p in enumerate(board):
        if p is None:
            continue
        c, t = p[0], p[1]
        sign = 1 if c == "w" else -1
        val = PIECE_VALUES[t]
        material[c] += val

        if t not in ("P", "K"):
            phase += PHASE.get(t, 0)

        idx = i if c == "w" else MIRROR[i]

        if t == "K":
            kings[c] = i
        else:
            score += sign * (val + PST[t][idx])

        if t == "B":
            bishops[c] += 1
        elif t == "P":
            pawns_files[c][i & 7] += 1
            pawn_squares[c].append(i)
        elif t == "R":
            rooks[c].append(i)

    phase = min(24, phase)
    mid = phase / 24.0
    end = 1.0 - mid

    for c in ("w", "b"):
        k = kings[c]
        if k >= 0:
            sign = 1 if c == "w" else -1
            idx = k if c == "w" else MIRROR[k]
            score += sign * (mid * KING_MID_PST[idx] + end * KING_END_PST[idx])

    for c in ("w", "b"):
        sign = 1 if c == "w" else -1
        if bishops[c] >= 2:
            score += sign * 35

    for c in ("w", "b"):
        sign = 1 if c == "w" else -1
        enemy = OPP[c]
        pf = pawns_files[c]

        for f, count in enumerate(pf):
            if count > 1:
                score -= sign * 12 * (count - 1)

        for sq in pawn_squares[c]:
            f = sq & 7
            r = sq >> 3
            adv = r if c == "w" else 7 - r

            if (f == 0 or pf[f - 1] == 0) and (f == 7 or pf[f + 1] == 0):
                score -= sign * 10

            passed = True
            for esq in pawn_squares[enemy]:
                ef = esq & 7
                er = esq >> 3
                if abs(ef - f) <= 1 and ((c == "w" and er > r) or (c == "b" and er < r)):
                    passed = False
                    break
            if passed:
                base = PASSED_BONUS[adv]
                score += sign * (base + base * 0.6 * end)

            br = r - 1 if c == "w" else r + 1
            protected = False
            if 0 <= br < 8:
                if f > 0 and board[br * 8 + f - 1] == c + "P":
                    protected = True
                if f < 7 and board[br * 8 + f + 1] == c + "P":
                    protected = True
            if protected:
                score += sign * 5

            if f > 0 and board[r * 8 + f - 1] == c + "P":
                score += sign * 3
            if f < 7 and board[r * 8 + f + 1] == c + "P":
                score += sign * 3

    for c in ("w", "b"):
        sign = 1 if c == "w" else -1
        enemy = OPP[c]
        for sq in rooks[c]:
            f = sq & 7
            r = sq >> 3
            bonus = 0
            if pawns_files[c][f] == 0:
                bonus += 8
                if pawns_files[enemy][f] == 0:
                    bonus += 10
            if (c == "w" and r == 6) or (c == "b" and r == 1):
                bonus += 18
            score += sign * bonus

    if mid > 0:
        for c in ("w", "b"):
            k = kings[c]
            if k < 0:
                continue
            sign = 1 if c == "w" else -1
            f = k & 7
            r = k >> 3
            step = 1 if c == "w" else -1
            shield = 0
            r1 = r + step
            r2 = r + 2 * step
            for df in (-1, 0, 1):
                nf = f + df
                if 0 <= nf < 8:
                    if 0 <= r1 < 8 and board[r1 * 8 + nf] == c + "P":
                        shield += 2
                    elif 0 <= r2 < 8 and board[r2 * 8 + nf] == c + "P":
                        shield += 1

            penalty = max(0, 6 - shield) * 5
            for nf in range(max(0, f - 1), min(7, f + 1) + 1):
                if pawns_files[c][nf] == 0:
                    penalty += 6
                    if pawns_files[OPP[c]][nf] == 0:
                        penalty += 4

            if c == "w" and r >= 2:
                penalty += (r - 1) * 8
            elif c == "b" and r <= 5:
                penalty += (6 - r) * 8

            score -= sign * penalty * mid

    if kings["w"] >= 0 and kings["b"] >= 0 and end > 0.25:
        diff = material["w"] - material["b"]
        if diff > 250:
            score += _mop_up_bonus(kings["w"], kings["b"]) * end
        elif diff < -250:
            score -= _mop_up_bonus(kings["b"], kings["w"]) * end

    if mid > 0.65:
        for sq, pc in ORIGINAL_MINORS:
            if board[sq] == pc:
                sign = 1 if pc[0] == "w" else -1
                score -= sign * 7 * mid

        if board[SQ_TO_IDX["e4"]] == "wP":
            score += 8 * mid
        if board[SQ_TO_IDX["d4"]] == "wP":
            score += 8 * mid
        if board[SQ_TO_IDX["e5"]] == "bP":
            score -= 8 * mid
        if board[SQ_TO_IDX["d5"]] == "bP":
            score -= 8 * mid

    return int((score if side == "w" else -score) + 8)


def _matches_start_changes(board, changes):
    mapped = {}
    for sq, pc in changes.items():
        idx = SQ_TO_IDX.get(sq)
        if idx is not None:
            mapped[idx] = pc
    for i, base in enumerate(START_BOARD):
        if board[i] != mapped.get(i, base):
            return False
    return True


def _first_legal(legal_uci, *moves):
    for m in moves:
        if m in legal_uci:
            return m
    return None


def _choose_book_move(board, color, legal_uci):
    if board == START_BOARD:
        if color == "w":
            return _first_legal(legal_uci, "e2e4", "d2d4", "g1f3", "c2c4")
        return _first_legal(legal_uci, "e7e5", "d7d5", "g8f6", "c7c5")

    if color == "b":
        if _matches_start_changes(board, {"e2": None, "e4": "wP"}):
            return _first_legal(legal_uci, "c7c5", "e7e5", "c7c6", "e7e6")
        if _matches_start_changes(board, {"d2": None, "d4": "wP"}):
            return _first_legal(legal_uci, "g8f6", "d7d5", "e7e6", "c7c5")
        if _matches_start_changes(board, {"c2": None, "c4": "wP"}):
            return _first_legal(legal_uci, "e7e5", "g8f6", "c7c5")
        if _matches_start_changes(board, {"g1": None, "f3": "wN"}):
            return _first_legal(legal_uci, "d7d5", "g8f6", "c7c5")
    else:
        if _matches_start_changes(board, {"e2": None, "e4": "wP", "e7": None, "e5": "bP"}):
            return _first_legal(legal_uci, "g1f3", "f1c4", "d2d4")
        if _matches_start_changes(board, {"e2": None, "e4": "wP", "c7": None, "c5": "bP"}):
            return _first_legal(legal_uci, "g1f3", "d2d4", "c2c3")
        if _matches_start_changes(board, {"d2": None, "d4": "wP", "d7": None, "d5": "bP"}):
            return _first_legal(legal_uci, "c2c4", "g1f3", "c1f4")
        if _matches_start_changes(board, {"d2": None, "d4": "wP", "g8": None, "f6": "bN"}):
            return _first_legal(legal_uci, "c2c4", "g1f3", "c1g5")
    return None


def _get_provided_legal_moves():
    for name in ("legal_moves", "LEGAL_MOVES"):
        value = globals().get(name)
        if isinstance(value, (list, tuple, set)):
            out = []
            for x in value:
                out.append(x if isinstance(x, str) else str(x))
            if out:
                return out
    return None


def policy(pieces: dict[str, str], to_play: str) -> str:
    color = "w" if str(to_play).lower().startswith("w") else "b"
    board = _board_from_pieces(pieces)

    provided = _get_provided_legal_moves()
    provided_set = set(provided) if provided else set()
    root_moves = []
    uci_for_move = {}
    using_provided = False

    if provided:
        for s in provided:
            m = parse_uci_move(s, board)
            if m is None:
                continue
            piece = board[m[0]]
            if piece is None or piece[0] != color:
                continue
            if m not in uci_for_move:
                root_moves.append(m)
                uci_for_move[m] = s
        using_provided = len(root_moves) > 0

    if not root_moves:
        root_moves = generate_legal(board, color, tactical=False, include_castles=False)
        using_provided = False

    if not root_moves:
        if provided:
            return provided[0]
        pseudo = generate_pseudo_moves(board, color, tactical=False, include_castles=False)
        if pseudo:
            return move_to_uci(pseudo[0])
        return "a1a1"

    if len(root_moves) == 1:
        return uci_for_move.get(root_moves[0], move_to_uci(root_moves[0]))

    legal_uci = set(uci_for_move.values()) if using_provided else {move_to_uci(m) for m in root_moves}
    book = _choose_book_move(board, color, legal_uci)
    if book is not None:
        return book

    start_time = time.perf_counter()
    deadline = start_time + 0.88

    root_hash = compute_hash(board)
    tt = {}
    killers = [[None, None] for _ in range(128)]
    history = {}
    nodes = 0

    def check_time():
        nonlocal nodes
        nodes += 1
        if (nodes & 1023) == 0 and time.perf_counter() > deadline:
            raise SearchTimeout()

    def ordered_moves(moves, side, tt_move, ply):
        return sorted(
            moves,
            key=lambda mv: move_order_score(board, mv, side, tt_move, ply, killers, history),
            reverse=True,
        )

    def quiescence(alpha, beta, side, ply, qdepth):
        check_time()

        if in_check(board, side):
            if qdepth <= 0:
                return evaluate(board, side) - 75
            moves = generate_legal(board, side, tactical=False, include_castles=False)
            if not moves:
                return -MATE_SCORE + ply
            moves = ordered_moves(moves, side, None, ply)
            for m in moves:
                undo = make_move_simple(board, m)
                if undo is None:
                    continue
                try:
                    score = -quiescence(-beta, -alpha, OPP[side], ply + 1, qdepth - 1)
                finally:
                    undo_move_simple(board, m, undo)

                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
            return alpha

        stand = evaluate(board, side)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand

        if qdepth <= 0:
            return alpha

        moves = generate_legal(board, side, tactical=True, include_castles=False)
        if not moves:
            return alpha

        moves = ordered_moves(moves, side, None, ply)
        for m in moves:
            undo = make_move_simple(board, m)
            if undo is None:
                continue
            try:
                score = -quiescence(-beta, -alpha, OPP[side], ply + 1, qdepth - 1)
            finally:
                undo_move_simple(board, m, undo)

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def negamax(depth, alpha, beta, side, ply, h):
        check_time()

        if depth <= 0:
            return quiescence(alpha, beta, side, ply, 6)

        alpha_orig = alpha
        beta_orig = beta
        tt_key = (h, side)
        entry = tt.get(tt_key)
        tt_move = None

        if entry is not None:
            edepth, flag, val, emove = entry
            tt_move = emove
            if edepth >= depth:
                if flag == 0:
                    return val
                if flag == 1 and val > alpha:
                    alpha = val
                elif flag == 2 and val < beta:
                    beta = val
                if alpha >= beta:
                    return val

        checked = in_check(board, side)
        moves = generate_legal(board, side, tactical=False, include_castles=False)
        if not moves:
            return -MATE_SCORE + ply if checked else 0

        moves = ordered_moves(moves, side, tt_move, ply)
        best_score = -INF
        best_move = None

        for idx, m in enumerate(moves):
            cap = captured_piece_for_move(board, m)
            quiet = cap is None and not m[2] and m[3] != "c"

            undo, nh = make_move_hash(board, m, h)
            if undo is None:
                continue

            try:
                if idx == 0 or alpha + 1 >= beta:
                    score = -negamax(depth - 1, -beta, -alpha, OPP[side], ply + 1, nh)
                else:
                    score = -negamax(depth - 1, -alpha - 1, -alpha, OPP[side], ply + 1, nh)
                    if alpha < score < beta:
                        score = -negamax(depth - 1, -beta, -alpha, OPP[side], ply + 1, nh)
            finally:
                undo_move_simple(board, m, undo)

            if score > best_score:
                best_score = score
                best_move = m

            if score > alpha:
                alpha = score
                if alpha >= beta:
                    if quiet and ply < len(killers):
                        if killers[ply][0] != m:
                            killers[ply][1] = killers[ply][0]
                            killers[ply][0] = m
                        hk = (side, m[0], m[1], m[2])
                        history[hk] = min(history.get(hk, 0) + depth * depth, 1000000)
                    break

        if best_move is None:
            return evaluate(board, side)

        flag = 0
        if best_score <= alpha_orig:
            flag = 2
        elif best_score >= beta_orig:
            flag = 1

        if len(tt) < 250000:
            tt[tt_key] = (depth, flag, best_score, best_move)

        return best_score

    def search_root(depth, pv_move):
        alpha = -INF
        beta = INF
        moves = ordered_moves(root_moves, color, pv_move, 0)
        best_score = -INF
        best_move = None

        for idx, m in enumerate(moves):
            if time.perf_counter() > deadline:
                raise SearchTimeout()

            undo, nh = make_move_hash(board, m, root_hash)
            if undo is None:
                continue

            try:
                if idx == 0:
                    score = -negamax(depth - 1, -beta, -alpha, OPP[color], 1, nh)
                else:
                    score = -negamax(depth - 1, -alpha - 1, -alpha, OPP[color], 1, nh)
                    if alpha < score < beta:
                        score = -negamax(depth - 1, -beta, -alpha, OPP[color], 1, nh)
            finally:
                undo_move_simple(board, m, undo)

            if score > best_score:
                best_score = score
                best_move = m
            if score > alpha:
                alpha = score

        if best_move is None:
            return evaluate(board, color), root_moves[0]
        return best_score, best_move

    ordered_root = ordered_moves(root_moves, color, None, 0)
    best_move = ordered_root[0]
    previous_best = best_move

    piece_count = sum(1 for p in board if p is not None)
    if piece_count <= 6:
        max_depth = 7
    elif piece_count <= 10:
        max_depth = 6
    elif piece_count <= 18:
        max_depth = 5
    else:
        max_depth = 4

    if len(root_moves) > 45:
        max_depth = min(max_depth, 3)
    elif len(root_moves) <= 8:
        max_depth = min(max_depth + 1, 7)

    try:
        for depth in range(1, max_depth + 1):
            score, mv = search_root(depth, previous_best)
            if mv is not None:
                best_move = mv
                previous_best = mv
            if abs(score) > MATE_SCORE - 1000:
                break
            if time.perf_counter() > deadline - 0.03:
                break
    except SearchTimeout:
        pass

    result = uci_for_move.get(best_move, move_to_uci(best_move)) if using_provided else move_to_uci(best_move)

    if using_provided:
        if result in provided_set:
            return result
        normalized = move_to_uci(best_move)
        if normalized in provided_set:
            return normalized
        return next(iter(provided_set)) if provided_set else result

    return result
