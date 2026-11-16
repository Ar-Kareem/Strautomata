
import time

INF = 10**9
MATE = 100000

FILES = "abcdefgh"
RANKS = "12345678"
IDX_TO_SQ = [f + r for r in RANKS for f in FILES]
SQ_TO_IDX = {sq: i for i, sq in enumerate(IDX_TO_SQ)}

PIECE_VALUES = {
    "P": 100,
    "N": 320,
    "B": 330,
    "R": 500,
    "Q": 900,
    "K": 0,
}

PHASE_VALUES = {
    "P": 0,
    "N": 1,
    "B": 1,
    "R": 2,
    "Q": 4,
    "K": 0,
}

PROMOS = ("Q", "R", "B", "N")

KNIGHT_DELTAS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_DELTAS = ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1))
DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, 1), (1, -1), (-1, -1))

KNIGHT_ATTACKS = [[] for _ in range(64)]
KING_ATTACKS = [[] for _ in range(64)]
RAYS = [[[] for _ in range(8)] for _ in range(64)]

CENTER_SCORE = [0] * 64
EDGE_SCORE = [0] * 64
PAWN_TABLE = [0] * 64
KNIGHT_TABLE = [0] * 64
BISHOP_TABLE = [0] * 64
ROOK_TABLE = [0] * 64
QUEEN_TABLE = [0] * 64
KING_MG_TABLE = [0] * 64
KING_EG_TABLE = [0] * 64

for sq in range(64):
    f = sq & 7
    r = sq >> 3

    for df, dr in KNIGHT_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KNIGHT_ATTACKS[sq].append((nr << 3) + nf)

    for df, dr in KING_DELTAS:
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KING_ATTACKS[sq].append((nr << 3) + nf)

    for di, (df, dr) in enumerate(DIRS):
        nf, nr = f + df, r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            RAYS[sq][di].append((nr << 3) + nf)
            nf += df
            nr += dr

    dist = abs(f - 3.5) + abs(r - 3.5)
    center = 7.0 - dist
    CENTER_SCORE[sq] = int(center * 6)
    EDGE_SCORE[sq] = int(dist * 6)

    file_center = 3.5 - abs(f - 3.5)

    PAWN_TABLE[sq] = int(r * 12 + file_center * 4)
    KNIGHT_TABLE[sq] = CENTER_SCORE[sq] - (12 if f in (0, 7) or r in (0, 7) else 0)
    BISHOP_TABLE[sq] = CENTER_SCORE[sq] // 2 + 4
    ROOK_TABLE[sq] = int(file_center * 4 + r * 2 + (12 if r == 6 else 0))
    QUEEN_TABLE[sq] = CENTER_SCORE[sq] // 3
    KING_MG_TABLE[sq] = EDGE_SCORE[sq]
    KING_EG_TABLE[sq] = CENTER_SCORE[sq]

TT = {}
HISTORY = {}
KILLERS = [[None, None] for _ in range(128)]
NODE_COUNT = 0
DEADLINE = 0.0


class SearchTimeout(Exception):
    pass


def touch_time():
    global NODE_COUNT
    NODE_COUNT += 1
    if (NODE_COUNT & 511) == 0 and time.time() > DEADLINE:
        raise SearchTimeout


def board_key(board, white):
    return "".join(board) + ("w" if white else "b")


def move_to_uci(move):
    frm, to, promo = move
    s = IDX_TO_SQ[frm] + IDX_TO_SQ[to]
    if promo:
        s += promo.lower()
    return s


def parse_board(pieces):
    board = ["."] * 64
    for sq, code in pieces.items():
        idx = SQ_TO_IDX.get(sq)
        if idx is None or not isinstance(code, str) or len(code) != 2:
            continue
        color, pt = code[0], code[1].upper()
        if pt not in "KQRBNP":
            continue
        board[idx] = pt if color == "w" else pt.lower()
    return board


def find_king(board, white):
    k = "K" if white else "k"
    for i, p in enumerate(board):
        if p == k:
            return i
    return -1


def is_attacked(board, sq, by_white):
    f = sq & 7
    r = sq >> 3

    # Pawns
    if by_white:
        rr = r - 1
        if rr >= 0:
            if f - 1 >= 0 and board[(rr << 3) + (f - 1)] == "P":
                return True
            if f + 1 < 8 and board[(rr << 3) + (f + 1)] == "P":
                return True
    else:
        rr = r + 1
        if rr < 8:
            if f - 1 >= 0 and board[(rr << 3) + (f - 1)] == "p":
                return True
            if f + 1 < 8 and board[(rr << 3) + (f + 1)] == "p":
                return True

    # Knights
    target_knight = "N" if by_white else "n"
    for s in KNIGHT_ATTACKS[sq]:
        if board[s] == target_knight:
            return True

    # Kings
    target_king = "K" if by_white else "k"
    for s in KING_ATTACKS[sq]:
        if board[s] == target_king:
            return True

    # Rooks / Queens
    target_rook = "R" if by_white else "r"
    target_bishop = "B" if by_white else "b"
    target_queen = "Q" if by_white else "q"

    for di in range(4):
        for s in RAYS[sq][di]:
            p = board[s]
            if p != ".":
                if p == target_rook or p == target_queen:
                    return True
                break

    # Bishops / Queens
    for di in range(4, 8):
        for s in RAYS[sq][di]:
            p = board[s]
            if p != ".":
                if p == target_bishop or p == target_queen:
                    return True
                break

    return False


def is_in_check(board, white):
    ks = find_king(board, white)
    if ks == -1:
        return False
    return is_attacked(board, ks, not white)


def make_move(board, move):
    frm, to, promo = move
    nb = board[:]
    piece = nb[frm]
    nb[frm] = "."
    if promo:
        nb[to] = promo if piece.isupper() else promo.lower()
    else:
        nb[to] = piece
    return nb


def gen_pseudo(board, white, captures_only=False):
    moves = []
    for sq, piece in enumerate(board):
        if piece == "." or piece.isupper() != white:
            continue

        typ = piece.upper()
        f = sq & 7
        r = sq >> 3

        if typ == "P":
            step = 8 if white else -8
            start_rank = 1 if white else 6
            promo_rank = 6 if white else 1

            # Captures
            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8:
                    to = sq + step + df
                    if 0 <= to < 64:
                        target = board[to]
                        if target != "." and target.isupper() != white and target.upper() != "K":
                            if r == promo_rank:
                                for pr in PROMOS:
                                    moves.append((sq, to, pr))
                            else:
                                moves.append((sq, to, None))

            # Quiets
            one = sq + step
            if r == promo_rank:
                if 0 <= one < 64 and board[one] == ".":
                    for pr in PROMOS:
                        moves.append((sq, one, pr))
            elif not captures_only:
                if 0 <= one < 64 and board[one] == ".":
                    moves.append((sq, one, None))
                    if r == start_rank:
                        two = sq + 2 * step
                        if 0 <= two < 64 and board[two] == ".":
                            moves.append((sq, two, None))

        elif typ == "N":
            for to in KNIGHT_ATTACKS[sq]:
                target = board[to]
                if target == ".":
                    if not captures_only:
                        moves.append((sq, to, None))
                elif target.isupper() != white and target.upper() != "K":
                    moves.append((sq, to, None))

        elif typ == "B":
            dirs = range(4, 8)
            for di in dirs:
                for to in RAYS[sq][di]:
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            moves.append((sq, to, None))
                    else:
                        if target.isupper() != white and target.upper() != "K":
                            moves.append((sq, to, None))
                        break

        elif typ == "R":
            dirs = range(4)
            for di in dirs:
                for to in RAYS[sq][di]:
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            moves.append((sq, to, None))
                    else:
                        if target.isupper() != white and target.upper() != "K":
                            moves.append((sq, to, None))
                        break

        elif typ == "Q":
            for di in range(8):
                for to in RAYS[sq][di]:
                    target = board[to]
                    if target == ".":
                        if not captures_only:
                            moves.append((sq, to, None))
                    else:
                        if target.isupper() != white and target.upper() != "K":
                            moves.append((sq, to, None))
                        break

        elif typ == "K":
            for to in KING_ATTACKS[sq]:
                target = board[to]
                if target == ".":
                    if not captures_only:
                        moves.append((sq, to, None))
                elif target.isupper() != white and target.upper() != "K":
                    moves.append((sq, to, None))

    return moves


def gen_legal(board, white, captures_only=False):
    legal = []
    for mv in gen_pseudo(board, white, captures_only):
        nb = make_move(board, mv)
        if not is_in_check(nb, white):
            legal.append(mv)
    return legal


def king_shield(board, sq, white):
    if sq < 0:
        return 0
    f = sq & 7
    r = sq >> 3
    own_pawn = "P" if white else "p"
    opp_pawn = "p" if white else "P"

    bonus = 0
    front1 = r + 1 if white else r - 1
    front2 = r + 2 if white else r - 2

    for rr, val in ((front1, 8), (front2, 4)):
        if 0 <= rr < 8:
            base = rr << 3
            for ff in (f - 1, f, f + 1):
                if 0 <= ff < 8:
                    p = board[base + ff]
                    if p == own_pawn:
                        bonus += val
                    elif p == opp_pawn:
                        bonus -= val
    return bonus


def evaluate_white(board):
    score = 0
    phase = 0

    white_king = -1
    black_king = -1
    white_bishops = 0
    black_bishops = 0

    white_pawn_files = [0] * 8
    black_pawn_files = [0] * 8
    white_pawns_by_file = [[] for _ in range(8)]
    black_pawns_by_file = [[] for _ in range(8)]
    rooks = []

    for sq, p in enumerate(board):
        if p == ".":
            continue

        white_piece = p.isupper()
        sign = 1 if white_piece else -1
        typ = p.upper()
        osq = sq if white_piece else (sq ^ 56)

        score += sign * PIECE_VALUES[typ]
        phase += PHASE_VALUES[typ]

        if typ == "P":
            score += sign * PAWN_TABLE[osq]
            file_ = sq & 7
            rank_ = sq >> 3
            if white_piece:
                white_pawn_files[file_] += 1
                white_pawns_by_file[file_].append(rank_)
            else:
                black_pawn_files[file_] += 1
                black_pawns_by_file[file_].append(rank_)

        elif typ == "N":
            score += sign * KNIGHT_TABLE[sq]

        elif typ == "B":
            score += sign * BISHOP_TABLE[sq]
            if white_piece:
                white_bishops += 1
            else:
                black_bishops += 1

        elif typ == "R":
            score += sign * ROOK_TABLE[osq]
            rooks.append((sq, white_piece))

        elif typ == "Q":
            score += sign * QUEEN_TABLE[sq]

        elif typ == "K":
            if white_piece:
                white_king = sq
            else:
                black_king = sq

    if white_bishops >= 2:
        score += 30
    if black_bishops >= 2:
        score -= 30

    # Pawn structure
    for f in range(8):
        wc = white_pawn_files[f]
        bc = black_pawn_files[f]
        if wc > 1:
            score -= 14 * (wc - 1)
        if bc > 1:
            score += 14 * (bc - 1)

    for f in range(8):
        for r in white_pawns_by_file[f]:
            if (f == 0 or white_pawn_files[f - 1] == 0) and (f == 7 or white_pawn_files[f + 1] == 0):
                score -= 10
            passed = True
            for ef in range(max(0, f - 1), min(7, f + 1) + 1):
                for br in black_pawns_by_file[ef]:
                    if br > r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                score += 20 + r * 12

        for r in black_pawns_by_file[f]:
            if (f == 0 or black_pawn_files[f - 1] == 0) and (f == 7 or black_pawn_files[f + 1] == 0):
                score += 10
            passed = True
            for ef in range(max(0, f - 1), min(7, f + 1) + 1):
                for wr in white_pawns_by_file[ef]:
                    if wr < r:
                        passed = False
                        break
                if not passed:
                    break
            if passed:
                score -= 20 + (7 - r) * 12

    # Rooks on open files / 7th rank
    for sq, white_piece in rooks:
        f = sq & 7
        r = sq >> 3
        own = white_pawn_files[f] if white_piece else black_pawn_files[f]
        opp = black_pawn_files[f] if white_piece else white_pawn_files[f]
        bonus = 0
        if own == 0:
            bonus += 12
        if opp == 0:
            bonus += 10
        if (white_piece and r == 6) or ((not white_piece) and r == 1):
            bonus += 20
        score += bonus if white_piece else -bonus

    phase = min(24, phase)
    eg = 24 - phase

    if white_king != -1:
        score += (KING_MG_TABLE[white_king] * phase + KING_EG_TABLE[white_king] * eg) // 24
        score += king_shield(board, white_king, True) * phase // 24
    if black_king != -1:
        score -= (KING_MG_TABLE[black_king] * phase + KING_EG_TABLE[black_king] * eg) // 24
        score -= king_shield(board, black_king, False) * phase // 24

    return score


def evaluate(board, white):
    s = evaluate_white(board)
    return (s if white else -s) + 10


def order_moves(board, moves, ply, pv_move=None, tt_move=None):
    if len(moves) <= 1:
        return

    if ply < len(KILLERS):
        k1, k2 = KILLERS[ply]
    else:
        k1, k2 = None, None

    def score_move(mv):
        if pv_move is not None and mv == pv_move:
            return 1_000_000_000
        if tt_move is not None and mv == tt_move:
            return 900_000_000

        frm, to, promo = mv
        piece = board[frm]
        target = board[to]
        s = 0

        if promo:
            s += 200_000 + PIECE_VALUES[promo]

        if target != ".":
            s += 100_000 + 10 * PIECE_VALUES[target.upper()] - PIECE_VALUES[piece.upper()]
        else:
            if mv == k1:
                s += 90_000
            elif mv == k2:
                s += 80_000
            s += HISTORY.get((piece, to), 0)
            if piece.upper() == "P":
                osq_from = frm if piece.isupper() else (frm ^ 56)
                osq_to = to if piece.isupper() else (to ^ 56)
                s += (PAWN_TABLE[osq_to] - PAWN_TABLE[osq_from]) // 2
            else:
                s += CENTER_SCORE[to] - CENTER_SCORE[frm]

        return s

    moves.sort(key=score_move, reverse=True)


def quiescence(board, white, alpha, beta, ply, qdepth=6):
    touch_time()

    in_check = is_in_check(board, white)
    if in_check:
        moves = gen_legal(board, white, captures_only=False)
        if not moves:
            return -MATE + ply
        order_moves(board, moves, ply)
        best = -INF
        first = True
        for mv in moves:
            nb = make_move(board, mv)
            if first:
                score = -quiescence(nb, not white, -beta, -alpha, ply + 1, qdepth - 1)
                first = False
            else:
                score = -quiescence(nb, not white, -alpha - 1, -alpha, ply + 1, qdepth - 1)
                if alpha < score < beta:
                    score = -quiescence(nb, not white, -beta, -alpha, ply + 1, qdepth - 1)
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best

    stand_pat = evaluate(board, white)
    if stand_pat >= beta:
        return beta
    if stand_pat > alpha:
        alpha = stand_pat
    if qdepth <= 0:
        return alpha

    moves = gen_legal(board, white, captures_only=True)
    if not moves:
        return alpha

    order_moves(board, moves, ply)
    for mv in moves:
        nb = make_move(board, mv)
        score = -quiescence(nb, not white, -beta, -alpha, ply + 1, qdepth - 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def negamax(board, white, depth, alpha, beta, ply):
    touch_time()

    alpha_orig = alpha
    in_check = is_in_check(board, white)
    if in_check:
        depth += 1

    if depth <= 0:
        return quiescence(board, white, alpha, beta, ply)

    key = None
    tt_move = None
    if depth >= 2:
        key = board_key(board, white)
        entry = TT.get(key)
        if entry is not None:
            edepth, flag, score, best_move = entry
            tt_move = best_move
            if edepth >= depth:
                if flag == 0:
                    return score
                if flag == 1 and score >= beta:
                    return score
                if flag == -1 and score <= alpha:
                    return score

    moves = gen_legal(board, white, captures_only=False)
    if not moves:
        if in_check:
            return -MATE + ply
        return 0

    order_moves(board, moves, ply, tt_move=tt_move)

    best_score = -INF
    best_move = moves[0]
    first = True

    for mv in moves:
        nb = make_move(board, mv)

        if first:
            score = -negamax(nb, not white, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            score = -negamax(nb, not white, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -negamax(nb, not white, depth - 1, -beta, -alpha, ply + 1)

        if score > best_score:
            best_score = score
            best_move = mv

        if score > alpha:
            alpha = score

        if alpha >= beta:
            frm, to, promo = mv
            if promo is None and board[to] == "." and ply < len(KILLERS):
                if KILLERS[ply][0] != mv:
                    KILLERS[ply][1] = KILLERS[ply][0]
                    KILLERS[ply][0] = mv
                HISTORY[(board[frm], to)] = HISTORY.get((board[frm], to), 0) + depth * depth
            break

    if key is not None:
        flag = 0
        if best_score <= alpha_orig:
            flag = -1
        elif best_score >= beta:
            flag = 1
        TT[key] = (depth, flag, best_score, best_move)

    return best_score


def search_root(board, white, depth, legal_moves, pv_move):
    key = board_key(board, white)
    tt_entry = TT.get(key)
    tt_move = tt_entry[3] if tt_entry is not None else None

    moves = legal_moves[:]
    order_moves(board, moves, 0, pv_move=pv_move, tt_move=tt_move)

    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = moves[0]
    first = True

    for mv in moves:
        nb = make_move(board, mv)

        if first:
            score = -negamax(nb, not white, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -negamax(nb, not white, depth - 1, -alpha - 1, -alpha, 1)
            if alpha < score < beta:
                score = -negamax(nb, not white, depth - 1, -beta, -alpha, 1)

        if score > best_score:
            best_score = score
            best_move = mv

        if score > alpha:
            alpha = score

    TT[key] = (depth, 0, best_score, best_move)
    return best_move, best_score


def fallback_castle_like(board, white):
    moves = []
    if white:
        if board[4] == "K" and not is_attacked(board, 4, False):
            # O-O
            if board[7] == "R" and board[5] == "." and board[6] == ".":
                if not is_attacked(board, 5, False) and not is_attacked(board, 6, False):
                    moves.append((4, 6, None))
            # O-O-O
            if board[0] == "R" and board[1] == "." and board[2] == "." and board[3] == ".":
                if not is_attacked(board, 3, False) and not is_attacked(board, 2, False):
                    moves.append((4, 2, None))
    else:
        if board[60] == "k" and not is_attacked(board, 60, True):
            # O-O
            if board[63] == "r" and board[61] == "." and board[62] == ".":
                if not is_attacked(board, 61, True) and not is_attacked(board, 62, True):
                    moves.append((60, 62, None))
            # O-O-O
            if board[56] == "r" and board[57] == "." and board[58] == "." and board[59] == ".":
                if not is_attacked(board, 59, True) and not is_attacked(board, 58, True):
                    moves.append((60, 58, None))
    return moves


def policy(pieces: dict[str, str], to_play: str) -> str:
    global TT, HISTORY, KILLERS, NODE_COUNT, DEADLINE

    board = parse_board(pieces)
    white = str(to_play).lower() == "white"

    TT = {}
    HISTORY = {}
    KILLERS = [[None, None] for _ in range(128)]
    NODE_COUNT = 0
    DEADLINE = time.time() + 0.90

    legal = gen_legal(board, white, captures_only=False)

    if not legal:
        special = fallback_castle_like(board, white)
        if special:
            return move_to_uci(special[0])

        pseudo = gen_pseudo(board, white, captures_only=False)
        if pseudo:
            return move_to_uci(pseudo[0])

        return "a1a1"

    order_moves(board, legal, 0)
    if len(legal) == 1:
        return move_to_uci(legal[0])

    best_move = legal[0]
    pv_move = None

    piece_count = sum(1 for p in board if p != ".")
    max_depth = 5
    if piece_count <= 12:
        max_depth = 6
    if len(legal) <= 8:
        max_depth += 1

    try:
        for depth in range(1, max_depth + 1):
            mv, score = search_root(board, white, depth, legal, pv_move)
            if mv is not None:
                best_move = mv
                pv_move = mv
            if abs(score) >= MATE - 1000:
                break
    except SearchTimeout:
        pass

    return move_to_uci(best_move)
