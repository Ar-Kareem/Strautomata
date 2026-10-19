
# chess_policy.py
from __future__ import annotations

import time
import re
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict

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

# Simple piece-square tables (middlegame-ish), from White's perspective.
# Index: 0=a1 ... 7=h1 ... 56=a8 ... 63=h8 (we'll map accordingly).
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
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
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
    "K": [
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20,
    ],
}

KNIGHT_OFFSETS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                  (1, -2), (1, 2), (2, -1), (2, 1)]
KING_OFFSETS = [(-1, -1), (-1, 0), (-1, 1),
                (0, -1),          (0, 1),
                (1, -1),  (1, 0), (1, 1)]
BISHOP_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
ROOK_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

MATE_SCORE = 10_000_000


@dataclass(frozen=True)
class Move:
    frm: int
    to: int
    promo: Optional[str] = None  # 'Q','R','B','N'
    castle: Optional[str] = None  # 'K' or 'Q' (kingside/queenside)
    en_passant: bool = False


def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    # Always return something legal.
    if not legal_moves:
        return "O-O"  # should never happen if input is valid

    side = "w" if to_play.lower().startswith("w") else "b"
    board = dict_to_board(pieces)

    # Parse root legal moves to internal Move objects; keep mapping to original strings.
    root_moves: List[Tuple[str, Move]] = []
    for ms in legal_moves:
        mv = parse_move_string(ms, board, side)
        if mv is None:
            # If parsing fails, keep it as a fallback by assigning a dummy; we'll avoid using it unless needed.
            continue
        root_moves.append((ms, mv))

    if not root_moves:
        # Fallback: if SAN parsing failed across the board, just return first legal move.
        return legal_moves[0]

    # Time-bounded iterative deepening (small max depth to stay safe under 1s).
    start = time.time()
    time_limit = 0.92  # seconds

    # Move ordering at root.
    root_moves_sorted = sorted(root_moves, key=lambda x: move_order_key(board, side, x[1]), reverse=True)

    best_ms = root_moves_sorted[0][0]
    best_score = -10**18

    # Iterative deepening.
    for depth in (1, 2, 3):
        if time.time() - start > time_limit:
            break

        alpha = -10**18
        beta = 10**18
        current_best_ms = best_ms
        current_best_score = -10**18

        for ms, mv in root_moves_sorted:
            if time.time() - start > time_limit:
                break
            child = apply_move(board, mv, side)
            score = -negamax(child, other(side), depth - 1, -beta, -alpha, 1, start, time_limit)
            # Tie-breakers: prefer higher score; if equal, prefer tactical-looking move key.
            if score > current_best_score:
                current_best_score = score
                current_best_ms = ms
            if score > alpha:
                alpha = score

        # Update principal variation move if we finished most of the depth.
        best_ms = current_best_ms
        best_score = current_best_score

        # If we found a forced mate, we can stop.
        if best_score >= MATE_SCORE - 10_000:
            break

    # Ensure returned move is legal as per provided list.
    if best_ms in legal_moves:
        return best_ms
    return legal_moves[0]


# ---------------- Board helpers ----------------

def dict_to_board(pieces: Dict[str, str]) -> List[Optional[str]]:
    board = [None] * 64
    for sq, pc in pieces.items():
        idx = sq_to_i(sq)
        board[idx] = pc
    return board


def sq_to_i(sq: str) -> int:
    f = FILES.index(sq[0])
    r = RANKS.index(sq[1])
    return r * 8 + f


def i_to_xy(i: int) -> Tuple[int, int]:
    return (i % 8, i // 8)


def xy_to_i(x: int, y: int) -> int:
    return y * 8 + x


def on_board(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def other(color: str) -> str:
    return "b" if color == "w" else "w"


def find_king(board: List[Optional[str]], color: str) -> Optional[int]:
    target = color + "K"
    for i, pc in enumerate(board):
        if pc == target:
            return i
    return None


# ---------------- Attack / legality ----------------

def is_attacked(board: List[Optional[str]], sq: int, by_color: str) -> bool:
    x, y = i_to_xy(sq)

    # Pawns
    if by_color == "w":
        for dx in (-1, 1):
            x2, y2 = x - dx, y - 1  # from pawn to target: pawn at (x-dx, y-1) attacks (x,y)
            if on_board(x2, y2):
                pc = board[xy_to_i(x2, y2)]
                if pc == "wP":
                    return True
    else:
        for dx in (-1, 1):
            x2, y2 = x - dx, y + 1
            if on_board(x2, y2):
                pc = board[xy_to_i(x2, y2)]
                if pc == "bP":
                    return True

    # Knights
    for dx, dy in KNIGHT_OFFSETS:
        x2, y2 = x + dx, y + dy
        if on_board(x2, y2):
            pc = board[xy_to_i(x2, y2)]
            if pc == by_color + "N":
                return True

    # Kings
    for dx, dy in KING_OFFSETS:
        x2, y2 = x + dx, y + dy
        if on_board(x2, y2):
            pc = board[xy_to_i(x2, y2)]
            if pc == by_color + "K":
                return True

    # Sliding pieces: bishops/queens (diagonals)
    for dx, dy in BISHOP_DIRS:
        x2, y2 = x + dx, y + dy
        while on_board(x2, y2):
            pc = board[xy_to_i(x2, y2)]
            if pc is not None:
                if pc[0] == by_color and pc[1] in ("B", "Q"):
                    return True
                break
            x2 += dx
            y2 += dy

    # Sliding pieces: rooks/queens (orthogonals)
    for dx, dy in ROOK_DIRS:
        x2, y2 = x + dx, y + dy
        while on_board(x2, y2):
            pc = board[xy_to_i(x2, y2)]
            if pc is not None:
                if pc[0] == by_color and pc[1] in ("R", "Q"):
                    return True
                break
            x2 += dx
            y2 += dy

    return False


def in_check(board: List[Optional[str]], color: str) -> bool:
    ksq = find_king(board, color)
    if ksq is None:
        # Shouldn't happen in valid chess; treat as "in check" to avoid illegal lines.
        return True
    return is_attacked(board, ksq, other(color))


# ---------------- Move generation ----------------

def generate_legal_moves(board: List[Optional[str]], color: str) -> List[Move]:
    moves: List[Move] = []
    for i, pc in enumerate(board):
        if pc is None or pc[0] != color:
            continue
        p = pc[1]
        if p == "P":
            gen_pawn_moves(board, color, i, moves)
        elif p == "N":
            gen_knight_moves(board, color, i, moves)
        elif p == "B":
            gen_slider_moves(board, color, i, moves, BISHOP_DIRS)
        elif p == "R":
            gen_slider_moves(board, color, i, moves, ROOK_DIRS)
        elif p == "Q":
            gen_slider_moves(board, color, i, moves, QUEEN_DIRS)
        elif p == "K":
            gen_king_moves(board, color, i, moves)

    # Filter by king safety.
    legal: List[Move] = []
    for mv in moves:
        nb = apply_move(board, mv, color)
        if not in_check(nb, color):
            legal.append(mv)
    return legal


def gen_pawn_moves(board: List[Optional[str]], color: str, frm: int, out: List[Move]) -> None:
    x, y = i_to_xy(frm)
    diry = 1 if color == "w" else -1
    start_rank = 1 if color == "w" else 6  # y index: rank2 -> 1, rank7 -> 6
    promo_rank = 7 if color == "w" else 0

    # One step forward
    y1 = y + diry
    if on_board(x, y1):
        to1 = xy_to_i(x, y1)
        if board[to1] is None:
            if y1 == promo_rank:
                for pr in ("Q", "R", "B", "N"):
                    out.append(Move(frm, to1, promo=pr))
            else:
                out.append(Move(frm, to1))
            # Two steps
            if y == start_rank:
                y2 = y + 2 * diry
                to2 = xy_to_i(x, y2)
                if on_board(x, y2) and board[to2] is None:
                    out.append(Move(frm, to2))

    # Captures (including promotion captures)
    for dx in (-1, 1):
        x2, y2 = x + dx, y + diry
        if not on_board(x2, y2):
            continue
        to = xy_to_i(x2, y2)
        tgt = board[to]
        if tgt is not None and tgt[0] != color:
            if y2 == promo_rank:
                for pr in ("Q", "R", "B", "N"):
                    out.append(Move(frm, to, promo=pr))
            else:
                out.append(Move(frm, to))
        # En passant rights unknown (no history) => we do not generate it here.


def gen_knight_moves(board: List[Optional[str]], color: str, frm: int, out: List[Move]) -> None:
    x, y = i_to_xy(frm)
    for dx, dy in KNIGHT_OFFSETS:
        x2, y2 = x + dx, y + dy
        if not on_board(x2, y2):
            continue
        to = xy_to_i(x2, y2)
        tgt = board[to]
        if tgt is None or tgt[0] != color:
            out.append(Move(frm, to))


def gen_slider_moves(board: List[Optional[str]], color: str, frm: int, out: List[Move], dirs) -> None:
    x, y = i_to_xy(frm)
    for dx, dy in dirs:
        x2, y2 = x + dx, y + dy
        while on_board(x2, y2):
            to = xy_to_i(x2, y2)
            tgt = board[to]
            if tgt is None:
                out.append(Move(frm, to))
            else:
                if tgt[0] != color:
                    out.append(Move(frm, to))
                break
            x2 += dx
            y2 += dy


def gen_king_moves(board: List[Optional[str]], color: str, frm: int, out: List[Move]) -> None:
    x, y = i_to_xy(frm)
    for dx, dy in KING_OFFSETS:
        x2, y2 = x + dx, y + dy
        if not on_board(x2, y2):
            continue
        to = xy_to_i(x2, y2)
        tgt = board[to]
        if tgt is None or tgt[0] != color:
            out.append(Move(frm, to))

    # Castling (best-effort: assume rights if king/rook on starting squares)
    # White: king e1, rooks a1/h1. Black: king e8, rooks a8/h8.
    if color == "w" and frm == sq_to_i("e1") and board[frm] == "wK":
        # Kingside
        if board[sq_to_i("h1")] == "wR" and board[sq_to_i("f1")] is None and board[sq_to_i("g1")] is None:
            if not is_attacked(board, sq_to_i("e1"), "b") and not is_attacked(board, sq_to_i("f1"), "b") and not is_attacked(board, sq_to_i("g1"), "b"):
                out.append(Move(frm, sq_to_i("g1"), castle="K"))
        # Queenside
        if board[sq_to_i("a1")] == "wR" and board[sq_to_i("b1")] is None and board[sq_to_i("c1")] is None and board[sq_to_i("d1")] is None:
            if not is_attacked(board, sq_to_i("e1"), "b") and not is_attacked(board, sq_to_i("d1"), "b") and not is_attacked(board, sq_to_i("c1"), "b"):
                out.append(Move(frm, sq_to_i("c1"), castle="Q"))

    if color == "b" and frm == sq_to_i("e8") and board[frm] == "bK":
        # Kingside
        if board[sq_to_i("h8")] == "bR" and board[sq_to_i("f8")] is None and board[sq_to_i("g8")] is None:
            if not is_attacked(board, sq_to_i("e8"), "w") and not is_attacked(board, sq_to_i("f8"), "w") and not is_attacked(board, sq_to_i("g8"), "w"):
                out.append(Move(frm, sq_to_i("g8"), castle="K"))
        # Queenside
        if board[sq_to_i("a8")] == "bR" and board[sq_to_i("b8")] is None and board[sq_to_i("c8")] is None and board[sq_to_i("d8")] is None:
            if not is_attacked(board, sq_to_i("e8"), "w") and not is_attacked(board, sq_to_i("d8"), "w") and not is_attacked(board, sq_to_i("c8"), "w"):
                out.append(Move(frm, sq_to_i("c8"), castle="Q"))


def apply_move(board: List[Optional[str]], mv: Move, color: str) -> List[Optional[str]]:
    nb = board[:]  # copy
    pc = nb[mv.frm]
    nb[mv.frm] = None

    # Castling
    if mv.castle is not None and pc is not None and pc[1] == "K":
        nb[mv.to] = pc
        if color == "w":
            if mv.castle == "K":
                # rook h1 -> f1
                nb[sq_to_i("h1")] = None
                nb[sq_to_i("f1")] = "wR"
            else:
                # rook a1 -> d1
                nb[sq_to_i("a1")] = None
                nb[sq_to_i("d1")] = "wR"
        else:
            if mv.castle == "K":
                nb[sq_to_i("h8")] = None
                nb[sq_to_i("f8")] = "bR"
            else:
                nb[sq_to_i("a8")] = None
                nb[sq_to_i("d8")] = "bR"
        return nb

    # En passant capture (best-effort)
    if mv.en_passant and pc is not None and pc[1] == "P":
        # Destination is empty; captured pawn is behind destination.
        tx, ty = i_to_xy(mv.to)
        if color == "w":
            cap_sq = xy_to_i(tx, ty - 1)
        else:
            cap_sq = xy_to_i(tx, ty + 1)
        nb[cap_sq] = None

    # Normal move / capture
    if pc is None:
        return nb  # shouldn't happen, but avoid crash
    # Promotion
    if mv.promo is not None and pc[1] == "P":
        nb[mv.to] = color + mv.promo
    else:
        nb[mv.to] = pc
    return nb


# ---------------- Search ----------------

def negamax(board: List[Optional[str]], color: str, depth: int, alpha: int, beta: int, ply: int,
            start: float, time_limit: float) -> int:
    if time.time() - start > time_limit:
        return evaluate_pov(board, color)

    if depth <= 0:
        return evaluate_pov(board, color)

    moves = generate_legal_moves(board, color)
    if not moves:
        # Checkmate or stalemate
        if in_check(board, color):
            return -MATE_SCORE + ply
        return 0

    # Move ordering
    moves.sort(key=lambda mv: move_order_key(board, color, mv), reverse=True)

    best = -10**18
    oc = other(color)
    for mv in moves:
        if time.time() - start > time_limit:
            break
        child = apply_move(board, mv, color)
        score = -negamax(child, oc, depth - 1, -beta, -alpha, ply + 1, start, time_limit)
        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def evaluate_white(board: List[Optional[str]]) -> int:
    score = 0
    for i, pc in enumerate(board):
        if pc is None:
            continue
        col, pt = pc[0], pc[1]
        val = PIECE_VALUES[pt]
        pst = PST[pt][i if col == "w" else mirror_i(i)]
        if col == "w":
            score += val + pst
        else:
            score -= val + pst
    # Small mobility term to reduce aimless play
    # (bounded by generating pseudo-ish legal moves quickly is expensive; omit deep mobility)
    return score


def evaluate_pov(board: List[Optional[str]], color: str) -> int:
    w = evaluate_white(board)
    return w if color == "w" else -w


def mirror_i(i: int) -> int:
    # Flip vertically for black PST usage: a1 <-> a8, etc.
    x, y = i_to_xy(i)
    return xy_to_i(x, 7 - y)


def move_order_key(board: List[Optional[str]], color: str, mv: Move) -> int:
    # Higher is better for ordering.
    key = 0
    # Promotions
    if mv.promo is not None:
        key += 10_000 + PIECE_VALUES[mv.promo]
    # Captures (MVV-LVA style)
    tgt = board[mv.to]
    if tgt is not None and tgt[0] != color:
        attacker = board[mv.frm]
        av = PIECE_VALUES[attacker[1]] if attacker else 0
        key += 5_000 + 10 * PIECE_VALUES[tgt[1]] - av
    # Castling
    if mv.castle is not None:
        key += 800
    # Give check (quick test)
    nb = apply_move(board, mv, color)
    ok = find_king(nb, other(color))
    if ok is not None and is_attacked(nb, ok, color):
        key += 1200
    # Centralization preference
    tx, ty = i_to_xy(mv.to)
    key += 10 * (3 - abs(3.5 - tx)) + 10 * (3 - abs(3.5 - ty))
    return int(key)


# ---------------- SAN / move-string parsing ----------------

_SAN_STRIP_RE = re.compile(r"[+#?!]*$")

def parse_move_string(ms: str, board: List[Optional[str]], color: str) -> Optional[Move]:
    if not ms:
        return None

    s = ms.strip()
    s = s.replace("0-0-0", "O-O-O").replace("0-0", "O-O")
    s = s.replace("e.p.", "").replace("ep", "").strip()
    s = _SAN_STRIP_RE.sub("", s)

    # Coordinate notation support: e2e4, e7e8q, etc.
    m = re.fullmatch(r"([a-h][1-8])([a-h][1-8])([qrbnQRBN])?", s)
    if m:
        frm = sq_to_i(m.group(1))
        to = sq_to_i(m.group(2))
        promo = m.group(3).upper() if m.group(3) else None
        # If it looks like castling in coords, keep normal.
        # Determine en passant? no.
        return Move(frm, to, promo=promo)

    # Castling
    if s == "O-O":
        if color == "w":
            return Move(sq_to_i("e1"), sq_to_i("g1"), castle="K")
        else:
            return Move(sq_to_i("e8"), sq_to_i("g8"), castle="K")
    if s == "O-O-O":
        if color == "w":
            return Move(sq_to_i("e1"), sq_to_i("c1"), castle="Q")
        else:
            return Move(sq_to_i("e8"), sq_to_i("c8"), castle="Q")

    # Promotion
    promo = None
    if "=" in s:
        base, pr = s.split("=", 1)
        if pr:
            promo = pr[0].upper()
        s = base

    # Destination is last 2 chars
    if len(s) < 2 or s[-2] not in FILES or s[-1] not in RANKS:
        return None
    dest_sq = s[-2:]
    to = sq_to_i(dest_sq)

    capture = "x" in s
    core = s[:-2]

    # Piece letter or pawn
    piece_type = None
    if core and core[0] in "KQRBN":
        piece_type = core[0]
        rest = core[1:]
    else:
        piece_type = "P"
        rest = core

    # Remove capture marker for disambiguation parsing
    rest_no_x = rest.replace("x", "")

    if piece_type == "P":
        # Pawn SAN: "e4" or "exd5" (possibly with promotion handled above)
        from_file = None
        if capture:
            if not rest_no_x:
                return None
            from_file = rest_no_x[0] if rest_no_x[0] in FILES else None
            if from_file is None:
                return None
            candidates = pawn_capture_sources(board, color, from_file, to)
            # Allow en passant as best-effort if dest empty but capture indicated.
            enp = (board[to] is None)
        else:
            candidates = pawn_push_sources(board, color, to)
            enp = False

        for frm in candidates:
            mv = Move(frm, to, promo=promo, en_passant=enp)
            nb = apply_move(board, mv, color)
            if not in_check(nb, color):
                return mv
        # If all fail, still return first candidate (shouldn't happen with correct legal_moves)
        if candidates:
            return Move(candidates[0], to, promo=promo, en_passant=enp)
        return None

    # Piece moves with possible disambiguation like Nbd2, R1e2, Nec3 etc.
    disamb = rest_no_x  # may be '', 'b', '1', 'e2' etc.
    dis_file = None
    dis_rank = None
    if len(disamb) == 1:
        if disamb in FILES:
            dis_file = disamb
        elif disamb in RANKS:
            dis_rank = disamb
    elif len(disamb) == 2:
        # Could be file+rank
        if disamb[0] in FILES and disamb[1] in RANKS:
            dis_file, dis_rank = disamb[0], disamb[1]
        else:
            # Rare formats; ignore.
            pass
    elif len(disamb) > 2:
        # Ignore extra (shouldn't appear in legal SAN)
        pass

    candidates = []
    for frm, pc in enumerate(board):
        if pc is None or pc[0] != color or pc[1] != piece_type:
            continue
        if dis_file is not None:
            fx, _ = i_to_xy(frm)
            if FILES[fx] != dis_file:
                continue
        if dis_rank is not None:
            _, fy = i_to_xy(frm)
            if RANKS[fy] != dis_rank:
                continue
        if can_piece_move(board, frm, to, pc, require_capture=capture):
            candidates.append(frm)

    for frm in candidates:
        mv = Move(frm, to, promo=promo)
        nb = apply_move(board, mv, color)
        if not in_check(nb, color):
            return mv

    if candidates:
        return Move(candidates[0], to, promo=promo)
    return None


def pawn_push_sources(board: List[Optional[str]], color: str, to: int) -> List[int]:
    tx, ty = i_to_xy(to)
    diry = 1 if color == "w" else -1
    start_rank = 1 if color == "w" else 6

    sources = []
    # One step behind
    y1 = ty - diry
    if on_board(tx, y1):
        frm1 = xy_to_i(tx, y1)
        if board[frm1] == color + "P" and board[to] is None:
            sources.append(frm1)
    # Two steps behind (only if to is two ahead from start)
    y2 = ty - 2 * diry
    if on_board(tx, y2):
        frm2 = xy_to_i(tx, y2)
        mid = xy_to_i(tx, ty - diry) if on_board(tx, ty - diry) else None
        if board[frm2] == color + "P" and board[to] is None and mid is not None and board[mid] is None:
            _, fy = i_to_xy(frm2)
            if fy == start_rank:
                sources.append(frm2)
    return sources


def pawn_capture_sources(board: List[Optional[str]], color: str, from_file: str, to: int) -> List[int]:
    tx, ty = i_to_xy(to)
    fx = FILES.index(from_file)
    diry = 1 if color == "w" else -1
    sources = []
    # Pawn must come from (fx, ty - diry) and move diagonally to (tx, ty)
    frm_y = ty - diry
    if on_board(fx, frm_y):
        frm = xy_to_i(fx, frm_y)
        if board[frm] == color + "P":
            # Capture could be normal (dest occupied by enemy) or en passant (dest empty).
            if abs(tx - fx) == 1 and ty - frm_y == diry:
                sources.append(frm)
    return sources


def can_piece_move(board: List[Optional[str]], frm: int, to: int, pc: str, require_capture: bool) -> bool:
    if frm == to:
        return False
    color, pt = pc[0], pc[1]
    tgt = board[to]
    if tgt is not None and tgt[0] == color:
        return False
    if require_capture and tgt is None:
        return False
    if (not require_capture) and tgt is not None:
        # In SAN, non-capture should not land on occupied square.
        return False

    fx, fy = i_to_xy(frm)
    tx, ty = i_to_xy(to)
    dx, dy = tx - fx, ty - fy

    if pt == "N":
        return (dx, dy) in {(a, b) for a, b in KNIGHT_OFFSETS}
    if pt == "K":
        return max(abs(dx), abs(dy)) == 1
    if pt == "B":
        if abs(dx) != abs(dy):
            return False
        return path_clear(board, frm, to, step(sign(dx), sign(dy)))
    if pt == "R":
        if dx != 0 and dy != 0:
            return False
        sx, sy = sign(dx), sign(dy)
        return path_clear(board, frm, to, step(sx, sy))
    if pt == "Q":
        if dx == 0 or dy == 0 or abs(dx) == abs(dy):
            sx, sy = sign(dx), sign(dy)
            return path_clear(board, frm, to, step(sx, sy))
        return False
    # Pawns handled elsewhere
    return False


def sign(v: int) -> int:
    return (v > 0) - (v < 0)


def step(sx: int, sy: int) -> Tuple[int, int]:
    return sx, sy


def path_clear(board: List[Optional[str]], frm: int, to: int, st: Tuple[int, int]) -> bool:
    sx, sy = st
    fx, fy = i_to_xy(frm)
    tx, ty = i_to_xy(to)
    x, y = fx + sx, fy + sy
    while (x, y) != (tx, ty):
        if not on_board(x, y):
            return False
        if board[xy_to_i(x, y)] is not None:
            return False
        x += sx
        y += sy
    return True
