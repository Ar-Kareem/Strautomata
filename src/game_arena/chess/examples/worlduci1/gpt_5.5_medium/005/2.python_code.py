
import time

FILES = "abcdefgh"
INF = 10**9
MATE = 10**7

PIECE_VALUE = {
    "K": 0,
    "Q": 900,
    "R": 500,
    "B": 330,
    "N": 320,
    "P": 100,
}

PROMOS = ["q", "r", "b", "n"]


class SearchTimeout(Exception):
    pass


def opp(color):
    return "b" if color == "w" else "w"


def to_color(to_play):
    return "w" if to_play == "white" else "b"


def sq_to_xy(sq):
    return ord(sq[0]) - 97, ord(sq[1]) - 49


def xy_to_sq(x, y):
    return chr(97 + x) + chr(49 + y)


def on_board(x, y):
    return 0 <= x < 8 and 0 <= y < 8


def make_move(board, move):
    nb = board.copy()
    frm = move[:2]
    to = move[2:4]
    promo = move[4] if len(move) > 4 else ""

    if frm not in nb:
        return nb

    piece = nb[frm]
    color = piece[0]
    ptype = piece[1]
    fx, fy = sq_to_xy(frm)
    tx, ty = sq_to_xy(to)

    del nb[frm]

    # En passant capture, if the arena supplies such a legal move.
    if ptype == "P" and fx != tx and to not in board:
        cap_sq = xy_to_sq(tx, fy)
        nb.pop(cap_sq, None)

    # Castling, if the arena supplies such a legal move.
    if ptype == "K" and abs(tx - fx) == 2:
        rank = frm[1]
        if tx > fx:
            rook_from = "h" + rank
            rook_to = "f" + rank
        else:
            rook_from = "a" + rank
            rook_to = "d" + rank
        if rook_from in nb:
            rook_piece = nb.pop(rook_from)
            nb[rook_to] = rook_piece

    if promo:
        piece = color + promo.upper()

    nb[to] = piece
    return nb


def is_attacked(board, sq, by_color):
    x, y = sq_to_xy(sq)

    # Pawn attacks.
    if by_color == "w":
        for dx in (-1, 1):
            px, py = x + dx, y - 1
            if on_board(px, py) and board.get(xy_to_sq(px, py)) == "wP":
                return True
    else:
        for dx in (-1, 1):
            px, py = x + dx, y + 1
            if on_board(px, py) and board.get(xy_to_sq(px, py)) == "bP":
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
    for dx, dy, attackers in (
        (1, 0, "RQ"), (-1, 0, "RQ"), (0, 1, "RQ"), (0, -1, "RQ"),
        (1, 1, "BQ"), (1, -1, "BQ"), (-1, 1, "BQ"), (-1, -1, "BQ")
    ):
        nx, ny = x + dx, y + dy
        while on_board(nx, ny):
            p = board.get(xy_to_sq(nx, ny))
            if p:
                if p[0] == by_color and p[1] in attackers:
                    return True
                break
            nx += dx
            ny += dy

    return False


def king_square(board, color):
    target = color + "K"
    for sq, p in board.items():
        if p == target:
            return sq
    return None


def in_check(board, color):
    ksq = king_square(board, color)
    if ksq is None:
        return True
    return is_attacked(board, ksq, opp(color))


def pseudo_moves(board, color, include_castling=False):
    moves = []
    enemy = opp(color)

    for sq, piece in list(board.items()):
        if piece[0] != color:
            continue

        x, y = sq_to_xy(sq)
        p = piece[1]

        if p == "P":
            direction = 1 if color == "w" else -1
            start_rank = 1 if color == "w" else 6
            promo_rank = 7 if color == "w" else 0

            ny = y + direction
            if on_board(x, ny):
                one = xy_to_sq(x, ny)
                if one not in board:
                    if ny == promo_rank:
                        for pr in PROMOS:
                            moves.append(sq + one + pr)
                    else:
                        moves.append(sq + one)
                        if y == start_rank:
                            ny2 = y + 2 * direction
                            two = xy_to_sq(x, ny2)
                            if on_board(x, ny2) and two not in board:
                                moves.append(sq + two)

            for dx in (-1, 1):
                nx, ny = x + dx, y + direction
                if not on_board(nx, ny):
                    continue
                to = xy_to_sq(nx, ny)
                target = board.get(to)
                if target and target[0] == enemy and target[1] != "K":
                    if ny == promo_rank:
                        for pr in PROMOS:
                            moves.append(sq + to + pr)
                    else:
                        moves.append(sq + to)

        elif p == "N":
            for dx, dy in ((1, 2), (2, 1), (-1, 2), (-2, 1),
                           (1, -2), (2, -1), (-1, -2), (-2, -1)):
                nx, ny = x + dx, y + dy
                if not on_board(nx, ny):
                    continue
                to = xy_to_sq(nx, ny)
                target = board.get(to)
                if not target or (target[0] == enemy and target[1] != "K"):
                    moves.append(sq + to)

        elif p in ("B", "R", "Q"):
            dirs = []
            if p in ("B", "Q"):
                dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            if p in ("R", "Q"):
                dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]

            for dx, dy in dirs:
                nx, ny = x + dx, y + dy
                while on_board(nx, ny):
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if not target:
                        moves.append(sq + to)
                    else:
                        if target[0] == enemy and target[1] != "K":
                            moves.append(sq + to)
                        break
                    nx += dx
                    ny += dy

        elif p == "K":
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if not on_board(nx, ny):
                        continue
                    to = xy_to_sq(nx, ny)
                    target = board.get(to)
                    if not target or (target[0] == enemy and target[1] != "K"):
                        moves.append(sq + to)

    if include_castling:
        add_castles(board, color, moves)

    return moves


def add_castles(board, color, moves):
    enemy = opp(color)
    if color == "w":
        ksq = "e1"
        rank = "1"
    else:
        ksq = "e8"
        rank = "8"

    if board.get(ksq) != color + "K":
        return
    if in_check(board, color):
        return

    # Kingside.
    if board.get("h" + rank) == color + "R":
        f = "f" + rank
        g = "g" + rank
        if f not in board and g not in board:
            if not is_attacked(board, f, enemy) and not is_attacked(board, g, enemy):
                moves.append(ksq + g)

    # Queenside.
    if board.get("a" + rank) == color + "R":
        b = "b" + rank
        c = "c" + rank
        d = "d" + rank
        if b not in board and c not in board and d not in board:
            if not is_attacked(board, d, enemy) and not is_attacked(board, c, enemy):
                moves.append(ksq + c)


def legal_moves_generated(board, color, include_castling=False):
    legal = []
    for m in pseudo_moves(board, color, include_castling):
        nb = make_move(board, m)
        if not in_check(nb, color):
            legal.append(m)
    return legal


def nonking_material(board):
    s = 0
    for p in board.values():
        if p[1] != "K":
            s += PIECE_VALUE[p[1]]
    return s


def piece_square_bonus(board, sq, piece, endgame):
    color, p = piece[0], piece[1]
    x, y = sq_to_xy(sq)
    rank_from_home = y if color == "w" else 7 - y
    center_file = 3.5 - abs(x - 3.5)
    center_rank = 3.5 - abs(y - 3.5)
    center = center_file + center_rank

    if p == "P":
        bonus = rank_from_home * 8 + center_file * 4
        # Passed pawn bonus.
        enemy = opp(color)
        passed = True
        direction = 1 if color == "w" else -1
        for fx in (x - 1, x, x + 1):
            if not 0 <= fx < 8:
                continue
            yy = y + direction
            while 0 <= yy < 8:
                if board.get(xy_to_sq(fx, yy)) == enemy + "P":
                    passed = False
                    break
                yy += direction
            if not passed:
                break
        if passed:
            bonus += rank_from_home * rank_from_home * 5
        return bonus

    if p == "N":
        return center * 12 - (18 if x in (0, 7) or y in (0, 7) else 0)

    if p == "B":
        return center * 7

    if p == "R":
        bonus = 0
        if rank_from_home == 6:
            bonus += 18
        friendly_pawn = False
        enemy_pawn = False
        for yy in range(8):
            q = board.get(xy_to_sq(x, yy))
            if q == color + "P":
                friendly_pawn = True
            elif q == opp(color) + "P":
                enemy_pawn = True
        if not friendly_pawn:
            bonus += 15 if not enemy_pawn else 8
        return bonus

    if p == "Q":
        return center * 3

    if p == "K":
        if endgame:
            return center * 14
        bonus = 0
        # Prefer safer edge/back-rank king in middlegame.
        bonus += (7 - rank_from_home) * 4
        bonus += (abs(x - 3.5)) * 3

        # Pawn shield.
        direction = 1 if color == "w" else -1
        shield_rank = y + direction
        if 0 <= shield_rank < 8:
            for fx in (x - 1, x, x + 1):
                if 0 <= fx < 8 and board.get(xy_to_sq(fx, shield_rank)) == color + "P":
                    bonus += 10
        return bonus

    return 0


def static_eval(board, color):
    mat = nonking_material(board)
    endgame = mat <= 1700
    score = 0

    for sq, piece in board.items():
        val = PIECE_VALUE[piece[1]]
        val += piece_square_bonus(board, sq, piece, endgame)
        if piece[0] == color:
            score += val
        else:
            score -= val

    # Bishop pair.
    own_bishops = sum(1 for p in board.values() if p == color + "B")
    opp_bishops = sum(1 for p in board.values() if p == opp(color) + "B")
    if own_bishops >= 2:
        score += 35
    if opp_bishops >= 2:
        score -= 35

    return int(score)


def move_order_score(board, move, color):
    frm = move[:2]
    to = move[2:4]
    if frm not in board:
        return -999999

    piece = board[frm]
    score = 0
    target = board.get(to)

    if target and target[0] != color:
        score += 10 * PIECE_VALUE[target[1]] - PIECE_VALUE[piece[1]]

    # Likely en passant capture.
    fx, fy = sq_to_xy(frm)
    tx, ty = sq_to_xy(to)
    if piece[1] == "P" and fx != tx and target is None:
        score += 10 * PIECE_VALUE["P"] - PIECE_VALUE["P"]

    if len(move) > 4:
        score += PIECE_VALUE.get(move[4].upper(), 0) - PIECE_VALUE["P"] + 700
        if move[4] == "q":
            score += 60

    # Prefer central and checking-looking moves slightly.
    score += int((3.5 - abs(tx - 3.5)) + (3.5 - abs(ty - 3.5)))

    return score


def ordered_moves(board, moves, color):
    return sorted(moves, key=lambda m: move_order_score(board, m, color), reverse=True)


def capture_or_promo(board, move):
    frm = move[:2]
    to = move[2:4]
    if len(move) > 4:
        return True
    if to in board:
        return True
    if frm in board and board[frm][1] == "P":
        fx, fy = sq_to_xy(frm)
        tx, ty = sq_to_xy(to)
        if fx != tx:
            return True
    return False


def policy(pieces: dict[str, str], to_play: str) -> str:
    board = dict(pieces)
    color = to_color(to_play)

    # If the arena exposes legal_moves globally, obey it at the root.
    supplied = None
    for name in ("legal_moves", "LEGAL_MOVES", "moves", "MOVES"):
        obj = globals().get(name)
        if isinstance(obj, (list, tuple, set)) and all(isinstance(x, str) for x in obj):
            supplied = list(obj)
            break

    if supplied:
        root_moves = supplied[:]
    else:
        # Avoid choosing castling without explicit rights. If no move is found,
        # allow castling as a last-resort reconstruction from the position.
        root_moves = legal_moves_generated(board, color, include_castling=False)
        if not root_moves:
            root_moves = legal_moves_generated(board, color, include_castling=True)

    if not root_moves:
        # Terminal positions should not be queried. This is only a defensive fallback.
        pm = pseudo_moves(board, color, include_castling=False)
        return pm[0] if pm else "a1a1"

    if len(root_moves) == 1:
        return root_moves[0]

    deadline = time.perf_counter() + 0.88
    nodes = [0]
    tt = {}

    def time_check():
        nodes[0] += 1
        if (nodes[0] & 2047) == 0 and time.perf_counter() > deadline:
            raise SearchTimeout()

    def qsearch(bd, side, alpha, beta, ply, qply):
        time_check()

        if qply >= 6:
            return static_eval(bd, side)

        if in_check(bd, side):
            lm = legal_moves_generated(bd, side, include_castling=False)
            if not lm:
                return -MATE + ply
            best = -INF
            for m in ordered_moves(bd, lm, side):
                val = -qsearch(make_move(bd, m), opp(side), -beta, -alpha, ply + 1, qply + 1)
                if val > best:
                    best = val
                if val > alpha:
                    alpha = val
                if alpha >= beta:
                    break
            return best

        stand = static_eval(bd, side)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand

        lm = legal_moves_generated(bd, side, include_castling=False)
        noisy = [m for m in lm if capture_or_promo(bd, m)]
        for m in ordered_moves(bd, noisy, side):
            val = -qsearch(make_move(bd, m), opp(side), -beta, -alpha, ply + 1, qply + 1)
            if val >= beta:
                return beta
            if val > alpha:
                alpha = val
        return alpha

    def negamax(bd, side, depth, alpha, beta, ply):
        time_check()

        key = (side, depth, tuple(sorted(bd.items())))
        entry = tt.get(key)
        if entry is not None:
            edepth, evalv, flag = entry
            if edepth >= depth:
                if flag == 0:
                    return evalv
                if flag == 1 and evalv <= alpha:
                    return evalv
                if flag == 2 and evalv >= beta:
                    return evalv

        orig_alpha = alpha

        if depth <= 0:
            return qsearch(bd, side, alpha, beta, ply, 0)

        lm = legal_moves_generated(bd, side, include_castling=False)
        if not lm:
            if in_check(bd, side):
                return -MATE + ply
            return 0

        best = -INF
        for m in ordered_moves(bd, lm, side):
            val = -negamax(make_move(bd, m), opp(side), depth - 1, -beta, -alpha, ply + 1)
            if val > best:
                best = val
            if val > alpha:
                alpha = val
            if alpha >= beta:
                break

        flag = 0
        if best <= orig_alpha:
            flag = 1
        elif best >= beta:
            flag = 2
        tt[key] = (depth, best, flag)
        return best

    best_move = ordered_moves(board, root_moves, color)[0]
    ordered_root = ordered_moves(board, root_moves, color)

    piece_count = len(board)
    max_depth = 5
    if piece_count <= 8:
        max_depth = 7
    elif piece_count <= 14:
        max_depth = 6
    elif len(root_moves) > 35:
        max_depth = 4

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break

            current_best = best_move
            current_score = -INF
            alpha = -INF
            beta = INF

            # Principal variation first.
            if best_move in ordered_root:
                ordered_root = [best_move] + [m for m in ordered_root if m != best_move]

            for m in ordered_root:
                nb = make_move(board, m)
                val = -negamax(nb, opp(color), depth - 1, -beta, -alpha, 1)

                if val > current_score:
                    current_score = val
                    current_best = m

                if val > alpha:
                    alpha = val

            best_move = current_best

            # No need to search further after finding a forced immediate mate.
            if current_score > MATE // 2:
                break

    except SearchTimeout:
        pass
    except Exception:
        return root_moves[0]

    return best_move
