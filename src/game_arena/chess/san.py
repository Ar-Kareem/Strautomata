import re
from typing import Dict, Optional, Tuple, List

FILES = "abcdefgh"
RANKS = "12345678"


def san_to_uci(san: str, pieces: Dict[str, str], side_to_move: str) -> str:
    """
    Convert SAN -> UCI using `pieces` (square -> 'wK', 'bP', etc.) and side-to-move.

    Supports:
      - normal moves, captures, disambiguation
      - promotions (=Q etc.) -> uci suffix 'q','r','b','n'
      - castling O-O / O-O-O -> king move (e1g1, e1c1, e8g8, e8c8)
      - +/# suffix ignored for UCI
      - en passant (heuristic based on board state)

    Also filters candidates by king-safety (critical for resolving SAN like "Nd4" when one
    candidate is pinned and illegal).
    """

    def norm_side(s: str) -> str:
        s = s.strip().lower()
        if s in ("w", "white"):
            return "w"
        if s in ("b", "black"):
            return "b"
        raise ValueError(f"Invalid side_to_move: {side_to_move}")

    stm = norm_side(side_to_move)

    def sq_to_xy(sq: str) -> Tuple[int, int]:
        return (FILES.index(sq[0]), RANKS.index(sq[1]))

    def xy_to_sq(x: int, y: int) -> str:
        return FILES[x] + RANKS[y]

    def in_bounds(x: int, y: int) -> bool:
        return 0 <= x < 8 and 0 <= y < 8

    def piece_at(board: Dict[str, str], sq: str) -> Optional[str]:
        return board.get(sq)

    def is_empty(board: Dict[str, str], sq: str) -> bool:
        return sq not in board

    def color_of(code: str) -> str:
        return code[0]

    def kind_of(code: str) -> str:
        return code[1].upper()

    def opponent(color: str) -> str:
        return "b" if color == "w" else "w"

    def ray_clear(board: Dict[str, str], from_sq: str, to_sq: str, dx: int, dy: int) -> bool:
        fx, fy = sq_to_xy(from_sq)
        tx, ty = sq_to_xy(to_sq)
        x, y = fx + dx, fy + dy
        while (x, y) != (tx, ty):
            if not in_bounds(x, y):
                return False
            if not is_empty(board, xy_to_sq(x, y)):
                return False
            x += dx
            y += dy
        return True

    def is_en_passant_capture(board: Dict[str, str], color: str, from_sq: str, to_sq: str) -> bool:
        """
        Heuristic en passant detection (no explicit ep-square given):
        - pawn goes diagonally 1 step to an empty square
        - the square (to_file, from_rank) contains an opponent pawn
        """
        fx, fy = sq_to_xy(from_sq)
        tx, ty = sq_to_xy(to_sq)
        dx, dy = tx - fx, ty - fy

        direction = 1 if color == "w" else -1
        if dy != direction or abs(dx) != 1:
            return False
        if not is_empty(board, to_sq):
            return False

        passed_sq = xy_to_sq(tx, fy)
        passed_piece = piece_at(board, passed_sq)
        return passed_piece is not None and color_of(passed_piece) != color and kind_of(passed_piece) == "P"

    def can_reach_pseudolegal(board: Dict[str, str], color: str, from_sq: str, to_sq: str,
                             piece_kind: str, capture: bool) -> bool:
        # can't land on own piece
        dst = piece_at(board, to_sq)
        if dst is not None and color_of(dst) == color:
            return False

        # capture rules (pawn en passant allowed)
        if capture:
            if dst is None:
                if not (piece_kind == "P" and is_en_passant_capture(board, color, from_sq, to_sq)):
                    return False
            else:
                if color_of(dst) == color:
                    return False
        else:
            if dst is not None:
                return False

        fx, fy = sq_to_xy(from_sq)
        tx, ty = sq_to_xy(to_sq)
        dx, dy = tx - fx, ty - fy

        if piece_kind == "N":
            return (abs(dx), abs(dy)) in [(1, 2), (2, 1)]

        if piece_kind == "K":
            return max(abs(dx), abs(dy)) == 1

        if piece_kind == "B":
            if abs(dx) != abs(dy) or dx == 0:
                return False
            step_x = 1 if dx > 0 else -1
            step_y = 1 if dy > 0 else -1
            return ray_clear(board, from_sq, to_sq, step_x, step_y)

        if piece_kind == "R":
            if dx != 0 and dy != 0:
                return False
            if dx == 0 and dy == 0:
                return False
            step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            return ray_clear(board, from_sq, to_sq, step_x, step_y)

        if piece_kind == "Q":
            if dx == 0 and dy == 0:
                return False
            if dx == 0 or dy == 0:
                step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
                step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
                return ray_clear(board, from_sq, to_sq, step_x, step_y)
            if abs(dx) == abs(dy):
                step_x = 1 if dx > 0 else -1
                step_y = 1 if dy > 0 else -1
                return ray_clear(board, from_sq, to_sq, step_x, step_y)
            return False

        if piece_kind == "P":
            direction = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6  # y index: rank2=1, rank7=6

            if capture:
                return dy == direction and abs(dx) == 1

            if dx != 0:
                return False
            if dy == direction:
                return True
            if fy == start_rank and dy == 2 * direction:
                mid_sq = xy_to_sq(fx, fy + direction)
                return is_empty(board, mid_sq)
            return False

        return False

    def find_king(board: Dict[str, str], color: str) -> str:
        target = color + "K"
        for sq, code in board.items():
            if code == target:
                return sq
        raise ValueError(f"King not found for color {color}")

    def square_attacked_by(board: Dict[str, str], attacker_color: str, target_sq: str) -> bool:
        """
        True if target_sq is attacked by attacker_color in current board (pseudo-attacks).
        """
        tx, ty = sq_to_xy(target_sq)

        # helper to scan rays for sliders
        def scan_dirs(dirs, kinds):
            for dx, dy in dirs:
                x, y = tx + dx, ty + dy
                while in_bounds(x, y):
                    sq = xy_to_sq(x, y)
                    p = piece_at(board, sq)
                    if p is None:
                        x += dx
                        y += dy
                        continue
                    if color_of(p) == attacker_color and kind_of(p) in kinds:
                        return True
                    break
            return False

        # Knights
        for dx, dy in [(1,2),(2,1),(-1,2),(-2,1),(1,-2),(2,-1),(-1,-2),(-2,-1)]:
            x, y = tx + dx, ty + dy
            if in_bounds(x, y):
                p = piece_at(board, xy_to_sq(x, y))
                if p and color_of(p) == attacker_color and kind_of(p) == "N":
                    return True

        # Pawns (attacks differ by color)
        pawn_dir = 1 if attacker_color == "w" else -1
        for dx in (-1, 1):
            x, y = tx + dx, ty - pawn_dir  # from pawn square to target
            if in_bounds(x, y):
                p = piece_at(board, xy_to_sq(x, y))
                if p and color_of(p) == attacker_color and kind_of(p) == "P":
                    return True

        # King adjacency
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                x, y = tx + dx, ty + dy
                if in_bounds(x, y):
                    p = piece_at(board, xy_to_sq(x, y))
                    if p and color_of(p) == attacker_color and kind_of(p) == "K":
                        return True

        # Sliders
        if scan_dirs([(1,0),(-1,0),(0,1),(0,-1)], {"R","Q"}):
            return True
        if scan_dirs([(1,1),(1,-1),(-1,1),(-1,-1)], {"B","Q"}):
            return True

        return False

    def apply_move(board: Dict[str, str], color: str, from_sq: str, to_sq: str,
                   piece_kind: str, capture: bool, promo: Optional[str]) -> Dict[str, str]:
        """
        Return a new board dict after applying the move. Handles en passant capture + promotion.
        """
        newb = dict(board)
        moving = newb.get(from_sq)
        if moving is None:
            raise ValueError(f"No piece on {from_sq} to move")

        # en passant capture removal
        if piece_kind == "P" and capture and is_empty(newb, to_sq) and is_en_passant_capture(newb, color, from_sq, to_sq):
            fx, fy = sq_to_xy(from_sq)
            tx, _ = sq_to_xy(to_sq)
            passed_sq = xy_to_sq(tx, fy)
            newb.pop(passed_sq, None)

        # normal capture overwrite
        newb.pop(to_sq, None)

        # move piece
        newb.pop(from_sq)
        if promo:
            # promo given as 'Q','R','B','N' (SAN)
            newb[to_sq] = color + promo.upper()
        else:
            newb[to_sq] = moving

        return newb

    def is_legal_candidate(color: str, from_sq: str, to_sq: str, piece_kind: str,
                           capture: bool, promo: Optional[str]) -> bool:
        # simulate, then ensure own king not in check
        newb = apply_move(pieces, color, from_sq, to_sq, piece_kind, capture, promo)
        ksq = find_king(newb, color)
        return not square_attacked_by(newb, opponent(color), ksq)

    def parse_san_text(s: str) -> Dict[str, object]:
        s = s.strip()

        # strip check/mate for UCI
        if s.endswith("#") or s.endswith("+"):
            s = s[:-1]

        if s in ("O-O", "0-0"):
            return {"castle": "K", "piece": "K", "to": None, "capture": False,
                    "promotion": None, "dis_file": None, "dis_rank": None}
        if s in ("O-O-O", "0-0-0"):
            return {"castle": "Q", "piece": "K", "to": None, "capture": False,
                    "promotion": None, "dis_file": None, "dis_rank": None}

        promo = None
        m = re.search(r"=([QRBN])$", s)
        if m:
            promo = m.group(1)
            s = s[:m.start()]

        capture = "x" in s

        m = re.search(r"([a-h][1-8])$", s)
        if not m:
            raise ValueError(f"Bad SAN (no destination square): {san}")
        to_sq = m.group(1)
        head = s[:m.start()]

        piece = "P"
        if head and head[0] in "KQRBN":
            piece = head[0]
            head = head[1:]

        head = head.replace("x", "")

        dis_file = dis_rank = None
        if piece == "P":
            if capture:
                if len(head) != 1 or head not in FILES:
                    raise ValueError(f"Bad pawn capture SAN: {san}")
                dis_file = head
            else:
                if head != "":
                    raise ValueError(f"Bad pawn move SAN: {san}")
        else:
            if len(head) == 1:
                if head in FILES:
                    dis_file = head
                elif head in RANKS:
                    dis_rank = head
                elif head != "":
                    raise ValueError(f"Bad disambiguation: {san}")
            elif len(head) == 2:
                if head[0] in FILES and head[1] in RANKS:
                    dis_file, dis_rank = head[0], head[1]
                else:
                    raise ValueError(f"Bad disambiguation: {san}")
            elif head != "":
                raise ValueError(f"Bad SAN head: {san}")

        return {
            "castle": None,
            "piece": piece,
            "to": to_sq,
            "capture": capture,
            "promotion": promo,
            "dis_file": dis_file,
            "dis_rank": dis_rank,
        }

    def resolve(color: str, parsed: Dict[str, object]) -> Tuple[str, str, Optional[str]]:
        # castling -> king move
        if parsed["castle"] == "K":
            return ("e1", "g1", None) if color == "w" else ("e8", "g8", None)
        if parsed["castle"] == "Q":
            return ("e1", "c1", None) if color == "w" else ("e8", "c8", None)

        to_sq = parsed["to"]
        piece_kind = parsed["piece"]
        capture = parsed["capture"]
        dis_file = parsed["dis_file"]
        dis_rank = parsed["dis_rank"]
        promo = parsed["promotion"]

        candidates: List[str] = []
        for sq, code in pieces.items():
            if color_of(code) != color:
                continue
            if kind_of(code) != piece_kind:
                continue
            if dis_file and sq[0] != dis_file:
                continue
            if dis_rank and sq[1] != dis_rank:
                continue
            if not can_reach_pseudolegal(pieces, color, sq, to_sq, piece_kind, capture):
                continue
            # KING-SAFETY FILTER (this is what fixes "Nd4")
            if not is_legal_candidate(color, sq, to_sq, piece_kind, capture, promo):
                continue
            candidates.append(sq)

        if len(candidates) != 1:
            raise ValueError(f'Could not resolve SAN in this position for {color}: {san} (candidates={candidates})')

        from_sq = candidates[0]
        promo_uci = promo.lower() if promo else None
        return from_sq, to_sq, promo_uci

    parsed = parse_san_text(san)
    from_sq, to_sq, promo = resolve(stm, parsed)
    return from_sq + to_sq + (promo or "")
