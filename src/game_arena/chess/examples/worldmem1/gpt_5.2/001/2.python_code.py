
import re
from typing import Dict, List, Tuple, Optional, Set

PIECE_VALUES = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 0}
CENTER_SQUARES = {"d4", "e4", "d5", "e5", "c4", "f4", "c5", "f5"}


def policy(
    pieces: Dict[str, str],
    to_play: str,
    legal_moves: List[str],
    memory: dict
) -> Tuple[str, dict]:
    if not legal_moves:
        # Should never happen if the environment is correct; but must return something.
        return "", memory

    color = "w" if to_play == "white" else "b"

    # 1) Forced mate
    mates = [m for m in legal_moves if "#" in m]
    if mates:
        # Prefer mates with capture/promotion/check decorations doesn't matter; any mate wins.
        return mates[0], memory

    best_move = legal_moves[0]
    best_score = -10**18

    for mv in legal_moves:
        score = evaluate_move(pieces, color, mv)
        if score > best_score:
            best_score = score
            best_move = mv

    # Always return a legal move string.
    if best_move not in legal_moves:
        best_move = legal_moves[0]
    return best_move, memory


# ----------------- Core evaluation -----------------

def evaluate_move(pieces: Dict[str, str], color: str, move: str) -> int:
    # Big bonus for check (mate handled earlier)
    check_bonus = 35 if "+" in move else 0

    # Parse/apply
    parsed = parse_san(move)
    new_pieces, moved_code, origin, dest, captured_code = apply_move(pieces, color, parsed, move)

    # Material evaluation (delta from mover perspective)
    mat_before = material_score(pieces, color)
    mat_after = material_score(new_pieces, color)
    material_delta = mat_after - mat_before

    # Capture bonus (encourages tactics even if material calc equal due to promotions etc.)
    capture_bonus = 0
    if captured_code:
        capture_bonus += PIECE_VALUES.get(captured_code[1], 0) * 2

    # Promotion bonus
    promo_bonus = 0
    if parsed.get("promotion"):
        promo_bonus += PIECE_VALUES.get(parsed["promotion"], 0) * 2

    # Castling / king safety heuristic
    castle_bonus = 0
    if parsed.get("castle"):
        castle_bonus += 40

    # Centralization bonus
    center_bonus = 10 if dest in CENTER_SQUARES else 0

    # Hanging piece penalty: if moved piece sits on attacked square after move
    opp = "b" if color == "w" else "w"
    opp_attacks = attacked_squares(new_pieces, opp)
    my_attacks = attacked_squares(new_pieces, color)

    hang_penalty = 0
    if dest in opp_attacks:
        moved_value = PIECE_VALUES.get(moved_code[1], 0)
        defended = dest in my_attacks
        if defended:
            hang_penalty -= int(moved_value * 0.35)
        else:
            hang_penalty -= int(moved_value * 0.85)

    # Threat bonus: moved piece attacks enemy pieces
    threat_bonus = 0
    moved_attacks = attacks_from_square(new_pieces, dest, moved_code)
    for sq in moved_attacks:
        pc = new_pieces.get(sq)
        if pc and pc[0] == opp:
            threat_bonus += max(5, PIECE_VALUES.get(pc[1], 0) // 20)

    # Mobility / activity: slight preference for moves that increase our attack footprint
    # (Very small to avoid overriding tactics)
    activity_bonus = 0
    if moved_code[1] in ("N", "B", "R", "Q"):
        activity_bonus += min(20, len(moved_attacks))

    # Prefer captures with check a bit more (common tactical motif)
    cap_check_bonus = 0
    if ("x" in move) and ("+" in move):
        cap_check_bonus += 25

    # Total
    return (
        material_delta * 10
        + capture_bonus
        + promo_bonus
        + check_bonus
        + castle_bonus
        + center_bonus
        + threat_bonus
        + activity_bonus
        + cap_check_bonus
        + hang_penalty
    )


def material_score(pieces: Dict[str, str], perspective: str) -> int:
    # perspective: 'w' or 'b'
    score = 0
    for pc in pieces.values():
        val = PIECE_VALUES.get(pc[1], 0)
        if pc[0] == perspective:
            score += val
        else:
            score -= val
    return score


# ----------------- Move parsing / application -----------------

_SAN_SQ_RE = re.compile(r"([a-h][1-8])")


def parse_san(move: str) -> dict:
    mv = move.strip()

    # Remove trailing check/mate markers for parsing main fields
    suffix = ""
    if mv.endswith(("+", "#")):
        suffix = mv[-1]
        mv = mv[:-1]

    # Castling
    if mv in ("O-O", "O-O-O"):
        return {"castle": mv, "suffix": suffix}

    promotion = None
    if "=" in mv:
        base, promo = mv.split("=", 1)
        promotion = promo  # 'Q','R','B','N' possibly with extra? (should not)
        mv = base

    # Determine destination square: last square-looking token
    sqs = _SAN_SQ_RE.findall(mv)
    dest = sqs[-1] if sqs else None

    capture = "x" in mv

    # Piece type: leading letter if in KQRBN, else pawn
    piece = "P"
    if mv and mv[0] in "KQRBN":
        piece = mv[0]

    # Disambiguation (for pieces): between piece letter and 'x' or dest
    disambig = ""
    if piece != "P":
        start = 1
        end = mv.find("x")
        if end == -1:
            end = mv.rfind(dest) if dest else len(mv)
        disambig = mv[start:end]
        # disambig can be file/rank/both or empty
    else:
        # For pawn capture like exd5, disambig is origin file before 'x'
        if capture:
            disambig = mv[0]  # file
        else:
            disambig = ""  # not needed

    return {
        "piece": piece,
        "dest": dest,
        "capture": capture,
        "disambig": disambig,
        "promotion": promotion,
        "suffix": suffix,
        "castle": None,
    }


def apply_move(
    pieces: Dict[str, str],
    color: str,
    parsed: dict,
    original_move: str
) -> Tuple[Dict[str, str], str, str, str, Optional[str]]:
    # Returns: new_pieces, moved_piece_code, origin, dest, captured_piece_code
    if parsed.get("castle"):
        return apply_castle(pieces, color, parsed["castle"])

    piece_type = parsed["piece"]
    dest = parsed["dest"]
    capture = parsed["capture"]
    disambig = parsed.get("disambig", "")
    promotion = parsed.get("promotion")

    if not dest:
        # Fallback (shouldn't happen): return unchanged but must remain legal externally
        return dict(pieces), f"{color}P", "a1", "a1", None

    origin = find_origin_square(pieces, color, piece_type, dest, capture, disambig)

    moved_code = pieces.get(origin)
    if not moved_code:
        # Should not happen with correct legal SAN; fallback
        moved_code = color + piece_type

    new_pieces = dict(pieces)

    captured_code = None
    # Determine captured square (en passant if needed)
    captured_square = dest if capture else None
    if capture:
        if dest in new_pieces and new_pieces[dest][0] != color:
            captured_square = dest
        else:
            # Possibly en passant: pawn captures to empty destination
            if piece_type == "P":
                of, orank = origin[0], int(origin[1])
                df, drank = dest[0], int(dest[1])
                if abs(ord(df) - ord(of)) == 1 and dest not in new_pieces:
                    # Captured pawn is behind destination on origin rank
                    captured_square = df + str(orank)
            # Otherwise unknown; keep dest

        if captured_square and captured_square in new_pieces:
            captured_code = new_pieces[captured_square]
            del new_pieces[captured_square]

    # Move piece
    if origin in new_pieces:
        del new_pieces[origin]

    # Promotion handling
    placed_code = moved_code
    if piece_type == "P" and promotion:
        placed_code = color + promotion

    new_pieces[dest] = placed_code
    return new_pieces, placed_code, origin, dest, captured_code


def apply_castle(pieces: Dict[str, str], color: str, castle: str):
    new_pieces = dict(pieces)
    if color == "w":
        king_from = "e1"
        if castle == "O-O":
            king_to, rook_from, rook_to = "g1", "h1", "f1"
        else:
            king_to, rook_from, rook_to = "c1", "a1", "d1"
    else:
        king_from = "e8"
        if castle == "O-O":
            king_to, rook_from, rook_to = "g8", "h8", "f8"
        else:
            king_to, rook_from, rook_to = "c8", "a8", "d8"

    # Move king
    moved_king = new_pieces.get(king_from, color + "K")
    if king_from in new_pieces:
        del new_pieces[king_from]
    new_pieces[king_to] = moved_king

    # Move rook
    moved_rook = new_pieces.get(rook_from, color + "R")
    if rook_from in new_pieces:
        del new_pieces[rook_from]
    new_pieces[rook_to] = moved_rook

    return new_pieces, color + "K", king_from, king_to, None


def find_origin_square(
    pieces: Dict[str, str],
    color: str,
    piece_type: str,
    dest: str,
    capture: bool,
    disambig: str
) -> str:
    candidates = []
    for sq, pc in pieces.items():
        if pc[0] != color or pc[1] != piece_type:
            continue
        if disambig:
            # disambig can be file, rank, or both (rare)
            if len(disambig) == 1:
                if disambig in "abcdefgh" and sq[0] != disambig:
                    continue
                if disambig in "12345678" and sq[1] != disambig:
                    continue
            elif len(disambig) == 2:
                if sq[0] != disambig[0] or sq[1] != disambig[1]:
                    continue
        if can_piece_move(pieces, sq, dest, pc, capture):
            candidates.append(sq)

    # With correct legal SAN, should be exactly 1
    if candidates:
        # Prefer the only one; if multiple, choose deterministically
        candidates.sort()
        return candidates[0]

    # Fallback: return any piece of that type
    for sq, pc in pieces.items():
        if pc[0] == color and pc[1] == piece_type:
            return sq
    # Last fallback
    return "a1"


# ----------------- Geometry / movement / attacks -----------------

def sq_to_xy(sq: str) -> Tuple[int, int]:
    return ord(sq[0]) - ord("a"), int(sq[1]) - 1


def xy_to_sq(x: int, y: int) -> str:
    return chr(ord("a") + x) + str(y + 1)


def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def can_piece_move(pieces: Dict[str, str], origin: str, dest: str, pc: str, capture: bool) -> bool:
    # Pseudo-legal movement check (legal_moves already filtered by engine)
    ox, oy = sq_to_xy(origin)
    dx, dy = sq_to_xy(dest)
    vx, vy = dx - ox, dy - oy
    ptype = pc[1]
    color = pc[0]
    target = pieces.get(dest)

    if capture:
        # Must capture opponent or be en-passant-like pawn capture
        if target and target[0] == color:
            return False
    else:
        # Non-capture should land on empty square
        if target is not None:
            return False

    if ptype == "N":
        return (abs(vx), abs(vy)) in {(1, 2), (2, 1)}

    if ptype == "K":
        return max(abs(vx), abs(vy)) == 1

    if ptype == "B":
        if abs(vx) != abs(vy) or vx == 0:
            return False
        return path_clear(pieces, origin, dest)

    if ptype == "R":
        if vx != 0 and vy != 0:
            return False
        if vx == 0 and vy == 0:
            return False
        return path_clear(pieces, origin, dest)

    if ptype == "Q":
        if vx == 0 and vy == 0:
            return False
        if vx == 0 or vy == 0 or abs(vx) == abs(vy):
            return path_clear(pieces, origin, dest)
        return False

    if ptype == "P":
        direction = 1 if color == "w" else -1
        start_rank = 1 if color == "w" else 6  # 0-based: white starts at y=1 (rank2); black at y=6 (rank7)

        if capture:
            # Diagonal capture or en passant
            if vy != direction or abs(vx) != 1:
                return False
            if dest in pieces:
                return pieces[dest][0] != color
            # en passant possibility: destination empty, captured pawn on (dest_file, origin_rank)
            cap_sq = xy_to_sq(dx, oy)
            cap_pc = pieces.get(cap_sq)
            return cap_pc is not None and cap_pc[0] != color and cap_pc[1] == "P"
        else:
            # One step forward
            if vx != 0:
                return False
            if vy == direction:
                return dest not in pieces
            # Two steps from start rank
            if oy == start_rank and vy == 2 * direction:
                mid_sq = xy_to_sq(ox, oy + direction)
                return (mid_sq not in pieces) and (dest not in pieces)
            return False

    return False


def path_clear(pieces: Dict[str, str], origin: str, dest: str) -> bool:
    ox, oy = sq_to_xy(origin)
    dx, dy = sq_to_xy(dest)
    stepx = 0 if dx == ox else (1 if dx > ox else -1)
    stepy = 0 if dy == oy else (1 if dy > oy else -1)
    x, y = ox + stepx, oy + stepy
    while (x, y) != (dx, dy):
        if xy_to_sq(x, y) in pieces:
            return False
        x += stepx
        y += stepy
    return True


def attacked_squares(pieces: Dict[str, str], attacker_color: str) -> Set[str]:
    attacks: Set[str] = set()
    for sq, pc in pieces.items():
        if pc[0] != attacker_color:
            continue
        attacks |= attacks_from_square(pieces, sq, pc)
    return attacks


def attacks_from_square(pieces: Dict[str, str], sq: str, pc: str) -> Set[str]:
    x, y = sq_to_xy(sq)
    color, ptype = pc[0], pc[1]
    res: Set[str] = set()

    if ptype == "P":
        direction = 1 if color == "w" else -1
        for dx in (-1, 1):
            nx, ny = x + dx, y + direction
            if in_bounds(nx, ny):
                res.add(xy_to_sq(nx, ny))
        return res

    if ptype == "N":
        for dx, dy in ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)):
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny):
                res.add(xy_to_sq(nx, ny))
        return res

    if ptype == "K":
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny):
                    res.add(xy_to_sq(nx, ny))
        return res

    # Sliding pieces
    directions = []
    if ptype in ("B", "Q"):
        directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    if ptype in ("R", "Q"):
        directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while in_bounds(nx, ny):
            nsq = xy_to_sq(nx, ny)
            res.add(nsq)
            if nsq in pieces:
                break
            nx += dx
            ny += dy
    return res
