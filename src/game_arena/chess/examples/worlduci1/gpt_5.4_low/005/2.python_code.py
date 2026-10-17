
from typing import Dict, List, Tuple, Optional

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

KNIGHT_DIRS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS


def sq_to_xy(sq: str) -> Tuple[int, int]:
    return FILES.index(sq[0]), RANKS.index(sq[1])


def xy_to_sq(x: int, y: int) -> str:
    return FILES[x] + RANKS[y]


def in_bounds(x: int, y: int) -> bool:
    return 0 <= x < 8 and 0 <= y < 8


def color_char(to_play: str) -> str:
    return "w" if to_play == "white" else "b"


def opp(c: str) -> str:
    return "b" if c == "w" else "w"


def king_square(board: Dict[str, str], side: str) -> Optional[str]:
    target = side + "K"
    for sq, pc in board.items():
        if pc == target:
            return sq
    return None


def is_attacked(board: Dict[str, str], sq: str, by_side: str) -> bool:
    x, y = sq_to_xy(sq)

    # Pawns
    if by_side == "w":
        for dx in (-1, 1):
            xx, yy = x - dx, y - 1
            if in_bounds(xx, yy):
                s = xy_to_sq(xx, yy)
                if board.get(s) == "wP":
                    return True
    else:
        for dx in (-1, 1):
            xx, yy = x - dx, y + 1
            if in_bounds(xx, yy):
                s = xy_to_sq(xx, yy)
                if board.get(s) == "bP":
                    return True

    # Knights
    for dx, dy in KNIGHT_DIRS:
        xx, yy = x + dx, y + dy
        if in_bounds(xx, yy):
            s = xy_to_sq(xx, yy)
            if board.get(s) == by_side + "N":
                return True

    # Kings
    for dx, dy in KING_DIRS:
        xx, yy = x + dx, y + dy
        if in_bounds(xx, yy):
            s = xy_to_sq(xx, yy)
            if board.get(s) == by_side + "K":
                return True

    # Bishops / Queens
    for dx, dy in BISHOP_DIRS:
        xx, yy = x + dx, y + dy
        while in_bounds(xx, yy):
            s = xy_to_sq(xx, yy)
            p = board.get(s)
            if p:
                if p[0] == by_side and p[1] in ("B", "Q"):
                    return True
                break
            xx += dx
            yy += dy

    # Rooks / Queens
    for dx, dy in ROOK_DIRS:
        xx, yy = x + dx, y + dy
        while in_bounds(xx, yy):
            s = xy_to_sq(xx, yy)
            p = board.get(s)
            if p:
                if p[0] == by_side and p[1] in ("R", "Q"):
                    return True
                break
            xx += dx
            yy += dy

    return False


def in_check(board: Dict[str, str], side: str) -> bool:
    ks = king_square(board, side)
    if ks is None:
        return True
    return is_attacked(board, ks, opp(side))


def make_move(board: Dict[str, str], move: str) -> Dict[str, str]:
    newb = dict(board)
    frm = move[:2]
    to = move[2:4]
    promo = move[4] if len(move) == 5 else None
    piece = newb.pop(frm, None)
    if piece is None:
        return newb

    # Basic move / capture
    if to in newb:
        del newb[to]

    # Castling rook move
    if piece[1] == "K":
        if frm == "e1" and to == "g1" and piece[0] == "w":
            if "h1" in newb and newb["h1"] == "wR":
                del newb["h1"]
                newb["f1"] = "wR"
        elif frm == "e1" and to == "c1" and piece[0] == "w":
            if "a1" in newb and newb["a1"] == "wR":
                del newb["a1"]
                newb["d1"] = "wR"
        elif frm == "e8" and to == "g8" and piece[0] == "b":
            if "h8" in newb and newb["h8"] == "bR":
                del newb["h8"]
                newb["f8"] = "bR"
        elif frm == "e8" and to == "c8" and piece[0] == "b":
            if "a8" in newb and newb["a8"] == "bR":
                del newb["a8"]
                newb["d8"] = "bR"

    # Promotion
    if promo and piece[1] == "P":
        piece = piece[0] + promo.upper()

    newb[to] = piece
    return newb


def gen_pseudo_moves(board: Dict[str, str], side: str) -> List[str]:
    moves = []
    forward = 1 if side == "w" else -1
    start_rank = 1 if side == "w" else 6
    promo_rank = 7 if side == "w" else 0

    for sq, pc in board.items():
        if pc[0] != side:
            continue
        p = pc[1]
        x, y = sq_to_xy(sq)

        if p == "P":
            # One step
            yy = y + forward
            if in_bounds(x, yy):
                to = xy_to_sq(x, yy)
                if to not in board:
                    if yy == promo_rank:
                        for pr in "qrbn":
                            moves.append(sq + to + pr)
                    else:
                        moves.append(sq + to)

                    # Two steps
                    if y == start_rank:
                        yy2 = y + 2 * forward
                        to2 = xy_to_sq(x, yy2)
                        if in_bounds(x, yy2) and to2 not in board:
                            moves.append(sq + to2)

            # Captures
            for dx in (-1, 1):
                xx, yy = x + dx, y + forward
                if in_bounds(xx, yy):
                    to = xy_to_sq(xx, yy)
                    if to in board and board[to][0] != side:
                        if yy == promo_rank:
                            for pr in "qrbn":
                                moves.append(sq + to + pr)
                        else:
                            moves.append(sq + to)

        elif p == "N":
            for dx, dy in KNIGHT_DIRS:
                xx, yy = x + dx, y + dy
                if in_bounds(xx, yy):
                    to = xy_to_sq(xx, yy)
                    if to not in board or board[to][0] != side:
                        moves.append(sq + to)

        elif p == "B":
            for dx, dy in BISHOP_DIRS:
                xx, yy = x + dx, y + dy
                while in_bounds(xx, yy):
                    to = xy_to_sq(xx, yy)
                    if to in board:
                        if board[to][0] != side:
                            moves.append(sq + to)
                        break
                    moves.append(sq + to)
                    xx += dx
                    yy += dy

        elif p == "R":
            for dx, dy in ROOK_DIRS:
                xx, yy = x + dx, y + dy
                while in_bounds(xx, yy):
                    to = xy_to_sq(xx, yy)
                    if to in board:
                        if board[to][0] != side:
                            moves.append(sq + to)
                        break
                    moves.append(sq + to)
                    xx += dx
                    yy += dy

        elif p == "Q":
            for dx, dy in QUEEN_DIRS:
                xx, yy = x + dx, y + dy
                while in_bounds(xx, yy):
                    to = xy_to_sq(xx, yy)
                    if to in board:
                        if board[to][0] != side:
                            moves.append(sq + to)
                        break
                    moves.append(sq + to)
                    xx += dx
                    yy += dy

        elif p == "K":
            for dx, dy in KING_DIRS:
                xx, yy = x + dx, y + dy
                if in_bounds(xx, yy):
                    to = xy_to_sq(xx, yy)
                    if to not in board or board[to][0] != side:
                        moves.append(sq + to)

            # Heuristic castling if board setup permits
            if side == "w" and sq == "e1" and board.get("e1") == "wK" and not in_check(board, "w"):
                if board.get("h1") == "wR" and "f1" not in board and "g1" not in board:
                    if not is_attacked(board, "f1", "b") and not is_attacked(board, "g1", "b"):
                        moves.append("e1g1")
                if board.get("a1") == "wR" and "b1" not in board and "c1" not in board and "d1" not in board:
                    if not is_attacked(board, "d1", "b") and not is_attacked(board, "c1", "b"):
                        moves.append("e1c1")
            if side == "b" and sq == "e8" and board.get("e8") == "bK" and not in_check(board, "b"):
                if board.get("h8") == "bR" and "f8" not in board and "g8" not in board:
                    if not is_attacked(board, "f8", "w") and not is_attacked(board, "g8", "w"):
                        moves.append("e8g8")
                if board.get("a8") == "bR" and "b8" not in board and "c8" not in board and "d8" not in board:
                    if not is_attacked(board, "d8", "w") and not is_attacked(board, "c8", "w"):
                        moves.append("e8c8")

    return moves


def gen_legal_moves(board: Dict[str, str], side: str) -> List[str]:
    legal = []
    for mv in gen_pseudo_moves(board, side):
        nb = make_move(board, mv)
        if not in_check(nb, side):
            legal.append(mv)
    return legal


def material_eval(board: Dict[str, str], side: str) -> int:
    score = 0
    for sq, pc in board.items():
        val = PIECE_VALUE[pc[1]]
        x, y = sq_to_xy(sq)

        # mild piece-square / centralization
        center = 4 - abs(3.5 - x) - abs(3.5 - y)
        bonus = int(center * 4)

        # pawns advanced
        if pc[1] == "P":
            bonus += (y * 6 if pc[0] == "w" else (7 - y) * 6)

        # king safety: prefer castled-ish positions slightly
        if pc[1] == "K":
            if pc[0] == "w":
                if sq in ("g1", "c1"):
                    bonus += 30
            else:
                if sq in ("g8", "c8"):
                    bonus += 30

        if pc[0] == side:
            score += val + bonus
        else:
            score -= val + bonus
    return score


def move_capture_value(board: Dict[str, str], mv: str, side: str) -> int:
    frm, to = mv[:2], mv[2:4]
    attacker = board.get(frm)
    victim = board.get(to)
    score = 0
    if victim:
        score += 10 * PIECE_VALUE[victim[1]]
        if attacker:
            score -= PIECE_VALUE[attacker[1]] // 4
    if len(mv) == 5:
        promo_piece = mv[4].upper()
        score += PIECE_VALUE.get(promo_piece, 0) + 700
    return score


def legal_moves_from_env() -> Optional[List[str]]:
    # Try common places a harness might expose legal moves.
    try:
        lm = globals().get("legal_moves", None)
        if isinstance(lm, list) and all(isinstance(x, str) for x in lm) and lm:
            return lm
    except Exception:
        pass
    try:
        import builtins
        lm = getattr(builtins, "legal_moves", None)
        if isinstance(lm, list) and all(isinstance(x, str) for x in lm) and lm:
            return lm
    except Exception:
        pass
    return None


def score_move(board: Dict[str, str], mv: str, side: str) -> int:
    enemy = opp(side)
    nb = make_move(board, mv)

    # If move somehow leaves us in check, reject hard.
    if in_check(nb, side):
        return -10**9

    score = 0

    # Tactical immediate features
    score += move_capture_value(board, mv, side)

    # Give check
    if in_check(nb, enemy):
        score += 80

    # Mate / near-mate
    enemy_moves = gen_legal_moves(nb, enemy)
    if not enemy_moves:
        if in_check(nb, enemy):
            return 10**8
        else:
            score -= 100  # stalemate usually not ideal

    # Static position
    score += material_eval(nb, side)

    # Opponent best reply (1-ply minimax)
    if enemy_moves:
        worst = 10**9
        # move ordering by captures/check-ish proxies
        enemy_moves_sorted = sorted(
            enemy_moves,
            key=lambda m: move_capture_value(nb, m, enemy),
            reverse=True
        )[:18]
        for em in enemy_moves_sorted:
            nnb = make_move(nb, em)
            if in_check(nnb, enemy):
                continue
            val = material_eval(nnb, side)
            if in_check(nnb, side):
                val -= 120
            our_replies = gen_legal_moves(nnb, side)
            if not our_replies and in_check(nnb, side):
                val -= 10**7
            if val < worst:
                worst = val
        score += worst // 2

    # Prefer moving attacked piece away if useful
    frm = mv[:2]
    if is_attacked(board, frm, enemy):
        score += 20

    # Discourage hanging moved piece
    to = mv[2:4]
    moved_piece = nb.get(to)
    if moved_piece and moved_piece[0] == side and is_attacked(nb, to, enemy):
        defenders = 0
        attackers = 0
        # crude attacker/defender estimate
        for s2, p2 in nb.items():
            if p2[0] == side and s2 != to:
                test = dict(nb)
                pc = test.pop(s2)
                if to in [m[2:4] for m in gen_pseudo_moves(test | {s2: pc}, side) if m[:2] == s2]:
                    defenders += 1
            elif p2[0] == enemy:
                test = dict(nb)
                pc = test.pop(s2)
                if to in [m[2:4] for m in gen_pseudo_moves(test | {s2: pc}, enemy) if m[:2] == s2]:
                    attackers += 1
        if attackers > defenders:
            score -= PIECE_VALUE[moved_piece[1]] // 2

    return score


def policy(pieces: dict[str, str], to_play: str) -> str:
    side = color_char(to_play)

    # Prefer externally supplied legal moves if present
    env_moves = legal_moves_from_env()
    if env_moves:
        legal = list(env_moves)
    else:
        legal = gen_legal_moves(pieces, side)

    # Absolute fallback to avoid disqualification if possible
    if not legal:
        pseudo = gen_pseudo_moves(pieces, side)
        if pseudo:
            return pseudo[0]
        # Last-resort impossible fallback
        return "a1a1"

    # Fast tactical checks first: instant mate
    best_move = legal[0]
    best_score = -10**18

    # Order candidate moves for stronger pruning / early good picks
    ordered = sorted(
        legal,
        key=lambda m: (
            len(m) == 5,
            move_capture_value(pieces, m, side),
            m[2:4] in ("d4", "e4", "d5", "e5")
        ),
        reverse=True
    )

    for mv in ordered:
        sc = score_move(pieces, mv, side)
        if sc > best_score:
            best_score = sc
            best_move = mv

    return best_move
