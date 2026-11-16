
import time

FILES = "abcdefgh"

PIECE_VALUES = {
    "K": 0,
    "Q": 900,
    "R": 500,
    "B": 330,
    "N": 320,
    "P": 100,
}

INF = 10 ** 9
MATE = 10 ** 6

EXACT = 0
LOWER = 1
UPPER = 2

DEADLINE = 0.0
NODES = 0
TT = {}
KILLERS = []
HISTORY = {}


PAWN_PST = [
     0,  0,  0,   0,   0,  0,  0,  0,
     5, 10, 10, -20, -20, 10, 10,  5,
     5, -5,-10,   0,   0,-10, -5,  5,
     0,  0,  0,  20,  20,  0,  0,  0,
     5,  5, 10,  25,  25, 10,  5,  5,
    10, 10, 20,  30,  30, 20, 10, 10,
    50, 50, 50,  50,  50, 50, 50, 50,
     0,  0,  0,   0,   0,  0,  0,  0,
]

KNIGHT_PST = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_PST = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_PST = [
     0,  0,  0,  5,  5,  0,  0,  0,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     5, 10, 10, 10, 10, 10, 10,  5,
     0,  0,  0,  5,  5,  0,  0,  0,
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -10,  5,  5,  5,  5,  5,  0,-10,
      0,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MID_PST = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

KING_END_PST = [
    -50,-30,-30,-30,-30,-30,-30,-50,
    -30,-10,  0,  0,  0,  0,-10,-30,
    -30,  0, 20, 30, 30, 20,  0,-30,
    -30,  0, 30, 40, 40, 30,  0,-30,
    -30,  0, 30, 40, 40, 30,  0,-30,
    -30,  0, 20, 30, 30, 20,  0,-30,
    -30,-10,  0,  0,  0,  0,-10,-30,
    -50,-30,-30,-30,-30,-30,-30,-50,
]

PST = {
    "P": PAWN_PST,
    "N": KNIGHT_PST,
    "B": BISHOP_PST,
    "R": ROOK_PST,
    "Q": QUEEN_PST,
}


class SearchTimeout(Exception):
    pass


def policy(pieces: dict[str, str], to_play: str) -> str:
    try:
        return _policy_impl(pieces, to_play)
    except Exception:
        try:
            board = build_board(pieces)
            side = "w" if to_play and to_play[0].lower() == "w" else "b"
            moves = generate_legal(board, side)
            if moves:
                return move_to_uci(moves[0])
            moves = generate_pseudo(board, side, False)
            if moves:
                return move_to_uci(moves[0])
        except Exception:
            pass
        return "a1a1"


def _policy_impl(pieces, to_play):
    global DEADLINE, NODES, TT, KILLERS, HISTORY

    side = "w" if to_play and to_play[0].lower() == "w" else "b"
    board = build_board(pieces)

    DEADLINE = time.perf_counter() + 0.88
    NODES = 0
    TT = {}
    KILLERS = [[] for _ in range(96)]
    HISTORY = {}

    legal = generate_legal(board, side)
    if not legal:
        pseudo = generate_pseudo(board, side, False)
        return move_to_uci(pseudo[0]) if pseudo else "a1a1"

    if len(legal) == 1:
        return move_to_uci(legal[0])

    # Safe tiny opening hint for the exact initial board only.
    book = initial_book_move(board, side, legal)
    if book is not None:
        return move_to_uci(book)

    # Immediate checkmate has absolute priority.
    opp = opposite(side)
    for m in order_moves(board, side, legal, 0, None):
        nb = make_move(board, m)
        om = generate_legal(nb, opp)
        if not om and in_check(nb, opp):
            return move_to_uci(m)

    best_move = greedy_move(board, side, legal)
    best_score = -INF

    piece_count = sum(1 for p in board if p)
    legal_count = len(legal)

    if piece_count <= 4:
        max_depth = 8
    elif piece_count <= 7:
        max_depth = 7
    elif piece_count <= 11:
        max_depth = 6
    elif piece_count <= 16 or legal_count <= 14:
        max_depth = 5
    else:
        max_depth = 4

    for depth in range(1, max_depth + 1):
        if time.perf_counter() >= DEADLINE:
            break

        cur_best = None
        cur_score = -INF
        alpha = -INF
        beta = INF
        completed = True

        moves = order_moves(board, side, legal, 0, best_move)

        try:
            for m in moves:
                if time.perf_counter() >= DEADLINE:
                    raise SearchTimeout()

                nb = make_move(board, m)
                score = -negamax(nb, opposite(side), depth - 1, -beta, -alpha, 1)

                if score > cur_score:
                    cur_score = score
                    cur_best = m

                if score > alpha:
                    alpha = score

            if cur_best is not None:
                best_move = cur_best
                best_score = cur_score

            if best_score > MATE - 10000:
                break

        except SearchTimeout:
            completed = False

        if not completed:
            break

    return move_to_uci(best_move)


def build_board(pieces):
    board = [None] * 64
    for sq, pc in pieces.items():
        if len(sq) >= 2 and pc:
            f = ord(sq[0]) - 97
            r = ord(sq[1]) - 49
            if 0 <= f < 8 and 0 <= r < 8:
                board[r * 8 + f] = pc
    return board


def initial_book_move(board, side, legal):
    start = {
        0: "wR", 1: "wN", 2: "wB", 3: "wQ", 4: "wK", 5: "wB", 6: "wN", 7: "wR",
        8: "wP", 9: "wP", 10: "wP", 11: "wP", 12: "wP", 13: "wP", 14: "wP", 15: "wP",
        48: "bP", 49: "bP", 50: "bP", 51: "bP", 52: "bP", 53: "bP", 54: "bP", 55: "bP",
        56: "bR", 57: "bN", 58: "bB", 59: "bQ", 60: "bK", 61: "bB", 62: "bN", 63: "bR",
    }
    if sum(1 for p in board if p) == 32:
        ok = True
        for i in range(64):
            if board[i] != start.get(i):
                ok = False
                break
        if ok:
            want = uci_to_move("e2e4" if side == "w" else "e7e5")
            if want in legal:
                return want
    return None


def opposite(side):
    return "b" if side == "w" else "w"


def sq_name(i):
    return FILES[i & 7] + str((i >> 3) + 1)


def move_to_uci(m):
    s = sq_name(m[0]) + sq_name(m[1])
    if m[2]:
        s += m[2]
    return s


def uci_to_move(s):
    f1 = ord(s[0]) - 97
    r1 = ord(s[1]) - 49
    f2 = ord(s[2]) - 97
    r2 = ord(s[3]) - 49
    promo = s[4].lower() if len(s) > 4 else None
    return (r1 * 8 + f1, r2 * 8 + f2, promo)


def mirror_sq(i):
    return (7 - (i >> 3)) * 8 + (i & 7)


def find_king(board, side):
    target = side + "K"
    for i, p in enumerate(board):
        if p == target:
            return i
    return -1


def in_check(board, side):
    k = find_king(board, side)
    if k < 0:
        return False
    return is_attacked(board, k, opposite(side))


def is_attacked(board, sq, by_side):
    f = sq & 7
    r = sq >> 3

    # Pawns
    if by_side == "w":
        if r > 0:
            if f > 0 and board[sq - 9] == "wP":
                return True
            if f < 7 and board[sq - 7] == "wP":
                return True
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == "bP":
                return True
            if f < 7 and board[sq + 9] == "bP":
                return True

    # Knights
    for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nf = f + df
        nr = r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            if board[nr * 8 + nf] == by_side + "N":
                return True

    # Bishops / Queens
    for df, dr in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p:
                if p[0] == by_side and (p[1] == "B" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    # Rooks / Queens
    for df, dr in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p:
                if p[0] == by_side and (p[1] == "R" or p[1] == "Q"):
                    return True
                break
            nf += df
            nr += dr

    # King
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if df == 0 and dr == 0:
                continue
            nf = f + df
            nr = r + dr
            if 0 <= nf < 8 and 0 <= nr < 8:
                if board[nr * 8 + nf] == by_side + "K":
                    return True

    return False


def generate_pseudo(board, side, tactical_only=False):
    moves = []
    enemy = opposite(side)

    for i, pc in enumerate(board):
        if not pc or pc[0] != side:
            continue

        pt = pc[1]
        f = i & 7
        r = i >> 3

        if pt == "P":
            direction = 1 if side == "w" else -1
            start_rank = 1 if side == "w" else 6
            promo_rank = 7 if side == "w" else 0
            nr = r + direction

            if 0 <= nr < 8:
                one = nr * 8 + f
                is_promo = nr == promo_rank

                if board[one] is None:
                    if is_promo:
                        for pr in ("q", "r", "b", "n"):
                            moves.append((i, one, pr))
                    elif not tactical_only:
                        moves.append((i, one, None))
                        if r == start_rank:
                            nr2 = r + 2 * direction
                            two = nr2 * 8 + f
                            if 0 <= nr2 < 8 and board[two] is None:
                                moves.append((i, two, None))

                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if target and target[0] == enemy and target[1] != "K":
                            if is_promo:
                                for pr in ("q", "r", "b", "n"):
                                    moves.append((i, to, pr))
                            else:
                                moves.append((i, to, None))

        elif pt == "N":
            for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
                nf = f + df
                nr = r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not tactical_only:
                            moves.append((i, to, None))
                    elif target[0] == enemy and target[1] != "K":
                        moves.append((i, to, None))

        elif pt == "B" or pt == "R" or pt == "Q":
            dirs = []
            if pt == "B" or pt == "Q":
                dirs += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
            if pt == "R" or pt == "Q":
                dirs += [(1, 0), (-1, 0), (0, 1), (0, -1)]

            for df, dr in dirs:
                nf = f + df
                nr = r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not tactical_only:
                            moves.append((i, to, None))
                    else:
                        if target[0] == enemy and target[1] != "K":
                            moves.append((i, to, None))
                        break
                    nf += df
                    nr += dr

        elif pt == "K":
            for df in (-1, 0, 1):
                for dr in (-1, 0, 1):
                    if df == 0 and dr == 0:
                        continue
                    nf = f + df
                    nr = r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if target is None:
                            if not tactical_only:
                                moves.append((i, to, None))
                        elif target[0] == enemy and target[1] != "K":
                            moves.append((i, to, None))

    return moves


def generate_legal(board, side, tactical_only=False):
    pseudo = generate_pseudo(board, side, tactical_only)
    ksq = find_king(board, side)
    if ksq < 0:
        return pseudo

    enemy = opposite(side)
    legal = []
    for m in pseudo:
        nb = make_move(board, m)
        moving_piece = board[m[0]]
        new_king = m[1] if moving_piece and moving_piece[1] == "K" else ksq
        if not is_attacked(nb, new_king, enemy):
            legal.append(m)

    return legal


def make_move(board, m):
    fr, to, promo = m
    nb = board.copy()
    pc = nb[fr]
    nb[fr] = None
    if promo:
        nb[to] = pc[0] + promo.upper()
    else:
        nb[to] = pc
    return nb


def move_gain(board, m):
    gain = 0
    target = board[m[1]]
    if target:
        gain += PIECE_VALUES[target[1]]
    if m[2]:
        gain += PIECE_VALUES[m[2].upper()] - PIECE_VALUES["P"]
    return gain


def is_quiet(board, m):
    return board[m[1]] is None and m[2] is None


def order_moves(board, side, moves, ply, tt_best):
    scored = []

    for m in moves:
        score = 0
        if tt_best is not None and m == tt_best:
            score += 10_000_000

        pc = board[m[0]]
        target = board[m[1]]

        if target:
            score += 1_000_000 + 10 * PIECE_VALUES[target[1]] - PIECE_VALUES[pc[1]]

        if m[2]:
            score += 900_000 + PIECE_VALUES[m[2].upper()]

        if target is None and m[2] is None:
            if ply < len(KILLERS):
                if len(KILLERS[ply]) > 0 and KILLERS[ply][0] == m:
                    score += 800_000
                elif len(KILLERS[ply]) > 1 and KILLERS[ply][1] == m:
                    score += 700_000

            score += HISTORY.get((side, m[0], m[1], m[2]), 0)

            tf = m[1] & 7
            tr = m[1] >> 3
            score += 4 * (7 - abs(2 * tf - 7) - abs(2 * tr - 7))

        scored.append((score, m))

    scored.sort(reverse=True, key=lambda x: x[0])
    return [m for _, m in scored]


def store_killer(m, ply):
    if ply >= len(KILLERS):
        return
    if m in KILLERS[ply]:
        return
    KILLERS[ply].insert(0, m)
    if len(KILLERS[ply]) > 2:
        KILLERS[ply].pop()


def negamax(board, side, depth, alpha, beta, ply):
    global NODES, TT, HISTORY

    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout()

    checked = in_check(board, side)

    if depth <= 0:
        return quiescence(board, side, alpha, beta, ply, 4)

    if checked and depth < 3:
        depth += 1

    key = (tuple(board), side)
    entry = TT.get(key)
    tt_best = None

    if entry is not None:
        ent_depth, ent_flag, ent_value, ent_best = entry
        tt_best = ent_best
        if ent_depth >= depth:
            if ent_flag == EXACT:
                return ent_value
            if ent_flag == LOWER:
                alpha = max(alpha, ent_value)
            elif ent_flag == UPPER:
                beta = min(beta, ent_value)
            if alpha >= beta:
                return ent_value

    orig_alpha = alpha
    orig_beta = beta

    moves = generate_legal(board, side)
    if not moves:
        if checked:
            return -MATE + ply
        return 0

    best_value = -INF
    best_move = None

    for m in order_moves(board, side, moves, ply, tt_best):
        nb = make_move(board, m)
        score = -negamax(nb, opposite(side), depth - 1, -beta, -alpha, ply + 1)

        if score > best_value:
            best_value = score
            best_move = m

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if is_quiet(board, m):
                store_killer(m, ply)
                HISTORY[(side, m[0], m[1], m[2])] = HISTORY.get((side, m[0], m[1], m[2]), 0) + depth * depth
            break

    if best_value <= orig_alpha:
        flag = UPPER
    elif best_value >= orig_beta:
        flag = LOWER
    else:
        flag = EXACT

    if len(TT) < 200000:
        TT[key] = (depth, flag, best_value, best_move)

    return best_value


def quiescence(board, side, alpha, beta, ply, qdepth):
    global NODES

    NODES += 1
    if (NODES & 511) == 0 and time.perf_counter() >= DEADLINE:
        raise SearchTimeout()

    checked = in_check(board, side)

    if checked:
        moves = generate_legal(board, side, False)
        if not moves:
            return -MATE + ply
        if qdepth <= 0:
            return evaluate(board, side) - 40
    else:
        stand_pat = evaluate(board, side)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        if qdepth <= 0:
            return alpha

        moves = generate_legal(board, side, True)
        if not moves:
            return alpha

    moves = order_moves(board, side, moves, ply, None)

    for m in moves:
        if not checked:
            gain = move_gain(board, m)
            if gain <= 0:
                continue
            if evaluate(board, side) + gain + 120 < alpha:
                continue

        nb = make_move(board, m)
        score = -quiescence(nb, opposite(side), -beta, -alpha, ply + 1, qdepth - 1)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def greedy_move(board, side, legal):
    best = legal[0]
    best_score = -INF
    opp = opposite(side)

    for m in legal:
        nb = make_move(board, m)
        om = generate_legal(nb, opp)

        if not om:
            score = MATE if in_check(nb, opp) else 0
        else:
            score = -evaluate(nb, opp)
            if in_check(nb, opp):
                score += 35
            score += move_gain(board, m)

        if score > best_score:
            best_score = score
            best = m

    return best


def evaluate(board, side):
    score = 0

    bishops = {"w": 0, "b": 0}
    pawns = {"w": [], "b": []}
    pawn_files = {"w": [0] * 8, "b": [0] * 8}
    kings = {"w": -1, "b": -1}
    material = {"w": 0, "b": 0}
    nonpawn_material = 0

    for i, p in enumerate(board):
        if not p:
            continue
        color = p[0]
        pt = p[1]

        if pt != "K":
            material[color] += PIECE_VALUES[pt]
        if pt != "K" and pt != "P":
            nonpawn_material += PIECE_VALUES[pt]
        if pt == "B":
            bishops[color] += 1
        elif pt == "P":
            pawns[color].append(i)
            pawn_files[color][i & 7] += 1
        elif pt == "K":
            kings[color] = i

    endgame = nonpawn_material <= 2600

    for i, p in enumerate(board):
        if not p:
            continue

        color = p[0]
        pt = p[1]
        sign = 1 if color == "w" else -1
        idx = i if color == "w" else mirror_sq(i)

        val = PIECE_VALUES[pt]

        if pt == "K":
            pst = KING_END_PST[idx] if endgame else KING_MID_PST[idx]
        else:
            pst = PST[pt][idx]

        score += sign * (val + pst)

    if bishops["w"] >= 2:
        score += 35
    if bishops["b"] >= 2:
        score -= 35

    passed_bonus = [0, 5, 12, 25, 45, 80, 135, 0]

    for color in ("w", "b"):
        sign = 1 if color == "w" else -1
        enemy = opposite(color)

        for f in range(8):
            if pawn_files[color][f] > 1:
                score -= sign * 14 * (pawn_files[color][f] - 1)

        for sq in pawns[color]:
            f = sq & 7
            r = sq >> 3

            isolated = True
            for af in (f - 1, f + 1):
                if 0 <= af < 8 and pawn_files[color][af] > 0:
                    isolated = False
                    break
            if isolated:
                score -= sign * 10

            passed = True
            for ep in pawns[enemy]:
                ef = ep & 7
                er = ep >> 3
                if abs(ef - f) <= 1:
                    if color == "w" and er > r:
                        passed = False
                        break
                    if color == "b" and er < r:
                        passed = False
                        break

            if passed:
                advance = r if color == "w" else 7 - r
                score += sign * passed_bonus[advance]

            if pawn_protected(board, color, sq):
                score += sign * 6

    if nonpawn_material > 1800:
        for color in ("w", "b"):
            k = kings[color]
            if k < 0:
                continue

            sign = 1 if color == "w" else -1
            kf = k & 7
            kr = k >> 3
            direction = 1 if color == "w" else -1
            shield = 0

            for df in (-1, 0, 1):
                ff = kf + df
                if not (0 <= ff < 8):
                    continue

                r1 = kr + direction
                r2 = kr + 2 * direction

                if 0 <= r1 < 8 and board[r1 * 8 + ff] == color + "P":
                    shield += 10
                elif 0 <= r2 < 8 and board[r2 * 8 + ff] == color + "P":
                    shield += 5

                if pawn_files[color][ff] == 0:
                    shield -= 8

            score += sign * shield

    wk = kings["w"]
    bk = kings["b"]

    if wk >= 0 and bk >= 0:
        wm = material["w"]
        bm = material["b"]
        wf = wk & 7
        wr = wk >> 3
        bf = bk & 7
        br = bk >> 3

        if wm > bm + 500:
            edge = (abs(2 * bf - 7) + abs(2 * br - 7)) * 6
            close = (14 - (abs(wf - bf) + abs(wr - br))) * 3
            score += edge + close
        elif bm > wm + 500:
            edge = (abs(2 * wf - 7) + abs(2 * wr - 7)) * 6
            close = (14 - (abs(wf - bf) + abs(wr - br))) * 3
            score -= edge + close

    return (score if side == "w" else -score) + 6


def pawn_protected(board, color, sq):
    f = sq & 7
    r = sq >> 3

    if color == "w":
        if r > 0:
            if f > 0 and board[sq - 9] == "wP":
                return True
            if f < 7 and board[sq - 7] == "wP":
                return True
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == "bP":
                return True
            if f < 7 and board[sq + 9] == "bP":
                return True

    return False
