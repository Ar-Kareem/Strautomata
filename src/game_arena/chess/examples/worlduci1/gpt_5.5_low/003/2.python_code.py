
import math
import time

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

DIRS_BISHOP = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
DIRS_ROOK = [(1, 0), (-1, 0), (0, 1), (0, -1)]
DIRS_QUEEN = DIRS_BISHOP + DIRS_ROOK
KNIGHT_DIRS = [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)]
KING_DIRS = DIRS_QUEEN

CENTER = {"d4", "e4", "d5", "e5"}
EXT_CENTER = {"c3", "d3", "e3", "f3", "c4", "f4", "c5", "f5", "c6", "d6", "e6", "f6"}

START_TIME = 0.0
TIME_LIMIT = 0.85


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


def move_piece(board, move):
    b = dict(board)
    frm, to = move[:2], move[2:4]
    pc = b.pop(frm)
    if len(move) == 5:
        pc = pc[0] + move[4].upper()
    b[to] = pc
    return b


def king_square(board, color):
    k = color + "K"
    for s, p in board.items():
        if p == k:
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

    # King
    for dx, dy in KING_DIRS:
        x, y = tx + dx, ty + dy
        if inside(x, y) and board.get(xy_to_sq(x, y)) == attacker + "K":
            return True

    # Sliders
    for dx, dy in DIRS_BISHOP:
        x, y = tx + dx, ty + dy
        while inside(x, y):
            p = board.get(xy_to_sq(x, y))
            if p:
                if p[0] == attacker and p[1] in ("B", "Q"):
                    return True
                break
            x += dx
            y += dy

    for dx, dy in DIRS_ROOK:
        x, y = tx + dx, ty + dy
        while inside(x, y):
            p = board.get(xy_to_sq(x, y))
            if p:
                if p[0] == attacker and p[1] in ("R", "Q"):
                    return True
                break
            x += dx
            y += dy

    return False


def in_check(board, color):
    ks = king_square(board, color)
    if ks is None:
        return True
    return attacked_by(board, ks, other(color))


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

            ny = y + step
            if inside(x, ny):
                ns = xy_to_sq(x, ny)
                if ns not in board:
                    if ny == promo_rank:
                        for pr in "qrbn":
                            moves.append(s + ns + pr)
                    else:
                        moves.append(s + ns)
                        if y == start_rank:
                            ny2 = y + 2 * step
                            ns2 = xy_to_sq(x, ny2)
                            if ns2 not in board:
                                moves.append(s + ns2)

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

        elif typ in ("B", "R", "Q"):
            dirs = DIRS_BISHOP if typ == "B" else DIRS_ROOK if typ == "R" else DIRS_QUEEN
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

        elif typ == "K":
            for dx, dy in KING_DIRS:
                nx, ny = x + dx, y + dy
                if inside(nx, ny):
                    ns = xy_to_sq(nx, ny)
                    if ns not in board or board[ns][0] != color:
                        moves.append(s + ns)

            # Conservative castling support when initial pieces/empty path allow it.
            if color == "w" and s == "e1" and not in_check(board, color):
                if board.get("h1") == "wR" and "f1" not in board and "g1" not in board:
                    if not attacked_by(board, "f1", "b") and not attacked_by(board, "g1", "b"):
                        moves.append("e1g1")
                if board.get("a1") == "wR" and "b1" not in board and "c1" not in board and "d1" not in board:
                    if not attacked_by(board, "d1", "b") and not attacked_by(board, "c1", "b"):
                        moves.append("e1c1")
            if color == "b" and s == "e8" and not in_check(board, color):
                if board.get("h8") == "bR" and "f8" not in board and "g8" not in board:
                    if not attacked_by(board, "f8", "w") and not attacked_by(board, "g8", "w"):
                        moves.append("e8g8")
                if board.get("a8") == "bR" and "b8" not in board and "c8" not in board and "d8" not in board:
                    if not attacked_by(board, "d8", "w") and not attacked_by(board, "c8", "w"):
                        moves.append("e8c8")

    return moves


def apply_move(board, move):
    b = dict(board)
    frm, to = move[:2], move[2:4]
    pc = b.pop(frm)

    # Move rook for castling.
    if pc[1] == "K" and abs(FILES.index(to[0]) - FILES.index(frm[0])) == 2:
        if to[0] == "g":
            rf, rt = "h" + frm[1], "f" + frm[1]
        else:
            rf, rt = "a" + frm[1], "d" + frm[1]
        if rf in b:
            b[rt] = b.pop(rf)

    if len(move) == 5:
        pc = pc[0] + move[4].upper()
    b[to] = pc
    return b


def legal_moves(board, color):
    res = []
    for m in pseudo_moves(board, color):
        nb = apply_move(board, m)
        if not in_check(nb, color):
            res.append(m)
    return res


def evaluate(board, me):
    opp = other(me)
    score = 0

    for s, p in board.items():
        c, t = p[0], p[1]
        v = VAL[t]
        x, y = sq_to_xy(s)

        # Positional nudges.
        if s in CENTER:
            v += 18 if t != "K" else 0
        elif s in EXT_CENTER:
            v += 8 if t != "K" else 0

        if t == "P":
            advance = y if c == "w" else 7 - y
            v += advance * 6
            if x in (3, 4):
                v += 8
        elif t == "N":
            v -= (abs(x - 3.5) + abs(y - 3.5)) * 5
        elif t == "B":
            v += 8
        elif t == "K":
            # In endgames centralize king, otherwise prefer relative safety.
            material = sum(VAL[q[1]] for q in board.values() if q[1] != "K")
            if material < 2400:
                v -= (abs(x - 3.5) + abs(y - 3.5)) * 6
            else:
                home = 0 if c == "w" else 7
                v -= abs(y - home) * 10

        score += v if c == me else -v

    if in_check(board, opp):
        score += 35
    if in_check(board, me):
        score -= 45

    return score


def move_order_score(board, move, color):
    frm, to = move[:2], move[2:4]
    pc = board.get(frm, color + "P")
    score = 0
    if to in board:
        score += 10 * VAL[board[to][1]] - VAL[pc[1]]
    if len(move) == 5:
        score += VAL[move[4].upper()]
    if to in CENTER:
        score += 20
    elif to in EXT_CENTER:
        score += 8
    return score


def search(board, color, me, depth, alpha, beta):
    if time.time() - START_TIME > TIME_LIMIT:
        return evaluate(board, me)

    moves = legal_moves(board, color)
    if not moves:
        if in_check(board, color):
            return -1000000 - depth if color == me else 1000000 + depth
        return 0

    if depth <= 0:
        return evaluate(board, me)

    moves.sort(key=lambda m: move_order_score(board, m, color), reverse=True)

    if color == me:
        best = -10**9
        for m in moves:
            val = search(apply_move(board, m), other(color), me, depth - 1, alpha, beta)
            if val > best:
                best = val
            alpha = max(alpha, best)
            if alpha >= beta:
                break
        return best
    else:
        best = 10**9
        for m in moves:
            val = search(apply_move(board, m), other(color), me, depth - 1, alpha, beta)
            if val < best:
                best = val
            beta = min(beta, best)
            if alpha >= beta:
                break
        return best


def policy(pieces: dict[str, str], to_play: str) -> str:
    global START_TIME
    START_TIME = time.time()

    me = color_code(to_play)
    board = dict(pieces)
    moves = legal_moves(board, me)

    # Absolute fallback; should only happen in checkmate/stalemate-like invalid API states.
    if not moves:
        for s, p in board.items():
            if p[0] == me:
                x, y = sq_to_xy(s)
                for dx, dy in KING_DIRS + KNIGHT_DIRS:
                    nx, ny = x + dx, y + dy
                    if inside(nx, ny):
                        return s + xy_to_sq(nx, ny)
        return "a1a1"

    # Immediate mate.
    for m in sorted(moves, key=lambda z: move_order_score(board, z, me), reverse=True):
        nb = apply_move(board, m)
        om = legal_moves(nb, other(me))
        if not om and in_check(nb, other(me)):
            return m

    best_move = moves[0]
    best_val = -10**9

    # Adaptive depth: small positions can search deeper.
    n = len(board)
    depth = 3 if n > 10 else 4
    if n <= 6:
        depth = 5

    ordered = sorted(moves, key=lambda z: move_order_score(board, z, me), reverse=True)

    for m in ordered:
        if time.time() - START_TIME > TIME_LIMIT:
            break
        nb = apply_move(board, m)
        val = search(nb, other(me), me, depth - 1, -10**9, 10**9)

        # Tiny deterministic tie-breaker favoring useful forcing moves.
        val += move_order_score(board, m, me) * 0.01

        if val > best_val:
            best_val = val
            best_move = m

    return best_move
