
import re
from typing import Dict, List, Tuple, Optional

# -----------------------------
# Core API
# -----------------------------
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    if not legal_moves:
        return ("O-O" if "O-O" in legal_moves else legal_moves[0], memory)

    # Always take mate if available
    for mv in legal_moves:
        if "#" in mv:
            return mv, memory

    us = "w" if to_play == "white" else "b"
    opp = "b" if us == "w" else "w"

    best_move = legal_moves[0]
    best_score = -10**18

    # Precompute king squares (current)
    # (after move we'll recompute cheaply by tracking)
    for mv in legal_moves:
        score = _evaluate_move_san(pieces, us, opp, mv)
        # Deterministic tie-break to avoid oscillation
        if score > best_score or (score == best_score and mv < best_move):
            best_score = score
            best_move = mv

    return best_move, memory


# -----------------------------
# Evaluation
# -----------------------------
PIECE_VALUE = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}

# Simple piece-square tables (white perspective). Small magnitudes; material dominates.
# Indexed by (rank-1)*8 + file where rank=1 is white home rank.
_PST = {
    "P": [
         0,  0,  0,  0,  0,  0,  0,  0,
        10, 10, 10,  0,  0, 10, 10, 10,
         6,  6, 10, 16, 16, 10,  6,  6,
         4,  4,  8, 14, 14,  8,  4,  4,
         2,  2,  4, 10, 10,  4,  2,  2,
         1,  1,  2,  6,  6,  2,  1,  1,
         0,  0,  0, -6, -6,  0,  0,  0,
         0,  0,  0,  0,  0,  0,  0,  0,
    ],
    "N": [
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  6,  8,  8,  6,  0,-10,
        -10,  2,  8, 10, 10,  8,  2,-10,
        -10,  0,  8, 10, 10,  8,  0,-10,
        -10,  2,  6,  8,  8,  6,  2,-10,
        -10,  0,  0,  2,  2,  0,  0,-10,
        -20,-10,-10,-10,-10,-10,-10,-20,
    ],
    "B": [
        -10, -5, -5, -5, -5, -5, -5,-10,
         -5,  2,  2,  2,  2,  2,  2, -5,
         -5,  2,  6,  6,  6,  6,  2, -5,
         -5,  2,  6,  8,  8,  6,  2, -5,
         -5,  2,  6,  8,  8,  6,  2, -5,
         -5,  2,  6,  6,  6,  6,  2, -5,
         -5,  2,  2,  2,  2,  2,  2, -5,
        -10, -5, -5, -5, -5, -5, -5,-10,
    ],
    "R": [
          0,  0,  2,  4,  4,  2,  0,  0,
         -2,  0,  0,  0,  0,  0,  0, -2,
         -2,  0,  0,  0,  0,  0,  0, -2,
         -2,  0,  0,  0,  0,  0,  0, -2,
         -2,  0,  0,  0,  0,  0,  0, -2,
         -2,  0,  0,  0,  0,  0,  0, -2,
          4,  6,  6,  6,  6,  6,  6,  4,
          0,  0,  0,  2,  2,  0,  0,  0,
    ],
    "Q": [
        -10, -5, -5, -2, -2, -5, -5,-10,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  2,  2,  2,  2,  0, -5,
         -2,  0,  2,  4,  4,  2,  0, -2,
         -2,  0,  2,  4,  4,  2,  0, -2,
         -5,  0,  2,  2,  2,  2,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
        -10, -5, -5, -2, -2, -5, -5,-10,
    ],
    "K": [
        -30,-30,-30,-30,-30,-30,-30,-30,
        -30,-30,-30,-30,-30,-30,-30,-30,
        -30,-30,-30,-30,-30,-30,-30,-30,
        -30,-30,-20,-20,-20,-20,-30,-30,
        -20,-20,-10,-10,-10,-10,-20,-20,
        -10,-10,  0,  0,  0,  0,-10,-10,
         10, 20, 20,  0,  0, 20, 20, 10,
         20, 30, 10,  0,  0, 10, 30, 20,
    ],
}

FILE_TO_X = {c: i for i, c in enumerate("abcdefgh")}
X_TO_FILE = "abcdefgh"


def _evaluate_move_san(pieces: Dict[str, str], us: str, opp: str, san: str) -> int:
    # Big bonuses for direct tactical SAN info
    mate_bonus = 1_000_000 if "#" in san else 0
    check_bonus = 80 if ("+" in san and "#" not in san) else 0

    # Try to parse/apply move; fall back to string heuristic if needed.
    applied = _apply_san_move(pieces, us, san)
    if applied is None:
        return mate_bonus + check_bonus + _fallback_san_heuristic(san)

    after, moved_to, moved_piece_type, captured_piece_type, promo_type, castled = applied

    # Material + PST evaluation from our perspective after the move
    base = _evaluate_position(after, us)

    # Capture / promotion bonuses
    cap_bonus = 0
    if captured_piece_type:
        cap_bonus += int(1.25 * PIECE_VALUE[captured_piece_type])
        # Encourage winning exchanges a bit
        cap_bonus += int(0.10 * PIECE_VALUE.get(moved_piece_type, 0))

    promo_bonus = 0
    if promo_type:
        promo_bonus += PIECE_VALUE.get(promo_type, 0) + 200  # promotion is huge

    castle_bonus = 35 if castled else 0

    # Hanging / tactical safety: penalize moving to attacked square if underdefended
    opp_att = _attacks_map(after, opp)
    us_att = _attacks_map(after, us)

    hang_penalty = 0
    if moved_to is not None and moved_piece_type is not None:
        attackers = opp_att.get(moved_to, 0)
        if attackers:
            defenders = us_att.get(moved_to, 0)
            mv_val = PIECE_VALUE.get(moved_piece_type, 0)
            if defenders == 0:
                hang_penalty -= int(0.85 * mv_val)
            else:
                # Under-defended: mild penalty
                if attackers > defenders:
                    hang_penalty -= int(0.35 * mv_val * (attackers - defenders))

    # King safety sanity: if our king is attacked in pseudo terms, heavily penalize
    us_king_sq = _find_king(after, us)
    king_penalty = 0
    if us_king_sq is not None and opp_att.get(us_king_sq, 0) > 0:
        king_penalty -= 20000

    return base + mate_bonus + check_bonus + cap_bonus + promo_bonus + castle_bonus + hang_penalty + king_penalty


def _evaluate_position(pieces: Dict[str, str], us: str) -> int:
    # material + pst for both sides, returned from "us" perspective
    score_white = 0
    score_black = 0

    for sq, pc in pieces.items():
        color = pc[0]
        ptype = pc[1]
        val = PIECE_VALUE.get(ptype, 0)
        pst = _pst_value(ptype, sq, color)
        if color == "w":
            score_white += val + pst
        else:
            score_black += val + pst

    raw = score_white - score_black
    return raw if us == "w" else -raw


def _pst_value(ptype: str, sq: str, color: str) -> int:
    table = _PST.get(ptype)
    if not table:
        return 0
    idx = _sq_index_white_perspective(sq, color)
    return table[idx]


def _sq_index_white_perspective(sq: str, color: str) -> int:
    # index into PST from white perspective; mirror for black.
    x, y = _sq_to_xy(sq)  # y: 0 for rank1 ... 7 for rank8
    if color == "w":
        return y * 8 + x
    # For black, mirror ranks so that "good squares" align.
    my = 7 - y
    return my * 8 + x


def _fallback_san_heuristic(san: str) -> int:
    s = san
    score = 0
    if "#" in s:
        score += 1_000_000
    if "+" in s:
        score += 80
    if "=" in s:
        # prefer queen promotions
        if "=Q" in s:
            score += 1100
        elif "=R" in s:
            score += 700
        elif "=B" in s or "=N" in s:
            score += 600
    if "x" in s:
        score += 120
    if s in ("O-O", "O-O-O", "0-0", "0-0-0"):
        score += 60
    # prefer developing moves slightly (minor pieces)
    if s and s[0] in "NB":
        score += 15
    if s and s[0] in "QR":
        score += 5
    return score


# -----------------------------
# SAN parsing and move application
# -----------------------------
_SAN_STRIP_RE = re.compile(r"[+#?!]+$")

def _apply_san_move(pieces: Dict[str, str], us: str, san: str):
    """
    Attempt to apply a SAN move to a pieces dict.
    Returns:
      (new_pieces, moved_to_sq, moved_piece_type, captured_piece_type, promotion_type, castled_flag)
    or None on failure.
    """
    s = san.strip()
    s = _SAN_STRIP_RE.sub("", s)

    # Normalize castling zeros
    if s in ("0-0", "O-O"):
        return _apply_castle(pieces, us, kingside=True)
    if s in ("0-0-0", "O-O-O"):
        return _apply_castle(pieces, us, kingside=False)

    # Extract promotion (e.g., e8=Q)
    promo_type = None
    if "=" in s:
        base, promo = s.split("=", 1)
        if promo:
            promo_type = promo[0]
        s = base

    # Destination is last two chars (square)
    if len(s) < 2:
        return None
    dest = s[-2:]
    if not _is_square(dest):
        return None

    main = s[:-2]
    capture = "x" in main
    main_no_x = main.replace("x", "")

    # Determine moving piece type and disambiguation / pawn info
    if main_no_x and main_no_x[0] in "KQRBN":
        ptype = main_no_x[0]
        disambig = main_no_x[1:]  # may be '', 'b', '1', 'bd', etc.
        from_sq = _find_from_square_piece(pieces, us, ptype, dest, capture, disambig)
        if from_sq is None:
            return None
        return _apply_move(pieces, us, from_sq, dest, ptype, capture, promo_type, san_castling=False)
    else:
        # Pawn move: main may be '' (e4) or 'ex'?? actually 'exd5' => main_no_x='e'
        ptype = "P"
        from_file = None
        if capture:
            # Expect like 'ex' removed => 'e' remains, so main_no_x[0] should be from file.
            if not main_no_x or main_no_x[0] not in FILE_TO_X:
                return None
            from_file = main_no_x[0]
        from_sq = _find_from_square_pawn(pieces, us, dest, capture, from_file)
        if from_sq is None:
            return None
        return _apply_move(pieces, us, from_sq, dest, ptype, capture, promo_type, san_castling=False)


def _apply_castle(pieces: Dict[str, str], us: str, kingside: bool):
    newp = dict(pieces)
    if us == "w":
        k_from = "e1"
        if kingside:
            k_to, r_from, r_to = "g1", "h1", "f1"
        else:
            k_to, r_from, r_to = "c1", "a1", "d1"
        king_code = "wK"
        rook_code = "wR"
    else:
        k_from = "e8"
        if kingside:
            k_to, r_from, r_to = "g8", "h8", "f8"
        else:
            k_to, r_from, r_to = "c8", "a8", "d8"
        king_code = "bK"
        rook_code = "bR"

    if newp.get(k_from) != king_code:
        return None
    if newp.get(r_from) != rook_code:
        return None

    # Apply
    del newp[k_from]
    del newp[r_from]
    newp[k_to] = king_code
    newp[r_to] = rook_code
    return newp, k_to, "K", None, None, True


def _apply_move(pieces: Dict[str, str], us: str, from_sq: str, to_sq: str, ptype: str,
                capture: bool, promo_type: Optional[str], san_castling: bool):
    newp = dict(pieces)
    mover_code = us + ptype
    if newp.get(from_sq) != mover_code:
        return None

    captured_piece_type = None

    # Capture handling (including en passant)
    if capture:
        if to_sq in newp and newp[to_sq][0] != us:
            captured_piece_type = newp[to_sq][1]
            del newp[to_sq]
        else:
            # Possible en passant: pawn captures to empty square
            if ptype == "P" and to_sq not in newp:
                tx, ty = _sq_to_xy(to_sq)
                # captured pawn is behind the destination
                diry = 1 if us == "w" else -1
                cap_y = ty - diry
                cap_sq = _xy_to_sq(tx, cap_y)
                if cap_sq in newp and newp[cap_sq] == (("b" if us == "w" else "w") + "P"):
                    captured_piece_type = "P"
                    del newp[cap_sq]
                else:
                    return None
            else:
                return None
    else:
        # Non-capture must not land on occupied square (by either color) in normal SAN
        if to_sq in newp:
            return None

    # Move piece
    del newp[from_sq]

    if promo_type:
        # Promotion should be pawn reaching last rank; trust SAN legality but enforce basic sanity
        newp[to_sq] = us + promo_type
        moved_piece_type = promo_type
    else:
        newp[to_sq] = mover_code
        moved_piece_type = ptype

    return newp, to_sq, moved_piece_type, captured_piece_type, promo_type, False


def _find_from_square_piece(pieces: Dict[str, str], us: str, ptype: str, dest: str, capture: bool, disambig: str) -> Optional[str]:
    # disambig can be '', 'b', '1', 'b1'
    dis_file = None
    dis_rank = None
    if len(disambig) == 1:
        if disambig in FILE_TO_X:
            dis_file = disambig
        elif disambig in "12345678":
            dis_rank = disambig
        else:
            return None
    elif len(disambig) == 2:
        a, b = disambig[0], disambig[1]
        if a in FILE_TO_X:
            dis_file = a
        if b in "12345678":
            dis_rank = b
        # Also allow reversed order though uncommon
        if dis_file is None and b in FILE_TO_X and a in "12345678":
            dis_file = b
            dis_rank = a

    candidates = []
    for sq, pc in pieces.items():
        if pc == us + ptype:
            if dis_file and sq[0] != dis_file:
                continue
            if dis_rank and sq[1] != dis_rank:
                continue
            if _can_reach(pieces, us, ptype, sq, dest, capture):
                # Also ensure destination isn't occupied by own piece
                if dest in pieces and pieces[dest][0] == us:
                    continue
                candidates.append(sq)

    if len(candidates) == 1:
        return candidates[0]
    # If ambiguous, pick deterministically (should not happen with legal SAN)
    if candidates:
        candidates.sort()
        return candidates[0]
    return None


def _find_from_square_pawn(pieces: Dict[str, str], us: str, dest: str, capture: bool, from_file: Optional[str]) -> Optional[str]:
    dx, dy = _sq_to_xy(dest)
    diry = 1 if us == "w" else -1
    start_rank = 1 if us == "w" else 6  # y index for rank2 / rank7
    pawn_code = us + "P"

    candidates = []

    if capture:
        if from_file is None:
            return None
        fx = FILE_TO_X[from_file]
        fy = dy - diry
        if not (0 <= fy <= 7):
            return None
        from_sq = _xy_to_sq(fx, fy)
        if pieces.get(from_sq) == pawn_code:
            # Enforce that it is a diagonal capture
            if abs(fx - dx) == 1:
                candidates.append(from_sq)
    else:
        # One-step
        fy = dy - diry
        if 0 <= fy <= 7:
            from_sq = _xy_to_sq(dx, fy)
            if pieces.get(from_sq) == pawn_code and dest not in pieces:
                candidates.append(from_sq)
        # Two-step
        fy2 = dy - 2 * diry
        if 0 <= fy2 <= 7:
            from_sq2 = _xy_to_sq(dx, fy2)
            between_sq = _xy_to_sq(dx, dy - diry)
            if pieces.get(from_sq2) == pawn_code and dest not in pieces and between_sq not in pieces:
                # Must be from starting rank
                _, y2 = _sq_to_xy(from_sq2)
                if y2 == start_rank:
                    candidates.append(from_sq2)

    if len(candidates) == 1:
        return candidates[0]
    if candidates:
        candidates.sort()
        return candidates[0]
    return None


def _can_reach(pieces: Dict[str, str], us: str, ptype: str, src: str, dst: str, capture: bool) -> bool:
    sx, sy = _sq_to_xy(src)
    dx, dy = _sq_to_xy(dst)
    ox = dx - sx
    oy = dy - sy

    if ptype == "N":
        return (abs(ox), abs(oy)) in ((1, 2), (2, 1))
    if ptype == "K":
        return max(abs(ox), abs(oy)) == 1
    if ptype == "B":
        if abs(ox) != abs(oy) or ox == 0:
            return False
        return _ray_clear(pieces, sx, sy, dx, dy)
    if ptype == "R":
        if not (ox == 0 or oy == 0) or (ox == 0 and oy == 0):
            return False
        return _ray_clear(pieces, sx, sy, dx, dy)
    if ptype == "Q":
        if (ox == 0 or oy == 0 or abs(ox) == abs(oy)) and not (ox == 0 and oy == 0):
            return _ray_clear(pieces, sx, sy, dx, dy)
        return False
    if ptype == "P":
        diry = 1 if us == "w" else -1
        # capture: diagonal 1
        if capture:
            return (abs(ox) == 1 and oy == diry)
        # non-capture: forward 1 or 2
        if ox != 0:
            return False
        if oy == diry:
            return dst not in pieces
        if oy == 2 * diry:
            start_y = 1 if us == "w" else 6
            if sy != start_y:
                return False
            mid_sq = _xy_to_sq(sx, sy + diry)
            return (mid_sq not in pieces) and (dst not in pieces)
        return False
    return False


def _ray_clear(pieces: Dict[str, str], sx: int, sy: int, dx: int, dy: int) -> bool:
    step_x = 0 if dx == sx else (1 if dx > sx else -1)
    step_y = 0 if dy == sy else (1 if dy > sy else -1)
    x, y = sx + step_x, sy + step_y
    while (x, y) != (dx, dy):
        sq = _xy_to_sq(x, y)
        if sq in pieces:
            return False
        x += step_x
        y += step_y
    return True


# -----------------------------
# Attack map (pseudo-attacks)
# -----------------------------
_KNIGHT_DELTAS = [(1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)]
_KING_DELTAS = [(1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
_BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
_ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def _attacks_map(pieces: Dict[str, str], color: str) -> Dict[str, int]:
    att: Dict[str, int] = {}
    for sq, pc in pieces.items():
        if pc[0] != color:
            continue
        ptype = pc[1]
        sx, sy = _sq_to_xy(sq)
        if ptype == "P":
            diry = 1 if color == "w" else -1
            for dx in (-1, 1):
                x, y = sx + dx, sy + diry
                if 0 <= x <= 7 and 0 <= y <= 7:
                    tsq = _xy_to_sq(x, y)
                    att[tsq] = att.get(tsq, 0) + 1
        elif ptype == "N":
            for dx, dy in _KNIGHT_DELTAS:
                x, y = sx + dx, sy + dy
                if 0 <= x <= 7 and 0 <= y <= 7:
                    tsq = _xy_to_sq(x, y)
                    att[tsq] = att.get(tsq, 0) + 1
        elif ptype == "K":
            for dx, dy in _KING_DELTAS:
                x, y = sx + dx, sy + dy
                if 0 <= x <= 7 and 0 <= y <= 7:
                    tsq = _xy_to_sq(x, y)
                    att[tsq] = att.get(tsq, 0) + 1
        elif ptype in ("B", "R", "Q"):
            dirs = []
            if ptype in ("B", "Q"):
                dirs += _BISHOP_DIRS
            if ptype in ("R", "Q"):
                dirs += _ROOK_DIRS
            for dx, dy in dirs:
                x, y = sx + dx, sy + dy
                while 0 <= x <= 7 and 0 <= y <= 7:
                    tsq = _xy_to_sq(x, y)
                    att[tsq] = att.get(tsq, 0) + 1
                    if tsq in pieces:  # blocked beyond first piece
                        break
                    x += dx
                    y += dy
    return att


def _find_king(pieces: Dict[str, str], color: str) -> Optional[str]:
    target = color + "K"
    for sq, pc in pieces.items():
        if pc == target:
            return sq
    return None


# -----------------------------
# Square helpers
# -----------------------------
def _is_square(s: str) -> bool:
    return (
        isinstance(s, str)
        and len(s) == 2
        and s[0] in FILE_TO_X
        and s[1] in "12345678"
    )


def _sq_to_xy(sq: str) -> Tuple[int, int]:
    x = FILE_TO_X[sq[0]]
    y = int(sq[1]) - 1
    return x, y


def _xy_to_sq(x: int, y: int) -> str:
    return f"{X_TO_FILE[x]}{y + 1}"
