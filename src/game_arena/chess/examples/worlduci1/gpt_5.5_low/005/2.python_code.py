
import math
import random

FILES = "abcdefgh"
RANKS = "12345678"

PIECE_VALUE = {
    "K": 0,
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


def other_color(c):
    return "b" if c == "w" else "w"


def other_turn(t):
    return "black" if t == "white" else "white"


def find_king(board, color):
    target = color + "K"
    for s, p in board.items():
        if p == target:
            return s
    return None


def is_square_attacked(board, square, by_color):
    x, y = sq_to_xy(square)

    # Pawns
    if by_color == "w":
        pawn_sources = [(x - 1, y - 1), (x + 1, y - 1)]
    else:
        pawn_sources = [(x - 1, y + 1), (x + 1, y + 1)]

    for px, py in pawn_sources:
        if on_board(px, py):
            p = board.get(xy_to_sq(px, py))
            if p == by_color + "P":
                return True

    # Knights
    for dx, dy in KNIGHT_DIRS:
        nx, ny = x + dx, y + dy
        if on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p == by_color + "N":
                return True

    # Kings
    for dx, dy in KING_DIRS:
        nx, ny = x + dx, y + dy
        if on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p == by_color + "K":
                return True

    # Bishops / Queens
    for dx, dy in BISHOP_DIRS:
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and (p[1] == "B" or p[1] == "Q"):
                    return True
                break
            nx += dx
            ny += dy

    # Rooks / Queens
    for dx, dy in ROOK_DIRS:
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and (p[1] == "R" or p[1] == "Q"):
                    return True
                break
            nx += dx
            ny += dy

    return False


def in_check(board, color):
    ksq = find_king(board, color)
    if ksq is None:
        return True
    return is_square_attacked(board, ksq, other_color(color))


def make_move(board, move):
    nb = dict(board)
    frm = move[:2]
    to = move[2:4]
    promo = move[4:] if len(move) > 4 else ""
    piece = nb.pop(frm)

    if promo:
        piece = piece[0] + promo.upper()

    nb[to] = piece
    return nb


def pseudo_moves(board, turn):
    color = color_char(turn)
    moves = []

    for sq, piece in list(board.items()):
        if piece[0] != color:
            continue

        x, y = sq_to_xy(sq)
        pt = piece[1]

        if pt == "P":
            direction = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promotion_rank = 7 if color == "w" else 0

            # One step
            ny = y + direction
            if on_board(x, ny):
                ns = xy_to_sq(x, ny)
                if ns not in board:
                    if ny == promotion_rank:
                        for pr in "qrbn":
                            moves.append(sq + ns + pr)
                    else:
                        moves.append(sq + ns)

                    # Two steps
                    ny2 = y + 2 * direction
                    if y == start_rank and on_board(x, ny2):
                        ns2 = xy_to_sq(x, ny2)
                        if ns2 not in board:
                            moves.append(sq + ns2)

            # Captures
            for dx in (-1, 1):
                nx, ny = x + dx, y + direction
                if on_board(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    target = board.get(ns)
                    if target and target[0] != color:
                        if ny == promotion_rank:
                            for pr in "qrbn":
                                moves.append(sq + ns + pr)
                        else:
                            moves.append(sq + ns)

        elif pt == "N":
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if on_board(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    target = board.get(ns)
                    if not target or target[0] != color:
                        moves.append(sq + ns)

        elif pt == "K":
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if on_board(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    target = board.get(ns)
                    if not target or target[0] != color:
                        moves.append(sq + ns)

        elif pt in ("B", "R", "Q"):
            if pt == "B":
                dirs = BISHOP_DIRS
            elif pt == "R":
                dirs = ROOK_DIRS
            else:
                dirs = QUEEN_DIRS

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while on_board(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    target = board.get(ns)
                    if not target:
                        moves.append(sq + ns)
                    else:
                        if target[0] != color:
                            moves.append(sq + ns)
                        break
                    nx += dx
                    ny += dy

    return moves


def legal_moves(board, turn):
    color = color_char(turn)
    result = []

    for mv in pseudo_moves(board, turn):
        nb = make_move(board, mv)
        if not in_check(nb, color):
            result.append(mv)

    return result


def piece_square_bonus(piece, square):
    x, y = sq_to_xy(square)
    color, pt = piece[0], piece[1]

    # Normalize from White's perspective.
    yy = y if color == "w" else 7 - y

    center_dist = abs(x - 3.5) + abs(yy - 3.5)
    center_bonus = int(14 - 3 * center_dist)

    if pt == "P":
        return yy * 8 - abs(x - 3.5) * 2
    if pt == "N":
        return center_bonus * 4
    if pt == "B":
        return center_bonus * 3
    if pt == "R":
        return yy * 3
    if pt == "Q":
        return center_bonus
    if pt == "K":
        # Prefer safer back ranks in middlegame-like material situations.
        return -center_bonus * 2 - yy * 2

    return 0


def evaluate(board, root_color):
    score = 0
    material_total = 0

    for sq, piece in board.items():
        val = PIECE_VALUE[piece[1]]
        material_total += val
        val += piece_square_bonus(piece, sq)
        if piece[0] == root_color:
            score += val
        else:
            score -= val

    # In low material, king activity becomes useful.
    if material_total < 2500:
        for sq, piece in board.items():
            if piece[1] == "K":
                x, y = sq_to_xy(sq)
                center = 14 - 3 * (abs(x - 3.5) + abs(y - 3.5))
                if piece[0] == root_color:
                    score += center * 2
                else:
                    score -= center * 2

    # Small check bonus.
    opp = other_color(root_color)
    if in_check(board, opp):
        score += 35
    if in_check(board, root_color):
        score -= 45

    return score


def move_order_score(board, mv):
    frm = mv[:2]
    to = mv[2:4]
    moving = board.get(frm, "")
    captured = board.get(to)

    score = 0
    if captured and moving:
        score += 10 * PIECE_VALUE[captured[1]] - PIECE_VALUE[moving[1]]

    if len(mv) > 4:
        if mv[4] == "q":
            score += 900
        else:
            score += 300

    # Prefer central destination.
    x, y = sq_to_xy(to)
    score += int(10 - (abs(x - 3.5) + abs(y - 3.5)))

    return score


def alphabeta(board, turn, depth, alpha, beta, root_color):
    moves = legal_moves(board, turn)

    if not moves:
        c = color_char(turn)
        if in_check(board, c):
            if c == root_color:
                return -1000000 - depth
            else:
                return 1000000 + depth
        return 0

    if depth == 0:
        return evaluate(board, root_color)

    maximizing = color_char(turn) == root_color
    moves.sort(key=lambda m: move_order_score(board, m), reverse=True)

    if maximizing:
        value = -math.inf
        for mv in moves:
            nb = make_move(board, mv)
            value = max(value, alphabeta(nb, other_turn(turn), depth - 1, alpha, beta, root_color))
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = math.inf
        for mv in moves:
            nb = make_move(board, mv)
            value = min(value, alphabeta(nb, other_turn(turn), depth - 1, alpha, beta, root_color))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def policy(pieces: dict[str, str], to_play: str) -> str:
    board = dict(pieces)
    moves = legal_moves(board, to_play)

    # Absolute safety fallback. In a valid chess position this should not be needed.
    if not moves:
        pm = pseudo_moves(board, to_play)
        if pm:
            return pm[0]
        return "a1a1"

    root_color = color_char(to_play)

    # Adaptive depth to stay fast.
    if len(moves) <= 8:
        depth = 3
    elif len(moves) <= 22:
        depth = 2
    else:
        depth = 2

    ordered = sorted(moves, key=lambda m: move_order_score(board, m), reverse=True)

    best_move = ordered[0]
    best_score = -math.inf

    for mv in ordered:
        nb = make_move(board, mv)

        # Immediate checkmate detection.
        opp_moves = legal_moves(nb, other_turn(to_play))
        if not opp_moves and in_check(nb, other_color(root_color)):
            return mv

        score = alphabeta(nb, other_turn(to_play), depth - 1, -math.inf, math.inf, root_color)

        # Tiny deterministic preference for queen promotions and captures.
        if len(mv) > 4 and mv[4] == "q":
            score += 5
        if board.get(mv[2:4]):
            score += 2

        if score > best_score:
            best_score = score
            best_move = mv

    return best_move
