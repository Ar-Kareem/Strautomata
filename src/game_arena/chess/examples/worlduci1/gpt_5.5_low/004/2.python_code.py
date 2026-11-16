
import math
import time
import random

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUE = {
    "K": 20000,
    "Q": 900,
    "R": 500,
    "B": 330,
    "N": 320,
    "P": 100,
}

KNIGHT_DIRS = [
    (1, 2), (2, 1), (2, -1), (1, -2),
    (-1, -2), (-2, -1), (-2, 1), (-1, 2)
]
KING_DIRS = [
    (1, 0), (1, 1), (0, 1), (-1, 1),
    (-1, 0), (-1, -1), (0, -1), (1, -1)
]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS


def sq_to_xy(s):
    return FILES.index(s[0]), int(s[1]) - 1


def xy_to_sq(x, y):
    return FILES[x] + str(y + 1)


def on_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def color_char(to_play):
    return "w" if to_play == "white" else "b"


def other(c):
    return "b" if c == "w" else "w"


def move_to_str(fr, to, promo=None):
    return fr + to + (promo if promo else "")


def find_king(board, color):
    target = color + "K"
    for s, p in board.items():
        if p == target:
            return s
    return None


def is_square_attacked(board, sq, by_color):
    x, y = sq_to_xy(sq)

    # Pawn attacks
    if by_color == "w":
        pawn_sources = [(x - 1, y - 1), (x + 1, y - 1)]
    else:
        pawn_sources = [(x - 1, y + 1), (x + 1, y + 1)]
    for px, py in pawn_sources:
        if on_board(px, py) and board.get(xy_to_sq(px, py)) == by_color + "P":
            return True

    # Knights
    for dx, dy in KNIGHT_DIRS:
        nx, ny = x + dx, y + dy
        if on_board(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + "N":
            return True

    # Kings
    for dx, dy in KING_DIRS:
        nx, ny = x + dx, y + dy
        if on_board(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + "K":
            return True

    # Bishops / queens
    for dx, dy in BISHOP_DIRS:
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and p[1] in ("B", "Q"):
                    return True
                break
            nx += dx
            ny += dy

    # Rooks / queens
    for dx, dy in ROOK_DIRS:
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and p[1] in ("R", "Q"):
                    return True
                break
            nx += dx
            ny += dy

    return False


def in_check(board, color):
    ksq = find_king(board, color)
    if not ksq:
        return True
    return is_square_attacked(board, ksq, other(color))


def make_move(board, mv):
    fr = mv[:2]
    to = mv[2:4]
    promo = mv[4:] if len(mv) > 4 else ""
    nb = dict(board)
    p = nb.pop(fr)
    if to in nb:
        nb.pop(to)
    if promo and p[1] == "P":
        p = p[0] + promo.upper()
    nb[to] = p
    return nb


def pseudo_moves(board, color):
    moves = []
    for sq, piece in list(board.items()):
        if piece[0] != color:
            continue

        typ = piece[1]
        x, y = sq_to_xy(sq)

        if typ == "P":
            direction = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promote_rank = 7 if color == "w" else 0

            # one step
            ny = y + direction
            if on_board(x, ny):
                to = xy_to_sq(x, ny)
                if to not in board:
                    if ny == promote_rank:
                        for pr in "qrbn":
                            moves.append(move_to_str(sq, to, pr))
                    else:
                        moves.append(move_to_str(sq, to))
                        # two steps
                        if y == start_rank:
                            ny2 = y + 2 * direction
                            to2 = xy_to_sq(x, ny2)
                            if on_board(x, ny2) and to2 not in board:
                                moves.append(move_to_str(sq, to2))

            # captures
            for dx in (-1, 1):
                nx, ny = x + dx, y + direction
                if on_board(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if target and target[0] != color:
                        if ny == promote_rank:
                            for pr in "qrbn":
                                moves.append(move_to_str(sq, to, pr))
                        else:
                            moves.append(move_to_str(sq, to))

        elif typ == "N":
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if on_board(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if not target or target[0] != color:
                        moves.append(move_to_str(sq, to))

        elif typ == "K":
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if on_board(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if not target or target[0] != color:
                        moves.append(move_to_str(sq, to))

            # Conservative castling support when path is clear and standard pieces exist.
            # Castling rights are not provided by the API, so this is intentionally only
            # generated from untouched-looking starting squares.
            if color == "w" and sq == "e1" and not in_check(board, color):
                if board.get("h1") == "wR" and "f1" not in board and "g1" not in board:
                    if not is_square_attacked(board, "f1", "b") and not is_square_attacked(board, "g1", "b"):
                        moves.append("e1g1")
                if board.get("a1") == "wR" and "b1" not in board and "c1" not in board and "d1" not in board:
                    if not is_square_attacked(board, "d1", "b") and not is_square_attacked(board, "c1", "b"):
                        moves.append("e1c1")
            elif color == "b" and sq == "e8" and not in_check(board, color):
                if board.get("h8") == "bR" and "f8" not in board and "g8" not in board:
                    if not is_square_attacked(board, "f8", "w") and not is_square_attacked(board, "g8", "w"):
                        moves.append("e8g8")
                if board.get("a8") == "bR" and "b8" not in board and "c8" not in board and "d8" not in board:
                    if not is_square_attacked(board, "d8", "w") and not is_square_attacked(board, "c8", "w"):
                        moves.append("e8c8")

        else:
            dirs = BISHOP_DIRS if typ == "B" else ROOK_DIRS if typ == "R" else QUEEN_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while on_board(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if not target:
                        moves.append(move_to_str(sq, to))
                    else:
                        if target[0] != color:
                            moves.append(move_to_str(sq, to))
                        break
                    nx += dx
                    ny += dy

    return moves


def legal_moves(board, color):
    res = []
    for mv in pseudo_moves(board, color):
        nb = make_move(board, mv)

        # Handle rook movement for castling.
        if mv == "e1g1" and board.get("e1") == "wK" and board.get("h1") == "wR":
            nb.pop("h1", None)
            nb["f1"] = "wR"
        elif mv == "e1c1" and board.get("e1") == "wK" and board.get("a1") == "wR":
            nb.pop("a1", None)
            nb["d1"] = "wR"
        elif mv == "e8g8" and board.get("e8") == "bK" and board.get("h8") == "bR":
            nb.pop("h8", None)
            nb["f8"] = "bR"
        elif mv == "e8c8" and board.get("e8") == "bK" and board.get("a8") == "bR":
            nb.pop("a8", None)
            nb["d8"] = "bR"

        if not in_check(nb, color):
            res.append(mv)
    return res


def mobility_score(board, color):
    # Fast pseudo mobility approximation.
    return len(pseudo_moves(board, color))


def evaluate(board, root_color):
    score = 0

    for sq, p in board.items():
        c, t = p[0], p[1]
        sign = 1 if c == root_color else -1
        x, y = sq_to_xy(sq)

        val = PIECE_VALUE[t]
        score += sign * val

        # Centralization.
        center_bonus = 8 - (abs(x - 3.5) + abs(y - 3.5))
        if t in ("N", "B"):
            score += sign * center_bonus * 6
        elif t == "Q":
            score += sign * center_bonus * 2
        elif t == "P":
            # Reward pawn advancement.
            adv = y if c == "w" else 7 - y
            score += sign * adv * 8
            # Small center pawn bonus.
            if x in (3, 4):
                score += sign * 10
        elif t == "K":
            # Prefer safer back-rank king in middlegame-ish positions.
            own_material = sum(PIECE_VALUE[q[1]] for q in board.values() if q[0] == c and q[1] != "K")
            if own_material > 1600:
                home_rank = 0 if c == "w" else 7
                score -= sign * (abs(y - home_rank) * 8)
            else:
                score += sign * center_bonus * 4

    # Check status and mobility.
    if in_check(board, other(root_color)):
        score += 35
    if in_check(board, root_color):
        score -= 45

    score += 2 * (mobility_score(board, root_color) - mobility_score(board, other(root_color)))
    return score


def move_order_score(board, mv, color):
    fr, to = mv[:2], mv[2:4]
    moving = board.get(fr, "")
    target = board.get(to, "")
    score = 0
    if target:
        score += 10 * PIECE_VALUE[target[1]] - PIECE_VALUE[moving[1]]
    if len(mv) > 4:
        score += PIECE_VALUE[mv[4].upper()] + 800
    if moving and moving[1] in ("N", "B", "Q"):
        x, y = sq_to_xy(to)
        score += int(10 - abs(x - 3.5) - abs(y - 3.5))
    return score


def negamax(board, color, root_color, depth, alpha, beta, end_time):
    if time.time() > end_time:
        return evaluate(board, root_color)

    moves = legal_moves(board, color)
    if not moves:
        if in_check(board, color):
            return -100000 if color == root_color else 100000
        return 0

    if depth <= 0:
        return evaluate(board, root_color)

    moves.sort(key=lambda m: move_order_score(board, m, color), reverse=True)

    best = -10**9
    for mv in moves:
        nb = make_move(board, mv)
        if mv == "e1g1":
            nb.pop("h1", None); nb["f1"] = "wR"
        elif mv == "e1c1":
            nb.pop("a1", None); nb["d1"] = "wR"
        elif mv == "e8g8":
            nb.pop("h8", None); nb["f8"] = "bR"
        elif mv == "e8c8":
            nb.pop("a8", None); nb["d8"] = "bR"

        val = -negamax(nb, other(color), root_color, depth - 1, -beta, -alpha, end_time)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def choose_from_given_legal_if_available(generated):
    # Some arenas expose legal_moves as a global. If present, intersect with our
    # generated moves to guarantee compatibility with the arena's exact rules.
    lm = globals().get("legal_moves", None)
    if isinstance(lm, (list, tuple, set)) and lm:
        given = list(lm)
        gs = set(generated)
        inter = [m for m in given if m in gs]
        if inter:
            return inter, given
        return given, given
    return generated, generated


def policy(pieces: dict[str, str], to_play: str) -> str:
    board = dict(pieces)
    color = color_char(to_play)

    generated = legal_moves(board, color)
    candidates, fallback_list = choose_from_given_legal_if_available(generated)

    if not candidates:
        # Should almost never occur in valid non-terminal games. Return any global
        # legal move if supplied; otherwise a harmless syntactically valid fallback.
        if fallback_list:
            return list(fallback_list)[0]
        return "a1a1"

    # Immediate mate check / high-value tactical filtering.
    opp = other(color)
    ordered = sorted(candidates, key=lambda m: move_order_score(board, m, color), reverse=True)

    for mv in ordered:
        nb = make_move(board, mv)
        if mv == "e1g1":
            nb.pop("h1", None); nb["f1"] = "wR"
        elif mv == "e1c1":
            nb.pop("a1", None); nb["d1"] = "wR"
        elif mv == "e8g8":
            nb.pop("h8", None); nb["f8"] = "bR"
        elif mv == "e8c8":
            nb.pop("a8", None); nb["d8"] = "bR"
        if in_check(nb, opp) and not legal_moves(nb, opp):
            return mv

    end_time = time.time() + 0.88
    best_move = ordered[0]
    best_score = -10**9

    # Adaptive depth: deeper in sparse/endgame positions.
    nmen = len(board)
    depth = 3
    if nmen <= 10:
        depth = 4
    if nmen <= 6:
        depth = 5
    if len(ordered) > 38:
        depth = 2

    alpha = -10**9
    beta = 10**9

    for mv in ordered:
        if time.time() > end_time:
            break
        nb = make_move(board, mv)
        if mv == "e1g1":
            nb.pop("h1", None); nb["f1"] = "wR"
        elif mv == "e1c1":
            nb.pop("a1", None); nb["d1"] = "wR"
        elif mv == "e8g8":
            nb.pop("h8", None); nb["f8"] = "bR"
        elif mv == "e8c8":
            nb.pop("a8", None); nb["d8"] = "bR"

        score = -negamax(nb, opp, color, depth - 1, -beta, -alpha, end_time)

        # Small deterministic tie-break favoring promotions/captures/central moves.
        score += 0.01 * move_order_score(board, mv, color)

        if score > best_score:
            best_score = score
            best_move = mv
        if score > alpha:
            alpha = score

    # If arena supplied exact legal_moves, make absolutely sure result is included.
    lm = globals().get("legal_moves", None)
    if isinstance(lm, (list, tuple, set)) and lm:
        if best_move in lm:
            return best_move
        return list(lm)[0]

    return best_move
