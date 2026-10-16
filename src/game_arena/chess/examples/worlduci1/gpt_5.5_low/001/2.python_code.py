
import math
import random

FILES = "abcdefgh"
RANKS = "12345678"

VAL = {
    "K": 20000,
    "Q": 900,
    "R": 500,
    "B": 330,
    "N": 320,
    "P": 100,
}

KNIGHT_DIRS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DIRS = [(1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS

CENTER = {"d4", "e4", "d5", "e5"}
EXT_CENTER = {"c3", "d3", "e3", "f3", "c4", "f4", "c5", "f5", "c6", "d6", "e6", "f6"}


def sq_to_xy(s):
    return FILES.index(s[0]), RANKS.index(s[1])


def xy_to_sq(x, y):
    return FILES[x] + RANKS[y]


def inside(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def color_code(to_play):
    return "w" if to_play == "white" else "b"


def other(c):
    return "b" if c == "w" else "w"


def color_name(c):
    return "white" if c == "w" else "black"


def find_king(board, color):
    target = color + "K"
    for s, p in board.items():
        if p == target:
            return s
    return None


def attacked_by(board, sq, attacker):
    tx, ty = sq_to_xy(sq)

    # Pawns
    pawn_dir = 1 if attacker == "w" else -1
    for dx in (-1, 1):
        x, y = tx - dx, ty - pawn_dir
        if inside(x, y) and board.get(xy_to_sq(x, y)) == attacker + "P":
            return True

    # Knights
    for dx, dy in KNIGHT_DIRS:
        x, y = tx + dx, ty + dy
        if inside(x, y) and board.get(xy_to_sq(x, y)) == attacker + "N":
            return True

    # Kings
    for dx, dy in KING_DIRS:
        x, y = tx + dx, ty + dy
        if inside(x, y) and board.get(xy_to_sq(x, y)) == attacker + "K":
            return True

    # Sliding pieces
    for dirs, pieces in ((BISHOP_DIRS, ("B", "Q")), (ROOK_DIRS, ("R", "Q"))):
        for dx, dy in dirs:
            x, y = tx + dx, ty + dy
            while inside(x, y):
                s = xy_to_sq(x, y)
                p = board.get(s)
                if p:
                    if p[0] == attacker and p[1] in pieces:
                        return True
                    break
                x += dx
                y += dy

    return False


def in_check(board, color):
    k = find_king(board, color)
    if k is None:
        return True
    return attacked_by(board, k, other(color))


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


def pseudo_moves(board, color):
    moves = []

    for s, p in list(board.items()):
        if p[0] != color:
            continue

        typ = p[1]
        x, y = sq_to_xy(s)

        if typ == "P":
            step = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promo_rank = 7 if color == "w" else 0

            # One step
            ny = y + step
            if inside(x, ny):
                ns = xy_to_sq(x, ny)
                if ns not in board:
                    if ny == promo_rank:
                        for pr in "qrbn":
                            moves.append(s + ns + pr)
                    else:
                        moves.append(s + ns)

                    # Two steps
                    ny2 = y + 2 * step
                    if y == start_rank and inside(x, ny2):
                        ns2 = xy_to_sq(x, ny2)
                        if ns2 not in board:
                            moves.append(s + ns2)

            # Captures
            for dx in (-1, 1):
                nx, ny = x + dx, y + step
                if inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns in board and board[ns][0] != color:
                        if ny == promo_rank:
                            for pr in "qrbn":
                                moves.append(s + ns + pr)
                        else:
                            moves.append(s + ns)

        elif typ == "N":
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns not in board or board[ns][0] != color:
                        moves.append(s + ns)

        elif typ == "K":
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns not in board or board[ns][0] != color:
                        moves.append(s + ns)

        elif typ in ("B", "R", "Q"):
            dirs = BISHOP_DIRS if typ == "B" else ROOK_DIRS if typ == "R" else QUEEN_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns in board:
                        if board[ns][0] != color:
                            moves.append(s + ns)
                        break
                    moves.append(s + ns)
                    nx += dx
                    ny += dy

    return moves


def legal_moves(board, color):
    res = []
    for m in pseudo_moves(board, color):
        nb = make_move(board, m)
        if not in_check(nb, color):
            res.append(m)
    return res


def mobility_score(board, color):
    # Cheap pseudo-mobility, not full legality, for evaluation speed.
    return len(pseudo_moves(board, color))


def evaluate(board, root_color):
    if find_king(board, root_color) is None:
        return -999999
    if find_king(board, other(root_color)) is None:
        return 999999

    score = 0

    for s, p in board.items():
        c, t = p[0], p[1]
        sign = 1 if c == root_color else -1
        x, y = sq_to_xy(s)

        score += sign * VAL[t]

        # Positional bonuses
        if s in CENTER:
            score += sign * (18 if t in "NBRQ" else 10)
        elif s in EXT_CENTER:
            score += sign * 7

        # Pawn advancement
        if t == "P":
            adv = y if c == "w" else 7 - y
            score += sign * adv * 8

        # Knights prefer central squares
        if t == "N":
            dist = abs(x - 3.5) + abs(y - 3.5)
            score += sign * int(20 - 6 * dist)

        # King safety: prefer back ranks unless endgame
        if t == "K":
            home = 0 if c == "w" else 7
            score -= sign * abs(y - home) * 6

    score += 2 * (mobility_score(board, root_color) - mobility_score(board, other(root_color)))

    if in_check(board, other(root_color)):
        score += 35
    if in_check(board, root_color):
        score -= 45

    return score


def move_order_score(board, move, color):
    to = move[2:4]
    frm = move[:2]
    sc = 0
    if to in board:
        victim = board[to][1]
        attacker = board[frm][1]
        sc += 10 * VAL[victim] - VAL[attacker]
    if len(move) > 4:
        sc += VAL[move[4].upper()]
    if to in CENTER:
        sc += 20
    return sc


def negamax(board, color, depth, alpha, beta, root_color):
    lm = legal_moves(board, color)

    if not lm:
        if in_check(board, color):
            return -999999 if color == root_color else 999999
        return 0

    if depth == 0:
        return evaluate(board, root_color)

    lm.sort(key=lambda m: move_order_score(board, m, color), reverse=True)

    if color == root_color:
        best = -10**9
        for m in lm:
            val = negamax(make_move(board, m), other(color), depth - 1, alpha, beta, root_color)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:
        best = 10**9
        for m in lm:
            val = negamax(make_move(board, m), other(color), depth - 1, alpha, beta, root_color)
            if val < best:
                best = val
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best


def policy(pieces: dict[str, str], to_play: str) -> str:
    color = color_code(to_play)
    board = dict(pieces)

    lm = legal_moves(board, color)

    # Absolute fallback: should only happen in checkmate/stalemate positions.
    if not lm:
        pm = pseudo_moves(board, color)
        if pm:
            return pm[0]
        return "a1a1"

    # Use depth 2 normally; reduce if many moves to stay fast.
    depth = 2
    if len(lm) > 45:
        depth = 1

    lm.sort(key=lambda m: move_order_score(board, m, color), reverse=True)

    best_move = lm[0]
    best_val = -10**9

    alpha = -10**9
    beta = 10**9

    for m in lm:
        nb = make_move(board, m)
        val = negamax(nb, other(color), depth - 1, alpha, beta, color)

        # Tiny deterministic tie-breaker favoring promotion/capture/center.
        val += move_order_score(board, m, color) * 0.01

        if val > best_val:
            best_val = val
            best_move = m

        alpha = max(alpha, int(best_val))
        if alpha >= beta:
            break

    return best_move
