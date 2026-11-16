
# chess_policy.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math
import random

# ----------------------------
# Board / square utilities
# ----------------------------

FILES = "abcdefgh"
RANKS = "12345678"

def sq_to_idx(sq: str) -> int:
    f = FILES.index(sq[0])
    r = int(sq[1]) - 1
    return r * 8 + f

def idx_to_sq(i: int) -> str:
    return FILES[i % 8] + str(i // 8 + 1)

def on_board(f: int, r: int) -> bool:
    return 0 <= f < 8 and 0 <= r < 8

def piece_color(p: str) -> str:
    return p[0]  # 'w' or 'b'

def piece_type(p: str) -> str:
    return p[1]  # 'P','N','B','R','Q','K'

def other(color: str) -> str:
    return 'b' if color == 'w' else 'w'


# ----------------------------
# Evaluation
# ----------------------------

PIECE_VALUE = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0,
}

# Piece-square tables (from White perspective; Black mirrored)
# Values are modest; material dominates to keep stable.
PST_P = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-20,-20, 10, 10,  5,
     5, -5,-10,  0,  0,-10, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
]
PST_N = [
   -50,-40,-30,-30,-30,-30,-40,-50,
   -40,-20,  0,  5,  5,  0,-20,-40,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -40,-20,  0,  0,  0,  0,-20,-40,
   -50,-40,-30,-30,-30,-30,-40,-50,
]
PST_B = [
   -20,-10,-10,-10,-10,-10,-10,-20,
   -10,  5,  0,  0,  0,  0,  5,-10,
   -10, 10, 10, 10, 10, 10, 10,-10,
   -10,  0, 10, 10, 10, 10,  0,-10,
   -10,  5,  5, 10, 10,  5,  5,-10,
   -10,  0,  5, 10, 10,  5,  0,-10,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -20,-10,-10,-10,-10,-10,-10,-20,
]
PST_R = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]
PST_Q = [
   -20,-10,-10, -5, -5,-10,-10,-20,
   -10,  0,  0,  0,  0,  0,  0,-10,
   -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
     0,  0,  5,  5,  5,  5,  0, -5,
   -10,  5,  5,  5,  5,  5,  0,-10,
   -10,  0,  5,  0,  0,  0,  0,-10,
   -20,-10,-10, -5, -5,-10,-10,-20,
]
PST_K_MID = [
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -30,-40,-40,-50,-50,-40,-40,-30,
   -20,-30,-30,-40,-40,-30,-30,-20,
   -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20,
]
PST_K_END = [
   -50,-30,-30,-30,-30,-30,-30,-50,
   -30,-10,  0,  0,  0,  0,-10,-30,
   -30,  0, 10, 15, 15, 10,  0,-30,
   -30,  5, 15, 20, 20, 15,  5,-30,
   -30,  0, 15, 20, 20, 15,  0,-30,
   -30,  5, 10, 15, 15, 10,  5,-30,
   -30,-10,  0,  5,  5,  0,-10,-30,
   -50,-30,-30,-30,-30,-30,-30,-50,
]

PST_MAP = {
    'P': PST_P,
    'N': PST_N,
    'B': PST_B,
    'R': PST_R,
    'Q': PST_Q,
    'K': PST_K_MID,  # swapped depending on endgame
}

def mirror_idx(i: int) -> int:
    # Mirror vertically (rank flip): a1<->a8 etc.
    f = i % 8
    r = i // 8
    return (7 - r) * 8 + f

def is_endgame(board: List[Optional[str]]) -> bool:
    # crude: endgame if queens absent or total non-pawn material is low
    total_non_pawn = 0
    queens = 0
    for p in board:
        if not p:
            continue
        t = piece_type(p)
        if t == 'Q':
            queens += 1
        if t in ('N', 'B', 'R', 'Q'):
            total_non_pawn += PIECE_VALUE[t]
    return queens == 0 or total_non_pawn <= 1400

def eval_board(board: List[Optional[str]], side: str) -> int:
    # side: 'w' or 'b' to score from that side's perspective.
    endg = is_endgame(board)
    score_w = 0
    for idx, p in enumerate(board):
        if not p:
            continue
        c = piece_color(p)
        t = piece_type(p)
        val = PIECE_VALUE[t]
        if t == 'K':
            pst = PST_K_END if endg else PST_K_MID
        else:
            pst = PST_MAP[t]
        pst_idx = idx if c == 'w' else mirror_idx(idx)
        ps = pst[pst_idx]
        if c == 'w':
            score_w += val + ps
        else:
            score_w -= val + ps
    # Convert to perspective
    return score_w if side == 'w' else -score_w


# ----------------------------
# Move representation / mechanics
# ----------------------------

@dataclass(frozen=True)
class Move:
    frm: int
    to: int
    promo: Optional[str] = None  # 'Q','R','B','N'
    is_castle: bool = False
    is_ep: bool = False
    captured: Optional[int] = None  # square index of captured piece (for EP)
    # captured piece itself not stored (board has it)

def find_king(board: List[Optional[str]], color: str) -> int:
    target = color + 'K'
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1

def attacked_by(board: List[Optional[str]], attacker: str, sq: int) -> bool:
    # attacker: 'w' or 'b'
    f = sq % 8
    r = sq // 8

    # Pawns
    if attacker == 'w':
        for df in (-1, 1):
            nf, nr = f + df, r - 1
            if on_board(nf, nr):
                p = board[nr * 8 + nf]
                if p == 'wP':
                    return True
    else:
        for df in (-1, 1):
            nf, nr = f + df, r + 1
            if on_board(nf, nr):
                p = board[nr * 8 + nf]
                if p == 'bP':
                    return True

    # Knights
    knight_deltas = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
    for df, dr in knight_deltas:
        nf, nr = f + df, r + dr
        if on_board(nf, nr):
            p = board[nr * 8 + nf]
            if p == attacker + 'N':
                return True

    # Kings (adjacent)
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            nf, nr = f + df, r + dr
            if on_board(nf, nr):
                p = board[nr * 8 + nf]
                if p == attacker + 'K':
                    return True

    # Sliding pieces
    # Diagonals: bishop/queen
    for df, dr in [(-1,-1),(-1,1),(1,-1),(1,1)]:
        nf, nr = f + df, r + dr
        while on_board(nf, nr):
            p = board[nr * 8 + nf]
            if p:
                if piece_color(p) == attacker and piece_type(p) in ('B', 'Q'):
                    return True
                break
            nf += df
            nr += dr

    # Orthogonals: rook/queen
    for df, dr in [(-1,0),(1,0),(0,-1),(0,1)]:
        nf, nr = f + df, r + dr
        while on_board(nf, nr):
            p = board[nr * 8 + nf]
            if p:
                if piece_color(p) == attacker and piece_type(p) in ('R', 'Q'):
                    return True
                break
            nf += df
            nr += dr

    return False

def in_check(board: List[Optional[str]], color: str) -> bool:
    k = find_king(board, color)
    if k < 0:
        # Shouldn't happen in legal chess; treat as in check
        return True
    return attacked_by(board, other(color), k)

def apply_move(board: List[Optional[str]], mv: Move, color: str) -> List[Optional[str]]:
    nb = board[:]  # copy
    piece = nb[mv.frm]
    nb[mv.frm] = None

    # Handle captures (including EP)
    if mv.is_ep and mv.captured is not None:
        nb[mv.captured] = None

    # Castling rook move
    if mv.is_castle and piece and piece_type(piece) == 'K':
        # Determine rook movement by king destination
        # White: e1->g1 rook h1->f1; e1->c1 rook a1->d1
        # Black: e8->g8 rook h8->f8; e8->c8 rook a8->d8
        if color == 'w':
            if mv.to == sq_to_idx('g1'):
                rook_from, rook_to = sq_to_idx('h1'), sq_to_idx('f1')
            else:
                rook_from, rook_to = sq_to_idx('a1'), sq_to_idx('d1')
        else:
            if mv.to == sq_to_idx('g8'):
                rook_from, rook_to = sq_to_idx('h8'), sq_to_idx('f8')
            else:
                rook_from, rook_to = sq_to_idx('a8'), sq_to_idx('d8')
        rook = nb[rook_from]
        nb[rook_from] = None
        nb[rook_to] = rook

    # Place moved piece (promotion handled)
    if piece and mv.promo and piece_type(piece) == 'P':
        nb[mv.to] = color + mv.promo
    else:
        nb[mv.to] = piece

    return nb

def gen_pseudo_moves(board: List[Optional[str]], color: str) -> List[Move]:
    moves: List[Move] = []
    their = other(color)
    forward = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promo_rank = 7 if color == 'w' else 0

    for i, p in enumerate(board):
        if not p or piece_color(p) != color:
            continue
        t = piece_type(p)
        f, r = i % 8, i // 8

        if t == 'P':
            # forward one
            nr = r + forward
            if 0 <= nr <= 7:
                to = nr * 8 + f
                if board[to] is None:
                    if nr == promo_rank:
                        for pr in ('Q', 'R', 'B', 'N'):
                            moves.append(Move(i, to, promo=pr))
                    else:
                        moves.append(Move(i, to))
                    # forward two
                    if r == start_rank:
                        nr2 = r + 2 * forward
                        to2 = nr2 * 8 + f
                        if board[to2] is None:
                            moves.append(Move(i, to2))
            # captures
            for df in (-1, 1):
                nf = f + df
                nr = r + forward
                if not on_board(nf, nr):
                    continue
                to = nr * 8 + nf
                tp = board[to]
                if tp and piece_color(tp) == their:
                    if nr == promo_rank:
                        for pr in ('Q', 'R', 'B', 'N'):
                            moves.append(Move(i, to, promo=pr))
                    else:
                        moves.append(Move(i, to))
            # EP not generated (unknown rights)

        elif t == 'N':
            for df, dr in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                nf, nr = f + df, r + dr
                if not on_board(nf, nr):
                    continue
                to = nr * 8 + nf
                tp = board[to]
                if tp is None or piece_color(tp) == their:
                    moves.append(Move(i, to))

        elif t in ('B', 'R', 'Q'):
            dirs = []
            if t in ('B', 'Q'):
                dirs += [(-1,-1),(-1,1),(1,-1),(1,1)]
            if t in ('R', 'Q'):
                dirs += [(-1,0),(1,0),(0,-1),(0,1)]
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while on_board(nf, nr):
                    to = nr * 8 + nf
                    tp = board[to]
                    if tp is None:
                        moves.append(Move(i, to))
                    else:
                        if piece_color(tp) == their:
                            moves.append(Move(i, to))
                        break
                    nf += df
                    nr += dr

        elif t == 'K':
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = f + df, r + dr
                    if not on_board(nf, nr):
                        continue
                    to = nr * 8 + nf
                    tp = board[to]
                    if tp is None or piece_color(tp) == their:
                        moves.append(Move(i, to))
            # crude castling allowance (rights unknown). We'll generate only if pieces on start squares.
            if color == 'w' and i == sq_to_idx('e1'):
                # O-O
                if board[sq_to_idx('h1')] == 'wR' and board[sq_to_idx('f1')] is None and board[sq_to_idx('g1')] is None:
                    moves.append(Move(i, sq_to_idx('g1'), is_castle=True))
                # O-O-O
                if board[sq_to_idx('a1')] == 'wR' and board[sq_to_idx('b1')] is None and board[sq_to_idx('c1')] is None and board[sq_to_idx('d1')] is None:
                    moves.append(Move(i, sq_to_idx('c1'), is_castle=True))
            if color == 'b' and i == sq_to_idx('e8'):
                if board[sq_to_idx('h8')] == 'bR' and board[sq_to_idx('f8')] is None and board[sq_to_idx('g8')] is None:
                    moves.append(Move(i, sq_to_idx('g8'), is_castle=True))
                if board[sq_to_idx('a8')] == 'bR' and board[sq_to_idx('b8')] is None and board[sq_to_idx('c8')] is None and board[sq_to_idx('d8')] is None:
                    moves.append(Move(i, sq_to_idx('c8'), is_castle=True))

    return moves

def gen_legal_moves(board: List[Optional[str]], color: str) -> List[Move]:
    moves = []
    for mv in gen_pseudo_moves(board, color):
        # extra constraints for castling safety
        if mv.is_castle:
            # king may not be in check, and squares passed through not attacked
            if in_check(board, color):
                continue
            k_from = mv.frm
            k_to = mv.to
            # Determine intermediate squares (f-file for O-O, d-file for O-O-O)
            if color == 'w':
                if k_to == sq_to_idx('g1'):
                    through = [sq_to_idx('f1'), sq_to_idx('g1')]
                else:
                    through = [sq_to_idx('d1'), sq_to_idx('c1')]
            else:
                if k_to == sq_to_idx('g8'):
                    through = [sq_to_idx('f8'), sq_to_idx('g8')]
                else:
                    through = [sq_to_idx('d8'), sq_to_idx('c8')]
            # king cannot pass through attacked squares
            ok = True
            for s in through:
                nb = board[:]
                nb[k_from] = None
                nb[s] = color + 'K'
                if attacked_by(nb, other(color), s):
                    ok = False
                    break
            if not ok:
                continue

        nb = apply_move(board, mv, color)
        if not in_check(nb, color):
            moves.append(mv)
    return moves


# ----------------------------
# SAN parsing for given legal_moves
# ----------------------------

def strip_suffixes(s: str) -> str:
    # remove check/mate and common annotations if present
    while s and s[-1] in ['+', '#', '!', '?']:
        s = s[:-1]
    return s

def parse_san_to_move(board: List[Optional[str]], san: str, color: str) -> Optional[Move]:
    s = strip_suffixes(san.strip())

    # Castling
    if s == "O-O" or s == "0-0":
        if color == 'w':
            return Move(sq_to_idx('e1'), sq_to_idx('g1'), is_castle=True)
        else:
            return Move(sq_to_idx('e8'), sq_to_idx('g8'), is_castle=True)
    if s == "O-O-O" or s == "0-0-0":
        if color == 'w':
            return Move(sq_to_idx('e1'), sq_to_idx('c1'), is_castle=True)
        else:
            return Move(sq_to_idx('e8'), sq_to_idx('c8'), is_castle=True)

    promo = None
    if "=" in s:
        base, pr = s.split("=")
        s = base
        promo = pr[0] if pr else None

    # destination square is last two chars of remaining string
    if len(s) < 2:
        return None
    dest_sq = s[-2:]
    if dest_sq[0] not in FILES or dest_sq[1] not in RANKS:
        return None
    to = sq_to_idx(dest_sq)
    body = s[:-2]

    capture = 'x' in body
    body = body.replace('x', '')

    # Determine moving piece
    piece_letter = None
    if body and body[0] in "KQRBN":
        piece_letter = body[0]
        disamb = body[1:]  # may contain file/rank or both
    else:
        piece_letter = 'P'
        disamb = body  # for pawn moves, this is origin file for captures, else empty

    # Find candidate origin squares that can reach `to`
    candidates: List[int] = []
    their = other(color)

    def add_candidate(frm: int):
        if board[frm] == color + piece_letter:
            candidates.append(frm)

    # Target occupancy and EP possibility (only for SAN parsing for given legal list)
    target_piece = board[to]
    is_ep = False
    captured_sq = None

    if piece_letter == 'P':
        # Pawn SAN:
        # - "e4"   (push)
        # - "exd5" (capture; disamb is origin file)
        # Direction
        f_to, r_to = to % 8, to // 8
        if capture:
            if not disamb or disamb[0] not in FILES:
                return None
            f_from = FILES.index(disamb[0])
            r_from = r_to - (1 if color == 'w' else -1)
            if not (0 <= r_from <= 7):
                return None
            frm = r_from * 8 + f_from
            # if destination empty, treat as EP (best-effort)
            if target_piece is None:
                is_ep = True
                # captured pawn is behind destination
                cap_r = r_to - (1 if color == 'w' else -1)
                captured_sq = cap_r * 8 + f_to
            add_candidate(frm)
        else:
            # non-capture: could be one-step or two-step
            f_from = to % 8
            r_from1 = r_to - (1 if color == 'w' else -1)
            if 0 <= r_from1 <= 7:
                add_candidate(r_from1 * 8 + f_from)
            # two-step
            r_from2 = r_to - (2 if color == 'w' else -2)
            if 0 <= r_from2 <= 7:
                add_candidate(r_from2 * 8 + f_from)

    else:
        # Piece move with possible disambiguation (file/rank/both)
        # Find all pieces of that type that can pseudo-move to destination.
        for frm, p in enumerate(board):
            if p != color + piece_letter:
                continue
            if can_piece_reach(board, frm, to, color, piece_letter, capture):
                candidates.append(frm)

        # Apply disambiguation if present
        if disamb:
            # disamb can be file (a-h), rank (1-8), or both (e.g., "bd2": "b" for file)
            filt: List[int] = []
            for frm in candidates:
                fs, rs = frm % 8, frm // 8
                ok = True
                for ch in disamb:
                    if ch in FILES:
                        ok = ok and (fs == FILES.index(ch))
                    elif ch in RANKS:
                        ok = ok and (rs == int(ch) - 1)
                if ok:
                    filt.append(frm)
            candidates = filt

    if not candidates:
        return None

    # Since SAN is legal, there should be exactly one legal origin after filtering;
    # still, we select the one that yields a legal position.
    for frm in candidates:
        mv = Move(frm, to, promo=promo, is_castle=False, is_ep=is_ep, captured=captured_sq)
        nb = apply_move(board, mv, color)
        if not in_check(nb, color):
            return mv

    # Fallback: return first candidate (shouldn't happen if input is legal)
    frm = candidates[0]
    return Move(frm, to, promo=promo, is_castle=False, is_ep=is_ep, captured=captured_sq)

def can_piece_reach(board: List[Optional[str]], frm: int, to: int, color: str, pt: str, is_capture: bool) -> bool:
    their = other(color)
    tp = board[to]
    if is_capture:
        # For captures, destination should be occupied by enemy in normal cases;
        # we won't strictly enforce here.
        if tp and piece_color(tp) == color:
            return False
    else:
        if tp is not None:
            return False

    ff, fr = frm % 8, frm // 8
    tf, tr = to % 8, to // 8
    df, dr = tf - ff, tr - fr

    if pt == 'N':
        return (abs(df), abs(dr)) in [(1,2),(2,1)]
    if pt == 'K':
        return max(abs(df), abs(dr)) == 1
    if pt == 'B':
        if abs(df) != abs(dr) or df == 0:
            return False
        stepf = 1 if df > 0 else -1
        stepr = 1 if dr > 0 else -1
        f, r = ff + stepf, fr + stepr
        while f != tf and r != tr:
            if board[r * 8 + f] is not None:
                return False
            f += stepf
            r += stepr
        return True
    if pt == 'R':
        if df != 0 and dr != 0:
            return False
        stepf = 0 if df == 0 else (1 if df > 0 else -1)
        stepr = 0 if dr == 0 else (1 if dr > 0 else -1)
        f, r = ff + stepf, fr + stepr
        while f != tf or r != tr:
            if board[r * 8 + f] is not None:
                return False
            f += stepf
            r += stepr
        return True
    if pt == 'Q':
        # rook or bishop move
        if df == 0 or dr == 0:
            return can_piece_reach(board, frm, to, color, 'R', is_capture)
        if abs(df) == abs(dr):
            return can_piece_reach(board, frm, to, color, 'B', is_capture)
        return False
    return False


# ----------------------------
# Search
# ----------------------------

MATE_SCORE = 10_000
INF = 1_000_000

def negamax(board: List[Optional[str]], color: str, depth: int, alpha: int, beta: int) -> int:
    # Return score from perspective of `color` to move.
    if depth == 0:
        return eval_board(board, color)

    moves = gen_legal_moves(board, color)
    if not moves:
        # checkmate or stalemate
        if in_check(board, color):
            return -MATE_SCORE + (2 - depth)  # prefer faster mates against us are bad
        return 0  # stalemate

    # Move ordering: captures/promotions first
    def mv_key(m: Move) -> int:
        score = 0
        tp = board[m.to]
        if tp is not None:
            score += 10_000 + PIECE_VALUE[piece_type(tp)]
        if m.promo:
            score += 9_000 + PIECE_VALUE[m.promo]
        if m.is_castle:
            score += 500
        return -score

    moves.sort(key=mv_key)

    best = -INF
    for mv in moves:
        nb = apply_move(board, mv, color)
        val = -negamax(nb, other(color), depth - 1, -beta, -alpha)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best

def quick_san_bonus(san: str) -> int:
    s = san.strip()
    b = 0
    if s.endswith('+'):
        b += 60
    if s.endswith('#'):
        b += 10_000
    if s.startswith('O-O'):
        b += 40
    if '=Q' in s:
        b += 800
    elif '=R' in s:
        b += 400
    elif '=B' in s or '=N' in s:
        b += 250
    if 'x' in s:
        b += 10
    return b


# ----------------------------
# Required API
# ----------------------------

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    # Always return a legal move string from legal_moves.
    if not legal_moves:
        return ""  # should not happen in arena

    # 1) If SAN includes a mate marker, play it immediately.
    for m in legal_moves:
        if m.strip().endswith('#'):
            return m

    # Build internal board
    board: List[Optional[str]] = [None] * 64
    for sq, pc in pieces.items():
        try:
            board[sq_to_idx(sq)] = pc
        except Exception:
            # ignore malformed; should not happen
            pass

    color = 'w' if to_play == 'white' else 'b'

    # Parse each provided legal SAN move; score with shallow search.
    best_move = legal_moves[0]
    best_score = -INF

    # Small random to break ties (but stable across identical evals)
    rnd = random.Random(0xC0FFEE)

    # Root depth (2 ply = us + opponent). Keep fast and robust.
    depth = 2

    for san in legal_moves:
        mv = parse_san_to_move(board, san, color)
        if mv is None:
            # If we fail to parse, still must be legal: deprioritize but keep valid.
            score = -999999 + rnd.randint(0, 5)
        else:
            nb = apply_move(board, mv, color)
            # If somehow illegal (shouldn't be), deprioritize.
            if in_check(nb, color):
                score = -999999 + rnd.randint(0, 5)
            else:
                score = quick_san_bonus(san)
                score += -negamax(nb, other(color), depth - 1, -INF, INF)

        if score > best_score:
            best_score = score
            best_move = san

    # Final safety: ensure we output a provided legal move string
    if best_move not in legal_moves:
        return legal_moves[0]
    return best_move
