
from time import perf_counter

P, N, B, R, Q, K = 1, 2, 3, 4, 5, 6

PIECE_FROM_CHAR = {
    'P': P, 'N': N, 'B': B, 'R': R, 'Q': Q, 'K': K
}

PIECE_VALUES = [0, 100, 320, 330, 500, 900, 0]
PHASE_VALUES = [0, 0, 1, 1, 2, 4, 0]
PROMO_TO_CHAR = {Q: 'q', R: 'r', B: 'b', N: 'n'}

INF = 10**9
MATE = 100000

PAWN_PST = [
     0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
     5,   5,  10,  25,  25,  10,   5,   5,
     0,   0,   0,  20,  20,   0,   0,   0,
     5,  -5, -10,   0,   0, -10,  -5,   5,
     5,  10,  10, -20, -20,  10,  10,   5,
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
   -10,   0,   0,   0,   0,   0,   0, -10,
   -10,   0,   5,  10,  10,   5,   0, -10,
   -10,   5,   5,  10,  10,   5,   5, -10,
   -10,   0,  10,  10,  10,  10,   0, -10,
   -10,  10,  10,  10,  10,  10,  10, -10,
   -10,   5,   0,   0,   0,   0,   5, -10,
   -20, -10, -10, -10, -10, -10, -10, -20,
]

ROOK_PST = [
     0,   0,   0,   0,   0,   0,   0,   0,
     5,  10,  10,  10,  10,  10,  10,   5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
     0,   0,   0,   5,   5,   0,   0,   0,
]

QUEEN_PST = [
   -20, -10, -10,  -5,  -5, -10, -10, -20,
   -10,   0,   0,   0,   0,   0,   0, -10,
   -10,   0,   5,   5,   5,   5,   0, -10,
    -5,   0,   5,   5,   5,   5,   0,  -5,
     0,   0,   5,   5,   5,   5,   0,  -5,
   -10,   0,   5,   5,   5,   5,   0, -10,
   -10,   0,   5,   0,   0,   0,   0, -10,
   -20, -10, -10,  -5,  -5, -10, -10, -20,
]

KING_MG = [
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -30, -40, -40, -50, -50, -40, -40, -30,
   -20, -30, -30, -40, -40, -30, -30, -20,
   -10, -20, -20, -20, -20, -20, -20, -10,
    20,  20,   0,   0,   0,   0,  20,  20,
    20,  30,  10,   0,   0,  10,  30,  20,
]

KING_EG = [
   -50, -40, -30, -20, -20, -30, -40, -50,
   -30, -20, -10,   0,   0, -10, -20, -30,
   -30, -10,  20,  30,  30,  20, -10, -30,
   -30, -10,  30,  40,  40,  30, -10, -30,
   -30, -10,  30,  40,  40,  30, -10, -30,
   -30, -10,  20,  30,  30,  20, -10, -30,
   -30, -30,   0,   0,   0,   0, -30, -30,
   -50, -30, -30, -30, -30, -30, -30, -50,
]

PST = [None, PAWN_PST, KNIGHT_PST, BISHOP_PST, ROOK_PST, QUEEN_PST, KING_MG]
MIRROR = [i ^ 56 for i in range(64)]
PASSED_BONUS = [0, 5, 10, 20, 35, 60, 100, 0]

KNIGHT_ATTACKS = [[] for _ in range(64)]
KING_ATTACKS = [[] for _ in range(64)]

for sq in range(64):
    f = sq & 7
    r = sq >> 3
    for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KNIGHT_ATTACKS[sq].append((nr << 3) | nf)
    for df, dr in ((1, 1), (1, 0), (1, -1), (0, 1), (0, -1), (-1, 1), (-1, 0), (-1, -1)):
        nf, nr = f + df, r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KING_ATTACKS[sq].append((nr << 3) | nf)

DEADLINE = 0.0
NODES = 0
HISTORY = None
KILLERS = None


class SearchTimeout(Exception):
    pass


def sq_to_idx(s):
    return (ord(s[0]) - 97) + 8 * (ord(s[1]) - 49)


def idx_to_sq(i):
    return chr(97 + (i & 7)) + chr(49 + (i >> 3))


def move_to_uci(move):
    fr, to, promo, _castle = move
    s = idx_to_sq(fr) + idx_to_sq(to)
    if promo:
        s += PROMO_TO_CHAR[promo]
    return s


def parse_board(pieces):
    board = [0] * 64
    wk = -1
    bk = -1
    for sq, code in pieces.items():
        idx = sq_to_idx(sq)
        piece = PIECE_FROM_CHAR[code[1]]
        if code[0] == 'w':
            board[idx] = piece
            if piece == K:
                wk = idx
        else:
            board[idx] = -piece
            if piece == K:
                bk = idx
    return board, wk, bk


def is_attacked(board, sq, by_white):
    if sq < 0:
        return False

    b = board
    f = sq & 7
    r = sq >> 3

    pawn = P if by_white else -P
    knight = N if by_white else -N
    bishop = B if by_white else -B
    rook = R if by_white else -R
    queen = Q if by_white else -Q
    king = K if by_white else -K

    if by_white:
        x = sq - 9
        if f > 0 and x >= 0 and b[x] == pawn:
            return True
        x = sq - 7
        if f < 7 and x >= 0 and b[x] == pawn:
            return True
    else:
        x = sq + 7
        if f > 0 and x < 64 and b[x] == pawn:
            return True
        x = sq + 9
        if f < 7 and x < 64 and b[x] == pawn:
            return True

    for x in KNIGHT_ATTACKS[sq]:
        if b[x] == knight:
            return True

    nf, nr = f + 1, r + 1
    while nf < 8 and nr < 8:
        p = b[(nr << 3) | nf]
        if p:
            if p == bishop or p == queen:
                return True
            break
        nf += 1
        nr += 1

    nf, nr = f - 1, r + 1
    while nf >= 0 and nr < 8:
        p = b[(nr << 3) | nf]
        if p:
            if p == bishop or p == queen:
                return True
            break
        nf -= 1
        nr += 1

    nf, nr = f + 1, r - 1
    while nf < 8 and nr >= 0:
        p = b[(nr << 3) | nf]
        if p:
            if p == bishop or p == queen:
                return True
            break
        nf += 1
        nr -= 1

    nf, nr = f - 1, r - 1
    while nf >= 0 and nr >= 0:
        p = b[(nr << 3) | nf]
        if p:
            if p == bishop or p == queen:
                return True
            break
        nf -= 1
        nr -= 1

    nf = f + 1
    while nf < 8:
        p = b[(r << 3) | nf]
        if p:
            if p == rook or p == queen:
                return True
            break
        nf += 1

    nf = f - 1
    while nf >= 0:
        p = b[(r << 3) | nf]
        if p:
            if p == rook or p == queen:
                return True
            break
        nf -= 1

    nr = r + 1
    while nr < 8:
        p = b[(nr << 3) | f]
        if p:
            if p == rook or p == queen:
                return True
            break
        nr += 1

    nr = r - 1
    while nr >= 0:
        p = b[(nr << 3) | f]
        if p:
            if p == rook or p == queen:
                return True
            break
        nr -= 1

    for x in KING_ATTACKS[sq]:
        if b[x] == king:
            return True

    return False


def king_shield(board, king_sq, white):
    if king_sq < 0:
        return 0
    f = king_sq & 7
    r = king_sq >> 3
    fr = r + 1 if white else r - 1
    if fr < 0 or fr > 7:
        return 0

    target = P if white else -P
    base = fr << 3
    bonus = 0
    for df in (-1, 0, 1):
        nf = f + df
        if 0 <= nf < 8:
            if board[base | nf] == target:
                bonus += 10
            else:
                bonus -= 6
    return bonus


def evaluate(board):
    score = 0
    phase = 0

    white_bishops = 0
    black_bishops = 0
    white_queens = 0
    black_queens = 0

    white_pawns = []
    black_pawns = []
    white_rooks = []
    black_rooks = []

    white_files = [0] * 8
    black_files = [0] * 8

    white_king = -1
    black_king = -1

    for sq, p in enumerate(board):
        if p == 0:
            continue

        white = p > 0
        a = p if p > 0 else -p
        idx = sq if white else MIRROR[sq]

        if a == K:
            if white:
                white_king = sq
            else:
                black_king = sq
            continue

        val = PIECE_VALUES[a] + PST[a][idx]
        if white:
            score += val
        else:
            score -= val

        phase += PHASE_VALUES[a]

        if a == P:
            if white:
                white_pawns.append(sq)
                white_files[sq & 7] += 1
            else:
                black_pawns.append(sq)
                black_files[sq & 7] += 1
        elif a == B:
            if white:
                white_bishops += 1
            else:
                black_bishops += 1
        elif a == R:
            if white:
                white_rooks.append(sq)
            else:
                black_rooks.append(sq)
        elif a == Q:
            if white:
                white_queens += 1
            else:
                black_queens += 1

    endgame = (phase <= 6) or (white_queens == 0 and black_queens == 0 and phase <= 10)

    if white_king != -1:
        score += (KING_EG if endgame else KING_MG)[white_king]
    if black_king != -1:
        score -= (KING_EG if endgame else KING_MG)[MIRROR[black_king]]

    if white_bishops >= 2:
        score += 30
    if black_bishops >= 2:
        score -= 30

    for f in range(8):
        wc = white_files[f]
        bc = black_files[f]
        if wc > 1:
            score -= 12 * (wc - 1)
        if bc > 1:
            score += 12 * (bc - 1)

    for sq in white_pawns:
        f = sq & 7
        r = sq >> 3

        if (f == 0 or white_files[f - 1] == 0) and (f == 7 or white_files[f + 1] == 0):
            score -= 10

        passed = True
        for ep in black_pawns:
            ef = ep & 7
            er = ep >> 3
            if abs(ef - f) <= 1 and er > r:
                passed = False
                break
        if passed:
            bonus = PASSED_BONUS[r]
            score += bonus * (2 if endgame else 1)

    for sq in black_pawns:
        f = sq & 7
        r = sq >> 3

        if (f == 0 or black_files[f - 1] == 0) and (f == 7 or black_files[f + 1] == 0):
            score += 10

        passed = True
        for ep in white_pawns:
            ef = ep & 7
            er = ep >> 3
            if abs(ef - f) <= 1 and er < r:
                passed = False
                break
        if passed:
            bonus = PASSED_BONUS[7 - r]
            score -= bonus * (2 if endgame else 1)

    for sq in white_rooks:
        f = sq & 7
        if white_files[f] == 0:
            score += 10
            if black_files[f] == 0:
                score += 6

    for sq in black_rooks:
        f = sq & 7
        if black_files[f] == 0:
            score -= 10
            if white_files[f] == 0:
                score -= 6

    if not endgame:
        if white_king != -1:
            shield = king_shield(board, white_king, True)
            if black_queens == 0:
                shield //= 2
            score += shield
        if black_king != -1:
            shield = king_shield(board, black_king, False)
            if white_queens == 0:
                shield //= 2
            score -= shield

    return score


def generate_pseudo_moves(board, white, captures_only=False):
    moves = []
    add = moves.append
    color = 1 if white else -1
    b = board

    for sq, piece in enumerate(b):
        if piece == 0 or piece * color <= 0:
            continue

        a = piece if piece > 0 else -piece
        f = sq & 7
        r = sq >> 3

        if a == P:
            if white:
                one = sq + 8
                if one < 64 and b[one] == 0:
                    if r == 6:
                        add((sq, one, Q, 0))
                        add((sq, one, R, 0))
                        add((sq, one, B, 0))
                        add((sq, one, N, 0))
                    elif not captures_only:
                        add((sq, one, 0, 0))
                        if r == 1 and b[sq + 16] == 0:
                            add((sq, sq + 16, 0, 0))

                if f > 0:
                    to = sq + 7
                    if to < 64:
                        target = b[to]
                        if target < 0 and target != -K:
                            if r == 6:
                                add((sq, to, Q, 0))
                                add((sq, to, R, 0))
                                add((sq, to, B, 0))
                                add((sq, to, N, 0))
                            else:
                                add((sq, to, 0, 0))

                if f < 7:
                    to = sq + 9
                    if to < 64:
                        target = b[to]
                        if target < 0 and target != -K:
                            if r == 6:
                                add((sq, to, Q, 0))
                                add((sq, to, R, 0))
                                add((sq, to, B, 0))
                                add((sq, to, N, 0))
                            else:
                                add((sq, to, 0, 0))
            else:
                one = sq - 8
                if one >= 0 and b[one] == 0:
                    if r == 1:
                        add((sq, one, Q, 0))
                        add((sq, one, R, 0))
                        add((sq, one, B, 0))
                        add((sq, one, N, 0))
                    elif not captures_only:
                        add((sq, one, 0, 0))
                        if r == 6 and b[sq - 16] == 0:
                            add((sq, sq - 16, 0, 0))

                if f > 0:
                    to = sq - 9
                    if to >= 0:
                        target = b[to]
                        if target > 0 and target != K:
                            if r == 1:
                                add((sq, to, Q, 0))
                                add((sq, to, R, 0))
                                add((sq, to, B, 0))
                                add((sq, to, N, 0))
                            else:
                                add((sq, to, 0, 0))

                if f < 7:
                    to = sq - 7
                    if to >= 0:
                        target = b[to]
                        if target > 0 and target != K:
                            if r == 1:
                                add((sq, to, Q, 0))
                                add((sq, to, R, 0))
                                add((sq, to, B, 0))
                                add((sq, to, N, 0))
                            else:
                                add((sq, to, 0, 0))

        elif a == N:
            for to in KNIGHT_ATTACKS[sq]:
                target = b[to]
                if target == 0:
                    if not captures_only:
                        add((sq, to, 0, 0))
                elif target * color < 0 and target != (-K if white else K):
                    add((sq, to, 0, 0))

        elif a == B or a == R or a == Q:
            if a == B:
                dirs = ((1, 1), (1, -1), (-1, 1), (-1, -1))
            elif a == R:
                dirs = ((1, 0), (-1, 0), (0, 1), (0, -1))
            else:
                dirs = ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1))

            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = (nr << 3) | nf
                    target = b[to]
                    if target == 0:
                        if not captures_only:
                            add((sq, to, 0, 0))
                    else:
                        if target * color < 0 and target != (-K if white else K):
                            add((sq, to, 0, 0))
                        break
                    nf += df
                    nr += dr

        elif a == K:
            for to in KING_ATTACKS[sq]:
                target = b[to]
                if target == 0:
                    if not captures_only:
                        add((sq, to, 0, 0))
                elif target * color < 0 and target != (-K if white else K):
                    add((sq, to, 0, 0))

            if not captures_only:
                if white and sq == 4:
                    if b[7] == R and b[5] == 0 and b[6] == 0:
                        if not is_attacked(b, 4, False) and not is_attacked(b, 5, False):
                            add((4, 6, 0, 1))
                    if b[0] == R and b[1] == 0 and b[2] == 0 and b[3] == 0:
                        if not is_attacked(b, 4, False) and not is_attacked(b, 3, False):
                            add((4, 2, 0, 2))
                elif (not white) and sq == 60:
                    if b[63] == -R and b[61] == 0 and b[62] == 0:
                        if not is_attacked(b, 60, True) and not is_attacked(b, 61, True):
                            add((60, 62, 0, 1))
                    if b[56] == -R and b[57] == 0 and b[58] == 0 and b[59] == 0:
                        if not is_attacked(b, 60, True) and not is_attacked(b, 59, True):
                            add((60, 58, 0, 2))

    return moves


def do_move(board, move, wk, bk):
    fr, to, promo, castle = move
    piece = board[fr]
    captured = board[to]

    board[fr] = 0
    board[to] = (promo if piece > 0 else -promo) if promo else piece

    rook_from = -1
    rook_to = -1
    rook_piece = 0

    if castle:
        if castle == 1:
            rook_from = fr + 3
            rook_to = fr + 1
        else:
            rook_from = fr - 4
            rook_to = fr - 1
        rook_piece = board[rook_from]
        board[rook_from] = 0
        board[rook_to] = rook_piece

    if piece == K:
        wk = to
    elif piece == -K:
        bk = to

    return captured, piece, rook_from, rook_to, rook_piece, wk, bk


def undo_move(board, move, captured, piece, rook_from, rook_to, rook_piece):
    fr, to, promo, castle = move
    board[fr] = piece
    board[to] = captured
    if rook_from != -1:
        board[rook_from] = rook_piece
        board[rook_to] = 0


def generate_legal_moves(board, white, wk, bk, captures_only=False):
    legal = []
    for move in generate_pseudo_moves(board, white, captures_only):
        captured, piece, rook_from, rook_to, rook_piece, nwk, nbk = do_move(board, move, wk, bk)
        my_king = nwk if white else nbk
        if not is_attacked(board, my_king, not white):
            legal.append(move)
        undo_move(board, move, captured, piece, rook_from, rook_to, rook_piece)
    return legal


def score_move(board, move, white, ply, pv_move=None):
    if pv_move is not None and move == pv_move:
        return 10_000_000

    fr, to, promo, castle = move
    attacker = board[fr]
    a = attacker if attacker > 0 else -attacker
    target = board[to]
    t = target if target > 0 else -target

    score = 0

    if promo:
        score += 2_000_000 + PIECE_VALUES[promo]
    if t:
        score += 1_000_000 + 16 * PIECE_VALUES[t] - PIECE_VALUES[a]
    elif castle:
        score += 50_000
    else:
        k0, k1 = KILLERS[ply]
        if move == k0:
            score += 90_000
        elif move == k1:
            score += 80_000

        side_idx = 0 if white else 1
        score += HISTORY[side_idx][fr][to]

        idx_from = fr if white else MIRROR[fr]
        idx_to = to if white else MIRROR[to]
        score += PST[a][idx_to] - PST[a][idx_from]

    return score


def score_qmove(board, move):
    fr, to, promo, _castle = move
    attacker = board[fr]
    a = attacker if attacker > 0 else -attacker
    target = board[to]
    t = target if target > 0 else -target

    score = 0
    if promo:
        score += 2_000_000 + PIECE_VALUES[promo]
    if t:
        score += 1_000_000 + 16 * PIECE_VALUES[t] - PIECE_VALUES[a]
    return score


def quiescence(board, white, wk, bk, alpha, beta, qdepth):
    global NODES, DEADLINE
    NODES += 1
    if (NODES & 2047) == 0 and perf_counter() >= DEADLINE:
        raise SearchTimeout

    stand = evaluate(board)
    if not white:
        stand = -stand

    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand

    if qdepth <= 0:
        return alpha

    moves = generate_legal_moves(board, white, wk, bk, True)
    if not moves:
        return alpha

    moves.sort(key=lambda m: score_qmove(board, m), reverse=True)

    for move in moves:
        captured_est = board[move[1]]
        captured_est = captured_est if captured_est > 0 else -captured_est

        if move[2] == 0 and captured_est and stand + PIECE_VALUES[captured_est] + 90 < alpha:
            continue

        captured, piece, rook_from, rook_to, rook_piece, nwk, nbk = do_move(board, move, wk, bk)
        score = -quiescence(board, not white, nwk, nbk, -beta, -alpha, qdepth - 1)
        undo_move(board, move, captured, piece, rook_from, rook_to, rook_piece)

        if score >= beta:
            return beta
        if score > alpha:
            alpha = score

    return alpha


def negamax(board, white, wk, bk, depth, alpha, beta, ply):
    global NODES, DEADLINE, HISTORY, KILLERS
    NODES += 1
    if (NODES & 1023) == 0 and perf_counter() >= DEADLINE:
        raise SearchTimeout

    in_check = is_attacked(board, wk if white else bk, not white)

    if depth <= 0:
        if in_check:
            depth = 1
        else:
            return quiescence(board, white, wk, bk, alpha, beta, 6)

    moves = generate_legal_moves(board, white, wk, bk, False)

    if not moves:
        if in_check:
            return -MATE + ply
        return 0

    moves.sort(key=lambda m: score_move(board, m, white, ply), reverse=True)

    best = -INF
    side_idx = 0 if white else 1
    first = True

    for move in moves:
        captured, piece, rook_from, rook_to, rook_piece, nwk, nbk = do_move(board, move, wk, bk)

        if first:
            score = -negamax(board, not white, nwk, nbk, depth - 1, -beta, -alpha, ply + 1)
            first = False
        else:
            score = -negamax(board, not white, nwk, nbk, depth - 1, -alpha - 1, -alpha, ply + 1)
            if alpha < score < beta:
                score = -negamax(board, not white, nwk, nbk, depth - 1, -beta, -alpha, ply + 1)

        undo_move(board, move, captured, piece, rook_from, rook_to, rook_piece)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
            if alpha >= beta:
                if captured == 0 and move[2] == 0 and move[3] == 0:
                    if KILLERS[ply][0] != move:
                        KILLERS[ply][1] = KILLERS[ply][0]
                        KILLERS[ply][0] = move
                    HISTORY[side_idx][move[0]][move[1]] += depth * depth
                return alpha

    return best


def search_root(board, white, wk, bk, depth, legal_moves, prev_best):
    alpha = -INF
    beta = INF
    best_score = -INF
    best_move = legal_moves[0]

    moves = legal_moves[:]
    moves.sort(key=lambda m: score_move(board, m, white, 0, prev_best), reverse=True)

    first = True
    for move in moves:
        captured, piece, rook_from, rook_to, rook_piece, nwk, nbk = do_move(board, move, wk, bk)

        if first:
            score = -negamax(board, not white, nwk, nbk, depth - 1, -beta, -alpha, 1)
            first = False
        else:
            score = -negamax(board, not white, nwk, nbk, depth - 1, -alpha - 1, -alpha, 1)
            if score > alpha:
                score = -negamax(board, not white, nwk, nbk, depth - 1, -beta, -alpha, 1)

        undo_move(board, move, captured, piece, rook_from, rook_to, rook_piece)

        if score > best_score:
            best_score = score
            best_move = move
        if score > alpha:
            alpha = score

    return best_score, best_move


def pick_fallback(board, white, wk, bk, legal_moves):
    best_move = legal_moves[0]
    best_score = -INF

    for move in legal_moves:
        score = score_move(board, move, white, 0)

        captured, piece, rook_from, rook_to, rook_piece, nwk, nbk = do_move(board, move, wk, bk)
        enemy_king = nbk if white else nwk
        if enemy_king != -1 and is_attacked(board, enemy_king, white):
            score += 250
        undo_move(board, move, captured, piece, rook_from, rook_to, rook_piece)

        if score > best_score:
            best_score = score
            best_move = move

    return best_move


def policy(pieces: dict[str, str], to_play: str) -> str:
    global DEADLINE, NODES, HISTORY, KILLERS

    board, wk, bk = parse_board(pieces)
    white = (to_play == 'white')

    legal_moves = generate_legal_moves(board, white, wk, bk, False)
    if not legal_moves:
        pseudo = generate_pseudo_moves(board, white, False)
        if pseudo:
            return move_to_uci(pseudo[0])
        return "a1a1"

    if len(legal_moves) == 1:
        return move_to_uci(legal_moves[0])

    HISTORY = [[[0] * 64 for _ in range(64)] for _ in range(2)]
    KILLERS = [[None, None] for _ in range(64)]

    best_move = pick_fallback(board, white, wk, bk, legal_moves)

    DEADLINE = perf_counter() + 0.95
    NODES = 0

    piece_count = sum(1 for p in board if p)
    if piece_count <= 8:
        max_depth = 7
    elif piece_count <= 12:
        max_depth = 6
    elif piece_count <= 20:
        max_depth = 5
    else:
        max_depth = 4

    prev_best = best_move

    try:
        for depth in range(1, max_depth + 1):
            score, move = search_root(board, white, wk, bk, depth, legal_moves, prev_best)
            best_move = move
            prev_best = move
            if abs(score) >= MATE - 100:
                break
    except SearchTimeout:
        pass

    return move_to_uci(best_move)
