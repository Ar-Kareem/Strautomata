
import time
import random

INF = 10**9
MATE = 100000
MAX_PLY = 96

FILES = "abcdefgh"
PROMOTIONS = (5, 4, 3, 2)  # Q, R, B, N
PROMO_TO_CHAR = {5: "q", 4: "r", 3: "b", 2: "n"}

PIECE_FROM_CHAR = {"P": 1, "N": 2, "B": 3, "R": 4, "Q": 5, "K": 6}
PIECE_VALUE = [0, 100, 320, 335, 500, 900, 0]

PAWN_PST = [
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10, -20, -20,  10,  10,   5,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,   5,  10,  25,  25,  10,   5,   5,
    10,  10,  20,  30,  30,  20,  10,  10,
    50,  50,  50,  50,  50,  50,  50,  50,
     0,   0,   0,   0,   0,   0,   0,   0,
]

KNIGHT_PST = [
   -50, -40, -30, -30, -30, -30, -40, -50,
   -40, -20,   0,   0,   0,   0, -20, -40,
   -30,   0,  10,  15,  15,  10,   0, -30,
   -30,   5,  15,  20,  20,  15,   5, -30,
   -30,   0,  15,  20,  20,  15,   0, -30,
   -30,   5,  10,  15,  15,  10,   5, -30,
   -40, -20,   0,   5,   5,   0, -20, -40,
   -50, -40, -30, -30, -30, -30, -40, -50,
]

BISHOP_PST = [
   -20, -10, -10, -10, -10, -10, -10, -20,
   -10,   5,   0,   0,   0,   0,   5, -10,
   -10,  10,  10,  10,  10,  10,  10, -10,
   -10,   0,  10,  10,  10,  10,   0, -10,
   -10,   5,   5,  10,  10,   5,   5, -10,
   -10,   0,   5,  10,  10,   5,   0, -10,
   -10,   0,   0,   0,   0,   0,   0, -10,
   -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_PST = [
     0,   0,   0,   5,   5,   0,   0,   0,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     5,  10,  10,  10,  10,  10,  10,   5,
     0,   0,   0,   0,   0,   0,   0,   0,
]

QUEEN_PST = [
   -20, -10, -10,  -5,  -5, -10, -10, -20,
   -10,   0,   0,   0,   0,   0,   0, -10,
   -10,   0,   5,   5,   5,   5,   0, -10,
    -5,   0,   5,   5,   5,   5,   0,  -5,
     0,   0,   5,   5,   5,   5,   0,  -5,
   -10,   5,   5,   5,   5,   5,   0, -10,
   -10,   0,   5,   0,   0,   0,   0, -10,
   -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_MID_PST = [
    20,  30,  10,   0,   0,  10,  30,  20,
    20,  20,   0,   0,   0,   0,  20,  20,
   -10, -20, -20, -20, -20, -20, -20, -10,
   -20, -30, -30, -40, -40, -30, -30, -20,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
]

KING_END_PST = [
   -50, -30, -30, -30, -30, -30, -30, -50,
   -30, -10,   0,   0,   0,   0, -10, -30,
   -30,   0,  20,  30,  30,  20,   0, -30,
   -30,  10,  30,  40,  40,  30,  10, -30,
   -30,  10,  30,  40,  40,  30,  10, -30,
   -30,   0,  20,  30,  30,  20,   0, -30,
   -30, -10,   0,   0,   0,   0, -10, -30,
   -50, -30, -30, -30, -30, -30, -30, -50,
]

PST = [None, PAWN_PST, KNIGHT_PST, BISHOP_PST, ROOK_PST, QUEEN_PST]
PASSED_BONUS = [0, 5, 10, 18, 30, 50, 80, 0]

MIRROR = [sq ^ 56 for sq in range(64)]

KNIGHT_ATTACKS = [[] for _ in range(64)]
KING_ATTACKS = [[] for _ in range(64)]
RAYS = [[[] for _ in range(8)] for _ in range(64)]
MANHATTAN = [[0] * 64 for _ in range(64)]
EDGE_BONUS = [0] * 64

DIRS = [
    (1, 0),   # N
    (-1, 0),  # S
    (0, 1),   # E
    (0, -1),  # W
    (1, 1),   # NE
    (1, -1),  # NW
    (-1, 1),  # SE
    (-1, -1), # SW
]

for sq in range(64):
    r, f = divmod(sq, 8)

    km = []
    for dr, df in ((2, 1), (2, -1), (1, 2), (1, -2), (-1, 2), (-1, -2), (-2, 1), (-2, -1)):
        rr, ff = r + dr, f + df
        if 0 <= rr < 8 and 0 <= ff < 8:
            km.append(rr * 8 + ff)
    KNIGHT_ATTACKS[sq] = km

    km = []
    for dr in (-1, 0, 1):
        for df in (-1, 0, 1):
            if dr == 0 and df == 0:
                continue
            rr, ff = r + dr, f + df
            if 0 <= rr < 8 and 0 <= ff < 8:
                km.append(rr * 8 + ff)
    KING_ATTACKS[sq] = km

    for d, (dr, df) in enumerate(DIRS):
        rr, ff = r + dr, f + df
        ray = []
        while 0 <= rr < 8 and 0 <= ff < 8:
            ray.append(rr * 8 + ff)
            rr += dr
            ff += df
        RAYS[sq][d] = ray

    EDGE_BONUS[sq] = max(abs(f - 3), abs(f - 4), abs(r - 3), abs(r - 4))

for a in range(64):
    ra, fa = divmod(a, 8)
    for b in range(64):
        rb, fb = divmod(b, 8)
        MANHATTAN[a][b] = abs(ra - rb) + abs(fa - fb)

_rng = random.Random(0)
ZOBRIST = [[0] * 13 for _ in range(64)]
for sq in range(64):
    for i in range(13):
        ZOBRIST[sq][i] = _rng.getrandbits(64)
SIDE_KEY = _rng.getrandbits(64)

DEADLINE = 0.0
NODES = 0
TT = {}
HISTORY = None
KILLERS = None


class SearchTimeout(Exception):
    pass


def piece_index(p):
    return p if p > 0 else 6 - p  # 1..6 for white, 7..12 for black


def square_to_index(s):
    return (ord(s[1]) - 49) * 8 + (ord(s[0]) - 97)


def move_to_uci(move):
    fr, to, promo = move
    s = FILES[fr & 7] + str((fr >> 3) + 1) + FILES[to & 7] + str((to >> 3) + 1)
    if promo:
        s += PROMO_TO_CHAR[promo]
    return s


def move_key(move):
    fr, to, promo = move
    return fr | (to << 6) | (promo << 12)


def parse_board(pieces):
    board = [0] * 64
    wk = bk = 0
    for sq, code in pieces.items():
        idx = square_to_index(sq)
        val = PIECE_FROM_CHAR[code[1]]
        if code[0] == "w":
            board[idx] = val
            if val == 6:
                wk = idx
        else:
            board[idx] = -val
            if val == 6:
                bk = idx
    return board, wk, bk


def compute_hash(board, side):
    h = 0
    for sq, p in enumerate(board):
        if p:
            h ^= ZOBRIST[sq][piece_index(p)]
    if side == -1:
        h ^= SIDE_KEY
    return h


def is_attacked(board, sq, attacker):
    f = sq & 7

    # Pawn attacks
    if attacker == 1:
        if f > 0:
            s = sq - 9
            if s >= 0 and board[s] == 1:
                return True
        if f < 7:
            s = sq - 7
            if s >= 0 and board[s] == 1:
                return True
    else:
        if f > 0:
            s = sq + 7
            if s < 64 and board[s] == -1:
                return True
        if f < 7:
            s = sq + 9
            if s < 64 and board[s] == -1:
                return True

    # Knight attacks
    target = 2 * attacker
    for s in KNIGHT_ATTACKS[sq]:
        if board[s] == target:
            return True

    # King attacks
    target = 6 * attacker
    for s in KING_ATTACKS[sq]:
        if board[s] == target:
            return True

    # Rook/Queen lines
    for d in range(4):
        for s in RAYS[sq][d]:
            p = board[s]
            if p:
                if p * attacker > 0 and abs(p) in (4, 5):
                    return True
                break

    # Bishop/Queen lines
    for d in range(4, 8):
        for s in RAYS[sq][d]:
            p = board[s]
            if p:
                if p * attacker > 0 and abs(p) in (3, 5):
                    return True
                break

    return False


def do_move(board, move, wk, bk):
    fr, to, promo = move
    moved = board[fr]
    captured = board[to]
    new_piece = moved if promo == 0 else (promo if moved > 0 else -promo)

    board[fr] = 0
    board[to] = new_piece

    new_wk, new_bk = wk, bk
    if moved == 6:
        new_wk = to
    elif moved == -6:
        new_bk = to

    return captured, moved, new_piece, new_wk, new_bk


def undo_move(board, move, moved, captured):
    fr, to, _ = move
    board[fr] = moved
    board[to] = captured


def hash_after_move(hashv, move, moved, captured, new_piece):
    fr, to, _ = move
    h = hashv ^ SIDE_KEY
    h ^= ZOBRIST[fr][piece_index(moved)]
    if captured:
        h ^= ZOBRIST[to][piece_index(captured)]
    h ^= ZOBRIST[to][piece_index(new_piece)]
    return h


def generate_pseudo(board, side, captures_only=False):
    moves = []
    append = moves.append

    for sq, p in enumerate(board):
        if p * side <= 0:
            continue

        ap = abs(p)
        r, f = divmod(sq, 8)

        if ap == 1:  # pawn
            if side == 1:
                one = sq + 8
                if one < 64 and board[one] == 0:
                    if r == 6:
                        for promo in PROMOTIONS:
                            append((sq, one, promo))
                    elif not captures_only:
                        append((sq, one, 0))
                        if r == 1:
                            two = sq + 16
                            if board[two] == 0:
                                append((sq, two, 0))

                if f > 0:
                    to = sq + 7
                    target = board[to]
                    if target < 0 and abs(target) != 6:
                        if r == 6:
                            for promo in PROMOTIONS:
                                append((sq, to, promo))
                        else:
                            append((sq, to, 0))
                if f < 7:
                    to = sq + 9
                    target = board[to]
                    if target < 0 and abs(target) != 6:
                        if r == 6:
                            for promo in PROMOTIONS:
                                append((sq, to, promo))
                        else:
                            append((sq, to, 0))
            else:
                one = sq - 8
                if one >= 0 and board[one] == 0:
                    if r == 1:
                        for promo in PROMOTIONS:
                            append((sq, one, promo))
                    elif not captures_only:
                        append((sq, one, 0))
                        if r == 6:
                            two = sq - 16
                            if board[two] == 0:
                                append((sq, two, 0))

                if f > 0:
                    to = sq - 9
                    target = board[to]
                    if target > 0 and abs(target) != 6:
                        if r == 1:
                            for promo in PROMOTIONS:
                                append((sq, to, promo))
                        else:
                            append((sq, to, 0))
                if f < 7:
                    to = sq - 7
                    target = board[to]
                    if target > 0 and abs(target) != 6:
                        if r == 1:
                            for promo in PROMOTIONS:
                                append((sq, to, promo))
                        else:
                            append((sq, to, 0))

        elif ap == 2:  # knight
            for to in KNIGHT_ATTACKS[sq]:
                target = board[to]
                if captures_only:
                    if target and target * side < 0 and abs(target) != 6:
                        append((sq, to, 0))
                else:
                    if target == 0 or (target * side < 0 and abs(target) != 6):
                        append((sq, to, 0))

        elif ap == 3:  # bishop
            for d in range(4, 8):
                for to in RAYS[sq][d]:
                    target = board[to]
                    if target == 0:
                        if not captures_only:
                            append((sq, to, 0))
                    else:
                        if target * side < 0 and abs(target) != 6:
                            append((sq, to, 0))
                        break

        elif ap == 4:  # rook
            for d in range(4):
                for to in RAYS[sq][d]:
                    target = board[to]
                    if target == 0:
                        if not captures_only:
                            append((sq, to, 0))
                    else:
                        if target * side < 0 and abs(target) != 6:
                            append((sq, to, 0))
                        break

        elif ap == 5:  # queen
            for d in range(8):
                for to in RAYS[sq][d]:
                    target = board[to]
                    if target == 0:
                        if not captures_only:
                            append((sq, to, 0))
                    else:
                        if target * side < 0 and abs(target) != 6:
                            append((sq, to, 0))
                        break

        else:  # king
            for to in KING_ATTACKS[sq]:
                target = board[to]
                if captures_only:
                    if target and target * side < 0 and abs(target) != 6:
                        append((sq, to, 0))
                else:
                    if target == 0 or (target * side < 0 and abs(target) != 6):
                        append((sq, to, 0))

    return moves


def generate_legal(board, side, wk, bk, captures_only=False):
    legal = []
    king_sq = wk if side == 1 else bk

    for move in generate_pseudo(board, side, captures_only):
        captured, moved, new_piece, new_wk, new_bk = do_move(board, move, wk, bk)
        try:
            my_king = new_wk if side == 1 else new_bk
            if not is_attacked(board, my_king, -side):
                legal.append(move)
        finally:
            undo_move(board, move, moved, captured)

    return legal


def evaluate(board, wk, bk):
    score = 0
    wp_files = [0] * 8
    bp_files = [0] * 8
    white_pawn_ranks = [[] for _ in range(8)]
    black_pawn_ranks = [[] for _ in range(8)]
    white_rook_files = []
    black_rook_files = []
    white_bishops = 0
    black_bishops = 0
    nonpawn = 0

    for sq, p in enumerate(board):
        if not p:
            continue
        ap = abs(p)
        f = sq & 7
        r = sq >> 3

        if ap != 6:
            val = PIECE_VALUE[ap]
            pst = PST[ap][sq if p > 0 else MIRROR[sq]]
            if p > 0:
                score += val + pst
            else:
                score -= val + pst

        if ap not in (1, 6):
            nonpawn += PIECE_VALUE[ap]

        if ap == 1:
            if p > 0:
                wp_files[f] += 1
                white_pawn_ranks[f].append(r)
            else:
                bp_files[f] += 1
                black_pawn_ranks[f].append(r)
        elif ap == 3:
            if p > 0:
                white_bishops += 1
            else:
                black_bishops += 1
        elif ap == 4:
            if p > 0:
                white_rook_files.append(f)
            else:
                black_rook_files.append(f)

    if white_bishops >= 2:
        score += 30
    if black_bishops >= 2:
        score -= 30

    king_pst = KING_MID_PST if nonpawn > 2200 else KING_END_PST
    score += king_pst[wk] - king_pst[MIRROR[bk]]

    for f in range(8):
        if wp_files[f] > 1:
            score -= 14 * (wp_files[f] - 1)
        if bp_files[f] > 1:
            score += 14 * (bp_files[f] - 1)

        if wp_files[f] and (f == 0 or wp_files[f - 1] == 0) and (f == 7 or wp_files[f + 1] == 0):
            score -= 8 * wp_files[f]
        if bp_files[f] and (f == 0 or bp_files[f - 1] == 0) and (f == 7 or bp_files[f + 1] == 0):
            score += 8 * bp_files[f]

    for f in range(8):
        for r in white_pawn_ranks[f]:
            passed = True
            for ff in range(max(0, f - 1), min(7, f + 1) + 1):
                for br in black_pawn_ranks[ff]:
                    if br > r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                score += PASSED_BONUS[r]

        for r in black_pawn_ranks[f]:
            passed = True
            for ff in range(max(0, f - 1), min(7, f + 1) + 1):
                for wr in white_pawn_ranks[ff]:
                    if wr < r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                score -= PASSED_BONUS[7 - r]

    for f in white_rook_files:
        if wp_files[f] == 0:
            score += 12 + (8 if bp_files[f] == 0 else 0)
    for f in black_rook_files:
        if bp_files[f] == 0:
            score -= 12 + (8 if wp_files[f] == 0 else 0)

    if nonpawn < 1400:
        kd = 14 - MANHATTAN[wk][bk]
        if score > 250:
            score += 6 * EDGE_BONUS[bk] + 2 * kd
        elif score < -250:
            score -= 6 * EDGE_BONUS[wk] + 2 * kd

    return score


def order_moves(moves, board, side, tt_move, ply):
    if not moves:
        return moves

    hist = HISTORY[0 if side == 1 else 1]
    scored = []

    for move in moves:
        fr, to, promo = move
        moved = abs(board[fr])
        target = board[to]
        captured = abs(target) if target else 0

        score = 0
        if tt_move is not None and move == tt_move:
            score += 1_000_000

        if captured:
            score += 100_000 + 10 * PIECE_VALUE[captured] - PIECE_VALUE[moved]
        if promo:
            score += 90_000 + PIECE_VALUE[promo]

        if not captured and not promo:
            mk = move_key(move)
            if KILLERS[ply][0] == mk:
                score += 80_000
            elif KILLERS[ply][1] == mk:
                score += 79_000
            score += hist[fr][to]

            if moved < 6:
                pst = PST[moved]
                a = fr if side == 1 else MIRROR[fr]
                b = to if side == 1 else MIRROR[to]
                score += pst[b] - pst[a]

        scored.append((score, move))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [m for _, m in scored]


def qsearch(board, side, wk, bk, alpha, beta, ply):
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.time() > DEADLINE:
        raise SearchTimeout

    if ply >= MAX_PLY - 1:
        return evaluate(board, wk, bk) * side

    my_king = wk if side == 1 else bk
    in_check = is_attacked(board, my_king, -side)

    if in_check:
        moves = generate_legal(board, side, wk, bk, False)
        if not moves:
            return -MATE + ply
        moves = order_moves(moves, board, side, None, ply)

        best = -INF
        for move in moves:
            captured, moved, new_piece, new_wk, new_bk = do_move(board, move, wk, bk)
            try:
                score = -qsearch(board, -side, new_wk, new_bk, -beta, -alpha, ply + 1)
            finally:
                undo_move(board, move, moved, captured)

            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                return beta
        return best

    stand = evaluate(board, wk, bk) * side
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    moves = generate_legal(board, side, wk, bk, True)
    if not moves:
        return stand

    moves = order_moves(moves, board, side, None, ply)

    for move in moves:
        fr, to, promo = move
        captured_piece = board[to]
        if not captured_piece and not promo:
            continue

        gain = (PIECE_VALUE[abs(captured_piece)] if captured_piece else 0)
        if promo:
            gain += PIECE_VALUE[promo] - 100
        if stand + gain + 100 < alpha:
            continue

        captured, moved, new_piece, new_wk, new_bk = do_move(board, move, wk, bk)
        try:
            score = -qsearch(board, -side, new_wk, new_bk, -beta, -alpha, ply + 1)
        finally:
            undo_move(board, move, moved, captured)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board, side, wk, bk, depth, alpha, beta, ply, hashv):
    global NODES
    NODES += 1
    if (NODES & 511) == 0 and time.time() > DEADLINE:
        raise SearchTimeout

    if ply >= MAX_PLY - 1:
        return evaluate(board, wk, bk) * side

    my_king = wk if side == 1 else bk
    in_check = is_attacked(board, my_king, -side)
    if in_check:
        depth += 1

    if depth <= 0:
        return qsearch(board, side, wk, bk, alpha, beta, ply)

    alpha0 = alpha
    beta0 = beta
    tt_move = None
    entry = TT.get(hashv)
    if entry is not None:
        edepth, flag, val, bestm = entry
        tt_move = bestm
        if edepth >= depth:
            if flag == 0:
                return val
            elif flag == 1:
                if val > alpha:
                    alpha = val
            else:
                if val < beta:
                    beta = val
            if alpha >= beta:
                return val

    moves = generate_legal(board, side, wk, bk, False)
    if not moves:
        return -MATE + ply if in_check else 0

    moves = order_moves(moves, board, side, tt_move, ply)

    best = -INF
    best_move = moves[0]
    color_idx = 0 if side == 1 else 1

    for i, move in enumerate(moves):
        captured, moved, new_piece, new_wk, new_bk = do_move(board, move, wk, bk)
        new_hash = hash_after_move(hashv, move, moved, captured, new_piece)
        try:
            if i == 0:
                score = -negamax(board, -side, new_wk, new_bk, depth - 1, -beta, -alpha, ply + 1, new_hash)
            else:
                score = -negamax(board, -side, new_wk, new_bk, depth - 1, -alpha - 1, -alpha, ply + 1, new_hash)
                if alpha < score < beta:
                    score = -negamax(board, -side, new_wk, new_bk, depth - 1, -beta, -alpha, ply + 1, new_hash)
        finally:
            undo_move(board, move, moved, captured)

        if score > best:
            best = score
            best_move = move
        if score > alpha:
            alpha = score

        if alpha >= beta:
            if captured == 0 and move[2] == 0:
                mk = move_key(move)
                if KILLERS[ply][0] != mk:
                    KILLERS[ply][1] = KILLERS[ply][0]
                    KILLERS[ply][0] = mk
                HISTORY[color_idx][move[0]][move[1]] += depth * depth
            break

    if best <= alpha0:
        flag = 2  # upper
    elif best >= beta0:
        flag = 1  # lower
    else:
        flag = 0  # exact
    TT[hashv] = (depth, flag, best, best_move)

    return best


def inferred_castles(board, side, wk, bk):
    moves = []
    if side == 1:
        if board[4] == 6 and wk == 4 and not is_attacked(board, 4, -1):
            if board[7] == 4 and board[5] == 0 and board[6] == 0:
                if not is_attacked(board, 5, -1) and not is_attacked(board, 6, -1):
                    moves.append((4, 6, 0))
            if board[0] == 4 and board[1] == 0 and board[2] == 0 and board[3] == 0:
                if not is_attacked(board, 3, -1) and not is_attacked(board, 2, -1):
                    moves.append((4, 2, 0))
    else:
        if board[60] == -6 and bk == 60 and not is_attacked(board, 60, 1):
            if board[63] == -4 and board[61] == 0 and board[62] == 0:
                if not is_attacked(board, 61, 1) and not is_attacked(board, 62, 1):
                    moves.append((60, 62, 0))
            if board[56] == -4 and board[57] == 0 and board[58] == 0 and board[59] == 0:
                if not is_attacked(board, 59, 1) and not is_attacked(board, 58, 1):
                    moves.append((60, 58, 0))
    return moves


def inferred_en_passant(board, side, wk, bk):
    moves = []

    if side == 1:
        for sq in range(64):
            if board[sq] != 1 or (sq >> 3) != 4:
                continue
            f = sq & 7

            if f > 0 and board[sq - 1] == -1 and sq + 7 < 64 and board[sq + 7] == 0:
                board[sq] = 0
                board[sq - 1] = 0
                board[sq + 7] = 1
                try:
                    if not is_attacked(board, wk, -1):
                        moves.append((sq, sq + 7, 0))
                finally:
                    board[sq] = 1
                    board[sq - 1] = -1
                    board[sq + 7] = 0

            if f < 7 and board[sq + 1] == -1 and sq + 9 < 64 and board[sq + 9] == 0:
                board[sq] = 0
                board[sq + 1] = 0
                board[sq + 9] = 1
                try:
                    if not is_attacked(board, wk, -1):
                        moves.append((sq, sq + 9, 0))
                finally:
                    board[sq] = 1
                    board[sq + 1] = -1
                    board[sq + 9] = 0
    else:
        for sq in range(64):
            if board[sq] != -1 or (sq >> 3) != 3:
                continue
            f = sq & 7

            if f > 0 and board[sq - 1] == 1 and sq - 9 >= 0 and board[sq - 9] == 0:
                board[sq] = 0
                board[sq - 1] = 0
                board[sq - 9] = -1
                try:
                    if not is_attacked(board, bk, 1):
                        moves.append((sq, sq - 9, 0))
                finally:
                    board[sq] = -1
                    board[sq - 1] = 1
                    board[sq - 9] = 0

            if f < 7 and board[sq + 1] == 1 and sq - 7 >= 0 and board[sq - 7] == 0:
                board[sq] = 0
                board[sq + 1] = 0
                board[sq - 7] = -1
                try:
                    if not is_attacked(board, bk, 1):
                        moves.append((sq, sq - 7, 0))
                finally:
                    board[sq] = -1
                    board[sq + 1] = 1
                    board[sq - 7] = 0

    return moves


def emergency_special_move(board, side, wk, bk):
    castles = inferred_castles(board, side, wk, bk)
    if castles:
        return move_to_uci(castles[0])

    eps = inferred_en_passant(board, side, wk, bk)
    if eps:
        return move_to_uci(eps[0])

    return None


def policy(pieces, to_play):
    global DEADLINE, NODES, TT, HISTORY, KILLERS

    side = 1 if to_play[0] == "w" else -1
    board, wk, bk = parse_board(pieces)

    legal_moves = generate_legal(board, side, wk, bk, False)
    if not legal_moves:
        special = emergency_special_move(board, side, wk, bk)
        if special is not None:
            return special
        return "a1a1"

    if len(legal_moves) == 1:
        return move_to_uci(legal_moves[0])

    piece_count = len(pieces)
    if piece_count > 26:
        time_limit = 0.42
        max_depth = 4
    elif piece_count > 18:
        time_limit = 0.62
        max_depth = 5
    elif piece_count > 10:
        time_limit = 0.82
        max_depth = 5
    else:
        time_limit = 0.92
        max_depth = 6

    DEADLINE = time.time() + time_limit
    NODES = 0
    TT = {}
    HISTORY = [[[0] * 64 for _ in range(64)] for _ in range(2)]
    KILLERS = [[0, 0] for _ in range(MAX_PLY)]

    hashv = compute_hash(board, side)

    best_move = legal_moves[0]
    best_score = -INF

    try:
        for depth in range(1, max_depth + 1):
            tt_entry = TT.get(hashv)
            root_hint = best_move if best_move is not None else (tt_entry[3] if tt_entry else None)
            moves = order_moves(legal_moves, board, side, root_hint, 0)

            alpha = -INF
            beta = INF
            current_best = None
            current_score = -INF

            for i, move in enumerate(moves):
                captured, moved, new_piece, new_wk, new_bk = do_move(board, move, wk, bk)
                new_hash = hash_after_move(hashv, move, moved, captured, new_piece)
                try:
                    if i == 0:
                        score = -negamax(board, -side, new_wk, new_bk, depth - 1, -beta, -alpha, 1, new_hash)
                    else:
                        score = -negamax(board, -side, new_wk, new_bk, depth - 1, -alpha - 1, -alpha, 1, new_hash)
                        if score > alpha:
                            score = -negamax(board, -side, new_wk, new_bk, depth - 1, -beta, -alpha, 1, new_hash)
                finally:
                    undo_move(board, move, moved, captured)

                if score > current_score:
                    current_score = score
                    current_best = move
                if score > alpha:
                    alpha = score

            if current_best is not None:
                best_move = current_best
                best_score = current_score

            if abs(best_score) > MATE - 1000:
                break

    except SearchTimeout:
        pass

    return move_to_uci(best_move)
