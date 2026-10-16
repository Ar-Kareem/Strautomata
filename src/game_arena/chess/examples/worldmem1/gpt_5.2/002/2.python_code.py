
from __future__ import annotations

from dataclasses import dataclass
import math
import re
from typing import Dict, List, Tuple, Optional, Set


# ----------------------------
# Core API
# ----------------------------

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    if not legal_moves:
        # Should never happen in a legal chess environment, but must return something.
        return ("", memory)

    color = "w" if to_play == "white" else "b"

    # Immediate mate if available
    for mv in legal_moves:
        if "#" in mv:
            _update_memory(memory, pieces, color)
            return (mv, memory)

    # Lightweight opening preferences (only if clearly early and move present)
    if _looks_like_initial_position(pieces):
        if color == "w":
            for pref in ("e4", "d4", "Nf3", "c4"):
                if pref in legal_moves:
                    _update_memory(memory, pieces, color)
                    return (pref, memory)

    # Evaluate all moves by simulation + static eval
    base_eval = _evaluate_position(pieces)

    best_move = legal_moves[0]
    best_score = -float("inf")

    # Repetition discouragement (soft)
    hist = memory.get("history", [])
    hist_set = set(hist[-10:]) if hist else set()

    for mv in legal_moves:
        score = _score_move(mv, pieces, color, base_eval, hist_set)
        if score > best_score:
            best_score = score
            best_move = mv

    _update_memory(memory, pieces, color)
    return (best_move, memory)


def _update_memory(memory: dict, pieces: dict[str, str], color: str) -> None:
    # Store a short history of board hashes to softly avoid repetition
    h = _board_hash(pieces)
    history = memory.get("history")
    if history is None:
        history = []
    history.append(h)
    if len(history) > 32:
        history = history[-32:]
    memory["history"] = history
    memory["last_color"] = color
    memory["prev_pieces"] = dict(pieces)


# ----------------------------
# Board / move utilities
# ----------------------------

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}

# Simple, fast piece-square tables (white perspective). Black is mirrored.
# Values are in centipawns; intentionally modest to keep material primary.
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

SAN_STRIP_RE = re.compile(r"[!?]+$")


def _board_hash(pieces: dict[str, str]) -> str:
    # Deterministic compact hash from sorted items
    items = sorted(pieces.items())
    return "|".join([f"{sq}{pc}" for sq, pc in items])


def _looks_like_initial_position(pieces: dict[str, str]) -> bool:
    # Loose check: 32 pieces and both kings on e1/e8 and pawns on 2nd/7th ranks
    if len(pieces) != 32:
        return False
    if pieces.get("e1") != "wK" or pieces.get("e8") != "bK":
        return False
    # a2..h2 and a7..h7 pawns
    for f in FILES:
        if pieces.get(f + "2") != "wP":
            return False
        if pieces.get(f + "7") != "bP":
            return False
    return True


def _sq_to_xy(sq: str) -> tuple[int, int]:
    return (FILES.index(sq[0]), RANKS.index(sq[1]))


def _xy_to_sq(x: int, y: int) -> str:
    return FILES[x] + RANKS[y]


def _in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def _mirror_index_for_black(idx: int) -> int:
    # idx is 0..63 in a1..h8 (row-major from rank1 upwards)
    # Mirror vertically: rank r -> 7-r
    r = idx // 8
    f = idx % 8
    mr = 7 - r
    return mr * 8 + f


def _pst_value(piece_type: str, sq: str, color: str) -> int:
    x, y = _sq_to_xy(sq)
    idx = y * 8 + x  # rank1 is y=0
    table = PST[piece_type]
    if color == "w":
        return table[idx]
    else:
        return table[_mirror_index_for_black(idx)]


def _evaluate_position(pieces: dict[str, str]) -> float:
    # Positive means better for White
    score = 0

    bishops_w = 0
    bishops_b = 0

    for sq, pc in pieces.items():
        c = pc[0]
        t = pc[1]
        val = PIECE_VALUES[t]
        pst = _pst_value(t, sq, c)

        if c == "w":
            score += val + pst
            if t == "B":
                bishops_w += 1
        else:
            score -= val + pst
            if t == "B":
                bishops_b += 1

    # Bishop pair bonus
    if bishops_w >= 2:
        score += 30
    if bishops_b >= 2:
        score -= 30

    # Simple king safety / castling encouragement
    wk = _find_king("w", pieces)
    bk = _find_king("b", pieces)
    if wk in ("g1", "c1"):
        score += 25
    if bk in ("g8", "c8"):
        score -= 25

    # Modest mobility proxy: number of attacked squares (excluding pawns to reduce noise)
    w_att = _attacked_squares("w", pieces, include_pawns=False)
    b_att = _attacked_squares("b", pieces, include_pawns=False)
    score += 0.4 * (len(w_att) - len(b_att))

    return score


def _find_king(color: str, pieces: dict[str, str]) -> str:
    target = color + "K"
    for sq, pc in pieces.items():
        if pc == target:
            return sq
    # Should never happen
    return "e1" if color == "w" else "e8"


def _attacked_squares(color: str, pieces: dict[str, str], include_pawns: bool = True) -> Set[str]:
    out: Set[str] = set()
    for sq, pc in pieces.items():
        if pc[0] != color:
            continue
        t = pc[1]
        if (not include_pawns) and t == "P":
            continue
        out |= _piece_attacks_from(sq, pc, pieces)
    return out


def _king_in_check(color: str, pieces: dict[str, str]) -> bool:
    king_sq = _find_king(color, pieces)
    opp = "b" if color == "w" else "w"
    return king_sq in _attacked_squares(opp, pieces, include_pawns=True)


def _piece_attacks_from(src: str, pc: str, pieces: dict[str, str]) -> Set[str]:
    color, t = pc[0], pc[1]
    sx, sy = _sq_to_xy(src)
    attacks: Set[str] = set()

    if t == "P":
        dy = 1 if color == "w" else -1
        for dx in (-1, 1):
            x, y = sx + dx, sy + dy
            if _in_bounds(x, y):
                attacks.add(_xy_to_sq(x, y))
        return attacks

    if t == "N":
        for dx, dy in ((1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)):
            x, y = sx + dx, sy + dy
            if _in_bounds(x, y):
                attacks.add(_xy_to_sq(x, y))
        return attacks

    if t == "K":
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                x, y = sx + dx, sy + dy
                if _in_bounds(x, y):
                    attacks.add(_xy_to_sq(x, y))
        return attacks

    # Sliders
    dirs = []
    if t in ("B", "Q"):
        dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
    if t in ("R", "Q"):
        dirs += [(1,0),(-1,0),(0,1),(0,-1)]

    for dx, dy in dirs:
        x, y = sx + dx, sy + dy
        while _in_bounds(x, y):
            sq = _xy_to_sq(x, y)
            attacks.add(sq)
            if sq in pieces:
                break
            x += dx
            y += dy

    return attacks


@dataclass
class MoveMeta:
    moved_from: Optional[str] = None
    moved_to: Optional[str] = None
    moved_piece: Optional[str] = None
    captured_piece: Optional[str] = None
    promotion: Optional[str] = None
    is_castle: bool = False
    is_ep: bool = False


def _score_move(move: str, pieces: dict[str, str], color: str, base_eval: float, hist_set: set[str]) -> float:
    # If parsing fails, fall back to a SAN-string heuristic but still return a score.
    try:
        new_pieces, meta = _apply_san_move(pieces, color, move)
        # Should always remain legal (given legal_moves), but keep guard:
        if _king_in_check(color, new_pieces):
            return -1e9
        after_eval = _evaluate_position(new_pieces)
    except Exception:
        # Heuristic only (still produces some ordering)
        return _fallback_san_score(move)

    persp = 1.0 if color == "w" else -1.0
    score = persp * after_eval

    # Tactical/tempo nudges using SAN glyphs and move type
    if "#" in move:
        return 1e9
    if "+" in move:
        score += 55

    if meta.is_castle:
        score += 35

    if meta.promotion:
        # Already in eval, but emphasize promotions (esp. to Q)
        promo_val = PIECE_VALUES.get(meta.promotion, 0)
        score += 0.2 * promo_val

    # Captures: MVV-ish encouragement
    if meta.captured_piece:
        cap_val = PIECE_VALUES[meta.captured_piece[1]]
        moved_val = PIECE_VALUES[meta.moved_piece[1]] if meta.moved_piece else 0
        score += 0.35 * cap_val - 0.08 * moved_val

    # Hanging-piece penalty: if moved piece ends up attacked and not defended
    if meta.moved_to and meta.moved_piece and meta.moved_piece[1] != "K":
        opp = "b" if color == "w" else "w"
        opp_att = _attacked_squares(opp, new_pieces, include_pawns=True)
        our_def = _attacked_squares(color, new_pieces, include_pawns=True)
        if meta.moved_to in opp_att and meta.moved_to not in our_def:
            v = PIECE_VALUES[meta.moved_piece[1]]
            if v >= 300:
                score -= 0.55 * v
            elif v >= 100:
                score -= 0.25 * v

    # Softly avoid repetition if possible
    h = _board_hash(new_pieces)
    if h in hist_set:
        score -= 25

    return score


def _fallback_san_score(move: str) -> float:
    # Always defined; used only if simulation/parsing fails.
    s = 0.0
    if "#" in move:
        s += 1e9
    if "+" in move:
        s += 200
    if "=Q" in move:
        s += 800
    elif "=R" in move:
        s += 450
    elif "=B" in move or "=N" in move:
        s += 300
    if "x" in move:
        s += 120
    if move in ("O-O", "O-O-O"):
        s += 80
    # Prefer central pawn pushes a bit
    if move in ("e4", "d4", "e5", "d5", "c4", "c5"):
        s += 40
    return s


# ----------------------------
# SAN parsing and move application
# ----------------------------

def _apply_san_move(pieces: dict[str, str], color: str, move: str) -> tuple[dict[str, str], MoveMeta]:
    m = move.strip()
    m = SAN_STRIP_RE.sub("", m)

    meta = MoveMeta()

    # Castling
    if m in ("O-O", "O-O-O"):
        newp = dict(pieces)
        meta.is_castle = True
        if color == "w":
            k_from = "e1"
            if m == "O-O":
                k_to, r_from, r_to = "g1", "h1", "f1"
            else:
                k_to, r_from, r_to = "c1", "a1", "d1"
        else:
            k_from = "e8"
            if m == "O-O":
                k_to, r_from, r_to = "g8", "h8", "f8"
            else:
                k_to, r_from, r_to = "c8", "a8", "d8"

        # Move pieces
        if newp.get(k_from) != color + "K":
            raise ValueError("King not on expected square for castling")
        newp.pop(k_from)
        newp[k_to] = color + "K"
        meta.moved_from, meta.moved_to, meta.moved_piece = k_from, k_to, color + "K"

        # Rook move
        rook = newp.get(r_from)
        if rook != color + "R":
            raise ValueError("Rook not on expected square for castling")
        newp.pop(r_from)
        newp[r_to] = color + "R"
        return newp, meta

    # Strip check/mate markers
    suffix = ""
    while m and m[-1] in "+#":
        suffix = m[-1] + suffix
        m = m[:-1]
    # (suffix kept in original move; not needed here)

    # Promotion
    promo = None
    if "=" in m:
        m, promo = m.split("=", 1)
        promo = promo.strip()
        promo = promo[0] if promo else None
        if promo not in ("Q", "R", "B", "N"):
            promo = None
        meta.promotion = promo

    capture = "x" in m

    # Destination is last two chars
    if len(m) < 2:
        raise ValueError("Bad SAN")
    dest = m[-2:]
    if dest[0] not in FILES or dest[1] not in RANKS:
        raise ValueError("No destination square")
    meta.moved_to = dest

    # Determine moving piece type and disambiguation
    first = m[0]
    if first in "KQRBN":
        piece_type = first
        rest = m[1:-2]  # between piece and dest
        disamb = ""
        if capture:
            left, _right = m.split("x", 1)
            disamb = left[1:]  # after piece letter
        else:
            disamb = rest
        disamb = disamb.strip()
        newp, meta = _apply_piece_move(pieces, color, piece_type, disamb, dest, capture, meta)
        # Promotion should never occur for non-pawns; ignore if present
        return newp, meta
    else:
        # Pawn move
        pawn_spec = ""
        if capture:
            left, _right = m.split("x", 1)
            pawn_spec = left  # origin file like 'e' in exd5
        # Non-capture pawn move: pawn_spec empty
        newp, meta = _apply_pawn_move(pieces, color, pawn_spec, dest, capture, promo, meta)
        return newp, meta


def _apply_piece_move(
    pieces: dict[str, str],
    color: str,
    piece_type: str,
    disamb: str,
    dest: str,
    capture: bool,
    meta: MoveMeta,
) -> tuple[dict[str, str], MoveMeta]:
    our_piece = color + piece_type

    # Determine disambiguation filters
    dis_file = None
    dis_rank = None
    if len(disamb) == 1:
        if disamb in FILES:
            dis_file = disamb
        elif disamb in RANKS:
            dis_rank = disamb
    elif len(disamb) >= 2:
        # Could be file+rank
        if disamb[0] in FILES:
            dis_file = disamb[0]
        if disamb[1] in RANKS:
            dis_rank = disamb[1]

    # Capture validity
    dest_piece = pieces.get(dest)
    if capture:
        # Could be capturing something (must be opponent)
        if dest_piece is None:
            # For pieces, no en passant; should not happen in legal SAN
            raise ValueError("Piece capture to empty square")
        if dest_piece[0] == color:
            raise ValueError("Capturing own piece")
    else:
        if dest_piece is not None:
            raise ValueError("Non-capture to occupied square")

    # Find candidate sources
    candidates = []
    for src, pc in pieces.items():
        if pc != our_piece:
            continue
        if dis_file is not None and src[0] != dis_file:
            continue
        if dis_rank is not None and src[1] != dis_rank:
            continue
        if _can_piece_move(piece_type, src, dest, pieces, color):
            candidates.append(src)

    if not candidates:
        raise ValueError("No candidate piece for SAN")

    # If ambiguous, choose the one that keeps our king safe (true legal move)
    chosen = None
    for src in candidates:
        trial = dict(pieces)
        captured = trial.pop(dest, None) if capture else None
        trial.pop(src)
        trial[dest] = our_piece
        if not _king_in_check(color, trial):
            chosen = src
            meta.captured_piece = captured
            break

    if chosen is None:
        # Fallback choose first
        chosen = candidates[0]
        meta.captured_piece = pieces.get(dest) if capture else None

    newp = dict(pieces)
    if capture:
        meta.captured_piece = newp.pop(dest, None)
    newp.pop(chosen)
    newp[dest] = our_piece
    meta.moved_from = chosen
    meta.moved_piece = our_piece
    return newp, meta


def _apply_pawn_move(
    pieces: dict[str, str],
    color: str,
    pawn_spec: str,
    dest: str,
    capture: bool,
    promo: Optional[str],
    meta: MoveMeta,
) -> tuple[dict[str, str], MoveMeta]:
    our_pawn = color + "P"
    dx = 0
    dy = 1 if color == "w" else -1

    dest_piece = pieces.get(dest)
    if not capture and dest_piece is not None:
        raise ValueError("Pawn non-capture to occupied square")
    if capture and dest_piece is not None and dest_piece[0] == color:
        raise ValueError("Pawn capturing own piece")

    tx, ty = _sq_to_xy(dest)

    # Determine source square(s)
    candidates = []

    if capture:
        # pawn_spec must be origin file letter
        if not pawn_spec or pawn_spec[0] not in FILES:
            raise ValueError("Pawn capture missing origin file")
        from_file = pawn_spec[0]
        fx = FILES.index(from_file)
        fy = ty - dy  # one rank behind destination
        if not _in_bounds(fx, fy):
            raise ValueError("Bad pawn capture source")
        src = _xy_to_sq(fx, fy)
        if pieces.get(src) == our_pawn:
            candidates.append(src)
    else:
        # One step forward: src at one behind dest
        fy1 = ty - dy
        if _in_bounds(tx, fy1):
            src1 = _xy_to_sq(tx, fy1)
            if pieces.get(src1) == our_pawn:
                # ensure destination empty already checked
                candidates.append(src1)

        # Two-step from starting rank
        start_rank = "2" if color == "w" else "7"
        if dest[1] == ("4" if color == "w" else "5"):
            fy2 = ty - 2 * dy
            if _in_bounds(tx, fy2):
                src2 = _xy_to_sq(tx, fy2)
                between = _xy_to_sq(tx, ty - dy)
                if src2[1] == start_rank and pieces.get(src2) == our_pawn and between not in pieces and dest not in pieces:
                    candidates.append(src2)

    if not candidates:
        raise ValueError("No pawn source candidates")

    # Pick the only candidate (SAN should be unambiguous for pawns)
    src = candidates[0]

    newp = dict(pieces)

    # Handle capture: normal or en passant
    captured = None
    is_ep = False
    if capture:
        if dest in newp:
            captured = newp.pop(dest)
        else:
            # En passant: destination empty but capture is legal
            is_ep = True
            sx, sy = _sq_to_xy(src)
            # Captured pawn is on same rank as source, file = dest file
            cap_sq = dest[0] + src[1]
            captured = newp.pop(cap_sq, None)
            if captured is None:
                # Still allow; but typically should exist
                raise ValueError("EP capture square empty")
            meta.is_ep = True

    newp.pop(src)
    # Promotion
    placed = our_pawn
    if promo is not None:
        placed = color + promo
    newp[dest] = placed

    meta.moved_from = src
    meta.moved_to = dest
    meta.moved_piece = placed
    meta.captured_piece = captured
    return newp, meta


def _can_piece_move(piece_type: str, src: str, dest: str, pieces: dict[str, str], color: str) -> bool:
    sx, sy = _sq_to_xy(src)
    tx, ty = _sq_to_xy(dest)
    dx = tx - sx
    dy = ty - sy

    if piece_type == "N":
        return (abs(dx), abs(dy)) in ((1, 2), (2, 1))

    if piece_type == "K":
        return max(abs(dx), abs(dy)) == 1

    if piece_type == "B":
        if abs(dx) != abs(dy) or dx == 0:
            return False
        return _clear_ray(src, dest, pieces)

    if piece_type == "R":
        if dx != 0 and dy != 0:
            return False
        if dx == 0 and dy == 0:
            return False
        return _clear_ray(src, dest, pieces)

    if piece_type == "Q":
        if dx == 0 and dy == 0:
            return False
        if dx == 0 or dy == 0 or abs(dx) == abs(dy):
            return _clear_ray(src, dest, pieces)
        return False

    return False


def _clear_ray(src: str, dest: str, pieces: dict[str, str]) -> bool:
    sx, sy = _sq_to_xy(src)
    tx, ty = _sq_to_xy(dest)
    dx = tx - sx
    dy = ty - sy
    step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
    step_y = 0 if dy == 0 else (1 if dy > 0 else -1)

    x, y = sx + step_x, sy + step_y
    while (x, y) != (tx, ty):
        sq = _xy_to_sq(x, y)
        if sq in pieces:
            return False
        x += step_x
        y += step_y
    return True
