
# chess_policy.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math
import random


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

# Light piece-square encouragement (from White's perspective; mirrored for Black).
# Values are intentionally small to avoid overpowering tactics.
PST_N = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   5,   5,   5,   5,   0, -10,
    -10,   5,  10,  12,  12,  10,   5, -10,
    -10,   5,  12,  15,  15,  12,   5, -10,
    -10,   5,  12,  15,  15,  12,   5, -10,
    -10,   5,  10,  12,  12,  10,   5, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20,
]
PST_B = [
    -10, -10, -10, -10, -10, -10, -10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   0,  10,  12,  12,  10,   0, -10,
    -10,   0,  10,  12,  12,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -10, -10, -10, -10, -10, -10, -10, -10,
]
PST_P = [
      0,   0,   0,   0,   0,   0,   0,   0,
      5,  10,  10, -10, -10,  10,  10,   5,
      5,  -5, -10,   0,   0, -10,  -5,   5,
      0,   0,   0,  20,  20,   0,   0,   0,
      5,   5,  10,  25,  25,  10,   5,   5,
     10,  10,  20,  30,  30,  20,  10,  10,
     50,  50,  50,  50,  50,  50,  50,  50,
      0,   0,   0,   0,   0,   0,   0,   0,
]
PST_R = [
      0,   0,   5,  10,  10,   5,   0,   0,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
     -5,   0,   0,   0,   0,   0,   0,  -5,
      5,  10,  10,  10,  10,  10,  10,   5,
      0,   0,   0,   0,   0,   0,   0,   0,
]
PST_Q = [
    -10, -10, -10,  -5,  -5, -10, -10, -10,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
     -5,   0,   5,   5,   5,   5,   0,  -5,
      0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -10, -10, -10,  -5,  -5, -10, -10, -10,
]
PST_K_MID = [
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
     20,  20,   0,   0,   0,   0,  20,  20,
     30,  40,  10,   0,   0,  10,  40,  30,
]

PST_BY_PIECE = {
    "P": PST_P,
    "N": PST_N,
    "B": PST_B,
    "R": PST_R,
    "Q": PST_Q,
    "K": PST_K_MID,
}


def _sq_to_xy(sq: str) -> Tuple[int, int]:
    return FILES.index(sq[0]), RANKS.index(sq[1])


def _xy_to_sq(x: int, y: int) -> str:
    return f"{FILES[x]}{RANKS[y]}"


def _in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def _other(color: str) -> str:
    return "b" if color == "w" else "w"


def _to_colorchar(to_play: str) -> str:
    return "w" if to_play == "white" else "b"


@dataclass(frozen=True)
class ParsedMove:
    raw: str
    is_castle: bool = False
    castle_side: Optional[str] = None  # "K" or "Q"
    piece: str = "P"  # "P" for pawn, else KQRBN
    capture: bool = False
    to_sq: Optional[str] = None
    disambig_file: Optional[str] = None
    disambig_rank: Optional[str] = None
    pawn_from_file: Optional[str] = None
    promotion: Optional[str] = None  # "Q","R","B","N"
    gives_check_symbol: bool = False
    gives_mate_symbol: bool = False


def _parse_san_like(move: str) -> ParsedMove:
    raw = move
    m = move.strip()
    if not m:
        raise ValueError("empty move")

    # Normalize castling zeros
    m = m.replace("0-0-0", "O-O-O").replace("0-0", "O-O")

    gives_mate = m.endswith("#")
    gives_check = m.endswith("+") or gives_mate
    while m and m[-1] in "+#":
        m = m[:-1]

    # Ignore rare annotations like "!" "?" if present
    while m and m[-1] in "!?":
        m = m[:-1]

    if m in ("O-O", "O-O-O"):
        return ParsedMove(
            raw=raw,
            is_castle=True,
            castle_side="K" if m == "O-O" else "Q",
            piece="K",
            gives_check_symbol=gives_check,
            gives_mate_symbol=gives_mate,
        )

    promotion = None
    base = m
    if "=" in base:
        base, promo = base.split("=", 1)
        promotion = promo[:1] if promo else None

    if len(base) < 2:
        raise ValueError(f"cannot parse move: {move}")

    to_sq = base[-2:]
    if to_sq[0] not in FILES or to_sq[1] not in RANKS:
        raise ValueError(f"bad destination in move: {move}")

    prefix = base[:-2]
    capture = "x" in prefix

    piece = "P"
    dis_file = None
    dis_rank = None
    pawn_from_file = None

    if prefix and prefix[0] in "KQRBN":
        piece = prefix[0]
        rest = prefix[1:]
        rest = rest.replace("x", "")
        # rest can be "", "e", "1", "e1"
        for ch in rest:
            if ch in FILES:
                dis_file = ch
            elif ch in RANKS:
                dis_rank = ch
    else:
        piece = "P"
        if capture:
            # "exd5" => prefix like "ex" or "exd"?? actually "ex" then dest
            pawn_from_file = prefix[0] if prefix and prefix[0] in FILES else None
        else:
            pawn_from_file = None

    return ParsedMove(
        raw=raw,
        is_castle=False,
        piece=piece,
        capture=capture,
        to_sq=to_sq,
        disambig_file=dis_file,
        disambig_rank=dis_rank,
        pawn_from_file=pawn_from_file,
        promotion=promotion,
        gives_check_symbol=gives_check,
        gives_mate_symbol=gives_mate,
    )


def _path_clear(board: Dict[str, str], frm: str, to: str, dx: int, dy: int) -> bool:
    fx, fy = _sq_to_xy(frm)
    tx, ty = _sq_to_xy(to)
    x, y = fx + dx, fy + dy
    while (x, y) != (tx, ty):
        sq = _xy_to_sq(x, y)
        if sq in board:
            return False
        x += dx
        y += dy
    return True


def _can_piece_reach(board: Dict[str, str], piece: str, frm: str, to: str, color: str, capture: bool) -> bool:
    if frm == to:
        return False
    fx, fy = _sq_to_xy(frm)
    tx, ty = _sq_to_xy(to)
    dx = tx - fx
    dy = ty - fy

    target = board.get(to)
    if capture:
        # captures can also be en-passant for pawns; handled separately.
        if target is not None and target[0] == color:
            return False
    else:
        if target is not None:
            return False

    adx, ady = abs(dx), abs(dy)

    if piece == "N":
        return (adx, ady) in ((1, 2), (2, 1))
    if piece == "K":
        return max(adx, ady) == 1
    if piece == "B":
        if adx != ady or adx == 0:
            return False
        step_x = 1 if dx > 0 else -1
        step_y = 1 if dy > 0 else -1
        return _path_clear(board, frm, to, step_x, step_y)
    if piece == "R":
        if dx != 0 and dy != 0:
            return False
        if dx == 0 and dy == 0:
            return False
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        return _path_clear(board, frm, to, step_x, step_y)
    if piece == "Q":
        if dx == 0 and dy == 0:
            return False
        if dx == 0 or dy == 0:
            step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            return _path_clear(board, frm, to, step_x, step_y)
        if adx == ady:
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            return _path_clear(board, frm, to, step_x, step_y)
        return False
    return False


def _attacks_from_square(board: Dict[str, str], sq: str) -> List[str]:
    """Pseudo-attacks for the piece on sq (ignores pins/check legality)."""
    p = board.get(sq)
    if not p:
        return []
    color = p[0]
    pt = p[1]
    x, y = _sq_to_xy(sq)
    out: List[str] = []

    if pt == "P":
        dy = 1 if color == "w" else -1
        for dx in (-1, 1):
            nx, ny = x + dx, y + dy
            if _in_bounds(nx, ny):
                out.append(_xy_to_sq(nx, ny))
        return out

    if pt == "N":
        for dx, dy in ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)):
            nx, ny = x + dx, y + dy
            if _in_bounds(nx, ny):
                out.append(_xy_to_sq(nx, ny))
        return out

    if pt == "K":
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if _in_bounds(nx, ny):
                    out.append(_xy_to_sq(nx, ny))
        return out

    # Sliding pieces
    directions = []
    if pt in ("B", "Q"):
        directions += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    if pt in ("R", "Q"):
        directions += [(1, 0), (-1, 0), (0, 1), (0, -1)]

    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while _in_bounds(nx, ny):
            nsq = _xy_to_sq(nx, ny)
            out.append(nsq)
            if nsq in board:
                break
            nx += dx
            ny += dy
    return out


def _is_square_attacked(board: Dict[str, str], sq: str, by_color: str) -> bool:
    for s, pc in board.items():
        if pc[0] != by_color:
            continue
        if sq in _attacks_from_square(board, s):
            # For pawns, attacks are correct; for sliders, includes squares until blocked.
            # Since _attacks_from_square stops at first occupied square, this is fine.
            return True
    return False


def _find_king_square(board: Dict[str, str], color: str) -> Optional[str]:
    target = color + "K"
    for s, pc in board.items():
        if pc == target:
            return s
    return None


def _in_check(board: Dict[str, str], color: str) -> bool:
    ksq = _find_king_square(board, color)
    if not ksq:
        return False
    return _is_square_attacked(board, ksq, _other(color))


def _count_attackers(board: Dict[str, str], sq: str, by_color: str) -> int:
    c = 0
    for s, pc in board.items():
        if pc[0] != by_color:
            continue
        if sq in _attacks_from_square(board, s):
            c += 1
    return c


def _apply_castle(board: Dict[str, str], color: str, side: str) -> Dict[str, str]:
    b = dict(board)
    if color == "w":
        k_from, r_from = "e1", ("h1" if side == "K" else "a1")
        k_to, r_to = ("g1", "f1") if side == "K" else ("c1", "d1")
    else:
        k_from, r_from = "e8", ("h8" if side == "K" else "a8")
        k_to, r_to = ("g8", "f8") if side == "K" else ("c8", "d8")

    # Move king
    if k_from in b:
        b.pop(k_from)
    b[k_to] = color + "K"
    # Move rook
    if r_from in b:
        b.pop(r_from)
    b[r_to] = color + "R"
    return b


def _apply_move(board: Dict[str, str], color: str, pm: ParsedMove) -> Tuple[Dict[str, str], Optional[str], Optional[str], Optional[str]]:
    """
    Returns: (new_board, from_sq, to_sq, moved_piece_type_letter)
    """
    if pm.is_castle:
        nb = _apply_castle(board, color, pm.castle_side or "K")
        return nb, ("e1" if color == "w" else "e8"), (("g1" if color == "w" else "g8") if pm.castle_side == "K" else ("c1" if color == "w" else "c8")), "K"

    to_sq = pm.to_sq
    assert to_sq is not None

    b = dict(board)

    # Determine origin square(s)
    from_candidates: List[str] = []

    if pm.piece == "P":
        tx, ty = _sq_to_xy(to_sq)
        direction = 1 if color == "w" else -1
        start_rank = 1 if color == "w" else 6  # 0-indexed: rank2 -> y=1, rank7 -> y=6

        if pm.capture:
            # Pawn capture: from_file given, from_rank = to_rank - direction
            if not pm.pawn_from_file:
                # fallback: infer from any pawn that can capture there
                for dx in (-1, 1):
                    fx = tx - dx
                    fy = ty - direction
                    if _in_bounds(fx, fy):
                        frm = _xy_to_sq(fx, fy)
                        if b.get(frm) == color + "P":
                            from_candidates.append(frm)
            else:
                fx = FILES.index(pm.pawn_from_file)
                fy = ty - direction
                if _in_bounds(fx, fy):
                    frm = _xy_to_sq(fx, fy)
                    if b.get(frm) == color + "P":
                        from_candidates.append(frm)
        else:
            # Pawn push: one step or two steps from start
            fy1 = ty - direction
            if _in_bounds(tx, fy1):
                frm1 = _xy_to_sq(tx, fy1)
                if b.get(frm1) == color + "P" and to_sq not in b:
                    from_candidates.append(frm1)
            # two-step
            fy2 = ty - 2 * direction
            if _in_bounds(tx, fy2):
                frm2 = _xy_to_sq(tx, fy2)
                between = _xy_to_sq(tx, ty - direction)
                if (b.get(frm2) == color + "P"
                        and _sq_to_xy(frm2)[1] == start_rank
                        and to_sq not in b
                        and between not in b):
                    from_candidates.append(frm2)
    else:
        # Piece move
        wanted = color + pm.piece
        for frm, pc in b.items():
            if pc != wanted:
                continue
            if pm.disambig_file and frm[0] != pm.disambig_file:
                continue
            if pm.disambig_rank and frm[1] != pm.disambig_rank:
                continue
            if _can_piece_reach(b, pm.piece, frm, to_sq, color, pm.capture):
                from_candidates.append(frm)

    if not from_candidates:
        raise ValueError(f"could not find origin for move {pm.raw}")

    # Try candidates; ensure king not left in check (resolves pin ambiguities)
    def try_apply_from(frm: str) -> Optional[Dict[str, str]]:
        bb = dict(b)
        moving = bb.get(frm)
        if not moving:
            return None
        moved_pt = moving[1]

        # Remove captured piece (normal capture)
        if pm.capture:
            if to_sq in bb and bb[to_sq][0] != color:
                bb.pop(to_sq)
            else:
                # possible en-passant-like capture: destination empty but capture indicated
                if moved_pt == "P" and frm[0] != to_sq[0] and to_sq not in bb:
                    fx, fy = _sq_to_xy(frm)
                    tx, ty = _sq_to_xy(to_sq)
                    # Captured pawn is on the square behind destination (same rank as from)
                    cap_sq = _xy_to_sq(tx, fy)
                    if cap_sq in bb and bb[cap_sq] == _other(color) + "P":
                        bb.pop(cap_sq)

        # Move piece
        bb.pop(frm, None)

        # Promotion
        if moved_pt == "P" and pm.promotion:
            bb[to_sq] = color + pm.promotion
        else:
            bb[to_sq] = moving

        # Must not leave own king in check
        if _in_check(bb, color):
            return None
        return bb

    chosen_board = None
    chosen_from = None
    for frm in from_candidates:
        nb = try_apply_from(frm)
        if nb is not None:
            chosen_board = nb
            chosen_from = frm
            break

    if chosen_board is None:
        # As a last resort, apply first candidate without legality check (should be rare).
        chosen_from = from_candidates[0]
        chosen_board = try_apply_from(chosen_from) or dict(b)

    moved_piece_type = pm.piece if pm.piece != "P" else "P"
    return chosen_board, chosen_from, to_sq, moved_piece_type


def _pst_value(piece_type: str, sq: str, color: str) -> int:
    table = PST_BY_PIECE.get(piece_type)
    if not table:
        return 0
    x, y = _sq_to_xy(sq)
    idx_white = y * 8 + x
    if color == "w":
        return table[idx_white]
    # mirror vertically for black
    idx_black = (7 - y) * 8 + x
    return table[idx_black]


def _eval_board(board: Dict[str, str], me: str) -> int:
    """Positive means good for 'me' (color char 'w'/'b')."""
    them = _other(me)
    score = 0

    # Material + PST
    for sq, pc in board.items():
        c, pt = pc[0], pc[1]
        v = PIECE_VALUES.get(pt, 0)
        ps = _pst_value(pt, sq, c)
        if c == me:
            score += v + ps
        else:
            score -= v + ps

    # King safety / castling encouragement
    my_king = _find_king_square(board, me)
    op_king = _find_king_square(board, them)

    def king_safety_bonus(ksq: Optional[str], color: str) -> int:
        if not ksq:
            return 0
        # Encourage castled squares
        bonus = 0
        if color == "w":
            if ksq in ("g1", "c1"):
                bonus += 35
            elif ksq in ("e1", "d1", "f1"):
                bonus -= 10
        else:
            if ksq in ("g8", "c8"):
                bonus += 35
            elif ksq in ("e8", "d8", "f8"):
                bonus -= 10
        return bonus

    score += king_safety_bonus(my_king, me)
    score -= king_safety_bonus(op_king, them)

    # Small bonus for giving check (computed, not SAN symbol)
    if op_king and _is_square_attacked(board, op_king, me):
        score += 45

    return score


def _move_heuristic_bonus(pm: ParsedMove) -> int:
    # Move-string based small priors
    if pm.gives_mate_symbol:
        return 10_000_000
    b = 0
    if pm.gives_check_symbol:
        b += 60
    if pm.is_castle:
        b += 40
    if pm.promotion:
        b += 800  # encourages promotion (material gain largely handled elsewhere too)
    if pm.capture:
        b += 15
    # Encourage central pawn pushes in opening-ish positions
    if pm.piece == "P" and pm.to_sq:
        if pm.to_sq in ("e4", "d4", "c4", "f4", "e5", "d5", "c5", "f5"):
            b += 12
    return b


def _blunder_penalty(board_after: Dict[str, str], me: str, moved_to: Optional[str], moved_piece_type: Optional[str]) -> int:
    if not moved_to or not moved_piece_type:
        return 0
    them = _other(me)
    # If destination is attacked by opponent, penalize; if defended too, reduce penalty.
    attackers = _count_attackers(board_after, moved_to, them)
    if attackers <= 0:
        return 0
    defenders = _count_attackers(board_after, moved_to, me)
    val = PIECE_VALUES.get(moved_piece_type, 0)

    # Penalize being en prise; scale by imbalance attackers/defenders.
    # If defended, still some risk, but smaller.
    if defenders <= 0:
        return int(0.75 * val) + 20
    if attackers > defenders:
        return int(0.35 * val) + 10
    return int(0.12 * val)


def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    me = _to_colorchar(to_play)

    # Safety: must always return a legal move string.
    if not legal_moves:
        # Should not happen; but avoid crash.
        return ("O-O" if "O-O" in legal_moves else legal_moves[0]), memory

    # Immediate mate by SAN symbol
    for mv in legal_moves:
        if mv.strip().endswith("#"):
            return mv, memory

    # Evaluate all moves by simulating and scoring.
    best_score = -10**18
    best_moves: List[str] = []

    # Small deterministic shuffle to avoid pathological ties, but keep reproducible per position.
    # Use a hash of pieces to seed.
    try:
        seed = 0
        for k, v in pieces.items():
            seed ^= (hash(k) * 1315423911) ^ (hash(v) * 2654435761)
        seed ^= hash(to_play)
        rng = random.Random(seed)
        moves_iter = list(legal_moves)
        rng.shuffle(moves_iter)
    except Exception:
        moves_iter = list(legal_moves)

    for mv in moves_iter:
        try:
            pm = _parse_san_like(mv)
            after, frm, to_sq, moved_pt = _apply_move(pieces, me, pm)
            score = _eval_board(after, me)
            score += _move_heuristic_bonus(pm)
            score -= _blunder_penalty(after, me, to_sq, moved_pt)

            # Extra nudge: prefer captures of higher-value pieces if detectable directly from current board.
            # (This is redundant with material eval but helps when parsing/ambiguity fails.)
            if pm.capture and to_sq and to_sq in pieces and pieces[to_sq][0] != me:
                score += PIECE_VALUES.get(pieces[to_sq][1], 0) // 12

        except Exception:
            # If parsing/simulation fails, fall back to a mild heuristic:
            pm = None
            score = 0
            if mv.endswith("#"):
                score = 10_000_000
            elif mv.endswith("+"):
                score = 80
            if "x" in mv:
                score += 20
            if "=Q" in mv:
                score += 900
            elif "=" in mv:
                score += 600
            if mv in ("O-O", "O-O-O"):
                score += 35

        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    # Tie-break: prefer checks, then captures, then promotions, then castles.
    def tie_key(mv: str) -> Tuple[int, int, int, int, int]:
        # Higher is better
        return (
            1 if mv.endswith("#") else 0,
            1 if mv.endswith("+") else 0,
            1 if "x" in mv else 0,
            1 if "=" in mv else 0,
            1 if mv in ("O-O", "O-O-O") else 0,
        )

    if len(best_moves) > 1:
        best_moves.sort(key=tie_key, reverse=True)

    chosen = best_moves[0] if best_moves else legal_moves[0]
    if chosen not in legal_moves:
        chosen = legal_moves[0]

    # Optional memory (not required, but can be useful for debugging/analysis)
    memory = memory or {}
    memory["last_move"] = chosen
    return chosen, memory
