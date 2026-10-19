
import math

FILES = "abcdefgh"
PROMOS = ("q", "r", "b", "n")

VAL = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

MATE = 1000000


def policy(pieces: dict[str, str], to_play: str) -> str:
    color = "w" if to_play == "white" else "b"
    board = dict(pieces)

    moves = legal_moves(board, color)
    if not moves:
        return ""

    # Immediate mate check and root move ordering.
    ordered = sorted(moves, key=lambda m: move_score(board, m, color), reverse=True)

    opp = other(color)
    for m in ordered:
        nb = make_move(board, m)
        om = legal_moves(nb, opp)
        if not om and in_check(nb, opp):
            return m

    # Adaptive depth: deeper in simpler positions.
    n_pieces = len(board)
    n_moves = len(moves)
    if n_pieces <= 6:
        depth = 5
    elif n_pieces <= 10:
        depth = 4
    elif n_moves <= 12:
        depth = 4
    else:
        depth = 3

    best_move = ordered[0]
    best_score = -10**18
    alpha = -10**18
    beta = 10**18

    for m in ordered:
        nb = make_move(board, m)
        score = -negamax(nb, opp, depth - 1, -beta, -alpha, 1)
        if score > best_score:
            best_score = score
            best_move = m
        if score > alpha:
            alpha = score

    return best_move


def other(c):
    return "b" if c == "w" else "w"


def sq_to_xy(s):
    return ord(s[0]) - 97, ord(s[1]) - 49


def xy_to_sq(x, y):
    return chr(97 + x) + chr(49 + y)


def on_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def make_move(board, move):
    a = move[:2]
    b = move[2:4]
    pc = board[a]
    nb = board.copy()
    del nb[a]
    if b in nb:
        del nb[b]
    if len(move) > 4:
        nb[b] = pc[0] + move[4].upper()
    else:
        nb[b] = pc
    return nb


def king_square(board, color):
    target = color + "K"
    for s, p in board.items():
        if p == target:
            return s
    return None


def in_check(board, color):
    ks = king_square(board, color)
    if ks is None:
        return True
    return is_attacked(board, ks, other(color))


def is_attacked(board, sq, by_color):
    x, y = sq_to_xy(sq)

    # Pawn attacks.
    if by_color == "w":
        for dx in (-1, 1):
            sx, sy = x - dx, y - 1
            if on_board(sx, sy) and board.get(xy_to_sq(sx, sy)) == "wP":
                return True
    else:
        for dx in (-1, 1):
            sx, sy = x - dx, y + 1
            if on_board(sx, sy) and board.get(xy_to_sq(sx, sy)) == "bP":
                return True

    # Knight attacks.
    for dx, dy in ((1, 2), (2, 1), (-1, 2), (-2, 1),
                   (1, -2), (2, -1), (-1, -2), (-2, -1)):
        nx, ny = x + dx, y + dy
        if on_board(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + "N":
            return True

    # King attacks.
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if on_board(nx, ny) and board.get(xy_to_sq(nx, ny)) == by_color + "K":
                return True

    # Sliding attacks.
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and p[1] in ("R", "Q"):
                    return True
                break
            nx += dx
            ny += dy

    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and p[1] in ("B", "Q"):
                    return True
                break
            nx += dx
            ny += dy

    return False


def legal_moves(board, color, captures_only=False):
    out = []
    for sq, pc in list(board.items()):
        if pc[0] != color:
            continue
        for m in pseudo_moves_for_piece(board, sq, pc, captures_only):
            nb = make_move(board, m)
            if not in_check(nb, color):
                out.append(m)
    return out


def pseudo_moves_for_piece(board, sq, pc, captures_only=False):
    color, pt = pc[0], pc[1]
    enemy = other(color)
    x, y = sq_to_xy(sq)
    moves = []

    def add_move(nx, ny, promo=False):
        if not on_board(nx, ny):
            return
        to = xy_to_sq(nx, ny)
        target = board.get(to)
        if target and target[0] == color:
            return
        if target and target[1] == "K":
            return
        if captures_only and not target and not promo:
            return
        if promo:
            for pr in PROMOS:
                moves.append(sq + to + pr)
        else:
            moves.append(sq + to)

    if pt == "P":
        direction = 1 if color == "w" else -1
        start_rank = 1 if color == "w" else 6
        promo_rank = 7 if color == "w" else 0

        # Captures.
        for dx in (-1, 1):
            nx, ny = x + dx, y + direction
            if on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                target = board.get(to)
                if target and target[0] == enemy and target[1] != "K":
                    add_move(nx, ny, ny == promo_rank)

        # Quiet pushes, including quiet promotions.
        if not captures_only:
            nx, ny = x, y + direction
            if on_board(nx, ny) and xy_to_sq(nx, ny) not in board:
                add_move(nx, ny, ny == promo_rank)
                if y == start_rank:
                    ny2 = y + 2 * direction
                    if on_board(x, ny2) and xy_to_sq(x, ny2) not in board:
                        add_move(x, ny2, False)
        else:
            # Quiet promotion is tactically important in quiescence.
            nx, ny = x, y + direction
            if on_board(nx, ny) and ny == promo_rank and xy_to_sq(nx, ny) not in board:
                add_move(nx, ny, True)

    elif pt == "N":
        for dx, dy in ((1, 2), (2, 1), (-1, 2), (-2, 1),
                       (1, -2), (2, -1), (-1, -2), (-2, -1)):
            add_move(x + dx, y + dy)

    elif pt in ("B", "R", "Q"):
        dirs = []
        if pt in ("B", "Q"):
            dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        if pt in ("R", "Q"):
            dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            while on_board(nx, ny):
                to = xy_to_sq(nx, ny)
                target = board.get(to)
                if target:
                    if target[0] != color and target[1] != "K":
                        if not captures_only or target:
                            moves.append(sq + to)
                    break
                else:
                    if not captures_only:
                        moves.append(sq + to)
                nx += dx
                ny += dy

    elif pt == "K":
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                add_move(x + dx, y + dy)

        # Castling is intentionally omitted because castling rights are not
        # present in the input state. Returning an illegal castle would lose.

    return moves


def negamax(board, color, depth, alpha, beta, ply):
    if depth <= 0:
        if in_check(board, color):
            depth = 1
        else:
            return quiescence(board, color, alpha, beta, 4)

    moves = legal_moves(board, color)
    if not moves:
        if in_check(board, color):
            return -MATE + ply
        return 0

    moves.sort(key=lambda m: move_score(board, m, color), reverse=True)

    best = -10**18
    opp = other(color)

    for m in moves:
        nb = make_move(board, m)
        score = -negamax(nb, opp, depth - 1, -beta, -alpha, ply + 1)
        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return best


def quiescence(board, color, alpha, beta, qdepth):
    stand = evaluate(board, color)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    if qdepth <= 0:
        return alpha

    moves = legal_moves(board, color, captures_only=True)
    if not moves:
        return alpha

    moves.sort(key=lambda m: move_score(board, m, color), reverse=True)
    opp = other(color)

    for m in moves:
        nb = make_move(board, m)
        score = -quiescence(nb, opp, -beta, -alpha, qdepth - 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def move_score(board, move, color):
    frm = move[:2]
    to = move[2:4]
    pc = board.get(frm, color + "P")
    target = board.get(to)
    score = 0

    if target:
        score += 10000 + VAL[target[1]] * 10 - VAL[pc[1]]

    if len(move) > 4:
        promo = move[4].upper()
        score += 8000 + VAL[promo]

    # Prefer checking moves a little.
    try:
        nb = make_move(board, move)
        if in_check(nb, other(color)):
            score += 250
    except Exception:
        pass

    # Mild central preference for quiet moves.
    x, y = sq_to_xy(to)
    score += int(10 - ((x - 3.5) ** 2 + (y - 3.5) ** 2))

    return score


def evaluate(board, color):
    white_score = 0
    black_score = 0
    white_bishops = 0
    black_bishops = 0
    white_pawns_by_file = [0] * 8
    black_pawns_by_file = [0] * 8
    total_nonking_material = 0

    for sq, pc in board.items():
        c, pt = pc[0], pc[1]
        if pt != "K":
            total_nonking_material += VAL[pt]
        if pt == "P":
            x, _ = sq_to_xy(sq)
            if c == "w":
                white_pawns_by_file[x] += 1
            else:
                black_pawns_by_file[x] += 1
        if pt == "B":
            if c == "w":
                white_bishops += 1
            else:
                black_bishops += 1

    endgame = total_nonking_material <= 1800

    for sq, pc in board.items():
        c, pt = pc[0], pc[1]
        x, y = sq_to_xy(sq)
        val = VAL[pt] + piece_square_value(pt, x, y, c, endgame)

        if pt == "P":
            files = white_pawns_by_file if c == "w" else black_pawns_by_file
            enemy_files = black_pawns_by_file if c == "w" else white_pawns_by_file
            val += pawn_structure_bonus(x, y, c, files, enemy_files)

        if pt == "K":
            val += king_safety(board, sq, c, endgame)

        if c == "w":
            white_score += val
        else:
            black_score += val

    if white_bishops >= 2:
        white_score += 30
    if black_bishops >= 2:
        black_score += 30

    abs_score = white_score - black_score
    return abs_score if color == "w" else -abs_score


def piece_square_value(pt, x, y, color, endgame):
    # yy is rank from own side: 0 home rank, 7 promotion rank.
    yy = y if color == "w" else 7 - y
    center = 14 - int(4 * ((x - 3.5) ** 2 + (y - 3.5) ** 2))

    if pt == "P":
        return yy * 10 + max(0, center // 2)
    if pt == "N":
        return center * 3 - 10
    if pt == "B":
        return center * 2 + 5
    if pt == "R":
        return yy * 3 + (15 if yy == 6 else 0)
    if pt == "Q":
        return center
    if pt == "K":
        if endgame:
            return center * 3
        # In middlegame, prefer staying near home rank and away from center.
        home_bonus = 25 if yy == 0 else (10 if yy == 1 else -15 * yy)
        edge_bonus = int(abs(x - 3.5) * 4)
        return home_bonus + edge_bonus - max(0, center)
    return 0


def pawn_structure_bonus(x, y, color, own_files, enemy_files):
    bonus = 0

    # Doubled pawns.
    if own_files[x] > 1:
        bonus -= 12 * (own_files[x] - 1)

    # Isolated pawns.
    left = own_files[x - 1] if x > 0 else 0
    right = own_files[x + 1] if x < 7 else 0
    if left == 0 and right == 0:
        bonus -= 10

    # Passed pawn approximation.
    passed = True
    for fx in (x - 1, x, x + 1):
        if 0 <= fx < 8 and enemy_files[fx] > 0:
            # Without exact enemy pawn ranks in this helper, keep it conservative.
            passed = False
            break
    if passed:
        advance = y if color == "w" else 7 - y
        bonus += 15 + advance * 8

    return bonus


def king_safety(board, sq, color, endgame):
    if endgame:
        return 0

    x, y = sq_to_xy(sq)
    shield = 0
    direction = 1 if color == "w" else -1

    for dx in (-1, 0, 1):
        for dy in (direction, 2 * direction):
            nx, ny = x + dx, y + dy
            if on_board(nx, ny):
                p = board.get(xy_to_sq(nx, ny))
                if p == color + "P":
                    shield += 6 if abs(dx) <= 1 else 3

    return shield
