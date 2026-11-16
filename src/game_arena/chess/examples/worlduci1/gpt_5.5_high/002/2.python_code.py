
import time

INF = 10**9
MATE = 100000
MAX_Q = 4

END_TIME = 0.0
NODES = 0
TT = {}

VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

PAWN_PST = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10,-10,-10, 10, 10,  5,
     5, -5, -5,  0,  0, -5, -5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5,  5, 10, 25, 25, 10,  5,  5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
     0,  0,  0,  0,  0,  0,  0,  0,
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
      0,  0,  0,  0,  0,  0,  0,  0,
]

QUEEN_PST = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]

KING_MG_PST = [
     20, 30, 10,  0,  0, 10, 30, 20,
     20, 20,  0,  0,  0,  0, 20, 20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
]

KING_EG_PST = [
    -50,-30,-20,-10,-10,-20,-30,-50,
    -30,-10,  0, 10, 10,  0,-10,-30,
    -20,  0, 20, 30, 30, 20,  0,-20,
    -10, 10, 30, 40, 40, 30, 10,-10,
    -10, 10, 30, 40, 40, 30, 10,-10,
    -20,  0, 20, 30, 30, 20,  0,-20,
    -30,-10,  0, 10, 10,  0,-10,-30,
    -50,-30,-20,-10,-10,-20,-30,-50,
]

PSTS = {
    "P": PAWN_PST,
    "N": KNIGHT_PST,
    "B": BISHOP_PST,
    "R": ROOK_PST,
    "Q": QUEEN_PST,
}

MIRROR = [((7 - (i >> 3)) * 8 + (i & 7)) for i in range(64)]

KNIGHT_STEPS = [
    (1, 2), (2, 1), (-1, 2), (-2, 1),
    (1, -2), (2, -1), (-1, -2), (-2, -1),
]
KING_STEPS = [
    (1, 0), (-1, 0), (0, 1), (0, -1),
    (1, 1), (1, -1), (-1, 1), (-1, -1),
]
BISHOP_DIRS = [(1, 1), (1, -1), (-1, 1), (-1, -1)]
ROOK_DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]
QUEEN_DIRS = BISHOP_DIRS + ROOK_DIRS


class SearchTimeout(Exception):
    pass


def other(color):
    return "b" if color == "w" else "w"


def sq_to_index(s):
    return (ord(s[1]) - 49) * 8 + (ord(s[0]) - 97)


def index_to_sq(i):
    return chr(97 + (i & 7)) + str((i >> 3) + 1)


def move_to_uci(m):
    a, b, promo = m
    if promo:
        return index_to_sq(a) + index_to_sq(b) + promo.lower()
    return index_to_sq(a) + index_to_sq(b)


def build_board(pieces):
    board = [None] * 64
    for sq, code in pieces.items():
        if not isinstance(sq, str) or len(sq) != 2:
            continue
        if not isinstance(code, str) or len(code) < 2:
            continue
        f = ord(sq[0]) - 97
        r = ord(sq[1]) - 49
        if not (0 <= f < 8 and 0 <= r < 8):
            continue
        typ = code[1].upper()
        if typ not in VALUES:
            continue
        board[r * 8 + f] = typ if code[0] == "w" else typ.lower()
    return board


def find_king(board, color):
    target = "K" if color == "w" else "k"
    for i, p in enumerate(board):
        if p == target:
            return i
    return None


def is_attacked(board, sq, by_color):
    f = sq & 7
    r = sq >> 3
    by_white = by_color == "w"

    pawn = "P" if by_white else "p"
    if by_white:
        rr = r - 1
        if rr >= 0:
            if f > 0 and board[rr * 8 + f - 1] == pawn:
                return True
            if f < 7 and board[rr * 8 + f + 1] == pawn:
                return True
    else:
        rr = r + 1
        if rr < 8:
            if f > 0 and board[rr * 8 + f - 1] == pawn:
                return True
            if f < 7 and board[rr * 8 + f + 1] == pawn:
                return True

    knight = "N" if by_white else "n"
    for df, dr in KNIGHT_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == knight:
            return True

    king = "K" if by_white else "k"
    for df, dr in KING_STEPS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8 and board[nr * 8 + nf] == king:
            return True

    for df, dr in ROOK_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p is not None:
                if p.isupper() == by_white and p.upper() in ("R", "Q"):
                    return True
                break
            nf += df
            nr += dr

    for df, dr in BISHOP_DIRS:
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p is not None:
                if p.isupper() == by_white and p.upper() in ("B", "Q"):
                    return True
                break
            nf += df
            nr += dr

    return False


def in_check(board, color):
    k = find_king(board, color)
    if k is None:
        return False
    return is_attacked(board, k, other(color))


def make_move(board, m):
    a, b, promo = m
    nb = board[:]
    p = nb[a]
    nb[a] = None
    if promo:
        nb[b] = promo if p is not None and p.isupper() else promo.lower()
    else:
        nb[b] = p
    return nb


def generate_pseudo(board, color, noisy_only=False):
    moves = []
    us_white = color == "w"

    for i, p in enumerate(board):
        if p is None or p.isupper() != us_white:
            continue

        typ = p.upper()
        f = i & 7
        r = i >> 3

        if typ == "P":
            dr = 1 if us_white else -1
            start_rank = 1 if us_white else 6
            promo_rank = 7 if us_white else 0
            nr = r + dr

            if 0 <= nr < 8:
                one = nr * 8 + f
                if board[one] is None:
                    if nr == promo_rank:
                        moves.append((i, one, "Q"))
                        moves.append((i, one, "R"))
                        moves.append((i, one, "B"))
                        moves.append((i, one, "N"))
                    elif not noisy_only:
                        moves.append((i, one, ""))
                        if r == start_rank:
                            two_r = r + 2 * dr
                            two = two_r * 8 + f
                            if board[two] is None:
                                moves.append((i, two, ""))

                for df in (-1, 1):
                    nf = f + df
                    if 0 <= nf < 8:
                        to = nr * 8 + nf
                        target = board[to]
                        if target is not None and target.isupper() != us_white and target.upper() != "K":
                            if nr == promo_rank:
                                moves.append((i, to, "Q"))
                                moves.append((i, to, "R"))
                                moves.append((i, to, "B"))
                                moves.append((i, to, "N"))
                            else:
                                moves.append((i, to, ""))

        elif typ == "N":
            for df, dr in KNIGHT_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not noisy_only:
                            moves.append((i, to, ""))
                    elif target.isupper() != us_white and target.upper() != "K":
                        moves.append((i, to, ""))

        elif typ in ("B", "R", "Q"):
            dirs = BISHOP_DIRS if typ == "B" else ROOK_DIRS if typ == "R" else QUEEN_DIRS
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not noisy_only:
                            moves.append((i, to, ""))
                    else:
                        if target.isupper() != us_white and target.upper() != "K":
                            moves.append((i, to, ""))
                        break
                    nf += df
                    nr += dr

        elif typ == "K":
            for df, dr in KING_STEPS:
                nf, nr = f + df, r + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not noisy_only:
                            moves.append((i, to, ""))
                    elif target.isupper() != us_white and target.upper() != "K":
                        moves.append((i, to, ""))

    return moves


def generate_legal(board, color, noisy_only=False):
    legal = []
    ksq = find_king(board, color)
    opp = other(color)

    for m in generate_pseudo(board, color, noisy_only):
        a, b, _ = m
        moving = board[a]
        nb = make_move(board, m)
        if ksq is None:
            legal.append(m)
            continue
        new_ksq = b if moving is not None and moving.upper() == "K" else ksq
        if not is_attacked(nb, new_ksq, opp):
            legal.append(m)

    return legal


def static_eval(board, color):
    nonking_material = 0
    white_material = 0
    black_material = 0
    white_bishops = 0
    black_bishops = 0
    white_pawn_files = [0] * 8
    black_pawn_files = [0] * 8
    white_pawns = []
    black_pawns = []
    wk = None
    bk = None

    for i, p in enumerate(board):
        if p is None:
            continue
        t = p.upper()
        v = VALUES[t]
        if t != "K":
            nonking_material += v
        if p.isupper():
            white_material += v
            if t == "B":
                white_bishops += 1
            elif t == "P":
                white_pawn_files[i & 7] += 1
                white_pawns.append(i)
            elif t == "K":
                wk = i
        else:
            black_material += v
            if t == "B":
                black_bishops += 1
            elif t == "P":
                black_pawn_files[i & 7] += 1
                black_pawns.append(i)
            elif t == "K":
                bk = i

    endgame = nonking_material <= 2400
    score = 0

    for i, p in enumerate(board):
        if p is None:
            continue
        t = p.upper()
        idx = i if p.isupper() else MIRROR[i]

        if t == "K":
            pst = KING_EG_PST[idx] if endgame else KING_MG_PST[idx]
        else:
            pst = PSTS[t][idx]

        val = VALUES[t] + pst
        if p.isupper():
            score += val
        else:
            score -= val

    if white_bishops >= 2:
        score += 30
    if black_bishops >= 2:
        score -= 30

    for f, c in enumerate(white_pawn_files):
        if c > 1:
            score -= 12 * (c - 1)
        if c and (f == 0 or white_pawn_files[f - 1] == 0) and (f == 7 or white_pawn_files[f + 1] == 0):
            score -= 8 * c

    for f, c in enumerate(black_pawn_files):
        if c > 1:
            score += 12 * (c - 1)
        if c and (f == 0 or black_pawn_files[f - 1] == 0) and (f == 7 or black_pawn_files[f + 1] == 0):
            score += 8 * c

    for wp in white_pawns:
        wf, wr = wp & 7, wp >> 3
        passed = True
        for bp in black_pawns:
            bf, br = bp & 7, bp >> 3
            if abs(bf - wf) <= 1 and br > wr:
                passed = False
                break
        if passed:
            score += 12 + 3 * wr * wr

    for bp in black_pawns:
        bf, br = bp & 7, bp >> 3
        passed = True
        for wp in white_pawns:
            wf, wr = wp & 7, wp >> 3
            if abs(wf - bf) <= 1 and wr < br:
                passed = False
                break
        if passed:
            adv = 7 - br
            score -= 12 + 3 * adv * adv

    if endgame and wk is not None and bk is not None:
        material_diff = white_material - black_material
        wkf, wkr = wk & 7, wk >> 3
        bkf, bkr = bk & 7, bk >> 3
        enemy_edge_black = abs(2 * bkf - 7) + abs(2 * bkr - 7)
        enemy_edge_white = abs(2 * wkf - 7) + abs(2 * wkr - 7)
        king_dist = abs(wkf - bkf) + abs(wkr - bkr)
        if material_diff > 300:
            score += 4 * enemy_edge_black + 3 * (14 - king_dist)
        elif material_diff < -300:
            score -= 4 * enemy_edge_white + 3 * (14 - king_dist)

    result = score if color == "w" else -score
    return result + 8


def move_order_score(board, m, color, tt_move=None):
    if tt_move is not None and m == tt_move:
        return 10**8

    a, b, promo = m
    p = board[a]
    target = board[b]
    score = 0

    if promo:
        score += 8000 + VALUES[promo]

    if target is not None and p is not None:
        score += 10 * VALUES[target.upper()] - VALUES[p.upper()]

    bf, br = b & 7, b >> 3
    score += 14 - (abs(2 * bf - 7) + abs(2 * br - 7))

    if p is not None and p.upper() == "P":
        score += br if color == "w" else (7 - br)

    return score


def order_moves(board, moves, color, tt_move=None):
    return sorted(moves, key=lambda m: move_order_score(board, m, color, tt_move), reverse=True)


def check_time():
    global NODES
    NODES += 1
    if (NODES & 2047) == 0 and time.perf_counter() > END_TIME:
        raise SearchTimeout()


def quiescence(board, color, alpha, beta, ply, qply):
    check_time()

    side_in_check = in_check(board, color)

    if side_in_check:
        if qply >= MAX_Q:
            return static_eval(board, color)
        moves = generate_legal(board, color, noisy_only=False)
        if not moves:
            return -MATE + ply
    else:
        stand = static_eval(board, color)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        if qply >= MAX_Q:
            return alpha
        moves = generate_legal(board, color, noisy_only=True)

    if not moves:
        return alpha

    for m in order_moves(board, moves, color):
        nb = make_move(board, m)
        score = -quiescence(nb, other(color), -beta, -alpha, ply + 1, qply + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board, color, depth, alpha, beta, ply):
    check_time()

    if depth <= 0:
        return quiescence(board, color, alpha, beta, ply, 0)

    alpha_orig = alpha
    beta_orig = beta
    key = (tuple(board), color)
    entry = TT.get(key)
    tt_move = None

    if entry is not None:
        edepth, flag, val, best_m = entry
        tt_move = best_m
        if edepth >= depth:
            if flag == 0:
                return val
            if flag == 1:
                alpha = max(alpha, val)
            elif flag == 2:
                beta = min(beta, val)
            if alpha >= beta:
                return val

    moves = generate_legal(board, color, noisy_only=False)
    if not moves:
        if in_check(board, color):
            return -MATE + ply
        return 0

    best = -INF
    best_m = None

    for m in order_moves(board, moves, color, tt_move):
        nb = make_move(board, m)
        score = -negamax(nb, other(color), depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
            best_m = m
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    if best <= alpha_orig:
        flag = 2
    elif best >= beta_orig:
        flag = 1
    else:
        flag = 0

    if len(TT) < 200000:
        TT[key] = (depth, flag, best, best_m)

    return best


def external_legal_moves():
    lm = globals().get("legal_moves")
    if lm is None:
        return []
    try:
        return [m for m in lm if isinstance(m, str)]
    except Exception:
        return []


def choose_greedy(board, moves, color):
    best = moves[0]
    best_score = -INF
    for m in moves:
        nb = make_move(board, m)
        score = -static_eval(nb, other(color)) + move_order_score(board, m, color) // 20
        if score > best_score:
            best_score = score
            best = m
    return best


def policy(pieces: dict[str, str], to_play: str) -> str:
    global END_TIME, NODES, TT

    END_TIME = time.perf_counter() + 0.85
    NODES = 0
    TT = {}

    try:
        color = "w" if str(to_play).lower().startswith("w") else "b"
        board = build_board(pieces)
        root_moves = generate_legal(board, color, noisy_only=False)

        ext = external_legal_moves()
        if ext:
            ext_set = set(ext)
            filtered = [m for m in root_moves if move_to_uci(m) in ext_set]
            if filtered:
                root_moves = filtered
            else:
                return ext[0]

        if not root_moves:
            return ext[0] if ext else ""

        if len(root_moves) == 1:
            return move_to_uci(root_moves[0])

        best_move = choose_greedy(board, root_moves, color)
        piece_count = sum(1 for p in board if p is not None)
        legal_count = len(root_moves)

        if piece_count <= 5:
            max_depth = 7
        elif piece_count <= 8:
            max_depth = 6
        elif piece_count <= 12:
            max_depth = 5
        elif legal_count <= 18:
            max_depth = 5
        else:
            max_depth = 4

        try:
            for depth in range(1, max_depth + 1):
                if time.perf_counter() > END_TIME:
                    raise SearchTimeout()

                local_best = best_move
                local_best_score = -INF
                alpha = -INF
                beta = INF

                for m in order_moves(board, root_moves, color, best_move):
                    if time.perf_counter() > END_TIME:
                        raise SearchTimeout()

                    nb = make_move(board, m)
                    score = -negamax(nb, other(color), depth - 1, -beta, -alpha, 1)

                    if score > local_best_score:
                        local_best_score = score
                        local_best = m
                    if score > alpha:
                        alpha = score

                best_move = local_best

                if local_best_score > MATE - 1000:
                    break

        except SearchTimeout:
            pass
        except Exception:
            pass

        return move_to_uci(best_move)

    except Exception:
        try:
            color = "w" if str(to_play).lower().startswith("w") else "b"
            board = build_board(pieces)
            moves = generate_legal(board, color, noisy_only=False)
            if moves:
                return move_to_uci(moves[0])
            ext = external_legal_moves()
            if ext:
                return ext[0]
        except Exception:
            pass
        return ""
