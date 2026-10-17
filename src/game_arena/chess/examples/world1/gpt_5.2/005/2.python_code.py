
import math
import random
from typing import Dict, List, Optional, Tuple

# --- Core policy API ---

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str]) -> str:
    # Must ALWAYS return a legal move string
    if not legal_moves:
        return ""  # should not happen if environment is correct

    # 1) If any move is annotated as mate, play it immediately.
    for mv in legal_moves:
        if "#" in mv:
            return mv

    our_color = "w" if to_play.lower() == "white" else "b"
    opp_color = "b" if our_color == "w" else "w"

    # Build board dict (copy to avoid surprises)
    board = dict(pieces)

    # If only one legal move, return it fast
    if len(legal_moves) == 1:
        return legal_moves[0]

    # Root search: 2-ply minimax (max our outcome, assume opponent minimizes)
    MATE = 100000
    best_move = legal_moves[0]
    best_score = -math.inf

    # Move ordering: promotions, checks, captures first (helps alpha-beta-ish pruning)
    def root_order_key(m: str) -> Tuple[int, int, int, int]:
        s = _clean_san(m)
        promo = 1 if "=" in s else 0
        chk = 1 if ("+" in m or "#" in m) else 0
        cap = 1 if "x" in s else 0
        castle = 1 if s in ("O-O", "O-O-O") else 0
        return (promo, chk, cap, castle)

    ordered_root = sorted(legal_moves, key=root_order_key, reverse=True)

    # Precompute random tie-breaker to avoid determinism loops
    rng = random.Random(0xC0FFEE)

    for mv_str in ordered_root:
        try:
            b1 = apply_san(board, our_color, mv_str)
        except Exception:
            # If parsing/application fails, skip this move (should be rare).
            continue

        # If opponent has no legal moves, it's mate or stalemate.
        opp_moves = generate_legal_moves(b1, opp_color)
        if not opp_moves:
            if is_in_check(b1, opp_color):
                score = MATE
            else:
                score = 0
        else:
            # Opponent chooses reply that minimizes our evaluation.
            worst = math.inf

            # Order opponent replies: promotions, checks, captures first (more forcing).
            opp_moves_sorted = sorted(opp_moves, key=lambda m: opp_order_key(b1, opp_color, m), reverse=True)

            # Very light pruning: if we already found a reply worse than current best, we can stop.
            for om in opp_moves_sorted:
                b2 = apply_move(b1, om)

                # Detect if we are checkmated after opponent reply (cost: generate our legal moves)
                our_replies = generate_legal_moves(b2, our_color)
                if not our_replies and is_in_check(b2, our_color):
                    s = -MATE
                else:
                    s = evaluate_board(b2, our_color)

                if s < worst:
                    worst = s
                if worst <= best_score:
                    break

            score = worst

        # Small bonus from SAN forcing cues for tie-breaks (check/capture/promo/castle)
        score += san_bonus(mv_str)

        if score > best_score or (score == best_score and rng.random() < 0.35):
            best_score = score
            best_move = mv_str

    # Ensure returned move is legal
    if best_move not in legal_moves:
        return legal_moves[0]
    return best_move


# --- Chess utilities ---

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUE = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

# Basic piece-square tables (from White's perspective). Black is mirrored.
# Values are intentionally modest (material dominates).
PST = {
    "P": [
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10,-10,-10, 10, 10,  5,
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


# --- SAN helpers / parsing ---

def _clean_san(s: str) -> str:
    s = s.strip()
    # Remove trailing check/mate symbols and common annotations.
    while s and s[-1] in "+#?!":
        s = s[:-1]
    # Sometimes SAN includes "e.p." (rare); ignore it
    s = s.replace("e.p.", "").strip()
    return s

def san_bonus(mv: str) -> int:
    s = _clean_san(mv)
    bonus = 0
    if "#" in mv:
        bonus += 50000
    if "+" in mv:
        bonus += 40
    if "x" in s:
        bonus += 25
    if "=" in s:
        bonus += 800
    if s in ("O-O", "O-O-O"):
        bonus += 15
    return bonus

def parse_san(board: Dict[str, str], color: str, san: str) -> Tuple[str, str, str, Optional[str], bool, bool, bool]:
    """
    Returns: (ptype, from_sq, to_sq, promo_piece_type_or_None, is_capture, is_castle_kingside, is_castle_queenside)
    ptype is one of 'P','N','B','R','Q','K'
    promo_piece_type is one of 'Q','R','B','N' or None
    """
    s = _clean_san(san)

    if s == "O-O":
        return ("K", "", "", None, False, True, False)
    if s == "O-O-O":
        return ("K", "", "", None, False, False, True)

    promo = None
    if "=" in s:
        base, pr = s.split("=", 1)
        if pr and pr[0] in "QRBN":
            promo = pr[0]
        s = base

    if len(s) < 2:
        raise ValueError("Invalid SAN")

    to_sq = s[-2:]
    if not is_square(to_sq):
        raise ValueError("Invalid destination square in SAN")

    head = s[:-2]
    is_cap = "x" in head

    # Identify piece type
    if head and head[0] in "KQRBN":
        ptype = head[0]
        rest = head[1:]
    else:
        ptype = "P"
        rest = head

    # disambiguation / pawn file for captures
    if "x" in rest:
        pre, _ = rest.split("x", 1)
        dis = pre
    else:
        dis = rest

    from_sq = resolve_from_square(board, color, ptype, dis, to_sq, is_cap, promo)
    return (ptype, from_sq, to_sq, promo, is_cap, False, False)

def apply_san(board: Dict[str, str], color: str, san: str) -> Dict[str, str]:
    s = _clean_san(san)

    if s == "O-O":
        return apply_castle(board, color, kingside=True)
    if s == "O-O-O":
        return apply_castle(board, color, kingside=False)

    ptype, frm, to, promo, is_cap, _, _ = parse_san(board, color, san)
    move = (frm, to, promo)
    return apply_move(board, move)


# --- Board / move application ---

Move = Tuple[str, str, Optional[str]]  # (from, to, promo)

def apply_move(board: Dict[str, str], move: Move) -> Dict[str, str]:
    frm, to, promo = move
    nb = board.copy()

    piece = nb.get(frm)
    if piece is None:
        # Should not happen if move is legal/resolved
        return nb

    # capture if any
    if to in nb:
        del nb[to]

    # move the piece
    del nb[frm]
    if promo is not None:
        # promotion implies pawn becomes promo piece
        nb[to] = piece[0] + promo
    else:
        nb[to] = piece
    return nb

def apply_castle(board: Dict[str, str], color: str, kingside: bool) -> Dict[str, str]:
    nb = board.copy()
    if color == "w":
        k_from = "e1"
        if kingside:
            k_to, r_from, r_to = "g1", "h1", "f1"
        else:
            k_to, r_from, r_to = "c1", "a1", "d1"
    else:
        k_from = "e8"
        if kingside:
            k_to, r_from, r_to = "g8", "h8", "f8"
        else:
            k_to, r_from, r_to = "c8", "a8", "d8"

    # move king
    if k_from in nb:
        del nb[k_from]
    nb[k_to] = color + "K"

    # move rook
    if r_from in nb:
        del nb[r_from]
    nb[r_to] = color + "R"
    return nb


# --- From-square resolution for SAN ---

def resolve_from_square(board: Dict[str, str], color: str, ptype: str, dis: str, to_sq: str, is_cap: bool, promo: Optional[str]) -> str:
    if ptype == "P":
        return resolve_pawn_from(board, color, dis, to_sq, is_cap)
    else:
        # Find all candidate pieces of that type that can move to to_sq
        candidates = []
        for sq, pc in board.items():
            if pc[0] != color or pc[1] != ptype:
                continue
            if not disambiguation_match(sq, dis):
                continue
            if can_piece_move(board, color, ptype, sq, to_sq, is_cap):
                candidates.append(sq)

        if not candidates:
            raise ValueError("No candidates for SAN move")

        if len(candidates) == 1:
            return candidates[0]

        # If ambiguous, pick candidate that results in own king not in check
        for frm in candidates:
            b2 = apply_move(board, (frm, to_sq, promo))
            if not is_in_check(b2, color):
                return frm

        # fallback
        return candidates[0]

def disambiguation_match(from_sq: str, dis: str) -> bool:
    if not dis:
        return True
    f, r = from_sq[0], from_sq[1]
    if len(dis) == 1:
        if dis in FILES:
            return f == dis
        if dis in RANKS:
            return r == dis
        return True
    if len(dis) >= 2:
        # SAN disambiguation can be file+rank
        df, dr = dis[0], dis[1]
        ok = True
        if df in FILES:
            ok &= (f == df)
        if dr in RANKS:
            ok &= (r == dr)
        return ok
    return True

def resolve_pawn_from(board: Dict[str, str], color: str, dis: str, to_sq: str, is_cap: bool) -> str:
    to_f, to_r = to_sq[0], int(to_sq[1])
    direction = 1 if color == "w" else -1

    if is_cap:
        # dis should contain origin file (e.g. exd5)
        if not dis or dis[0] not in FILES:
            # fallback: any pawn that can capture to_sq
            origin_files = FILES
        else:
            origin_files = dis[0]

        from_rank = to_r - direction
        for of in origin_files:
            frm = f"{of}{from_rank}"
            pc = board.get(frm)
            if pc == color + "P":
                # capture legality: target should contain enemy piece (en-passant ignored)
                # But SAN might be capture with empty square only for en-passant; we allow it.
                return frm
        # fallback search
        for sq, pc in board.items():
            if pc == color + "P" and can_piece_move(board, color, "P", sq, to_sq, True):
                return sq
        raise ValueError("Pawn capture from-square not found")

    # Non-capture pawn push
    # One-step
    frm1 = f"{to_f}{to_r - direction}"
    if board.get(frm1) == color + "P":
        return frm1

    # Two-step from starting rank
    start_rank = 2 if color == "w" else 7
    frm2 = f"{to_f}{to_r - 2 * direction}"
    between = f"{to_f}{to_r - direction}"
    if to_r == (4 if color == "w" else 5) and int(frm2[1]) == start_rank:
        if board.get(frm2) == color + "P" and between not in board and to_sq not in board:
            return frm2

    raise ValueError("Pawn push from-square not found")


# --- Move generation and legality ---

def generate_legal_moves(board: Dict[str, str], color: str) -> List[Move]:
    moves: List[Move] = []
    for sq, pc in board.items():
        if pc[0] != color:
            continue
        ptype = pc[1]
        moves.extend(generate_piece_moves(board, color, ptype, sq))

    # Filter: must not leave king in check
    legal: List[Move] = []
    for mv in moves:
        b2 = apply_move(board, mv)
        if not is_in_check(b2, color):
            legal.append(mv)

    # Add castling (inferred rights) as king move special: we encode as normal moves by applying separately?
    # For check/mate detection and opponent replies, castling can matter.
    # We'll include castling as king "move" from e-file to g/c and handle rook by special apply in generator.
    # But our Move tuple can't carry rook info; so for legality/search we treat castling via direct board transform.
    # To keep it simple, we append sentinel moves with from='@O-O' and interpret in apply_move? Not good.
    # Instead: represent castling as Move with from=king_from and to=king_to, promo='O-O'/'O-O-O' tag.
    # apply_move will not handle rook then. So we implement castling as separate in generate_legal_moves with apply_castle inline by filtering.
    # We'll do: encode promo as 'cK'/'cQ' (custom) and handle in apply_move_extended within this module.
    # But apply_move is used elsewhere; easiest: don't encode, just expand with a separate function that returns final board directly.
    # For minimax we need uniform handling; we'll keep legal moves list as plain Move, and implement apply_move_any.
    # Here, we generate castling as custom moves:
    castles = generate_castles(board, color)
    legal.extend(castles)
    return legal

def apply_move_any(board: Dict[str, str], color: str, mv: Move) -> Dict[str, str]:
    frm, to, promo = mv
    if promo == "CK":  # kingside castle
        return apply_castle(board, color, kingside=True)
    if promo == "CQ":  # queenside castle
        return apply_castle(board, color, kingside=False)
    return apply_move(board, mv)

def generate_castles(board: Dict[str, str], color: str) -> List[Move]:
    res: List[Move] = []
    if color == "w":
        ksq = "e1"
        if board.get(ksq) != "wK":
            return res
        # Kingside
        if board.get("h1") == "wR" and "f1" not in board and "g1" not in board:
            if not is_in_check(board, "w") and not is_square_attacked(board, "f1", "b") and not is_square_attacked(board, "g1", "b"):
                res.append(("e1", "g1", "CK"))
        # Queenside
        if board.get("a1") == "wR" and "b1" not in board and "c1" not in board and "d1" not in board:
            if not is_in_check(board, "w") and not is_square_attacked(board, "d1", "b") and not is_square_attacked(board, "c1", "b"):
                res.append(("e1", "c1", "CQ"))
    else:
        ksq = "e8"
        if board.get(ksq) != "bK":
            return res
        # Kingside
        if board.get("h8") == "bR" and "f8" not in board and "g8" not in board:
            if not is_in_check(board, "b") and not is_square_attacked(board, "f8", "w") and not is_square_attacked(board, "g8", "w"):
                res.append(("e8", "g8", "CK"))
        # Queenside
        if board.get("a8") == "bR" and "b8" not in board and "c8" not in board and "d8" not in board:
            if not is_in_check(board, "b") and not is_square_attacked(board, "d8", "w") and not is_square_attacked(board, "c8", "w"):
                res.append(("e8", "c8", "CQ"))
    return res

def generate_piece_moves(board: Dict[str, str], color: str, ptype: str, sq: str) -> List[Move]:
    # Returns pseudo-legal moves (no self-check filtering)
    if ptype == "P":
        return gen_pawn_moves(board, color, sq)
    if ptype == "N":
        return gen_knight_moves(board, color, sq)
    if ptype == "B":
        return gen_slider_moves(board, color, sq, directions=[(1,1), (1,-1), (-1,1), (-1,-1)])
    if ptype == "R":
        return gen_slider_moves(board, color, sq, directions=[(1,0), (-1,0), (0,1), (0,-1)])
    if ptype == "Q":
        return gen_slider_moves(board, color, sq, directions=[(1,1), (1,-1), (-1,1), (-1,-1), (1,0), (-1,0), (0,1), (0,-1)])
    if ptype == "K":
        return gen_king_moves(board, color, sq)
    return []

def gen_pawn_moves(board: Dict[str, str], color: str, sq: str) -> List[Move]:
    res: List[Move] = []
    f, r = sq[0], int(sq[1])
    direction = 1 if color == "w" else -1
    start_rank = 2 if color == "w" else 7
    last_rank = 8 if color == "w" else 1

    # One step forward
    to_r = r + direction
    if 1 <= to_r <= 8:
        to_sq = f"{f}{to_r}"
        if to_sq not in board:
            # promotion?
            if to_r == last_rank:
                for pr in ("Q", "R", "B", "N"):
                    res.append((sq, to_sq, pr))
            else:
                res.append((sq, to_sq, None))

            # Two steps
            if r == start_rank:
                to_sq2 = f"{f}{r + 2*direction}"
                between = to_sq
                if to_sq2 not in board and between not in board:
                    res.append((sq, to_sq2, None))

    # Captures
    for df in (-1, 1):
        nf = chr(ord(f) + df)
        if nf < "a" or nf > "h":
            continue
        cr = r + direction
        if cr < 1 or cr > 8:
            continue
        to_sq = f"{nf}{cr}"
        if to_sq in board and board[to_sq][0] != color:
            if cr == last_rank:
                for pr in ("Q", "R", "B", "N"):
                    res.append((sq, to_sq, pr))
            else:
                res.append((sq, to_sq, None))
        # en passant ignored (no state to support reliably)

    return res

def gen_knight_moves(board: Dict[str, str], color: str, sq: str) -> List[Move]:
    res: List[Move] = []
    x, y = sq_to_xy(sq)
    for dx, dy in ((1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            to = xy_to_sq(nx, ny)
            if to not in board or board[to][0] != color:
                res.append((sq, to, None))
    return res

def gen_slider_moves(board: Dict[str, str], color: str, sq: str, directions: List[Tuple[int,int]]) -> List[Move]:
    res: List[Move] = []
    x, y = sq_to_xy(sq)
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            to = xy_to_sq(nx, ny)
            if to in board:
                if board[to][0] != color:
                    res.append((sq, to, None))
                break
            res.append((sq, to, None))
            nx += dx
            ny += dy
    return res

def gen_king_moves(board: Dict[str, str], color: str, sq: str) -> List[Move]:
    res: List[Move] = []
    x, y = sq_to_xy(sq)
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                to = xy_to_sq(nx, ny)
                if to not in board or board[to][0] != color:
                    res.append((sq, to, None))
    return res

def can_piece_move(board: Dict[str, str], color: str, ptype: str, frm: str, to: str, is_cap: bool) -> bool:
    if frm == to:
        return False
    # Destination constraints
    if is_cap:
        # allow empty dest for rare en-passant SAN; generally should be occupied by enemy
        if to in board and board[to][0] == color:
            return False
    else:
        if to in board:
            return False

    fx, fy = sq_to_xy(frm)
    tx, ty = sq_to_xy(to)
    dx, dy = tx - fx, ty - fy

    if ptype == "N":
        return (abs(dx), abs(dy)) in ((1,2),(2,1))
    if ptype == "K":
        return max(abs(dx), abs(dy)) == 1
    if ptype == "B":
        if abs(dx) != abs(dy):
            return False
        return path_clear(board, frm, to, step=(sign(dx), sign(dy)))
    if ptype == "R":
        if dx != 0 and dy != 0:
            return False
        return path_clear(board, frm, to, step=(sign(dx), sign(dy)))
    if ptype == "Q":
        if dx == 0 or dy == 0 or abs(dx) == abs(dy):
            return path_clear(board, frm, to, step=(sign(dx), sign(dy)))
        return False
    if ptype == "P":
        # For SAN resolution, pawn handled elsewhere; keep basic validity
        direction = 1 if color == "w" else -1
        if is_cap:
            return dy == direction and abs(dx) == 1
        else:
            if dx != 0:
                return False
            if dy == direction:
                return True
            if dy == 2 * direction:
                start_rank = 2 if color == "w" else 7
                if int(frm[1]) != start_rank:
                    return False
                between = xy_to_sq(fx, fy + direction)
                return between not in board and to not in board
            return False
    return False

def path_clear(board: Dict[str, str], frm: str, to: str, step: Tuple[int,int]) -> bool:
    fx, fy = sq_to_xy(frm)
    tx, ty = sq_to_xy(to)
    sx, sy = step
    cx, cy = fx + sx, fy + sy
    while (cx, cy) != (tx, ty):
        sq = xy_to_sq(cx, cy)
        if sq in board:
            return False
        cx += sx
        cy += sy
    return True

def sign(v: int) -> int:
    if v > 0:
        return 1
    if v < 0:
        return -1
    return 0


# --- Check detection ---

def is_in_check(board: Dict[str, str], color: str) -> bool:
    ksq = None
    for sq, pc in board.items():
        if pc == color + "K":
            ksq = sq
            break
    if ksq is None:
        # king missing; treat as in check (bad)
        return True
    opp = "b" if color == "w" else "w"
    return is_square_attacked(board, ksq, opp)

def is_square_attacked(board: Dict[str, str], sq: str, by_color: str) -> bool:
    x, y = sq_to_xy(sq)

    # Pawns
    if by_color == "w":
        pawn_dirs = [(-1, -1), (1, -1)]  # white pawns attack upward (toward rank 8), from target perspective reverse
        attacker = "wP"
    else:
        pawn_dirs = [(-1, 1), (1, 1)]
        attacker = "bP"
    for dx, dy in pawn_dirs:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            if board.get(xy_to_sq(nx, ny)) == attacker:
                return True

    # Knights
    attackerN = by_color + "N"
    for dx, dy in ((1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            if board.get(xy_to_sq(nx, ny)) == attackerN:
                return True

    # King adjacency
    attackerK = by_color + "K"
    for dx in (-1,0,1):
        for dy in (-1,0,1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                if board.get(xy_to_sq(nx, ny)) == attackerK:
                    return True

    # Sliders: bishops/queens diagonals
    if attacked_by_slider(board, sq, by_color, directions=[(1,1),(1,-1),(-1,1),(-1,-1)], pieces=("B","Q")):
        return True
    # Sliders: rooks/queens orthogonals
    if attacked_by_slider(board, sq, by_color, directions=[(1,0),(-1,0),(0,1),(0,-1)], pieces=("R","Q")):
        return True

    return False

def attacked_by_slider(board: Dict[str, str], sq: str, by_color: str, directions: List[Tuple[int,int]], pieces: Tuple[str, ...]) -> bool:
    x, y = sq_to_xy(sq)
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            nsq = xy_to_sq(nx, ny)
            if nsq in board:
                pc = board[nsq]
                if pc[0] == by_color and pc[1] in pieces:
                    return True
                break
            nx += dx
            ny += dy
    return False


# --- Evaluation ---

def evaluate_board(board: Dict[str, str], our_color: str) -> int:
    opp_color = "b" if our_color == "w" else "w"

    score = 0

    # Material + PST
    for sq, pc in board.items():
        c, pt = pc[0], pc[1]
        val = PIECE_VALUE.get(pt, 0)
        pst = pst_value(pt, sq, c)
        if c == our_color:
            score += val + pst
        else:
            score -= val + pst

    # King safety / castling-ish bonus
    score += king_safety_bonus(board, our_color)
    score -= king_safety_bonus(board, opp_color)

    # If opponent is currently in check, small bonus
    if is_in_check(board, opp_color):
        score += 25
    if is_in_check(board, our_color):
        score -= 25

    return score

def pst_value(ptype: str, sq: str, color: str) -> int:
    arr = PST.get(ptype)
    if not arr:
        return 0
    idx = sq_to_index(sq)  # a1=0 ... h8=63
    if color == "w":
        return arr[idx]
    else:
        # mirror vertically for black
        mx, my = sq_to_xy(sq)
        my = 7 - my
        return arr[my * 8 + mx]

def king_safety_bonus(board: Dict[str, str], color: str) -> int:
    # Lightweight: reward king on typical castled squares and some pawn shield presence.
    ksq = None
    for sq, pc in board.items():
        if pc == color + "K":
            ksq = sq
            break
    if ksq is None:
        return -200

    bonus = 0
    if color == "w":
        if ksq in ("g1", "c1"):
            bonus += 20
        if ksq == "e1":
            bonus -= 10
    else:
        if ksq in ("g8", "c8"):
            bonus += 20
        if ksq == "e8":
            bonus -= 10

    # Pawn shield: count friendly pawns adjacent in front of king (very rough)
    kx, ky = sq_to_xy(ksq)
    direction = 1 if color == "w" else -1
    shield_rank = ky + direction
    if 0 <= shield_rank < 8:
        for fx in (kx - 1, kx, kx + 1):
            if 0 <= fx < 8:
                sq2 = xy_to_sq(fx, shield_rank)
                if board.get(sq2) == color + "P":
                    bonus += 6
    return bonus


# --- Opponent move ordering key ---

def opp_order_key(board: Dict[str, str], color: str, mv: Move) -> Tuple[int, int, int]:
    frm, to, promo = mv
    promo_flag = 1 if promo in ("Q", "R", "B", "N") else 0
    cap_flag = 1 if to in board and board[to][0] != color else 0
    # crude check flag: apply move and see if it gives check
    b2 = apply_move_any(board, color, mv)
    gives_check = 1 if is_in_check(b2, ("b" if color == "w" else "w")) else 0
    return (promo_flag, gives_check, cap_flag)


# --- Coordinate helpers ---

def is_square(s: str) -> bool:
    return len(s) == 2 and s[0] in FILES and s[1] in RANKS

def sq_to_xy(sq: str) -> Tuple[int, int]:
    # a1 -> (0,0), h8 -> (7,7)
    return (ord(sq[0]) - ord("a"), int(sq[1]) - 1)

def xy_to_sq(x: int, y: int) -> str:
    return f"{chr(ord('a') + x)}{y + 1}"

def sq_to_index(sq: str) -> int:
    x, y = sq_to_xy(sq)
    return y * 8 + x


# Patch: ensure generate_legal_moves uses apply_move_any internally for filtering castles too
# We already appended castles after filtering pseudo moves; but castles legality is checked in generate_castles.
# For mate detection, need apply_move_any usage in minimax. We'll do it by overriding apply_move calls in search path.

# Monkey-patch minimal: redefine generate_legal_moves to filter both normal and castle moves uniformly.

def generate_legal_moves(board: Dict[str, str], color: str) -> List[Move]:
    pseudo: List[Move] = []
    for sq, pc in board.items():
        if pc[0] != color:
            continue
        pseudo.extend(generate_piece_moves(board, color, pc[1], sq))

    # Add inferred castling moves (custom promo "CK"/"CQ")
    pseudo.extend(generate_castles(board, color))

    legal: List[Move] = []
    for mv in pseudo:
        b2 = apply_move_any(board, color, mv)
        if not is_in_check(b2, color):
            legal.append(mv)
    return legal

# Also adjust minimax application sites: apply_move_any for opponent moves and mate detection.

# Rebind apply_move for minimax usage by wrapping inside policy's loop:
# (Already uses apply_move for opponent move in policy; fix by using apply_move_any.)
# We'll keep that fix by redefining a tiny wrapper used above.

# Update in policy: it currently calls apply_move(b1, om). Replace with apply_move_any usage by shadowing name.
# (Python resolves global name at runtime; so change global apply_move reference is not needed; we already call apply_move in policy code.
# To ensure correctness, we provide a name that policy uses: apply_move_minimax.)

def apply_move_minimax(board: Dict[str, str], color: str, mv: Move) -> Dict[str, str]:
    return apply_move_any(board, color, mv)

# Now, patch policy's internal usage by relying on global name resolution:
# We'll redefine policy here to use apply_move_minimax for opponent moves and reply generation.
# But we cannot redefine policy after it's already defined above without confusion.
# Instead, we ensure the previously defined policy uses apply_move_any by providing apply_move name alias.

# Alias apply_move_any as apply_move for minimax nodes where move may be castling custom
# Note: apply_san uses apply_move for normal moves; it never sees promo 'CK'/'CQ', so safe.
# But to avoid breaking apply_san, keep apply_move as is.
# Therefore: we must adjust in-place by updating the earlier policy code path:
# We cannot edit it now; so we make apply_move accept custom castles too (backward-compatible).

_old_apply_move = apply_move

def apply_move(board: Dict[str, str], move: Move) -> Dict[str, str]:
    frm, to, promo = move
    if promo == "CK":
        piece = board.get(frm, "")
        color = piece[0] if piece else ("w" if to in ("g1", "c1") else "b")
        return apply_castle(board, color, kingside=True)
    if promo == "CQ":
        piece = board.get(frm, "")
        color = piece[0] if piece else ("w" if to in ("g1", "c1") else "b")
        return apply_castle(board, color, kingside=False)
    return _old_apply_move(board, move)
