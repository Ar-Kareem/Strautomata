
import time
from typing import Dict, List, Tuple, Optional

# =========================
# Lightweight Chess Engine
# =========================

# Board indexing: a1 = 0 ... h1 = 7, a8 = 56 ... h8 = 63
FILES = "abcdefgh"
RANKS = "12345678"

# Piece encoding
#  0 empty
#  1 wP, 2 wN, 3 wB, 4 wR, 5 wQ, 6 wK
# -1 bP, -2 bN, -3 bB, -4 bR, -5 bQ, -6 bK
PIECE_TO_INT = {
    "wP": 1, "wN": 2, "wB": 3, "wR": 4, "wQ": 5, "wK": 6,
    "bP": -1, "bN": -2, "bB": -3, "bR": -4, "bQ": -5, "bK": -6,
}
INT_TO_PIECE = {v: k for k, v in PIECE_TO_INT.items()}

# Material values
VAL = {1: 100, 2: 320, 3: 330, 4: 500, 5: 900, 6: 0}

# Piece-square tables (middlegame-ish), indexed by square a1..h8 for White.
# Black uses mirrored vertically.
PST_WP = [
      0,  0,  0,  0,  0,  0,  0,  0,
     10, 10, 10, 10, 10, 10, 10, 10,
      6,  6,  8, 12, 12,  8,  6,  6,
      4,  4,  6, 10, 10,  6,  4,  4,
      2,  2,  4,  8,  8,  4,  2,  2,
      1,  1,  2,  0,  0,  2,  1,  1,
      0,  0,  0, -8, -8,  0,  0,  0,
      0,  0,  0,  0,  0,  0,  0,  0,
]
PST_WN = [
    -30,-20,-10,-10,-10,-10,-20,-30,
    -20, -5,  0,  0,  0,  0, -5,-20,
    -10,  0, 10, 12, 12, 10,  0,-10,
    -10,  2, 12, 15, 15, 12,  2,-10,
    -10,  0, 12, 15, 15, 12,  0,-10,
    -10,  2, 10, 12, 12, 10,  2,-10,
    -20, -5,  0,  2,  2,  0, -5,-20,
    -30,-20,-10,-10,-10,-10,-20,-30,
]
PST_WB = [
    -10, -5, -5, -5, -5, -5, -5,-10,
     -5,  5,  0,  0,  0,  0,  5, -5,
     -5, 10, 10, 10, 10, 10, 10, -5,
     -5,  0, 10, 10, 10, 10,  0, -5,
     -5,  5,  8, 10, 10,  8,  5, -5,
     -5,  5,  5,  8,  8,  5,  5, -5,
     -5,  5,  0,  0,  0,  0,  5, -5,
    -10, -5, -5, -5, -5, -5, -5,-10,
]
PST_WR = [
      0,  0,  2,  5,  5,  2,  0,  0,
     -2,  0,  0,  0,  0,  0,  0, -2,
     -2,  0,  0,  0,  0,  0,  0, -2,
     -2,  0,  0,  0,  0,  0,  0, -2,
     -2,  0,  0,  0,  0,  0,  0, -2,
     -2,  0,  0,  0,  0,  0,  0, -2,
      5, 10, 10, 10, 10, 10, 10,  5,
      0,  0,  2,  6,  6,  2,  0,  0,
]
PST_WQ = [
    -10, -5, -5, -2, -2, -5, -5,-10,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
     -2,  0,  5,  6,  6,  5,  0, -2,
      0,  0,  5,  6,  6,  5,  0,  0,
     -5,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
    -10, -5, -5, -2, -2, -5, -5,-10,
]
PST_WK = [
    -30,-30,-30,-30,-30,-30,-30,-30,
    -30,-30,-30,-30,-30,-30,-30,-30,
    -30,-30,-30,-30,-30,-30,-30,-30,
    -30,-30,-30,-30,-30,-30,-30,-30,
    -20,-20,-20,-20,-20,-20,-20,-20,
    -10,-10,-10,-10,-10,-10,-10,-10,
     10, 10,  0,  0,  0,  0, 10, 10,
     15, 20, 10,  0,  0, 10, 20, 15,
]
PST = {
    1: PST_WP, 2: PST_WN, 3: PST_WB, 4: PST_WR, 5: PST_WQ, 6: PST_WK
}

KNIGHT_OFFS = (-17, -15, -10, -6, 6, 10, 15, 17)
KING_OFFS = (-9, -8, -7, -1, 1, 7, 8, 9)
BISHOP_DIRS = (-9, -7, 7, 9)
ROOK_DIRS = (-8, -1, 1, 8)
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

MATE_SCORE = 10**9
INF = 10**15

# Zobrist hashing (fixed seed for determinism)
def _zobrist_init() -> Tuple[List[List[int]], int]:
    x = 0x9E3779B97F4A7C15
    def rng64():
        nonlocal x
        x ^= (x >> 12) & ((1 << 64) - 1)
        x ^= (x << 25) & ((1 << 64) - 1)
        x ^= (x >> 27) & ((1 << 64) - 1)
        return (x * 0x2545F4914F6CDD1D) & ((1 << 64) - 1)
    table = [[0]*12 for _ in range(64)]
    for sq in range(64):
        for p in range(12):
            table[sq][p] = rng64()
    side_key = rng64()
    return table, side_key

ZOBRIST, Z_SIDE = _zobrist_init()

def sq_to_i(sq: str) -> int:
    return (ord(sq[0]) - 97) + 8 * (ord(sq[1]) - 49)

def i_to_sq(i: int) -> str:
    return FILES[i & 7] + RANKS[i >> 3]

def mirror_sq(i: int) -> int:
    # flip vertically: rank r -> 7-r
    return (7 - (i >> 3)) * 8 + (i & 7)

def on_board(i: int) -> bool:
    return 0 <= i < 64

def same_file(a: int, b: int) -> bool:
    return (a & 7) == (b & 7)

def file_of(i: int) -> int:
    return i & 7

def rank_of(i: int) -> int:
    return i >> 3

def uci_move(frm: int, to: int, promo: int = 0) -> str:
    s = i_to_sq(frm) + i_to_sq(to)
    if promo:
        # promo is piece type int: 2=N 3=B 4=R 5=Q
        s += {2: "n", 3: "b", 4: "r", 5: "q"}[promo]
    return s

class Board:
    __slots__ = ("b", "side", "wk", "bk", "hash")

    def __init__(self, arr: List[int], side: int):
        self.b = arr
        self.side = side  # 1 white to move, -1 black to move
        self.wk = -1
        self.bk = -1
        for i, p in enumerate(arr):
            if p == 6:
                self.wk = i
            elif p == -6:
                self.bk = i
        self.hash = self._compute_hash()

    def _compute_hash(self) -> int:
        h = 0
        for i, p in enumerate(self.b):
            if p:
                # map piece int to 0..11
                # white: 1..6 -> 0..5, black: -1..-6 -> 6..11
                if p > 0:
                    idx = p - 1
                else:
                    idx = (-p - 1) + 6
                h ^= ZOBRIST[i][idx]
        if self.side == -1:
            h ^= Z_SIDE
        return h

    def copy(self) -> "Board":
        nb = Board(self.b[:], self.side)
        nb.wk = self.wk
        nb.bk = self.bk
        nb.hash = self.hash
        return nb

def is_attacked(board: Board, sq: int, by_side: int) -> bool:
    b = board.b

    # pawns
    if by_side == 1:
        # white pawns attack up (towards higher ranks): from sq-7, sq-9
        r = rank_of(sq)
        if r > 0:
            if file_of(sq) != 0 and b[sq - 9] == 1:
                return True
            if file_of(sq) != 7 and b[sq - 7] == 1:
                return True
    else:
        # black pawns attack down: from sq+7, sq+9
        r = rank_of(sq)
        if r < 7:
            if file_of(sq) != 0 and b[sq + 7] == -1:
                return True
            if file_of(sq) != 7 and b[sq + 9] == -1:
                return True

    # knights
    for d in KNIGHT_OFFS:
        s2 = sq + d
        if not on_board(s2):
            continue
        # prevent wrap across files for knight moves:
        f1 = file_of(sq)
        f2 = file_of(s2)
        if abs(f1 - f2) not in (1, 2):
            continue
        if b[s2] == (2 * by_side):
            return True

    # bishops / queens (diagonals)
    for d in BISHOP_DIRS:
        s2 = sq + d
        while on_board(s2):
            # diagonal wrap check: file diff must change by 1 each step
            if abs(file_of(s2) - file_of(s2 - d)) != 1:
                break
            p = b[s2]
            if p:
                if p == (3 * by_side) or p == (5 * by_side):
                    return True
                break
            s2 += d

    # rooks / queens (orthogonals)
    for d in ROOK_DIRS:
        s2 = sq + d
        while on_board(s2):
            # horizontal wrap check
            if d in (-1, 1) and rank_of(s2) != rank_of(s2 - d):
                break
            p = b[s2]
            if p:
                if p == (4 * by_side) or p == (5 * by_side):
                    return True
                break
            s2 += d

    # king
    for d in KING_OFFS:
        s2 = sq + d
        if not on_board(s2):
            continue
        if abs(file_of(s2) - file_of(sq)) > 1:
            continue
        if b[s2] == (6 * by_side):
            return True

    return False

def in_check(board: Board, side: int) -> bool:
    ksq = board.wk if side == 1 else board.bk
    if ksq < 0:
        # Shouldn't happen in valid chess, but avoid crash.
        return False
    return is_attacked(board, ksq, -side)

def make_move(board: Board, frm: int, to: int, promo: int = 0) -> Board:
    nb = board.copy()
    b = nb.b
    p = b[frm]
    captured = b[to]

    # Update hash (incremental)
    # Remove moving piece from frm
    if p:
        if p > 0:
            idx = p - 1
        else:
            idx = (-p - 1) + 6
        nb.hash ^= ZOBRIST[frm][idx]
    # Remove captured piece from to
    if captured:
        if captured > 0:
            cidx = captured - 1
        else:
            cidx = (-captured - 1) + 6
        nb.hash ^= ZOBRIST[to][cidx]

    # Move piece
    b[frm] = 0

    # Handle castling rook move (detect king move two squares)
    if abs(p) == 6 and abs(to - frm) == 2:
        # King side or queen side
        if to > frm:
            # king side rook: h-file to f-file
            rook_from = frm + 3
            rook_to = frm + 1
        else:
            rook_from = frm - 4
            rook_to = frm - 1
        rook = b[rook_from]
        # remove rook from rook_from hash
        if rook:
            if rook > 0:
                ridx = rook - 1
            else:
                ridx = (-rook - 1) + 6
            nb.hash ^= ZOBRIST[rook_from][ridx]
            nb.hash ^= ZOBRIST[rook_to][ridx]
        b[rook_from] = 0
        b[rook_to] = rook

    # Promotion
    if promo and abs(p) == 1:
        p = promo * (1 if p > 0 else -1)

    b[to] = p

    # Add moving piece at to hash
    if p:
        if p > 0:
            idx2 = p - 1
        else:
            idx2 = (-p - 1) + 6
        nb.hash ^= ZOBRIST[to][idx2]

    # Update king squares
    if p == 6:
        nb.wk = to
    elif p == -6:
        nb.bk = to

    # Side to move toggle
    nb.side = -board.side
    nb.hash ^= Z_SIDE
    return nb

def gen_pseudo_moves(board: Board) -> List[Tuple[int, int, int]]:
    b = board.b
    side = board.side
    moves: List[Tuple[int, int, int]] = []

    for frm, p in enumerate(b):
        if not p or (p > 0) != (side > 0):
            continue
        pt = abs(p)

        if pt == 1:
            # Pawn
            r = rank_of(frm)
            f = file_of(frm)
            if side == 1:
                # forward one
                to = frm + 8
                if to < 64 and b[to] == 0:
                    if r == 6:
                        for pr in (5, 4, 3, 2):
                            moves.append((frm, to, pr))
                    else:
                        moves.append((frm, to, 0))
                        # forward two from rank 2 (r==1)
                        if r == 1 and b[frm + 16] == 0:
                            moves.append((frm, frm + 16, 0))
                # captures
                if f != 0:
                    to = frm + 7
                    if to < 64 and b[to] < 0:
                        if r == 6:
                            for pr in (5, 4, 3, 2):
                                moves.append((frm, to, pr))
                        else:
                            moves.append((frm, to, 0))
                if f != 7:
                    to = frm + 9
                    if to < 64 and b[to] < 0:
                        if r == 6:
                            for pr in (5, 4, 3, 2):
                                moves.append((frm, to, pr))
                        else:
                            moves.append((frm, to, 0))
            else:
                # black
                to = frm - 8
                if to >= 0 and b[to] == 0:
                    if r == 1:
                        for pr in (5, 4, 3, 2):
                            moves.append((frm, to, pr))
                    else:
                        moves.append((frm, to, 0))
                        if r == 6 and b[frm - 16] == 0:
                            moves.append((frm, frm - 16, 0))
                if f != 0:
                    to = frm - 9
                    if to >= 0 and b[to] > 0:
                        if r == 1:
                            for pr in (5, 4, 3, 2):
                                moves.append((frm, to, pr))
                        else:
                            moves.append((frm, to, 0))
                if f != 7:
                    to = frm - 7
                    if to >= 0 and b[to] > 0:
                        if r == 1:
                            for pr in (5, 4, 3, 2):
                                moves.append((frm, to, pr))
                        else:
                            moves.append((frm, to, 0))

        elif pt == 2:
            # Knight
            for d in KNIGHT_OFFS:
                to = frm + d
                if not on_board(to):
                    continue
                if abs(file_of(to) - file_of(frm)) not in (1, 2):
                    continue
                tp = b[to]
                if tp == 0 or (tp > 0) != (side > 0):
                    moves.append((frm, to, 0))

        elif pt == 3:
            # Bishop
            for d in BISHOP_DIRS:
                to = frm + d
                while on_board(to):
                    if abs(file_of(to) - file_of(to - d)) != 1:
                        break
                    tp = b[to]
                    if tp == 0:
                        moves.append((frm, to, 0))
                    else:
                        if (tp > 0) != (side > 0):
                            moves.append((frm, to, 0))
                        break
                    to += d

        elif pt == 4:
            # Rook
            for d in ROOK_DIRS:
                to = frm + d
                while on_board(to):
                    if d in (-1, 1) and rank_of(to) != rank_of(to - d):
                        break
                    tp = b[to]
                    if tp == 0:
                        moves.append((frm, to, 0))
                    else:
                        if (tp > 0) != (side > 0):
                            moves.append((frm, to, 0))
                        break
                    to += d

        elif pt == 5:
            # Queen
            for d in QUEEN_DIRS:
                to = frm + d
                while on_board(to):
                    if d in (-9, -7, 7, 9) and abs(file_of(to) - file_of(to - d)) != 1:
                        break
                    if d in (-1, 1) and rank_of(to) != rank_of(to - d):
                        break
                    tp = b[to]
                    if tp == 0:
                        moves.append((frm, to, 0))
                    else:
                        if (tp > 0) != (side > 0):
                            moves.append((frm, to, 0))
                        break
                    to += d

        elif pt == 6:
            # King
            for d in KING_OFFS:
                to = frm + d
                if not on_board(to):
                    continue
                if abs(file_of(to) - file_of(frm)) > 1:
                    continue
                tp = b[to]
                if tp == 0 or (tp > 0) != (side > 0):
                    moves.append((frm, to, 0))

            # Castling (heuristic rights: if pieces on initial squares)
            # Only attempt if king is on initial square and not currently in check.
            if side == 1 and frm == sq_to_i("e1") and b[frm] == 6:
                if not in_check(board, 1):
                    # King side: e1g1 with rook h1
                    if b[sq_to_i("h1")] == 4 and b[sq_to_i("f1")] == 0 and b[sq_to_i("g1")] == 0:
                        if (not is_attacked(board, sq_to_i("f1"), -1)) and (not is_attacked(board, sq_to_i("g1"), -1)):
                            moves.append((frm, sq_to_i("g1"), 0))
                    # Queen side: e1c1 with rook a1
                    if b[sq_to_i("a1")] == 4 and b[sq_to_i("b1")] == 0 and b[sq_to_i("c1")] == 0 and b[sq_to_i("d1")] == 0:
                        if (not is_attacked(board, sq_to_i("d1"), -1)) and (not is_attacked(board, sq_to_i("c1"), -1)):
                            moves.append((frm, sq_to_i("c1"), 0))
            elif side == -1 and frm == sq_to_i("e8") and b[frm] == -6:
                if not in_check(board, -1):
                    if b[sq_to_i("h8")] == -4 and b[sq_to_i("f8")] == 0 and b[sq_to_i("g8")] == 0:
                        if (not is_attacked(board, sq_to_i("f8"), 1)) and (not is_attacked(board, sq_to_i("g8"), 1)):
                            moves.append((frm, sq_to_i("g8"), 0))
                    if b[sq_to_i("a8")] == -4 and b[sq_to_i("b8")] == 0 and b[sq_to_i("c8")] == 0 and b[sq_to_i("d8")] == 0:
                        if (not is_attacked(board, sq_to_i("d8"), 1)) and (not is_attacked(board, sq_to_i("c8"), 1)):
                            moves.append((frm, sq_to_i("c8"), 0))

    return moves

def gen_legal_moves(board: Board) -> List[Tuple[int, int, int]]:
    moves = gen_pseudo_moves(board)
    legal: List[Tuple[int, int, int]] = []
    side = board.side
    for frm, to, promo in moves:
        nb = make_move(board, frm, to, promo)
        if not in_check(nb, side):
            legal.append((frm, to, promo))
    return legal

def move_is_capture(board: Board, mv: Tuple[int, int, int]) -> bool:
    frm, to, promo = mv
    # Castling isn't capture; promotion capture is still capture by target occupancy
    return board.b[to] != 0

def gives_check(board: Board, mv: Tuple[int, int, int]) -> bool:
    frm, to, promo = mv
    nb = make_move(board, frm, to, promo)
    return in_check(nb, nb.side)

def eval_board(board: Board) -> int:
    b = board.b
    score = 0
    # material + pst
    for sq, p in enumerate(b):
        if p == 0:
            continue
        pt = abs(p)
        v = VAL[pt]
        if p > 0:
            score += v + PST[pt][sq]
        else:
            score -= v + PST[pt][mirror_sq(sq)]

    # light mobility bonus (encourage activity)
    # compute pseudo mobility to keep it cheap
    saved_side = board.side
    board.side = 1
    wm = len(gen_pseudo_moves(board))
    board.side = -1
    bm = len(gen_pseudo_moves(board))
    board.side = saved_side
    score += 2 * (wm - bm)

    # king safety: penalize kings in center a bit (middlegame bias)
    if board.wk != -1:
        wkf, wkr = file_of(board.wk), rank_of(board.wk)
        score -= 3 * (abs(wkf - 3.5) + abs(wkr - 0.5))
    if board.bk != -1:
        bkf, bkr = file_of(board.bk), rank_of(board.bk)
        score += 3 * (abs(bkf - 3.5) + abs(bkr - 7.5))

    return int(score)

def order_moves(board: Board, moves: List[Tuple[int, int, int]]) -> List[Tuple[int, int, int]]:
    b = board.b
    side = board.side

    def mvv_lva(mv):
        frm, to, promo = mv
        cap = b[to]
        if cap == 0:
            return 0
        victim = VAL[abs(cap)]
        attacker = VAL[abs(b[frm])]
        return victim * 10 - attacker

    def score(mv):
        frm, to, promo = mv
        sc = 0
        # promotions
        if promo:
            sc += 800 + (promo * 10)
        # captures
        if b[to] != 0:
            sc += 500 + mvv_lva(mv)
        # checks
        if gives_check(board, mv):
            sc += 200
        # center preference
        cf = abs(file_of(to) - 3.5)
        cr = abs(rank_of(to) - 3.5)
        sc += int(10 - (cf + cr))
        # discourage moving into attacked square for king lightly (handled by legality but still)
        if abs(b[frm]) == 6 and is_attacked(board, to, -side):
            sc -= 50
        return sc

    return sorted(moves, key=score, reverse=True)

class Search:
    __slots__ = ("tt", "t_end", "nodes")

    def __init__(self, t_end: float):
        self.tt: Dict[Tuple[int, int], Tuple[int, int]] = {}  # (hash, depth)->(score, flag) not used much
        self.t_end = t_end
        self.nodes = 0

    def time_up(self) -> bool:
        return time.perf_counter() >= self.t_end

    def qsearch(self, board: Board, alpha: int, beta: int) -> int:
        if self.time_up():
            return 0
        self.nodes += 1
        stand = eval_board(board)
        # negamax; caller ensures proper sign
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand

        moves = gen_pseudo_moves(board)
        # only consider captures & promotions in quiescence
        caps = []
        for mv in moves:
            frm, to, promo = mv
            if promo or board.b[to] != 0:
                nb = make_move(board, frm, to, promo)
                if not in_check(nb, -nb.side):
                    caps.append(mv)
        caps = order_moves(board, caps)

        for mv in caps:
            if self.time_up():
                break
            frm, to, promo = mv
            nb = make_move(board, frm, to, promo)
            score = -self.qsearch(nb, -beta, -alpha)
            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def negamax(self, board: Board, depth: int, alpha: int, beta: int) -> int:
        if self.time_up():
            return 0
        self.nodes += 1

        side = board.side
        legal = None

        if depth <= 0:
            return self.qsearch(board, alpha, beta)

        # Terminal
        legal = gen_legal_moves(board)
        if not legal:
            if in_check(board, side):
                return -MATE_SCORE + (10 - depth)
            return 0

        legal = order_moves(board, legal)

        best = -INF
        for mv in legal:
            if self.time_up():
                break
            frm, to, promo = mv
            nb = make_move(board, frm, to, promo)
            score = -self.negamax(nb, depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

def _build_board(pieces: Dict[str, str], to_play: str) -> Board:
    arr = [0] * 64
    for sq, pc in pieces.items():
        if sq and len(sq) == 2 and pc in PIECE_TO_INT:
            arr[sq_to_i(sq)] = PIECE_TO_INT[pc]
    side = 1 if to_play == "white" else -1
    return Board(arr, side)

def policy(pieces: Dict[str, str], to_play: str) -> str:
    board = _build_board(pieces, to_play)
    legal = gen_legal_moves(board)
    if not legal:
        # In terminal/invalid states, fall back to any pseudo move (still may be illegal),
        # but arena should not query terminal positions.
        pseudo = gen_pseudo_moves(board)
        if pseudo:
            frm, to, promo = pseudo[0]
            return uci_move(frm, to, promo)
        return "a1a1"

    # Immediate tactical: if any move checkmates, play it.
    for mv in order_moves(board, legal):
        frm, to, promo = mv
        nb = make_move(board, frm, to, promo)
        reply = gen_legal_moves(nb)
        if not reply and in_check(nb, nb.side):
            return uci_move(frm, to, promo)

    # Iterative deepening within time budget
    t0 = time.perf_counter()
    t_end = t0 + 0.92  # keep margin for Python overhead
    search = Search(t_end)

    best_move = order_moves(board, legal)[0]
    best_score = -INF

    # Root move ordering once
    root_moves = order_moves(board, legal)

    for depth in range(1, 6):
        if time.perf_counter() >= t_end:
            break
        alpha, beta = -INF, INF
        cur_best = None
        cur_best_score = -INF

        for mv in root_moves:
            if time.perf_counter() >= t_end:
                break
            frm, to, promo = mv
            nb = make_move(board, frm, to, promo)
            sc = -search.negamax(nb, depth - 1, -beta, -alpha)

            if sc > cur_best_score:
                cur_best_score = sc
                cur_best = mv
            if sc > alpha:
                alpha = sc

        if cur_best is not None:
            best_move = cur_best
            best_score = cur_best_score

        # If we've essentially found a forced mate, stop early
        if best_score > MATE_SCORE // 2:
            break

    frm, to, promo = best_move
    return uci_move(frm, to, promo)
