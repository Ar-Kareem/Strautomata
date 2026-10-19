
import time
from typing import Dict

INF = 10**9
MATE_SCORE = 100000

PIECE_VALUE = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 0,
}

PROMOS = ('q', 'r', 'b', 'n')
DIAG_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
ORTH_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))
ALL_DIRS = DIAG_DIRS + ORTH_DIRS

FILE_OF = [i & 7 for i in range(64)]
RANK_OF = [i >> 3 for i in range(64)]
SQUARE_NAME = [chr(97 + FILE_OF[i]) + chr(49 + RANK_OF[i]) for i in range(64)]

CENTER_SCORE = []
for sq in range(64):
    f = FILE_OF[sq]
    r = RANK_OF[sq]
    CENTER_SCORE.append(14 - (abs(f - 3) + abs(f - 4) + abs(r - 3) + abs(r - 4)))

KNIGHT_ATTACKS = [[] for _ in range(64)]
KING_ATTACKS = [[] for _ in range(64)]

for sq in range(64):
    f = FILE_OF[sq]
    r = RANK_OF[sq]

    for df, dr in ((1, 2), (2, 1), (2, -1), (1, -2),
                   (-1, -2), (-2, -1), (-2, 1), (-1, 2)):
        nf = f + df
        nr = r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KNIGHT_ATTACKS[sq].append(nr * 8 + nf)

    for df, dr in ((1, 1), (1, 0), (1, -1), (0, 1),
                   (0, -1), (-1, 1), (-1, 0), (-1, -1)):
        nf = f + df
        nr = r + dr
        if 0 <= nf < 8 and 0 <= nr < 8:
            KING_ATTACKS[sq].append(nr * 8 + nf)

PASS_BONUS = [0, 5, 10, 20, 35, 60, 90, 0]

DEADLINE = 0.0
NODE_COUNT = 0
HISTORY = {}


def square_to_idx(sq: str) -> int:
    f = ord(sq[0]) - 97
    r = ord(sq[1]) - 49
    return r * 8 + f


def move_to_uci(move) -> str:
    frm, to, promo, _flag = move
    if promo:
        return SQUARE_NAME[frm] + SQUARE_NAME[to] + promo
    return SQUARE_NAME[frm] + SQUARE_NAME[to]


def captured_piece(board, move):
    frm, to, _promo, flag = move
    if flag == 'ep':
        return 'p' if board[frm].isupper() else 'P'
    return board[to]


def move_order(board, move, pv_move=None):
    score = 0
    if pv_move is not None and move == pv_move:
        score += 1_000_000

    frm, to, promo, flag = move
    mover = board[frm]
    cap = captured_piece(board, move)

    if cap != '.':
        score += 100_000 + 10 * PIECE_VALUE[cap.upper()] - PIECE_VALUE[mover.upper()]
    elif flag in ('ck', 'cq'):
        score += 500

    if promo:
        score += 80_000 + PIECE_VALUE[promo.upper()]

    score += HISTORY.get(move, 0)

    if cap == '.' and promo is None:
        score += CENTER_SCORE[to] - CENTER_SCORE[frm]

    return score


def order_moves(board, moves, pv_move=None):
    if len(moves) <= 1:
        return moves
    return sorted(moves, key=lambda m: move_order(board, m, pv_move), reverse=True)


def make_move(board, wk, bk, move):
    frm, to, promo, flag = move
    b = board.copy()
    piece = b[frm]
    b[frm] = '.'

    if flag == 'ep':
        cap_sq = to - 8 if piece.isupper() else to + 8
        b[cap_sq] = '.'
    elif flag == 'ck':
        if piece == 'K':
            b[7] = '.'
            b[5] = 'R'
        else:
            b[63] = '.'
            b[61] = 'r'
    elif flag == 'cq':
        if piece == 'K':
            b[0] = '.'
            b[3] = 'R'
        else:
            b[56] = '.'
            b[59] = 'r'

    if promo:
        piece = promo.upper() if piece.isupper() else promo

    b[to] = piece

    if piece == 'K':
        wk = to
    elif piece == 'k':
        bk = to

    return b, wk, bk


def square_attacked(board, sq, by_white):
    if sq < 0:
        return False

    f = FILE_OF[sq]
    r = RANK_OF[sq]

    if by_white:
        if r > 0:
            if f > 0 and board[sq - 9] == 'P':
                return True
            if f < 7 and board[sq - 7] == 'P':
                return True
        knight = 'N'
        bishop = 'B'
        rook = 'R'
        queen = 'Q'
        king = 'K'
    else:
        if r < 7:
            if f > 0 and board[sq + 7] == 'p':
                return True
            if f < 7 and board[sq + 9] == 'p':
                return True
        knight = 'n'
        bishop = 'b'
        rook = 'r'
        queen = 'q'
        king = 'k'

    for t in KNIGHT_ATTACKS[sq]:
        if board[t] == knight:
            return True

    for df, dr in DIAG_DIRS:
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p != '.':
                if p == bishop or p == queen:
                    return True
                break
            nf += df
            nr += dr

    for df, dr in ORTH_DIRS:
        nf = f + df
        nr = r + dr
        while 0 <= nf < 8 and 0 <= nr < 8:
            p = board[nr * 8 + nf]
            if p != '.':
                if p == rook or p == queen:
                    return True
                break
            nf += df
            nr += dr

    for t in KING_ATTACKS[sq]:
        if board[t] == king:
            return True

    return False


def generate_pseudo(board, white, tactical_only=False):
    moves = []

    for sq, p in enumerate(board):
        if p == '.' or (p.isupper() != white):
            continue

        pt = p.upper()
        f = FILE_OF[sq]
        r = RANK_OF[sq]

        if pt == 'P':
            if white:
                one = sq + 8
                if r < 7 and board[one] == '.':
                    if r == 6:
                        for pr in PROMOS:
                            moves.append((sq, one, pr, None))
                    elif not tactical_only:
                        moves.append((sq, one, None, None))
                        if r == 1:
                            two = sq + 16
                            if board[two] == '.':
                                moves.append((sq, two, None, None))

                if f > 0:
                    to = sq + 7
                    target = board[to]
                    if target != '.' and (target.isupper() != white) and target.upper() != 'K':
                        if r == 6:
                            for pr in PROMOS:
                                moves.append((sq, to, pr, None))
                        else:
                            moves.append((sq, to, None, None))

                if f < 7:
                    to = sq + 9
                    target = board[to]
                    if target != '.' and (target.isupper() != white) and target.upper() != 'K':
                        if r == 6:
                            for pr in PROMOS:
                                moves.append((sq, to, pr, None))
                        else:
                            moves.append((sq, to, None, None))

            else:
                one = sq - 8
                if r > 0 and board[one] == '.':
                    if r == 1:
                        for pr in PROMOS:
                            moves.append((sq, one, pr, None))
                    elif not tactical_only:
                        moves.append((sq, one, None, None))
                        if r == 6:
                            two = sq - 16
                            if board[two] == '.':
                                moves.append((sq, two, None, None))

                if f > 0:
                    to = sq - 9
                    target = board[to]
                    if target != '.' and (target.isupper() != white) and target.upper() != 'K':
                        if r == 1:
                            for pr in PROMOS:
                                moves.append((sq, to, pr, None))
                        else:
                            moves.append((sq, to, None, None))

                if f < 7:
                    to = sq - 7
                    target = board[to]
                    if target != '.' and (target.isupper() != white) and target.upper() != 'K':
                        if r == 1:
                            for pr in PROMOS:
                                moves.append((sq, to, pr, None))
                        else:
                            moves.append((sq, to, None, None))

        elif pt == 'N':
            for to in KNIGHT_ATTACKS[sq]:
                target = board[to]
                if target == '.':
                    if not tactical_only:
                        moves.append((sq, to, None, None))
                elif (target.isupper() != white) and target.upper() != 'K':
                    moves.append((sq, to, None, None))

        elif pt in ('B', 'R', 'Q'):
            dirs = DIAG_DIRS if pt == 'B' else ORTH_DIRS if pt == 'R' else ALL_DIRS
            for df, dr in dirs:
                nf = f + df
                nr = r + dr
                while 0 <= nf < 8 and 0 <= nr < 8:
                    to = nr * 8 + nf
                    target = board[to]
                    if target == '.':
                        if not tactical_only:
                            moves.append((sq, to, None, None))
                    else:
                        if (target.isupper() != white) and target.upper() != 'K':
                            moves.append((sq, to, None, None))
                        break
                    nf += df
                    nr += dr

        elif pt == 'K':
            for to in KING_ATTACKS[sq]:
                target = board[to]
                if target == '.':
                    if not tactical_only:
                        moves.append((sq, to, None, None))
                elif (target.isupper() != white) and target.upper() != 'K':
                    moves.append((sq, to, None, None))

    return moves


def generate_legal(board, wk, bk, white, tactical_only=False):
    if white and wk < 0:
        return generate_pseudo(board, white, tactical_only)
    if (not white) and bk < 0:
        return generate_pseudo(board, white, tactical_only)

    legal = []
    for move in generate_pseudo(board, white, tactical_only):
        nb, nwk, nbk = make_move(board, wk, bk, move)
        own_king = nwk if white else nbk
        if not square_attacked(nb, own_king, not white):
            legal.append(move)
    return legal


def generate_guessed_special_legal(board, wk, bk, white):
    candidates = []

    if white:
        if wk == 4 and board[4] == 'K' and not square_attacked(board, 4, False):
            if board[7] == 'R' and board[5] == '.' and board[6] == '.':
                if not square_attacked(board, 5, False) and not square_attacked(board, 6, False):
                    candidates.append((4, 6, None, 'ck'))
            if board[0] == 'R' and board[1] == '.' and board[2] == '.' and board[3] == '.':
                if not square_attacked(board, 3, False) and not square_attacked(board, 2, False):
                    candidates.append((4, 2, None, 'cq'))

        for sq, p in enumerate(board):
            if p == 'P' and RANK_OF[sq] == 4:
                f = FILE_OF[sq]
                if f > 0 and board[sq - 1] == 'p' and board[sq + 7] == '.':
                    candidates.append((sq, sq + 7, None, 'ep'))
                if f < 7 and board[sq + 1] == 'p' and board[sq + 9] == '.':
                    candidates.append((sq, sq + 9, None, 'ep'))
    else:
        if bk == 60 and board[60] == 'k' and not square_attacked(board, 60, True):
            if board[63] == 'r' and board[61] == '.' and board[62] == '.':
                if not square_attacked(board, 61, True) and not square_attacked(board, 62, True):
                    candidates.append((60, 62, None, 'ck'))
            if board[56] == 'r' and board[57] == '.' and board[58] == '.' and board[59] == '.':
                if not square_attacked(board, 59, True) and not square_attacked(board, 58, True):
                    candidates.append((60, 58, None, 'cq'))

        for sq, p in enumerate(board):
            if p == 'p' and RANK_OF[sq] == 3:
                f = FILE_OF[sq]
                if f > 0 and board[sq - 1] == 'P' and board[sq - 9] == '.':
                    candidates.append((sq, sq - 9, None, 'ep'))
                if f < 7 and board[sq + 1] == 'P' and board[sq - 7] == '.':
                    candidates.append((sq, sq - 7, None, 'ep'))

    legal = []
    for move in candidates:
        nb, nwk, nbk = make_move(board, wk, bk, move)
        own_king = nwk if white else nbk
        if not square_attacked(nb, own_king, not white):
            legal.append(move)
    return legal


def connected_rooks_bonus(board, rooks):
    n = len(rooks)
    if n < 2:
        return 0

    for i in range(n):
        a = rooks[i]
        for j in range(i + 1, n):
            b = rooks[j]

            if FILE_OF[a] == FILE_OF[b]:
                step = 8 if a < b else -8
                s = a + step
                clear = True
                while s != b:
                    if board[s] != '.':
                        clear = False
                        break
                    s += step
                if clear:
                    return 10

            elif RANK_OF[a] == RANK_OF[b]:
                step = 1 if a < b else -1
                s = a + step
                clear = True
                while s != b:
                    if board[s] != '.':
                        clear = False
                        break
                    s += step
                if clear:
                    return 10

    return 0


def king_placement(sq, white, endgame):
    if sq < 0:
        return 0
    f = FILE_OF[sq]
    r = RANK_OF[sq]
    rr = r if white else 7 - r
    center = CENTER_SCORE[sq]

    if endgame:
        return center * 5 + rr * 2

    bonus = -center * 3 - rr * 6
    if rr == 0 and f in (1, 2, 6):
        bonus += 10
    elif f in (0, 7):
        bonus += 4
    return bonus


def king_shield(board, sq, white):
    if sq < 0:
        return 0
    f = FILE_OF[sq]
    r = RANK_OF[sq]
    forward = 1 if white else -1
    pawn = 'P' if white else 'p'

    bonus = 0
    nr1 = r + forward
    nr2 = r + 2 * forward

    for df in (-1, 0, 1):
        nf = f + df
        if 0 <= nf < 8:
            if 0 <= nr1 < 8 and board[nr1 * 8 + nf] == pawn:
                bonus += 8
            elif 0 <= nr2 < 8 and board[nr2 * 8 + nf] == pawn:
                bonus += 3

    return bonus


def evaluate(board, wk, bk):
    if wk < 0:
        return -MATE_SCORE
    if bk < 0:
        return MATE_SCORE

    score = 0
    piece_total = 0
    nonpawn_material = 0

    white_bishops = 0
    black_bishops = 0
    white_rooks = []
    black_rooks = []
    white_pawns = []
    black_pawns = []
    white_pawn_files = [0] * 8
    black_pawn_files = [0] * 8
    white_pawn_ranks = [[] for _ in range(8)]
    black_pawn_ranks = [[] for _ in range(8)]
    white_queen_sq = -1
    black_queen_sq = -1

    for sq, p in enumerate(board):
        if p == '.':
            continue

        piece_total += 1
        white = p.isupper()
        pt = p.upper()
        f = FILE_OF[sq]
        r = RANK_OF[sq]
        rr = r if white else 7 - r
        val = PIECE_VALUE[pt]
        ps = 0

        if pt not in ('P', 'K'):
            nonpawn_material += val

        if pt == 'P':
            ps += rr * 10
            if 2 <= f <= 5:
                ps += 4
            if f in (3, 4):
                ps += max(0, rr - 1) * 2
            if white:
                white_pawns.append(sq)
                white_pawn_files[f] += 1
                white_pawn_ranks[f].append(r)
            else:
                black_pawns.append(sq)
                black_pawn_files[f] += 1
                black_pawn_ranks[f].append(r)

        elif pt == 'N':
            ps += CENTER_SCORE[sq] * 5 + rr * 2
            if f in (0, 7) or r in (0, 7):
                ps -= 18
            elif f in (1, 6) or r in (1, 6):
                ps -= 6

        elif pt == 'B':
            ps += CENTER_SCORE[sq] * 3 + rr * 2
            if f in (0, 7) or r in (0, 7):
                ps -= 6
            if white:
                white_bishops += 1
            else:
                black_bishops += 1

        elif pt == 'R':
            ps += rr * 2
            if rr == 6:
                ps += 18
            if white:
                white_rooks.append(sq)
            else:
                black_rooks.append(sq)

        elif pt == 'Q':
            ps += CENTER_SCORE[sq] * 2
            if white:
                white_queen_sq = sq
            else:
                black_queen_sq = sq

        if white:
            score += val + ps
        else:
            score -= val + ps

    endgame = nonpawn_material <= 2200

    score += king_placement(wk, True, endgame)
    score -= king_placement(bk, False, endgame)

    if not endgame:
        score += king_shield(board, wk, True)
        score -= king_shield(board, bk, False)

    if white_bishops >= 2:
        score += 25
    if black_bishops >= 2:
        score -= 25

    for f in range(8):
        if white_pawn_files[f] > 1:
            score -= 10 * (white_pawn_files[f] - 1)
        if black_pawn_files[f] > 1:
            score += 10 * (black_pawn_files[f] - 1)

    for sq in white_pawns:
        f = FILE_OF[sq]
        r = RANK_OF[sq]

        if (f == 0 or white_pawn_files[f - 1] == 0) and (f == 7 or white_pawn_files[f + 1] == 0):
            score -= 12

        passed = True
        for ef in (f - 1, f, f + 1):
            if 0 <= ef < 8:
                for br in black_pawn_ranks[ef]:
                    if br > r:
                        passed = False
                        break
            if not passed:
                break
        if passed:
            score += PASS_BONUS[r]

    for sq in black_pawns:
        f = FILE_OF[sq]
        r = RANK_OF[sq]
        rr = 7 - r

        if (f == 0 or black_pawn_files[f - 1] == 0) and (f == 7 or black_pawn_files[f + 1] == 0):
            score += 12

        passed = True
        for ef in (f - 1, f, f + 1):
            if 0 <= ef < 8:
                for wr in white_pawn_ranks[ef]:
                    if wr < r:
                        passed = False
                        break
            if not passed:
                break
        if passed:
            score -= PASS_BONUS[rr]

    for sq in white_rooks:
        f = FILE_OF[sq]
        if white_pawn_files[f] == 0:
            score += 14 if black_pawn_files[f] == 0 else 7

    for sq in black_rooks:
        f = FILE_OF[sq]
        if black_pawn_files[f] == 0:
            score -= 14 if white_pawn_files[f] == 0 else 7

    score += connected_rooks_bonus(board, white_rooks)
    score -= connected_rooks_bonus(board, black_rooks)

    if not endgame and piece_total >= 24:
        if board[1] == 'N':
            score -= 10
        if board[6] == 'N':
            score -= 10
        if board[2] == 'B':
            score -= 8
        if board[5] == 'B':
            score -= 8

        if board[57] == 'n':
            score += 10
        if board[62] == 'n':
            score += 10
        if board[58] == 'b':
            score += 8
        if board[61] == 'b':
            score += 8

        if board[11] == 'P':
            score -= 4
        if board[12] == 'P':
            score -= 4
        if board[51] == 'p':
            score += 4
        if board[52] == 'p':
            score += 4

        if white_queen_sq not in (-1, 3):
            score -= 8
        if black_queen_sq not in (-1, 59):
            score += 8

    return score


def qsearch(board, wk, bk, white, alpha, beta, ply):
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise TimeoutError

    if ply >= 48:
        val = evaluate(board, wk, bk)
        return val if white else -val

    own_king = wk if white else bk
    in_check = square_attacked(board, own_king, not white)

    if in_check:
        moves = generate_legal(board, wk, bk, white, tactical_only=False)
        if not moves:
            return -MATE_SCORE + ply

        best = -INF
        for move in order_moves(board, moves):
            nb, nwk, nbk = make_move(board, wk, bk, move)
            score = -qsearch(nb, nwk, nbk, not white, -beta, -alpha, ply + 1)
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                cap = captured_piece(board, move)
                if cap == '.' and move[2] is None and move[3] is None:
                    HISTORY[move] = HISTORY.get(move, 0) + 1
                break
        return best

    stand = evaluate(board, wk, bk)
    if not white:
        stand = -stand

    if stand >= beta:
        return stand
    if stand > alpha:
        alpha = stand

    moves = generate_legal(board, wk, bk, white, tactical_only=True)
    if not moves:
        return stand

    for move in order_moves(board, moves):
        nb, nwk, nbk = make_move(board, wk, bk, move)
        score = -qsearch(nb, nwk, nbk, not white, -beta, -alpha, ply + 1)
        if score > alpha:
            alpha = score
        if alpha >= beta:
            break

    return alpha


def search(board, wk, bk, white, depth, alpha, beta, ply):
    global NODE_COUNT

    NODE_COUNT += 1
    if (NODE_COUNT & 1023) == 0 and time.perf_counter() > DEADLINE:
        raise TimeoutError

    if ply >= 48:
        val = evaluate(board, wk, bk)
        return val if white else -val

    if depth <= 0:
        return qsearch(board, wk, bk, white, alpha, beta, ply)

    own_king = wk if white else bk
    in_check = square_attacked(board, own_king, not white)

    moves = generate_legal(board, wk, bk, white, tactical_only=False)
    if not moves:
        return -MATE_SCORE + ply if in_check else 0

    best = -INF
    for move in order_moves(board, moves):
        nb, nwk, nbk = make_move(board, wk, bk, move)
        score = -search(nb, nwk, nbk, not white, depth - 1, -beta, -alpha, ply + 1)

        if score > best:
            best = score
        if score > alpha:
            alpha = score
        if alpha >= beta:
            cap = captured_piece(board, move)
            if cap == '.' and move[2] is None and move[3] is None:
                HISTORY[move] = HISTORY.get(move, 0) + depth * depth
            break

    return best


def policy(pieces: Dict[str, str], to_play: str) -> str:
    global DEADLINE, NODE_COUNT, HISTORY

    DEADLINE = time.perf_counter() + 0.92
    NODE_COUNT = 0
    HISTORY = {}

    board = ['.'] * 64
    wk = -1
    bk = -1

    for sq, code in pieces.items():
        if len(sq) != 2 or len(code) != 2:
            continue

        f = ord(sq[0]) - 97
        r = ord(sq[1]) - 49
        if not (0 <= f < 8 and 0 <= r < 8):
            continue

        idx = r * 8 + f
        ch = code[1].upper() if code[0] == 'w' else code[1].lower()
        board[idx] = ch

        if ch == 'K':
            wk = idx
        elif ch == 'k':
            bk = idx

    white = (to_play == 'white')

    root_moves = generate_legal(board, wk, bk, white, tactical_only=False)
    if not root_moves:
        root_moves = generate_guessed_special_legal(board, wk, bk, white)

    if not root_moves:
        pseudo = generate_pseudo(board, white, tactical_only=False)
        if pseudo:
            return move_to_uci(order_moves(board, pseudo)[0])
        return "a1a1"

    if len(root_moves) == 1:
        return move_to_uci(root_moves[0])

    root_moves = order_moves(board, root_moves)
    best_move = root_moves[0]
    pv_move = best_move

    piece_count = len(pieces)
    if piece_count <= 6 or len(root_moves) <= 8:
        max_depth = 6
    elif piece_count <= 10 or len(root_moves) <= 14:
        max_depth = 5
    elif piece_count <= 18 or len(root_moves) <= 24:
        max_depth = 4
    else:
        max_depth = 3

    for depth in range(1, max_depth + 1):
        try:
            ordered = order_moves(board, root_moves, pv_move)
            current_best = ordered[0]
            current_best_score = -INF
            alpha = -INF
            beta = INF

            for move in ordered:
                nb, nwk, nbk = make_move(board, wk, bk, move)
                score = -search(nb, nwk, nbk, not white, depth - 1, -beta, -alpha, 1)

                if score > current_best_score:
                    current_best_score = score
                    current_best = move
                if score > alpha:
                    alpha = score

            best_move = current_best
            pv_move = current_best

            if current_best_score > MATE_SCORE - 1000:
                break

        except TimeoutError:
            break

    return move_to_uci(best_move)
