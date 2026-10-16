
import math
import random

FILES = "abcdefgh"
RANKS = "12345678"
VAL = {"P": 100, "N": 320, "B": 330, "R": 500, "Q": 900, "K": 20000}

CENTER = {
    "d4": 18, "e4": 18, "d5": 18, "e5": 18,
    "c3": 8, "d3": 10, "e3": 10, "f3": 8,
    "c4": 10, "f4": 10, "c5": 10, "f5": 10,
    "c6": 8, "d6": 10, "e6": 10, "f6": 8,
}

KNIGHT_DIRS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DIRS = [(1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS


def policy(pieces: dict[str, str], to_play: str) -> str:
    us = "w" if to_play == "white" else "b"
    them = "b" if us == "w" else "w"

    moves = legal_moves(pieces, us)
    if not moves:
        return "a1a1"

    # Immediate checkmate.
    for m in ordered_moves(pieces, moves, us):
        b = make_move(pieces, m)
        if is_check(b, them) and not legal_moves(b, them):
            return m

    # Avoid moves allowing immediate mate when possible.
    safe = []
    for m in ordered_moves(pieces, moves, us):
        b = make_move(pieces, m)
        opp = legal_moves(b, them)
        losing = False
        for om in ordered_moves(b, opp, them)[:18]:
            bb = make_move(b, om)
            if is_check(bb, us) and not legal_moves(bb, us):
                losing = True
                break
        if not losing:
            safe.append(m)
    if safe:
        moves = safe

    # Adaptive shallow negamax.
    depth = 3 if len(moves) <= 22 else 2
    best = moves[0]
    best_score = -10**9
    alpha = -10**9
    beta = 10**9

    for m in ordered_moves(pieces, moves, us):
        b = make_move(pieces, m)
        score = -search(b, them, depth - 1, -beta, -alpha, us)
        score += move_bonus(pieces, b, m, us)
        if score > best_score:
            best_score = score
            best = m
        alpha = max(alpha, best_score)

    return best


def sq_to_xy(s):
    return FILES.index(s[0]), RANKS.index(s[1])


def xy_to_sq(x, y):
    return FILES[x] + RANKS[y]


def inb(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def other(c):
    return "b" if c == "w" else "w"


def legal_moves(board, color):
    res = []
    for m in pseudo_moves(board, color):
        nb = make_move(board, m)
        if not is_check(nb, color):
            res.append(m)
    return res


def pseudo_moves(board, color):
    out = []
    for s, pc in board.items():
        if pc[0] != color:
            continue
        p = pc[1]
        x, y = sq_to_xy(s)

        if p == "P":
            dy = 1 if color == "w" else -1
            start = 1 if color == "w" else 6
            prom_rank = 7 if color == "w" else 0

            ny = y + dy
            if inb(x, ny):
                ns = xy_to_sq(x, ny)
                if ns not in board:
                    add_pawn_move(out, s, ns, ny == prom_rank)
                    if y == start:
                        ny2 = y + 2 * dy
                        ns2 = xy_to_sq(x, ny2)
                        if ns2 not in board:
                            out.append(s + ns2)

            for dx in (-1, 1):
                nx, ny = x + dx, y + dy
                if inb(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns in board and board[ns][0] != color:
                        add_pawn_move(out, s, ns, ny == prom_rank)

        elif p == "N":
            for dx, dy in KNIGHT_DIRS:
                nx, ny = x + dx, y + dy
                if inb(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns not in board or board[ns][0] != color:
                        out.append(s + ns)

        elif p == "K":
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if inb(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns not in board or board[ns][0] != color:
                        out.append(s + ns)

        elif p in ("B", "R", "Q"):
            dirs = BISHOP_DIRS if p == "B" else ROOK_DIRS if p == "R" else QUEEN_DIRS
            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while inb(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns in board:
                        if board[ns][0] != color:
                            out.append(s + ns)
                        break
                    out.append(s + ns)
                    nx += dx
                    ny += dy
    return out


def add_pawn_move(out, a, b, promo):
    if promo:
        out.append(a + b + "q")
        out.append(a + b + "r")
        out.append(a + b + "b")
        out.append(a + b + "n")
    else:
        out.append(a + b)


def make_move(board, m):
    nb = dict(board)
    a, b = m[:2], m[2:4]
    pc = nb.pop(a)
    if len(m) > 4:
        pc = pc[0] + m[4].upper()
    nb[b] = pc
    return nb


def king_square(board, color):
    target = color + "K"
    for s, p in board.items():
        if p == target:
            return s
    return None


def is_check(board, color):
    k = king_square(board, color)
    if k is None:
        return True
    return attacked(board, k, other(color))


def attacked(board, sq, by_color):
    tx, ty = sq_to_xy(sq)

    # Pawns
    pawn_from_y = ty - (1 if by_color == "w" else -1)
    for dx in (-1, 1):
        x = tx + dx
        if inb(x, pawn_from_y):
            s = xy_to_sq(x, pawn_from_y)
            if board.get(s) == by_color + "P":
                return True

    # Knights
    for dx, dy in KNIGHT_DIRS:
        x, y = tx + dx, ty + dy
        if inb(x, y) and board.get(xy_to_sq(x, y)) == by_color + "N":
            return True

    # King
    for dx, dy in KING_DIRS:
        x, y = tx + dx, ty + dy
        if inb(x, y) and board.get(xy_to_sq(x, y)) == by_color + "K":
            return True

    # Bishops / queens
    for dx, dy in BISHOP_DIRS:
        x, y = tx + dx, ty + dy
        while inb(x, y):
            p = board.get(xy_to_sq(x, y))
            if p:
                if p[0] == by_color and p[1] in ("B", "Q"):
                    return True
                break
            x += dx
            y += dy

    # Rooks / queens
    for dx, dy in ROOK_DIRS:
        x, y = tx + dx, ty + dy
        while inb(x, y):
            p = board.get(xy_to_sq(x, y))
            if p:
                if p[0] == by_color and p[1] in ("R", "Q"):
                    return True
                break
            x += dx
            y += dy

    return False


def search(board, color, depth, alpha, beta, root_color):
    moves = legal_moves(board, color)

    if not moves:
        if is_check(board, color):
            return -1000000 - depth
        return 0

    if depth <= 0:
        return evaluate(board, root_color) if color == root_color else -evaluate(board, root_color)

    best = -10**9
    for m in ordered_moves(board, moves, color):
        nb = make_move(board, m)
        sc = -search(nb, other(color), depth - 1, -beta, -alpha, root_color)
        sc += move_bonus(board, nb, m, color) // 3
        if sc > best:
            best = sc
        alpha = max(alpha, sc)
        if alpha >= beta:
            break
    return best


def evaluate(board, color):
    score = 0
    enemy = other(color)

    for s, p in board.items():
        sign = 1 if p[0] == color else -1
        score += sign * VAL[p[1]]

        if p[1] != "K":
            score += sign * CENTER.get(s, 0)

        if p[1] == "P":
            _, y = sq_to_xy(s)
            advance = y if p[0] == "w" else 7 - y
            score += sign * advance * 6

    # Mobility and check pressure.
    try:
        score += 2 * (len(pseudo_moves(board, color)) - len(pseudo_moves(board, enemy)))
    except Exception:
        pass

    if is_check(board, enemy):
        score += 35
    if is_check(board, color):
        score -= 45

    return score


def ordered_moves(board, moves, color):
    return sorted(moves, key=lambda m: move_order_score(board, m, color), reverse=True)


def move_order_score(board, m, color):
    a, b = m[:2], m[2:4]
    pc = board.get(a, color + "P")
    score = 0

    if b in board:
        victim = board[b][1]
        attacker = pc[1]
        score += 10 * VAL[victim] - VAL[attacker]

    if len(m) > 4:
        score += VAL.get(m[4].upper(), 900)

    nb = make_move(board, m)
    if is_check(nb, other(color)):
        score += 60

    score += CENTER.get(b, 0)
    return score


def move_bonus(old, new, m, color):
    bonus = 0
    a, b = m[:2], m[2:4]
    pc = old.get(a, color + "P")

    if b in old and old[b][0] != color:
        bonus += VAL[old[b][1]] - VAL[pc[1]] // 10

    if len(m) > 4:
        bonus += VAL.get(m[4].upper(), 900) - 100

    if is_check(new, other(color)):
        bonus += 40

    # Discourage moving into attacked square with valuable non-king piece.
    if pc[1] != "K" and attacked(new, b, other(color)):
        bonus -= VAL[pc[1]] // 8

    bonus += CENTER.get(b, 0) - CENTER.get(a, 0)
    return bonus
