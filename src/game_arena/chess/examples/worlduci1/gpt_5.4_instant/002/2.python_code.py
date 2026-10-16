
from __future__ import annotations

from dataclasses import dataclass
import math
import time
from typing import List, Dict, Optional, Tuple

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

MATE_SCORE = 1000000
INF = 10**18

# Piece-square tables from White perspective; Black mirrored.
PST = {
    "P": [
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10,-20,-20, 10, 10,  5,
         5, -5,-10,  0,  0,-10, -5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5,  5, 10, 25, 25, 10,  5,  5,
        10, 10, 20, 30, 30, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    "N": [
       -50,-40,-30,-30,-30,-30,-40,-50,
       -40,-20,  0,  0,  0,  0,-20,-40,
       -30,  0, 10, 15, 15, 10,  0,-30,
       -30,  5, 15, 20, 20, 15,  5,-30,
       -30,  0, 15, 20, 20, 15,  0,-30,
       -30,  5, 10, 15, 15, 10,  5,-30,
       -40,-20,  0,  5,  5,  0,-20,-40,
       -50,-40,-30,-30,-30,-30,-40,-50,
    ],
    "B": [
       -20,-10,-10,-10,-10,-10,-10,-20,
       -10,  5,  0,  0,  0,  0,  5,-10,
       -10, 10, 10, 10, 10, 10, 10,-10,
       -10,  0, 10, 10, 10, 10,  0,-10,
       -10,  5,  5, 10, 10,  5,  5,-10,
       -10,  0,  5, 10, 10,  5,  0,-10,
       -10,  0,  0,  0,  0,  0,  0,-10,
       -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    "R": [
         0,  0,  0,  5,  5,  0,  0,  0,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         5, 10, 10, 10, 10, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    "Q": [
       -20,-10,-10, -5, -5,-10,-10,-20,
       -10,  0,  0,  0,  0,  0,  0,-10,
       -10,  0,  5,  5,  5,  5,  0,-10,
        -5,  0,  5,  5,  5,  5,  0, -5,
         0,  0,  5,  5,  5,  5,  0, -5,
       -10,  5,  5,  5,  5,  5,  0,-10,
       -10,  0,  5,  0,  0,  0,  0,-10,
       -20,-10,-10, -5, -5,-10,-10,-20,
    ],
    "K_MID": [
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -30,-40,-40,-50,-50,-40,-40,-30,
       -20,-30,-30,-40,-40,-30,-30,-20,
       -10,-20,-20,-20,-20,-20,-20,-10,
        20, 20,  0,  0,  0,  0, 20, 20,
        20, 30, 10,  0,  0, 10, 30, 20,
    ],
    "K_END": [
       -50,-40,-30,-20,-20,-30,-40,-50,
       -30,-20,-10,  0,  0,-10,-20,-30,
       -30,-10, 20, 30, 30, 20,-10,-30,
       -30,-10, 30, 40, 40, 30,-10,-30,
       -30,-10, 30, 40, 40, 30,-10,-30,
       -30,-10, 20, 30, 30, 20,-10,-30,
       -30,-30,  0,  0,  0,  0,-30,-30,
       -50,-30,-30,-30,-30,-30,-30,-50,
    ],
}

KNIGHT_DELTAS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DELTAS = [(1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

def sq_to_idx(s: str) -> int:
    return (ord(s[1]) - 49) * 8 + (ord(s[0]) - 97)

def idx_to_sq(i: int) -> str:
    return chr(97 + (i % 8)) + chr(49 + (i // 8))

def on_board(f: int, r: int) -> bool:
    return 0 <= f < 8 and 0 <= r < 8

def idx_file(i: int) -> int:
    return i % 8

def idx_rank(i: int) -> int:
    return i // 8

def color_char(to_play: str) -> str:
    return "w" if to_play == "white" else "b"

def opp(c: str) -> str:
    return "b" if c == "w" else "w"

@dataclass
class Move:
    from_sq: int
    to_sq: int
    promotion: Optional[str] = None
    is_castle: bool = False
    is_en_passant: bool = False

    def uci(self) -> str:
        s = idx_to_sq(self.from_sq) + idx_to_sq(self.to_sq)
        if self.promotion:
            s += self.promotion.lower()
        return s

class Position:
    def __init__(self, board: List[Optional[str]], side: str,
                 castling: Optional[Dict[str, bool]] = None,
                 ep_square: Optional[int] = None):
        self.board = board
        self.side = side
        self.castling = castling if castling is not None else {"K": False, "Q": False, "k": False, "q": False}
        self.ep_square = ep_square

    @staticmethod
    def from_pieces(pieces: Dict[str, str], to_play: str) -> "Position":
        board = [None] * 64
        for sq, pc in pieces.items():
            board[sq_to_idx(sq)] = pc

        castling = infer_castling_rights(board)
        ep_square = infer_ep_square(board, color_char(to_play))
        return Position(board, color_char(to_play), castling, ep_square)

    def clone(self) -> "Position":
        return Position(self.board[:], self.side, dict(self.castling), self.ep_square)

    def king_square(self, side: str) -> Optional[int]:
        target = side + "K"
        for i, p in enumerate(self.board):
            if p == target:
                return i
        return None

def infer_castling_rights(board: List[Optional[str]]) -> Dict[str, bool]:
    rights = {"K": False, "Q": False, "k": False, "q": False}
    if board[sq_to_idx("e1")] == "wK":
        if board[sq_to_idx("h1")] == "wR":
            rights["K"] = True
        if board[sq_to_idx("a1")] == "wR":
            rights["Q"] = True
    if board[sq_to_idx("e8")] == "bK":
        if board[sq_to_idx("h8")] == "bR":
            rights["k"] = True
        if board[sq_to_idx("a8")] == "bR":
            rights["q"] = True
    return rights

def infer_ep_square(board: List[Optional[str]], side_to_move: str) -> Optional[int]:
    # Limited inference from static position:
    # if side to move can potentially capture en passant and a just-moved pawn layout exists.
    if side_to_move == "w":
        # black just moved two squares to rank 5, ep target on rank 6
        for file in range(8):
            sq5 = 4 * 8 + file
            if board[sq5] == "bP":
                if file > 0 and board[sq5 - 1] == "wP":
                    return 5 * 8 + file
                if file < 7 and board[sq5 + 1] == "wP":
                    return 5 * 8 + file
    else:
        # white just moved two squares to rank 4, ep target on rank 3
        for file in range(8):
            sq4 = 3 * 8 + file
            if board[sq4] == "wP":
                if file > 0 and board[sq4 - 1] == "bP":
                    return 2 * 8 + file
                if file < 7 and board[sq4 + 1] == "bP":
                    return 2 * 8 + file
    return None

def is_attacked(pos: Position, sq: int, by_side: str) -> bool:
    b = pos.board
    f, r = idx_file(sq), idx_rank(sq)

    # Pawn attacks
    if by_side == "w":
        for df in (-1, 1):
            nf, nr = f + df, r - 1
            if on_board(nf, nr):
                p = b[nr * 8 + nf]
                if p == "wP":
                    return True
    else:
        for df in (-1, 1):
            nf, nr = f + df, r + 1
            if on_board(nf, nr):
                p = b[nr * 8 + nf]
                if p == "bP":
                    return True

    # Knights
    for df, dr in KNIGHT_DELTAS:
        nf, nr = f + df, r + dr
        if on_board(nf, nr):
            p = b[nr * 8 + nf]
            if p == by_side + "N":
                return True

    # Bishops / Queens
    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while on_board(nf, nr):
            p = b[nr * 8 + nf]
            if p is not None:
                if p[0] == by_side and p[1] in ("B", "Q"):
                    return True
                break
            nf += df
            nr += dr

    # Rooks / Queens
    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while on_board(nf, nr):
            p = b[nr * 8 + nf]
            if p is not None:
                if p[0] == by_side and p[1] in ("R", "Q"):
                    return True
                break
            nf += df
            nr += dr

    # King
    for df, dr in KING_DELTAS:
        nf, nr = f + df, r + dr
        if on_board(nf, nr):
            p = b[nr * 8 + nf]
            if p == by_side + "K":
                return True

    return False

def in_check(pos: Position, side: str) -> bool:
    ksq = pos.king_square(side)
    if ksq is None:
        return True
    return is_attacked(pos, ksq, opp(side))

def generate_pseudo_moves(pos: Position) -> List[Move]:
    b = pos.board
    side = pos.side
    enemy = opp(side)
    moves: List[Move] = []

    for i, p in enumerate(b):
        if p is None or p[0] != side:
            continue
        pt = p[1]
        f, r = idx_file(i), idx_rank(i)

        if pt == "P":
            dirr = 1 if side == "w" else -1
            start_rank = 1 if side == "w" else 6
            promo_rank = 6 if side == "w" else 1
            one_r = r + dirr
            if on_board(f, one_r):
                to = one_r * 8 + f
                if b[to] is None:
                    if r == promo_rank:
                        for pr in ("q", "r", "b", "n"):
                            moves.append(Move(i, to, pr))
                    else:
                        moves.append(Move(i, to))
                    if r == start_rank:
                        two_r = r + 2 * dirr
                        to2 = two_r * 8 + f
                        if b[to2] is None:
                            moves.append(Move(i, to2))
            for df in (-1, 1):
                nf, nr = f + df, r + dirr
                if on_board(nf, nr):
                    to = nr * 8 + nf
                    tp = b[to]
                    if tp is not None and tp[0] == enemy:
                        if r == promo_rank:
                            for pr in ("q", "r", "b", "n"):
                                moves.append(Move(i, to, pr))
                        else:
                            moves.append(Move(i, to))
                    if pos.ep_square is not None and to == pos.ep_square:
                        moves.append(Move(i, to, is_en_passant=True))

        elif pt == "N":
            for df, dr in KNIGHT_DELTAS:
                nf, nr = f + df, r + dr
                if on_board(nf, nr):
                    to = nr * 8 + nf
                    tp = b[to]
                    if tp is None or tp[0] == enemy:
                        moves.append(Move(i, to))

        elif pt == "B":
            for df, dr in BISHOP_DIRS:
                nf, nr = f + df, r + dr
                while on_board(nf, nr):
                    to = nr * 8 + nf
                    tp = b[to]
                    if tp is None:
                        moves.append(Move(i, to))
                    else:
                        if tp[0] == enemy:
                            moves.append(Move(i, to))
                        break
                    nf += df
                    nr += dr

        elif pt == "R":
            for df, dr in ROOK_DIRS:
                nf, nr = f + df, r + dr
                while on_board(nf, nr):
                    to = nr * 8 + nf
                    tp = b[to]
                    if tp is None:
                        moves.append(Move(i, to))
                    else:
                        if tp[0] == enemy:
                            moves.append(Move(i, to))
                        break
                    nf += df
                    nr += dr

        elif pt == "Q":
            for df, dr in QUEEN_DIRS:
                nf, nr = f + df, r + dr
                while on_board(nf, nr):
                    to = nr * 8 + nf
                    tp = b[to]
                    if tp is None:
                        moves.append(Move(i, to))
                    else:
                        if tp[0] == enemy:
                            moves.append(Move(i, to))
                        break
                    nf += df
                    nr += dr

        elif pt == "K":
            for df, dr in KING_DELTAS:
                nf, nr = f + df, r + dr
                if on_board(nf, nr):
                    to = nr * 8 + nf
                    tp = b[to]
                    if tp is None or tp[0] == enemy:
                        moves.append(Move(i, to))

            # Castling
            if side == "w" and i == sq_to_idx("e1"):
                if pos.castling.get("K", False):
                    if b[sq_to_idx("f1")] is None and b[sq_to_idx("g1")] is None:
                        if not is_attacked(pos, sq_to_idx("e1"), enemy) and not is_attacked(pos, sq_to_idx("f1"), enemy) and not is_attacked(pos, sq_to_idx("g1"), enemy):
                            moves.append(Move(i, sq_to_idx("g1"), is_castle=True))
                if pos.castling.get("Q", False):
                    if b[sq_to_idx("d1")] is None and b[sq_to_idx("c1")] is None and b[sq_to_idx("b1")] is None:
                        if not is_attacked(pos, sq_to_idx("e1"), enemy) and not is_attacked(pos, sq_to_idx("d1"), enemy) and not is_attacked(pos, sq_to_idx("c1"), enemy):
                            moves.append(Move(i, sq_to_idx("c1"), is_castle=True))
            elif side == "b" and i == sq_to_idx("e8"):
                if pos.castling.get("k", False):
                    if b[sq_to_idx("f8")] is None and b[sq_to_idx("g8")] is None:
                        if not is_attacked(pos, sq_to_idx("e8"), enemy) and not is_attacked(pos, sq_to_idx("f8"), enemy) and not is_attacked(pos, sq_to_idx("g8"), enemy):
                            moves.append(Move(i, sq_to_idx("g8"), is_castle=True))
                if pos.castling.get("q", False):
                    if b[sq_to_idx("d8")] is None and b[sq_to_idx("c8")] is None and b[sq_to_idx("b8")] is None:
                        if not is_attacked(pos, sq_to_idx("e8"), enemy) and not is_attacked(pos, sq_to_idx("d8"), enemy) and not is_attacked(pos, sq_to_idx("c8"), enemy):
                            moves.append(Move(i, sq_to_idx("c8"), is_castle=True))

    return moves

def make_move(pos: Position, mv: Move) -> Position:
    np = pos.clone()
    b = np.board
    piece = b[mv.from_sq]
    side = pos.side
    enemy = opp(side)

    # clear EP by default
    np.ep_square = None

    # update castling rights on piece move/capture
    def remove_castling_for_square(square: int):
        if square == sq_to_idx("a1"):
            np.castling["Q"] = False
        elif square == sq_to_idx("h1"):
            np.castling["K"] = False
        elif square == sq_to_idx("a8"):
            np.castling["q"] = False
        elif square == sq_to_idx("h8"):
            np.castling["k"] = False
        elif square == sq_to_idx("e1"):
            np.castling["K"] = False
            np.castling["Q"] = False
        elif square == sq_to_idx("e8"):
            np.castling["k"] = False
            np.castling["q"] = False

    remove_castling_for_square(mv.from_sq)
    if b[mv.to_sq] is not None:
        remove_castling_for_square(mv.to_sq)

    b[mv.from_sq] = None

    if mv.is_en_passant:
        b[mv.to_sq] = piece
        tf, tr = idx_file(mv.to_sq), idx_rank(mv.to_sq)
        cap_sq = (tr - 1) * 8 + tf if side == "w" else (tr + 1) * 8 + tf
        b[cap_sq] = None
    elif mv.is_castle and piece is not None and piece[1] == "K":
        b[mv.to_sq] = piece
        if mv.to_sq == sq_to_idx("g1"):
            b[sq_to_idx("h1")] = None
            b[sq_to_idx("f1")] = "wR"
        elif mv.to_sq == sq_to_idx("c1"):
            b[sq_to_idx("a1")] = None
            b[sq_to_idx("d1")] = "wR"
        elif mv.to_sq == sq_to_idx("g8"):
            b[sq_to_idx("h8")] = None
            b[sq_to_idx("f8")] = "bR"
        elif mv.to_sq == sq_to_idx("c8"):
            b[sq_to_idx("a8")] = None
            b[sq_to_idx("d8")] = "bR"
    else:
        if piece is not None and piece[1] == "P" and mv.promotion:
            b[mv.to_sq] = side + mv.promotion.upper()
        else:
            b[mv.to_sq] = piece

    # set en passant square after double pawn move
    if piece is not None and piece[1] == "P":
        fr, tr = idx_rank(mv.from_sq), idx_rank(mv.to_sq)
        if abs(tr - fr) == 2:
            mid_rank = (tr + fr) // 2
            np.ep_square = mid_rank * 8 + idx_file(mv.from_sq)

    np.side = enemy
    return np

def legal_moves(pos: Position) -> List[Move]:
    out = []
    side = pos.side
    for mv in generate_pseudo_moves(pos):
        np = make_move(pos, mv)
        if not in_check(np, side):
            out.append(mv)
    return out

def game_over_score(pos: Position, ply: int) -> Optional[int]:
    lms = legal_moves(pos)
    if lms:
        return None
    if in_check(pos, pos.side):
        return -MATE_SCORE + ply
    return 0

def pst_value(piece: str, sq: int, endgame: bool) -> int:
    side, pt = piece[0], piece[1]
    if pt == "K":
        table = PST["K_END"] if endgame else PST["K_MID"]
    else:
        table = PST[pt]
    idx = sq if side == "w" else (7 - idx_rank(sq)) * 8 + idx_file(sq)
    return table[idx]

def is_passed_pawn(board: List[Optional[str]], sq: int, side: str) -> bool:
    f, r = idx_file(sq), idx_rank(sq)
    enemy = opp(side)
    if side == "w":
        for rr in range(r + 1, 8):
            for ff in (f - 1, f, f + 1):
                if 0 <= ff < 8:
                    p = board[rr * 8 + ff]
                    if p == enemy + "P":
                        return False
    else:
        for rr in range(r - 1, -1, -1):
            for ff in (f - 1, f, f + 1):
                if 0 <= ff < 8:
                    p = board[rr * 8 + ff]
                    if p == enemy + "P":
                        return False
    return True

def evaluate(pos: Position) -> int:
    board = pos.board
    material_nonpawn = 0
    queens = 0
    score = 0

    for i, p in enumerate(board):
        if p is None:
            continue
        side = 1 if p[0] == "w" else -1
        val = PIECE_VALUES[p[1]]
        score += side * val
        if p[1] != "P" and p[1] != "K":
            material_nonpawn += val
        if p[1] == "Q":
            queens += 1

    endgame = (material_nonpawn <= 1300) or queens == 0

    # PST and pawn structure
    for i, p in enumerate(board):
        if p is None:
            continue
        side = 1 if p[0] == "w" else -1
        score += side * pst_value(p, i, endgame)
        if p[1] == "P":
            rank_adv = idx_rank(i) if p[0] == "w" else 7 - idx_rank(i)
            score += side * rank_adv * 8
            if is_passed_pawn(board, i, p[0]):
                score += side * (20 + rank_adv * 12)

    # Bishop pair
    wb = sum(1 for p in board if p == "wB")
    bb = sum(1 for p in board if p == "bB")
    if wb >= 2:
        score += 35
    if bb >= 2:
        score -= 35

    # King safety / activity
    for sidec in ("w", "b"):
        ksq = None
        for i, p in enumerate(board):
            if p == sidec + "K":
                ksq = i
                break
        if ksq is None:
            continue
        sign = 1 if sidec == "w" else -1
        kf, kr = idx_file(ksq), idx_rank(ksq)
        if not endgame:
            shelter = 0
            direction = 1 if sidec == "w" else -1
            front_rank = kr + direction
            if 0 <= front_rank < 8:
                for df in (-1, 0, 1):
                    nf = kf + df
                    if 0 <= nf < 8:
                        p = board[front_rank * 8 + nf]
                        if p == sidec + "P":
                            shelter += 12
            # bonus for castled-ish file
            if (sidec == "w" and ksq in (sq_to_idx("g1"), sq_to_idx("c1"))) or (sidec == "b" and ksq in (sq_to_idx("g8"), sq_to_idx("c8"))):
                shelter += 20
            score += sign * shelter
        else:
            # central king in endgame
            dist_center = abs(kf - 3.5) + abs(kr - 3.5)
            score += sign * int(20 - dist_center * 6)

    # Mobility
    side_save = pos.side
    pos.side = "w"
    wm = len(legal_moves(pos))
    pos.side = "b"
    bm = len(legal_moves(pos))
    pos.side = side_save
    score += (wm - bm) * 4

    return score if pos.side == "w" else -score

def move_score(pos: Position, mv: Move) -> int:
    b = pos.board
    piece = b[mv.from_sq]
    target = b[mv.to_sq]
    score = 0
    if target is not None and piece is not None:
        score += 10 * PIECE_VALUES[target[1]] - PIECE_VALUES[piece[1]]
    if mv.promotion:
        score += PIECE_VALUES[mv.promotion.upper()] + 500
    if mv.is_castle:
        score += 80
    np = make_move(pos, mv)
    if in_check(np, np.side):
        score += 120
    # prefer advancing passed pawns / centralization a bit
    if piece is not None:
        if piece[1] == "P":
            delta = abs(idx_rank(mv.to_sq) - idx_rank(mv.from_sq))
            score += delta * 8
        elif piece[1] in ("N", "B"):
            cf = abs(idx_file(mv.to_sq) - 3.5)
            cr = abs(idx_rank(mv.to_sq) - 3.5)
            score += int(10 - (cf + cr))
    return score

def alphabeta(pos: Position, depth: int, alpha: int, beta: int, ply: int, end_time: float) -> int:
    if time.time() >= end_time:
        raise TimeoutError

    gos = game_over_score(pos, ply)
    if gos is not None:
        return gos
    if depth == 0:
        return evaluate(pos)

    moves = legal_moves(pos)
    moves.sort(key=lambda m: move_score(pos, m), reverse=True)

    best = -INF
    for mv in moves:
        np = make_move(pos, mv)
        val = -alphabeta(np, depth - 1, -beta, -alpha, ply + 1, end_time)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def choose_move(pos: Position, time_limit: float = 0.95) -> str:
    moves = legal_moves(pos)
    if not moves:
        # Should not happen in a valid arena state, but ensure a string.
        return "a1a1"
    if len(moves) == 1:
        return moves[0].uci()

    end_time = time.time() + time_limit
    moves.sort(key=lambda m: move_score(pos, m), reverse=True)
    best_move = moves[0]
    best_val = -INF

    depth = 1
    try:
        while depth <= 4:
            current_best = None
            current_best_val = -INF
            alpha = -INF
            beta = INF

            ordered = sorted(moves, key=lambda m: move_score(pos, m), reverse=True)
            for mv in ordered:
                if time.time() >= end_time:
                    raise TimeoutError
                np = make_move(pos, mv)
                val = -alphabeta(np, depth - 1, -beta, -alpha, 1, end_time)
                if val > current_best_val:
                    current_best_val = val
                    current_best = mv
                if val > alpha:
                    alpha = val

            if current_best is not None:
                best_move = current_best
                best_val = current_best_val
                # principal variation move first next iteration
                moves.remove(best_move)
                moves.insert(0, best_move)

            # early mate found
            if best_val > MATE_SCORE // 2:
                break

            depth += 1
    except TimeoutError:
        pass

    return best_move.uci()

def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        pos = Position.from_pieces(pieces, to_play)
        mv = choose_move(pos, 0.95)
        # Verify legality before returning.
        lms = legal_moves(pos)
        legal_uci = [m.uci() for m in lms]
        if mv in legal_uci:
            return mv
        return legal_uci[0] if legal_uci else "a1a1"
    except Exception:
        # Ultra-safe fallback: generate minimal legal moves if possible.
        try:
            pos = Position.from_pieces(pieces, to_play)
            lms = legal_moves(pos)
            if lms:
                return lms[0].uci()
        except Exception:
            pass
        return "a1a1"
